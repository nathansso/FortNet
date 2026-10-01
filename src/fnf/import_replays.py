"""Import .replay files into data/raw/replays and record provenance in data/raw/manifest.csv.

Files are deduplicated by content hash and originals are never modified.
Files already in data/raw/replays but missing from the manifest are backfilled
with the provenance given on the command line.

Usage:
    uv run fnf-import                                   # local Fortnite Demos folder, client replays
    uv run fnf-import D:/donations/alice --source donated --kind client \\
        --contributor c017 --consent CONSENT-2026-014
"""

import argparse
import hashlib
import os
import shutil
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from fnf import DATA
from fnf.schema import TABLES, coerce, validate

DEFAULT_SOURCE_DIR = Path(os.environ.get("LOCALAPPDATA", "")) / "FortniteGame" / "Saved" / "Demos"
SOURCES = ("local_demos", "donated", "tournament_ingame", "partner_osirion", "partner_other")
KINDS = ("client", "server", "unknown")
REPLAYS = DATA / "raw" / "replays"
MANIFEST = DATA / "raw" / "manifest.csv"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_manifest() -> pd.DataFrame:
    cols = TABLES["manifest"].column_names
    if not MANIFEST.exists():
        return coerce(pd.DataFrame(columns=cols), "manifest")
    return coerce(pd.read_csv(MANIFEST, dtype=str), "manifest")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source_dir", nargs="?", type=Path, default=DEFAULT_SOURCE_DIR)
    ap.add_argument("--source", choices=SOURCES, default="local_demos")
    ap.add_argument("--kind", choices=KINDS, default="client")
    ap.add_argument("--contributor", help="Pseudonymous contributor id (never a real name)")
    ap.add_argument("--consent", help="Consent record id (required for --source donated)")
    ap.add_argument("--notes")
    args = ap.parse_args()

    if args.source == "donated" and not args.consent:
        raise SystemExit("--consent is required for donated replays (see docs/data_sourcing.md)")
    if not args.source_dir.is_dir():
        raise SystemExit(f"Source folder not found: {args.source_dir}")

    REPLAYS.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest()
    known_hashes = set(manifest["sha256"].dropna())
    known_files = set(manifest["replay_file"].dropna())
    now = datetime.now(UTC).isoformat(timespec="seconds")

    def row(path: Path, digest: str) -> dict:
        return {
            "replay_file": path.name, "sha256": digest, "size_bytes": path.stat().st_size,
            "source": args.source, "replay_kind": args.kind, "contributor": args.contributor,
            "consent_ref": args.consent, "acquired_at": now, "notes": args.notes,
        }

    # Backfill files already present but missing from the manifest first, so they count as known.
    new_rows, backfilled = [], 0
    for f in sorted(REPLAYS.glob("*.replay")):
        if f.name not in known_files:
            digest = sha256(f)
            new_rows.append(row(f, digest) | {"notes": "backfilled: present before manifest existed"})
            known_hashes.add(digest)
            backfilled += 1

    copied = duplicates = 0
    for f in sorted(args.source_dir.glob("*.replay")):
        digest = sha256(f)
        if digest in known_hashes:
            duplicates += 1
            continue
        target = REPLAYS / f.name
        if target.exists():  # same name, different content: keep both
            target = REPLAYS / f"{f.stem}-{digest[:8]}{f.suffix}"
        shutil.copy2(f, target)
        new_rows.append(row(target, digest))
        known_hashes.add(digest)
        copied += 1

    if new_rows:
        manifest = coerce(pd.concat([manifest, pd.DataFrame(new_rows)], ignore_index=True), "manifest")
        problems = validate(manifest, "manifest")
        if problems:
            raise SystemExit("Manifest invalid:\n  " + "\n  ".join(problems))
        manifest.to_csv(MANIFEST, index=False)

    print(f"Copied {copied}, skipped {duplicates} duplicates, backfilled {backfilled} -> {REPLAYS}")
    print(f"Manifest: {len(manifest)} replays ({MANIFEST})")


if __name__ == "__main__":
    main()
