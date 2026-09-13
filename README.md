# Football Data Explorations

A small Python portfolio project for exploring [StatsBomb](https://github.com/statsbomb/open-data) open football event data. The first example loads the **2022 FIFA World Cup Final** (Argentina vs France), plots every shot on a pitch, and draws a completed-pass map for Lionel Messi.

Later iterations will add an expected-goals (xG) chart and a second match. For now this is one working end-to-end script.

## What the script does

`scripts/explore_match.py`:

1. Looks up the World Cup 2022 Final `match_id` with `sb.matches(competition_id=43, season_id=106)`.
2. Downloads that match’s events into a pandas DataFrame via `statsbombpy`.
3. Filters **shots** and plots them on an `mplsoccer` pitch, color-coded by team. Goals are drawn as larger gold-edged stars.
4. Filters **Messi’s completed passes** and plots them as a second pitch map.
5. Saves both charts as PNGs in `outputs/` and prints shot/goal counts plus Messi’s pass completion percentage.

## Setup

From the project root (`football-data-explorations/`):

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

On macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

`statsbombpy` reads StatsBomb’s **free open-data** (no API credentials required). The first run downloads match JSON over the network.

## Run

```powershell
python scripts\explore_match.py
```

Charts land in `outputs/`:

- `wc2022_final_<match_id>_shots.png`
- `wc2022_final_<match_id>_messi_passes.png`

## Project layout

```
football-data-explorations/
├── venv/                 # local virtual environment (not committed)
├── data/                 # place for cloned/cached StatsBomb files
├── scripts/
│   └── explore_match.py
├── outputs/              # generated charts
├── requirements.txt
└── README.md
```

## Data credit

Event data comes from [StatsBomb Open Data](https://github.com/statsbomb/open-data). Please follow their license and attribution guidelines if you publish charts.
