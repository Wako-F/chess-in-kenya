export type LatestRun = {
  id: number;
  started_at: string;
  ended_at: string | null;
  status: string;
  active_count: number;
  updated_count: number;
  error_count: number;
};

export type Overview = {
  total_players: number;
  total_games: number;
  average_ratings: {
    rapid: number | null;
    blitz: number | null;
    bullet: number | null;
    daily: number | null;
    puzzle: number | null;
  };
  latest_run: LatestRun | null;
};

export type Quality = {
  total_users: number;
  active_users: number;
  deleted_users: number;
  stats_rows: number;
  missing_stats_for_active_users: number;
  latest_snapshot_date: string | null;
  latest_snapshot_count: number;
  latest_active_coverage_ratio: number;
  latest_run: LatestRun | null;
};

export type LeaderboardItem = {
  username: string;
  score: number;
  games: number;
  rapid_rating: number;
  blitz_rating: number;
  bullet_rating: number;
  daily_rating: number;
  highest_puzzle_rating: number;
  total_games: number;
};

export type LeaderboardResponse = {
  board: string;
  items: LeaderboardItem[];
};

export type TrendPoint = {
  month?: string;
  day?: string;
  players?: number;
  active_players?: number;
  new_signups?: number;
  new_logins?: number;
};

export type TrendResponse = {
  items: TrendPoint[];
};

export type RunRecord = {
  id: number;
  started_at: string;
  ended_at: string | null;
  status: string;
  active_count: number;
  updated_count: number;
  deleted_count: number;
  refresh_count: number;
  error_count: number;
};

export type RunResponse = {
  items: RunRecord[];
};

export type ErrorRecord = {
  id: number;
  run_id: number;
  username: string | null;
  stage: string;
  error: string;
  created_at: string;
};

export type ErrorResponse = {
  items: ErrorRecord[];
};

export type DistributionPoint = {
  bucket: number;
  players: number;
};

export type DistributionResponse = {
  items: DistributionPoint[];
};

export type FormatSummaryPoint = {
  format: string;
  games: number;
  avg_rating: number;
};

export type FormatSummaryResponse = {
  items: FormatSummaryPoint[];
};

export type ActivityBucketPoint = {
  bucket: string;
  players: number;
};

export type ActivityBucketResponse = {
  items: ActivityBucketPoint[];
};

export type RatingScatterPoint = {
  username: string;
  rapid_rating: number;
  blitz_rating: number;
  bullet_rating: number;
  daily_rating: number;
  total_games: number;
};

export type RatingScatterResponse = {
  items: RatingScatterPoint[];
};

export type CorrelationPoint = {
  x: string;
  y: string;
  value: number;
};

export type CorrelationResponse = {
  items: CorrelationPoint[];
};

export type PercentileBandPoint = {
  format: string;
  percentile: number;
  rating: number;
};

export type PercentileBandResponse = {
  items: PercentileBandPoint[];
};

export type CohortPoint = {
  cohort: string;
  total_players: number;
  retained_90d: number;
  retention_rate: number;
};

export type CohortResponse = {
  items: CohortPoint[];
};

export type StorySnapshot = {
  tracked_players: number;
  total_games: number;
  median_games: number;
  mean_games: number;
  p90_games: number;
  p99_games: number;
  active_7d: number;
  active_30d: number;
  active_90d: number;
  dormant_365d: number;
  active_share_90d: number;
};

export type StoryCountPoint = {
  label?: string;
  tier?: string;
  format?: string;
  segment?: string;
  formats?: string;
  players: number;
  share?: number;
};

export type StorySharePoint = {
  group: string;
  share: number;
};

export type StoryCurvePoint = {
  player_percentile: number;
  game_share: number;
};

export type RapidBlitzGap = {
  median_gap: number;
  blitz_200_plus: number;
  rapid_200_plus: number;
};

export type StoryCohortPoint = {
  cohort: string;
  players: number;
  median_games: number;
  active_90d: number;
  active_rate_90d: number;
};

export type PuzzleCorrelationPoint = {
  format: string;
  correlation: number;
};

export type StoryArchetype = {
  name: string;
  count: number;
  description: string;
};

export type OutcomeStylePoint = {
  format: string;
  median_win_rate: number;
  median_draw_rate: number;
};

export type StoryReport = {
  snapshot: StorySnapshot;
  recency_buckets: StoryCountPoint[];
  concentration: {
    top_shares: StorySharePoint[];
    curve: StoryCurvePoint[];
    volume_tiers: StoryCountPoint[];
  };
  format_identity: {
    participation: StoryCountPoint[];
    dominance: StoryCountPoint[];
    format_mix: StoryCountPoint[];
    rapid_blitz_gap: RapidBlitzGap;
  };
  cohorts: StoryCohortPoint[];
  puzzle_culture: {
    segments: StoryCountPoint[];
    correlations: PuzzleCorrelationPoint[];
  };
  archetypes: StoryArchetype[];
  outcome_style: OutcomeStylePoint[];
};

export type PlayerBenchmarkMetric = {
  value: number;
  percentile: number | null;
};

export type PlayerBenchmark = {
  username: string;
  metrics: Record<string, PlayerBenchmarkMetric>;
};

export type Player = {
  username: string;
  joined_at: string | null;
  last_online: string | null;
  status: string;
  total_games: number;
  total_rapid: number;
  total_blitz: number;
  total_bullet: number;
  total_daily: number;
  rapid_rating: number;
  blitz_rating: number;
  bullet_rating: number;
  daily_rating: number;
  highest_puzzle_rating: number | null;
};
