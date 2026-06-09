import os
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List, Literal, Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .analytics import (
    build_analytics_pack_payload,
    build_cohort_retention_payload,
    build_correlation_matrix_payload,
    build_percentile_bands_payload,
    build_player_benchmark_payload,
    build_story_report_payload,
    get_or_build_cached_payload,
)
from .cache import cached_json, delete_by_pattern
from .client import ChessComClient
from .config import Settings
from .db import get_conn, init_db
from .pipeline import _build_user_record
from .quality import compute_quality_report
from .repository import query_all, query_one, upsert_user_and_stats


def _env_enabled(name: str, default: bool = True) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() not in {"0", "false", "no", "off"}


def _resolve_bootstrap_csv(settings: Settings) -> Optional[Path]:
    configured = os.getenv("CHESSKE_BOOTSTRAP_CSV", "").strip()
    candidates = [configured] if configured else []
    candidates.extend(["cleaned_master_chess_players.csv", "master_chess_players.csv"])
    for candidate in candidates:
        p = Path(candidate)
        if not p.is_absolute():
            p = settings.base_dir / p
        if p.exists():
            return p
    return None


def _profile_country_code(profile: Dict[str, object]) -> str:
    country = str(profile.get("country") or "").rstrip("/")
    if not country:
        return ""
    return country.rsplit("/", 1)[-1].upper()


def _player_payload(conn, username: str) -> Optional[Dict[str, object]]:
    row = query_one(
        conn,
        """
        SELECT
            u.username, u.joined_at, u.last_online, u.status, u.first_seen_at, u.last_seen_active_at,
            u.next_refresh_at, u.updated_at AS ledger_updated_at,
            s.*
        FROM users u
        LEFT JOIN user_stats_latest s ON s.username = u.username
        WHERE u.username = ?
        """,
        (username,),
    )
    return dict(row) if row else None


