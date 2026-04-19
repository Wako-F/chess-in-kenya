export default function Loading() {
  return (
    <main className="atlas-page">
      <section className="hero compact">
        <p className="eyebrow">Loading</p>
        <h1>Preparing Intelligence Surfaces...</h1>
        <p className="lead">Pulling the latest curated API views.</p>
      </section>
      <section className="metrics-grid">
        {Array.from({ length: 4 }).map((_, i) => (
          <article key={i} className="metric-card skeleton">
            <p className="metric-label"> </p>
            <p className="metric-value"> </p>
          </article>
        ))}
      </section>
    </main>
  );
}

