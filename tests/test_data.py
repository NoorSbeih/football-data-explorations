from __future__ import annotations

import pandas as pd
import pytest

import football_data.data as data_module
from football_data.data import MatchInfo, find_match, get_showcase_match, match_to_dict


def _fake_matches() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "match_id": 111,
                "home_team": "Home FC",
                "away_team": "Away FC",
                "home_score": 2,
                "away_score": 1,
                "match_date": "2022-01-01",
                "competition_stage": "Final",
            },
            {
                "match_id": 112,
                "home_team": "Home FC",
                "away_team": "Away FC",
                "home_score": 0,
                "away_score": 0,
                "match_date": "2021-01-01",
                "competition_stage": "Group Stage",
            },
        ]
    )


def test_find_match_prefers_the_requested_stage(monkeypatch):
    monkeypatch.setattr(
        data_module, "get_matches", lambda competition_id, season_id: _fake_matches()
    )

    match = find_match(43, 106, home_team="Home FC", away_team="Away FC", stage="Final")

    assert match.match_id == 111
    assert match.home_score == 2


def test_find_match_matches_teams_regardless_of_home_away_order(monkeypatch):
    monkeypatch.setattr(
        data_module, "get_matches", lambda competition_id, season_id: _fake_matches()
    )

    match = find_match(43, 106, home_team="Away FC", away_team="Home FC")

    assert match.match_id in {111, 112}


def test_find_match_raises_when_teams_never_played(monkeypatch):
    monkeypatch.setattr(
        data_module, "get_matches", lambda competition_id, season_id: _fake_matches()
    )

    with pytest.raises(ValueError):
        find_match(43, 106, home_team="Nobody", away_team="Nobody Else")


def test_match_to_dict_shapes_a_json_friendly_payload():
    match = MatchInfo(match_id=1, home_team="A", away_team="B", home_score=3, away_score=1)

    assert match_to_dict(match) == {
        "match_id": 1,
        "home_team": "A",
        "away_team": "B",
        "home_score": 3,
        "away_score": 1,
        "match_date": None,
        "competition_stage": None,
        "label": "A vs B",
    }


def test_get_showcase_match_returns_the_known_match(monkeypatch):
    known = [MatchInfo(match_id=42, home_team="A", away_team="B")]
    monkeypatch.setattr(data_module, "showcase_matches", lambda: known)

    assert get_showcase_match(42) is known[0]


def test_get_showcase_match_raises_for_an_unknown_id(monkeypatch):
    monkeypatch.setattr(data_module, "showcase_matches", lambda: [])

    with pytest.raises(ValueError):
        get_showcase_match(9999)
