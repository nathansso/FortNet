"""Phase 4 sensitivity sweeps for fight segmentation (handoff 02).

For GAP_S x GRACE_S x OVERLAP_TOL_S: number of fights, multi-team share, outcome shares of two-team sides,
duration percentiles, recorder-knock coverage. Then fight/pick/poke shares by POKE_MINORITY_SHARE and poke
conversion by POKE_CONVERT_S.

Usage: uv run python scripts/sweep_fights.py
"""

import argparse
import itertools

import numpy as np
import pandas as pd

from fnf import DATA
from fnf.pokes import build_pokes
from fnf.fights import (
    GRACE_S, POKE_CONVERT_S, POKE_MINORITY_SHARE, build_fight_sides, recorder_knock_coverage,
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


def type_sweep(fs: pd.DataFrame) -> None:
    """fight / pick / poke shares by POKE_MINORITY_SHARE, from stored `mutual`, `minority_damage_share`, `outcome`."""
    print(f"\n== engagement type sweep (current POKE_MINORITY_SHARE={POKE_MINORITY_SHARE:g}); shares are % of fights ==")
    f = fs.drop_duplicates("fight_id").set_index("fight_id")
    decisive = fs["outcome"].ne("disengage").groupby(fs["fight_id"]).any().reindex(f.index)
    print(f"fights {len(f):,}; mutual {100 * f['mutual'].mean():.1f}%; "
          f"median distance known for {100 * f['dist_median_m'].notna().mean():.1f}%")
    rows = {}
    for share in (0.0, 0.05, 0.10, 0.15, 0.20, 0.30):
        one_sided = ~(f["mutual"] & (f["minority_damage_share"] >= share))
        kind = np.where(~one_sided, "fight", np.where(decisive, "pick", "poke"))
        k = pd.Series(kind, index=f.index)
        two = ~f["multi_team"]
        dec = k[decisive]
        rows[f"share>={share:g}"] = {
            "fight %": 100 * (k == "fight").mean(), "pick %": 100 * (k == "pick").mean(),
            "poke %": 100 * (k == "poke").mean(),
            "decided fights that are picks %": 100 * (dec == "pick").mean(),
            "two-team: poke %": 100 * (k[two] == "poke").mean(),
        }
    print(pd.DataFrame(rows).round(1).to_string())
    decided = f[decisive]
    cur = decided["engagement_type"].value_counts()
    print(f"decided fights at the current setting: {len(decided):,} = " + ", ".join(f"{n} {c:,}" for n, c in cur.items()))
    for kind in ("fight", "pick", "poke"):
        x = f[f["engagement_type"] == kind]
        print(f"{kind}: {len(x):,} fights; median hits {(x['hits_dealt'] + x['hits_taken']).median() / 2:.0f} per side; "
              f"median shooter distance {x['dist_median_m'].median():.0f} m; two-team {100 * (~x['multi_team']).mean():.0f}%")


def convert_sweep(damage, teams, elims, players, positions, fs) -> None:
    """Poke outcome labels by POKE_CONVERT_S. Conversions count only after the grace window."""
    print(f"\n== poke outcome sweep (current POKE_CONVERT_S={POKE_CONVERT_S:g}; conversions after GRACE_S only) ==")
    rows = {}
    for conv in (10, 20, 30, 45):
        pk = build_pokes(damage, teams, elims, players, positions, fs, convert_s=conv)
        rows[f"conv {conv}s"] = {
            "pokes": len(pk), "converted %": 100 * pk["converted"].mean(),
            "by poker %": 100 * (pk["converted_by"] == "poker").mean(),
            "by third party %": 100 * (pk["converted_by"] == "third_party").mean(),
            "environment %": 100 * (pk["converted_by"] == "environment").mean(),
            "storm_death": int(pk["storm_death"].sum()),
            "structure hits>0": int((pk["structure_hits"] > 0).sum()),
        }
    print(pd.DataFrame(rows).round(1).to_string())
    pk = build_pokes(damage, teams, elims, players, positions, fs)
    print(f"net damage median {pk['net_damage'].median():.0f}; converted t_convert median "
          f"{pk['t_convert'].median():.1f}s")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--skip-grid", action="store_true", help="skip the 48-cell GAP/TOL/GRACE grid (about 2 min)")
    args = ap.parse_args()
    damage, teams, elims, players, matches, positions = (
        read(n) for n in ("damage", "teams", "elims", "players", "matches", "positions"))
    pd.set_option("display.width", 250, "display.max_rows", 200)
    if not args.skip_grid:
        res = sweep(damage, teams, elims, players, matches)
        fmt = res.copy()
        for c in ("multi", "win", "loss", "tie", "disengage", "in_fight", "coverage"):
            fmt[c] = (100 * fmt[c]).round(1)
        for c in ("dur_p50", "dur_p90", "dur_max"):
            fmt[c] = fmt[c].round(1)
        print("== sweep (shares in %; win/loss/tie/disengage over two-team sides) ==")
        print(fmt.to_string(index=False))
    fs = build_fight_sides(damage, teams, elims, players, matches, positions)
    type_sweep(fs)
    convert_sweep(damage, teams, elims, players, positions, fs)


if __name__ == "__main__":
    main()
