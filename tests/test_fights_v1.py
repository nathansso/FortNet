"""Synthetic-frame tests for damage-based fight segmentation (src/fnf/fights.py v1)."""

import numpy as np
import pandas as pd

from fight_frames import M, dmg, elim, matches_frame, no_elims, players_frame, sides, teams_frame  # noqa: F401
from fnf.fights import (
    GRACE_S, TIE_S, build_fight_sides, engagement_damage, group_fights, hit_distances, label_outcomes, outcome_events,
    seg_version,
)

def outcome(fs, fight_id, team):
    return fs[(fs["fight_id"] == fight_id) & (fs["team_index"] == team)]["outcome"].iloc[0]


# A fight where A hits B for 100 and B hits back for 30: mutual, B knocked at t=4.
EXCHANGE = [(0.0, "A1", "B1", 40), (0.5, "B1", "A1", 30), (1.0, "A1", "B1", 30), (2.0, "A2", "B1", 30)]


def test_clean_1v1_win():
    fs = sides(dmg(EXCHANGE), elim([(2.5, "A1", "B1", True)]))
    assert len(fs) == 2 and fs["fight_id"].nunique() == 1
    assert outcome(fs, f"{M}:0", 1) == "win" and outcome(fs, f"{M}:0", 2) == "loss"
    assert not fs["multi_team"].any() and fs["mutual"].all() and (fs["engagement_type"] == "fight").all()
    a = fs[fs["team_index"] == 1].iloc[0]
    assert (a["t0"], a["t_end"], a["hits_dealt"], a["hits_taken"]) == (0.0, 2.0, 3, 1)
    assert (a["damage_dealt"], a["damage_taken"]) == (100, 30) and a["opp_team_index"] == 2
    assert a["players"] == "A1;A2" and a["recorder_involved"]


def test_gap_splits_fights():
    d = dmg([(0.0, "A1", "B1", 20), (1.0, "A1", "B1", 20), (30.0, "A1", "B1", 20), (31.0, "A1", "B1", 20)])
    assert sides(d, gap_s=10)["fight_id"].nunique() == 2
    assert sides(d, gap_s=40)["fight_id"].nunique() == 1


def test_friendly_fire_ignored():
    d = dmg([(0.0, "A1", "A2", 50), (1.0, "A1", "A2", 50)])
    assert engagement_damage(d, teams_frame()).empty
    assert sides(d).empty


def test_zero_magnitude_and_structure_hits_ignored():
    d = pd.concat([dmg([(0.0, "A1", "B1", 0)]), dmg([(1.0, "A1", None, 50)])], ignore_index=True)
    assert engagement_damage(d, teams_frame()).empty


def test_knock_inside_grace_counts_and_after_grace_does_not():
    d = dmg(EXCHANGE)  # t_end = 2.0
    inside = sides(d, elim([(2.0 + GRACE_S - 0.1, "A1", "B1", True)]))
    assert outcome(inside, f"{M}:0", 1) == "win"
    after = sides(d, elim([(2.0 + GRACE_S + 0.1, "A1", "B1", True)]))
    assert set(after["outcome"]) == {"disengage"}


def test_knock_before_t0_does_not_count():
    fs = sides(dmg(EXCHANGE), elim([(-1.0, "A1", "B1", True)]))
    assert set(fs["outcome"]) == {"disengage"}


def test_tie_within_tie_s_and_first_decides_beyond():
    d = dmg(EXCHANGE)
    tie = sides(d, elim([(3.0, "A1", "B1", True), (3.0 + TIE_S - 0.2, "B2", "A2", True)]))
    assert set(tie["outcome"]) == {"tie"}
    later = sides(d, elim([(3.0, "A1", "B1", True), (3.0 + TIE_S + 0.5, "B2", "A2", True)]))
    assert outcome(later, f"{M}:0", 1) == "win" and outcome(later, f"{M}:0", 2) == "loss"


def test_disengage_when_nobody_is_knocked():
    assert set(sides(dmg(EXCHANGE))["outcome"]) == {"disengage"}


def test_knock_by_third_party_outside_fight_teams_ignored():
    fs = sides(dmg(EXCHANGE), elim([(2.5, "C1", "B1", True)]))
    assert set(fs["outcome"]) == {"disengage"}


