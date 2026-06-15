import Link from "next/link";
import { MetricCard } from "@/components/metric-card";
import { getOverview, getQuality } from "@/lib/api";

export const revalidate = 300;

const ledgerGrowth = [
  ["2024-12-04", "2bf7165", "First draft", "4,337", "4,336", "8 cols", "Raw country scrape: username, title, join date, last online, bullet, blitz, rapid, FIDE."],
  ["2024-12-06", "7a9b300", "Stats expansion", "6,080", "6,080", "24 cols", "Per-format totals and records arrived; the dataset stopped being only ratings."],
  ["2024-12-14", "59506c1", "Ledger crossed 10k", "11,044", "11,044", "cleaned CSV", "The cumulative ledger crossed 10k, but the active-country endpoint itself was still around 5k-6k."],
  ["2024-12-22", "052240a", "Skip-ci automation", "18,460", "18,460", "master CSV", "The auto-update workflow was now committing processed results back to Git."],
  ["2025-01-01", "8af174f", "New year base", "25,286", "25,286", "master CSV", "The ledger had grown almost sixfold from the first scrape."],
  ["2025-02-01", "b629450", "February base", "41,852", "41,852", "master CSV", "Daily automation compounded discovery into a much larger historical register."],
  ["2025-03-01", "1fdebd0", "March base", "55,405", "55,405", "master CSV", "At this point, the project was clearly a rolling ledger, not a one-off dashboard."],
  ["2025-04-01", "16216aa", "April base", "68,921", "68,921", "master CSV", "Growth continued, then the first obvious maintenance gap appeared in April."],
  ["2025-05-01", "f29a857", "May base", "78,080", "78,080", "master CSV", "Automation resumed and carried the dataset forward."],
  ["2025-06-01", "5f24dcb", "June base", "88,595", "88,595", "master CSV", "The ledger was adding roughly ten thousand observed accounts per month."],
  ["2025-07-01", "952efd3", "Six figures", "101,093", "101,093", "master CSV", "First measured repo snapshot above 100k unique observed accounts."],
  ["2025-08-01", "2f99c7e", "August base", "110,749", "110,749", "master CSV", "Still clean: rows and unique usernames matched."],
  ["2025-09-01", "2db8015", "Duplicate surge", "227,919", "118,367", "master CSV", "Rows jumped, but unique users did not. More rows had stopped meaning more players."],
  ["2025-12-01", "85e41f8", "Inflated winter ledger", "242,988", "133,436", "master CSV", "The duplicate delta had reached 109,552 rows, proving the need for identity controls."],
  ["2026-04-19", "5a2d78f", "Canonical refresh", "143,238", "143,238", "master CSV", "The public dataset was rebuilt back to one row per username."],
  ["2026-05-19", "VPS", "Production API", "155,972", "155,972", "Postgres", "The live VPS-backed API is now ahead of the checked-in CSV and should be treated as current truth."],
];

const endpointHistory = [
  ["2024-12-10", 5805, "First Africa count"],
  ["2025-01-01", 5495, "Old normal"],
  ["2025-02-28", 6918, "Late-Feb lift"],
  ["2025-04-04", 7605, "Pre-gap high"],
  ["2025-06-26", 8005, "First 8k"],
  ["2025-07-22", 8836, "Last sub-10k"],
  ["2025-07-23", 10000, "Endpoint hits cap"],
  ["2025-08-01", 10000, "Pinned"],
  ["2025-12-01", 10000, "Still capped"],
  ["2026-05-19", 10000, "VPS run"],
];

const ledgerChart = [
  ["Dec 2024", 4337],
  ["Jan 2025", 25286],
  ["Mar 2025", 55405],
  ["Jul 2025", 101093],
  ["Dec 2025", 133436],
  ["Apr 2026", 143238],
  ["VPS now", 155972],
];

