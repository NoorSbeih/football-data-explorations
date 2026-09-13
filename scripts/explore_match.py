"""Explore a single StatsBomb match: shot map + one player's completed passes."""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from mplsoccer import Pitch
from statsbombpy import sb
from statsbombpy.api_client import NoAuthWarning

warnings.filterwarnings("ignore", category=NoAuthWarning)

ROOT = Path(__file__).resolve().parent.parent
OUTPUTS = ROOT / "outputs"

# FIFA World Cup 2022
COMPETITION_ID = 43
SEASON_ID = 106
HOME_TEAM = "Argentina"
AWAY_TEAM = "France"
PLAYER_NAME_FRAGMENT = "Messi"

TEAM_COLORS = {
    "Argentina": "#75AADB",
    "France": "#002654",
}


def lookup_match_id() -> tuple[int, str, str]:
    """Find the 2022 World Cup Final (Argentina vs France) via sb.matches()."""
    matches = sb.matches(competition_id=COMPETITION_ID, season_id=SEASON_ID)
    pair = matches[
        ((matches["home_team"] == HOME_TEAM) & (matches["away_team"] == AWAY_TEAM))
        | ((matches["home_team"] == AWAY_TEAM) & (matches["away_team"] == HOME_TEAM))
    ]
    if "competition_stage" in pair.columns:
        final = pair[pair["competition_stage"] == "Final"]
        if not final.empty:
            pair = final
    if pair.empty:
        raise SystemExit(
            "Could not find Argentina vs France in competition_id=43, season_id=106."
        )
    row = pair.sort_values("match_date").iloc[-1]
    return int(row["match_id"]), str(row["home_team"]), str(row["away_team"])


def xy(locations, invert: bool = False) -> tuple[list[float], list[float]]:
    xs, ys = [], []
    for loc in locations:
        if isinstance(loc, (list, tuple)) and len(loc) >= 2:
            x, y = float(loc[0]), float(loc[1])
            if invert:
                x, y = 120.0 - x, 80.0 - y
            xs.append(x)
            ys.append(y)
    return xs, ys


def find_player(events, fragment: str) -> str:
    players = events["player"].dropna().unique()
    hits = [p for p in players if fragment.lower() in str(p).lower()]
    if not hits:
        raise SystemExit(f"No player matching '{fragment}' in this match.")
    return sorted(hits, key=len)[0]


def plot_shots(shots, home_team: str, away_team: str, match_id: int) -> Path:
    pitch = Pitch(pitch_type="statsbomb", pitch_color="#1a472a", line_color="#f0f0f0")
    fig, ax = pitch.draw(figsize=(10, 7))
    fig.set_facecolor("#1a472a")

    for team, group in shots.groupby("team"):
        color = TEAM_COLORS.get(team, "#dddddd")
        invert = team == away_team
        is_goal = group["shot_outcome"] == "Goal"
        missed = group.loc[~is_goal]
        goals = group.loc[is_goal]

        mx, my = xy(missed["location"], invert=invert)
        pitch.scatter(
            mx,
            my,
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
        gx, gy = xy(goals["location"], invert=invert)
        pitch.scatter(
            gx,
            gy,
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
        f"{home_team} vs {away_team} — World Cup 2022 Final\n"
        f"Shot map (stars = goals; {away_team} attacking left)",
        color="white",
        pad=12,
        fontsize=13,
    )
    path = OUTPUTS / f"wc2022_final_{match_id}_shots.png"
    fig.savefig(path, dpi=160, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return path


def plot_passes(completed, player: str, match_id: int) -> Path:
    pitch = Pitch(pitch_type="statsbomb", pitch_color="#1a472a", line_color="#f0f0f0")
    fig, ax = pitch.draw(figsize=(10, 7))
    fig.set_facecolor("#1a472a")

    start_x, start_y = xy(completed["location"])
    end_x, end_y = xy(completed["pass_end_location"])
    pitch.arrows(
        start_x,
        start_y,
        end_x,
        end_y,
        ax=ax,
        width=1.4,
        headwidth=4,
        headlength=4,
        color="#F6C945",
        alpha=0.8,
    )
    ax.set_title(
        f"{player} — completed passes\nWorld Cup 2022 Final",
        color="white",
        pad=12,
        fontsize=13,
    )
    slug = PLAYER_NAME_FRAGMENT.lower()
    path = OUTPUTS / f"wc2022_final_{match_id}_{slug}_passes.png"
    fig.savefig(path, dpi=160, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return path


def main() -> None:
    OUTPUTS.mkdir(parents=True, exist_ok=True)

    match_id, home_team, away_team = lookup_match_id()
    print(f"Match: {home_team} vs {away_team} (match_id={match_id})")

    events = sb.events(match_id=match_id)
    shots = events[events["type"] == "Shot"].copy()
    passes = events[events["type"] == "Pass"].copy()

    shot_path = plot_shots(shots, home_team, away_team, match_id)

    player = find_player(events, PLAYER_NAME_FRAGMENT)
    player_passes = passes[passes["player"] == player]
    completed = player_passes[player_passes["pass_outcome"].isna()]
    pass_path = plot_passes(completed, player, match_id)

    print("\n--- Shots ---")
    for team in [home_team, away_team]:
        team_shots = shots[shots["team"] == team]
        goals = (team_shots["shot_outcome"] == "Goal").sum()
        print(f"{team}: {len(team_shots)} shots, {goals} goals")

    total = len(player_passes)
    n_completed = len(completed)
    pct = (100.0 * n_completed / total) if total else 0.0
    print(f"\n--- Passes ({player}) ---")
    print(f"Completed {n_completed}/{total} ({pct:.1f}%)")
    print(f"\nSaved:\n  {shot_path}\n  {pass_path}")


if __name__ == "__main__":
    main()
