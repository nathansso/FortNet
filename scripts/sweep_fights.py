"""Phase 4 sensitivity sweep and v0-vs-v1 comparison for fight segmentation (handoff 02).

For GAP_S x GRACE_S x OVERLAP_TOL_S: number of fights, multi-team share, outcome shares of two-team sides,
duration percentiles, recorder-knock coverage. Then: how many kill-feed v0 fights with a knock a v1 fight matches.

Usage: uv run python scripts/sweep_fights.py
"""

import itertools

import numpy as np
import pandas as pd

from fnf import DATA
from fnf.fights import (
    GAP_S, GRACE_S, OVERLAP_TOL_S, build_fight_sides, engagement_damage, group_fights, recorder_knock_coverage,
)

P = DATA / "processed"


def read(name: str) -> pd.DataFrame:
    return pd.read_parquet(P / f"{name}.parquet")


def sweep(damage, teams, elims, players, matches) -> pd.DataFrame:
    rows = []
    for gap, tol, grace in itertools.product((5, 10, 15, 20), (0, 1, 2, 3), (1, 3, 5)):
        fs = build_fight_sides(damage, teams, elims, players, matches, gap_s=gap, overlap_tol_s=tol, grace_s=grace)
        f = fs.drop_duplicates("fight_id")
        two = fs[~fs["multi_team"]]
        dur = (f["t_end"] - f["t0"]).to_numpy()
        cov = recorder_knock_coverage(elims, fs, teams, matches, grace_s=grace)
        share = two["outcome"].value_counts(normalize=True)
        rows.append({
            "gap": gap, "tol": tol, "grace": grace, "fights": len(f), "multi": f["multi_team"].mean(),
            "win": share.get("win", 0), "loss": share.get("loss", 0), "tie": share.get("tie", 0),
            "disengage": share.get("disengage", 0),
            "labelled_2team": int((two["outcome"].isin(["win", "loss"])).sum() // 2),
            "dur_p50": np.median(dur), "dur_p90": np.quantile(dur, 0.9), "dur_max": dur.max(),
            "in_fight": cov["in_fight"].mean(), "coverage": cov["covered"].mean(),
        })
    return pd.DataFrame(rows)


def v0_vs_v1(damage, teams, elims, players, matches, fights_v0, fs) -> None:
    """Share of v0 fights with a knock that overlap (time, with GRACE_S) and share a player with a v1 fight."""
    ek = elims.copy()
    ek["t"] = ek["t_ms"] / 1000
    v0 = ek.groupby("fight_id").agg(match_id=("match_id", "first"), t_start=("t", "min"), t_end=("t", "max"),
                                    knocks=("knocked", "sum"))
    v0 = v0[v0["knocks"] > 0]
    pl = ek.groupby("fight_id").apply(lambda d: set(d["eliminator"]) | set(d["eliminated"]), include_groups=False)
    v1 = fs.groupby("fight_id").agg(match_id=("match_id", "first"), t0=("t0", "first"), t_end=("t_end", "first"))
    v1_players = fs.groupby("fight_id")["players"].apply(lambda s: set(";".join(s).split(";")))
    by_match = {m: g for m, g in v1.groupby("match_id")}
    owner = matches.set_index("match_id")["replay_owner"]
    dmg_by = {k: g["t"].to_numpy() for k, g in damage[damage["target"].notna()].sort_values("t")
              .groupby(["match_id", "target"])}
    miss = []
    for fid, r in v0.iterrows():
        g = by_match.get(r["match_id"])
        ok = False
        if g is not None:
            for v in g.index[(g["t0"] <= r["t_end"] + GRACE_S) & (g["t_end"] + GRACE_S >= r["t_start"])]:
                if pl[fid] & v1_players[v]:
                    ok = True
                    break
        if not ok:
            ps = pl[fid]
            any_dmg = False
            for p in ps:
                ts = dmg_by.get((r["match_id"], p))
                if ts is not None and ((ts >= r["t_start"] - 30) & (ts <= r["t_end"] + GRACE_S)).any():
                    any_dmg = True
            miss.append({"fight_id": fid, "recorder": owner.get(r["match_id"]) in ps, "any_damage_on_participants": any_dmg})
    miss = pd.DataFrame(miss)
    n, m = len(v0), len(miss)
    print(f"v0 fights with a knock: {n:,}; matched by a v1 fight: {n - m:,} ({100 * (n - m) / n:.1f}%); missed {m:,}")
    if m:
        print(f"  misses involving the recorder: {int(miss['recorder'].sum())}; "
              f"with some damage on a participant in [t_start-30s, t_end+grace] (filtered or other team): "
              f"{int(miss['any_damage_on_participants'].sum())}; no damage recorded at all: "
              f"{int((~miss['any_damage_on_participants']).sum())}")


def main() -> None:
    damage, teams, elims, players, matches = (read(n) for n in ("damage", "teams", "elims", "players", "matches"))
    pd.set_option("display.width", 250, "display.max_rows", 200)
    res = sweep(damage, teams, elims, players, matches)
    fmt = res.copy()
    for c in ("multi", "win", "loss", "tie", "disengage", "in_fight", "coverage"):
        fmt[c] = (100 * fmt[c]).round(1)
    for c in ("dur_p50", "dur_p90", "dur_max"):
        fmt[c] = fmt[c].round(1)
    print("== sweep (shares in %; win/loss/tie/disengage over two-team sides) ==")
    print(fmt.to_string(index=False))
    print(f"\n== v0 vs v1 at defaults (gap {GAP_S:g}, tol {OVERLAP_TOL_S:g}, grace {GRACE_S:g}) ==")
    fs = build_fight_sides(damage, teams, elims, players, matches)
    v0_vs_v1(damage, teams, elims, players, matches, None, fs)


if __name__ == "__main__":
    main()