const automationCadence = [
  ["2024-12", "34", "85", "Workflow born; early manual commits plus GitHub automation setup."],
  ["2025-01", "31", "37", "Daily automation mostly held."],
  ["2025-02", "46", "51", "Multiple days had more than one automated data commit."],
  ["2025-03", "60", "61", "Peak cadence: roughly twice-daily processed-data commits."],
  ["2025-04", "28", "29", "A 15-day quiet stretch split the month."],
  ["2025-05", "58", "59", "Automation recovered strongly."],
  ["2025-06", "53", "54", "The rolling ledger kept growing."],
  ["2025-07", "58", "59", "Six-figure registry month."],
  ["2025-08", "50", "52", "Still frequent, but heading toward the duplicate-pressure period."],
  ["2025-09", "58", "58", "High automation volume, but row inflation appeared."],
  ["2025-10", "0", "0", "No commits: the project effectively went quiet."],
  ["2025-11", "39", "40", "Automation resumed after the October gap."],
  ["2025-12", "60", "60", "Heavy automation, but against an already inflated ledger."],
  ["2026-01", "0", "0", "No automation commits."],
  ["2026-02", "0", "0", "No automation commits."],
  ["2026-03", "0", "0", "No automation commits."],
  ["2026-04", "21", "38", "Project revived: production platform, Postgres, API, analytics work."],
  ["2026-05", "35", "54", "VPS cutover, Redis/cache work, live lookup, and production hardening."],
];

const quietGaps = [
  ["2025-04-04 -> 2025-04-20", "15 days", "The first visible automation silence after a strong March."],
  ["2025-09-29 -> 2025-11-11", "42 days", "October disappeared from the history; this is the clearest 'forgot about it' gap."],
  ["2025-12-30 -> 2026-04-20", "110 days", "The long winter/spring pause before the production-platform revival."],
];

const productionFacts = [
  ["Active users", "155,972", "VPS Postgres/API, not the checked-in CSV."],
  ["Total games", "82,951,536", "Current production sum across rapid, blitz, bullet, and daily."],
  ["Median games", "10", "The normal tracked player remains very light-touch."],
  ["Mean games", "531.8", "The mean is far higher because volume is extremely concentrated."],
  ["Rapid players", "126,311", "81.0% of production active users have rapid data."],
  ["Puzzle players", "149,532", "95.9% have puzzle rating data, the broadest skill signal."],
  ["Blitz players", "47,210", "30.3% have blitz data."],
  ["Bullet players", "35,154", "22.5% have bullet data."],
];

const productionOps = [
  ["2026-05-18 15:49 UTC", "Initial VPS/Postgres bootstrap", "155,564 users loaded from cleaned_master_chess_players.csv."],
  ["2026-05-19 00:01 UTC", "First rolling run failed", "10,000 active users were fetched, then the run failed on a Postgres executemany wrapper issue."],
  ["2026-05-19 12:06-15:10 UTC", "Long rolling run succeeded", "10,000 active users processed; 9,990 updated, 1 deleted, 9 errors."],
  ["2026-05-19 17:10 UTC", "Export and rebootstrap tension", "CSV export reached 155,972 total, but verification later saw csv_rows=155,564 vs db_users=155,972."],
  ["Current timer", "VPS owns ingestion", "chesske-pipeline.timer is enabled and scheduled twice daily; GitHub Actions no longer owns production data."],
];

const activityTiers = [
  ["0 games", "26,317", "16.9%"],
  ["1-9 games", "49,748", "31.9%"],
  ["10-49 games", "28,752", "18.4%"],
  ["50-199 games", "18,944", "12.1%"],
  ["200-999 games", "16,410", "10.5%"],
  ["1k-4.9k games", "11,853", "7.6%"],
  ["5k+ games", "3,948", "2.5%"],
];

const concentrationFacts = [
  ["Top 1%", "35.1% of games", "1,559 users account for 29.1M games."],
  ["Top 5%", "71.3% of games", "7,798 users account for 59.1M games."],
  ["Top 10%", "86.8% of games", "15,597 users account for 72.0M games."],
];

const formatCoverage = [
  ["Puzzle", 149532, "95.9%"],
  ["Rapid", 126311, "81.0%"],
  ["Blitz", 47210, "30.3%"],
  ["Bullet", 35154, "22.5%"],
  ["Daily", 34299, "22.0%"],
];

