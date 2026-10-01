"""Render random recorder-involved fights to PNGs for visual review (handoff 02, Phase 4.2).

Top-down tracks of every engaged player from t0-5 s to t_end+5 s (colored by team), damage as source->target
segments, knocks between the fight's teams marked with black X at the victim, title with outcome and duration.
Output: data/reports/fights/ (git-ignored).

Usage: uv run python scripts/plot_fights.py [--n 12] [--seed 0] [--gap-s 10 --tol-s 1 --grace-s 3]
"""

import argparse

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from fnf import DATA  # noqa: E402
from fnf.fights import (  # noqa: E402
    GAP_S, GRACE_S, OVERLAP_TOL_S, TIE_S, build_fight_sides, engagement_damage, group_fights, outcome_events,
)

P = DATA / "processed"
PAD_S = 5.0
COLORS = ["#1f77b4", "#d62728", "#2ca02c", "#ff7f0e", "#9467bd", "#8c564b", "#e377c2", "#17becf"]


def read(name: str, **kw) -> pd.DataFrame:
    return pd.read_parquet(P / f"{name}.parquet", **kw)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--gap-s", type=float, default=GAP_S)
    ap.add_argument("--tol-s", type=float, default=OVERLAP_TOL_S)
    ap.add_argument("--grace-s", type=float, default=GRACE_S)
    ap.add_argument("--outcome", choices=["win", "loss", "tie", "disengage"], help="only fights with this outcome")
    args = ap.parse_args()

    damage, teams, elims, players, matches = (read(n) for n in ("damage", "teams", "elims", "players", "matches"))
    fs = build_fight_sides(damage, teams, elims, players, matches, gap_s=args.gap_s, overlap_tol_s=args.tol_s,
                           grace_s=args.grace_s)
    eng = group_fights(engagement_damage(damage, teams), args.gap_s, args.tol_s)
    size = teams.groupby(["match_id", "team_index"])["player_id"].nunique().groupby("match_id").max()
    ev = outcome_events(elims, teams, set(size[size <= 1].index))

    cand = fs[fs["recorder_involved"]]
    if args.outcome:
        cand = cand[cand["fight_id"].isin(fs.loc[fs["outcome"] == args.outcome, "fight_id"])]
    ids = sorted(cand["fight_id"].unique())
    rng = np.random.default_rng(args.seed)
    pick = sorted(rng.choice(ids, size=min(args.n, len(ids)), replace=False))
    out_dir = DATA / "reports" / "fights"
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("*.png"):
        old.unlink()

    owner = matches.set_index("match_id")["replay_owner"]
    pos_cache: dict[str, pd.DataFrame] = {}
    for fid in pick:
        sides = fs[fs["fight_id"] == fid]
        m = sides["match_id"].iloc[0]
        t0, t_end = sides["t0"].iloc[0], sides["t_end"].iloc[0]
        if m not in pos_cache:
            pos_cache[m] = read("positions", columns=["match_id", "t", "player_id", "x", "y"],
                                filters=[("match_id", "==", m)])
        pos = pos_cache[m]
        players_here = {p for s in sides["players"] for p in s.split(";")}
        team_of = {p: int(t) for t, s in zip(sides["team_index"], sides["players"]) for p in s.split(";")}
        color = {t: COLORS[i % len(COLORS)] for i, t in enumerate(sorted(sides["team_index"]))}
        lo, hi = t0 - PAD_S, t_end + PAD_S

        fig, ax = plt.subplots(figsize=(8, 8))
        tracks = {}
        for p in players_here:
            tr = pos[(pos["player_id"] == p) & (pos["t"] >= lo) & (pos["t"] <= hi)].sort_values("t")
            if tr.empty:
                continue
            tracks[p] = tr
            c = color[team_of[p]]
            ax.plot(tr["x"] / 100, tr["y"] / 100, "-", color=c, lw=1.2, alpha=0.8)
            ax.plot(tr["x"].iloc[0] / 100, tr["y"].iloc[0] / 100, "o", color=c, ms=5)
            ax.plot(tr["x"].iloc[-1] / 100, tr["y"].iloc[-1] / 100, "s", color=c, ms=5)
            ax.annotate(("REC " if p == owner.get(m) else "") + p[:4], (tr["x"].iloc[-1] / 100, tr["y"].iloc[-1] / 100),
                        fontsize=7, color=c)

        def at(p: str, t: float):
            tr = tracks.get(p)
            if tr is None:
                return None
            return np.interp(t, tr["t"], tr["x"]) / 100, np.interp(t, tr["t"], tr["y"]) / 100

        for r in eng[eng["fight_id"] == fid].itertuples():
            a, b = at(r.source, r.t), at(r.target, r.t)
            if a and b:
                ax.annotate("", xy=b, xytext=a, arrowprops=dict(arrowstyle="->", color=color[r.source_team],
                                                              lw=0.6, alpha=0.5))
        evm = ev[(ev["match_id"] == m) & (ev["t"] >= lo) & (ev["t"] <= hi + args.grace_s)
                 & ev["victim_team"].isin(color) & ev["killer_team"].isin(color)]
        for r in evm.itertuples():
            pt = at(r.eliminated, r.t)
            if pt:
                ax.plot(*pt, "kX", ms=11)
                ax.annotate(f"knock t={r.t - t0:+.1f}s", pt, fontsize=7, xytext=(6, 6), textcoords="offset points")
        labels = ", ".join(f"team {t}: {o}" for t, o in zip(sides["team_index"], sides["outcome"]))
        ax.set_title(f"{fid[-26:]}\n{labels}\nduration {t_end - t0:.1f}s, t0={t0:.1f}s"
                     f"{', multi-team' if sides['multi_team'].iloc[0] else ''}", fontsize=9)
        ax.set_aspect("equal")
        ax.set_xlabel("x (m)")
        ax.set_ylabel("y (m)")
        fig.savefig(out_dir / (fid.replace(":", "_").replace(" ", "") + ".png"), dpi=110, bbox_inches="tight")
        plt.close(fig)
    print(f"wrote {len(pick)} plots to {out_dir}")
    print(fs[fs["fight_id"].isin(pick)].groupby("fight_id").agg(
        outcome=("outcome", "/".join), multi=("multi_team", "first")).to_string())


if __name__ == "__main__":
    main()
