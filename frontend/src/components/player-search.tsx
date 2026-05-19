"use client";

import { useState } from "react";
import Link from "next/link";

import type { Player } from "@/lib/types";

const configuredApiBase = process.env.NEXT_PUBLIC_CHESSKE_API_BASE ?? "";
const API_BASE = configuredApiBase.includes("chess-in-kenya.onrender.com")
  ? "/api"
  : configuredApiBase || "/api";

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
      const res = await fetch(`${API_BASE}/players/${encodeURIComponent(query.toLowerCase())}/lookup`);
      if (!res.ok) {
        const detail = await res.json().catch(() => null);
        setError(detail?.detail ?? "Player not found or not listed as Kenya on Chess.com.");
      } else {
        const data = (await res.json()) as Player;
        setPlayer(data);
      }
    } catch {
      setError("Live lookup unavailable. Retry in a moment.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="panel stagger">
      <div className="panel-head">
        <h3>Player Intelligence</h3>
        <span className="pill">LIVE CHESS.COM LOOKUP</span>
      </div>
      <p className="status">
        Searches Chess.com directly, verifies the account is listed under Kenya, then refreshes the local ledger.
      </p>
      <div className="search-row">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Type username, e.g. atem_n"
          onKeyDown={(e) => {
            if (e.key === "Enter") onSearch();
          }}
        />
        <button onClick={onSearch} disabled={loading}>
          {loading ? "Checking..." : "Live Search"}
        </button>
      </div>
      {error && <p className="status error">{error}</p>}
      {player && <PlayerLookupCard player={player} />}
    </section>
  );
}

function fmt(n: number | null | undefined) {
  return (n ?? 0).toLocaleString();
}

function date(v: string | null | undefined) {
  return v ? new Date(v).toLocaleString() : "Unknown";
}

function winRate(wins = 0, losses = 0, draws = 0) {
  const total = wins + losses + draws;
  if (!total) return "0.0%";
  return `${((wins / total) * 100).toFixed(1)}%`;
}

function formatRows(player: Player) {
  return [
    {
      key: "Rapid",
      rating: player.rapid_rating,
      games: player.total_rapid,
      wins: player.rapid_wins ?? 0,
      losses: player.rapid_losses ?? 0,
      draws: player.rapid_draws ?? 0,
    },
    {
      key: "Blitz",
      rating: player.blitz_rating,
      games: player.total_blitz,
      wins: player.blitz_wins ?? 0,
      losses: player.blitz_losses ?? 0,
      draws: player.blitz_draws ?? 0,
    },
    {
      key: "Bullet",
      rating: player.bullet_rating,
      games: player.total_bullet,
      wins: player.bullet_wins ?? 0,
      losses: player.bullet_losses ?? 0,
      draws: player.bullet_draws ?? 0,
    },
    {
      key: "Daily",
      rating: player.daily_rating,
      games: player.total_daily,
      wins: player.daily_wins ?? 0,
      losses: player.daily_losses ?? 0,
      draws: player.daily_draws ?? 0,
    },
  ];
}

function PlayerLookupCard({ player }: { player: Player }) {
  const rows = formatRows(player);
  const topFormat = rows.reduce((best, row) => (row.rating > best.rating ? row : best), rows[0]);

  return (
    <div className="lookup-card">
      <div className="lookup-hero">
        <div className="avatar-frame">
          {player.avatar ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={player.avatar} alt="" />
          ) : (
            <span>{player.username.slice(0, 2).toUpperCase()}</span>
          )}
        </div>
        <div>
          <p className="route-eyebrow">Verified Kenya account</p>
          <h4>{player.username}</h4>
          <div className="run-meta">
            <span className="pill">{player.lookup_country ?? "KE"}</span>
            <span className="pill">{player.lookup_refreshed ? "Refreshed now" : "Ledger"}</span>
            <span className="mono">Last online {date(player.last_online)}</span>
          </div>
        </div>
      </div>

      <div className="lookup-metrics">
        <div>
          <p className="k">Total Games</p>
          <p className="v">{fmt(player.total_games)}</p>
        </div>
        <div>
          <p className="k">Best Format</p>
          <p className="v">
            {topFormat.key} {fmt(topFormat.rating)}
          </p>
        </div>
        <div>
          <p className="k">Puzzle Peak</p>
          <p className="v">{fmt(player.highest_puzzle_rating)}</p>
        </div>
        <div>
          <p className="k">Ledger Updated</p>
          <p className="v small">{date(player.ledger_updated_at)}</p>
        </div>
      </div>

      <div className="format-table">
        {rows.map((row) => (
          <div key={row.key} className="format-row">
            <strong>{row.key}</strong>
            <span>{fmt(row.rating)} rating</span>
            <span>{fmt(row.games)} games</span>
            <span>{winRate(row.wins, row.losses, row.draws)} win</span>
          </div>
        ))}
      </div>

      <div className="lookup-actions">
        <Link href={`/player/${player.username}`} className="profile-link">
          Open deep profile
        </Link>
        {player.profile_url && (
          <a href={player.profile_url} target="_blank" rel="noreferrer" className="profile-link">
            Chess.com profile
          </a>
        )}
      </div>
    </div>
  );
}
