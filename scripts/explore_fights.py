"""Phase 1 exploration for damage-based fight segmentation (handoff 02). Deterministic, prints numbers.

Reproduces the handoff's measured facts, then answers the four open questions (overlap, recorder-knock
coverage, solos/no-knock eliminations, bots). Not library code: the logic that survives lives in fnf/fights.py.

Usage: uv run python scripts/explore_fights.py
"""

import numpy as np
import pandas as pd

from fnf import DATA

P = DATA / "processed"
GAP_S = 10.0
GRACE_S = 3.0


def pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def load():
    d = pd.read_parquet(P / "damage.parquet")
    return (
        d, pd.read_parquet(P / "elims.parquet"), pd.read_parquet(P / "teams.parquet"),
        pd.read_parquet(P / "players.parquet"), pd.read_parquet(P / "matches.parquet"),
    )


def team_at(df: pd.DataFrame, col: str, teams: pd.DataFrame, t_col: str = "t") -> pd.Series:
    """Team of `df[col]` at `df[t_col]`: last assignment at or before t, per match and player."""
    left = df[["match_id", t_col, col]].rename(columns={col: "player_id", t_col: "t"}).reset_index()
    left = left.dropna(subset=["player_id"]).sort_values("t")
    right = teams.sort_values("t")[["match_id", "player_id", "t", "team_index"]]
    out = pd.merge_asof(left, right, on="t", by=["match_id", "player_id"], direction="backward")
    return out.set_index("index")["team_index"].reindex(df.index)


