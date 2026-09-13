"""Fetch StatsBomb open-data matches and events."""

from __future__ import annotations

import warnings
from dataclasses import dataclass

import pandas as pd
from statsbombpy import sb
from statsbombpy.api_client import NoAuthWarning

warnings.filterwarnings("ignore", category=NoAuthWarning)

WC_COMPETITION_ID = 43
WC_2018_SEASON_ID = 3
WC_2022_COMPETITION_ID = WC_COMPETITION_ID
WC_2022_SEASON_ID = 106


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
    """Return the StatsBomb match list for a competition season."""
    return sb.matches(competition_id=competition_id, season_id=season_id)


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


def showcase_matches() -> list[MatchInfo]:
    """Curated matches the mini-app exposes (World Cup finals for now)."""
    return [world_cup_2018_final(), world_cup_2022_final()]


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
    """Load every event for a match into a DataFrame."""
    return sb.events(match_id=match_id)
