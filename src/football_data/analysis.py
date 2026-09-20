"""Turn raw StatsBomb events into tables and summary stats.

Plotting stays in ``viz.py``. High-level helpers here load a match, build the
table, and return a figure so a notebook or API can call one function.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from matplotlib.figure import Figure

from football_data.data import MatchInfo, load_events


def _xy(location: Any) -> tuple[float | None, float | None]:
    """Unpack StatsBomb ``[x, y]`` locations.

    Fresh ``statsbombpy`` frames (and Parquet round-trips) often store
    coordinates as ``numpy.ndarray``, not ``list``/``tuple`` — both must work.
    """
    if location is None:
        return None, None
    try:
        if hasattr(location, "__len__") and len(location) >= 2:
            return float(location[0]), float(location[1])
    except (TypeError, ValueError):
        return None, None
    return None, None


def resolve_player(events: pd.DataFrame, name_fragment: str) -> str:
    """Return the StatsBomb player name matching ``name_fragment`` (e.g. ``\"Messi\"``)."""
    players = events["player"].dropna().unique()
    hits = [p for p in players if name_fragment.lower() in str(p).lower()]
    if not hits:
        raise ValueError(f"No player matching {name_fragment!r} in this match.")
    return sorted(hits, key=len)[0]


def shots_table(
    events: pd.DataFrame,
    *,
    include_shootout: bool = True,
) -> pd.DataFrame:
    """Shots with unpacked coordinates and xG — ready to plot or serialize as JSON.

    Penalty *shootouts* are StatsBomb period 5. Leave them out of xG views so
    the map describes the match, not the lottery at the end.
    """
    shots = events.loc[events["type"] == "Shot"].copy()
    if not include_shootout and "period" in shots.columns:
        shots = shots.loc[shots["period"] != 5]
    coords = shots["location"].map(_xy)
    shots["x"] = coords.map(lambda xy: xy[0])
    shots["y"] = coords.map(lambda xy: xy[1])
    if "shot_statsbomb_xg" in shots.columns:
        shots["xg"] = pd.to_numeric(shots["shot_statsbomb_xg"], errors="coerce")
    else:
        shots["xg"] = pd.NA
    shots["is_goal"] = shots["shot_outcome"].eq("Goal")
    return shots.reset_index(drop=True)


def shot_summary(shots: pd.DataFrame) -> pd.DataFrame:
    """Per-team shot count, goals, and summed StatsBomb xG."""
    frame = shots.copy()
    if "is_goal" not in frame.columns:
        frame["is_goal"] = frame["shot_outcome"].eq("Goal")
    aggs: dict[str, tuple[str, str]] = {
        "shots": ("is_goal", "count"),
        "goals": ("is_goal", "sum"),
    }
    if "xg" in frame.columns:
        aggs["xg"] = ("xg", "sum")
    return frame.groupby("team", as_index=False).agg(**aggs)


def match_shot_summary(
    match: MatchInfo,
    *,
    include_shootout: bool = False,
) -> pd.DataFrame:
    """Per-team shots / goals / xG for one match, with match labels on the table."""
    events = load_events(match.match_id)
    shots = shots_table(events, include_shootout=include_shootout)
    table = shot_summary(shots)
    table.insert(0, "match", f"{match.home_team} vs {match.away_team}")
    table.insert(1, "match_id", match.match_id)
    return table


def completed_passes_table(events: pd.DataFrame, player: str) -> pd.DataFrame:
    """Completed passes for one player, with start/end coordinates.

    StatsBomb leaves ``pass_outcome`` empty on completions; incompletions are
    tagged Incomplete, Out, Offside, etc.
    """
    resolved = resolve_player(events, player)
    passes = events.loc[
        (events["type"] == "Pass") & (events["player"] == resolved)
    ].copy()
    completed = passes[passes["pass_outcome"].isna()].copy()
    start = completed["location"].map(_xy)
    end = completed["pass_end_location"].map(_xy)
    completed["x"] = start.map(lambda xy: xy[0])
    completed["y"] = start.map(lambda xy: xy[1])
    completed["end_x"] = end.map(lambda xy: xy[0])
    completed["end_y"] = end.map(lambda xy: xy[1])
    completed.attrs["player"] = resolved
    return completed.reset_index(drop=True)


def pass_completion(events: pd.DataFrame, player: str) -> dict[str, Any]:
    """Attempted vs completed passes for one player (JSON-friendly)."""
    resolved = resolve_player(events, player)
    passes = events.loc[
        (events["type"] == "Pass") & (events["player"] == resolved)
    ]
    attempted = int(len(passes))
    completed = int(passes["pass_outcome"].isna().sum())
    pct = round(100.0 * completed / attempted, 1) if attempted else 0.0
    return {
        "player": resolved,
        "attempted": attempted,
        "completed": completed,
        "completion_pct": pct,
    }


def get_shot_map(
    match: MatchInfo,
    *,
    save_path: str | Path | None = None,
    title: str | None = None,
) -> Figure:
    """Load a match and draw a two-team shot map (away team attacking left)."""
    from football_data.viz import plot_shot_map

    events = load_events(match.match_id)
    shots = shots_table(events)
    return plot_shot_map(
        shots,
        home_team=match.home_team,
        away_team=match.away_team,
        title=title,
        save_path=save_path,
    )


def get_xg_shot_map(
    match: MatchInfo,
    *,
    include_shootout: bool = False,
    save_path: str | Path | None = None,
    title: str | None = None,
) -> Figure:
    """Load a match and draw a shot map with marker size proportional to xG."""
    from football_data.viz import plot_xg_shot_map

    events = load_events(match.match_id)
    shots = shots_table(events, include_shootout=include_shootout)
    return plot_xg_shot_map(
        shots,
        home_team=match.home_team,
        away_team=match.away_team,
        title=title,
        save_path=save_path,
    )


def get_pass_map(
    match: MatchInfo,
    player: str,
    *,
    save_path: str | Path | None = None,
    title: str | None = None,
) -> Figure:
    """Load a match and draw one player's completed-pass map."""
    from football_data.viz import plot_pass_map

    events = load_events(match.match_id)
    completed = completed_passes_table(events, player)
    resolved = completed.attrs.get("player") or resolve_player(events, player)
    return plot_pass_map(
        completed,
        player=resolved,
        title=title
        or f"{resolved} — completed passes\n{match.home_team} vs {match.away_team}",
        save_path=save_path,
    )
