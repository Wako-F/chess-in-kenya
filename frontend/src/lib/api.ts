import type {
  ActivityBucketResponse,
  CohortResponse,
  CorrelationResponse,
  DistributionResponse,
  ErrorResponse,
  FormatSummaryResponse,
  LeaderboardResponse,
  Overview,
  Player,
  PlayerBenchmark,
  PercentileBandResponse,
  Quality,
  RatingScatterResponse,
  RunResponse,
  StoryReport,
  TrendResponse,
} from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_CHESSKE_API_BASE ?? "http://127.0.0.1:8000";

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`API ${path} failed with ${res.status}`);
  }
  return (await res.json()) as T;
}

export async function getOverview(): Promise<Overview | null> {
  try {
    return await fetchJson<Overview>("/overview");
  } catch {
    return null;
  }
}

export async function getQuality(): Promise<Quality | null> {
  try {
    return await fetchJson<Quality>("/meta/quality");
  } catch {
    return null;
  }
}

export async function getLeaderboard(board: string, limit = 12): Promise<LeaderboardResponse | null> {
  try {
    return await fetchJson<LeaderboardResponse>(
      `/leaderboards/${board}?limit=${limit}&min_games=20`,
    );
  } catch {
    return null;
  }
}

export async function getJoinTrend(): Promise<TrendResponse | null> {
  try {
    return await fetchJson<TrendResponse>("/trends/joins?months=36");
  } catch {
    return null;
  }
}

export async function getDiscoveryTrend(): Promise<TrendResponse | null> {
  try {
    return await fetchJson<TrendResponse>("/trends/discovery?days=60");
  } catch {
    return null;
  }
}

export async function getRuns(limit = 20): Promise<RunResponse | null> {
  try {
    return await fetchJson<RunResponse>(`/meta/runs?limit=${limit}`);
  } catch {
    return null;
  }
}

export async function getErrors(limit = 30): Promise<ErrorResponse | null> {
  try {
    return await fetchJson<ErrorResponse>(`/meta/errors?limit=${limit}`);
  } catch {
    return null;
  }
}

export async function getDistribution(bucketSize = 100): Promise<DistributionResponse | null> {
  try {
    return await fetchJson<DistributionResponse>(`/stats/distribution?bucket_size=${bucketSize}`);
  } catch {
    return null;
  }
}

export async function getFormatSummary(): Promise<FormatSummaryResponse | null> {
  try {
    return await fetchJson<FormatSummaryResponse>("/stats/format-summary");
  } catch {
    return null;
  }
}

export async function getActivityBuckets(): Promise<ActivityBucketResponse | null> {
  try {
    return await fetchJson<ActivityBucketResponse>("/stats/activity-buckets");
  } catch {
    return null;
  }
}

export async function getRatingScatter(limit = 1200): Promise<RatingScatterResponse | null> {
  try {
    return await fetchJson<RatingScatterResponse>(`/stats/rating-scatter?limit=${limit}`);
  } catch {
    return null;
  }
}

export async function getCorrelationMatrix(): Promise<CorrelationResponse | null> {
  try {
    return await fetchJson<CorrelationResponse>("/stats/correlation-matrix");
  } catch {
    return null;
  }
}

export async function getPercentileBands(): Promise<PercentileBandResponse | null> {
  try {
    return await fetchJson<PercentileBandResponse>("/stats/percentile-bands");
  } catch {
    return null;
  }
}

export async function getCohortRetention(months = 24): Promise<CohortResponse | null> {
  try {
    return await fetchJson<CohortResponse>(`/stats/cohort-retention?months=${months}`);
  } catch {
    return null;
  }
}

export async function getStoryReport(): Promise<StoryReport | null> {
  try {
    return await fetchJson<StoryReport>("/stats/story-report");
  } catch {
    return null;
  }
}

export async function findPlayer(username: string): Promise<Player | null> {
  if (!username) return null;
  try {
    const res = await fetch(`${API_BASE}/players/${encodeURIComponent(username.toLowerCase())}`, {
      cache: "no-store",
    });
    if (!res.ok) return null;
    return (await res.json()) as Player;
  } catch {
    return null;
  }
}

export async function getPlayer(username: string): Promise<Player | null> {
  if (!username) return null;
  try {
    return await fetchJson<Player>(`/players/${encodeURIComponent(username.toLowerCase())}`);
  } catch {
    return null;
  }
}

export async function getPlayerBenchmark(username: string): Promise<PlayerBenchmark | null> {
  if (!username) return null;
  try {
    return await fetchJson<PlayerBenchmark>(`/players/${encodeURIComponent(username.toLowerCase())}/benchmark`);
  } catch {
    return null;
  }
}
