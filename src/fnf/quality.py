"""Post-ingest quality gates. Run after fnf-build-tables; see docs/data_sourcing.md.

Usage: uv run fnf-quality
Exit code 1 if any gate fails.
"""

import re

import numpy as np
import pandas as pd

from fnf import DATA, ROOT
from fnf.telemetry import load_table

P = DATA / "processed"

GATES = {
    "damage_corr": 0.90,  # recorder damage to players vs. game end-of-match stat (Pearson r)
    "damage_ratio_lo": 0.90,  # median parsed/game ratio bounds
    "damage_ratio_hi": 1.10,
    "position_resolution": 0.99,  # share of position rows with a player_id
    "clock_offset_s": 0.05,  # |median| downed-flag time minus knock-event time
    "recorder_knock_coverage": 0.90,  # recorder-involved opposing-team knocks inside a v1 fight with an outcome
}


def damage_vs_stats() -> tuple[float, float, int]:
    d = pd.read_parquet(P / "damage.parquet", columns=["match_id", "source", "target", "magnitude"])
    m = pd.read_parquet(P / "matches.parquet")
    own = m.set_index("match_id")["replay_owner"]
    dp = d[d["target"].notna() & (d["source"] != d["target"])]
    dp = dp[dp["source"] == dp["match_id"].map(own)]
    parsed = dp.groupby("match_id")["magnitude"].sum()
    game = (m.set_index("match_id")[["rec_weapon_damage", "rec_other_damage"]].sum(axis=1, min_count=1)).dropna()
    both = pd.concat([game.rename("game"), parsed.rename("parsed")], axis=1).fillna({"parsed": 0})
    both = both[both["game"] > 0]
    if len(both) < 5:
        return float("nan"), float("nan"), len(both)
    return both.corr().iloc[0, 1], (both["parsed"] / both["game"]).median(), len(both)


def clock_offset() -> tuple[float, int]:
    e = pd.read_parquet(P / "elims.parquet")
    p = pd.read_parquet(P / "positions.parquet", columns=["match_id", "t", "player_id", "downed"])
    p = p[p["downed"] == True].sort_values("t")  # noqa: E712 (nullable boolean)
    times = p.groupby(["match_id", "player_id"])["t"].apply(lambda s: s.to_numpy())
    diffs = []
    for r in e[e["knocked"]].itertuples():
        key = (r.match_id, str(r.eliminated).upper())
        if key not in times.index:
            continue
        ts, te = times[key], r.t_ms / 1000
        j = np.searchsorted(ts, te - 5)
        if j < len(ts) and ts[j] - te < 5:
            diffs.append(ts[j] - te)
    return (float(np.median(diffs)) if diffs else float("nan")), len(diffs)


def knock_coverage() -> tuple[float, int]:
    from fnf.fights import recorder_knock_coverage

    cov = recorder_knock_coverage(
        pd.read_parquet(P / "elims.parquet"), pd.read_parquet(P / "fight_sides.parquet"),
        pd.read_parquet(P / "teams.parquet"), pd.read_parquet(P / "matches.parquet"),
    )
    return (float(cov["covered"].mean()) if len(cov) else float("nan")), len(cov)


def unknown_build_shapes() -> list[str]:
    gen = (ROOT / "ingest" / "gen_build_pieces.py").read_text(encoding="utf-8")
    block = gen[gen.index("SHAPES = sorted({"):gen.index("})")]
    known = set(re.findall(r'"([A-Za-z]+)"', block))
    classes = load_table(DATA / "interim" / "telemetry", "actor_classes")
    seen = set(classes["path"].dropna().str.extract(r"^PBWA_[A-Z]\d_(.+)_C$")[0].dropna()) if len(classes) else set()
    return sorted(seen - known)


def unexported_replays() -> list[str]:
    manifest = pd.read_csv(DATA / "raw" / "manifest.csv")
    tele = DATA / "interim" / "telemetry"
    return sorted(f for f in manifest["replay_file"] if not (tele / f.removesuffix(".replay") / "meta.csv").exists())


def main() -> None:
    failed = False

    def report(ok: bool, name: str, detail: str) -> None:
        nonlocal failed
        failed |= not ok
        print(f"{'PASS' if ok else 'FAIL'}  {name:22s} {detail}")

    r, ratio, n = damage_vs_stats()
    report(r >= GATES["damage_corr"] and GATES["damage_ratio_lo"] <= ratio <= GATES["damage_ratio_hi"],
           "damage vs game stats", f"r={r:.3f}, median ratio={ratio:.2f} over {n} matches")

    pos = pd.read_parquet(P / "positions.parquet", columns=["player_id"])
    res = pos["player_id"].notna().mean()
    report(res >= GATES["position_resolution"], "position resolution", f"{res:.4f} of rows have player_id")

    off, n = clock_offset()
    report(abs(off) <= GATES["clock_offset_s"], "event/frame clocks", f"median offset {off * 1000:.0f} ms over {n} knocks")

    cov, n = knock_coverage()
    report(cov >= GATES["recorder_knock_coverage"], "recorder knock coverage",
           f"{cov:.3f} of {n} recorder-involved opposing-team knocks inside a fight with an outcome")

    shapes = unknown_build_shapes()
    report(not shapes, "build shapes covered", "all known" if not shapes else f"add to gen_build_pieces.py: {shapes}")

    missing = unexported_replays()
    report(True, "export coverage", f"{len(missing)} manifest replays without telemetry"
           + (f" (e.g. {missing[:3]}; unfinalized recordings fail to parse)" if missing else ""))

    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
