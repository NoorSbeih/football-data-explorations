"""API-level tests. ``football_data`` calls are monkeypatched on the
``app.api.main`` module (where they were imported), so no test here touches
the network or renders a real chart.
"""

from __future__ import annotations

import app.api.main as api_main
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from football_data.data import MatchInfo


def _raise_unknown_match() -> None:
    raise ValueError("Unknown showcase match_id")


@pytest.fixture
def client(monkeypatch) -> TestClient:
    match = MatchInfo(
        match_id=1, home_team="Home FC", away_team="Away FC", home_score=1, away_score=0
    )

    monkeypatch.setattr(api_main, "showcase_matches", lambda: [match])
    monkeypatch.setattr(
        api_main,
        "get_showcase_match",
        lambda match_id: match if match_id == 1 else _raise_unknown_match(),
    )
    monkeypatch.setattr(
        api_main,
        "match_shot_summary",
        lambda m, include_shootout=False: pd.DataFrame(
            [
                {
                    "match": "Home FC vs Away FC",
                    "match_id": 1,
                    "team": "Home FC",
                    "shots": 4,
                    "goals": 1,
                    "xg": 0.55,
                }
            ]
        ),
    )
    return TestClient(api_main.app)


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_matches_endpoint(client: TestClient) -> None:
    response = client.get("/api/matches")
    assert response.status_code == 200
    body = response.json()
    assert body[0]["match_id"] == 1
    assert body[0]["label"] == "Home FC vs Away FC"


def test_shot_summary_endpoint(client: TestClient) -> None:
    response = client.get("/api/matches/1/shot-summary")
    assert response.status_code == 200
    body = response.json()
    assert body["teams"][0]["team"] == "Home FC"
    assert body["match"]["match_id"] == 1


def test_unknown_match_returns_404(client: TestClient) -> None:
    response = client.get("/api/matches/999/shot-summary")
    assert response.status_code == 404