def create_app(settings: Optional[Settings] = None) -> FastAPI:
    settings = settings or Settings()
    if not settings.database_url or _env_enabled("CHESSKE_API_INIT_DB", default=False):
        init_db(settings)
    app = FastAPI(title="ChessKE Data API", version="1.0.0")

    cors_origins = os.getenv("CHESSKE_CORS_ORIGINS", "*").strip()
    if cors_origins == "*":
        allow_origins = ["*"]
    else:
        allow_origins = [o.strip() for o in cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def start_bootstrap_if_empty() -> None:
        if not _env_enabled("CHESSKE_AUTO_BOOTSTRAP", default=True):
            return
        min_users_raw = os.getenv("CHESSKE_BOOTSTRAP_MIN_USERS", "1").strip()
        min_users = int(min_users_raw) if min_users_raw.isdigit() else 1
        with get_conn(settings) as conn:
            row = query_one(conn, "SELECT COUNT(*) AS n FROM users")
        current_users = int(row["n"] or 0) if row else 0
        if current_users > min_users:
            return
        csv_path = _resolve_bootstrap_csv(settings)
        if not csv_path:
            print("[chesske] Auto-bootstrap skipped: no CSV found.")
            return

        limit_raw = os.getenv("CHESSKE_BOOTSTRAP_LIMIT", "0").strip()
        limit = int(limit_raw) if limit_raw.isdigit() and int(limit_raw) > 0 else None

        def worker() -> None:
            try:
                from chesske_platform.scripts.bootstrap_from_master_csv import bootstrap_from_csv

                print(
                    f"[chesske] Auto-bootstrap started from {csv_path} "
                    f"(users={current_users}, min_users={min_users})"
                )
                loaded = bootstrap_from_csv(settings, csv_path=str(csv_path), reset_db=False, limit=limit)
                print(f"[chesske] Auto-bootstrap complete: loaded {loaded} users")
            except Exception as exc:
                print(f"[chesske] Auto-bootstrap failed: {exc}")

        threading.Thread(target=worker, daemon=True, name="chesske-auto-bootstrap").start()

    @app.get("/health")
    def health() -> Dict[str, str]:
        return {"status": "ok"}

    @app.get("/meta/quality")
    def quality() -> Dict[str, object]:
        return cached_json(settings, "api:meta:quality", 300, lambda: compute_quality_report(settings))

    @app.get("/meta/runs")
    def runs(limit: int = Query(default=20, ge=1, le=200)) -> Dict[str, List[Dict[str, object]]]:
        with get_conn(settings) as conn:
            rows = query_all(
                conn,
                """
                SELECT id, started_at, ended_at, status, active_count, updated_count, deleted_count, refresh_count, error_count
                FROM pipeline_runs
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            )
        return {"items": [dict(r) for r in rows]}

    @app.get("/meta/errors")
    def errors(limit: int = Query(default=50, ge=1, le=500)) -> Dict[str, List[Dict[str, object]]]:
        with get_conn(settings) as conn:
            rows = query_all(
                conn,
                """
                SELECT e.id, e.run_id, e.username, e.stage, e.error, e.created_at
                FROM run_errors e
                ORDER BY e.id DESC
                LIMIT ?
                """,
                (limit,),
            )
        return {"items": [dict(r) for r in rows]}

    @app.get("/overview")
    def overview() -> Dict[str, object]:
        def build() -> Dict[str, object]:
            with get_conn(settings) as conn:
                row = query_one(
                    conn,
                    """
                    SELECT
                        COUNT(*) AS total_players,
                        SUM(COALESCE(s.total_games, 0)) AS total_games,
                        AVG(CASE WHEN s.rapid_rating > 0 THEN s.rapid_rating END) AS avg_rapid,
                        AVG(CASE WHEN s.blitz_rating > 0 THEN s.blitz_rating END) AS avg_blitz,
                        AVG(CASE WHEN s.bullet_rating > 0 THEN s.bullet_rating END) AS avg_bullet,
                        AVG(CASE WHEN s.daily_rating > 0 THEN s.daily_rating END) AS avg_daily,
                        AVG(CASE WHEN s.highest_puzzle_rating > 0 THEN s.highest_puzzle_rating END) AS avg_puzzle
                    FROM users u
                    LEFT JOIN user_stats_latest s ON s.username = u.username
                    WHERE u.status = 'active'
                    """,
                )
                latest_run = query_one(
                    conn,
                    """
                    SELECT id, started_at, ended_at, status, active_count, updated_count, error_count
                    FROM pipeline_runs
                    ORDER BY id DESC LIMIT 1
                    """,
                )
            return {
                "total_players": int(row["total_players"] or 0),
                "total_games": int(row["total_games"] or 0),
                "average_ratings": {
                    "rapid": round(float(row["avg_rapid"]), 2) if row["avg_rapid"] is not None else None,
                    "blitz": round(float(row["avg_blitz"]), 2) if row["avg_blitz"] is not None else None,
                    "bullet": round(float(row["avg_bullet"]), 2) if row["avg_bullet"] is not None else None,
                    "daily": round(float(row["avg_daily"]), 2) if row["avg_daily"] is not None else None,
                    "puzzle": round(float(row["avg_puzzle"]), 2) if row["avg_puzzle"] is not None else None,
                },
                "latest_run": dict(latest_run) if latest_run else None,
            }

        return cached_json(settings, "api:overview", 120, build)

    @app.get("/leaderboards/{board}")
    def leaderboards(
        board: Literal["rapid", "blitz", "bullet", "daily", "puzzle", "games"],
        limit: int = Query(default=20, ge=1, le=200),
        min_games: int = Query(default=50, ge=0),
    ) -> Dict[str, object]:
        mapping = {
            "rapid": ("s.rapid_rating", "s.total_rapid"),
            "blitz": ("s.blitz_rating", "s.total_blitz"),
            "bullet": ("s.bullet_rating", "s.total_bullet"),
            "daily": ("s.daily_rating", "s.total_daily"),
            "puzzle": ("s.highest_puzzle_rating", "s.total_games"),
            "games": ("s.total_games", "s.total_games"),
        }
        rating_col, games_col = mapping[board]

        sql = f"""
            SELECT
                u.username,
                {rating_col} AS score,
                {games_col} AS games,
                s.rapid_rating, s.blitz_rating, s.bullet_rating, s.daily_rating,
                s.highest_puzzle_rating, s.total_games
            FROM users u
            JOIN user_stats_latest s ON s.username = u.username
            WHERE u.status = 'active'
              AND COALESCE({rating_col}, 0) > 0
              AND COALESCE({games_col}, 0) >= ?
            ORDER BY score DESC
            LIMIT ?
        """

        def build() -> Dict[str, object]:
            with get_conn(settings) as conn:
                rows = query_all(conn, sql, (min_games, limit))
            return {"board": board, "items": [dict(r) for r in rows]}

        return cached_json(settings, f"api:leaderboards:{board}:{limit}:{min_games}", 300, build)

    @app.get("/players/{username}")
    def player_detail(username: str) -> Dict[str, object]:
        normalized = username.strip().lower()
        with get_conn(settings) as conn:
            payload = _player_payload(conn, normalized)
        if not payload:
            raise HTTPException(status_code=404, detail="Player not found")
        return payload

    @app.get("/players/{username}/lookup")
    def player_live_lookup(username: str) -> Dict[str, object]:
        normalized = username.strip().lower()
        if not normalized:
            raise HTTPException(status_code=400, detail="Username is required")

        def build() -> Dict[str, object]:
            client = ChessComClient(settings)
            with ThreadPoolExecutor(max_workers=2) as executor:
                profile_future = executor.submit(client.fetch_profile, normalized)
                stats_future = executor.submit(client.fetch_stats, normalized)
                profile_status, profile = profile_future.result()
                stats_status, stats = stats_future.result()

            if profile_status == "not_found":
                raise HTTPException(status_code=404, detail="Chess.com player not found")
            if profile_status != "ok" or not profile:
                raise HTTPException(status_code=502, detail=f"Chess.com profile fetch failed: {profile_status}")

            country_code = _profile_country_code(profile)
            if country_code != settings.country_code.upper():
                raise HTTPException(
                    status_code=404,
                    detail=f"Player is listed under {country_code or 'unknown country'}, not {settings.country_code.upper()}",
                )

            canonical_username = str(profile.get("username") or normalized).strip().lower()
            if canonical_username != normalized:
                stats_status, stats = client.fetch_stats(canonical_username)
            if stats_status not in {"ok", "not_found"}:
                raise HTTPException(status_code=502, detail=f"Chess.com stats fetch failed: {stats_status}")

            record = _build_user_record(profile, stats or {})
            with get_conn(settings) as conn:
                upsert_user_and_stats(conn, canonical_username, record, seen_in_active=False)
                payload = _player_payload(conn, canonical_username)

            delete_by_pattern(settings, "api:home*")
            delete_by_pattern(settings, "api:overview*")
            delete_by_pattern(settings, "api:leaderboards:*")
            delete_by_pattern(settings, "api:trends:*")

            if not payload:
                raise HTTPException(status_code=500, detail="Player refreshed but could not be read back")

            payload.update(
                {
                    "lookup_source": "chess.com-live",
                    "lookup_country": country_code,
                    "lookup_refreshed": True,
                    "profile_url": profile.get("url"),
                    "avatar": profile.get("avatar"),
                }
            )
            return payload

        return cached_json(settings, f"api:player-lookup:{normalized}", 300, build)

    @app.get("/trends/joins")
    def joins_trend(months: int = Query(default=48, ge=1, le=240)) -> Dict[str, List[Dict[str, object]]]:
        def build() -> Dict[str, List[Dict[str, object]]]:
            with get_conn(settings) as conn:
                rows = query_all(
                    conn,
                    """
                    SELECT SUBSTR(joined_at, 1, 7) AS month, COUNT(*) AS players
                    FROM users
                    WHERE status='active' AND joined_at IS NOT NULL
                    GROUP BY month
                    ORDER BY month DESC
                    LIMIT ?
                    """,
                    (months,),
                )
            data = [dict(r) for r in reversed(rows)]
            return {"items": data}

        return cached_json(settings, f"api:trends:joins:{months}", 300, build)

    @app.get("/trends/discovery")
    def discovery_trend(days: int = Query(default=60, ge=1, le=365)) -> Dict[str, List[Dict[str, object]]]:
        def build() -> Dict[str, List[Dict[str, object]]]:
            cutoff_date = (pd.Timestamp.utcnow() - pd.Timedelta(days=days)).date().isoformat()
            with get_conn(settings) as conn:
                signup_rows = query_all(
                    conn,
                    """
                    SELECT SUBSTR(joined_at, 1, 10) AS day, COUNT(*) AS new_signups
                    FROM users
                    WHERE status='active' AND joined_at IS NOT NULL AND SUBSTR(joined_at, 1, 10) >= ?
                    GROUP BY day
                    """,
                    (cutoff_date,),
                )
                login_rows = query_all(
                    conn,
                    """
                    SELECT SUBSTR(last_online, 1, 10) AS day, COUNT(*) AS new_logins
                    FROM users
                    WHERE status='active' AND last_online IS NOT NULL AND SUBSTR(last_online, 1, 10) >= ?
                    GROUP BY day
                    """,
                    (cutoff_date,),
                )

            by_day: Dict[str, Dict[str, object]] = {}
            for row in signup_rows:
                day = str(row["day"])
                by_day.setdefault(day, {"day": day, "new_signups": 0, "new_logins": 0})
                by_day[day]["new_signups"] = int(row["new_signups"] or 0)
            for row in login_rows:
                day = str(row["day"])
                by_day.setdefault(day, {"day": day, "new_signups": 0, "new_logins": 0})
                by_day[day]["new_logins"] = int(row["new_logins"] or 0)

            today = pd.Timestamp.utcnow().date()
            days_index = pd.date_range(start=cutoff_date, end=today, freq="D")
            items = []
            for day_ts in days_index:
                day = day_ts.date().isoformat()
                items.append(by_day.get(day, {"day": day, "new_signups": 0, "new_logins": 0}))
            return {"items": items}

        return cached_json(settings, f"api:trends:discovery:{days}", 300, build)

    @app.get("/trends/ledger-adds")
    def ledger_adds_trend(
        start: str = Query(default="2026-05-18", pattern=r"^\d{4}-\d{2}-\d{2}$"),
    ) -> Dict[str, List[Dict[str, object]]]:
        def build() -> Dict[str, List[Dict[str, object]]]:
            today = pd.Timestamp.utcnow().date()
            start_date = pd.to_datetime(start, errors="coerce", utc=True)
            if pd.isna(start_date):
                raise HTTPException(status_code=400, detail="start must be YYYY-MM-DD")
            cutoff_date = start_date.date().isoformat()

            with get_conn(settings) as conn:
                rows = query_all(
                    conn,
                    """
                    SELECT SUBSTR(first_seen_at, 1, 10) AS day, COUNT(*) AS new_tracked_players
                    FROM users
                    WHERE status='active'
                      AND first_seen_at IS NOT NULL
                      AND SUBSTR(first_seen_at, 1, 10) >= ?
                    GROUP BY day
                    """,
                    (cutoff_date,),
                )
                baseline_row = query_one(
                    conn,
                    """
                    SELECT COUNT(*) AS players
                    FROM users
                    WHERE status='active'
                      AND first_seen_at IS NOT NULL
                      AND SUBSTR(first_seen_at, 1, 10) < ?
                    """,
                    (cutoff_date,),
                )

            by_day = {str(row["day"]): int(row["new_tracked_players"] or 0) for row in rows}
            # CSV/Postgres reboots reset first_seen_at; keep the VPS bootstrap cohort anchored.
            if cutoff_date not in by_day and len(by_day) == 1:
                only_day, only_count = next(iter(by_day.items()))
                if only_day > cutoff_date and only_count >= 10000:
                    by_day = {cutoff_date: only_count}
            cumulative = int(baseline_row["players"] or 0) if baseline_row else 0
            items = []
            for day_ts in pd.date_range(start=cutoff_date, end=today, freq="D"):
                day = day_ts.date().isoformat()
                added = by_day.get(day, 0)
                cumulative += added
                items.append(
                    {
                        "day": day,
                        "new_tracked_players": added,
                        "cumulative_tracked_players": cumulative,
                    }
                )
            return {"items": items}

        return cached_json(settings, f"api:trends:ledger-adds:{start}", 300, build)

    @app.get("/home")
    def home() -> Dict[str, object]:
        def build() -> Dict[str, object]:
            return {
                "overview": overview(),
                "quality": quality(),
                "leaderboards": {
                    "rapid": leaderboards("rapid", limit=12, min_games=20),
                    "blitz": leaderboards("blitz", limit=12, min_games=20),
                },
                "trends": {
                    "joins": joins_trend(months=36),
                    "discovery": discovery_trend(days=60),
                    "ledger_adds": ledger_adds_trend(start="2026-05-18"),
                },
            }

        return cached_json(settings, "api:home", 120, build)

    @app.get("/stats/distribution")
    def rating_distribution(bucket_size: int = Query(default=100, ge=25, le=400)) -> Dict[str, List[Dict[str, object]]]:
        with get_conn(settings) as conn:
            rows = query_all(
                conn,
                f"""
                SELECT
                    (CAST(s.rapid_rating / {bucket_size} AS INT) * {bucket_size}) AS bucket,
                    COUNT(*) AS players
                FROM users u
                JOIN user_stats_latest s ON s.username = u.username
                WHERE u.status='active' AND s.rapid_rating > 0
                GROUP BY bucket
                ORDER BY bucket
                """
            )
        return {"items": [dict(r) for r in rows]}

    @app.get("/stats/format-summary")
    def format_summary() -> Dict[str, List[Dict[str, object]]]:
        with get_conn(settings) as conn:
            row = query_one(
                conn,
                """
                SELECT
                    SUM(COALESCE(s.total_rapid, 0)) AS rapid_games,
                    SUM(COALESCE(s.total_blitz, 0)) AS blitz_games,
                    SUM(COALESCE(s.total_bullet, 0)) AS bullet_games,
                    SUM(COALESCE(s.total_daily, 0)) AS daily_games,
                    AVG(CASE WHEN s.rapid_rating > 0 THEN s.rapid_rating END) AS rapid_avg,
                    AVG(CASE WHEN s.blitz_rating > 0 THEN s.blitz_rating END) AS blitz_avg,
                    AVG(CASE WHEN s.bullet_rating > 0 THEN s.bullet_rating END) AS bullet_avg,
                    AVG(CASE WHEN s.daily_rating > 0 THEN s.daily_rating END) AS daily_avg,
                    AVG(CASE WHEN s.highest_puzzle_rating > 0 THEN s.highest_puzzle_rating END) AS puzzle_avg
                FROM users u
                JOIN user_stats_latest s ON s.username = u.username
                WHERE u.status='active'
                """
            )
        return {
            "items": [
                {"format": "rapid", "games": int(row["rapid_games"] or 0), "avg_rating": float(row["rapid_avg"] or 0)},
                {"format": "blitz", "games": int(row["blitz_games"] or 0), "avg_rating": float(row["blitz_avg"] or 0)},
                {"format": "bullet", "games": int(row["bullet_games"] or 0), "avg_rating": float(row["bullet_avg"] or 0)},
                {"format": "daily", "games": int(row["daily_games"] or 0), "avg_rating": float(row["daily_avg"] or 0)},
                {"format": "puzzle", "games": 0, "avg_rating": float(row["puzzle_avg"] or 0)},
            ]
        }

    @app.get("/stats/activity-buckets")
    def activity_buckets() -> Dict[str, List[Dict[str, object]]]:
        with get_conn(settings) as conn:
            rows = query_all(
                conn,
                """
                SELECT bucket, COUNT(*) AS players
                FROM (
                    SELECT
                        CASE
                            WHEN COALESCE(s.total_games, 0) < 10 THEN '0-9'
                            WHEN COALESCE(s.total_games, 0) < 50 THEN '10-49'
                            WHEN COALESCE(s.total_games, 0) < 200 THEN '50-199'
                            WHEN COALESCE(s.total_games, 0) < 1000 THEN '200-999'
                            WHEN COALESCE(s.total_games, 0) < 5000 THEN '1k-4.9k'
                            WHEN COALESCE(s.total_games, 0) < 20000 THEN '5k-19.9k'
                            ELSE '20k+'
                        END AS bucket
                    FROM users u
                    JOIN user_stats_latest s ON s.username = u.username
                    WHERE u.status='active'
                )
                GROUP BY bucket
                ORDER BY
                    CASE bucket
                        WHEN '0-9' THEN 1
                        WHEN '10-49' THEN 2
                        WHEN '50-199' THEN 3
                        WHEN '200-999' THEN 4
                        WHEN '1k-4.9k' THEN 5
                        WHEN '5k-19.9k' THEN 6
                        WHEN '20k+' THEN 7
                    END
                """
            )
        return {"items": [dict(r) for r in rows]}

    @app.get("/stats/rating-scatter")
    def rating_scatter(limit: int = Query(default=1200, ge=10, le=5000)) -> Dict[str, List[Dict[str, object]]]:
        with get_conn(settings) as conn:
            rows = query_all(
                conn,
                """
                SELECT
                    u.username,
                    s.rapid_rating,
                    s.blitz_rating,
                    s.bullet_rating,
                    s.daily_rating,
                    s.total_games
                FROM users u
                JOIN user_stats_latest s ON s.username = u.username
                WHERE u.status='active'
                  AND s.rapid_rating > 0
                  AND s.blitz_rating > 0
                ORDER BY s.total_games DESC
                LIMIT ?
                """,
                (limit,),
            )
        return {"items": [dict(r) for r in rows]}

    @app.get("/stats/analytics-pack")
    def analytics_pack() -> Dict[str, object]:
        return get_or_build_cached_payload(
            settings,
            cache_key="stats:analytics-pack",
            builder=build_analytics_pack_payload,
            source="api:analytics-pack",
        )

    @app.get("/stats/correlation-matrix")
    def correlation_matrix() -> Dict[str, List[Dict[str, object]]]:
        return get_or_build_cached_payload(
            settings,
            cache_key="stats:correlation-matrix",
            builder=build_correlation_matrix_payload,
            source="api:correlation-matrix",
        )

    @app.get("/stats/percentile-bands")
    def percentile_bands() -> Dict[str, List[Dict[str, object]]]:
        return get_or_build_cached_payload(
            settings,
            cache_key="stats:percentile-bands",
            builder=build_percentile_bands_payload,
            source="api:percentile-bands",
        )

    @app.get("/stats/cohort-retention")
    def cohort_retention(months: int = Query(default=24, ge=6, le=120)) -> Dict[str, List[Dict[str, object]]]:
        if months == 24:
            return get_or_build_cached_payload(
                settings,
                cache_key="stats:cohort-retention:24",
                builder=lambda conn: build_cohort_retention_payload(conn, months=24),
                source="api:cohort-retention",
            )
        with get_conn(settings) as conn:
            return build_cohort_retention_payload(conn, months=months)

    @app.get("/stats/story-report")
    def story_report() -> Dict[str, object]:
        return get_or_build_cached_payload(
            settings,
            cache_key="stats:story-report",
            builder=build_story_report_payload,
            source="api:story-report",
        )

    @app.get("/players/{username}/benchmark")
    def player_benchmark(username: str) -> Dict[str, object]:
        normalized = username.strip().lower()
        with get_conn(settings) as conn:
            payload = build_player_benchmark_payload(conn, normalized)
        if not payload:
            raise HTTPException(status_code=404, detail="Player not found")
        return payload

    return app
