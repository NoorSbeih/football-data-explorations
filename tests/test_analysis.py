from __future__ import annotations

import numpy as np
import pytest

from football_data.analysis import (
    completed_passes_table,
    match_shot_summary,
    pass_completion,
    resolve_player,
    shot_summary,
    shots_table,
)
from football_data.data import MatchInfo


def test_shots_table_unpacks_coordinates_and_xg(sample_events):
    shots = shots_table(sample_events, include_shootout=True)
    assert len(shots) == 4

    first_goal = shots.loc[shots["shot_outcome"] == "Goal"].iloc[0]
    assert (first_goal["x"], first_goal["y"]) == (110, 40)
    assert bool(first_goal["is_goal"]) is True


def test_shots_table_unpacks_numpy_ndarray_locations(sample_events):
    """statsbombpy / Parquet store locations as ndarray, not list."""
    events = sample_events.copy()
    events["location"] = events["location"].map(
        lambda xy: np.asarray(xy) if xy is not None else xy
    )
    events["pass_end_location"] = events["pass_end_location"].map(
        lambda xy: np.asarray(xy) if isinstance(xy, list) else xy
    )

    shots = shots_table(events, include_shootout=False)
    assert len(shots) == 3
    assert shots[["x", "y"]].notna().all().all()
    assert (shots.iloc[0]["x"], shots.iloc[0]["y"]) == (110.0, 40.0)

    completed = completed_passes_table(events, "Playmaker")
    assert (completed.iloc[0]["x"], completed.iloc[0]["y"]) == (60.0, 40.0)
    assert (completed.iloc[0]["end_x"], completed.iloc[0]["end_y"]) == (80.0, 42.0)


def test_shots_table_excludes_shootout_by_default(sample_events):
    shots = shots_table(sample_events, include_shootout=False)
    assert len(shots) == 3
    assert (shots["period"] != 5).all()


def test_shot_summary_aggregates_per_team(sample_events):
    shots = shots_table(sample_events, include_shootout=False)
    summary = shot_summary(shots).set_index("team")

    assert summary.loc["Home FC", "shots"] == 2
    assert summary.loc["Home FC", "goals"] == 1
    assert summary.loc["Home FC", "xg"] == pytest.approx(0.5)
    assert summary.loc["Away FC", "shots"] == 1
    assert summary.loc["Away FC", "goals"] == 0


def test_match_shot_summary_labels_the_match(sample_events, monkeypatch):
    monkeypatch.setattr(
        "football_data.analysis.load_events", lambda match_id: sample_events
    )
    match = MatchInfo(match_id=999, home_team="Home FC", away_team="Away FC")

    table = match_shot_summary(match)

    assert set(table["match_id"]) == {999}
    assert set(table["match"]) == {"Home FC vs Away FC"}


def test_resolve_player_matches_fragment_case_insensitively(sample_events):
    assert resolve_player(sample_events, "playmaker") == "Playmaker C"


def test_resolve_player_raises_for_unknown_name(sample_events):
    with pytest.raises(ValueError):
        resolve_player(sample_events, "Nobody")


def test_completed_passes_table_only_keeps_completions(sample_events):
    completed = completed_passes_table(sample_events, "Playmaker")

    assert len(completed) == 1
    row = completed.iloc[0]
    assert (row["x"], row["y"]) == (60, 40)
    assert (row["end_x"], row["end_y"]) == (80, 42)


def test_pass_completion_percentage(sample_events):
    stats = pass_completion(sample_events, "Playmaker")

    assert stats == {
        "player": "Playmaker C",
        "attempted": 2,
        "completed": 1,
        "completion_pct": 50.0,
    }
