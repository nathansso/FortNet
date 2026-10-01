"""Synthetic frame builders shared by the fight and poke tests."""

import numpy as np
import pandas as pd

from fnf.fights import build_fight_sides

M = "m1"
TEAM = {"A1": 1, "A2": 1, "B1": 2, "B2": 2, "C1": 3, "C2": 3}


def teams_frame(extra=()):
    rows = [(M, p, 0.0, t) for p, t in TEAM.items()] + list(extra)
    return pd.DataFrame(rows, columns=["match_id", "player_id", "t", "team_index"])


def dmg(rows, match=M):
    """rows: (t, source, target, magnitude)"""
    return pd.DataFrame([(match, t, s, g, m) for t, s, g, m in rows],
                        columns=["match_id", "t", "source", "target", "magnitude"])


def elim(rows, match=M):
    """rows: (t_seconds, eliminator, eliminated, knocked)"""
    return pd.DataFrame([(match, int(t * 1000), a, b, k) for t, a, b, k in rows],
                        columns=["match_id", "t_ms", "eliminator", "eliminated", "knocked"])


def no_elims():
    return elim([])


def players_frame(ids=None, match=M):
    ids = ids or list(TEAM)
    return pd.DataFrame({"match_id": match, "player_id": ids, "is_bot": False, "death_time": np.nan})


def matches_frame(owner="A1", match=M):
    return pd.DataFrame({"match_id": [match], "replay_owner": [owner]})


def sides(damage, elims=None, teams=None, players=None, owner="A1", **kw):
    return build_fight_sides(damage, teams if teams is not None else teams_frame(),
                             elims if elims is not None else no_elims(),
                             players if players is not None else players_frame(), matches_frame(owner), **kw)
