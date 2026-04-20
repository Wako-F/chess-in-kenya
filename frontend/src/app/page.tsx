import { AnalyticsLab } from "@/components/analytics-lab";
import Link from "next/link";
import { LeaderboardTable } from "@/components/leaderboard-table";
import { MetricCard } from "@/components/metric-card";
import { PlayerSearch } from "@/components/player-search";
import { TrendCharts } from "@/components/trend-charts";
import {
  getDiscoveryTrend,
  getJoinTrend,
  getLeaderboard,
  getOverview,
  getQuality,
} from "@/lib/api";

export const dynamic = "force-dynamic";

function fmt(n: number | null | undefined) {
  if (n === null || n === undefined) return "N/A";
  return n.toLocaleString();
}

function pct(v: number | null | undefined) {
  if (v === null || v === undefined) return "N/A";
  return `${(v * 100).toFixed(1)}%`;
}

export default async function Home() {
  const [overview, quality, rapid, blitz, joins, discovery] = await Promise.all([
    getOverview(),
    getQuality(),
    getLeaderboard("rapid", 12),
    getLeaderboard("blitz", 12),
    getJoinTrend(),
    getDiscoveryTrend(),
  ]);

  const latestRun = overview?.latest_run ?? quality?.latest_run ?? null;

  return (
    <main className="atlas-page">
      <div className="atmosphere" aria-hidden />
      <section className="hero">
        <p className="eyebrow">Kenya Chess Intelligence Platform</p>
        <h1>ChessKE Atlas</h1>
        <p className="lead">
          A production-grade, API-driven intelligence interface for tracking growth, performance,
          and competitive shape across Kenya&apos;s online chess community.
        </p>
        <div className="run-meta">
          <span className="pill">{latestRun ? `RUN #${latestRun.id}` : "NO RUN DATA"}</span>
          <span className="mono">
            {latestRun?.ended_at
              ? `Last sync ${new Date(latestRun.ended_at).toLocaleString()}`
              : overview || quality
                ? "No pipeline run recorded yet"
                : "Backend API offline or not yet synced"}
          </span>
        </div>
      </section>

      <section className="metrics-grid">
        <MetricCard label="Tracked Players" value={fmt(overview?.total_players)} accent="sun" />
        <MetricCard label="Total Games" value={fmt(overview?.total_games)} accent="jade" />
        <MetricCard label="Active Coverage" value={pct(quality?.latest_active_coverage_ratio)} accent="coral" />
        <MetricCard label="Data Gaps" value={fmt(quality?.missing_stats_for_active_users)} accent="ink" />
      </section>

      <section className="panel intro stagger">
        <div className="panel-head">
          <h2>System Snapshot</h2>
          <span className="pill">LIVE API</span>
        </div>
        <p>
          This frontend is fully decoupled from raw CSV files. It consumes the production API backed
          by your rolling discovery ledger and refresh queue. Recruiters get a clear signal that this
          project is engineered as a data product, not a one-off dashboard.
        </p>
      </section>

      <section className="route-cards">
        <Link href="/leaderboards" className="route-card stagger">
          <p className="route-eyebrow">Competitive Lens</p>
          <h3>Explore all leaderboards</h3>
          <p>Rapid, blitz, bullet, daily, puzzle, and volume rankings with deeper route-level views.</p>
        </Link>
        <Link href="/observability" className="route-card stagger">
          <p className="route-eyebrow">Engineering Lens</p>
          <h3>Inspect pipeline health</h3>
          <p>Run history, sync reliability, and latest system status in one observability console.</p>
        </Link>
        <Link href="/methodology" className="route-card stagger">
          <p className="route-eyebrow">Trust Lens</p>
          <h3>Read data methodology</h3>
          <p>Transparent explanation of API constraints, rolling discovery logic, and data quality policy.</p>
        </Link>
      </section>

      <TrendCharts joins={joins?.items ?? []} discovery={discovery?.items ?? []} />
      <AnalyticsLab />

      <section className="boards-grid">
        <LeaderboardTable title="Rapid Commanders" board="rapid" items={rapid?.items ?? []} />
        <LeaderboardTable title="Blitz Specialists" board="blitz" items={blitz?.items ?? []} />
      </section>

      <PlayerSearch />

      <footer className="foot mono">
        <span>API base: {process.env.NEXT_PUBLIC_CHESSKE_API_BASE ?? "http://127.0.0.1:8000"}</span>
        <span>
          If data is empty, start backend with
          {" "}
          <code>python -m chesske_platform.scripts.serve_api</code>
        </span>
      </footer>
    </main>
  );
}
