"""Fetch StatsBomb open-data matches and events.

Every StatsBomb call goes through a tiny local cache (``_read_cache`` /
``_write_cache`` below): the first call for a given match or competition
hits StatsBomb's GitHub-hosted JSON and writes a Parquet file under
``data/cache/``; every call after that reads the Parquet file instead. This
matters in practice — the demo app re-requests the same two matches on every
page load, and a notebook re-run shouldn't re-download anything. Disable it
with ``FOOTBALL_DATA_CACHE=0`` (e.g. to confirm you're seeing fresh data).
"""

from __future__ import annotations

import os
import warnings
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from statsbombpy import sb
from statsbombpy.api_client import NoAuthWarning

warnings.filterwarnings("ignore", category=NoAuthWarning)

WC_COMPETITION_ID = 43
WC_2018_SEASON_ID = 3
WC_2022_COMPETITION_ID = WC_COMPETITION_ID
WC_2022_SEASON_ID = 106
CL_COMPETITION_ID = 16
CL_2019_SEASON_ID = 4
EURO_COMPETITION_ID = 55
EURO_2020_SEASON_ID = 43
WWC_COMPETITION_ID = 72
WWC_2023_SEASON_ID = 107

CACHE_DIR = Path(os.environ.get("FOOTBALL_DATA_CACHE_DIR", "data/cache"))
CACHE_ENABLED = os.environ.get("FOOTBALL_DATA_CACHE", "1") != "0"


def _cache_path(key: str) -> Path:
    return CACHE_DIR / f"{key}.parquet"


def _read_cache(key: str) -> pd.DataFrame | None:
    if not CACHE_ENABLED:
        return None
    path = _cache_path(key)
    return pd.read_parquet(path) if path.exists() else None


def _write_cache(key: str, frame: pd.DataFrame) -> None:
    if not CACHE_ENABLED:
        return
    path = _cache_path(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(path)


@dataclass(frozen=True)
class MatchInfo:
    """Identifying fields for a single StatsBomb match."""

    match_id: int
    home_team: str
    away_team: str
    home_score: int | None = None
    away_score: int | None = None
    match_date: str | None = None
    competition_stage: str | None = None


def _row_to_match(row: pd.Series) -> MatchInfo:
    stage = row["competition_stage"] if "competition_stage" in row.index else None
    date = row["match_date"] if "match_date" in row.index else None
    return MatchInfo(
        match_id=int(row["match_id"]),
        home_team=str(row["home_team"]),
        away_team=str(row["away_team"]),
        home_score=None if pd.isna(row.get("home_score")) else int(row["home_score"]),
        away_score=None if pd.isna(row.get("away_score")) else int(row["away_score"]),
        match_date=None if date is None or pd.isna(date) else str(date),
        competition_stage=None if stage is None or pd.isna(stage) else str(stage),
    )


def get_matches(competition_id: int, season_id: int) -> pd.DataFrame:
    """Return the StatsBomb match list for a competition season (Parquet-cached)."""
    key = f"matches_{competition_id}_{season_id}"
    cached = _read_cache(key)
    if cached is not None:
        return cached
    matches = sb.matches(competition_id=competition_id, season_id=season_id)
    _write_cache(key, matches)
    return matches


def find_match(
    competition_id: int,
    season_id: int,
    *,
    home_team: str,
    away_team: str,
    stage: str | None = None,
) -> MatchInfo:
    """Look up one match by teams (and optional competition stage)."""
    matches = get_matches(competition_id, season_id)
    pair = matches[
        ((matches["home_team"] == home_team) & (matches["away_team"] == away_team))
        | ((matches["home_team"] == away_team) & (matches["away_team"] == home_team))
    ]
    if stage and "competition_stage" in pair.columns:
        staged = pair[pair["competition_stage"] == stage]
        if not staged.empty:
            pair = staged
    if pair.empty:
        raise ValueError(
            f"No match found for {home_team} vs {away_team} "
            f"(competition_id={competition_id}, season_id={season_id})."
        )
    row = pair.sort_values("match_date").iloc[-1]
    return _row_to_match(row)


def world_cup_2018_final() -> MatchInfo:
    """France vs Croatia, Moscow, 15 July 2018."""
    return find_match(
        WC_COMPETITION_ID,
        WC_2018_SEASON_ID,
        home_team="France",
        away_team="Croatia",
        stage="Final",
    )


def world_cup_2022_final() -> MatchInfo:
    """Argentina vs France, Lusail, 18 December 2022 (open-data match_id 3869685)."""
    return find_match(
        WC_2022_COMPETITION_ID,
        WC_2022_SEASON_ID,
        home_team="Argentina",
        away_team="France",
        stage="Final",
    )


def champions_league_2019_final() -> MatchInfo:
    """Tottenham Hotspur vs Liverpool, Madrid, 1 June 2019."""
    return find_match(
        CL_COMPETITION_ID,
        CL_2019_SEASON_ID,
        home_team="Tottenham Hotspur",
        away_team="Liverpool",
        stage="Final",
    )


def euro_2020_final() -> MatchInfo:
    """Italy vs England, London, 11 July 2021 (played in the delayed Euro 2020)."""
    return find_match(
        EURO_COMPETITION_ID,
        EURO_2020_SEASON_ID,
        home_team="Italy",
        away_team="England",
        stage="Final",
    )


def womens_world_cup_2023_final() -> MatchInfo:
    """Spain Women's vs England Women's, Sydney, 20 August 2023."""
    return find_match(
        WWC_COMPETITION_ID,
        WWC_2023_SEASON_ID,
        home_team="Spain Women's",
        away_team="England Women's",
        stage="Final",
    )


def showcase_matches() -> list[MatchInfo]:
    """Curated matches the mini-app exposes.

    Deliberately spans more than one competition format (World Cup, Champions
    League, continental championship, Women's World Cup) so the app proves it
    generalizes past "the two World Cup finals" rather than being hardcoded
    for a single dataset shape.
    """
    return [
        world_cup_2018_final(),
        world_cup_2022_final(),
        champions_league_2019_final(),
        euro_2020_final(),
        womens_world_cup_2023_final(),
    ]


def get_showcase_match(match_id: int) -> MatchInfo:
    """Return one curated match by StatsBomb ``match_id``."""
    for match in showcase_matches():
        if match.match_id == match_id:
            return match
    known = ", ".join(str(m.match_id) for m in showcase_matches())
    raise ValueError(f"Unknown showcase match_id={match_id}. Known: {known}")


def match_to_dict(match: MatchInfo) -> dict:
    """JSON-friendly match payload for an API response."""
    return {
        "match_id": match.match_id,
        "home_team": match.home_team,
        "away_team": match.away_team,
        "home_score": match.home_score,
        "away_score": match.away_score,
        "match_date": match.match_date,
        "competition_stage": match.competition_stage,
        "label": f"{match.home_team} vs {match.away_team}",
    }


def load_events(match_id: int) -> pd.DataFrame:
    """Load every event for a match into a DataFrame (Parquet-cached)."""
    key = f"events_{match_id}"
    cached = _read_cache(key)
    if cached is not None:
        return cached
    events = sb.events(match_id=match_id)
    _write_cache(key, events)
    return events
