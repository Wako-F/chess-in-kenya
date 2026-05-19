import { PlayerSearch } from "@/components/player-search";

export default function PlayerEntryPage() {
  return (
    <main id="main-content" className="atlas-page">
      <div className="atmosphere" aria-hidden />
      <section className="hero compact">
        <div className="hero-copy">
          <p className="eyebrow">Player route</p>
          <h1>Player Intelligence</h1>
          <p className="lead">
            Search a Chess.com username, verify the account belongs to Kenya, and refresh its local
            ratings profile in one pass.
          </p>
        </div>
      </section>
      <PlayerSearch />
    </main>
  );
}
