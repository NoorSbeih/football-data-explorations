# Football Data Explorations

StatsBomb open-data analysis packaged as an **importable Python module**, with notebooks as demos and a small **FastAPI + Next.js** app on top.

Reusable entry points in `src/football_data/`:

- `get_shot_map(match)` — two-team shot map (goals as stars)
- `get_pass_map(match, player)` — completed-pass map
- `get_xg_shot_map(match)` — shot map sized by StatsBomb xG (shootout excluded)

Showcase matches: **2018** (France vs Croatia) and **2022** (Argentina vs France) World Cup finals.

## Layout

```
football-data-explorations/
├── notebooks/              # thin demos that call the package
├── src/football_data/      # importable loaders / analysis / viz
├── app/
│   ├── api/                # FastAPI — JSON + PNG maps
│   └── web/                # Next.js pitchboard UI
├── outputs/
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Setup

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

`requirements.txt` editable-installs this repo (`pip install -e .`) and pulls FastAPI + Jupyter.

## Run the mini-app

```powershell
# API (repo root, venv on)
uvicorn app.api.main:app --reload --port 8000

# UI (second terminal)
cd app\web
npm install
npm run dev
```

Open http://localhost:3000 — pick a final, inspect xG / shots / passes.

See [app/README.md](app/README.md) for API routes.

## Notebooks

```powershell
jupyter notebook notebooks\01_explore_wc_final.ipynb
jupyter notebook notebooks\02_xg_two_finals.ipynb
```

## From Python

```python
from pathlib import Path
from football_data import world_cup_2022_final, get_xg_shot_map

match = world_cup_2022_final()
get_xg_shot_map(match, save_path=Path("outputs") / f"wc2022_final_{match.match_id}_xg_shots.png")
```

## Data credit

Event data from [StatsBomb Open Data](https://github.com/statsbomb/open-data). Follow their license and attribution if you publish charts.
