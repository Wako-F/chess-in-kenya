"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { StoryReport } from "@/lib/types";

const palette = ["#174f3f", "#b64a32", "#c18b2f", "#28342f", "#6f9da4", "#688858"];

function fmtInt(value: number | undefined) {
  return (value ?? 0).toLocaleString();
}

function fmtPct(value: number | undefined, digits = 1) {
  return `${(((value ?? 0) * 100)).toFixed(digits)}%`;
}

function tooltipPct(value: string | number | readonly (string | number)[] | undefined, digits = 1) {
  const first = Array.isArray(value) ? value[0] : value;
  const numeric = typeof first === "number" ? first : Number(first ?? 0);
  return fmtPct(Number.isFinite(numeric) ? numeric : 0, digits);
}

export function StoryMarvel({ report }: { report: StoryReport | null }) {
  if (!report) {
    return (
      <section className="panel stagger">
        <div className="panel-head">
          <h3>Story Engine</h3>
          <span className="pill">UNAVAILABLE</span>
        </div>
        <p>The narrative analytics layer could not be loaded from the API.</p>
      </section>
    );
  }

  const top1 = report.concentration.top_shares.find((item) => item.group === "Top 1%")?.share ?? 0;
  const top10 = report.concentration.top_shares.find((item) => item.group === "Top 10%")?.share ?? 0;
  const rapidDominant =
    report.format_identity.dominance.find((item) => item.format === "Rapid")?.players ?? 0;
  const puzzleLight =
    report.puzzle_culture.segments.find((item) => item.segment === "Puzzle rated, <10 games")?.players ?? 0;

  return (
    <>
      <section className="story-hero-grid">
        <article className="story-callout stagger">
          <p className="route-eyebrow">Story 1</p>
          <h3>The ecosystem is wide, but the active core is narrow.</h3>
          <p>
            {fmtInt(report.snapshot.tracked_players)} tracked players sit behind the registry, but only{" "}
            {fmtInt(report.snapshot.active_90d)} appear in the recent 90-day window. That gap should be
            read as a coverage-sensitive activity proxy, not a literal census of all currently active Kenyan players.
          </p>
        </article>
        <article className="story-callout stagger">
          <p className="route-eyebrow">Story 2</p>
          <h3>A small committed minority carries most visible play.</h3>
          <p>
            The top 1% of players account for {fmtPct(top1)} of all recorded games, and the top 10%
            account for {fmtPct(top10)}. Average activity alone hides how top-heavy the ecosystem really is.
          </p>
        </article>
        <article className="story-callout stagger">
          <p className="route-eyebrow">Story 3</p>
          <h3>Rapid is the center of gravity, puzzles are the broad on-ramp.</h3>
          <p>
            {fmtInt(rapidDominant)} committed specialists are rapid-dominant, while {fmtInt(puzzleLight)}
            players have puzzle ratings but fewer than 10 recorded games. Competitive play and tactical engagement are not the same population.
          </p>
        </article>
      </section>

      <section className="panel stagger note-panel">
        <div className="panel-head">
          <h3>How To Read The Recency Metrics</h3>
          <span className="pill">IMPORTANT</span>
        </div>
        <p>
          Recent-activity views are activity proxies, not retention proofs. They use Chess.com profile
          last-online timestamps from the refreshed active Kenya roster, so they are useful for comparing
          shape and direction but should not be read as a complete behavioral census.
        </p>
      </section>

      <section className="story-grid">
        <article className="panel stagger">
          <div className="panel-head">
            <h3>Ecosystem State</h3>
            <span className="pill">ALL-TIME VS RECENT</span>
          </div>
          <p>
            The registry is large, but the typical player is light-touch. The median tracked player has only{" "}
            {fmtInt(report.snapshot.median_games)} games, versus a mean of {report.snapshot.mean_games.toFixed(1)}.
          </p>
          <div className="snapshot-grid">
            <div className="snapshot-stat">
              <span>Tracked players</span>
              <strong>{fmtInt(report.snapshot.tracked_players)}</strong>
            </div>
            <div className="snapshot-stat">
              <span>Total games</span>
              <strong>{fmtInt(report.snapshot.total_games)}</strong>
            </div>
            <div className="snapshot-stat">
              <span>Active 90d share</span>
              <strong>{fmtPct(report.snapshot.active_share_90d)}</strong>
            </div>
            <div className="snapshot-stat">
              <span>P99 games</span>
              <strong>{fmtInt(report.snapshot.p99_games)}</strong>
            </div>
          </div>
          <div className="chart-wrap">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={report.recency_buckets}>
                <CartesianGrid strokeDasharray="3 6" stroke="#d8d4c8" />
                <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="players" radius={[6, 6, 0, 0]}>
                  {report.recency_buckets.map((entry, index) => (
                    <Cell key={`${entry.label}-${index}`} fill={palette[index % palette.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </article>

        <article className="panel stagger">
          <div className="panel-head">
            <h3>Concentration Of Play</h3>
            <span className="pill">TOP-HEAVY</span>
          </div>
          <p>
            A small layer of committed grinders generates most recorded games. This is why averages overstate
            what a normal account looks like.
          </p>
          <div className="share-row">
            {report.concentration.top_shares.map((item) => (
              <div key={item.group} className="share-card">
                <span>{item.group}</span>
                <strong>{fmtPct(item.share)}</strong>
                <small>of all games</small>
              </div>
            ))}
          </div>
          <div className="chart-wrap">
            <ResponsiveContainer width="100%" height={260}>
              <ComposedChart data={report.concentration.curve}>
                <CartesianGrid strokeDasharray="3 6" stroke="#d8d4c8" />
                <XAxis dataKey="player_percentile" tickFormatter={(v) => `${v}%`} />
                <YAxis tickFormatter={(v) => `${Math.round(v * 100)}%`} />
                <Tooltip formatter={(value) => tooltipPct(value, 1)} />
                <Line type="monotone" dataKey="game_share" stroke="#b64a32" strokeWidth={3} dot={false} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </article>
      </section>

      <section className="story-grid">
        <article className="panel stagger">
          <div className="panel-head">
            <h3>Player Shape</h3>
            <span className="pill">VOLUME TIERS</span>
          </div>
          <p>
            The player base is dominated by light-touch accounts, while the visible competitive layer sits in the
            upper volume tiers.
          </p>
          <div className="chart-wrap">
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={report.concentration.volume_tiers}>
                <CartesianGrid strokeDasharray="3 6" stroke="#d8d4c8" />
                <XAxis dataKey="tier" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="players" fill="#174f3f" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </article>

        <article className="panel stagger">
          <div className="panel-head">
            <h3>Format Identity</h3>
            <span className="pill">RAPID-FIRST</span>
          </div>
          <p>
            Rapid is the center of gravity. The specialization count makes that clearer than raw format share alone.
          </p>
          <div className="chart-wrap">
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={report.format_identity.dominance}>
                <CartesianGrid strokeDasharray="3 6" stroke="#d8d4c8" />
                <XAxis dataKey="format" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="players" fill="#c18b2f" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="micro-grid">
            <div className="micro-card">
              <span>Median blitz minus rapid</span>
              <strong>{report.format_identity.rapid_blitz_gap.median_gap}</strong>
            </div>
            <div className="micro-card">
              <span>Rapid 200+ above blitz</span>
              <strong>{fmtInt(report.format_identity.rapid_blitz_gap.rapid_200_plus)}</strong>
            </div>
            <div className="micro-card">
              <span>Blitz 200+ above rapid</span>
              <strong>{fmtInt(report.format_identity.rapid_blitz_gap.blitz_200_plus)}</strong>
            </div>
          </div>
        </article>
      </section>

      <section className="story-grid">
        <article className="panel stagger">
          <div className="panel-head">
            <h3>Growth vs Depth</h3>
            <span className="pill">COHORT TENSION</span>
          </div>
          <p>
            Complete join-year cohorts show how growth and game depth move together. The active-rate line is
            current 90-day profile activity by join year, not literal retention from signup.
          </p>
          <div className="chart-wrap">
            <ResponsiveContainer width="100%" height={290}>
              <ComposedChart data={report.cohorts}>
                <CartesianGrid strokeDasharray="3 6" stroke="#d8d4c8" />
                <XAxis dataKey="cohort" tick={{ fontSize: 11 }} />
                <YAxis yAxisId="left" tick={{ fontSize: 11 }} />
                <YAxis yAxisId="right" orientation="right" tickFormatter={(v) => `${Math.round(v * 100)}%`} />
                <Tooltip />
                <Legend />
                <Bar yAxisId="left" dataKey="players" name="Join-year players" fill="#c18b2f" radius={[6, 6, 0, 0]} />
                <Line yAxisId="left" type="monotone" dataKey="median_games" name="Median games" stroke="#174f3f" strokeWidth={2.5} />
                <Line yAxisId="right" type="monotone" dataKey="active_rate_90d" name="Active 90d rate" stroke="#b64a32" strokeWidth={2.5} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </article>

        <article className="panel stagger">
          <div className="panel-head">
            <h3>Puzzle Culture vs Competitive Play</h3>
            <span className="pill">TACTICAL ON-RAMP</span>
          </div>
          <p>
            Puzzle participation is broad, but game participation is much thinner. This is a useful story about how
            people first engage with chess before they become regular competitors.
          </p>
          <div className="chart-wrap">
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={report.puzzle_culture.segments}>
                <CartesianGrid strokeDasharray="3 6" stroke="#d8d4c8" />
                <XAxis dataKey="segment" tick={{ fontSize: 10 }} interval={0} angle={-15} textAnchor="end" height={72} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="players" fill="#6f9da4" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="mini-table">
            {report.puzzle_culture.correlations.map((item) => (
              <div key={item.format} className="mini-row">
                <span>{item.format} correlation</span>
                <strong>{item.correlation.toFixed(2)}</strong>
              </div>
            ))}
          </div>
        </article>
      </section>

      <section className="panel stagger">
        <div className="panel-head">
          <h3>Archetypes And Format Style</h3>
          <span className="pill">PEOPLE, NOT JUST COUNTS</span>
        </div>
        <p>
          These segments make the player base legible for ordinary users. They answer who is arriving, who stays,
          and which styles define the visible chess scene.
        </p>
        <div className="archetype-grid">
          {report.archetypes.map((item) => (
            <article key={item.name} className="archetype-card">
              <p className="route-eyebrow">{fmtInt(item.count)} players</p>
              <h4>{item.name}</h4>
              <p>{item.description}</p>
            </article>
          ))}
        </div>
        <div className="chart-wrap">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={report.outcome_style}>
              <CartesianGrid strokeDasharray="3 6" stroke="#d8d4c8" />
              <XAxis dataKey="format" tick={{ fontSize: 11 }} />
              <YAxis tickFormatter={(v) => `${Math.round(v * 100)}%`} />
              <Tooltip formatter={(value) => tooltipPct(value)} />
              <Legend />
              <Bar dataKey="median_win_rate" fill="#174f3f" radius={[6, 6, 0, 0]} />
              <Bar dataKey="median_draw_rate" fill="#b64a32" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>
    </>
  );
}
