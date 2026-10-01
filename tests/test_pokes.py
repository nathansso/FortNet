"""Synthetic-frame tests for poke classification outcomes (src/fnf/pokes.py)."""

import numpy as np
import pandas as pd
import pytest

from fnf.fights import GRACE_S, POKE_CONVERT_S, build_fight_sides
from fnf.pokes import build_pokes
from fight_frames import M, dmg, elim, matches_frame, no_elims, players_frame, teams_frame

# Team 1 pokes team 2 (target B1) for 80 damage, takes 0 back: t0=0, t_end=2. A2 -> B2 is not part of the poke.
POKE = [(0.0, "A1", "B1", 30), (1.0, "A1", "B1", 30), (2.0, "A1", "B1", 20)]


def players_with_deaths(deaths=None):
    p = players_frame()
    for pid, t in (deaths or {}).items():
        p.loc[p["player_id"] == pid, "death_time"] = t
    return p


def positions_frame(rows=()):
    return pd.DataFrame(list(rows), columns=["match_id", "player_id", "t", "x", "y", "z", "in_storm"]).astype(
        {"in_storm": "object"})


def run(damage, elims=None, players=None, positions=None, **kw):
    damage = damage if "x" in damage else damage.assign(x=0.0, y=0.0)
    elims = elims if elims is not None else no_elims()
    players = players if players is not None else players_frame()
    positions = positions if positions is not None else positions_frame()
    fs_kw = {k: v for k, v in kw.items() if k in ("gap_s", "overlap_tol_s", "grace_s")}
    if "convert_s" in kw:
        fs_kw["poke_convert_s"] = kw["convert_s"]
    fs = build_fight_sides(damage, teams_frame(), elims, players, matches_frame(), **fs_kw)
    pk = build_pokes(damage, teams_frame(), elims, players, positions, fs,
                     **{k: v for k, v in kw.items() if k in ("gap_s", "overlap_tol_s", "grace_s", "convert_s")})
    return fs, pk


def test_one_row_per_poke_with_teams_and_net_damage():
    _, pk = run(dmg(POKE))
    assert len(pk) == 1
    r = pk.iloc[0]
    assert (r["poker_team"], r["target_team"], r["net_damage"], r["target_players"]) == (1, 2, 80.0, "B1")
    assert (r["t0"], r["t_end"], r["fight_id"]) == (0.0, 2.0, f"{M}:0")


def test_net_damage_subtracts_damage_taken_back():
    fs, pk = run(dmg(POKE + [(1.5, "B1", "A1", 8)]))  # 8 of 88 = 9.1% < 10% -> still a poke
    assert len(pk) == 1 and pk["net_damage"].iloc[0] == 72.0


def test_fights_are_not_in_pokes():
    fs, pk = run(dmg([(0.0, "A1", "B1", 50), (0.5, "B1", "A1", 50)]))
    assert (fs["engagement_type"] == "fight").all() and pk.empty


def test_conversion_by_poker_within_window():
    _, pk = run(dmg(POKE), elim([(2.0 + 5.0, "A2", "B1", True)]))
    r = pk.iloc[0]
    assert r["converted"] and r["converted_by"] == "poker" and r["converter_team"] == 1
    assert r["t_convert"] == pytest.approx(5.0)


def test_conversion_by_third_party():
    _, pk = run(dmg(POKE), elim([(10.0, "C1", "B1", True)]))
    r = pk.iloc[0]
    assert r["converted"] and r["converted_by"] == "third_party" and r["converter_team"] == 3


def test_conversion_after_window_does_not_count():
    _, pk = run(dmg(POKE), elim([(2.0 + POKE_CONVERT_S + 1.0, "C1", "B1", True)]))
    assert not pk["converted"].iloc[0] and pk["converted_by"].isna().iloc[0] and pk["t_convert"].isna().iloc[0]
    _, wide = run(dmg(POKE), elim([(2.0 + POKE_CONVERT_S + 1.0, "C1", "B1", True)]), convert_s=30.0)
    assert wide["converted"].iloc[0]


def test_conversion_ignores_non_target_players_and_uses_first_event():
    # B2 was not hit by the poke; B1 is knocked by C1 at 6 s and finished by A1 at 8 s -> first event decides.
    e = elim([(4.0, "C1", "B2", True), (6.0, "C1", "B1", True), (8.0, "A1", "B1", False)])
    _, pk = run(dmg(POKE), e)
    assert pk["converted_by"].iloc[0] == "third_party" and pk["t_convert"].iloc[0] == pytest.approx(4.0)


def test_environment_conversion_when_victim_is_own_eliminator():
    _, pk = run(dmg(POKE), elim([(6.0, "B1", "B1", False)]))
    r = pk.iloc[0]
    assert r["converted"] and r["converted_by"] == "environment" and pd.isna(r["converter_team"])


def test_knock_during_or_within_grace_makes_a_pick_not_a_poke():
    for t in (1.5, 2.0 + GRACE_S - 0.1):
        fs, pk = run(dmg(POKE), elim([(t, "A1", "B1", True)]))
        assert (fs["engagement_type"] == "pick").all() and pk.empty


