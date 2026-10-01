import pandas as pd

from fnf.builds import attribute_builders, detect_edits, parse_pieces

BUILD_COLS = ["match_id", "spawn_t", "path", "x", "y", "z", "yaw", "close_t", "team_index"]


def _builds(rows):
    return pd.DataFrame(rows, columns=BUILD_COLS)


def test_predicted_spawn_is_merged_into_confirmed_piece():
    b = _builds([
        ("m", 10.00, "PBWA_W1_Solid_C", 0, 0, 0, 0, 10.02, None),  # predicted
        ("m", 10.05, "PBWA_W1_Solid_C", 0, 0, 0, 0, 50.0, 3),  # confirmed
    ])
    p = parse_pieces(b)
    assert len(p) == 1
    assert p.loc[0, ["spawn_t", "close_t", "team_index", "kind", "material"]].tolist() == [10.0, 50.0, 3, "wall", "wood"]


def test_edit_and_reset_detected_in_same_cell():
    b = _builds([
        ("m", 1.0, "PBWA_W1_Solid_C", 0, 0, 0, 0, 5.0, 3),
        ("m", 5.1, "PBWA_W1_ArchwayLarge_C", 0, 0, 0, 0, 8.0, 3),  # edit
        ("m", 8.1, "PBWA_W1_Solid_C", 0, 0, 0, 0, 20.0, 3),  # reset
        ("m", 9.0, "PBWA_W1_Solid_C", 512, 0, 0, 0, 20.0, 3),  # new piece elsewhere
    ])
    e = detect_edits(parse_pieces(b)).set_index("spawn_t")
    assert e.loc[5.1, "is_edit"] and not e.loc[5.1, "is_reset"]
    assert e.loc[8.1, "is_reset"] and not e.loc[8.1, "is_edit"]
    assert not e.loc[9.0, "is_edit"] and not e.loc[9.0, "is_reset"]


def test_builder_from_team_beats_nearest_player():
    pieces = detect_edits(parse_pieces(_builds([("m", 10.0, "PBWA_W1_Floor_C", 0, 0, 0, 0, 30.0, 7)])))
    positions = pd.DataFrame(
        [("m", 9.0, "near_enemy", 10, 0, 0), ("m", 9.0, "far_teammate", 700, 0, 0)],
        columns=["match_id", "t", "player_id", "x", "y", "z"],
    )
    teams = pd.DataFrame(
        [("m", 0.0, "near_enemy", 4), ("m", 0.0, "far_teammate", 7)],
        columns=["match_id", "t", "player_id", "team_index"],
    )
    out = attribute_builders(pieces, positions, teams)
    assert out.loc[0, "builder"] == "far_teammate" and out.loc[0, "builder_source"] == "team"


def test_build_tool_holder_beats_nearer_teammate_for_new_pieces():
    pieces = detect_edits(parse_pieces(_builds([("m", 10.0, "PBWA_W1_Solid_C", 0, 0, 0, 0, 30.0, 7)])))
    positions = pd.DataFrame(
        [("m", 9.0, "near_shooting", 100, 0, 0), ("m", 9.0, "far_building", 500, 0, 0)],
        columns=["match_id", "t", "player_id", "x", "y", "z"],
    )
    teams = pd.DataFrame(
        [("m", 0.0, "near_shooting", 7), ("m", 0.0, "far_building", 7)],
        columns=["match_id", "t", "player_id", "team_index"],
    )
    weapons = pd.DataFrame(
        [("m", 8.0, "near_shooting", "B_Shotgun_Pump_Athena_C"), ("m", 8.0, "far_building", "DefaultBuildingTool_C")],
        columns=["match_id", "t", "player_id", "weapon_class"],
    )
    out = attribute_builders(pieces, positions, teams, weapons)
    assert out.loc[0, "builder"] == "far_building" and out.loc[0, "builder_source"] == "team+tool"


def test_edits_ignore_held_item():
    pieces = detect_edits(parse_pieces(_builds([
        ("m", 1.0, "PBWA_W1_Solid_C", 0, 0, 0, 0, 10.0, 7),
        ("m", 10.1, "PBWA_W1_DoorC_C", 0, 0, 0, 0, 30.0, 7),
    ])))
    positions = pd.DataFrame(
        [("m", 0.5, "a", 100, 0, 0), ("m", 0.5, "b", 500, 0, 0)],
        columns=["match_id", "t", "player_id", "x", "y", "z"],
    )
    teams = pd.DataFrame([("m", 0.0, "a", 7), ("m", 0.0, "b", 7)], columns=["match_id", "t", "player_id", "team_index"])
    weapons = pd.DataFrame([("m", 0.0, "b", "DefaultBuildingTool_C")], columns=["match_id", "t", "player_id", "weapon_class"])
    out = attribute_builders(pieces, positions, teams, weapons).set_index("spawn_t")
    assert out.loc[10.1, "is_edit"] and out.loc[10.1, "builder"] == "a"