const phases = [
  {
    title: "1. The scrape proved Kenya was visible",
    date: "Dec 2024",
    body:
      "The first dataset was small but important: about 4.3k observed Kenyan accounts from Chess.com country discovery. It established that Kenya could be studied as a distinct online chess ecosystem.",
    evidence: "First snapshot: 4,337 rows, 4,336 unique usernames, 8 columns.",
  },
  {
    title: "2. The dataset learned behavior",
    date: "Dec 2024",
    body:
      "Within days, the data grew from profile fields into chess behavior: total games, format totals, ratings, wins, losses, draws, puzzle data, converted timestamps, join trends, country counts, and dashboards.",
    evidence: "The partial CSV grew from 8 to 24 columns; the master ledger introduced 26+ fields.",
  },
  {
    title: "3. The active endpoint hit 10k in July",
    date: "Jul 23, 2025",
    body:
      "This is the big country-endpoint milestone: for months, Chess.com's Kenya country response returned roughly five to seven thousand recently active players. It reached 8,836 on July 22, 2025, then hit 10,000 on July 23 and stayed pinned there.",
    evidence: "african_country_player_counts.csv: 8,836 on 2025-07-22, then 10,000 on 2025-07-23.",
  },
  {
    title: "4. Automation made the ledger remember",
    date: "2025",
    body:
      "The automated commits were not noise. They were the data engine. The project had 345 distinct days with automated data commits across the full history, including 60 auto commits in March 2025 and 60 in December 2025.",
    evidence: "Git history shows 34 auto commits in Dec 2024, then 31 in Jan, 46 in Feb, and 60 in Mar 2025.",
  },
  {
    title: "5. Absence is part of the data story",
    date: "2025-2026",
    body:
      "The missing months matter because rolling discovery only works when it rolls. October 2025 had no commits. January, February, and March 2026 had no automation commits. Those gaps explain why later refreshes had to do heavier catch-up work.",
    evidence: "Longest automation silence: 110 days from Dec 30, 2025 to Apr 20, 2026.",
  },
  {
    title: "6. More rows became a warning sign",
    date: "Sep-Dec 2025",
    body:
      "By September 2025, row count and player count diverged. The ledger showed 227,919 rows but only 118,367 unique usernames. By December, the duplicate gap reached 109,552 rows.",
    evidence: "This is why the April 2026 canonical refresh matters.",
  },
  {
    title: "7. Production moved to the VPS",
    date: "May 2026",
    body:
      "Production data now lives on the Contabo VPS in PostgreSQL, served through FastAPI and consumed by the Next.js frontend. The API, not the checked-in CSV, is the accurate current data source.",
    evidence: "VPS API currently reports 155,972 active users and 82,951,536 games.",
  },
];

function fmt(n: number | null | undefined) {
  if (n === null || n === undefined) return "N/A";
  return n.toLocaleString();
}

function pct(v: number | null | undefined) {
  if (v === null || v === undefined) return "N/A";
  return `${(v * 100).toFixed(1)}%`;
}

function barWidth(value: number, max: number) {
  return `${Math.max(3, Math.round((value / max) * 100))}%`;
}

