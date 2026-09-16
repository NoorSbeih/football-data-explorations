"""Pitch-map rendering. Analysis tables come from ``analysis.py``."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from mplsoccer import Pitch

STATSBomb_LENGTH = 120.0
STATSBomb_WIDTH = 80.0

TEAM_COLORS = {
    "Argentina": "#75AADB",
    "France": "#002654",
    "Croatia": "#C60C30",
    "Tottenham Hotspur": "#132257",
    "Liverpool": "#C8102E",
    "Italy": "#0068A8",
    "England": "#CE1124",
    "Spain Women's": "#AA151B",
    "England Women's": "#0033A0",
}

_PITCH_COLOR = "#1a472a"
_LINE_COLOR = "#f0f0f0"


def _pitch() -> tuple[Pitch, Figure, object]:
    pitch = Pitch(pitch_type="statsbomb", pitch_color=_PITCH_COLOR, line_color=_LINE_COLOR)
    fig, ax = pitch.draw(figsize=(10, 7))
    fig.set_facecolor(_PITCH_COLOR)
    return pitch, fig, ax


def _maybe_save(fig: Figure, save_path: str | Path | None) -> None:
    if save_path is None:
        return
    path = Path(save_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=160, bbox_inches="tight", facecolor=fig.get_facecolor())


def invert_xy(x: pd.Series, y: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Flip StatsBomb coordinates so the team attacks the left goal."""
    return STATSBomb_LENGTH - x, STATSBomb_WIDTH - y


def xg_marker_size(xg: pd.Series | float) -> pd.Series | float:
    """Map expected-goals values to scatter sizes."""
    if isinstance(xg, pd.Series):
        return 50.0 + xg.fillna(0).clip(lower=0) * 900.0
    return 50.0 + max(float(xg), 0.0) * 900.0


def plot_shot_map(
    shots: pd.DataFrame,
    *,
    home_team: str,
    away_team: str,
    title: str | None = None,
    save_path: str | Path | None = None,
) -> Figure:
    """Plot shots color-coded by team. Goals are gold-edged stars.

    StatsBomb stores every shot in the attacking direction (x toward 120).
    The away team is inverted so the two teams attack opposite ends.
    """
    pitch, fig, ax = _pitch()
    frame = shots.dropna(subset=["x", "y"])

    for team, group in frame.groupby("team"):
        color = TEAM_COLORS.get(str(team), "#dddddd")
        xs, ys = group["x"], group["y"]
        if team == away_team:
            xs, ys = invert_xy(xs, ys)
        if "is_goal" in group.columns:
            is_goal = group["is_goal"]
        else:
            is_goal = group["shot_outcome"].eq("Goal")

        pitch.scatter(
            xs.loc[~is_goal],
            ys.loc[~is_goal],
            s=120,
            c=color,
            ax=ax,
            edgecolors="white",
            linewidth=0.8,
            alpha=0.85,
            marker="o",
            label=f"{team} shot",
            zorder=3,
        )
        pitch.scatter(
            xs.loc[is_goal],
            ys.loc[is_goal],
            s=280,
            c=color,
            ax=ax,
            edgecolors="gold",
            linewidth=1.6,
            marker="*",
            label=f"{team} goal",
            zorder=4,
        )

    ax.legend(loc="upper left", frameon=True, fontsize=8)
    ax.set_title(
        title
        or (
            f"{home_team} vs {away_team}\n"
            f"Shot map (stars = goals; {away_team} attacking left)"
        ),
        color="white",
        pad=12,
        fontsize=13,
    )
    _maybe_save(fig, save_path)
    return fig


def plot_xg_shot_map(
    shots: pd.DataFrame,
    *,
    home_team: str,
    away_team: str,
    title: str | None = None,
    save_path: str | Path | None = None,
) -> Figure:
    """Shot map where marker size is StatsBomb xG and a gold edge marks a goal.

    Away-team shots are inverted. Penalty shootouts should already be filtered
    out of ``shots`` (see ``shots_table(..., include_shootout=False)``).
    """
    pitch, fig, ax = _pitch()
    frame = shots.dropna(subset=["x", "y"]).copy()
    if "xg" not in frame.columns:
        frame["xg"] = 0.0
    if "is_goal" not in frame.columns:
        frame["is_goal"] = (
            frame["shot_outcome"].eq("Goal") if "shot_outcome" in frame.columns else False
        )

    for team, group in frame.groupby("team"):
        color = TEAM_COLORS.get(str(team), "#dddddd")
        xs, ys = group["x"], group["y"]
        if team == away_team:
            xs, ys = invert_xy(xs, ys)
        sizes = xg_marker_size(group["xg"])
        edges = ["gold" if goal else "white" for goal in group["is_goal"]]
        widths = [1.8 if goal else 0.6 for goal in group["is_goal"]]
        pitch.scatter(
            xs,
            ys,
            s=sizes,
            c=color,
            ax=ax,
            edgecolors=edges,
            linewidth=widths,
            alpha=0.88,
            marker="o",
            zorder=3,
        )

    team_handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=TEAM_COLORS.get(home_team, "#dddddd"),
            markeredgecolor="white",
            markersize=9,
            label=home_team,
        ),
        Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=TEAM_COLORS.get(away_team, "#dddddd"),
            markeredgecolor="white",
            markersize=9,
            label=away_team,
        ),
        Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor="none",
            markeredgecolor="gold",
            markeredgewidth=1.8,
            markersize=9,
            label="Goal",
        ),
    ]
    leg_teams = ax.legend(
        handles=team_handles, loc="upper left", frameon=True, fontsize=8
    )
    ax.add_artist(leg_teams)

    size_handles = [
        ax.scatter(
            [],
            [],
            s=float(xg_marker_size(val)),
            c="#f0f0f0",
            edgecolors="white",
            linewidths=0.6,
            label=f"{val:.2f} xG",
        )
        for val in (0.05, 0.15, 0.35)
    ]
    ax.legend(
        handles=size_handles,
        loc="lower left",
        frameon=True,
        fontsize=8,
        title="Chance quality",
    )

    ax.set_title(
        title
        or (
            f"{home_team} vs {away_team}\n"
            f"xG shot map (size = xG; gold edge = goal; {away_team} attacking left)"
        ),
        color="white",
        pad=12,
        fontsize=13,
    )
    _maybe_save(fig, save_path)
    return fig


def plot_pass_map(
    completed: pd.DataFrame,
    *,
    player: str,
    title: str | None = None,
    save_path: str | Path | None = None,
) -> Figure:
    """Draw arrows for completed passes (expects ``x, y, end_x, end_y`` columns)."""
    pitch, fig, ax = _pitch()
    frame = completed.dropna(subset=["x", "y", "end_x", "end_y"])
    pitch.arrows(
        frame["x"],
        frame["y"],
        frame["end_x"],
        frame["end_y"],
        ax=ax,
        width=1.4,
        headwidth=4,
        headlength=4,
        color="#F6C945",
        alpha=0.8,
    )
    ax.set_title(
        title or f"{player} — completed passes",
        color="white",
        pad=12,
        fontsize=13,
    )
    _maybe_save(fig, save_path)
    return fig
