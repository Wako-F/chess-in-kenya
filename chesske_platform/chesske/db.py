import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Optional, Sequence

import psycopg
from psycopg.rows import dict_row

from .config import Settings


SQLITE_SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS pipeline_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    username TEXT,
    stage TEXT NOT NULL,
    error TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES pipeline_runs(id) ON DELETE CASCADE
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
    username TEXT PRIMARY KEY,
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
    updated_at TEXT NOT NULL,
    FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS country_active_snapshots (
    snapshot_date TEXT NOT NULL,
    username TEXT NOT NULL,
    inserted_at TEXT NOT NULL,
    PRIMARY KEY (snapshot_date, username)
);

CREATE TABLE IF NOT EXISTS analytics_cache (
    cache_key TEXT PRIMARY KEY,
    payload_json TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    source TEXT
);

CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_users_next_refresh ON users(next_refresh_at);
CREATE INDEX IF NOT EXISTS idx_users_last_online ON users(last_online);
CREATE INDEX IF NOT EXISTS idx_active_snapshot_date ON country_active_snapshots(snapshot_date);
CREATE INDEX IF NOT EXISTS idx_stats_total_games ON user_stats_latest(total_games);
CREATE INDEX IF NOT EXISTS idx_stats_rapid_board ON user_stats_latest(rapid_rating DESC, total_rapid DESC);
CREATE INDEX IF NOT EXISTS idx_stats_blitz_board ON user_stats_latest(blitz_rating DESC, total_blitz DESC);
CREATE INDEX IF NOT EXISTS idx_stats_bullet_board ON user_stats_latest(bullet_rating DESC, total_bullet DESC);
CREATE INDEX IF NOT EXISTS idx_stats_daily_board ON user_stats_latest(daily_rating DESC, total_daily DESC);
CREATE INDEX IF NOT EXISTS idx_stats_puzzle_board ON user_stats_latest(highest_puzzle_rating DESC, total_games DESC);
"""


POSTGRES_SCHEMA_SQL = """
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

CREATE TABLE IF NOT EXISTS analytics_cache (
    cache_key TEXT PRIMARY KEY,
    payload_json TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    source TEXT
);

CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_users_next_refresh ON users(next_refresh_at);
CREATE INDEX IF NOT EXISTS idx_users_last_online ON users(last_online);
CREATE INDEX IF NOT EXISTS idx_active_snapshot_date ON country_active_snapshots(snapshot_date);
CREATE INDEX IF NOT EXISTS idx_stats_total_games ON user_stats_latest(total_games);
CREATE INDEX IF NOT EXISTS idx_stats_rapid_board ON user_stats_latest(rapid_rating DESC, total_rapid DESC);
CREATE INDEX IF NOT EXISTS idx_stats_blitz_board ON user_stats_latest(blitz_rating DESC, total_blitz DESC);
CREATE INDEX IF NOT EXISTS idx_stats_bullet_board ON user_stats_latest(bullet_rating DESC, total_bullet DESC);
CREATE INDEX IF NOT EXISTS idx_stats_daily_board ON user_stats_latest(daily_rating DESC, total_daily DESC);
CREATE INDEX IF NOT EXISTS idx_stats_puzzle_board ON user_stats_latest(highest_puzzle_rating DESC, total_games DESC);
"""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _to_postgres_placeholders(sql: str) -> str:
    return sql.replace("?", "%s")


class DBConn:
    def __init__(self, raw: Any, backend: str):
        self._raw = raw
        self.backend = backend

    def execute(self, sql: str, params: Sequence[Any] = ()) -> Any:
        if self.backend == "postgres":
            return self._raw.execute(_to_postgres_placeholders(sql), params)
        return self._raw.execute(sql, params)

    def executemany(self, sql: str, params_seq: Sequence[Sequence[Any]]) -> Any:
        if self.backend == "postgres":
            return self._raw.executemany(_to_postgres_placeholders(sql), params_seq)
        return self._raw.executemany(sql, params_seq)

    def executescript(self, sql: str) -> None:
        if self.backend == "postgres":
            statements = [stmt.strip() for stmt in sql.split(";") if stmt.strip()]
            for stmt in statements:
                self._raw.execute(stmt)
            return
        self._raw.executescript(sql)

    def commit(self) -> None:
        self._raw.commit()

    def rollback(self) -> None:
        self._raw.rollback()

    def close(self) -> None:
        self._raw.close()


def init_db(settings: Settings) -> None:
    if settings.database_url:
        with psycopg.connect(settings.database_url, autocommit=False, row_factory=dict_row) as conn:
            db = DBConn(conn, "postgres")
            db.executescript(POSTGRES_SCHEMA_SQL)
            db.commit()
        return

    db_path = settings.resolved_db_path
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        db = DBConn(conn, "sqlite")
        db.executescript(SQLITE_SCHEMA_SQL)
        db.commit()


@contextmanager
def get_conn(settings: Settings) -> Iterator[DBConn]:
    if settings.database_url:
        conn = psycopg.connect(settings.database_url, autocommit=False, row_factory=dict_row)
        db = DBConn(conn, "postgres")
    else:
        conn = sqlite3.connect(settings.resolved_db_path)
        conn.row_factory = sqlite3.Row
        db = DBConn(conn, "sqlite")

    try:
        yield db
    finally:
        db.close()
