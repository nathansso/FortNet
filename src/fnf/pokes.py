"""Poke outcome labels (architecture 1.1a): what a poke caused, for fights typed `poke` in `fight_sides`.

A poke is a one-sided (or nearly one-sided) engagement. Its value is what it causes next, so each poke gets:
net damage, `converted` (a target player knocked/eliminated by anyone soon after), `storm_death`, and structure
pressure. Forced heal is skipped: `health` is recorder-only in client replays.

These labels look ahead of the poke by design (`POKE_CONVERT_S` after `t_end`). The poke's own `t0`, participants
and classification never do: they come from `fnf.fights`. All thresholds are v1 values tuned on local Zero Build
pub replays and will be re-tuned on competitive Build data (architecture: "Label calibration and relabeling").
"""

import numpy as np
import pandas as pd

from fnf.fights import (
    GAP_S, GRACE_S, HIT_POS_MAX_AGE_S, OVERLAP_TOL_S, POKE_CONVERT_S, POKE_MINORITY_SHARE, engagement_damage,
    group_fights, seg_version, team_at,
)

TILE_UU = 512.0
STRUCTURE_RADIUS_TILES = 2.0
"""Structure damage counts as pressure if it lands within this many build tiles (horizontal) of a target player's
position at that moment. Only a handful of Build matches exist locally, so this is implemented but not tuned."""

POKE_COLUMNS = [
    "fight_id", "match_id", "poker_team", "target_team", "t0", "t_end", "net_damage", "target_players", "converted",
    "converted_by", "converter_team", "t_convert", "storm_death", "structure_damage", "structure_hits", "seg_version",
]


def _objects(df: pd.DataFrame, *cols: str) -> pd.DataFrame:
    return df.astype({c: "object" for c in cols})


def poke_pairs(eng: pd.DataFrame) -> pd.DataFrame:
    """Per fight: the poking team (most damage dealt, ties to the lowest index), its main target team (the team
    it dealt the most damage to), net damage (poker's damage to that team minus that team's damage back), the
    target players the poker hit, and the fight's t0/t_end."""
    dealt = eng.groupby(["fight_id", "source_team"])["magnitude"].sum().reset_index().sort_values(
        ["fight_id", "magnitude", "source_team"], ascending=[True, False, True])
    poker = dealt.drop_duplicates("fight_id").rename(columns={"source_team": "poker_team"})[["fight_id", "poker_team"]]
    e = eng.merge(poker, on="fight_id")
    out = e[e["source_team"] == e["poker_team"]]
    tgt = out.groupby(["fight_id", "target_team"])["magnitude"].sum().reset_index().sort_values(
        ["fight_id", "magnitude", "target_team"], ascending=[True, False, True]).drop_duplicates("fight_id")
    pairs = poker.merge(tgt[["fight_id", "target_team"]], on="fight_id")
    e = e.merge(pairs[["fight_id", "target_team"]].rename(columns={"target_team": "tt"}), on="fight_id")
    fwd = e[(e["source_team"] == e["poker_team"]) & (e["target_team"] == e["tt"])]
    back = e[(e["source_team"] == e["tt"]) & (e["target_team"] == e["poker_team"])]
    pairs["net_damage"] = pairs["fight_id"].map(fwd.groupby("fight_id")["magnitude"].sum()).fillna(0) \
        - pairs["fight_id"].map(back.groupby("fight_id")["magnitude"].sum()).fillna(0)
    pairs["target_players"] = pairs["fight_id"].map(
        fwd.groupby("fight_id")["target"].agg(lambda s: ";".join(sorted(set(s)))))
    span = eng.groupby("fight_id").agg(match_id=("match_id", "first"), t0=("t", "min"), t_end=("t", "max"))
    return pairs.merge(span.reset_index(), on="fight_id")


