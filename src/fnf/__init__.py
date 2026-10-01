"""Fortnite pro placement forecasting."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# data/ is git-ignored, so a git worktree has none: point FNF_DATA_DIR at the main checkout's data/.
DATA = Path(os.environ["FNF_DATA_DIR"]) if os.environ.get("FNF_DATA_DIR") else ROOT / "data"
