import { getQuality } from "@/lib/api";

export const revalidate = 300;

export default async function MethodologyPage() {
  const quality = await getQuality();
  return (
    <main id="main-content" className="atlas-page">
      <div className="atmosphere" aria-hidden />
      <section className="hero compact">
        <div className="hero-copy">
          <p className="eyebrow">Transparency</p>
          <h1>Methodology & Data Trust</h1>
          <p className="lead">
            This system is intentionally explicit about source constraints and processing logic.
            It favors explainability and operational reliability over vanity metrics.
          </p>
        </div>
      </section>

      <section className="panel prose stagger">
        <h3>Collection Model</h3>
        <p>
          Chess.com country endpoint returns recently active users only. To preserve historical
          continuity, the platform uses rolling discovery: active users are fetched daily and upserted
          into the canonical ledger, while stale users are revalidated through a refresh queue.
        </p>
        <h3>Storage Model</h3>
        <p>
          Data is stored in normalized SQLite tables (`users`, `user_stats_latest`,
          `country_active_snapshots`, `pipeline_runs`, `run_errors`) to support reproducibility,
          queryability, and operational diagnostics.
        </p>
        <h3>Validation Rules</h3>
        <p>
          Quality gates enforce deduplicated usernames, conflict-marker sanitation, and required-schema
          checks before export. The frontend consumes the API contract, not raw ad-hoc CSV transforms.
        </p>
        <h3>Current Quality Snapshot</h3>
        <ul>
          <li>Total users in ledger: {quality?.total_users ?? "N/A"}</li>
          <li>Active users: {quality?.active_users ?? "N/A"}</li>
          <li>Missing stats for active users: {quality?.missing_stats_for_active_users ?? "N/A"}</li>
          <li>Latest active coverage ratio: {quality ? `${(quality.latest_active_coverage_ratio * 100).toFixed(1)}%` : "N/A"}</li>
        </ul>
      </section>
    </main>
  );
}