def label_conversion(pairs: pd.DataFrame, elims: pd.DataFrame, teams: pd.DataFrame, convert_s: float) -> pd.DataFrame:
    """`converted`, `converted_by` (poker | third_party | environment), `converter_team`, `t_convert` (seconds after
    t_end; negative if it happened during the poke) from the first knock/elimination of a target player in
    [t0, t_end + convert_s]. `environment` = the eliminator is the victim itself or has no team (storm, fall)."""
    tp = pairs[["fight_id", "match_id", "t0", "t_end", "target_players"]].assign(
        player=pairs["target_players"].str.split(";")).explode("player")
    ev = _objects(elims[["match_id", "t_ms", "eliminator", "eliminated"]], "match_id", "eliminator", "eliminated")
    ev["t"] = ev["t_ms"] / 1000
    m = _objects(tp, "match_id", "player").merge(ev, left_on=["match_id", "player"], right_on=["match_id", "eliminated"])
    m = m[(m["t"] >= m["t0"]) & (m["t"] <= m["t_end"] + convert_s)].sort_values(["fight_id", "t"], kind="stable")
    first = m.drop_duplicates("fight_id").copy()
    first["killer_team"] = team_at(first, "eliminator", "t", teams)
    first = first.merge(pairs[["fight_id", "poker_team"]], on="fight_id")
    kt = first["killer_team"]
    first["converted_by"] = np.where(
        (first["eliminator"] == first["eliminated"]) | kt.isna(), "environment",
        np.where(kt == first["poker_team"], "poker", "third_party"))
    first["converter_team"] = kt.where(first["converted_by"] != "environment")
    first["t_convert"] = first["t"] - first["t_end"]
    return first[["fight_id", "converted_by", "converter_team", "t_convert"]]


def label_storm_death(pairs: pd.DataFrame, players: pd.DataFrame, positions: pd.DataFrame,
                      convert_s: float) -> pd.Series:
    """Fight ids where a target player died in [t0, t_end + convert_s] with `in_storm` true at their last known flag."""
    tp = pairs[["fight_id", "match_id", "t0", "t_end", "target_players"]].assign(
        player=pairs["target_players"].str.split(";")).explode("player")
    pl = _objects(players[["match_id", "player_id", "death_time"]].dropna(subset=["death_time"]), "match_id", "player_id")
    m = _objects(tp, "match_id", "player").merge(pl, left_on=["match_id", "player"], right_on=["match_id", "player_id"])
    m = m[(m["death_time"] >= m["t0"]) & (m["death_time"] <= m["t_end"] + convert_s)]
    if m.empty:
        return pd.Series([], dtype=object)
    flag = positions.loc[positions["in_storm"].notna(), ["match_id", "player_id", "t", "in_storm"]]
    if flag.empty:
        return pd.Series([], dtype=object)
    flag = _objects(flag, "match_id", "player_id").sort_values("t")
    left = m[["fight_id", "match_id", "player_id", "death_time"]].rename(columns={"death_time": "t"}).sort_values("t")
    got = pd.merge_asof(left, flag, on="t", by=["match_id", "player_id"], direction="backward")
    return got.loc[got["in_storm"].fillna(False).astype(bool), "fight_id"].drop_duplicates()


