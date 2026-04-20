import os
import threading
from pathlib import Path
from typing import Dict, List, Literal, Optional

import numpy as np
import pandas as pd

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .config import Settings
from .db import get_conn, init_db
from .quality import compute_quality_report
from .repository import query_all, query_one


RATING_COLUMNS = [
    "rapid_rating",
    "blitz_rating",
    "bullet_rating",
    "daily_rating",
    "highest_puzzle_rating",
]


def _rows_to_frame(rows: List[object], required_cols: List[str]) -> pd.DataFrame:
    df = pd.DataFrame([dict(r) for r in rows])
    for col in required_cols:
        if col not in df.columns:
            df[col] = pd.Series(dtype="float64")
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


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


def create_app(settings: Optional[Settings] = None) -> FastAPI:
    settings = settings or Settings()
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
        return compute_quality_report(settings)

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
        with get_conn(settings) as conn:
            rows = query_all(conn, sql, (min_games, limit))
        return {"board": board, "items": [dict(r) for r in rows]}

    @app.get("/players/{username}")
    def player_detail(username: str) -> Dict[str, object]:
        normalized = username.strip().lower()
        with get_conn(settings) as conn:
            row = query_one(
                conn,
                """
                SELECT
                    u.username, u.joined_at, u.last_online, u.status, u.first_seen_at, u.last_seen_active_at,
                    s.*
                FROM users u
                LEFT JOIN user_stats_latest s ON s.username = u.username
                WHERE u.username = ?
                """,
                (normalized,),
            )
        if not row:
            raise HTTPException(status_code=404, detail="Player not found")
        payload = dict(row)
        return payload

    @app.get("/trends/joins")
    def joins_trend(months: int = Query(default=48, ge=1, le=240)) -> Dict[str, List[Dict[str, object]]]:
        with get_conn(settings) as conn:
            rows = query_all(
                conn,
                """
                SELECT strftime('%Y-%m', joined_at) AS month, COUNT(*) AS players
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

    @app.get("/trends/discovery")
    def discovery_trend(days: int = Query(default=60, ge=1, le=365)) -> Dict[str, List[Dict[str, object]]]:
        with get_conn(settings) as conn:
            rows = query_all(
                conn,
                """
                SELECT snapshot_date AS day, COUNT(*) AS active_players
                FROM country_active_snapshots
                WHERE snapshot_date >= date('now', ?)
                GROUP BY snapshot_date
                ORDER BY snapshot_date
                """,
                (f"-{days} day",),
            )
        return {"items": [dict(r) for r in rows]}

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

    @app.get("/stats/correlation-matrix")
    def correlation_matrix() -> Dict[str, List[Dict[str, object]]]:
        with get_conn(settings) as conn:
            rows = query_all(
                conn,
                """
                SELECT
                    s.rapid_rating,
                    s.blitz_rating,
                    s.bullet_rating,
                    s.daily_rating,
                    s.highest_puzzle_rating
                FROM users u
                JOIN user_stats_latest s ON s.username = u.username
                WHERE u.status='active'
                """
            )
        df = _rows_to_frame(rows, RATING_COLUMNS)
        corr = df[RATING_COLUMNS].corr(method="pearson").fillna(0.0)
        matrix: List[Dict[str, object]] = []
        for r in RATING_COLUMNS:
            for c in RATING_COLUMNS:
                matrix.append({"x": r, "y": c, "value": round(float(corr.loc[r, c]), 4)})
        return {"items": matrix}

    @app.get("/stats/percentile-bands")
    def percentile_bands() -> Dict[str, List[Dict[str, object]]]:
        with get_conn(settings) as conn:
            rows = query_all(
                conn,
                """
                SELECT
                    s.rapid_rating,
                    s.blitz_rating,
                    s.bullet_rating,
                    s.daily_rating,
                    s.highest_puzzle_rating
                FROM users u
                JOIN user_stats_latest s ON s.username = u.username
                WHERE u.status='active'
                """
            )
        df = _rows_to_frame(rows, RATING_COLUMNS)
        pct_points = [10, 25, 50, 75, 90, 99]
        out: List[Dict[str, object]] = []
        mapping = {
            "rapid_rating": "rapid",
            "blitz_rating": "blitz",
            "bullet_rating": "bullet",
            "daily_rating": "daily",
            "highest_puzzle_rating": "puzzle",
        }
        for col, name in mapping.items():
            values = df[col]
            values = values[values > 0].dropna()
            if len(values) == 0:
                continue
            for p in pct_points:
                out.append(
                    {
                        "format": name,
                        "percentile": p,
                        "rating": int(np.percentile(values, p)),
                    }
                )
        return {"items": out}

    @app.get("/stats/cohort-retention")
    def cohort_retention(months: int = Query(default=24, ge=6, le=120)) -> Dict[str, List[Dict[str, object]]]:
        with get_conn(settings) as conn:
            rows = query_all(
                conn,
                """
                SELECT joined_at, last_seen_active_at
                FROM users
                WHERE status='active' AND joined_at IS NOT NULL
                """
            )
        df = pd.DataFrame([dict(r) for r in rows])
        if df.empty:
            return {"items": []}
        df["joined_at"] = pd.to_datetime(df["joined_at"], errors="coerce", utc=True)
        df["last_seen_active_at"] = pd.to_datetime(df["last_seen_active_at"], errors="coerce", utc=True)
        df = df.dropna(subset=["joined_at"])
        cutoff = pd.Timestamp.utcnow() - pd.Timedelta(days=90)
        df["recent_active"] = df["last_seen_active_at"].fillna(pd.Timestamp("1970-01-01", tz="UTC")) >= cutoff
        df["cohort"] = df["joined_at"].dt.tz_convert(None).dt.to_period("M").astype(str)
        grouped = (
            df.groupby("cohort")
            .agg(total_players=("cohort", "size"), retained_90d=("recent_active", "sum"))
            .reset_index()
            .sort_values("cohort", ascending=False)
            .head(months)
            .sort_values("cohort")
        )
        grouped["retention_rate"] = (grouped["retained_90d"] / grouped["total_players"]).fillna(0)
        return {
            "items": [
                {
                    "cohort": str(r["cohort"]),
                    "total_players": int(r["total_players"]),
                    "retained_90d": int(r["retained_90d"]),
                    "retention_rate": round(float(r["retention_rate"]), 4),
                }
                for _, r in grouped.iterrows()
            ]
        }

    @app.get("/players/{username}/benchmark")
    def player_benchmark(username: str) -> Dict[str, object]:
        normalized = username.strip().lower()
        with get_conn(settings) as conn:
            target = query_one(
                conn,
                """
                SELECT s.rapid_rating, s.blitz_rating, s.bullet_rating, s.daily_rating,
                       s.highest_puzzle_rating, s.total_games
                FROM users u
                JOIN user_stats_latest s ON s.username = u.username
                WHERE u.username = ? AND u.status='active'
                """,
                (normalized,),
            )
            if not target:
                raise HTTPException(status_code=404, detail="Player not found")
            population = query_all(
                conn,
                """
                SELECT s.rapid_rating, s.blitz_rating, s.bullet_rating, s.daily_rating,
                       s.highest_puzzle_rating, s.total_games
                FROM users u
                JOIN user_stats_latest s ON s.username = u.username
                WHERE u.status='active'
                """
            )
        pop_df = pd.DataFrame([dict(r) for r in population])
        tgt = dict(target)
        out = {}
        for key in ["rapid_rating", "blitz_rating", "bullet_rating", "daily_rating", "highest_puzzle_rating", "total_games"]:
            vals = pd.to_numeric(pop_df[key], errors="coerce").dropna()
            tv = float(tgt.get(key) or 0)
            if len(vals) == 0:
                out[key] = {"value": tv, "percentile": None}
                continue
            percentile = float((vals <= tv).mean() * 100.0)
            out[key] = {"value": tv, "percentile": round(percentile, 2)}
        return {"username": normalized, "metrics": out}

    return app