def engagement(d: pd.DataFrame, teams: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    stats = {"rows": len(d), "target_null": d["target"].isna().mean(), "mag0": (d["magnitude"] == 0).mean()}
    pp = d[d["target"].notna() & d["source"].notna()]
    stats["self"] = (pp["source"] == pp["target"]).sum() / len(d)
    pp = pp[(pp["source"] != pp["target"]) & (pp["magnitude"] > 0)].copy()
    stats["engagement_rows"] = len(pp)
    pp["st"] = team_at(pp, "source", teams)
    pp["tt"] = team_at(pp, "target", teams)
    stats["team_resolved"] = (pp["st"].notna() & pp["tt"].notna()).mean()
    pp = pp.dropna(subset=["st", "tt"])
    stats["friendly"] = (pp["st"] == pp["tt"]).mean()
    pp = pp[pp["st"] != pp["tt"]].astype({"st": int, "tt": int})
    pp["ta"] = pp[["st", "tt"]].min(axis=1)
    pp["tb"] = pp[["st", "tt"]].max(axis=1)
    return pp.sort_values(["match_id", "t"]).reset_index(drop=True), stats


def segments(eng: pd.DataFrame, gap_s: float) -> pd.DataFrame:
    """Team-pair segments: new segment when the gap between consecutive hits of the pair exceeds gap_s."""
    e = eng.sort_values(["match_id", "ta", "tb", "t"])
    key = ["match_id", "ta", "tb"]
    new = e.groupby(key)["t"].diff().gt(gap_s) | e.groupby(key)["t"].diff().isna()
    e = e.assign(seg=new.cumsum())
    return e.groupby("seg").agg(
        match_id=("match_id", "first"), ta=("ta", "first"), tb=("tb", "first"),
        t_start=("t", "min"), t_end=("t", "max"), n=("t", "size"),
    ).reset_index(drop=True)


def main() -> None:
    d, elims, teams, players, matches = load()
    eng, st = engagement(d, teams)

    print("== Facts (handoff: 159,724 / 74.6% / 42.5% / 36,076 / 100% / 0.03%) ==")
    print(f"damage rows {st['rows']:,}; target null {pct(st['target_null'])}; magnitude 0 {pct(st['mag0'])}; self-hits {pct(st['self'])}")
    print(f"engagement rows {st['engagement_rows']:,}; team resolved {pct(st['team_resolved'])}; friendly fire {pct(st['friendly'])}")
    print(f"after dropping friendly fire: {len(eng):,} rows")

    gaps = eng.groupby(["match_id", "ta", "tb"])["t"].diff().dropna()
    print("gap between consecutive hits of a team pair (s): "
          + ", ".join(f"p{q}={gaps.quantile(q / 100):.1f}" for q in (50, 75, 90, 95, 99)))
    n_pairs = len(eng.groupby(["match_id", "ta", "tb"]))
    print("team-pair segments by gap: " + ", ".join(f"{g}s->{len(segments(eng, g)):,}" for g in (5, 10, 15, 20))
          + f"  (= {n_pairs:,} distinct pairs + splits; the handoff's counts match the splits alone)")

    ek = elims.sort_values(["match_id", "t_ms"]).reset_index(drop=True)
    ek["t"] = ek["t_ms"] / 1000
    ek["vt"] = team_at(ek, "eliminated", teams)
    ek["et"] = team_at(ek, "eliminator", teams)
    print(f"\nelims rows {len(ek):,}; knocks {int(ek['knocked'].sum()):,}; victim/eliminator team resolved "
          f"{pct((ek['vt'].notna() & ek['et'].notna()).mean())}")

    # time from last damage on the victim to the knock
    owner = matches.set_index("match_id")["replay_owner"]
    ek["rec"] = (ek["eliminated"] == ek["match_id"].map(owner)) | (ek["eliminator"] == ek["match_id"].map(owner))
    ek["pa"] = ek[["vt", "et"]].min(axis=1)
    ek["pb"] = ek[["vt", "et"]].max(axis=1)
    byv = {k: g["t"].to_numpy() for k, g in d[d["target"].notna()].sort_values("t").groupby(["match_id", "target"])}
    last = []
    for r in ek.itertuples():
        ts = byv.get((r.match_id, r.eliminated))
        j = np.searchsorted(ts, r.t, side="right") - 1 if ts is not None else -1
        last.append(r.t - ts[j] if j >= 0 else np.inf)
    ek["since_dmg"] = last
    for name, sub in (("recorder-involved", ek[ek["knocked"] & ek["rec"]]), ("all", ek[ek["knocked"]])):
        x = sub["since_dmg"].to_numpy()
        f = x[np.isfinite(x)]
        print(f"knocks {name} ({len(x):,}): no damage ever on victim {pct(np.isinf(x).mean())}; among the rest "
              f"median {np.median(f):.2f}s, p90 {np.quantile(f, .9):.1f}s")

    seg = segments(eng, GAP_S)
    print(f"\n== Q1: overlapping segments that share a team (GAP_S={GAP_S:g}) ==")
    lags, shared = [], 0
    for _, g in seg.groupby("match_id"):
        a = g[["ta", "tb", "t_start", "t_end"]].to_numpy()
        for i in range(len(a)):
            hit = False
            for j in range(len(a)):
                if i == j or not ({a[i][0], a[i][1]} & {a[j][0], a[j][1]}) or {a[i][0], a[i][1]} == {a[j][0], a[j][1]}:
                    continue
                lag = max(a[i][2], a[j][2]) - min(a[i][3], a[j][3])  # <0 overlap, >0 separation
                if lag <= GAP_S:
                    hit = True
                    lags.append(lag)
            shared += hit
    lags = np.array(lags)
    print(f"{shared:,}/{len(seg):,} segments ({pct(shared / len(seg))}) have a team-sharing segment of another pair within {GAP_S:g}s")
    if len(lags):
        print(f"  of those links: truly overlapping (lag<0) {pct((lags < 0).mean())}; lag in [0,{GAP_S:g}] {pct((lags >= 0).mean())}")
    for w in (0, 5, 10, 20, 30):
        n = 0
        for _, g in seg.groupby("match_id"):
            a = g[["ta", "tb", "t_start", "t_end"]].to_numpy()
            for i in range(len(a)):
                if any(i != j and ({a[i][0], a[i][1]} & {a[j][0], a[j][1]}) and {a[i][0], a[i][1]} != {a[j][0], a[j][1]}
                       and max(a[i][2], a[j][2]) - min(a[i][3], a[j][3]) <= w for j in range(len(a))):
                    n += 1
        print(f"  window {w:>2d}s: {pct(n / len(seg))} of segments linked to a third party")

    print("\n== Q1b: fights after merging team-sharing segments (segment gap 10s; link if lag <= window) ==")
    for w in (0, 5, 10):
        rows = []
        for _, g in seg.groupby("match_id"):
            a = g[["ta", "tb", "t_start", "t_end"]].to_numpy()
            parent = list(range(len(a)))

            def find(i):
                while parent[i] != i:
                    parent[i] = parent[parent[i]]
                    i = parent[i]
                return i

            for i in range(len(a)):
                for j in range(i + 1, len(a)):
                    if ({a[i][0], a[i][1]} & {a[j][0], a[j][1]}) and max(a[i][2], a[j][2]) - min(a[i][3], a[j][3]) <= w:
                        parent[find(i)] = find(j)
            comp: dict[int, list[int]] = {}
            for i in range(len(a)):
                comp.setdefault(find(i), []).append(i)
            for idx in comp.values():
                teams_in = {int(x) for i in idx for x in a[i][:2]}
                rows.append((len(teams_in), a[idx][:, 3].max() - a[idx][:, 2].min()))
        r = np.array(rows, dtype=float)
        print(f"window {w:>2d}s: {len(r):,} fights; multi-team {pct((r[:, 0] > 2).mean())}; teams p50/p90/max "
              f"{np.median(r[:, 0]):.0f}/{np.quantile(r[:, 0], .9):.0f}/{r[:, 0].max():.0f}; duration p50/p90/max "
              f"{np.median(r[:, 1]):.1f}/{np.quantile(r[:, 1], .9):.1f}/{r[:, 1].max():.0f}s; "
              f"fights >= 60s {pct((r[:, 1] >= 60).mean())}")

    print(f"\n== Q2: opposing-team knocks inside a segment (gap {GAP_S:g}s + {GRACE_S:g}s grace) ==")
    kn = ek[ek["knocked"] & ek["vt"].notna() & ek["et"].notna() & (ek["vt"] != ek["et"])].copy()
    kn = kn.astype({"pa": int, "pb": int})
    sg = {k: g[["t_start", "t_end"]].to_numpy() for k, g in seg.groupby(["match_id", "ta", "tb"])}

    def inside(r, grace=GRACE_S):
        for s, e in sg.get((r.match_id, r.pa, r.pb), []):
            if s <= r.t <= e + grace:
                return True
        return False

    kn["in_seg"] = [inside(r) for r in kn.itertuples()]
    for name, sub in (("recorder-involved", kn[kn["rec"]]), ("all", kn)):
        print(f"{name}: {len(sub):,} opposing-team knocks; inside segment {pct(sub['in_seg'].mean())}")
    miss = kn[kn["rec"] & ~kn["in_seg"]]
    print(f"  recorder misses: {len(miss)}")
    # characterize misses by whether any pair damage exists in the match for that pair at all
    pair_any = set(zip(eng["match_id"], eng["ta"], eng["tb"]))
    m_pair = np.mean([(r.match_id, r.pa, r.pb) in pair_any for r in miss.itertuples()]) if len(miss) else float("nan")
    print(f"  of recorder misses, the team pair has some damage elsewhere in the match: {pct(m_pair)}")

    print("\n== Q3: solos and eliminations without a knock ==")
    print("playlists:", matches["playlist"].value_counts(dropna=False).to_dict())
    solo = matches["playlist"].fillna("").str.contains("Solo", case=False)
    print(f"solo matches in this data: {int(solo.sum())}")
    nk = ek[~ek["knocked"]].copy()
    prior = ek[ek["knocked"]].groupby(["match_id", "eliminated"])["t"].min()
    nk["first_knock_t"] = [prior.get((r.match_id, r.eliminated), np.inf) for r in nk.itertuples()]
    direct = nk[nk["first_knock_t"] > nk["t"]]
    print(f"eliminations (knocked=False) {len(nk):,}; with no earlier knock of that victim {len(direct):,} "
          f"({pct(len(direct) / max(len(nk), 1))})")
    dd = direct[direct["vt"].notna() & direct["et"].notna() & (direct["vt"] != direct["et"])].astype({"pa": int, "pb": int})
    print(f"  of those, opposing-team {len(dd):,}; inside a segment {pct(np.mean([inside(r) for r in dd.itertuples()]) if len(dd) else float('nan'))}")

    print("\n== Q4: bots ==")
    pb = players.set_index(["match_id", "player_id"])["is_bot"]
    bot_team = teams.merge(players[["match_id", "player_id", "is_bot"]], on=["match_id", "player_id"], how="left")
    agg = bot_team.groupby(["match_id", "team_index"])["is_bot"].agg(["any", "all"])
    print(f"team rows with a bot: {pct(bot_team['is_bot'].mean())}; teams any-bot {pct(agg['any'].mean())}, all-bot {pct(agg['all'].mean())}")
    for how in ("any", "all"):
        isb = agg[how].to_dict()
        flag = [isb.get((r.match_id, r.ta), False) or isb.get((r.match_id, r.tb), False) for r in seg.itertuples()]
        print(f"segments involving a {how}-bot team: {int(sum(flag)):,}/{len(seg):,} ({pct(np.mean(flag))})")
    print("(proposal: keep, flag has_bots)")


if __name__ == "__main__":
    main()