def label_structure_pressure(pairs: pd.DataFrame, damage: pd.DataFrame, teams: pd.DataFrame, positions: pd.DataFrame,
                             radius_uu: float, max_age_s: float = HIT_POS_MAX_AGE_S) -> pd.DataFrame:
    """Structure damage (`target` null, magnitude > 0) by the poking team during [t0, t_end] that lands within
    `radius_uu` horizontally of a target player's position (last update at most `max_age_s` old)."""
    s = damage[damage["target"].isna() & damage["source"].notna() & (damage["magnitude"] > 0)
               & damage["x"].notna() & damage["y"].notna()][["match_id", "t", "source", "magnitude", "x", "y"]]
    s = _objects(s, "match_id", "source").reset_index(drop=True)
    s["team"] = team_at(s, "source", "t", teams)
    s = s.dropna(subset=["team"]).astype({"team": int})
    s_by = {m: g.sort_values("t") for m, g in s.groupby("match_id")}
    pos = _objects(positions[["match_id", "player_id", "t", "x", "y"]].dropna(subset=["player_id"]),
                   "match_id", "player_id")
    wanted = _objects(pairs[["match_id", "target_players"]].assign(
        player_id=pairs["target_players"].str.split(";")).explode("player_id")[["match_id", "player_id"]],
        "match_id", "player_id").drop_duplicates()
    pos = pos.merge(wanted, on=["match_id", "player_id"]).sort_values("t")
    pos_by = {k: (g["t"].to_numpy(), g["x"].to_numpy(), g["y"].to_numpy()) for k, g in pos.groupby(["match_id", "player_id"])}
    rows = []
    for r in pairs.itertuples():
        g = s_by.get(r.match_id)
        dmg = hits = 0
        if g is not None:
            w = g[(g["t"] >= r.t0) & (g["t"] <= r.t_end) & (g["team"] == r.poker_team)]
            tracks = [pos_by[(r.match_id, p)] for p in r.target_players.split(";") if (r.match_id, p) in pos_by]
            for t, x, y, mag in zip(w["t"], w["x"], w["y"], w["magnitude"]):
                for tt, tx, ty in tracks:
                    j = np.searchsorted(tt, t, side="right") - 1
                    if j >= 0 and t - tt[j] <= max_age_s and np.hypot(tx[j] - x, ty[j] - y) <= radius_uu:
                        dmg += mag
                        hits += 1
                        break
        rows.append((r.fight_id, dmg, hits))
    return pd.DataFrame(rows, columns=["fight_id", "structure_damage", "structure_hits"])


def build_pokes(
    damage: pd.DataFrame, teams: pd.DataFrame, elims: pd.DataFrame, players: pd.DataFrame, positions: pd.DataFrame,
    fight_sides: pd.DataFrame, *, gap_s: float = GAP_S, overlap_tol_s: float = OVERLAP_TOL_S,
    grace_s: float = GRACE_S, poke_minority_share: float = POKE_MINORITY_SHARE, convert_s: float = POKE_CONVERT_S,
    structure_radius_tiles: float = STRUCTURE_RADIUS_TILES,
) -> pd.DataFrame:
    """One row per poke (`fight_sides.engagement_type == 'poke'`): the `pokes` table.

    `gap_s` and `overlap_tol_s` must match the parameters `fight_sides` was built with (fight ids are only
    stable under the same segmentation); a mismatch raises.
    """
    ids = set(fight_sides.loc[fight_sides["engagement_type"] == "poke", "fight_id"])
    eng = group_fights(engagement_damage(damage, teams), gap_s, overlap_tol_s)
    if not ids <= set(eng["fight_id"]):
        raise ValueError("fight_sides was built with a different segmentation than gap_s/overlap_tol_s")
    eng = eng[eng["fight_id"].isin(ids)]
    if eng.empty:
        return pd.DataFrame({c: [] for c in POKE_COLUMNS})
    pairs = poke_pairs(eng)
    conv = label_conversion(pairs, elims, teams, convert_s)
    storm = set(label_storm_death(pairs, players, positions, convert_s))
    struct = label_structure_pressure(pairs, damage, teams, positions, structure_radius_tiles * TILE_UU)
    out = pairs.merge(conv, on="fight_id", how="left").merge(struct, on="fight_id", how="left")
    out["converted"] = out["converted_by"].notna()
    out["storm_death"] = out["fight_id"].isin(storm)
    out["seg_version"] = seg_version(gap_s, overlap_tol_s, grace_s, poke_minority_share, convert_s)
    out = out.sort_values(["match_id", "t0", "fight_id"], kind="stable").reset_index(drop=True)
    return out[POKE_COLUMNS]
