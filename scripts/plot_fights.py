"""Render fights to PNGs for visual review (handoff 02, Phase 4).

Default mode: random recorder-involved fights. Top-down tracks of every engaged player from t0-5 s to
t_end+5 s (colored by team), damage as source->target arrows, knocks between the fight's teams as black X at the
victim, title with outcome, type and duration. Output: data/reports/fights/ (git-ignored).

--split-contrast ALT_GAP: instead pick fights that are ONE fight at --gap-s but split into 2+ fights at ALT_GAP
(same tolerance), so the GAP_S choice can be judged. Left: tracks and arrows colored by the ALT_GAP sub-fight;
right: timeline of hits (one row per shooter team), knocks as dashed lines. Output: data/reports/fights_split/.

Usage: uv run python scripts/plot_fights.py [--n 12] [--seed 0] [--gap-s 10 --tol-s 1 --grace-s 3]
                                            [--outcome win] [--split-contrast 5]
"""

import argparse
import shutil

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from fnf import DATA  # noqa: E402
from fnf.fights import (  # noqa: E402
    GAP_S, GRACE_S, OVERLAP_TOL_S, build_fight_sides, engagement_damage, group_fights, outcome_events,
)

P = DATA / "processed"
PAD_S = 5.0
COLORS = ["#1f77b4", "#d62728", "#2ca02c", "#ff7f0e", "#9467bd", "#8c564b", "#e377c2", "#17becf"]
SUB_COLORS = ["#e41a1c", "#377eb8", "#4daf4a", "#984ea3", "#ff7f00", "#a65628"]


def read(name: str, **kw) -> pd.DataFrame:
    return pd.read_parquet(P / f"{name}.parquet", **kw)


