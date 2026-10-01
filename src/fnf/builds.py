"""Reconstruct building and editing from build-piece spawns (builds.csv).

Pieces are PBWA_<material><tier>_<shape>_C actors snapped to the build grid.
An edit replaces a piece with a different shape in the same cell, so edits
are recovered as shape changes within one cell.

Owner and editing-player fields exist on pieces but aren't replicated in
client replays, so the builder is inferred. Candidates are the players on the
piece's team at spawn time (everyone, if the team is unknown). For new pieces,
candidates holding the building tool win; edits don't change the held item,
so they fall straight to distance. Ties go to the nearest candidate.

On 1,142 Creative pieces with a known builder, and ignoring team, this picks
the right player 95% of the time: 89% where 2+ players were within ~2 tiles,
vs 67% for nearest-only.
"""

import re

import numpy as np
import pandas as pd

CLASS_RE = re.compile(r"^PBWA_(?P<mat>[A-Z])(?P<tier>\d)_(?P<shape>.+)_C$")
MATERIALS = {"W": "wood", "S": "brick", "M": "metal"}
DEFAULT_SHAPES = {"Solid": "wall", "Floor": "floor", "StairW": "stair", "RoofC": "cone"}
DUPLICATE_WINDOW_S = 0.2  # predicted spawn + confirmed respawn of the same piece
EDIT_WINDOW_S = 1.5  # max gap between old piece closing and edited piece appearing
MAX_BUILDER_DIST = 800.0  # ~1.5 tiles; farther than this, leave the builder unknown


def kind_of(shape: str) -> str:
    if shape in DEFAULT_SHAPES:
        return DEFAULT_SHAPES[shape]
    s = shape.lower()
    if s.startswith("stair"):
        return "stair"
    if s.startswith("roof"):
        return "cone"
    if s.startswith(("floor", "balcony")):
        return "floor"
    return "wall"  # archways, doors, windows, half walls, braces


def parse_pieces(builds: pd.DataFrame) -> pd.DataFrame:
    """Classify pieces and drop predicted-then-confirmed duplicate spawns."""
    m = builds["path"].str.extract(CLASS_RE)
    df = builds.assign(
        material=m["mat"].map(MATERIALS),
        shape=m["shape"],
        kind=m["shape"].map(kind_of, na_action="ignore"),
        edited=~m["shape"].isin(DEFAULT_SHAPES.keys()),
    ).sort_values(["match_id", "spawn_t"], ignore_index=True)

    # A predicted spawn closes almost immediately and the confirmed piece respawns
    # in the same spot: keep the confirmed row, but with the predicted spawn time.
    key = ["match_id", "path", "x", "y", "z", "yaw"]
    df["predicted"] = (df.groupby(key, dropna=False)["spawn_t"].shift(-1) - df["close_t"]).abs() <= DUPLICATE_WINDOW_S
    grp = df.groupby(key, dropna=False)
    prev_predicted_spawn = grp["spawn_t"].shift().where(grp["predicted"].shift(fill_value=False))
    df["spawn_t"] = prev_predicted_spawn.fillna(df["spawn_t"])
    return df.loc[~df["predicted"]].drop(columns="predicted").reset_index(drop=True)


def detect_edits(pieces: pd.DataFrame) -> pd.DataFrame:
    """Pair each piece with the piece it replaced in the same cell (an edit or edit reset)."""
    cell = ["match_id", "x", "y", "z", "kind"]
    out = pieces.sort_values([*cell, "spawn_t"]).copy()
    grp = out.groupby(cell, dropna=False)
    out["prev_shape"] = grp["shape"].shift()
    out["prev_close_t"] = grp["close_t"].shift()
    replaced = (
        out["prev_shape"].notna()
        & (out["prev_shape"] != out["shape"])
        & ((out["spawn_t"] - out["prev_close_t"]).abs() <= EDIT_WINDOW_S)
    )
    out["is_edit"] = replaced & out["edited"]
    out["is_reset"] = replaced & ~out["edited"]
    return out.sort_values(["match_id", "spawn_t"], ignore_index=True)


