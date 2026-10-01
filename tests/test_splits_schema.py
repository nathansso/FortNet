import pandas as pd

from fnf.schema import DOC_PATH, coerce, render_markdown, validate
from fnf.splits import (
    chronological_split,
    cross_fit_fold,
    is_held_out_player,
    match_start,
    rolling_origins,
)


def test_schema_doc_is_up_to_date():
    assert DOC_PATH.read_text(encoding="utf-8") == render_markdown(), "run `uv run fnf-schema-doc`"


def test_coerce_and_validate_csv_style_frame():
    raw = pd.DataFrame({
        "match_id": ["m", "m"], "t": ["1.5", "2"], "player_id": ["A", "A"], "team_index": ["3", "4"],
    })
    df = coerce(raw, "teams")
    assert validate(df, "teams") == []
    assert df["team_index"].dtype == "int64" and df["t"].dtype == "float64"


def test_validate_flags_nulls_missing_and_extra_columns():
    df = coerce(pd.DataFrame({"match_id": ["m"], "t": [1.0], "player_id": [None], "bogus": [1]}), "teams")
    problems = " ".join(validate(df, "teams"))
    assert "missing columns ['team_index']" in problems
    assert "undeclared columns ['bogus']" in problems
    assert "player_id: 1 nulls" in problems


def test_bool_flags_keep_null_as_unknown():
    df = coerce(pd.DataFrame({"downed": ["1", "0", ""]}), "positions")
    assert df["downed"].tolist()[:2] == [True, False] and pd.isna(df["downed"].iloc[2])


def test_holdout_is_deterministic_case_insensitive_and_about_20pct():
    ids = [f"{i:032X}" for i in range(5000)]
    held = [is_held_out_player(i) for i in ids]
    assert held == [is_held_out_player(i.lower()) for i in ids]
    assert 0.18 < sum(held) / len(held) < 0.22
    assert not is_held_out_player("BOT_257")


def test_chronological_split_orders_by_start_and_falls_back_to_file_name():
    matches = pd.DataFrame({
        "match_id": [f"UnsavedReplay-2026.08.{d:02d}-12.00.00" for d in range(1, 21)],
        "utc_start": [None] * 20,
    })
    split = chronological_split(matches)
    assert split.value_counts().to_dict() == {"train": 14, "val": 3, "test": 3}
    start = match_start(matches)
    assert start[split == "train"].max() < start[split == "val"].min() < start[split == "test"].min()


def test_cross_fit_fold_is_stable():
    assert cross_fit_fold("m1") == cross_fit_fold("m1")
    assert {cross_fit_fold(f"m{i}") for i in range(200)} == set(range(5))


def test_rolling_origins_never_train_on_same_day_or_later():
    events = pd.DataFrame({"event_id": list("abcdef"), "date": ["2026-01-01"] * 2 + ["2026-01-08"] * 2 + ["2026-01-15"] * 2})
    folds = list(rolling_origins(events, min_train_events=2))
    assert [(train, test) for _, train, test in folds] == [(["a", "b"], ["c", "d"]), (["a", "b", "c", "d"], ["e", "f"])]
