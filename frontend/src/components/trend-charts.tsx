"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type JoinPoint = { month?: string; players?: number };
type DiscoveryPoint = { day?: string; active_players?: number };

type TrendChartsProps = {
  joins: JoinPoint[];
  discovery: DiscoveryPoint[];
};

export function TrendCharts({ joins, discovery }: TrendChartsProps) {
  return (
    <section className="charts-grid">
      <article className="panel stagger">
        <div className="panel-head">
          <h3>Join Momentum</h3>
          <span className="pill">36 MONTHS</span>
        </div>
        <div className="chart-wrap">
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={joins}>
              <defs>
                <linearGradient id="joinFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#ff8f5a" stopOpacity={0.45} />
                  <stop offset="100%" stopColor="#ff8f5a" stopOpacity={0.03} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 6" stroke="#e8ddd0" />
              <XAxis dataKey="month" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Area
                type="monotone"
                dataKey="players"
                stroke="#d6521f"
                strokeWidth={2}
                fill="url(#joinFill)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </article>

      <article className="panel stagger">
        <div className="panel-head">
          <h3>Daily Active Discovery</h3>
          <span className="pill">60 DAYS</span>
        </div>
        <div className="chart-wrap">
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={discovery}>
              <CartesianGrid strokeDasharray="3 6" stroke="#e8ddd0" />
              <XAxis dataKey="day" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="active_players"
                stroke="#127a66"
                strokeWidth={2.5}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </article>
    </section>
  );
}

