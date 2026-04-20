import argparse
import os
from datetime import datetime, timezone
from typing import Optional

import psycopg

from chesske_platform.chesske.analytics import refresh_cached_analytics
from chesske_platform.chesske.config import Settings
from chesske_platform.scripts.bootstrap_from_master_csv import _iter_clean_chunks, _to_iso

import pandas as pd


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id BIGSERIAL PRIMARY KEY,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    status TEXT NOT NULL,
    active_count INTEGER NOT NULL DEFAULT 0,
    updated_count INTEGER NOT NULL DEFAULT 0,
    deleted_count INTEGER NOT NULL DEFAULT 0,
    refresh_count INTEGER NOT NULL DEFAULT 0,
    error_count INTEGER NOT NULL DEFAULT 0,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS run_errors (
    id BIGSERIAL PRIMARY KEY,
    run_id BIGINT NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
    username TEXT,
    stage TEXT NOT NULL,
    error TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    joined_at TEXT,
    last_online TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    first_seen_at TEXT NOT NULL,
    last_seen_active_at TEXT,
    next_refresh_at TEXT,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS user_stats_latest (
    username TEXT PRIMARY KEY REFERENCES users(username) ON DELETE CASCADE,
    total_games INTEGER NOT NULL DEFAULT 0,
    total_daily INTEGER NOT NULL DEFAULT 0,
    total_rapid INTEGER NOT NULL DEFAULT 0,
    total_bullet INTEGER NOT NULL DEFAULT 0,
    total_blitz INTEGER NOT NULL DEFAULT 0,
    daily_rating INTEGER NOT NULL DEFAULT 0,
    rapid_rating INTEGER NOT NULL DEFAULT 0,
    bullet_rating INTEGER NOT NULL DEFAULT 0,
    blitz_rating INTEGER NOT NULL DEFAULT 0,
    highest_puzzle_rating INTEGER,
    highest_puzzle_date TEXT,
    daily_wins INTEGER NOT NULL DEFAULT 0,
    daily_losses INTEGER NOT NULL DEFAULT 0,
    daily_draws INTEGER NOT NULL DEFAULT 0,
    rapid_wins INTEGER NOT NULL DEFAULT 0,
    rapid_losses INTEGER NOT NULL DEFAULT 0,
    rapid_draws INTEGER NOT NULL DEFAULT 0,
    bullet_wins INTEGER NOT NULL DEFAULT 0,
    bullet_losses INTEGER NOT NULL DEFAULT 0,
    bullet_draws INTEGER NOT NULL DEFAULT 0,
    blitz_wins INTEGER NOT NULL DEFAULT 0,
    blitz_losses INTEGER NOT NULL DEFAULT 0,
    blitz_draws INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS country_active_snapshots (
    snapshot_date TEXT NOT NULL,
    username TEXT NOT NULL,
    inserted_at TEXT NOT NULL,
    PRIMARY KEY (snapshot_date, username)
);

CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_users_next_refresh ON users(next_refresh_at);
CREATE INDEX IF NOT EXISTS idx_users_last_online ON users(last_online);
CREATE INDEX IF NOT EXISTS idx_active_snapshot_date ON country_active_snapshots(snapshot_date);
"""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _to_int(value: object) -> int:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return 0
    try:
        return int(value)
    except Exception:
        return 0


def bootstrap_postgres(database_url: str, csv_path: str, limit: Optional[int], reset: bool) -> int:
    loaded = 0
    with psycopg.connect(database_url, autocommit=False) as conn:
        with conn.cursor() as cur:
            cur.execute(SCHEMA_SQL)
            if reset:
                cur.execute("TRUNCATE run_errors, pipeline_runs, country_active_snapshots, user_stats_latest, users")

            now = _utc_now_iso()
            for idx, chunk in enumerate(_iter_clean_chunks(csv_path, limit, chunk_size=2000), start=1):
                users_payload = []
                stats_payload = []
                for row in chunk.itertuples(index=False):
                    username = str(getattr(row, "username"))
                    joined_at = _to_iso(getattr(row, "join_date", None))
                    last_online = _to_iso(getattr(row, "last_online", None))
                    users_payload.append(
                        (
                            username,
                            joined_at,
                            last_online,
                            "active",
                            now,
                            None,
                            None,
                            now,
                        )
                    )
                    stats_payload.append(
                        (
                            username,
                            _to_int(getattr(row, "total_games", 0)),
                            _to_int(getattr(row, "total_daily", 0)),
                            _to_int(getattr(row, "total_rapid", 0)),
                            _to_int(getattr(row, "total_bullet", 0)),
                            _to_int(getattr(row, "total_blitz", 0)),
                            _to_int(getattr(row, "daily_rating", 0)),
                            _to_int(getattr(row, "rapid_rating", 0)),
                            _to_int(getattr(row, "bullet_rating", 0)),
                            _to_int(getattr(row, "blitz_rating", 0)),
                            _to_int(getattr(row, "highest_puzzle_rating", 0)),
                            _to_iso(getattr(row, "highest_puzzle_date", None)),
                            _to_int(getattr(row, "daily_wins", 0)),
                            _to_int(getattr(row, "daily_losses", 0)),
                            _to_int(getattr(row, "daily_draws", 0)),
                            _to_int(getattr(row, "rapid_wins", 0)),
                            _to_int(getattr(row, "rapid_losses", 0)),
                            _to_int(getattr(row, "rapid_draws", 0)),
                            _to_int(getattr(row, "bullet_wins", 0)),
                            _to_int(getattr(row, "bullet_losses", 0)),
                            _to_int(getattr(row, "bullet_draws", 0)),
                            _to_int(getattr(row, "blitz_wins", 0)),
                            _to_int(getattr(row, "blitz_losses", 0)),
                            _to_int(getattr(row, "blitz_draws", 0)),
                            now,
                        )
                    )

                cur.executemany(
                    """
                    INSERT INTO users (username, joined_at, last_online, status, first_seen_at, last_seen_active_at, next_refresh_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (username) DO UPDATE SET
                        joined_at = COALESCE(EXCLUDED.joined_at, users.joined_at),
                        last_online = COALESCE(EXCLUDED.last_online, users.last_online),
                        status = 'active',
                        updated_at = EXCLUDED.updated_at
                    """,
                    users_payload,
                )
                cur.executemany(
                    """
                    INSERT INTO user_stats_latest (
                        username, total_games, total_daily, total_rapid, total_bullet, total_blitz,
                        daily_rating, rapid_rating, bullet_rating, blitz_rating,
                        highest_puzzle_rating, highest_puzzle_date,
                        daily_wins, daily_losses, daily_draws,
                        rapid_wins, rapid_losses, rapid_draws,
                        bullet_wins, bullet_losses, bullet_draws,
                        blitz_wins, blitz_losses, blitz_draws, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (username) DO UPDATE SET
                        total_games = EXCLUDED.total_games,
                        total_daily = EXCLUDED.total_daily,
                        total_rapid = EXCLUDED.total_rapid,
                        total_bullet = EXCLUDED.total_bullet,
                        total_blitz = EXCLUDED.total_blitz,
                        daily_rating = EXCLUDED.daily_rating,
                        rapid_rating = EXCLUDED.rapid_rating,
                        bullet_rating = EXCLUDED.bullet_rating,
                        blitz_rating = EXCLUDED.blitz_rating,
                        highest_puzzle_rating = EXCLUDED.highest_puzzle_rating,
                        highest_puzzle_date = EXCLUDED.highest_puzzle_date,
                        daily_wins = EXCLUDED.daily_wins,
                        daily_losses = EXCLUDED.daily_losses,
                        daily_draws = EXCLUDED.daily_draws,
                        rapid_wins = EXCLUDED.rapid_wins,
                        rapid_losses = EXCLUDED.rapid_losses,
                        rapid_draws = EXCLUDED.rapid_draws,
                        bullet_wins = EXCLUDED.bullet_wins,
                        bullet_losses = EXCLUDED.bullet_losses,
                        bullet_draws = EXCLUDED.bullet_draws,
                        blitz_wins = EXCLUDED.blitz_wins,
                        blitz_losses = EXCLUDED.blitz_losses,
                        blitz_draws = EXCLUDED.blitz_draws,
                        updated_at = EXCLUDED.updated_at
                    """,
                    stats_payload,
                )
                conn.commit()
                loaded += len(chunk)
                if idx % 5 == 0:
                    print(f"Processed {loaded} rows")

            snapshot_date = datetime.now(timezone.utc).date().isoformat()
            inserted_at = _utc_now_iso()
            cur.execute(
                """
                INSERT INTO country_active_snapshots (snapshot_date, username, inserted_at)
                SELECT %s, username, %s
                FROM users
                WHERE status='active'
                ON CONFLICT DO NOTHING
                """,
                (snapshot_date, inserted_at),
            )
            cur.execute("SELECT COUNT(*) FROM users WHERE status='active'")
            active_users = int(cur.fetchone()[0])
            cur.execute(
                """
                INSERT INTO pipeline_runs (
                    started_at, ended_at, status, active_count, updated_count,
                    deleted_count, refresh_count, error_count, notes
                ) VALUES (%s, %s, 'success', %s, %s, 0, 0, 0, %s)
                """,
                (
                    _utc_now_iso(),
                    _utc_now_iso(),
                    active_users,
                    loaded,
                    f"bootstrap_postgres_from_csv:{csv_path}",
                ),
            )
            conn.commit()
    refresh_cached_analytics(Settings(database_url=database_url), source=f"bootstrap-postgres:{os.path.basename(csv_path)}")
    return loaded


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap Aiven/Postgres from master CSV.")
    parser.add_argument("--csv", default=os.getenv("CHESSKE_BOOTSTRAP_CSV", "cleaned_master_chess_players.csv"))
    parser.add_argument("--limit", type=int, default=int(os.getenv("CHESSKE_BOOTSTRAP_LIMIT", "0")))
    parser.add_argument("--reset", action="store_true", help="Truncate core tables before import.")
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL", ""))
    args = parser.parse_args()

    if not args.database_url:
        raise SystemExit("DATABASE_URL is required (argument or environment variable).")

    loaded = bootstrap_postgres(
        database_url=args.database_url,
        csv_path=args.csv,
        limit=(args.limit if args.limit > 0 else None),
        reset=args.reset,
    )
    print(f"Postgres bootstrap complete: loaded {loaded} users")


if __name__ == "__main__":
    main()
