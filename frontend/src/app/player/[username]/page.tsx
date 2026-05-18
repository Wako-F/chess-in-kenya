import Link from "next/link";
import { notFound } from "next/navigation";

import { getPlayer, getPlayerBenchmark } from "@/lib/api";

function stat(v: number | null | undefined) {
  return (v ?? 0).toLocaleString();
}

export default async function PlayerPage({
  params,
}: {
  params: Promise<{ username: string }>;
}) {
  const { username } = await params;
  const [player, benchmark] = await Promise.all([getPlayer(username), getPlayerBenchmark(username)]);
  if (!player) notFound();

  return (
    <main id="main-content" className="atlas-page">
      <div className="atmosphere" aria-hidden />
      <section className="hero compact">
        <div className="hero-copy">
          <p className="eyebrow">Player route</p>
          <h1>{player.username}</h1>
          <p className="lead">
            Individual performance snapshot from the latest production ledger sync.
          </p>
          <div className="run-meta">
            <span className="pill">{player.status.toUpperCase()}</span>
            <span className="mono">
              Joined {player.joined_at ? new Date(player.joined_at).toLocaleDateString() : "unknown"}
            </span>
          </div>
        </div>
      </section>

      <section className="metrics-grid">
        <article className="metric-card accent-jade">
          <p className="metric-label">Total Games</p>
          <p className="metric-value">{stat(player.total_games)}</p>
        </article>
        <article className="metric-card accent-sun">
          <p className="metric-label">Rapid</p>
          <p className="metric-value">{stat(player.rapid_rating)}</p>
        </article>
        <article className="metric-card accent-coral">
          <p className="metric-label">Blitz</p>
          <p className="metric-value">{stat(player.blitz_rating)}</p>
        </article>
        <article className="metric-card accent-ink">
          <p className="metric-label">Bullet</p>
          <p className="metric-value">{stat(player.bullet_rating)}</p>
        </article>
      </section>

      <section className="panel stagger">
        <div className="panel-head">
          <h3>Format Breakdown</h3>
          <span className="pill">DETAIL</span>
        </div>
        <div className="player-grid">
          <div>
            <p className="k">Daily Rating</p>
            <p className="v">{stat(player.daily_rating)}</p>
          </div>
          <div>
            <p className="k">Puzzle Rating</p>
            <p className="v">{stat(player.highest_puzzle_rating)}</p>
          </div>
          <div>
            <p className="k">Rapid Games</p>
            <p className="v">{stat(player.total_rapid)}</p>
          </div>
          <div>
            <p className="k">Blitz Games</p>
            <p className="v">{stat(player.total_blitz)}</p>
          </div>
          <div>
            <p className="k">Bullet Games</p>
            <p className="v">{stat(player.total_bullet)}</p>
          </div>
          <div>
            <p className="k">Daily Games</p>
            <p className="v">{stat(player.total_daily)}</p>
          </div>
          <div>
            <p className="k">Last Online</p>
            <p className="v">{player.last_online ? new Date(player.last_online).toLocaleString() : "N/A"}</p>
          </div>
        </div>
      </section>

      <section className="panel stagger">
        <div className="panel-head">
          <h3>Population Percentiles</h3>
          <span className="pill">BENCHMARK</span>
        </div>
        {benchmark ? (
          <div className="player-grid">
            {Object.entries(benchmark.metrics).map(([k, m]) => (
              <div key={k}>
                <p className="k">{k.replaceAll("_", " ")}</p>
                <p className="v">
                  {m.value.toLocaleString()}{" "}
                  {m.percentile !== null ? `(P${m.percentile.toFixed(1)})` : ""}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <p className="chart-empty">No benchmark data available.</p>
        )}
      </section>

      <p className="mono" style={{ marginTop: "0.8rem" }}>
        <Link href="/">← Back to atlas</Link>
      </p>
    </main>
  );
}
