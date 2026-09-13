# Mini-app

Thin product surface over `football_data`:

- `api/` — FastAPI (JSON summaries + PNG pitch maps)
- `web/` — Next.js pitchboard UI

## Run locally

From the repo root (with the project venv active):

```powershell
# terminal 1 — API
uvicorn app.api.main:app --reload --port 8000

# terminal 2 — UI
cd app\web
npm install
npm run dev
```

Open http://localhost:3000

Optional: point the UI at another API host:

```powershell
$env:NEXT_PUBLIC_API_URL="http://127.0.0.1:8000"
npm run dev
```

## Endpoints

| Method | Path | Notes |
|---|---|---|
| GET | `/api/health` | Liveness |
| GET | `/api/matches` | Showcase finals |
| GET | `/api/matches/{id}/shot-summary` | Shots / goals / xG (no shootout) |
| GET | `/api/matches/{id}/xg-map.png` | xG-sized shot map |
| GET | `/api/matches/{id}/shot-map.png` | Classic shot map |
| GET | `/api/matches/{id}/pass-map.png?player=Messi` | Completed passes |

The API only exposes curated showcase matches for now (2018 + 2022 World Cup finals).