def draw(fid, fs, eng, ev, owner, pos, args, path, sub=None) -> None:
    """Draw one fight. `sub` maps engagement-row index -> sub-fight label (contrast mode)."""
    sides = fs[fs["fight_id"] == fid]
    m = sides["match_id"].iloc[0]
    t0, t_end = sides["t0"].iloc[0], sides["t_end"].iloc[0]
    players_here = {p for s in sides["players"] for p in s.split(";")}
    team_of = {p: int(t) for t, s in zip(sides["team_index"], sides["players"]) for p in s.split(";")}
    color = {t: COLORS[i % len(COLORS)] for i, t in enumerate(sorted(sides["team_index"]))}
    lo, hi = t0 - PAD_S, t_end + PAD_S
    rows = eng[eng["fight_id"] == fid]

    if sub is None:
        fig, ax = plt.subplots(figsize=(8, 8))
        axt = None
    else:
        fig, (ax, axt) = plt.subplots(1, 2, figsize=(15, 7), gridspec_kw={"width_ratios": [1, 1]})
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

    def at(p, t):
        tr = tracks.get(p)
        if tr is None:
            return None
        return np.interp(t, tr["t"], tr["x"]) / 100, np.interp(t, tr["t"], tr["y"]) / 100

    labels = sorted(set(sub.loc[rows.index])) if sub is not None else []
    sub_color = {s: SUB_COLORS[i % len(SUB_COLORS)] for i, s in enumerate(labels)}
    for r in rows.itertuples():
        a, b = at(r.source, r.t), at(r.target, r.t)
        c = sub_color[sub[r.Index]] if sub is not None else color[r.source_team]
        if a and b:
            ax.annotate("", xy=b, xytext=a, arrowprops=dict(arrowstyle="->", color=c, lw=0.8, alpha=0.6))
        if axt is not None:
            axt.plot(r.t - t0, r.source_team, "o", color=c, ms=4)
    evm = ev[(ev["match_id"] == m) & (ev["t"] >= lo) & (ev["t"] <= hi + args.grace_s)
             & ev["victim_team"].isin(color) & ev["killer_team"].isin(color)]
    for r in evm.itertuples():
        pt = at(r.eliminated, r.t)
        if pt:
            ax.plot(*pt, "kX", ms=11)
            ax.annotate(f"knock t={r.t - t0:+.1f}s", pt, fontsize=7, xytext=(6, 6), textcoords="offset points")
        if axt is not None:
            axt.axvline(r.t - t0, color="k", ls="--", lw=1)
            axt.annotate(f"knock (team {r.victim_team} down)", (r.t - t0, max(color)), fontsize=7, rotation=90)
    outcomes = ", ".join(f"team {t}: {o}" for t, o in zip(sides["team_index"], sides["outcome"]))
    ax.set_title(f"{fid[-26:]}\n{outcomes}\n{sides['engagement_type'].iloc[0]}, duration {t_end - t0:.1f}s, "
                 f"t0={t0:.1f}s{', multi-team' if sides['multi_team'].iloc[0] else ''}", fontsize=9)
    ax.set_aspect("equal")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    if axt is not None:
        axt.set_yticks(sorted(color))
        axt.set_ylabel("shooter team")
        axt.set_xlabel("seconds since t0")
        axt.set_title("hits by shooter team; color = sub-fight at the smaller GAP_S\n" + ", ".join(
            f"{s}: {sub_color[s]}" for s in labels), fontsize=8)
        gaps = sorted(rows["t"] - t0)
        axt.set_xlim(min(gaps) - 1, max(gaps) + 1)
    fig.savefig(path, dpi=110, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--gap-s", type=float, default=GAP_S)
    ap.add_argument("--tol-s", type=float, default=OVERLAP_TOL_S)
    ap.add_argument("--grace-s", type=float, default=GRACE_S)
    ap.add_argument("--outcome", choices=["win", "loss", "tie", "disengage"], help="only fights with this outcome")
    ap.add_argument("--split-contrast", type=float, metavar="ALT_GAP",
                    help="pick fights that are one fight at --gap-s but 2+ fights at ALT_GAP")
    args = ap.parse_args()

    damage, teams, elims, players, matches, positions = (
        read(n) for n in ("damage", "teams", "elims", "players", "matches", "positions"))
    fs = build_fight_sides(damage, teams, elims, players, matches, positions, gap_s=args.gap_s,
                           overlap_tol_s=args.tol_s, grace_s=args.grace_s)
    base = engagement_damage(damage, teams)
    eng = group_fights(base, args.gap_s, args.tol_s)
    size = teams.groupby(["match_id", "team_index"])["player_id"].nunique().groupby("match_id").max()
    ev = outcome_events(elims, teams, set(size[size <= 1].index))

    sub = None
    cand = fs[fs["recorder_involved"]]
    if args.split_contrast is not None:
        alt = group_fights(base, args.split_contrast, args.tol_s)
        # same sort in both calls, so rows align positionally
        assert (alt[["match_id", "t", "source", "target"]].to_numpy() == eng[["match_id", "t", "source", "target"]]
                .to_numpy()).all()
        sub = alt["fight_id"].str.rsplit(":", n=1).str[1].radd("alt#")
        sub.index = eng.index
        n_alt = eng.assign(sub=sub).groupby("fight_id")["sub"].nunique()
        split_ids = set(n_alt[n_alt >= 2].index)
        print(f"fights at gap {args.gap_s:g} that split into 2+ at gap {args.split_contrast:g}: {len(split_ids):,} of "
              f"{fs['fight_id'].nunique():,} ({sum(fs.drop_duplicates('fight_id')['recorder_involved'] & fs.drop_duplicates('fight_id')['fight_id'].isin(split_ids))} recorder-involved)")
        cand = cand[cand["fight_id"].isin(split_ids)]
    if args.outcome:
        cand = cand[cand["fight_id"].isin(fs.loc[fs["outcome"] == args.outcome, "fight_id"])]
    ids = sorted(cand["fight_id"].unique())
    rng = np.random.default_rng(args.seed)
    pick = sorted(rng.choice(ids, size=min(args.n, len(ids)), replace=False))
    out_dir = DATA / "reports" / ("fights_split" if sub is not None else "fights")
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    owner = matches.set_index("match_id")["replay_owner"]
    pos_cache: dict[str, pd.DataFrame] = {}
    for fid in pick:
        m = fs.loc[fs["fight_id"] == fid, "match_id"].iloc[0]
        if m not in pos_cache:
            pos_cache[m] = read("positions", columns=["match_id", "t", "player_id", "x", "y"],
                                filters=[("match_id", "==", m)])
        draw(fid, fs, eng, ev, owner, pos_cache[m], args, out_dir / (fid.replace(":", "_").replace(" ", "") + ".png"),
             sub)
    print(f"wrote {len(pick)} plots to {out_dir}")
    print(fs[fs["fight_id"].isin(pick)].groupby("fight_id").agg(
        outcome=("outcome", "/".join), type=("engagement_type", "first"), multi=("multi_team", "first")).to_string())


if __name__ == "__main__":
    main()
