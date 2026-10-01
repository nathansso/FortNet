"""Deterministic data splits. See docs/architecture.md, "Data splits".

Every split is a pure function of ids and dates, so any session reproduces the
same assignment. Changing a salt or fraction is a versioned decision: bump the
salt suffix and record it in the architecture doc's Decisions table.
"""

import hashlib
import re
from collections.abc import Iterator

import pandas as pd

HOLDOUT_SALT = "fnf-holdout-v1"
HOLDOUT_FRAC = 0.20
FOLD_SALT = "fnf-folds-v1"
VAL_FRAC = 0.15
TEST_FRAC = 0.15

_REPLAY_TS = re.compile(r"(\d{4})\.(\d{2})\.(\d{2})-(\d{2})\.(\d{2})\.(\d{2})")


def _unit_hash(salt: str, key: str) -> float:
    """Uniform in [0, 1), stable across machines and Python versions."""
    digest = hashlib.sha256(f"{salt}:{key}".encode()).hexdigest()
    return int(digest[:12], 16) / 16**12


def is_held_out_player(player_id: str, frac: float = HOLDOUT_FRAC, salt: str = HOLDOUT_SALT) -> bool:
    """Held-out players are excluded from all training (encoder, forecaster) and evaluated separately.

    Bots are never held out. Ids are case-insensitive.
    """
    if not isinstance(player_id, str) or player_id.startswith("BOT_"):
        return False
    return _unit_hash(salt, player_id.upper()) < frac


def match_start(matches: pd.DataFrame) -> pd.Series:
    """Match start (UTC) per match_id: utc_start, else the timestamp in the replay file name.

    File-name timestamps are the recorder's local time, so they can be off by the UTC offset;
    only used when utc_start is missing (some Creative modes).
    """
    utc = pd.to_datetime(matches["utc_start"], utc=True, errors="coerce", format="ISO8601")

    def from_name(mid: str):
        m = _REPLAY_TS.search(mid)
        return pd.Timestamp(*map(int, m.groups()), tz="UTC") if m else pd.NaT

    fallback = matches["match_id"].map(from_name)
    return pd.Series(utc.fillna(fallback).to_numpy(), index=matches["match_id"].to_numpy(), name="start")


def chronological_split(matches: pd.DataFrame, val_frac: float = VAL_FRAC, test_frac: float = TEST_FRAC) -> pd.Series:
    """train / val / test by match start time, whole matches only (fight models).

    The latest test_frac of matches is test, the val_frac before it is val.
    """
    start = match_start(matches).sort_values(kind="stable")
    n = len(start)
    n_test, n_val = round(n * test_frac), round(n * val_frac)
    labels = ["train"] * (n - n_val - n_test) + ["val"] * n_val + ["test"] * n_test
    return pd.Series(labels, index=start.index, name="split")


def cross_fit_fold(match_id: str, k: int = 5, salt: str = FOLD_SALT) -> int:
    """Fold for out-of-fold residuals: a fight's residual comes from a model not trained on its match."""
    return int(_unit_hash(salt, match_id) * k)


def rolling_origins(events: pd.DataFrame, min_train_events: int = 10) -> Iterator[tuple[pd.Timestamp, list, list]]:
    """Forecaster evaluation: for each event date, train on all events strictly before it.

    `events` needs event_id and date columns. Yields (origin_date, train_event_ids, test_event_ids).
    """
    ev = events.assign(date=pd.to_datetime(events["date"], utc=True)).sort_values("date")
    for origin, test in ev.groupby("date", sort=True):
        train = ev[ev["date"] < origin]
        if len(train) >= min_train_events:
            yield origin, train["event_id"].tolist(), test["event_id"].tolist()
