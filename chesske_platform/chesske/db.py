import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from .config import Settings


SCHEMA_SQL = """
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

CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_users_next_refresh ON users(next_refresh_at);
CREATE INDEX IF NOT EXISTS idx_users_last_online ON users(last_online);
CREATE INDEX IF NOT EXISTS idx_active_snapshot_date ON country_active_snapshots(snapshot_date);
"""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_db(settings: Settings) -> None:
    db_path = settings.resolved_db_path
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.executescript(SCHEMA_SQL)
        conn.commit()


@contextmanager
def get_conn(settings: Settings) -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(settings.resolved_db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

