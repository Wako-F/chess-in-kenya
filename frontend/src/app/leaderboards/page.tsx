import { LeaderboardTable } from "@/components/leaderboard-table";
import { LeaderboardMarvel } from "@/components/leaderboard-marvel";
import { getLeaderboard } from "@/lib/api";

export const revalidate = 300;

const boards = [
  { key: "rapid", title: "Rapid Commanders" },
  { key: "blitz", title: "Blitz Specialists" },
  { key: "bullet", title: "Bullet Sharpshooters" },
  { key: "daily", title: "Daily Strategists" },
  { key: "puzzle", title: "Puzzle Engineers" },
  { key: "games", title: "Volume Titans" },
];

export default async function LeaderboardsPage() {
  const data = await Promise.all(boards.map((b) => getLeaderboard(b.key, 15)));
  const summary = boards.map((board, idx) => {
    const items = data[idx]?.items ?? [];
    const topScore = items[0]?.score ?? 0;
    const avgTopScore = items.length
      ? items.reduce((acc, cur) => acc + (cur.score ?? 0), 0) / items.length
      : 0;
    return { board: board.key, topScore, avgTopScore };
  }).filter((row) => row.board !== "games");

  return (
    <main id="main-content" className="atlas-page">
      <div className="atmosphere" aria-hidden />
      <section className="hero compact">
        <div className="hero-copy">
          <p className="eyebrow">Competitive index</p>
          <h1>Leaderboards</h1>
          <p className="lead">
            Multi-format ranking surfaces for quickly understanding where strength, activity,
            and tactical performance concentrate in the Kenyan ecosystem.
          </p>
        </div>
      </section>

      <LeaderboardMarvel summary={summary} />

      <section className="board-stack">
        {boards.map((board, idx) => (
          <LeaderboardTable
            key={board.key}
            title={board.title}
            board={board.key}
            items={data[idx]?.items ?? []}
          />
        ))}
      </section>
    </main>
  );
}
