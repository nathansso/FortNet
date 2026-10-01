"""Copy .replay files from the local Fortnite Demos folder into data/raw/replays.

Existing files are skipped and originals are never modified.

Usage: uv run fnf-import-local [source_dir]
"""

import os
import shutil
import sys
from pathlib import Path

from fnf import DATA

DEFAULT_SOURCE = Path(os.environ.get("LOCALAPPDATA", "")) / "FortniteGame" / "Saved" / "Demos"


def main() -> None:
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SOURCE
    if not source.is_dir():
        raise SystemExit(f"Source folder not found: {source}")

    dest = DATA / "raw" / "replays"
    dest.mkdir(parents=True, exist_ok=True)

    copied = skipped = 0
    for f in source.glob("*.replay"):
        target = dest / f.name
        if target.exists():
            skipped += 1
            continue
        shutil.copy2(f, target)
        copied += 1

    print(f"Copied {copied}, skipped {skipped} (already present) -> {dest}")


if __name__ == "__main__":
    main()
