"use client";

import { useEffect, useMemo, useState } from "react";

import { DataMarvel } from "@/components/data-marvel";
import { DeepAnalytics } from "@/components/deep-analytics";
import { RatingDistribution } from "@/components/rating-distribution";
import type {
  ActivityBucketPoint,
  CohortPoint,
  CorrelationPoint,
  DistributionPoint,
  FormatSummaryPoint,
  PercentileBandPoint,
  RatingScatterPoint,
} from "@/lib/types";

type AnalyticsPayload = {
  distribution: DistributionPoint[];
  formatSummary: FormatSummaryPoint[];
  activityBuckets: ActivityBucketPoint[];
  scatter: RatingScatterPoint[];
  correlation: CorrelationPoint[];
  percentileBands: PercentileBandPoint[];
  cohorts: CohortPoint[];
};

type EndpointStatus = {
  label: string;
  ok: boolean;
  detail: string;
};

const API_BASE = process.env.NEXT_PUBLIC_CHESSKE_API_BASE ?? "http://127.0.0.1:8000";

async function fetchItems<T>(path: string): Promise<T[]> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`${path} -> ${res.status}`);
  }
  const json = (await res.json()) as { items?: T[] };
  return json.items ?? [];
}

export function AnalyticsLab() {
  const [data, setData] = useState<AnalyticsPayload>({
    distribution: [],
    formatSummary: [],
    activityBuckets: [],
    scatter: [],
    correlation: [],
    percentileBands: [],
    cohorts: [],
  });
  const [loading, setLoading] = useState(true);
  const [statuses, setStatuses] = useState<EndpointStatus[]>([]);

  useEffect(() => {
    let mounted = true;
    async function load() {
      setLoading(true);
      const defs = [
        { key: "distribution", label: "distribution", path: "/stats/distribution?bucket_size=100" },
        { key: "formatSummary", label: "format-summary", path: "/stats/format-summary" },
        { key: "activityBuckets", label: "activity-buckets", path: "/stats/activity-buckets" },
        { key: "scatter", label: "rating-scatter", path: "/stats/rating-scatter?limit=1200" },
        { key: "correlation", label: "correlation-matrix", path: "/stats/correlation-matrix" },
        { key: "percentileBands", label: "percentile-bands", path: "/stats/percentile-bands" },
        { key: "cohorts", label: "cohort-retention", path: "/stats/cohort-retention?months=24" },
      ] as const;

      const nextStatuses: EndpointStatus[] = [];
      const nextData: AnalyticsPayload = {
        distribution: [],
        formatSummary: [],
        activityBuckets: [],
        scatter: [],
        correlation: [],
        percentileBands: [],
        cohorts: [],
      };

      function setDataKey<K extends keyof AnalyticsPayload>(key: K, items: AnalyticsPayload[K]) {
        nextData[key] = items;
      }

      await Promise.all(
        defs.map(async (d) => {
          try {
            if (d.key === "distribution") {
              const items = await fetchItems<DistributionPoint>(d.path);
              setDataKey(d.key, items);
              nextStatuses.push({ label: d.label, ok: true, detail: `${items.length} rows` });
              return;
            }
            if (d.key === "formatSummary") {
              const items = await fetchItems<FormatSummaryPoint>(d.path);
              setDataKey(d.key, items);
              nextStatuses.push({ label: d.label, ok: true, detail: `${items.length} rows` });
              return;
            }
            if (d.key === "activityBuckets") {
              const items = await fetchItems<ActivityBucketPoint>(d.path);
              setDataKey(d.key, items);
              nextStatuses.push({ label: d.label, ok: true, detail: `${items.length} rows` });
              return;
            }
            if (d.key === "scatter") {
              const items = await fetchItems<RatingScatterPoint>(d.path);
              setDataKey(d.key, items);
              nextStatuses.push({ label: d.label, ok: true, detail: `${items.length} rows` });
              return;
            }
            if (d.key === "correlation") {
              const items = await fetchItems<CorrelationPoint>(d.path);
              setDataKey(d.key, items);
              nextStatuses.push({ label: d.label, ok: true, detail: `${items.length} rows` });
              return;
            }
            if (d.key === "percentileBands") {
              const items = await fetchItems<PercentileBandPoint>(d.path);
              setDataKey(d.key, items);
              nextStatuses.push({ label: d.label, ok: true, detail: `${items.length} rows` });
              return;
            }
            const items = await fetchItems<CohortPoint>(d.path);
            setDataKey(d.key, items);
            nextStatuses.push({ label: d.label, ok: true, detail: `${items.length} rows` });
          } catch (err) {
            nextStatuses.push({
              label: d.label,
              ok: false,
              detail: err instanceof Error ? err.message : "fetch failed",
            });
          }
        }),
      );

      if (!mounted) return;
      setData(nextData);
      setStatuses(nextStatuses.sort((a, b) => Number(b.ok) - Number(a.ok)));
      setLoading(false);
    }
    void load();
    return () => {
      mounted = false;
    };
  }, []);

  const failed = useMemo(() => statuses.filter((s) => !s.ok), [statuses]);

  return (
    <>
      <section className="panel stagger">
        <div className="panel-head">
          <h3>Analytics Engine Status</h3>
          <span className="pill">{loading ? "LOADING" : failed.length ? "DEGRADED" : "HEALTHY"}</span>
        </div>
        <p className="mono">
          API: <code>{API_BASE}</code>
        </p>
        <div className="status-grid mono">
          {statuses.map((s) => (
            <div key={s.label} className={`status-chip ${s.ok ? "ok" : "bad"}`}>
              <strong>{s.label}</strong>: {s.detail}
            </div>
          ))}
        </div>
      </section>

      <RatingDistribution points={data.distribution} />
      <DataMarvel formats={data.formatSummary} activity={data.activityBuckets} scatter={data.scatter} />
      <DeepAnalytics
        correlation={data.correlation}
        percentiles={data.percentileBands}
        cohorts={data.cohorts}
      />
    </>
  );
}
