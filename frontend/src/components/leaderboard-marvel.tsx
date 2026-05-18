"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export function LeaderboardMarvel({
  summary,
}: {
  summary: Array<{ board: string; topScore: number; avgTopScore: number }>;
}) {
  const rows = summary.map((s) => ({
    board: s.board.toUpperCase(),
    "Top Score": s.topScore,
    "Top 15 Avg": Math.round(s.avgTopScore),
  }));

  return (
    <article className="panel stagger">
      <div className="panel-head">
        <h3>Leaderboard Strength Profile</h3>
        <span className="pill">COMPARATIVE</span>
      </div>
      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={rows}>
            <CartesianGrid strokeDasharray="3 6" stroke="#d8d4c8" />
            <XAxis dataKey="board" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="Top Score" fill="#b64a32" radius={[4, 4, 0, 0]} />
            <Bar dataKey="Top 15 Avg" fill="#174f3f" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </article>
  );
}

