"use client";

import {
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Bar,
} from "recharts";

import type { CohortPoint, CorrelationPoint, PercentileBandPoint } from "@/lib/types";

const labels: Record<string, string> = {
  rapid_rating: "Rapid",
  blitz_rating: "Blitz",
  bullet_rating: "Bullet",
  daily_rating: "Daily",
  highest_puzzle_rating: "Puzzle",
};

function colorForCorrelation(v: number) {
  // -1 (red) to +1 (green)
  const clamped = Math.max(-1, Math.min(1, v));
  if (clamped > 0.75) return "#0d5d4e";
  if (clamped > 0.45) return "#127a66";
  if (clamped > 0.15) return "#5c9b8e";
  if (clamped > -0.15) return "#cbbba6";
  if (clamped > -0.45) return "#d88f73";
  if (clamped > -0.75) return "#cc6f4a";
  return "#b94a1d";
}

export function DeepAnalytics({
  correlation,
  percentiles,
  cohorts,
}: {
  correlation: CorrelationPoint[];
  percentiles: PercentileBandPoint[];
  cohorts: CohortPoint[];
}) {
  const keys = Array.from(new Set(correlation.map((c) => c.x)));
  const pctData = Array.from(new Set(percentiles.map((p) => p.percentile)))
    .sort((a, b) => a - b)
    .map((pct) => {
      const row: Record<string, number> = { percentile: pct };
      percentiles
        .filter((p) => p.percentile === pct)
        .forEach((p) => {
          row[p.format] = p.rating;
        });
      return row;
    });

  return (
    <section className="deep-grid">
      <article className="panel stagger">
        <div className="panel-head">
          <h3>Rating Correlation Matrix</h3>
          <span className="pill">DEPENDENCY MAP</span>
        </div>
        <p>
          Correlation is not causation, but it does show which skill domains tend to travel together.
          In this dataset, puzzle and rapid tend to move together more tightly than puzzle and bullet.
        </p>
        {keys.length ? (
          <div className="heatmap">
            <table className="heat-table">
              <thead>
                <tr>
                  <th />
                  {keys.map((k) => (
                    <th key={`h-${k}`}>{labels[k] ?? k}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {keys.map((rowKey) => (
                  <tr key={`row-${rowKey}`}>
                    <th>{labels[rowKey] ?? rowKey}</th>
                    {keys.map((colKey) => {
                      const point = correlation.find((c) => c.x === colKey && c.y === rowKey);
                      const v = point?.value ?? 0;
                      return (
                        <td key={`${rowKey}-${colKey}`}>
                          <div
                            className="heat-cell"
                            style={{ background: colorForCorrelation(v) }}
                            title={`${labels[rowKey] ?? rowKey} vs ${labels[colKey] ?? colKey}: ${v.toFixed(2)}`}
                          >
                            {v.toFixed(2)}
                          </div>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="chart-empty">No correlation data available.</p>
        )}
      </article>

      <article className="panel stagger">
        <div className="panel-head">
          <h3>Percentile Rating Curves</h3>
          <span className="pill">DISTRIBUTION BANDS</span>
        </div>
        <p>
          Percentile curves are a better trust layer than averages. They show what median, upper-tier,
          and elite-local performance actually look like in each format.
        </p>
        {pctData.length ? (
          <div className="chart-wrap">
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={pctData}>
                <CartesianGrid strokeDasharray="3 6" stroke="#e8ddd0" />
                <XAxis dataKey="percentile" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="rapid" stroke="#127a66" dot={false} />
                <Line type="monotone" dataKey="blitz" stroke="#d6521f" dot={false} />
                <Line type="monotone" dataKey="bullet" stroke="#f5ab3c" dot={false} />
                <Line type="monotone" dataKey="daily" stroke="#39424f" dot={false} />
                <Line type="monotone" dataKey="puzzle" stroke="#8d4fdb" dot={false} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <p className="chart-empty">No percentile data available.</p>
        )}
      </article>

      <article className="panel stagger deep-full">
        <div className="panel-head">
          <h3>Cohort Retention (90-day active)</h3>
          <span className="pill">LONGITUDINAL</span>
        </div>
        <p>
          Read this as a proxy for observed recency, not a definitive retention measure. It is directionally useful,
          but it is sensitive to pipeline freshness and to Chess.com&apos;s recency-capped country roster.
        </p>
        {cohorts.length ? (
          <div className="chart-wrap">
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={cohorts}>
                <CartesianGrid strokeDasharray="3 6" stroke="#e8ddd0" />
                <XAxis dataKey="cohort" />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" domain={[0, 1]} />
                <Tooltip />
                <Legend />
                <Bar yAxisId="left" dataKey="total_players" fill="#e6b15d" />
                <Bar yAxisId="left" dataKey="retained_90d" fill="#127a66" />
                <Line yAxisId="right" type="monotone" dataKey="retention_rate" stroke="#d6521f" dot={false} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <p className="chart-empty">No cohort data available.</p>
        )}
      </article>
    </section>
  );
}
