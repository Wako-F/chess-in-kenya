import Link from "next/link";
import { notFound } from "next/navigation";

import { PlayerInsights } from "@/components/player-insights";
import { getLivePlayer, getPlayer, getPlayerBenchmark } from "@/lib/api";

function stat(v: number | null | undefined) {
  return (v ?? 0).toLocaleString();
}

function dt(v: string | null | undefined) {
  return v ? new Date(v).toLocaleString() : "N/A";
}

export default async function PlayerPage({
  params,
}: {
  params: Promise<{ username: string }>;
}) {
  const { username } = await params;
  const player = (await getLivePlayer(username)) ?? (await getPlayer(username));
  if (!player) notFound();
  const benchmark = await getPlayerBenchmark(player.username);

  return (
    <main id="main-content" className="atlas-page">
      <div className="atmosphere" aria-hidden />
      <section className="hero compact">
        <div className="profile-hero">
          <div className="avatar-frame profile-avatar">
            {player.avatar ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={player.avatar} alt="" />
            ) : (
              <span>{player.username.slice(0, 2).toUpperCase()}</span>
            )}
          </div>
          <div className="hero-copy">
            <p className="eyebrow">Live player route</p>
            <h1>{player.username}</h1>
            <p className="lead">
              Fresh Chess.com profile refresh with local Kenya rank context and format-level
              performance shape.
            </p>
            <div className="run-meta">
              <span className="pill">{player.lookup_refreshed ? "LIVE REFRESHED" : player.status.toUpperCase()}</span>
              <span className="pill">{player.lookup_country ?? "KE"}</span>
              <span className="mono">
                Joined {player.joined_at ? new Date(player.joined_at).toLocaleDateString() : "unknown"}
              </span>
              <span className="mono">Last online {dt(player.last_online)}</span>
            </div>
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
          <h3>Current Format Snapshot</h3>
          <span className="pill">LIVE DETAIL</span>
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
            <p className="k">Ledger Updated</p>
            <p className="v">{dt(player.ledger_updated_at ?? player.last_online)}</p>
          </div>
        </div>
      </section>

      <PlayerInsights player={player} benchmark={benchmark} />

      <section className="panel stagger">
        <div className="panel-head">
          <h3>Raw Population Standing</h3>
          <span className="pill">BENCHMARK TABLE</span>
        </div>
        {benchmark ? (
          <div className="player-grid">
            {Object.entries(benchmark.metrics).map(([k, m]) => (
              <div key={k}>
                <p className="k">{k.replaceAll("_", " ")}</p>
                <p className="v">
                  {m.value.toLocaleString()}{" "}
                  {m.percentile !== null ? `(P${m.percentile.toFixed(1)})` : ""}
                  {m.rank && m.total_ranked ? ` #${m.rank.toLocaleString()} / ${m.total_ranked.toLocaleString()}` : ""}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <p className="chart-empty">No benchmark data available.</p>
        )}
      </section>

      <p className="mono" style={{ marginTop: "0.8rem" }}>
        <Link href="/">Back to atlas</Link>
        {player.profile_url ? (
          <>
            {" "}
            /{" "}
            <a href={player.profile_url} target="_blank" rel="noreferrer">
              Chess.com profile
            </a>
          </>
        ) : null}
      </p>
    </main>
  );
}
