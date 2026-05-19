import { AnalyticsLab } from "@/components/analytics-lab";
import Link from "next/link";
import { LeaderboardTable } from "@/components/leaderboard-table";
import { MetricCard } from "@/components/metric-card";
import { PlayerSearch } from "@/components/player-search";
import { TrendCharts } from "@/components/trend-charts";
import { getHomePayload } from "@/lib/api";

export const revalidate = 300;

function fmt(n: number | null | undefined) {
  if (n === null || n === undefined) return "N/A";
  return n.toLocaleString();
}

function pct(v: number | null | undefined) {
  if (v === null || v === undefined) return "N/A";
  return `${(v * 100).toFixed(1)}%`;
}

function displayApiBase() {
  const configured = process.env.NEXT_PUBLIC_CHESSKE_API_BASE ?? "";
  if (!configured || configured.includes("chess-in-kenya.onrender.com")) return "/api";
  return configured;
}

export default async function Home() {
  const home = await getHomePayload();
  const overview = home?.overview ?? null;
  const quality = home?.quality ?? null;
  const rapid = home?.leaderboards?.rapid ?? null;
  const blitz = home?.leaderboards?.blitz ?? null;
  const joins = home?.trends?.joins ?? null;
  const discovery = home?.trends?.discovery ?? null;

  return (
    <main id="main-content" className="atlas-page">
      <div className="atmosphere" aria-hidden />
      <section className="metrics-grid">
        <MetricCard label="Tracked Players" value={fmt(overview?.total_players)} accent="sun" />
        <MetricCard label="Total Games" value={fmt(overview?.total_games)} accent="jade" />
        <MetricCard
          label="Active Coverage"
          value={quality ? pct(quality.latest_active_coverage_ratio) : "Pending"}
          accent="coral"
        />
        <MetricCard
          label="Data Gaps"
          value={quality ? fmt(quality.missing_stats_for_active_users) : "Pending"}
          accent="ink"
        />
      </section>

      <section className="panel intro stagger">
        <div className="panel-head">
          <h2>System snapshot</h2>
          <span className="pill">Live API</span>
        </div>
        <p>
          The interface reads from the production API behind the rolling discovery ledger and refresh
          queue. The goal is simple: show where Kenya&apos;s chess activity is expanding, who carries
          the visible play, and where growth still needs depth.
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
        <Link href="/data-journey" className="route-card stagger">
          <p className="route-eyebrow">History Lens</p>
          <h3>Follow the data journey</h3>
          <p>From a 4.3k-player scrape to a production ledger with quality checks and live refresh.</p>
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
        <span>API base: {displayApiBase()}</span>
        <span>
          If data is empty, start backend with
          {" "}
          <code>python -m chesske_platform.scripts.serve_api</code>
        </span>
      </footer>
    </main>
  );
}
