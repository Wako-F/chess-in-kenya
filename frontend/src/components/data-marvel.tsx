"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";

import type { ActivityBucketPoint, FormatSummaryPoint, RatingScatterPoint } from "@/lib/types";

const pieColors = ["#127a66", "#d6521f", "#f5ab3c", "#39424f"];

function titleCase(s: string) {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

export function DataMarvel({
  formats,
  activity,
  scatter,
}: {
  formats: FormatSummaryPoint[];
  activity: ActivityBucketPoint[];
  scatter: RatingScatterPoint[];
}) {
  const gamesPie = formats
    .filter((f) => f.format !== "puzzle")
    .map((f) => ({ name: titleCase(f.format), value: Number(f.games) || 0 }))
    .filter((f) => f.value > 0);
  const radar = formats.map((f) => ({
    format: titleCase(f.format),
    rating: Math.round(Number(f.avg_rating) || 0),
  })).filter((p) => Number.isFinite(p.rating));
  const activityData = activity.map((a) => ({
    bucket: a.bucket,
    players: Number(a.players) || 0,
  })).filter((a) => a.players >= 0);
  const scatterData = scatter.map((p) => ({
    rapid: Number(p.rapid_rating) || 0,
    blitz: Number(p.blitz_rating) || 0,
    games: Math.max(1, Math.min(10000, Number(p.total_games) || 0)),
  })).filter((p) => p.rapid > 0 && p.blitz > 0);

  return (
    <section className="marvel-grid">
      <article className="panel stagger">
        <div className="panel-head">
          <h3>Format Rating Radar</h3>
          <span className="pill">SKILL TOPOLOGY</span>
        </div>
        {radar.length ? (
          <div className="chart-wrap">
            <ResponsiveContainer width="100%" height={300}>
              <RadarChart data={radar}>
                <PolarGrid stroke="#e6d5bf" />
                <PolarAngleAxis dataKey="format" />
                <Tooltip />
                <Radar dataKey="rating" stroke="#d6521f" fill="#d6521f" fillOpacity={0.35} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <p className="chart-empty">No radar data available.</p>
        )}
      </article>

      <article className="panel stagger">
        <div className="panel-head">
          <h3>Game Volume Composition</h3>
          <span className="pill">FORMAT SHARE</span>
        </div>
        {gamesPie.length ? (
          <div className="chart-wrap">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie data={gamesPie} dataKey="value" nameKey="name" outerRadius={95} innerRadius={48}>
                  {gamesPie.map((entry, i) => (
                    <Cell key={entry.name} fill={pieColors[i % pieColors.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <p className="chart-empty">No composition data available.</p>
        )}
      </article>

      <article className="panel stagger">
        <div className="panel-head">
          <h3>Player Activity Distribution</h3>
          <span className="pill">ENGAGEMENT</span>
        </div>
        {activityData.length ? (
          <div className="chart-wrap">
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={activityData}>
                <CartesianGrid strokeDasharray="3 6" stroke="#e8ddd0" />
                <XAxis dataKey="bucket" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="players" fill="#127a66" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <p className="chart-empty">No activity-bucket data available.</p>
        )}
      </article>

      <article className="panel stagger">
        <div className="panel-head">
          <h3>Rapid vs Blitz Rating Space</h3>
          <span className="pill">SCATTER MAP</span>
        </div>
        {scatterData.length ? (
          <div className="chart-wrap">
            <ResponsiveContainer width="100%" height={280}>
              <ScatterChart>
                <CartesianGrid strokeDasharray="3 6" stroke="#e8ddd0" />
                <XAxis type="number" dataKey="rapid" name="Rapid" />
                <YAxis type="number" dataKey="blitz" name="Blitz" />
                <ZAxis type="number" dataKey="games" range={[14, 140]} />
                <Tooltip cursor={{ strokeDasharray: "3 3" }} />
                <Scatter data={scatterData} fill="#d6521f" fillOpacity={0.42} />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <p className="chart-empty">No scatter data available.</p>
        )}
      </article>
    </section>
  );
}
