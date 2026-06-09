"use client";

import {
  Area,
  AreaChart,
  Bar,
  ComposedChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type JoinPoint = { month?: string; players?: number };
type DiscoveryPoint = { day?: string; new_signups?: number; new_logins?: number };
type LedgerAddPoint = {
  day?: string;
  new_tracked_players?: number;
  cumulative_tracked_players?: number;
};

type TrendChartsProps = {
  joins: JoinPoint[];
  discovery: DiscoveryPoint[];
  ledgerAdds: LedgerAddPoint[];
};

export function TrendCharts({ joins, discovery, ledgerAdds }: TrendChartsProps) {
  return (
    <section className="charts-grid">
      <article className="panel stagger trend-wide">
        <div className="panel-head">
          <h3>New Tracked Players</h3>
          <span className="pill">SINCE VPS START</span>
        </div>
        <div className="chart-wrap">
          <ResponsiveContainer width="100%" height={280}>
            <ComposedChart data={ledgerAdds}>
              <CartesianGrid strokeDasharray="3 6" stroke="#d8d4c8" />
              <XAxis dataKey="day" tick={{ fontSize: 11 }} />
              <YAxis yAxisId="left" tick={{ fontSize: 11 }} />
              <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar
                yAxisId="left"
                dataKey="new_tracked_players"
                name="New tracked players"
                fill="#174f3f"
                radius={[3, 3, 0, 0]}
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="cumulative_tracked_players"
                name="Cumulative tracked players"
                stroke="#b64a32"
                strokeWidth={2.5}
                dot={false}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </article>

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
                  <stop offset="0%" stopColor="#b64a32" stopOpacity={0.36} />
                  <stop offset="100%" stopColor="#b64a32" stopOpacity={0.04} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 6" stroke="#d8d4c8" />
              <XAxis dataKey="month" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Area
                type="monotone"
                dataKey="players"
                stroke="#b64a32"
                strokeWidth={2}
                fill="url(#joinFill)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </article>

      <article className="panel stagger">
        <div className="panel-head">
          <h3>Recent Account Activity</h3>
          <span className="pill">60 DAYS</span>
        </div>
        <div className="chart-wrap">
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={discovery}>
              <CartesianGrid strokeDasharray="3 6" stroke="#d8d4c8" />
              <XAxis dataKey="day" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="new_signups"
                name="New signups"
                stroke="#174f3f"
                strokeWidth={2.5}
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="new_logins"
                name="New logins"
                stroke="#b64a32"
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

