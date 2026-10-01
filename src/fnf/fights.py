"""Fight segmentation, v0: from the kill feed only.

A fight is a connected group of knock/elim events within one match, where two
events are linked if they share a player and are at most `gap_ms` apart.
This undercounts fights (any fight with no knock is invisible) and has no team
info. Once packet parsing works, replace it with damage-event segmentation,
which also sees fights that end without a knock.
"""

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
