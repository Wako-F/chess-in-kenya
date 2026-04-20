import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from .analytics import refresh_cached_analytics
from .client import ChessComClient
from .config import Settings
from .db import get_conn, init_db
from .repository import (
    finish_run,
    get_refresh_candidates,
    log_run_error,
    mark_user_deleted,
    start_run,
    upsert_active_snapshot,
    upsert_user_and_stats,
)


logger = logging.getLogger(__name__)


def _to_datetime_utc(timestamp: Optional[int]) -> Optional[str]:
    if not timestamp:
        return None
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()


def _extract_record_stats(stats: Dict, category: str):
    record = stats.get(category, {}).get("record", {})
    last = stats.get(category, {}).get("last", {})
    wins = int(record.get("win", 0) or 0)
    losses = int(record.get("loss", 0) or 0)
    draws = int(record.get("draw", 0) or 0)
    rating = int(last.get("rating", 0) or 0)
    total = wins + losses + draws
    return total, wins, losses, draws, rating


def _build_user_record(profile: Dict, stats: Dict) -> Dict:
    total_daily, daily_wins, daily_losses, daily_draws, daily_rating = _extract_record_stats(
        stats, "chess_daily"
    )
    total_rapid, rapid_wins, rapid_losses, rapid_draws, rapid_rating = _extract_record_stats(
        stats, "chess_rapid"
    )
    total_bullet, bullet_wins, bullet_losses, bullet_draws, bullet_rating = _extract_record_stats(
        stats, "chess_bullet"
    )
    total_blitz, blitz_wins, blitz_losses, blitz_draws, blitz_rating = _extract_record_stats(
        stats, "chess_blitz"
    )

    tactics = stats.get("tactics", {})
    highest_puzzle_rating = tactics.get("highest", {}).get("rating")
    highest_puzzle_date = _to_datetime_utc(tactics.get("highest", {}).get("date"))

    return {
        "join_date": _to_datetime_utc(profile.get("joined")),
        "last_online": _to_datetime_utc(profile.get("last_online")),
        "total_games": total_daily + total_rapid + total_bullet + total_blitz,
        "total_daily": total_daily,
        "total_rapid": total_rapid,
        "total_bullet": total_bullet,
        "total_blitz": total_blitz,
        "daily_rating": daily_rating,
        "rapid_rating": rapid_rating,
        "bullet_rating": bullet_rating,
        "blitz_rating": blitz_rating,
        "highest_puzzle_rating": highest_puzzle_rating,
        "highest_puzzle_date": highest_puzzle_date,
        "daily_wins": daily_wins,
        "daily_losses": daily_losses,
        "daily_draws": daily_draws,
        "rapid_wins": rapid_wins,
        "rapid_losses": rapid_losses,
        "rapid_draws": rapid_draws,
        "bullet_wins": bullet_wins,
        "bullet_losses": bullet_losses,
        "bullet_draws": bullet_draws,
        "blitz_wins": blitz_wins,
        "blitz_losses": blitz_losses,
        "blitz_draws": blitz_draws,
    }


def _process_username(
    client: ChessComClient,
    username: str,
) -> Tuple[str, Optional[Dict], Optional[str]]:
    profile_status, profile = client.fetch_profile(username)
    if profile_status == "not_found":
        return "deleted", None, None
    if profile_status != "ok" or profile is None:
        return "error", None, profile_status

    stats_status, stats = client.fetch_stats(username)
    if stats_status != "ok":
        # If stats fail but profile is valid, keep partial record with zero stats.
        stats = {}
    built = _build_user_record(profile, stats or {})
    return "ok", built, None


def run_ingestion_pipeline(settings: Settings) -> Dict[str, int]:
    init_db(settings)
    client = ChessComClient(settings)

    with get_conn(settings) as conn:
        run_id = start_run(conn, notes="rolling discovery + refresh")
        active_count = 0
        updated_count = 0
        deleted_count = 0
        refresh_count = 0
        error_count = 0

        try:
            active_usernames = client.fetch_active_country_players(settings.country_code)
            active_count = len(active_usernames)
            snapshot_date = datetime.now(timezone.utc).date().isoformat()
            upsert_active_snapshot(conn, snapshot_date, active_usernames)
            print(f"Active snapshot: {active_count} users for {settings.country_code}")

            conn.execute("BEGIN")
            for idx, username in enumerate(active_usernames, start=1):
                state, record, error_detail = _process_username(client, username)
                if state == "deleted":
                    mark_user_deleted(conn, username, commit=False)
                    deleted_count += 1
                elif state == "ok" and record:
                    upsert_user_and_stats(conn, username, record, seen_in_active=True, commit=False)
                    updated_count += 1
                else:
                    log_run_error(conn, run_id, "active_fetch", str(error_detail), username)
                    error_count += 1

                if idx % 200 == 0:
                    conn.commit()
                    conn.execute("BEGIN")
                if idx % 100 == 0:
                    print(f"Active progress: {idx}/{active_count}")
                time.sleep(settings.request_delay_seconds)
            conn.commit()

            refresh_candidates = get_refresh_candidates(
                conn,
                snapshot_date=snapshot_date,
                limit=settings.refresh_limit,
            )
            if refresh_candidates:
                print(f"Refresh queue: {len(refresh_candidates)} users")

            conn.execute("BEGIN")
            for idx, username in enumerate(refresh_candidates, start=1):
                state, record, error_detail = _process_username(client, username)
                if state == "deleted":
                    mark_user_deleted(conn, username, commit=False)
                    deleted_count += 1
                    refresh_count += 1
                elif state == "ok" and record:
                    upsert_user_and_stats(conn, username, record, seen_in_active=False, commit=False)
                    updated_count += 1
                    refresh_count += 1
                else:
                    log_run_error(conn, run_id, "refresh_fetch", str(error_detail), username)
                    error_count += 1

                if idx % 200 == 0:
                    conn.commit()
                    conn.execute("BEGIN")
                if idx % 100 == 0:
                    print(f"Refresh progress: {idx}/{len(refresh_candidates)}")
                time.sleep(settings.request_delay_seconds)
            conn.commit()

            finish_run(
                conn,
                run_id=run_id,
                status="success",
                active_count=active_count,
                updated_count=updated_count,
                deleted_count=deleted_count,
                refresh_count=refresh_count,
                error_count=error_count,
            )
            refresh_cached_analytics(settings, source=f"pipeline-run:{run_id}")
            return {
                "run_id": run_id,
                "active_count": active_count,
                "updated_count": updated_count,
                "deleted_count": deleted_count,
                "refresh_count": refresh_count,
                "error_count": error_count,
            }
        except KeyboardInterrupt:
            finish_run(
                conn,
                run_id=run_id,
                status="interrupted",
                active_count=active_count,
                updated_count=updated_count,
                deleted_count=deleted_count,
                refresh_count=refresh_count,
                error_count=error_count,
            )
            raise
        except Exception as exc:
            logger.exception("Pipeline failed")
            log_run_error(conn, run_id, "pipeline", str(exc))
            finish_run(
                conn,
                run_id=run_id,
                status="failed",
                active_count=active_count,
                updated_count=updated_count,
                deleted_count=deleted_count,
                refresh_count=refresh_count,
                error_count=error_count + 1,
            )
            raise
