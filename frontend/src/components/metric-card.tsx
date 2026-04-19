type MetricCardProps = {
  label: string;
  value: string;
  accent?: "sun" | "jade" | "coral" | "ink";
};

export function MetricCard({ label, value, accent = "ink" }: MetricCardProps) {
  return (
    <article className={`metric-card accent-${accent}`}>
      <p className="metric-label">{label}</p>
      <p className="metric-value">{value}</p>
    </article>
  );
}

