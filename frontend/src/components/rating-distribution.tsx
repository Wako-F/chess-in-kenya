"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type DistributionPoint = {
  bucket: number;
  players: number;
};

export function RatingDistribution({ points }: { points: DistributionPoint[] }) {
  const formatted = points.map((p) => ({
    range: `${p.bucket}-${p.bucket + 99}`,
    players: p.players,
  }));

  return (
    <article className="panel stagger">
      <div className="panel-head">
        <h3>Rapid Rating Distribution</h3>
        <span className="pill">BUCKET 100</span>
      </div>
      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={formatted}>
            <CartesianGrid strokeDasharray="3 6" stroke="#e8ddd0" />
            <XAxis dataKey="range" tick={{ fontSize: 10 }} interval={2} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip />
            <Bar dataKey="players" fill="#127a66" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </article>
  );
}