export default async function DataJourneyPage() {
  const [overview, quality] = await Promise.all([getOverview(), getQuality()]);

  return (
    <main id="main-content" className="atlas-page">
      <div className="atmosphere" aria-hidden />
      <section className="hero compact">
        <div className="hero-copy">
          <p className="eyebrow">Data history</p>
          <h1>The Data Journey</h1>
          <p className="lead">
            The honest version: a 4.3k-player scrape became a rolling ledger, then an inflated
            CSV, then a cleaned production data platform. The gaps, failures, duplicate rows,
            and VPS cutover are part of the story.
          </p>
          <div className="run-meta mono">
            <span className="pill">VPS-verified</span>
            <span>Current production users: {fmt(overview?.total_players ?? 155972)}</span>
            <span>Latest coverage: {quality ? pct(quality.latest_active_coverage_ratio) : "API pending"}</span>
          </div>
        </div>
      </section>

      <section className="metrics-grid">
        <MetricCard label="First Snapshot" value="4,337" accent="sun" />
        <MetricCard label="Endpoint Hit 10k" value="Jul 23, 2025" accent="jade" />
        <MetricCard label="Production Users" value={fmt(overview?.total_players ?? 155972)} accent="coral" />
        <MetricCard label="Production Games" value={fmt(overview?.total_games ?? 82951536)} accent="ink" />
      </section>

      <section className="panel intro stagger">
        <div className="panel-head">
          <h2>The Core Lesson</h2>
          <span className="pill">Rows are not truth</span>
        </div>
        <div>
          <p>
            The project did not just grow. It learned what can go wrong when growth is measured
            by raw rows. Early automation successfully discovered more Kenyan accounts, but later
            history showed duplicate pressure, inactive-window ambiguity, missing automation
            months, and production-state drift between CSV and Postgres.
          </p>
          <p>
            So the current data journey has two timelines: the historical Git ledger, which shows
            how the dataset was built, and the VPS-backed production API, which is the current
            source of truth for live numbers.
          </p>
        </div>
      </section>

      <section className="visual-grid">
        <div className="panel stagger">
          <div className="panel-head">
            <h2>Country Endpoint Breakthrough</h2>
            <span className="pill">Recently active response</span>
          </div>
          <p>
            This is the threshold you meant: not cumulative ledger size, but the number returned by
            Chess.com&apos;s Kenya country endpoint. It lived around the 5k band for months, climbed
            through June and July, then hit the 10k ceiling on July 23, 2025.
          </p>
          <div className="bar-chart endpoint-chart">
            {endpointHistory.map(([date, value, label]) => (
              <div className={`bar-row ${Number(value) === 10000 ? "cap" : ""}`} key={`${date}-${label}`}>
                <div className="bar-label">
                  <strong>{date}</strong>
                  <span>{label}</span>
                </div>
                <div className="bar-track">
                  <span style={{ width: barWidth(Number(value), 10000) }} />
                </div>
                <em>{Number(value).toLocaleString()}</em>
              </div>
            ))}
          </div>
        </div>

        <div className="panel stagger">
          <div className="panel-head">
            <h2>Ledger Accumulation</h2>
            <span className="pill">Unique users</span>
          </div>
          <p>
            The endpoint cap is only the daily discovery window. The ledger kept accumulating
            observed users across runs, which is how a 10k active window became a 155k production
            registry.
          </p>
          <div className="bar-chart">
            {ledgerChart.map(([label, value]) => (
              <div className="bar-row" key={label}>
                <div className="bar-label">
                  <strong>{label}</strong>
                  <span>canonical users</span>
                </div>
                <div className="bar-track">
                  <span style={{ width: barWidth(Number(value), 155972) }} />
                </div>
                <em>{Number(value).toLocaleString()}</em>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="panel stagger">
        <div className="panel-head">
          <h2>Automation Heat</h2>
          <span className="pill">Auto commits per month</span>
        </div>
        <div className="month-strip">
          {automationCadence.map(([month, auto, total]) => (
            <div className={`month-cell ${Number(auto) === 0 ? "empty" : ""}`} key={month}>
              <span style={{ height: barWidth(Number(auto), 60) }} />
              <strong>{auto}</strong>
              <small>{month}</small>
              <em>{total} total</em>
            </div>
          ))}
        </div>
      </section>

      <section className="panel stagger">
        <div className="panel-head">
          <h2>Ledger Milestones</h2>
          <span className="pill">Git plus VPS</span>
        </div>
        <div className="journey-table-wrap">
          <table className="journey-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Moment</th>
                <th>Rows</th>
                <th>Unique</th>
                <th>Shape</th>
                <th>What it means</th>
              </tr>
            </thead>
            <tbody>
              {ledgerGrowth.map(([date, commit, label, rows, unique, shape, note]) => (
                <tr key={`${date}-${commit}`}>
                  <td>{date}</td>
                  <td>
                    <strong>{label}</strong>
                    <span>{commit}</span>
                  </td>
                  <td>{rows}</td>
                  <td>{unique}</td>
                  <td>{shape}</td>
                  <td>{note}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="journey-timeline">
        {phases.map((phase) => (
          <article className="journey-step stagger" key={phase.title}>
            <div className="journey-marker">
              <span>{phase.date}</span>
            </div>
            <div>
              <h3>{phase.title}</h3>
              <p>{phase.body}</p>
              <p className="journey-evidence">{phase.evidence}</p>
            </div>
          </article>
        ))}
      </section>

      <section className="panel stagger">
        <div className="panel-head">
          <h2>Automation Cadence</h2>
          <span className="pill">Commit history</span>
        </div>
        <p>
          Automated commits are a proxy for when the project was actively refreshing and committing
          processed data. They also show the human story: periods of intense maintenance, then
          quiet gaps where rolling discovery stopped rolling.
        </p>
        <div className="journey-table-wrap">
          <table className="journey-table compact-table">
            <thead>
              <tr>
                <th>Month</th>
                <th>Auto commits</th>
                <th>Total commits</th>
                <th>Read</th>
              </tr>
            </thead>
            <tbody>
              {automationCadence.map(([month, auto, total, note]) => (
                <tr key={month}>
                  <td>{month}</td>
                  <td>{auto}</td>
                  <td>{total}</td>
                  <td>{note}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="story-grid">
        <div className="panel stagger">
          <div className="panel-head">
            <h2>Quiet Gaps</h2>
            <span className="pill">Missing months</span>
          </div>
          <div className="mini-table">
            {quietGaps.map(([period, duration, note]) => (
              <div className="mini-row rich-row" key={period}>
                <span>{period}</span>
                <strong>{duration}</strong>
                <p>{note}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="panel stagger">
          <div className="panel-head">
            <h2>Production Cutover</h2>
            <span className="pill">VPS logs</span>
          </div>
          <div className="mini-table">
            {productionOps.map(([time, title, note]) => (
              <div className="mini-row rich-row" key={`${time}-${title}`}>
                <span>{time}</span>
                <strong>{title}</strong>
                <p>{note}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="panel stagger">
        <div className="panel-head">
          <h2>Current Production Shape</h2>
          <span className="pill">VPS Postgres/API</span>
        </div>
        <div className="snapshot-grid">
          {productionFacts.map(([label, value, note]) => (
            <div className="snapshot-stat" key={label}>
              <span>{label}</span>
              <strong>{value}</strong>
              <p>{note}</p>
            </div>
          ))}
        </div>
        <div className="coverage-board">
          <div>
            <h3>Format Coverage</h3>
            <p>
              Puzzle and rapid dominate coverage. Blitz, bullet, and daily are real but much smaller
              slices of the active production registry.
            </p>
          </div>
          <div className="coverage-bars">
            {formatCoverage.map(([label, value, share]) => (
              <div className="coverage-row" key={label}>
                <span>{label}</span>
                <div className="bar-track">
                  <span style={{ width: barWidth(Number(value), 155972) }} />
                </div>
                <strong>{share}</strong>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="story-grid">
        <div className="panel stagger">
          <div className="panel-head">
            <h2>Activity Tiers</h2>
            <span className="pill">Production users</span>
          </div>
          <div className="mini-table">
            {activityTiers.map(([label, players, share]) => (
              <div className="mini-row" key={label}>
                <span>{label}</span>
                <strong>{players}</strong>
                <em>{share}</em>
              </div>
            ))}
          </div>
        </div>

        <div className="panel stagger">
          <div className="panel-head">
            <h2>Concentration</h2>
            <span className="pill">Games</span>
          </div>
          <p>
            The production dataset is broad, but play volume is not evenly distributed. This is
            why the project needs medians, percentiles, and tiering rather than only averages.
          </p>
          <div className="share-row journey-share">
            {concentrationFacts.map(([label, value, note]) => (
              <div className="share-card" key={label}>
                <span>{label}</span>
                <strong>{value}</strong>
                <small>{note}</small>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="panel intro stagger">
        <div className="panel-head">
          <h2>What Needs Watching</h2>
          <span className="pill">Operational truth</span>
        </div>
        <div>
          <p>
            The latest production API numbers are strong, but the VPS logs show a real operational
            caveat: the current database was recently bootstrapped and the pipeline history in
            Postgres is not a complete historical record. Git is still the better source for the
            long automation timeline; VPS is the better source for current production state.
          </p>
          <p>
            The next data-quality milestone should be preserving pipeline runs across bootstraps,
            separating true active-country snapshots from full-ledger imports, and resolving the
            CSV/Postgres verification mismatch so the production timer can be trusted end to end.
          </p>
        </div>
      </section>

      <section className="route-cards journey-routes">
        <Link href="/methodology" className="route-card stagger">
          <p className="route-eyebrow">Trust Lens</p>
          <h3>Read the methodology</h3>
          <p>How to interpret active users, rolling discovery, quality ratios, and data gaps.</p>
        </Link>
        <Link href="/observability" className="route-card stagger">
          <p className="route-eyebrow">Ops Lens</p>
          <h3>Inspect pipeline health</h3>
          <p>Recent runs, error traces, and production data freshness in one place.</p>
        </Link>
        <Link href="/leaderboards" className="route-card stagger">
          <p className="route-eyebrow">Competitive Lens</p>
          <h3>See the rankings</h3>
          <p>The current production leaderboard surface built from the VPS-backed API.</p>
        </Link>
      </section>
    </main>
  );
}
