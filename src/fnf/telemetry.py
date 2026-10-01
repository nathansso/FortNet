"""Load per-replay telemetry CSVs (from ingest/ReplayExport) into combined DataFrames."""

from pathlib import Path

import pandas as pd

TABLES = ["meta", "players", "positions", "damage", "health", "eliminations", "safezones"]


def replay_dirs(telemetry_dir: Path) -> list[Path]:
    return sorted(p for p in telemetry_dir.iterdir() if (p / "meta.csv").exists())


def load_table(telemetry_dir: Path, name: str) -> pd.DataFrame:
    """Concatenate one table across replays, tagged with match_id (the replay name)."""
    parts = []
    for d in replay_dirs(telemetry_dir):
        f = d / f"{name}.csv"
        if f.exists() and f.stat().st_size > 0:
            df = pd.read_csv(f, low_memory=False)
            if len(df):
                parts.append(df.assign(match_id=d.name))
    if not parts:
        return pd.DataFrame()
    df = pd.concat(parts, ignore_index=True)
    return df[["match_id", *[c for c in df.columns if c != "match_id"]]]


def elims_table(eliminations: pd.DataFrame) -> pd.DataFrame:
    """Kill feed in the schema fights.py expects (t_ms, eliminator, eliminated, knocked, gun_type)."""
    cols = ["match_id", "t_ms", "eliminator", "eliminated", "knocked", "gun_type"]
    if eliminations.empty:
        return pd.DataFrame(columns=cols)
    df = eliminations.assign(
        t_ms=(eliminations["t"] * 1000).round().astype("int64"),
        knocked=eliminations["knocked"].astype(bool),
        gun_type=eliminations["gun_type"].astype("string"),
    )
    return df[cols].sort_values(["match_id", "t_ms"], ignore_index=True)