def test_conversion_counts_only_after_the_grace_window():
    _, just_after = run(dmg(POKE), elim([(2.0 + GRACE_S + 0.1, "C1", "B1", True)]))
    assert just_after["converted"].iloc[0] and just_after["t_convert"].iloc[0] > GRACE_S
    # a third-party knock of the target DURING the poke is not an opposing fight-team knock (still a poke) but it
    # sits inside the engagement window, so it is not a conversion either
    fs, during = run(dmg(POKE), elim([(1.0, "C1", "B1", True)]))
    assert (fs["engagement_type"] == "poke").all() and not during["converted"].iloc[0]


def test_storm_death_requires_in_storm_flag_at_death():
    pos = lambda flag: positions_frame([(M, "B1", 0.5, 0, 0, 0, flag)])  # noqa: E731
    deaths = players_with_deaths({"B1": 9.0})
    _, yes = run(dmg(POKE), players=deaths, positions=pos(True))
    assert yes["storm_death"].iloc[0]
    _, no = run(dmg(POKE), players=deaths, positions=pos(False))
    assert not no["storm_death"].iloc[0]
    _, unknown = run(dmg(POKE), players=deaths, positions=positions_frame())
    assert not unknown["storm_death"].iloc[0]


def test_storm_death_outside_window_or_for_other_players_ignored():
    pos = positions_frame([(M, "B1", 0.5, 0, 0, 0, True), (M, "B2", 0.5, 0, 0, 0, True)])
    late = players_with_deaths({"B1": 2.0 + POKE_CONVERT_S + 5})
    assert not run(dmg(POKE), players=late, positions=pos)[1]["storm_death"].iloc[0]
    other = players_with_deaths({"B2": 9.0})
    assert not run(dmg(POKE), players=other, positions=pos)[1]["storm_death"].iloc[0]


def structure_row(t, source, x, y, mag=100.0):
    return pd.DataFrame({"match_id": [M], "t": [t], "source": [source], "target": [None], "magnitude": [mag],
                         "x": [x], "y": [y]})


def test_structure_pressure_counts_nearby_poker_team_structure_damage():
    d = pd.concat([dmg(POKE).assign(x=0.0, y=0.0), structure_row(1.0, "A1", 500, 0),
                   structure_row(1.5, "A2", 900, 0, 50.0),
                   structure_row(1.0, "A1", 5000, 0),      # far from the target
                   structure_row(1.0, "B2", 100, 0),       # not the poker team
                   structure_row(9.0, "A1", 100, 0)],      # after the poke
                  ignore_index=True)
    pos = positions_frame([(M, "B1", 0.5, 0, 0, 0, None), (M, "B1", 1.4, 0, 0, 0, None)])
    _, pk = run(d, positions=pos)
    r = pk.iloc[0]
    assert (r["structure_hits"], r["structure_damage"]) == (2, 150.0)


def test_structure_pressure_zero_without_target_positions():
    d = pd.concat([dmg(POKE).assign(x=0.0, y=0.0), structure_row(1.0, "A1", 100, 0)], ignore_index=True)
    assert run(d)[1]["structure_hits"].iloc[0] == 0


def test_poke_row_carries_seg_version():
    fs, pk = run(dmg(POKE), gap_s=5)
    assert (pk["seg_version"] == fs["seg_version"].iloc[0]).all() and "gap5" in pk["seg_version"].iloc[0]


def test_mismatched_segmentation_params_raise():
    d = dmg(POKE + [(60.0, "A1", "B1", 30), (61.0, "A1", "B1", 30)])
    fs = build_fight_sides(d.assign(x=0.0, y=0.0), teams_frame(), no_elims(), players_frame(), matches_frame(), gap_s=10)
    with pytest.raises(ValueError):
        build_pokes(d.assign(x=0.0, y=0.0), teams_frame(), no_elims(), players_frame(), positions_frame(), fs, gap_s=100)


def test_leakage_guard_poke_identity_ignores_later_data_but_labels_look_ahead():
    d = dmg(POKE + [(60.0, "A1", "C1", 30), (61.0, "A1", "C1", 30)])
    e = elim([(8.0, "C1", "B1", True), (62.0, "A1", "C1", True)])
    full_fs, full_pk = run(d, e)
    cutoff = 2.0 + GRACE_S
    d_cut = d[d["t"] <= cutoff].reset_index(drop=True)
    e_cut = e[e["t_ms"] / 1000 <= cutoff].reset_index(drop=True)
    cut_fs, cut_pk = run(d_cut, e_cut)
    keep = ["fight_id", "team_index", "t0", "t_end", "players", "engagement_type", "mutual", "minority_damage_share"]
    a = full_fs[full_fs["fight_id"] == f"{M}:0"][keep].reset_index(drop=True)
    b = cut_fs[cut_fs["fight_id"] == f"{M}:0"][keep].reset_index(drop=True)
    pd.testing.assert_frame_equal(a, b)
    ident = ["fight_id", "poker_team", "target_team", "t0", "t_end", "target_players", "net_damage"]
    f0, c0 = full_pk[full_pk["fight_id"] == f"{M}:0"], cut_pk[cut_pk["fight_id"] == f"{M}:0"]
    pd.testing.assert_frame_equal(f0[ident].reset_index(drop=True), c0[ident].reset_index(drop=True))
    # the conversion at 8 s is beyond the cutoff: labels look ahead by design, so they differ
    assert f0["converted"].iloc[0] and not c0["converted"].iloc[0]