def test_third_party_overlap_merges_into_multi_team_fight():
    d = dmg(EXCHANGE + [(1.5, "C1", "B1", 40), (2.5, "B2", "C1", 20)])
    fs = sides(d, elim([(3.0, "A1", "B1", True)]))
    assert fs["fight_id"].nunique() == 1 and sorted(fs["team_index"]) == [1, 2, 3]
    assert fs["multi_team"].all()
    assert outcome(fs, f"{M}:0", 2) == "loss" and outcome(fs, f"{M}:0", 1) == "win"
    assert outcome(fs, f"{M}:0", 3) == "disengage"


def test_back_to_back_fights_sharing_a_team_stay_separate():
    d = dmg(EXCHANGE + [(20.0, "A1", "C1", 40), (21.0, "C1", "A1", 20)])  # A beats B, then meets C 18 s later
    fs = sides(d)
    assert fs["fight_id"].nunique() == 2 and not fs["multi_team"].any()


def test_overlap_tolerance_links_near_misses():
    near = dmg([(0.0, "A1", "B1", 20), (1.0, "A1", "B1", 20), (1.5, "A1", "C1", 20), (2.5, "A1", "C1", 20)])
    assert sides(near, overlap_tol_s=0.0)["fight_id"].nunique() == 2  # B segment ends at 1.0, C starts at 1.5
    assert sides(near, overlap_tol_s=0.5)["fight_id"].nunique() == 1
    far = dmg([(0.0, "A1", "B1", 20), (1.0, "A1", "B1", 20), (3.0, "A1", "C1", 20), (4.0, "A1", "C1", 20)])
    assert sides(far, overlap_tol_s=0.5)["fight_id"].nunique() == 2
    assert sides(far, overlap_tol_s=2.0)["fight_id"].nunique() == 1


def test_team_at_hit_time_after_mid_match_team_change():
    # B1 switches from team 2 to team 3 at t=50.
    teams = teams_frame([(M, "B1", 50.0, 3)])
    fs = sides(dmg([(60.0, "A1", "B1", 30), (61.0, "B1", "A1", 30)]), teams=teams)
    assert sorted(fs["team_index"]) == [1, 3]
    early = sides(dmg([(10.0, "A1", "B1", 30), (11.0, "B1", "A1", 30)]), teams=teams)
    assert sorted(early["team_index"]) == [1, 2]


def test_solo_elim_without_knock_counts_but_team_mode_default_does_not():
    solo_teams = pd.DataFrame([(M, "S1", 0.0, 1), (M, "S2", 0.0, 2)], columns=["match_id", "player_id", "t", "team_index"])
    solo_players = players_frame(["S1", "S2"])
    d = dmg([(0.0, "S1", "S2", 60), (1.0, "S2", "S1", 20), (2.0, "S1", "S2", 40)])
    e = elim([(2.2, "S1", "S2", False)])
    fs = sides(d, e, teams=solo_teams, players=solo_players)
    assert outcome(fs, f"{M}:0", 1) == "win" and outcome(fs, f"{M}:0", 2) == "loss"
    # same elimination in a duo match is ignored by default, counted with direct_elim_all_modes
    duo = sides(dmg(EXCHANGE), elim([(2.5, "A1", "B1", False)]))
    assert set(duo["outcome"]) == {"disengage"}
    duo_all = sides(dmg(EXCHANGE), elim([(2.5, "A1", "B1", False)]), direct_elim_all_modes=True)
    assert outcome(duo_all, f"{M}:0", 1) == "win"


def test_elim_after_an_earlier_knock_is_not_a_direct_elim():
    e = elim([(2.2, "A1", "B1", True), (2.8, "A2", "B1", False)])
    ev = outcome_events(e, teams_frame(), solo_matches=set(), direct_elim_all_modes=True)
    assert len(ev) == 1 and ev["t"].iloc[0] == 2.2


