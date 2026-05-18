import Link from "next/link";

export default function NotFound() {
  return (
    <main id="main-content" className="atlas-page">
      <div className="atmosphere" aria-hidden />
      <section className="hero compact">
        <p className="eyebrow">404</p>
        <h1>Position not found</h1>
        <p className="lead">
          The resource you requested is not available in the current ledger state.
        </p>
        <p className="mono">
          <Link href="/">Return to atlas</Link>
        </p>
      </section>
    </main>
  );
}

