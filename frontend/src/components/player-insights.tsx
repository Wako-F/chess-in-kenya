"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { Player, PlayerBenchmark } from "@/lib/types";

const colors = {
  rapid: "#174f3f",
  blitz: "#b64a32",
  bullet: "#c18b2f",
  daily: "#28342f",
  puzzle: "#6f9da4",
  losses: "#b9b09f",
  draws: "#857a67",
};

function fmt(n: number | null | undefined) {
  return (n ?? 0).toLocaleString();
}

function pct(v: number | null | undefined) {
  if (v === null || v === undefined) return "PENDING";
  return `P${v.toFixed(1)}`;
}

function since(value: string | null | undefined) {
  if (!value) return "Unknown";
  const days = Math.max(0, Math.round((Date.now() - new Date(value).getTime()) / 86400000));
  if (days === 0) return "Today";
  if (days === 1) return "Yesterday";
  if (days < 31) return `${days} days ago`;
  if (days < 365) return `${Math.round(days / 30)} months ago`;
  return `${Math.round(days / 365)} years ago`;
}

function formatData(player: Player) {
  return [
    {
      key: "Rapid",
      rating: player.rapid_rating,
      games: player.total_rapid,
      wins: player.rapid_wins ?? 0,
      losses: player.rapid_losses ?? 0,
      draws: player.rapid_draws ?? 0,
      color: colors.rapid,
    },
    {
      key: "Blitz",
      rating: player.blitz_rating,
      games: player.total_blitz,
      wins: player.blitz_wins ?? 0,
      losses: player.blitz_losses ?? 0,
      draws: player.blitz_draws ?? 0,
      color: colors.blitz,
    },
    {
      key: "Bullet",
      rating: player.bullet_rating,
      games: player.total_bullet,
      wins: player.bullet_wins ?? 0,
      losses: player.bullet_losses ?? 0,
      draws: player.bullet_draws ?? 0,
      color: colors.bullet,
    },
    {
      key: "Daily",
      rating: player.daily_rating,
      games: player.total_daily,
      wins: player.daily_wins ?? 0,
      losses: player.daily_losses ?? 0,
      draws: player.daily_draws ?? 0,
      color: colors.daily,
    },
  ];
}

function formatMix(player: Player) {
  const total = Math.max(1, player.total_rapid + player.total_blitz + player.total_bullet + player.total_daily);
  return formatData(player).map((row) => ({
    ...row,
    share: Math.round((row.games / total) * 1000) / 10,
  }));
}

function benchmarkRows(benchmark: PlayerBenchmark | null) {
  const labels: Record<string, string> = {
    rapid_rating: "Rapid rating",
    blitz_rating: "Blitz rating",
    bullet_rating: "Bullet rating",
    daily_rating: "Daily rating",
    highest_puzzle_rating: "Puzzle peak",
    total_games: "Total games",
  };

  return Object.entries(benchmark?.metrics ?? {})
    .filter(([key]) => labels[key])
    .map(([key, metric]) => ({
      key,
      label: labels[key],
      value: metric.value,
      percentile: metric.percentile ?? 0,
    }));
}

function playerArchetype(player: Player) {
  const mix = formatMix(player).sort((a, b) => b.games - a.games);
  const best = formatData(player).sort((a, b) => b.rating - a.rating)[0];
  const primary = mix[0];
  if (primary.share >= 55) return `${primary.key} specialist`;
  if (best.rating >= 1800) return `${best.key} strength profile`;
  if (player.highest_puzzle_rating && player.highest_puzzle_rating > best.rating + 250) return "Puzzle-forward tactician";
  return "Multi-format player";
}

export function PlayerInsights({
  player,
  benchmark,
}: {
  player: Player;
  benchmark: PlayerBenchmark | null;
}) {
  const formats = formatData(player);
  const mix = formatMix(player);
  const rows = benchmarkRows(benchmark);
  const radar = [
    { metric: "Rapid", value: player.rapid_rating },
    { metric: "Blitz", value: player.blitz_rating },
    { metric: "Bullet", value: player.bullet_rating },
    { metric: "Daily", value: player.daily_rating },
    { metric: "Puzzle", value: player.highest_puzzle_rating ?? 0 },
  ];

  return (
    <section className="player-insights">
      <article className="panel stagger">
        <div className="panel-head">
          <h3>Competitive Shape</h3>
          <span className="pill">RATING MAP</span>
        </div>
        <div className="insight-copy">
          <strong>{playerArchetype(player)}</strong>
          <span>
            Last online {since(player.last_online)}. Live refreshed from Chess.com, then benchmarked against the
            Kenya ledger.
          </span>
        </div>
        <div className="profile-chart">
          <ResponsiveContainer width="100%" height={320}>
            <RadarChart data={radar}>
              <PolarGrid stroke="#d8d4c8" />
              <PolarAngleAxis dataKey="metric" />
              <Radar dataKey="value" stroke={colors.rapid} fill={colors.rapid} fillOpacity={0.28} />
              <Tooltip />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </article>

      <article className="panel stagger">
        <div className="panel-head">
          <h3>Format Workload</h3>
          <span className="pill">GAMES + OUTCOMES</span>
        </div>
        <div className="profile-chart">
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={formats}>
              <CartesianGrid strokeDasharray="3 6" stroke="#d8d4c8" />
              <XAxis dataKey="key" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="wins" stackId="outcomes" fill={colors.rapid} />
              <Bar dataKey="losses" stackId="outcomes" fill={colors.losses} />
              <Bar dataKey="draws" stackId="outcomes" fill={colors.draws} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </article>

      <article className="panel stagger">
        <div className="panel-head">
          <h3>Population Standing</h3>
          <span className="pill">LOCAL PERCENTILE</span>
        </div>
        <div className="percentile-stack">
          {rows.map((row) => (
            <div key={row.key} className="percentile-row">
              <div>
                <strong>{row.label}</strong>
                <span>{fmt(row.value)}</span>
              </div>
              <div className="percentile-track" aria-hidden>
                <span style={{ width: `${Math.max(2, Math.min(100, row.percentile))}%` }} />
              </div>
              <em>{pct(row.percentile)}</em>
            </div>
          ))}
        </div>
      </article>

      <article className="panel stagger">
        <div className="panel-head">
          <h3>Format Mix</h3>
          <span className="pill">PLAY IDENTITY</span>
        </div>
        <div className="mix-list">
          {mix.map((row) => (
            <div key={row.key} className="mix-row">
              <div>
                <strong>{row.key}</strong>
                <span>{fmt(row.games)} games</span>
              </div>
              <div className="mix-track" aria-hidden>
                <span style={{ width: `${row.share}%`, background: row.color }} />
              </div>
              <em>{row.share.toFixed(1)}%</em>
            </div>
          ))}
        </div>
      </article>
    </section>
  );
}