def test_fight_ids_are_deterministic_and_ordered_by_t0():
    d = dmg([(50.0, "A1", "C1", 30), (51.0, "C1", "A1", 30), (0.0, "A1", "B1", 30), (1.0, "B1", "A1", 30)])
    fs = sides(d)
    first = fs[fs["fight_id"] == f"{M}:0"]
    assert first["t0"].iloc[0] == 0.0 and sorted(first["team_index"]) == [1, 2]
    shuffled = sides(d.sample(frac=1.0, random_state=3).reset_index(drop=True))
    pd.testing.assert_frame_equal(fs, shuffled)
    pd.testing.assert_frame_equal(fs, sides(d))


def test_matches_do_not_merge_and_ids_are_per_match():
    d = pd.concat([dmg(EXCHANGE), dmg(EXCHANGE, match="m2")], ignore_index=True)
    t = pd.concat([teams_frame(), teams_frame().assign(match_id="m2")], ignore_index=True)
    p = pd.concat([players_frame(), players_frame(match="m2")], ignore_index=True)
    fs = build_fight_sides(d, t, no_elims(), p, pd.DataFrame({"match_id": [M, "m2"], "replay_owner": ["A1", "A1"]}))
    assert set(fs["fight_id"]) == {"m1:0", "m2:0"}


def test_poke_classification():
    one_sided = sides(dmg([(0.0, "A1", "B1", 20), (1.0, "A1", "B1", 20)]))
    assert (one_sided["engagement_type"] == "poke").all() and not one_sided["mutual"].any()
    assert one_sided["minority_damage_share"].eq(0).all()
    even = sides(dmg([(0.0, "A1", "B1", 50), (0.5, "B1", "A1", 50)]))
    assert (even["engagement_type"] == "fight").all() and even["minority_damage_share"].iloc[0] == 0.5
    five = dmg([(0.0, "A1", "B1", 95), (0.5, "B1", "A1", 5)])
    assert (sides(five)["engagement_type"] == "poke").all() and sides(five)["mutual"].all()
    fifteen = dmg([(0.0, "A1", "B1", 85), (0.5, "B1", "A1", 15)])
    assert (sides(fifteen)["engagement_type"] == "fight").all()
    assert (sides(fifteen, poke_minority_share=0.2)["engagement_type"] == "poke").all()


def test_pick_is_one_sided_with_a_knock_and_keeps_win_loss():
    fs = sides(dmg([(0.0, "A1", "B1", 100)]), elim([(0.5, "A1", "B1", True)]))
    assert (fs["engagement_type"] == "pick").all() and not fs["mutual"].any()
    assert outcome(fs, f"{M}:0", 1) == "win" and outcome(fs, f"{M}:0", 2) == "loss"


def test_knock_inside_grace_after_last_hit_makes_a_pick_and_after_grace_a_poke():
    d = dmg([(0.0, "A1", "B1", 40), (1.0, "A1", "B1", 40)])
    assert (sides(d, elim([(1.0 + GRACE_S - 0.1, "A1", "B1", True)]))["engagement_type"] == "pick").all()
    assert (sides(d, elim([(1.0 + GRACE_S + 0.1, "A1", "B1", True)]))["engagement_type"] == "poke").all()


def test_knock_by_a_third_party_outside_the_engagement_does_not_make_a_pick():
    fs = sides(dmg([(0.0, "A1", "B1", 40), (1.0, "A1", "B1", 40)]), elim([(1.5, "C1", "B1", True)]))
    assert (fs["engagement_type"] == "poke").all() and set(fs["outcome"]) == {"disengage"}


def test_mutual_fight_with_or_without_a_knock_stays_a_fight():
    assert (sides(dmg(EXCHANGE), elim([(2.5, "A1", "B1", True)]))["engagement_type"] == "fight").all()
    assert (sides(dmg(EXCHANGE))["engagement_type"] == "fight").all()


def test_three_way_shares_partition_the_fights():
    d = pd.concat([dmg(EXCHANGE), dmg([(100.0, "A1", "C1", 50)]), dmg([(200.0, "A1", "B1", 50)])], ignore_index=True)
    e = elim([(2.5, "A1", "B1", True), (200.5, "A1", "B1", True)])
    fs = sides(d, e).drop_duplicates("fight_id")
    assert sorted(fs["engagement_type"]) == ["fight", "pick", "poke"]


