"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  chartUrl,
  getMatches,
  getShotSummary,
  type ChartKind,
  type Match,
  type TeamShotRow,
} from "@/lib/api";

function defaultPlayer(match: Match): string {
  const teams = `${match.home_team} ${match.away_team}`.toLowerCase();
  if (teams.includes("argentina")) return "Messi";
  if (teams.includes("croatia")) return "Modri";
  return "Messi";
}

function formatDate(iso: string | null): string {
  if (!iso) return "";
  return new Date(`${iso}T12:00:00`).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

function yearLabel(iso: string | null): string {
  if (!iso) return "Final";
  return iso.slice(0, 4);
}

function scoreline(match: Match): string {
  if (match.home_score == null || match.away_score == null) return "—";
  return `${match.home_score}–${match.away_score}`;
}

function teamRow(teams: TeamShotRow[], name: string): TeamShotRow | undefined {
  return teams.find((t) => t.team === name);
}

function Metric({
  label,
  value,
  accent = false,
}: {
  label: string;
  value: string | number;
  accent?: boolean;
}) {
  return (
    <div className={`metric${accent ? " xg" : ""}`}>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}

const TABS: { value: ChartKind; label: string }[] = [
  { value: "xg", label: "xG map" },
  { value: "shots", label: "Shots" },
  { value: "passes", label: "Passes" },
];

export default function PitchBoard() {
  const [matches, setMatches] = useState<Match[]>([]);
  const [matchId, setMatchId] = useState<number | null>(null);
  const [teams, setTeams] = useState<TeamShotRow[]>([]);
  const [kind, setKind] = useState<ChartKind>("xg");
  const [loadingList, setLoadingList] = useState(true);
  const [loadingSummary, setLoadingSummary] = useState(false);
  const [imgLoading, setImgLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selected = useMemo(
    () => matches.find((m) => m.match_id === matchId) ?? null,
    [matches, matchId],
  );

  const player = selected ? defaultPlayer(selected) : "Messi";
  const homeStats = selected ? teamRow(teams, selected.home_team) : undefined;
  const awayStats = selected ? teamRow(teams, selected.away_team) : undefined;

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoadingList(true);
      setError(null);
      try {
        const list = await getMatches();
        if (cancelled) return;
        setMatches(list);
        setMatchId(list[0]?.match_id ?? null);
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "Could not reach the API. Is uvicorn running on :8000?",
          );
        }
      } finally {
        if (!cancelled) setLoadingList(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (matchId == null) return;
    let cancelled = false;
    (async () => {
      setLoadingSummary(true);
      setError(null);
      try {
        const data = await getShotSummary(matchId);
        if (cancelled) return;
        setTeams(data.teams);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load summary");
          setTeams([]);
        }
      } finally {
        if (!cancelled) setLoadingSummary(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [matchId]);

  const onSelectMatch = useCallback((id: number) => {
    setMatchId(id);
    setKind("xg");
  }, []);

  const resolvedSrc =
    matchId == null
      ? null
      : kind === "passes"
        ? `${chartUrl(matchId, kind, player)}&_=${matchId}-${kind}`
        : `${chartUrl(matchId, kind)}?_=${matchId}-${kind}`;

  useEffect(() => {
    if (resolvedSrc) setImgLoading(true);
  }, [resolvedSrc]);

  const chartHint =
    kind === "passes"
      ? `Completed passes · ${player}`
      : kind === "xg"
        ? "Size = xG · gold edge = goal · shootout excluded"
        : "Stars = goals · away team attacks left";

  const dash = loadingSummary ? "—" : undefined;

  return (
    <div className="shell">
      <header className="topbar fade-up">
        <div className="brand">Football Data Explorations</div>
        <p className="brand-note">World Cup finals · StatsBomb open data</p>
      </header>

      {error ? (
        <div className="alert" role="alert">
          {error}
        </div>
      ) : null}

      <section className="board fade-up" aria-label="Match scoreboard">
        <div className="board-inner">
          <div className="switcher" role="group" aria-label="Choose final">
            {loadingList
              ? null
              : matches.map((m) => (
                  <button
                    key={m.match_id}
                    type="button"
                    className="chip"
                    aria-pressed={m.match_id === matchId}
                    onClick={() => onSelectMatch(m.match_id)}
                  >
                    {yearLabel(m.match_date)} · {m.home_team} v {m.away_team}
                  </button>
                ))}
          </div>

          {selected ? (
            <div className="hero" aria-live="polite">
              <div className="side">
                <div className="team-name">{selected.home_team}</div>
                <div className="metrics">
                  <Metric label="Shots" value={dash ?? homeStats?.shots ?? "—"} />
                  <Metric label="Goals" value={dash ?? homeStats?.goals ?? "—"} />
                  <Metric
                    label="xG"
                    accent
                    value={
                      dash ??
                      (homeStats ? Number(homeStats.xg).toFixed(2) : "—")
                    }
                  />
                </div>
              </div>

              <div className="score-block">
                <div className="score">{scoreline(selected)}</div>
                <div className="score-meta">
                  {formatDate(selected.match_date)} · {selected.competition_stage}
                </div>
              </div>

              <div className="side away">
                <div className="team-name">{selected.away_team}</div>
                <div className="metrics">
                  <Metric label="Shots" value={dash ?? awayStats?.shots ?? "—"} />
                  <Metric label="Goals" value={dash ?? awayStats?.goals ?? "—"} />
                  <Metric
                    label="xG"
                    accent
                    value={
                      dash ??
                      (awayStats ? Number(awayStats.xg).toFixed(2) : "—")
                    }
                  />
                </div>
              </div>
            </div>
          ) : (
            <div className="score-meta">Loading showcase finals…</div>
          )}
        </div>
      </section>

      <main className="stage fade-up">
        <div className="stage-bar">
          <div className="stage-copy">
            <h2>Pitch map</h2>
            <p>{chartHint}</p>
          </div>
          <div className="tabs" role="tablist" aria-label="Chart type">
            {TABS.map((tab) => (
              <button
                key={tab.value}
                type="button"
                role="tab"
                className="tab"
                aria-selected={kind === tab.value}
                onClick={() => setKind(tab.value)}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        <div className="pitch-frame">
          {resolvedSrc ? (
            <>
              {imgLoading ? (
                <div className="pitch-loading" aria-live="polite">
                  Rendering map…
                </div>
              ) : null}
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                key={resolvedSrc}
                src={resolvedSrc}
                alt={
                  selected
                    ? `${selected.label} ${kind} pitch map`
                    : "Pitch map"
                }
                onLoad={() => setImgLoading(false)}
                onError={() => {
                  setImgLoading(false);
                  setError(
                    kind === "passes"
                      ? `Pass map failed — “${player}” may not appear in this match.`
                      : "Could not render the pitch map from the API.",
                  );
                }}
              />
            </>
          ) : (
            <div className="pitch-empty">Select a final to render a map.</div>
          )}
        </div>
      </main>

      <footer className="footer">
        Event data © StatsBomb Open Data · served via{" "}
        <code>football_data.get_xg_shot_map</code>
      </footer>
    </div>
  );
}
