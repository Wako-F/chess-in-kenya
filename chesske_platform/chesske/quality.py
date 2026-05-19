from typing import Dict

from .config import Settings
from .db import get_conn, init_db


def compute_quality_report(settings: Settings) -> Dict[str, object]:
    if not settings.database_url:
        init_db(settings)
    with get_conn(settings) as conn:
        total_users = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
        active_users = conn.execute("SELECT COUNT(*) AS c FROM users WHERE status='active'").fetchone()["c"]
        deleted_users = conn.execute("SELECT COUNT(*) AS c FROM users WHERE status='deleted'").fetchone()["c"]
        stat_rows = conn.execute("SELECT COUNT(*) AS c FROM user_stats_latest").fetchone()["c"]
        missing_stats = conn.execute(
            """
            SELECT COUNT(*) AS c
            FROM users u
            LEFT JOIN user_stats_latest s ON s.username = u.username
            WHERE u.status='active' AND s.username IS NULL
            """
        ).fetchone()["c"]
        latest_snapshot = conn.execute(
            "SELECT MAX(snapshot_date) AS d FROM country_active_snapshots"
        ).fetchone()["d"]
        latest_run = conn.execute(
            """
            SELECT id, started_at, ended_at, status, active_count, updated_count, error_count
            FROM pipeline_runs
            ORDER BY id DESC LIMIT 1
            """
        ).fetchone()
        latest_snapshot_count = 0
        coverage_ratio = 0.0
        if latest_snapshot:
            latest_snapshot_count = conn.execute(
                "SELECT COUNT(*) AS c FROM country_active_snapshots WHERE snapshot_date = ?",
                (latest_snapshot,),
            ).fetchone()["c"]
            matched = conn.execute(
                """
                SELECT COUNT(*) AS c
                FROM country_active_snapshots a
                JOIN users u ON u.username = a.username AND u.status='active'
                WHERE a.snapshot_date = ?
                """,
                (latest_snapshot,),
            ).fetchone()["c"]
            coverage_ratio = (matched / latest_snapshot_count) if latest_snapshot_count else 0.0

    return {
        "total_users": int(total_users or 0),
        "active_users": int(active_users or 0),
        "deleted_users": int(deleted_users or 0),
        "stats_rows": int(stat_rows or 0),
        "missing_stats_for_active_users": int(missing_stats or 0),
        "latest_snapshot_date": latest_snapshot,
        "latest_snapshot_count": int(latest_snapshot_count or 0),
        "latest_active_coverage_ratio": round(float(coverage_ratio), 4),
        "latest_run": dict(latest_run) if latest_run else None,
    }

