import type { LeaderboardItem } from "@/lib/types";

type LeaderboardTableProps = {
  title: string;
  board: string;
  items: LeaderboardItem[];
};

export function LeaderboardTable({ title, board, items }: LeaderboardTableProps) {
  return (
    <section className="panel stagger">
      <div className="panel-head">
        <h3>{title}</h3>
        <span className="pill">{board.toUpperCase()}</span>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>Player</th>
              <th>Score</th>
              <th>Games</th>
            </tr>
          </thead>
          <tbody>
            {items.slice(0, 12).map((item, idx) => (
              <tr key={item.username}>
                <td>{idx + 1}</td>
                <td>{item.username}</td>
                <td>{item.score?.toLocaleString()}</td>
                <td>{item.games?.toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