def test_label_only_columns_cannot_be_features():
    from fnf.fights import LABEL_ONLY_COLUMNS, assert_no_label_features
    assert "engagement_type" in LABEL_ONLY_COLUMNS and "outcome" in LABEL_ONLY_COLUMNS
    assert_no_label_features(["t0", "match_id"])
    for col in ("engagement_type", "outcome", "mutual", "damage_dealt"):
        try:
            assert_no_label_features(["t0", col])
        except ValueError:
            continue
        raise AssertionError(f"{col} should be rejected")
    assert set(LABEL_ONLY_COLUMNS) <= set(sides(dmg(EXCHANGE)).columns)


def test_hit_distance_from_positions():
    d = engagement_damage(dmg([(1.0, "A1", "B1", 30), (2.0, "A1", "B1", 30)]), teams_frame())
    pos = pd.DataFrame([(M, "A1", 0.5, 0, 0, 0), (M, "B1", 0.5, 3000, 4000, 0), (M, "A1", 1.9, 0, 0, 0)],
                       columns=["match_id", "player_id", "t", "x", "y", "z"])
    dist = hit_distances(group_fights(d), pos)
    assert dist.iloc[0] == 50.0  # 3-4-5 triangle in uu -> 5000 uu = 50 m
    assert dist.iloc[1] == 50.0 or np.isnan(dist.iloc[1])  # B1's last update is 1.5 s old: within the 2 s max age
    fs = sides(dmg([(1.0, "A1", "B1", 30), (2.0, "A1", "B1", 30)]), positions=pos)
    assert fs["dist_max_m"].iloc[0] == 50.0
    assert sides(dmg([(1.0, "A1", "B1", 30)]))["dist_max_m"].isna().all()


def test_stale_position_gives_no_distance():
    d = group_fights(engagement_damage(dmg([(10.0, "A1", "B1", 30)]), teams_frame()))
    pos = pd.DataFrame([(M, "A1", 0.0, 0, 0, 0), (M, "B1", 0.0, 100, 0, 0)],
                       columns=["match_id", "player_id", "t", "x", "y", "z"])
    assert hit_distances(d, pos).isna().all()


def test_seg_version_names_the_parameter_set():
    assert seg_version() == "v2-gap10-tol1-grace3-poke10-conv20"
    assert seg_version(5, 0, 1, 0.2, 30) == "v2-gap5-tol0-grace1-poke20-conv30"
    assert (sides(dmg(EXCHANGE), gap_s=5)["seg_version"] == seg_version(gap_s=5)).all()


def test_label_outcomes_unit():
    ev = pd.DataFrame({"t": [5.0], "victim_team": [2], "killer_team": [1]})
    assert label_outcomes({1, 2}, 0.0, 4.0, ev) == {1: "win", 2: "loss"}
    assert label_outcomes({1, 2}, 0.0, 1.0, ev) == {1: "disengage", 2: "disengage"}


def _truncate(frame, col, cutoff):
    return frame[frame[col] <= cutoff].reset_index(drop=True)


def test_leakage_guard_later_events_do_not_change_a_fight():
    # Three fights in sequence; deleting everything after fight 0's t_end + GRACE_S must not change fight 0.
    d = dmg(EXCHANGE + [(40.0, "A1", "C1", 50), (41.0, "C1", "A1", 30), (80.0, "B1", "C1", 60)])
    e = elim([(2.5, "A1", "B1", True), (42.0, "C1", "A1", True), (81.0, "B1", "C1", True)])
    full = sides(d, e)
    keep = ["fight_id", "team_index", "t0", "t_end", "players", "outcome", "engagement_type", "mutual", "multi_team",
            "hits_dealt", "hits_taken", "damage_dealt", "damage_taken"]
    for fid in sorted(full["fight_id"].unique()):
        rows = full[full["fight_id"] == fid]
        cutoff = rows["t_end"].iloc[0] + GRACE_S
        cut = sides(_truncate(d, "t", cutoff), _truncate(e.assign(t=e["t_ms"] / 1000), "t", cutoff).drop(columns="t"))
        got = cut[cut["fight_id"] == fid]
        pd.testing.assert_frame_equal(rows[keep].reset_index(drop=True), got[keep].reset_index(drop=True))
