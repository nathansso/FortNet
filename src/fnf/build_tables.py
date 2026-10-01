"""Build processed parquet tables from data/interim/telemetry.

Usage: uv run fnf-build-tables [--gap-ms 30000]
"""

import argparse

from fnf import DATA
from fnf.builds import attribute_builders, detect_edits, parse_pieces
from fnf.schema import coerce, validate
from fnf.fights import DEFAULT_GAP_MS, assign_fights, build_fight_sides, fights_table, player_fight_outcomes
from fnf.telemetry import elims_table, load_table, replay_dirs


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--gap-ms", type=int, default=DEFAULT_GAP_MS)
    args = ap.parse_args()

    src = DATA / "interim" / "telemetry"
    if not src.exists() or not replay_dirs(src):
        raise SystemExit("No exported replays in data/interim/telemetry. Run the ReplayExport tool first (see README).")

    out = DATA / "processed"
    out.mkdir(parents=True, exist_ok=True)

    tables = {
        "matches": load_table(src, "meta"),
        "players": load_table(src, "players"),
        "positions": load_table(src, "positions"),
        "damage": load_table(src, "damage"),
        "health": load_table(src, "health"),
        "safezones": load_table(src, "safezones"),
        "teams": load_table(src, "teams"),
        "weapons": load_table(src, "weapons"),
    }
    builds = load_table(src, "builds")
    if not builds.empty:
        tables["pieces"] = attribute_builders(
            detect_edits(parse_pieces(builds)), tables["positions"], tables["teams"], tables["weapons"]
        )
    elims = assign_fights(elims_table(load_table(src, "eliminations")), gap_ms=args.gap_ms)
    tables["elims"] = elims
    tables["fights"] = fights_table(elims)
    tables["player_fights"] = player_fight_outcomes(elims)
    tables["fight_sides"] = build_fight_sides(
        tables["damage"], tables["teams"], elims, tables["players"], tables["matches"]
    )

    problems = []
    for name, df in tables.items():
        tables[name] = coerce(df, name)
        problems += validate(tables[name], name)
    if problems:
        raise SystemExit("Schema validation failed (see src/fnf/schema.py):\n  " + "\n  ".join(problems))

    for name, df in tables.items():
        df.to_parquet(out / f"{name}.parquet", index=False)
        print(f"{name:14s} {len(df):9d} rows -> {out / f'{name}.parquet'}")


if __name__ == "__main__":
    main()
