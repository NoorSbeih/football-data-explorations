"""Shared fixtures. No test in this suite hits the network — StatsBomb calls
(``statsbombpy.sb.matches`` / ``sb.events``) are monkeypatched wherever they'd
otherwise be exercised, and a small hand-built events table stands in for a
real match everywhere else.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")  # headless backend so plotting tests don't need a display

import pandas as pd
import pytest


@pytest.fixture
def sample_events() -> pd.DataFrame:
    """A tiny, hand-built StatsBomb-shaped events table.

    Covers everything ``analysis.py`` touches: shots with and without a
    goal outcome, a period-5 (penalty shootout) shot that should be
    excludable, and one player's completed + incomplete passes.
    """
    rows = [
        {
            "type": "Shot",
            "team": "Home FC",
            "player": "Striker A",
            "location": [110, 40],
            "shot_outcome": "Goal",
            "shot_statsbomb_xg": 0.42,
            "period": 2,
        },
        {
            "type": "Shot",
            "team": "Home FC",
            "player": "Striker A",
            "location": [95, 30],
            "shot_outcome": "Saved",
            "shot_statsbomb_xg": 0.08,
            "period": 1,
        },
        {
            "type": "Shot",
            "team": "Away FC",
            "player": "Forward B",
            "location": [12, 38],
            "shot_outcome": "Off T",
            "shot_statsbomb_xg": 0.05,
            "period": 1,
        },
        # Penalty shootout (period 5) — excluded from xG views by default.
        {
            "type": "Shot",
            "team": "Away FC",
            "player": "Forward B",
            "location": [108, 40],
            "shot_outcome": "Goal",
            "shot_statsbomb_xg": 0.76,
            "period": 5,
        },
        {
            "type": "Pass",
            "team": "Home FC",
            "player": "Playmaker C",
            "location": [60, 40],
            "pass_end_location": [80, 42],
            "pass_outcome": None,
        },
        {
            "type": "Pass",
            "team": "Home FC",
            "player": "Playmaker C",
            "location": [70, 20],
            "pass_end_location": [90, 25],
            "pass_outcome": "Incomplete",
        },
    ]
    return pd.DataFrame(rows)
