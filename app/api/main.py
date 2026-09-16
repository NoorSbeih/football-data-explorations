"""FastAPI surface over ``football_data`` — JSON tables + PNG pitch maps."""

from __future__ import annotations

import io
from contextlib import contextmanager

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from matplotlib.figure import Figure

from football_data import (
    get_pass_map,
    get_shot_map,
    get_showcase_match,
    get_xg_shot_map,
    load_events,
    match_shot_summary,
    match_to_dict,
    pass_completion,
    showcase_matches,
)

app = FastAPI(
    title="Football Data Explorations API",
    description="Thin HTTP layer over importable StatsBomb analysis helpers.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    # Any Vercel deployment (production + preview URLs) is allowed too — this
    # API is public/read-only with no auth, so a permissive origin policy for
    # the UI's own hosting provider is fine.
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _resolve(match_id: int):
    try:
        return get_showcase_match(match_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@contextmanager
def _png_bytes(fig: Figure):
    buf = io.BytesIO()
    try:
        fig.savefig(buf, format="png", dpi=160, bbox_inches="tight", facecolor=fig.get_facecolor())
        buf.seek(0)
        yield buf.read()
    finally:
        plt.close(fig)
        buf.close()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/matches")
def list_matches() -> list[dict]:
    return [match_to_dict(m) for m in showcase_matches()]


@app.get("/api/matches/{match_id}")
def get_match(match_id: int) -> dict:
    return match_to_dict(_resolve(match_id))


@app.get("/api/matches/{match_id}/shot-summary")
def shot_summary_endpoint(match_id: int) -> dict:
    match = _resolve(match_id)
    table = match_shot_summary(match, include_shootout=False)
    rows = table.round({"xg": 3}).to_dict(orient="records")
    return {"match": match_to_dict(match), "teams": rows}


@app.get("/api/matches/{match_id}/pass-completion")
def pass_completion_endpoint(
    match_id: int,
    player: str = Query("Messi", min_length=2, max_length=80),
) -> dict:
    match = _resolve(match_id)
    try:
        stats = pass_completion(load_events(match.match_id), player)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"match": match_to_dict(match), "pass_completion": stats}


@app.get("/api/matches/{match_id}/xg-map.png")
def xg_map_png(match_id: int) -> Response:
    match = _resolve(match_id)
    fig = get_xg_shot_map(
        match,
        title=(
            f"{match.home_team} vs {match.away_team}\n"
            f"xG shot map (size = xG; gold edge = goal; {match.away_team} attacking left)"
        ),
    )
    with _png_bytes(fig) as payload:
        return Response(content=payload, media_type="image/png")


@app.get("/api/matches/{match_id}/shot-map.png")
def shot_map_png(match_id: int) -> Response:
    match = _resolve(match_id)
    fig = get_shot_map(
        match,
        title=(
            f"{match.home_team} vs {match.away_team}\n"
            f"Shot map (stars = goals; {match.away_team} attacking left)"
        ),
    )
    with _png_bytes(fig) as payload:
        return Response(content=payload, media_type="image/png")


@app.get("/api/matches/{match_id}/pass-map.png")
def pass_map_png(
    match_id: int,
    player: str = Query("Messi", min_length=2, max_length=80),
) -> Response:
    match = _resolve(match_id)
    try:
        fig = get_pass_map(
            match,
            player,
            title=f"{player} — completed passes\n{match.home_team} vs {match.away_team}",
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    with _png_bytes(fig) as payload:
        return Response(content=payload, media_type="image/png")
