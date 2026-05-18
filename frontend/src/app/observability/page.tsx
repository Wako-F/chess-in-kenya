import { RunHistory } from "@/components/run-history";
import { MetricCard } from "@/components/metric-card";
import { getErrors, getQuality, getRuns } from "@/lib/api";

export default async function ObservabilityPage() {
  const [quality, runs, errors] = await Promise.all([
    getQuality(),
    getRuns(20),
    getErrors(40),
  ]);

  const latest = quality?.latest_run;
  return (
    <main id="main-content" className="atlas-page">
      <div className="atmosphere" aria-hidden />
      <section className="hero compact">
        <div className="hero-copy">
          <p className="eyebrow">Operational clarity</p>
          <h1>Pipeline Observability</h1>
          <p className="lead">
            Live operational view of ingestion reliability, run throughput, and quality drift.
          </p>
        </div>
      </section>

      <section className="metrics-grid">
        <MetricCard label="Latest Run" value={latest ? `#${latest.id}` : "N/A"} accent="ink" />
        <MetricCard label="Latest Status" value={latest?.status ?? "N/A"} accent="jade" />
        <MetricCard label="Latest Updated" value={latest ? latest.updated_count.toLocaleString() : "N/A"} accent="sun" />
        <MetricCard label="Latest Errors" value={latest ? latest.error_count.toLocaleString() : "N/A"} accent="coral" />
      </section>

      <RunHistory runs={runs?.items ?? []} errors={errors?.items ?? []} />
    </main>
  );
}