def _asof_by_player(times: pd.Series, events: pd.DataFrame, cols: list[str]) -> dict[str, pd.DataFrame]:
    """Per player, the last event at or before each time (times must be sorted)."""
    out = {}
    for player, ev in events.groupby("player_id"):
        out[player] = pd.merge_asof(times.to_frame("t0"), ev[["t", *cols]], left_on="t0", right_on="t", direction="backward")
    return out


def attribute_builders(
    pieces: pd.DataFrame,
    positions: pd.DataFrame,
    teams: pd.DataFrame,
    weapons: pd.DataFrame | None = None,
    max_dist: float = MAX_BUILDER_DIST,
) -> pd.DataFrame:
    """Add `builder`, `builder_dist` and `builder_source` to pieces.

    `builder_source`: "team" (the only team member), "team+tool" or "team+nearest"
    (several team members), "tool" or "nearest" (team unknown; only within
    max_dist), None (no candidate).
    """
    pos = positions.dropna(subset=["player_id"]).sort_values("t")
    tms = teams.sort_values("t")
    wps = pd.DataFrame(columns=["match_id", "t", "player_id", "tool"])
    if weapons is not None and not weapons.empty:
        wps = weapons.dropna(subset=["player_id"]).sort_values("t").assign(
            tool=lambda d: d["weapon_class"].fillna("").str.contains("BuildingTool")
        )

    parts = []
    for match_id, pc in pieces.groupby("match_id", sort=False):
        pc = pc.sort_values("spawn_t")
        t0 = pc["spawn_t"].reset_index(drop=True)
        where = _asof_by_player(t0, pos[pos["match_id"] == match_id], ["x", "y", "z"])
        team_at = _asof_by_player(t0, tms[tms["match_id"] == match_id], ["team_index"])
        tool_at = _asof_by_player(t0, wps[wps["match_id"] == match_id], ["tool"])

        players = list(where)
        n = len(pc)
        dist = np.full((n, len(players)), np.inf)
        on_team = np.zeros((n, len(players)), bool)
        tool = np.zeros((n, len(players)), bool)
        piece_team = pc["team_index"].to_numpy() if "team_index" in pc else np.full(n, np.nan)
        for k, p in enumerate(players):
            w = where[p]
            d = np.sqrt((w["x"].to_numpy() - pc["x"].to_numpy()) ** 2
                        + (w["y"].to_numpy() - pc["y"].to_numpy()) ** 2
                        + (w["z"].to_numpy() - pc["z"].to_numpy()) ** 2)
            dist[:, k] = np.nan_to_num(d, nan=np.inf)
            if p in team_at:
                on_team[:, k] = team_at[p]["team_index"].to_numpy() == piece_team
            if p in tool_at:
                tool[:, k] = tool_at[p]["tool"].astype("boolean").fillna(False).to_numpy()

        team_known = on_team.any(axis=1)
        new_piece = ~(pc["is_edit"] | pc["is_reset"]).to_numpy() if "is_edit" in pc else np.ones(n, bool)
        # Lexicographic score: off-team (when team is known) >> not holding the tool (new pieces) >> distance.
        score = (
            np.where(team_known[:, None] & ~on_team, 1e12, 0.0)
            + np.where(new_piece[:, None] & ~tool, 1e6, 0.0)
            + np.minimum(dist, 1e5)
        )
        builder = np.full(n, None, dtype=object)
        builder_dist = np.full(n, np.inf)
        source = np.full(n, None, dtype=object)
        if players:
            best = score.argmin(axis=1)
            rows = np.arange(n)
            builder_dist = dist[rows, best]
            chosen_tool = tool[rows, best] & new_piece
            n_team = on_team.sum(axis=1)
            for i in range(n):
                if team_known[i]:
                    builder[i] = players[best[i]]
                    source[i] = "team" if n_team[i] == 1 else ("team+tool" if chosen_tool[i] else "team+nearest")
                elif builder_dist[i] <= max_dist:
                    builder[i] = players[best[i]]
                    source[i] = "tool" if chosen_tool[i] else "nearest"
        parts.append(pc.assign(builder=builder, builder_dist=builder_dist, builder_source=source))
    if not parts:
        return pieces.assign(builder=None, builder_dist=np.nan, builder_source=None)
    return pd.concat(parts, ignore_index=True)
