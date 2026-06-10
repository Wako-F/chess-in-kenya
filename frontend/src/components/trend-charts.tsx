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
type LedgerGrowthPoint = {
  date?: string;
  tracked_players?: number;
  daily_added?: number;
  source?: string;
};

type TrendChartsProps = {
  joins: JoinPoint[];
  discovery: DiscoveryPoint[];
  ledgerGrowth: LedgerGrowthPoint[];
};

export function TrendCharts({ joins, discovery, ledgerGrowth }: TrendChartsProps) {
  return (
    <section className="charts-grid">
      <article className="panel stagger trend-wide">
        <div className="panel-head">
          <h3>Tracked Player Growth</h3>
          <span className="pill">PROJECT HISTORY</span>
        </div>
        <div className="chart-wrap">
          <ResponsiveContainer width="100%" height={280}>
            <ComposedChart data={ledgerGrowth}>
              <defs>
                <linearGradient id="ledgerFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#174f3f" stopOpacity={0.32} />
                  <stop offset="100%" stopColor="#174f3f" stopOpacity={0.04} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 6" stroke="#d8d4c8" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} minTickGap={34} />
              <YAxis yAxisId="left" tick={{ fontSize: 11 }} />
              <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar
                yAxisId="right"
                dataKey="daily_added"
                name="Daily added"
                fill="#c18b2f"
                opacity={0.36}
              />
              <Area
                yAxisId="left"
                type="monotone"
                dataKey="tracked_players"
                name="Tracked players"
                stroke="#174f3f"
                strokeWidth={2.5}
                fill="url(#ledgerFill)"
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

