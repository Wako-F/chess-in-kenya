from datetime import datetime, timedelta, timezone
import json
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from .db import utc_now_iso


def _iso_after(days: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def start_run(conn: Any, notes: str = "") -> int:
    cur = conn.execute(
        """
        INSERT INTO pipeline_runs (started_at, status, notes)
        VALUES (?, 'running', ?)
        RETURNING id
        """,
        (utc_now_iso(), notes),
    )
    row = cur.fetchone()
    conn.commit()
    if row is None:
        raise RuntimeError("Failed to start run: no id returned")
    return int(row["id"] if isinstance(row, dict) else row[0])


def finish_run(
    conn: Any,
    run_id: int,
    status: str,
    active_count: int,
    updated_count: int,
    deleted_count: int,
    refresh_count: int,
    error_count: int,
) -> None:
    conn.execute(
        """
        UPDATE pipeline_runs
        SET ended_at = ?, status = ?, active_count = ?, updated_count = ?,
            deleted_count = ?, refresh_count = ?, error_count = ?
        WHERE id = ?
        """,
        (
            utc_now_iso(),
            status,
            active_count,
            updated_count,
            deleted_count,
            refresh_count,
            error_count,
            run_id,
        ),
    )
    conn.commit()


def log_run_error(conn: Any, run_id: int, stage: str, error: str, username: Optional[str] = None) -> None:
    conn.execute(
        """
        INSERT INTO run_errors (run_id, username, stage, error, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (run_id, username, stage, error[:2000], utc_now_iso()),
    )
    conn.commit()


def upsert_active_snapshot(conn: Any, snapshot_date: str, usernames: Sequence[str]) -> None:
    inserted_at = utc_now_iso()
    conn.executemany(
        """
        INSERT INTO country_active_snapshots (snapshot_date, username, inserted_at)
        VALUES (?, ?, ?)
        ON CONFLICT (snapshot_date, username) DO NOTHING
        """,
        [(snapshot_date, u, inserted_at) for u in usernames],
    )
    conn.commit()


def upsert_user_and_stats(
    conn: Any,
    username: str,
    record: Dict,
    seen_in_active: bool,
    commit: bool = True,
) -> None:
    now = utc_now_iso()
    next_refresh_days = 7 if seen_in_active else 30
    next_refresh_at = _iso_after(next_refresh_days)

    conn.execute(
        """
        INSERT INTO users (username, joined_at, last_online, status, first_seen_at, last_seen_active_at, next_refresh_at, updated_at)
        VALUES (?, ?, ?, 'active', ?, ?, ?, ?)
        ON CONFLICT(username) DO UPDATE SET
            joined_at = COALESCE(excluded.joined_at, users.joined_at),
            last_online = COALESCE(excluded.last_online, users.last_online),
            status = 'active',
            last_seen_active_at = CASE WHEN ? THEN excluded.last_seen_active_at ELSE users.last_seen_active_at END,
            next_refresh_at = excluded.next_refresh_at,
            updated_at = excluded.updated_at
        """,
        (
            username,
            record.get("join_date"),
            record.get("last_online"),
            now,
            now if seen_in_active else None,
            next_refresh_at,
            now,
            1 if seen_in_active else 0,
        ),
    )

    conn.execute(
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
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
        ON CONFLICT(username) DO UPDATE SET
            total_games = excluded.total_games,
            total_daily = excluded.total_daily,
            total_rapid = excluded.total_rapid,
            total_bullet = excluded.total_bullet,
            total_blitz = excluded.total_blitz,
            daily_rating = excluded.daily_rating,
            rapid_rating = excluded.rapid_rating,
            bullet_rating = excluded.bullet_rating,
            blitz_rating = excluded.blitz_rating,
            highest_puzzle_rating = excluded.highest_puzzle_rating,
            highest_puzzle_date = excluded.highest_puzzle_date,
            daily_wins = excluded.daily_wins,
            daily_losses = excluded.daily_losses,
            daily_draws = excluded.daily_draws,
            rapid_wins = excluded.rapid_wins,
            rapid_losses = excluded.rapid_losses,
            rapid_draws = excluded.rapid_draws,
            bullet_wins = excluded.bullet_wins,
            bullet_losses = excluded.bullet_losses,
            bullet_draws = excluded.bullet_draws,
            blitz_wins = excluded.blitz_wins,
            blitz_losses = excluded.blitz_losses,
            blitz_draws = excluded.blitz_draws,
            updated_at = excluded.updated_at
        """,
        (
            username,
            int(record.get("total_games", 0) or 0),
            int(record.get("total_daily", 0) or 0),
            int(record.get("total_rapid", 0) or 0),
            int(record.get("total_bullet", 0) or 0),
            int(record.get("total_blitz", 0) or 0),
            int(record.get("daily_rating", 0) or 0),
            int(record.get("rapid_rating", 0) or 0),
            int(record.get("bullet_rating", 0) or 0),
            int(record.get("blitz_rating", 0) or 0),
            record.get("highest_puzzle_rating"),
            record.get("highest_puzzle_date"),
            int(record.get("daily_wins", 0) or 0),
            int(record.get("daily_losses", 0) or 0),
            int(record.get("daily_draws", 0) or 0),
            int(record.get("rapid_wins", 0) or 0),
            int(record.get("rapid_losses", 0) or 0),
            int(record.get("rapid_draws", 0) or 0),
            int(record.get("bullet_wins", 0) or 0),
            int(record.get("bullet_losses", 0) or 0),
            int(record.get("bullet_draws", 0) or 0),
            int(record.get("blitz_wins", 0) or 0),
            int(record.get("blitz_losses", 0) or 0),
            int(record.get("blitz_draws", 0) or 0),
            now,
        ),
    )
    if commit:
        conn.commit()


def mark_user_deleted(conn: Any, username: str, commit: bool = True) -> None:
    conn.execute(
        """
        UPDATE users
        SET status = 'deleted', next_refresh_at = NULL, updated_at = ?
        WHERE username = ?
        """,
        (utc_now_iso(), username),
    )
    if commit:
        conn.commit()


def get_refresh_candidates(conn: Any, snapshot_date: str, limit: int) -> List[str]:
    rows = conn.execute(
        """
        SELECT u.username
        FROM users u
        WHERE u.status = 'active'
          AND (u.next_refresh_at IS NULL OR u.next_refresh_at <= ?)
          AND NOT EXISTS (
              SELECT 1
              FROM country_active_snapshots s
              WHERE s.snapshot_date = ?
                AND s.username = u.username
          )
        ORDER BY COALESCE(u.last_online, '1970-01-01T00:00:00+00:00') DESC
        LIMIT ?
        """,
        (utc_now_iso(), snapshot_date, limit),
    ).fetchall()
    return [str(row["username"]) for row in rows]


def query_one(conn: Any, sql: str, params: Tuple = ()) -> Optional[Any]:
    row = conn.execute(sql, params).fetchone()
    return row


def query_all(conn: Any, sql: str, params: Tuple = ()) -> List[Any]:
    return conn.execute(sql, params).fetchall()


def get_cached_payload(conn: Any, cache_key: str) -> Optional[Dict[str, Any]]:
    row = conn.execute(
        """
        SELECT payload_json, updated_at, source
        FROM analytics_cache
        WHERE cache_key = ?
        """,
        (cache_key,),
    ).fetchone()
    if not row:
        return None
    payload = json.loads(row["payload_json"])
    return {
        "payload": payload,
        "updated_at": row["updated_at"],
        "source": row["source"],
    }


def upsert_cached_payload(
    conn: Any,
    cache_key: str,
    payload: Dict[str, Any],
    source: str,
    commit: bool = True,
) -> None:
    now = utc_now_iso()
    conn.execute(
        """
        INSERT INTO analytics_cache (cache_key, payload_json, updated_at, source)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(cache_key) DO UPDATE SET
            payload_json = excluded.payload_json,
            updated_at = excluded.updated_at,
            source = excluded.source
        """,
        (cache_key, json.dumps(payload), now, source),
    )
    if commit:
        conn.commit()
