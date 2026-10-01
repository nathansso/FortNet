import pandas as pd

from fnf.fights import assign_fights, fights_table, player_fight_outcomes


def _elims(rows):
    return pd.DataFrame(rows, columns=["match_id", "t_ms", "eliminator", "eliminated", "knocked", "gun_type"])


def test_shared_player_within_gap_is_one_fight():
    ev = _elims([
        ("m1", 1_000, "A", "B", True, "SMG"),
        ("m1", 5_000, "A", "B", False, "SMG"),
        ("m1", 9_000, "C", "A", True, "Shotgun"),
    ])
    out = assign_fights(ev, gap_ms=30_000)
    assert out["fight_id"].nunique() == 1


def test_gap_splits_fights():
    ev = _elims([
        ("m1", 1_000, "A", "B", True, "SMG"),
        ("m1", 100_000, "A", "C", True, "SMG"),
    ])
    out = assign_fights(ev, gap_ms=30_000)
    assert out["fight_id"].nunique() == 2


def test_disjoint_players_are_separate_fights():
    ev = _elims([
        ("m1", 1_000, "A", "B", True, "SMG"),
        ("m1", 2_000, "C", "D", True, "SMG"),
    ])
    assert assign_fights(ev)["fight_id"].nunique() == 2


def test_matches_never_merge():
    ev = _elims([
        ("m1", 1_000, "A", "B", True, "SMG"),
        ("m2", 1_000, "A", "B", True, "SMG"),
    ])
    assert assign_fights(ev)["fight_id"].nunique() == 2


def test_fight_and_player_tables():
    ev = assign_fights(_elims([
        ("m1", 1_000, "A", "B", True, "SMG"),
        ("m1", 4_000, "A", "B", False, "SMG"),
    ]))
    fights = fights_table(ev)
    assert fights.loc[0, ["n_knocks", "n_elims", "n_players", "duration_ms"]].tolist() == [1, 1, 2, 3_000]

    pf = player_fight_outcomes(ev).set_index("player")
    assert pf.loc["A", "knocks_dealt"] == 1 and pf.loc["A", "elims_dealt"] == 1 and not pf.loc["A", "lost"]
    assert pf.loc["B", "knocks_recv"] == 1 and pf.loc["B", "elims_recv"] == 1 and pf.loc["B", "lost"]
