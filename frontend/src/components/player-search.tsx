"use client";

import { useState } from "react";
import Link from "next/link";

import type { Player } from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_CHESSKE_API_BASE ?? "http://127.0.0.1:8000";

export function PlayerSearch() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [player, setPlayer] = useState<Player | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function onSearch() {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    setPlayer(null);
    try {
      const res = await fetch(`${API_BASE}/players/${encodeURIComponent(query.toLowerCase())}`);
      if (!res.ok) {
        setError("Player not found in the current ledger.");
      } else {
        const data = (await res.json()) as Player;
        setPlayer(data);
      }
    } catch {
      setError("API unavailable. Start the backend API and retry.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="panel stagger">
      <div className="panel-head">
        <h3>Player Intelligence</h3>
        <span className="pill">LIVE LOOKUP</span>
      </div>
      <div className="search-row">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Type username, e.g. 0-216ie"
          onKeyDown={(e) => {
            if (e.key === "Enter") onSearch();
          }}
        />
        <button onClick={onSearch} disabled={loading}>
          {loading ? "Searching..." : "Search"}
        </button>
      </div>
      {error && <p className="status error">{error}</p>}
      {player && (
        <div className="player-grid">
          <div>
            <p className="k">Username</p>
            <p className="v">{player.username}</p>
          </div>
          <div>
            <p className="k">Rapid</p>
            <p className="v">{player.rapid_rating ?? 0}</p>
          </div>
          <div>
            <p className="k">Blitz</p>
            <p className="v">{player.blitz_rating ?? 0}</p>
          </div>
          <div>
            <p className="k">Bullet</p>
            <p className="v">{player.bullet_rating ?? 0}</p>
          </div>
          <div>
            <p className="k">Daily</p>
            <p className="v">{player.daily_rating ?? 0}</p>
          </div>
          <div>
            <p className="k">Puzzle</p>
            <p className="v">{player.highest_puzzle_rating ?? 0}</p>
          </div>
          <div>
            <p className="k">Total Games</p>
            <p className="v">{player.total_games?.toLocaleString() ?? 0}</p>
          </div>
          <div>
            <p className="k">Last Online</p>
            <p className="v">{player.last_online ? new Date(player.last_online).toLocaleString() : "N/A"}</p>
          </div>
          <div>
            <p className="k">Deep Profile</p>
            <p className="v">
              <Link href={`/player/${player.username}`} className="profile-link">
                Open player route
              </Link>
            </p>
          </div>
        </div>
      )}
    </section>
  );
}
