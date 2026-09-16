from __future__ import annotations

import pandas as pd
import pytest
from matplotlib.figure import Figure

from football_data.analysis import completed_passes_table, shots_table
from football_data.viz import (
    invert_xy,
    plot_pass_map,
    plot_shot_map,
    plot_xg_shot_map,
    xg_marker_size,
)


def test_invert_xy_flips_within_pitch_bounds():
    x, y = invert_xy(pd.Series([0, 120]), pd.Series([0, 80]))
    assert list(x) == [120, 0]
    assert list(y) == [80, 0]


def test_xg_marker_size_scales_with_xg_for_scalars():
    assert xg_marker_size(0.0) == 50.0
    assert xg_marker_size(1.0) == pytest.approx(950.0)
    assert xg_marker_size(-0.5) == 50.0  # clipped, never shrinks below the floor


def test_xg_marker_size_handles_a_series_with_missing_values():
    sizes = xg_marker_size(pd.Series([0.0, 0.5, None]))
    assert sizes.tolist() == pytest.approx([50.0, 500.0, 50.0])


def test_plot_shot_map_returns_a_figure(sample_events):
    shots = shots_table(sample_events, include_shootout=True)
    fig = plot_shot_map(shots, home_team="Home FC", away_team="Away FC")
    assert isinstance(fig, Figure)


def test_plot_xg_shot_map_returns_a_figure(sample_events):
    shots = shots_table(sample_events, include_shootout=False)
    fig = plot_xg_shot_map(shots, home_team="Home FC", away_team="Away FC")
    assert isinstance(fig, Figure)


def test_plot_pass_map_returns_a_figure(sample_events):
    completed = completed_passes_table(sample_events, "Playmaker")
    fig = plot_pass_map(completed, player="Playmaker C")
    assert isinstance(fig, Figure)
