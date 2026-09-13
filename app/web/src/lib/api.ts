export type Match = {
  match_id: number;
  home_team: string;
  away_team: string;
  home_score: number | null;
  away_score: number | null;
  match_date: string | null;
  competition_stage: string | null;
  label: string;
};

export type TeamShotRow = {
  match: string;
  match_id: number;
  team: string;
  shots: number;
  goals: number;
  xg: number;
};

export type ShotSummaryResponse = {
  match: Match;
  teams: TeamShotRow[];
};

export type ChartKind = "xg" | "shots" | "passes";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ||
  "http://127.0.0.1:8000";

async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || `Request failed (${res.status})`);
  }
  return res.json() as Promise<T>;
}

export function getMatches(): Promise<Match[]> {
  return apiGet<Match[]>("/api/matches");
}

export function getShotSummary(matchId: number): Promise<ShotSummaryResponse> {
  return apiGet<ShotSummaryResponse>(`/api/matches/${matchId}/shot-summary`);
}

export function chartUrl(
  matchId: number,
  kind: ChartKind,
  player = "Messi",
): string {
  if (kind === "xg") return `${API_BASE}/api/matches/${matchId}/xg-map.png`;
  if (kind === "shots") return `${API_BASE}/api/matches/${matchId}/shot-map.png`;
  return `${API_BASE}/api/matches/${matchId}/pass-map.png?player=${encodeURIComponent(player)}`;
}

export { API_BASE };
