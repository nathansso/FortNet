"""Fight segmentation, v0: from the kill feed only.

A fight is a connected group of knock/elim events within one match, where two
events are linked if they share a player and are at most `gap_ms` apart.
This undercounts fights (any fight with no knock is invisible) and has no team
info. Once packet parsing works, replace it with damage-event segmentation,
which also sees fights that end without a knock.
"""

import numpy as np
import pandas as pd

DEFAULT_GAP_MS = 30_000


def _segment_match(ev: pd.DataFrame, gap_ms: int) -> list[int]:
    parent = list(range(len(ev)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    last_seen: dict[str, tuple[int, int]] = {}  # player -> (event idx, t_ms)
    for i, (t, a, b) in enumerate(zip(ev["t_ms"], ev["eliminator"], ev["eliminated"])):
        for player in (a, b):
            if player is None or pd.isna(player):
                continue
            if player in last_seen and t - last_seen[player][1] <= gap_ms:
                parent[find(i)] = find(last_seen[player][0])
            last_seen[player] = (i, t)

    roots = [find(i) for i in range(len(ev))]
    ids = {r: n for n, r in enumerate(dict.fromkeys(roots))}
    return [ids[r] for r in roots]


def assign_fights(elims: pd.DataFrame, gap_ms: int = DEFAULT_GAP_MS) -> pd.DataFrame:
    """Add a `fight_id` column (unique across matches) to the kill-feed table."""
    parts = []
    for match_id, ev in elims.groupby("match_id", sort=False):
        ev = ev.sort_values("t_ms").reset_index(drop=True)
        local = _segment_match(ev, gap_ms)
        ev["fight_id"] = [f"{match_id}:{n}" for n in local]
        parts.append(ev)
    if not parts:
        return elims.assign(fight_id=pd.Series(dtype=str))
    return pd.concat(parts, ignore_index=True)


def fights_table(elims_with_fights: pd.DataFrame) -> pd.DataFrame:
    """One row per fight."""
    g = elims_with_fights.groupby("fight_id", sort=False)
    out = g.agg(
        match_id=("match_id", "first"),
        t_start_ms=("t_ms", "min"),
        t_end_ms=("t_ms", "max"),
        n_events=("t_ms", "size"),
        n_knocks=("knocked", "sum"),
    ).reset_index()
    out["n_elims"] = out["n_events"] - out["n_knocks"]
    out["duration_ms"] = out["t_end_ms"] - out["t_start_ms"]
    players = g.apply(
        lambda d: sorted(set(d["eliminator"].dropna()) | set(d["eliminated"].dropna())),
        include_groups=False,
    )
    out["n_players"] = out["fight_id"].map(players.map(len))
    return out


def player_fight_outcomes(elims_with_fights: pd.DataFrame) -> pd.DataFrame:
    """One row per (fight, player): knocks/elims dealt and received.

    `lost` = the player was knocked or eliminated in the fight. This is the
    provisional per-player label for the fight-level model.
    """
    dealt = elims_with_fights.dropna(subset=["eliminator"]).assign(player=lambda d: d["eliminator"])
    recv = elims_with_fights.dropna(subset=["eliminated"]).assign(player=lambda d: d["eliminated"])

    d = dealt.groupby(["fight_id", "player"]).agg(
        knocks_dealt=("knocked", "sum"), events_dealt=("t_ms", "size")
    )
    r = recv.groupby(["fight_id", "player"]).agg(
        knocks_recv=("knocked", "sum"), events_recv=("t_ms", "size")
    )
    out = d.join(r, how="outer").fillna(0).astype(int).reset_index()
    out["elims_dealt"] = out["events_dealt"] - out["knocks_dealt"]
    out["elims_recv"] = out["events_recv"] - out["knocks_recv"]
    out["lost"] = out["events_recv"] > 0
    return out.drop(columns=["events_dealt", "events_recv"])


# ---------------------------------------------------------------------------------------------------------------------
# v1: damage-based segmentation (architecture 1.1). Everything below produces `fight_sides`.
# ---------------------------------------------------------------------------------------------------------------------

GAP_S = 10.0
"""A team pair's damage stream splits into separate segments when consecutive hits are more than this far apart."""

OVERLAP_TOL_S = 1.0
"""Two team-pair segments that share a team join into one (multi-team) fight if their time spans overlap, or are
separated by at most this many seconds. 0 = strict overlap. Deliberately NOT `GAP_S`: with GAP_S proximity, sequential
fights (A beats B, then A meets C within 10 s) chain into 13-team blobs and 38% of fights become multi-team."""

GRACE_S = 3.0
"""A knock/elimination counts for a fight if it lands within this many seconds after the last damage event.
Covers the killing blow's damage cue being missing or arriving slightly late."""

TIE_S = 1.0
"""If two sides each suffer a first knock within this many seconds of each other, both are labelled `tie`."""

DIRECT_ELIM_ALL_MODES = False
"""An elimination with no earlier knock of that victim counts as a knock. Always true for solo matches. If False,
team modes ignore such eliminations (the plan's default); if True they count too (last alive teammate dying)."""

POKE_MIN_SHARE = 0.10
"""A fight is a `poke` if it is not mutual (only one team dealt damage) or the second-largest dealing team
dealt less than this share of the fight's total damage; otherwise it is a `fight`. Pokes are classified, never
dropped: zone-edge poking is a skill in its own right. Provisional, swept in scripts/sweep_fights.py."""

HIT_POS_MAX_AGE_S = 2.0
"""A player's position counts for a hit's shooter-target distance only if the last position update is at most this
old (distant pawns update rarely in client replays)."""


def team_at(df: pd.DataFrame, player_col: str, time_col: str, teams: pd.DataFrame) -> pd.Series:
    """Team of `df[player_col]` at `df[time_col]`: the last `teams` row at or before that time, per match and player.

    Returns nullable ints aligned to `df.index` (NA where the player has no assignment yet).
    """
    left = df[["match_id", time_col, player_col]].rename(columns={player_col: "player_id", time_col: "t"})
    left = left.assign(_i=np.arange(len(df))).dropna(subset=["player_id"]).sort_values("t")
    right = teams[["match_id", "player_id", "t", "team_index"]].sort_values("t")
    right = right.astype({"match_id": "object", "player_id": "object"})
    left = left.astype({"match_id": "object", "player_id": "object"})
    got = pd.merge_asof(left, right, on="t", by=["match_id", "player_id"], direction="backward")
    vals = pd.array([pd.NA] * len(df), dtype="Int64")
    vals[got["_i"].to_numpy()] = got["team_index"].astype("Int64").to_numpy()
    return pd.Series(vals, index=df.index)


def engagement_damage(damage: pd.DataFrame, teams: pd.DataFrame) -> pd.DataFrame:
    """Player-to-player damage between different teams, with each side's team at hit time.

    Keeps `target` and `source` not null, `source != target`, `magnitude > 0`. Drops rows whose team is unknown or
    that are friendly fire. Adds `source_team`, `target_team` and the unordered pair `team_a < team_b`.
    """
    d = damage[["match_id", "t", "source", "target", "magnitude"]]
    d = d[d["target"].notna() & d["source"].notna() & (d["source"] != d["target"]) & (d["magnitude"] > 0)].copy()
    d = d.astype({"match_id": "object", "source": "object", "target": "object"})
    d["source_team"] = team_at(d, "source", "t", teams)
    d["target_team"] = team_at(d, "target", "t", teams)
    d = d.dropna(subset=["source_team", "target_team"])
    d = d[d["source_team"] != d["target_team"]].astype({"source_team": int, "target_team": int})
    d["team_a"] = d[["source_team", "target_team"]].min(axis=1)
    d["team_b"] = d[["source_team", "target_team"]].max(axis=1)
    return d.sort_values(["match_id", "t", "source", "target"], kind="stable").reset_index(drop=True)


def team_pair_segments(eng: pd.DataFrame, gap_s: float = GAP_S) -> pd.DataFrame:
    """Add a global `segment` id: per match and unordered team pair, a new segment after a gap > `gap_s`."""
    e = eng.sort_values(["match_id", "team_a", "team_b", "t"], kind="stable")
    step = e.groupby(["match_id", "team_a", "team_b"], sort=False)["t"].diff()
    new = step.isna() | (step > gap_s)
    e = e.assign(segment=new.cumsum().astype(int))
    return e.sort_values(["match_id", "t", "source", "target"], kind="stable").reset_index(drop=True)


def _link_segments(spans: np.ndarray, tol_s: float) -> list[int]:
    """Union-find over one match's segments [team_a, team_b, start, end]; link if they share a team and overlap
    within `tol_s` (lag = later start - earlier end). Returns each segment's component root."""
    parent = list(range(len(spans)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(spans)):
        for j in range(i + 1, len(spans)):
            shares = {spans[i][0], spans[i][1]} & {spans[j][0], spans[j][1]}
            if shares and max(spans[i][2], spans[j][2]) - min(spans[i][3], spans[j][3]) <= tol_s:
                parent[find(i)] = find(j)
    return [find(i) for i in range(len(spans))]


def group_fights(eng: pd.DataFrame, gap_s: float = GAP_S, overlap_tol_s: float = OVERLAP_TOL_S) -> pd.DataFrame:
    """Add `segment` and `fight_id` to engagement damage: segments merged into fights (see OVERLAP_TOL_S).

    Ids are `f"{match_id}:{n}"`, n in order of (t0, lowest team index), so reruns give identical ids.
    """
    if eng.empty:
        return eng.assign(segment=pd.Series(dtype=int), fight_id=pd.Series(dtype=object))
    e = team_pair_segments(eng, gap_s)
    seg = e.groupby("segment").agg(
        match_id=("match_id", "first"), team_a=("team_a", "first"), team_b=("team_b", "first"),
        start=("t", "min"), end=("t", "max"),
    ).reset_index()
    seg["root"] = -1
    for _, g in seg.groupby("match_id", sort=False):
        roots = _link_segments(g[["team_a", "team_b", "start", "end"]].to_numpy(), overlap_tol_s)
        seg.loc[g.index, "root"] = g.index.to_numpy()[roots]
    f = seg.groupby("root").agg(
        match_id=("match_id", "first"), t0=("start", "min"), low=("team_a", "min"),
    ).reset_index().sort_values(["match_id", "t0", "low"], kind="stable")
    f["n"] = f.groupby("match_id").cumcount()
    f["fight_id"] = f["match_id"] + ":" + f["n"].astype(str)
    seg = seg.merge(f[["root", "fight_id"]], on="root")
    return e.merge(seg[["segment", "fight_id"]], on="segment")


def outcome_events(elims: pd.DataFrame, teams: pd.DataFrame, solo_matches: set[str],
                   direct_elim_all_modes: bool = DIRECT_ELIM_ALL_MODES) -> pd.DataFrame:
    """Knocks (and eliminations that stand in for a knock) between different teams, sorted by time.

    Columns: match_id, t, eliminator, eliminated, victim_team, killer_team. A not-knocked elimination counts when
    the victim has no earlier knock and the match is solo (or `direct_elim_all_modes`).
    """
    e = elims[["match_id", "t_ms", "eliminator", "eliminated", "knocked"]].copy()
    e = e.astype({"match_id": "object", "eliminator": "object", "eliminated": "object"})
    e["t"] = e["t_ms"] / 1000
    first_knock = e[e["knocked"]].groupby(["match_id", "eliminated"])["t"].min()
    key = pd.MultiIndex.from_frame(e[["match_id", "eliminated"]])
    prior = first_knock.reindex(key).to_numpy()
    no_prior = ~(prior <= e["t"].to_numpy())
    eligible = e["match_id"].isin(solo_matches) | direct_elim_all_modes
    e = e[e["knocked"] | (no_prior & eligible)].copy()
    e["victim_team"] = team_at(e, "eliminated", "t", teams)
    e["killer_team"] = team_at(e, "eliminator", "t", teams)
    e = e.dropna(subset=["victim_team", "killer_team"])
    e = e[e["victim_team"] != e["killer_team"]].astype({"victim_team": int, "killer_team": int})
    return e[["match_id", "t", "eliminator", "eliminated", "victim_team", "killer_team"]].sort_values(
        ["match_id", "t"], kind="stable").reset_index(drop=True)


def label_outcomes(fight_teams: set[int], t0: float, t_end: float, ev: pd.DataFrame,
                   grace_s: float = GRACE_S, tie_s: float = TIE_S) -> dict[int, str]:
    """Outcome per team for one fight. `ev` is that match's `outcome_events`, sorted by t.

    Only events in [t0, t_end + grace_s] between two fight teams count. A team's first loss (a member knocked by
    another fight team) and first win (it knocked another fight team's member) decide: the team is `tie` if
    at least two teams' first losses fall within `tie_s` of the earliest one, else `loss` if its first loss
    precedes its first win (or it has no win), else `win` if it has a win, else `disengage`.
    """
    sel = ev[(ev["t"] >= t0) & (ev["t"] <= t_end + grace_s) & ev["victim_team"].isin(fight_teams)
             & ev["killer_team"].isin(fight_teams)]
    first_loss: dict[int, float] = {}
    first_win: dict[int, float] = {}
    for t, v, k in zip(sel["t"], sel["victim_team"], sel["killer_team"]):
        first_loss.setdefault(int(v), t)
        first_win.setdefault(int(k), t)
    out = {tm: "disengage" for tm in fight_teams}
    if not first_loss:
        return out
    earliest = min(first_loss.values())
    tied = [tm for tm, t in first_loss.items() if t <= earliest + tie_s]
    for tm in fight_teams:
        if len(tied) >= 2 and tm in tied:
            out[tm] = "tie"
        elif tm in first_loss and (tm not in first_win or first_loss[tm] <= first_win[tm]):
            out[tm] = "loss"
        elif tm in first_win:
            out[tm] = "win"
    return out


def hit_distances(eng: pd.DataFrame, positions: pd.DataFrame, max_age_s: float = HIT_POS_MAX_AGE_S) -> pd.Series:
    """3-D shooter-to-target distance in metres at each engagement hit (NaN if either position is missing/stale)."""
    pos = positions[["match_id", "player_id", "t", "x", "y", "z"]].dropna(subset=["player_id"])
    pos = pos.astype({"match_id": "object", "player_id": "object"}).sort_values("t")
    out = eng[["match_id", "t"]].astype({"match_id": "object"}).assign(_i=np.arange(len(eng)))
    xyz = {}
    for who in ("source", "target"):
        left = out.assign(player_id=eng[who].to_numpy()).astype({"match_id": "object", "player_id": "object"})
        left = left.sort_values("t")
        got = pd.merge_asof(left, pos, on="t", by=["match_id", "player_id"], direction="backward",
                            tolerance=max_age_s).sort_values("_i")
        xyz[who] = got[["x", "y", "z"]].to_numpy()
    d = np.sqrt(((xyz["source"] - xyz["target"]) ** 2).sum(axis=1)) / 100
    return pd.Series(d, index=eng.index)


def build_fight_sides(
    damage: pd.DataFrame, teams: pd.DataFrame, elims: pd.DataFrame, players: pd.DataFrame, matches: pd.DataFrame,
    positions: pd.DataFrame | None = None,
    *, gap_s: float = GAP_S, overlap_tol_s: float = OVERLAP_TOL_S, grace_s: float = GRACE_S, tie_s: float = TIE_S,
    direct_elim_all_modes: bool = DIRECT_ELIM_ALL_MODES, poke_min_share: float = POKE_MIN_SHARE,
) -> pd.DataFrame:
    """One row per (fight, team): the `fight_sides` table. See docs/architecture.md 1.1 and the module constants."""
    eng = group_fights(engagement_damage(damage, teams), gap_s, overlap_tol_s)
    cols = ["fight_id", "match_id", "team_index", "opp_team_index", "t0", "t_end", "players", "outcome", "multi_team",
            "n_damage_events", "hits_dealt", "hits_taken", "damage_dealt", "damage_taken", "recorder_involved",
            "has_bots", "mutual", "minority_damage_share", "engagement_type", "dist_median_m", "dist_max_m"]
    if eng.empty:
        return pd.DataFrame({c: [] for c in cols})

    # Per (fight, team) side: both directions of every engagement row.
    src = eng.assign(team=eng["source_team"], opp=eng["target_team"], player=eng["source"],
                     dealt=eng["magnitude"], taken=0.0)
    tgt = eng.assign(team=eng["target_team"], opp=eng["source_team"], player=eng["target"],
                     dealt=0.0, taken=eng["magnitude"])
    sides = pd.concat([src, tgt], ignore_index=True)
    sides["flow"] = sides["dealt"] + sides["taken"]
    sides["hit_dealt"] = (sides["dealt"] > 0).astype(int)
    sides["hit_taken"] = (sides["taken"] > 0).astype(int)
    agg = sides.groupby(["fight_id", "team"]).agg(
        n_damage_events=("t", "size"), hits_dealt=("hit_dealt", "sum"), hits_taken=("hit_taken", "sum"),
        damage_dealt=("dealt", "sum"), damage_taken=("taken", "sum"),
        players=("player", lambda s: ";".join(sorted(set(s)))),
    ).reset_index()
    # n_damage_events counts rows involving the team, either direction (each row appears once per side)
    # primary opponent: the other team this team exchanged the most damage with (ties -> lowest index)
    pair = sides.groupby(["fight_id", "team", "opp"])["flow"].sum().reset_index().sort_values(
        ["fight_id", "team", "flow", "opp"], ascending=[True, True, False, True])
    agg = agg.merge(pair.drop_duplicates(["fight_id", "team"])[["fight_id", "team", "opp"]], on=["fight_id", "team"])

    span = eng.groupby("fight_id").agg(match_id=("match_id", "first"), t0=("t", "min"), t_end=("t", "max"))
    n_teams = agg.groupby("fight_id")["team"].nunique().rename("n_teams")
    fights = span.join(n_teams)
    # Poke vs fight: per fight, shares of total damage by dealing team; minority = second-largest dealer.
    dealt = agg.pivot_table(index="fight_id", columns="team", values="damage_dealt", aggfunc="sum").fillna(0)
    ranked = -np.sort(-dealt.to_numpy(), axis=1)
    total = ranked.sum(axis=1)
    second = ranked[:, 1] if ranked.shape[1] > 1 else np.zeros(len(ranked))
    fights["minority_damage_share"] = pd.Series(second / np.where(total > 0, total, 1), index=dealt.index)
    fights["mutual"] = pd.Series((dealt > 0).sum(axis=1) >= 2, index=dealt.index)
    fights["engagement_type"] = np.where(
        fights["mutual"] & (fights["minority_damage_share"] >= poke_min_share), "fight", "poke")
    if positions is not None:
        eng = eng.assign(dist=hit_distances(eng, positions))
        dist = eng.groupby("fight_id")["dist"].agg(dist_median_m="median", dist_max_m="max")
        fights = fights.join(dist)
    else:
        fights["dist_median_m"] = np.nan
        fights["dist_max_m"] = np.nan
    all_players = agg.groupby("fight_id")["players"].apply(lambda s: set(";".join(s).split(";")))

    owner = matches.set_index("match_id")["replay_owner"]
    bots = set(zip(players.loc[players["is_bot"], "match_id"], players.loc[players["is_bot"], "player_id"]))
    fights["recorder_involved"] = [
        owner.get(m) is not None and owner.get(m) in all_players[f] for f, m in zip(fights.index, fights["match_id"])
    ]
    fights["has_bots"] = [
        any((m, p) in bots or p.startswith("BOT_") for p in all_players[f])
        for f, m in zip(fights.index, fights["match_id"])
    ]

    size = teams.groupby(["match_id", "team_index"])["player_id"].nunique().groupby("match_id").max()
    solo = set(size[size <= 1].index)
    ev = outcome_events(elims, teams, solo, direct_elim_all_modes)
    ev_by_match = {m: g.reset_index(drop=True) for m, g in ev.groupby("match_id")}
    empty = ev.iloc[:0]
    team_sets = agg.groupby("fight_id")["team"].apply(lambda s: {int(x) for x in s})
    outcome: dict[tuple[str, int], str] = {}
    for fid, row in fights.iterrows():
        lab = label_outcomes(team_sets[fid], row["t0"], row["t_end"], ev_by_match.get(row["match_id"], empty),
                             grace_s, tie_s)
        outcome.update({(fid, tm): o for tm, o in lab.items()})

    out = agg.rename(columns={"team": "team_index", "opp": "opp_team_index"}).merge(fights.reset_index(), on="fight_id")
    out["outcome"] = [outcome[(f, t)] for f, t in zip(out["fight_id"], out["team_index"])]
    out["multi_team"] = out["n_teams"] > 2
    out["n"] = out["fight_id"].str.rsplit(":", n=1).str[1].astype(int)
    out = out.sort_values(["match_id", "n", "team_index"], kind="stable").reset_index(drop=True)
    return out[cols]


def recorder_knock_coverage(elims: pd.DataFrame, fight_sides: pd.DataFrame, teams: pd.DataFrame,
                            matches: pd.DataFrame, grace_s: float = GRACE_S) -> pd.DataFrame:
    """Recorder-involved opposing-team knocks and whether a v1 fight explains each one.

    Returns one row per knock with `covered` (inside a fight of both teams, [t0, t_end + grace_s], where the
    victim's side has a non-`disengage` outcome) and `in_fight` (same but any outcome). The recorder sees every
    fight it takes part in, so this is the segmentation's recall; other knocks may be out of view range.
    """
    owner = matches.set_index("match_id")["replay_owner"]
    k = elims[elims["knocked"]].astype({"match_id": "object", "eliminator": "object", "eliminated": "object"}).copy()
    k["t"] = k["t_ms"] / 1000
    own = k["match_id"].map(owner)
    k = k[(k["eliminated"] == own) | (k["eliminator"] == own)].copy()
    k["victim_team"] = team_at(k, "eliminated", "t", teams)
    k["killer_team"] = team_at(k, "eliminator", "t", teams)
    k = k.dropna(subset=["victim_team", "killer_team"])
    k = k[k["victim_team"] != k["killer_team"]].astype({"victim_team": int, "killer_team": int})
    fights = fight_sides.groupby("fight_id").agg(match_id=("match_id", "first"), t0=("t0", "first"),
                                                 t_end=("t_end", "first"))
    fs = fight_sides.set_index(["fight_id", "team_index"])["outcome"]
    teams_of = fight_sides.groupby("fight_id")["team_index"].apply(set)
    by_match = {m: g for m, g in fights.groupby("match_id")}
    in_fight, covered = [], []
    for r in k.itertuples():
        g = by_match.get(r.match_id)
        hit_any = hit_out = False
        if g is not None:
            for fid in g.index[(g["t0"] <= r.t) & (r.t <= g["t_end"] + grace_s)]:
                if r.victim_team in teams_of[fid] and r.killer_team in teams_of[fid]:
                    hit_any = True
                    hit_out |= fs[(fid, r.victim_team)] != "disengage"
        in_fight.append(hit_any)
        covered.append(hit_out)
    return k.assign(in_fight=in_fight, covered=covered)[["match_id", "t", "eliminator", "eliminated", "in_fight", "covered"]]
