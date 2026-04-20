"use client";

import { useEffect, useMemo, useState } from "react";

import { DataMarvel } from "@/components/data-marvel";
import { DeepAnalytics } from "@/components/deep-analytics";
import { RatingDistribution } from "@/components/rating-distribution";
import { StoryMarvel } from "@/components/story-marvel";
import type {
  ActivityBucketPoint,
  CohortPoint,
  CorrelationPoint,
  DistributionPoint,
  FormatSummaryPoint,
  PercentileBandPoint,
  RatingScatterPoint,
  StoryReport,
} from "@/lib/types";

type AnalyticsPayload = {
  distribution: DistributionPoint[];
  formatSummary: FormatSummaryPoint[];
  activityBuckets: ActivityBucketPoint[];
  scatter: RatingScatterPoint[];
  correlation: CorrelationPoint[];
  percentileBands: PercentileBandPoint[];
  cohorts: CohortPoint[];
  story: StoryReport | null;
};

type EndpointStatus = {
  label: string;
  ok: boolean;
  detail: string;
};

type AnalyticsPackResponse = {
  distribution?: { items?: DistributionPoint[] };
  formatSummary?: { items?: FormatSummaryPoint[] };
  activityBuckets?: { items?: ActivityBucketPoint[] };
  scatter?: { items?: RatingScatterPoint[] };
  correlation?: { items?: CorrelationPoint[] };
  percentileBands?: { items?: PercentileBandPoint[] };
  cohorts?: { items?: CohortPoint[] };
  story?: StoryReport | null;
};

const API_BASE = process.env.NEXT_PUBLIC_CHESSKE_API_BASE ?? "http://127.0.0.1:8000";

export function AnalyticsLab() {
  const [data, setData] = useState<AnalyticsPayload>({
    distribution: [],
    formatSummary: [],
    activityBuckets: [],
    scatter: [],
    correlation: [],
    percentileBands: [],
    cohorts: [],
    story: null,
  });
  const [loading, setLoading] = useState(true);
  const [statuses, setStatuses] = useState<EndpointStatus[]>([]);

  useEffect(() => {
    let mounted = true;
    async function load() {
      setLoading(true);
      const nextData: AnalyticsPayload = {
        distribution: [],
        formatSummary: [],
        activityBuckets: [],
        scatter: [],
        correlation: [],
        percentileBands: [],
        cohorts: [],
        story: null,
      };
      let nextStatuses: EndpointStatus[] = [];

      try {
        const res = await fetch(`${API_BASE}/stats/analytics-pack`, { cache: "default" });
        if (!res.ok) {
          throw new Error(`/stats/analytics-pack -> ${res.status}`);
        }
        const pack = (await res.json()) as AnalyticsPackResponse;
        nextData.distribution = pack.distribution?.items ?? [];
        nextData.formatSummary = pack.formatSummary?.items ?? [];
        nextData.activityBuckets = pack.activityBuckets?.items ?? [];
        nextData.scatter = pack.scatter?.items ?? [];
        nextData.correlation = pack.correlation?.items ?? [];
        nextData.percentileBands = pack.percentileBands?.items ?? [];
        nextData.cohorts = pack.cohorts?.items ?? [];
        nextData.story = pack.story ?? null;
        nextStatuses = [
          { label: "analytics-pack", ok: true, detail: "1 request collapsed from 8 endpoints" },
          { label: "distribution", ok: true, detail: `${nextData.distribution.length} rows` },
          { label: "format-summary", ok: true, detail: `${nextData.formatSummary.length} rows` },
          { label: "activity-buckets", ok: true, detail: `${nextData.activityBuckets.length} rows` },
          { label: "rating-scatter", ok: true, detail: `${nextData.scatter.length} rows` },
          { label: "correlation-matrix", ok: true, detail: `${nextData.correlation.length} rows` },
          { label: "percentile-bands", ok: true, detail: `${nextData.percentileBands.length} rows` },
          { label: "cohort-retention", ok: true, detail: `${nextData.cohorts.length} rows` },
          { label: "story-report", ok: true, detail: nextData.story ? "derived metrics ready" : "no data" },
        ];
      } catch (err) {
        nextStatuses = [
          {
            label: "analytics-pack",
            ok: false,
            detail: err instanceof Error ? err.message : "fetch failed",
          },
        ];
      }

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
      <StoryMarvel report={data.story} />

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

      <section className="panel stagger">
        <div className="panel-head">
          <h3>Statistical Lab</h3>
          <span className="pill">SUPPORTING EVIDENCE</span>
        </div>
        <p>
          The charts below back up the headline story with distribution, skill-shape, and cohort structure.
          They are most useful when read after the narrative modules above, not before them.
        </p>
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
