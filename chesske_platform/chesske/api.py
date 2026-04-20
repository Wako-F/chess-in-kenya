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

FORMAT_GAME_COLUMNS = ["total_daily", "total_rapid", "total_blitz", "total_bullet"]
STORY_NUMERIC_COLUMNS = [
    "total_games",
    *FORMAT_GAME_COLUMNS,
    "daily_rating",
    "rapid_rating",
    "blitz_rating",
    "bullet_rating",
    "highest_puzzle_rating",
    "daily_wins",
    "daily_losses",
    "daily_draws",
    "rapid_wins",
    "rapid_losses",
    "rapid_draws",
    "blitz_wins",
    "blitz_losses",
    "blitz_draws",
    "bullet_wins",
    "bullet_losses",
    "bullet_draws",
]


def _rows_to_frame(rows: List[object], required_cols: List[str]) -> pd.DataFrame:
    df = pd.DataFrame([dict(r) for r in rows])
    for col in required_cols:
        if col not in df.columns:
            df[col] = pd.Series(dtype="float64")
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def _pct(part: float, whole: float) -> float:
    if not whole:
        return 0.0
    return float(part) / float(whole)


def _population_frame(settings: Settings) -> pd.DataFrame:
    with get_conn(settings) as conn:
        rows = query_all(
            conn,
            """
            SELECT
                u.username,
                u.joined_at,
                u.last_online,
                u.last_seen_active_at,
                s.total_games,
                s.total_daily,
                s.total_rapid,
                s.total_blitz,
                s.total_bullet,
                s.daily_rating,
                s.rapid_rating,
                s.blitz_rating,
                s.bullet_rating,
                s.highest_puzzle_rating,
                s.daily_wins,
                s.daily_losses,
                s.daily_draws,
                s.rapid_wins,
                s.rapid_losses,
                s.rapid_draws,
                s.blitz_wins,
                s.blitz_losses,
                s.blitz_draws,
                s.bullet_wins,
                s.bullet_losses,
                s.bullet_draws
            FROM users u
            JOIN user_stats_latest s ON s.username = u.username
            WHERE u.status = 'active'
            """
        )
    df = pd.DataFrame([dict(r) for r in rows])
    if df.empty:
        for col in STORY_NUMERIC_COLUMNS:
            df[col] = pd.Series(dtype="float64")
        for col in ["username", "joined_at", "last_online", "last_seen_active_at"]:
            df[col] = pd.Series(dtype="object")
        return df

    for col in STORY_NUMERIC_COLUMNS:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    for col in ["joined_at", "last_online", "last_seen_active_at"]:
        if col not in df.columns:
            df[col] = pd.NaT
        df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)

    now = pd.Timestamp.now(tz="UTC")
    df["days_since_online"] = (now - df["last_online"]).dt.total_seconds().div(86400)
    df["days_since_join"] = (now - df["joined_at"]).dt.total_seconds().div(86400)
    df["formats_played"] = (df[FORMAT_GAME_COLUMNS] > 0).sum(axis=1)
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

    @app.get("/trends/discovery")
    def discovery_trend(days: int = Query(default=60, ge=1, le=365)) -> Dict[str, List[Dict[str, object]]]:
        cutoff_date = (pd.Timestamp.utcnow() - pd.Timedelta(days=days)).date().isoformat()
        with get_conn(settings) as conn:
            rows = query_all(
                conn,
                """
                SELECT snapshot_date AS day, COUNT(*) AS active_players
                FROM country_active_snapshots
                WHERE snapshot_date >= ?
                GROUP BY snapshot_date
                ORDER BY snapshot_date
                """,
                (cutoff_date,),
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

    @app.get("/stats/story-report")
    def story_report() -> Dict[str, object]:
        df = _population_frame(settings)
        if df.empty:
            return {
                "snapshot": {},
                "recency_buckets": [],
                "concentration": {"top_shares": [], "curve": [], "volume_tiers": []},
                "format_identity": {
                    "participation": [],
                    "dominance": [],
                    "format_mix": [],
                    "rapid_blitz_gap": {},
                },
                "cohorts": [],
                "puzzle_culture": {"segments": [], "correlations": []},
                "archetypes": [],
                "outcome_style": [],
            }

        total_players = int(len(df))
        total_games = float(df["total_games"].sum())
        nonzero_games = df["total_games"].clip(lower=0)

        recency_defs = [
            ("Active 7d", (df["days_since_online"] <= 7)),
            ("Active 30d", (df["days_since_online"] <= 30)),
            ("Active 90d", (df["days_since_online"] <= 90)),
            ("Dormant 365d+", (df["days_since_online"] > 365)),
        ]
        recency_buckets = [
            {"label": label, "players": int(mask.fillna(False).sum())}
            for label, mask in recency_defs
        ]

        sorted_games = nonzero_games.sort_values().reset_index(drop=True)
        cumulative_games = sorted_games.cumsum()
        total_games_safe = float(cumulative_games.iloc[-1]) if len(cumulative_games) else 0.0
        curve = []
        for pct in range(10, 101, 10):
            idx = max(0, int(np.ceil(len(sorted_games) * (pct / 100))) - 1)
            games_share = _pct(float(cumulative_games.iloc[idx]), total_games_safe) if len(cumulative_games) else 0.0
            curve.append({"player_percentile": pct, "game_share": round(games_share, 4)})

        top_shares = []
        for pct in (1, 5, 10):
            n = max(1, int(np.ceil(total_players * (pct / 100))))
            share = _pct(float(nonzero_games.nlargest(n).sum()), total_games_safe)
            top_shares.append({"group": f"Top {pct}%", "share": round(share, 4)})

        tier_bins = [-1, 0, 9, 49, 199, 999, 4999, float("inf")]
        tier_labels = ["0", "1-9", "10-49", "50-199", "200-999", "1k-4.9k", "5k+"]
        tier_counts = (
            pd.cut(df["total_games"], bins=tier_bins, labels=tier_labels)
            .value_counts()
            .sort_index()
        )
        volume_tiers = [
            {"tier": str(tier), "players": int(count)}
            for tier, count in tier_counts.items()
        ]

        participation = [
            {
                "format": label,
                "players": int((df[games_col] > 0).sum()),
                "share": round(float((df[games_col] > 0).mean()), 4),
            }
            for label, games_col in [
                ("Daily", "total_daily"),
                ("Rapid", "total_rapid"),
                ("Blitz", "total_blitz"),
                ("Bullet", "total_bullet"),
            ]
        ]

        format_volume = df[FORMAT_GAME_COLUMNS].copy()
        format_volume.columns = ["daily", "rapid", "blitz", "bullet"]
        format_total = format_volume.sum(axis=1)
        dominant_format = format_volume.idxmax(axis=1)
        dominant_share = format_volume.max(axis=1).div(format_total.replace(0, np.nan))
        dominant_df = pd.DataFrame(
            {
                "dominant_format": dominant_format,
                "dominant_share": dominant_share,
            }
        )
        dominant_df = dominant_df[(format_total > 0) & (dominant_df["dominant_share"] >= 0.8)]
        dominance = [
            {"format": fmt.title(), "players": int(count)}
            for fmt, count in dominant_df["dominant_format"].value_counts().reindex(
                ["rapid", "blitz", "bullet", "daily"], fill_value=0
            ).items()
        ]

        format_mix = [
            {"formats": str(idx), "players": int(count)}
            for idx, count in df["formats_played"].value_counts().sort_index().items()
        ]

        rapid_blitz = df[
            (df["rapid_rating"] > 0)
            & (df["blitz_rating"] > 0)
            & (df["total_rapid"] >= 20)
            & (df["total_blitz"] >= 20)
        ].copy()
        rapid_blitz["gap"] = rapid_blitz["blitz_rating"] - rapid_blitz["rapid_rating"]
        rapid_blitz_gap = {
            "median_gap": int(rapid_blitz["gap"].median()) if not rapid_blitz.empty else 0,
            "blitz_200_plus": int((rapid_blitz["gap"] >= 200).sum()) if not rapid_blitz.empty else 0,
            "rapid_200_plus": int((rapid_blitz["gap"] <= -200).sum()) if not rapid_blitz.empty else 0,
        }

        cohort_df = df.dropna(subset=["joined_at"]).copy()
        cohort_df["join_year"] = cohort_df["joined_at"].dt.year.astype("Int64")
        cohorts = []
        grouped = (
            cohort_df.groupby("join_year")
            .agg(
                players=("username", "count"),
                median_games=("total_games", "median"),
                active_90d=("days_since_online", lambda s: int((s <= 90).sum())),
            )
            .reset_index()
        )
        for _, row in grouped.tail(8).iterrows():
            players = int(row["players"])
            cohorts.append(
                {
                    "cohort": str(int(row["join_year"])),
                    "players": players,
                    "median_games": int(row["median_games"] or 0),
                    "active_90d": int(row["active_90d"] or 0),
                    "active_rate_90d": round(_pct(float(row["active_90d"] or 0), players), 4),
                }
            )

        puzzle_rating = df["highest_puzzle_rating"].fillna(0)
        puzzle_segments = [
            {
                "segment": "Puzzle rated",
                "players": int((puzzle_rating > 0).sum()),
            },
            {
                "segment": "Puzzle rated, <10 games",
                "players": int(((puzzle_rating > 0) & (df["total_games"] < 10)).sum()),
            },
            {
                "segment": "Top 10% puzzle, <50 games",
                "players": int(
                    (
                        (puzzle_rating >= puzzle_rating[puzzle_rating > 0].quantile(0.9))
                        & (df["total_games"] < 50)
                    ).sum()
                )
                if (puzzle_rating > 0).any()
                else 0,
            },
            {
                "segment": "Puzzle rated, 200+ games",
                "players": int(((puzzle_rating > 0) & (df["total_games"] >= 200)).sum()),
            },
        ]
        puzzle_correlations = []
        for label, col in [("Rapid", "rapid_rating"), ("Blitz", "blitz_rating"), ("Bullet", "bullet_rating"), ("Daily", "daily_rating")]:
            sub = df[(df[col] > 0) & (puzzle_rating > 0)]
            corr = sub[col].corr(sub["highest_puzzle_rating"]) if len(sub) else 0.0
            puzzle_correlations.append({"format": label, "correlation": round(float(corr or 0.0), 4)})

        now = pd.Timestamp.now(tz="UTC")
        recent_join_cutoff = now - pd.Timedelta(days=365)
        veteran_cutoff = now - pd.Timedelta(days=730)
        share_frame = format_volume.div(format_total.replace(0, np.nan), axis=0)
        archetypes = [
            {
                "name": "New, low volume",
                "count": int(((df["joined_at"] >= recent_join_cutoff) & (df["total_games"] < 50)).sum()),
                "description": "Joined within the last year, but still light-touch participants.",
            },
            {
                "name": "New, high volume",
                "count": int(((df["joined_at"] >= recent_join_cutoff) & (df["total_games"] >= 500)).sum()),
                "description": "Recent arrivals who converted quickly into committed play.",
            },
            {
                "name": "Veteran, still active",
                "count": int(((df["joined_at"] < veteran_cutoff) & (df["days_since_online"] <= 90)).sum()),
                "description": "Longer-tenured players who still appear in the recent activity window.",
            },
            {
                "name": "Veteran, dormant",
                "count": int(((df["joined_at"] < veteran_cutoff) & (df["days_since_online"] > 365)).sum()),
                "description": "Older accounts that still expand the talent base but have gone quiet.",
            },
            {
                "name": "Rapid specialists",
                "count": int(((df["total_games"] >= 200) & (share_frame["rapid"] >= 0.7)).sum()),
                "description": "Committed players whose game volume is overwhelmingly rapid.",
            },
            {
                "name": "All-rounders",
                "count": int(((df["formats_played"] >= 3) & (df["total_games"] >= 200)).sum()),
                "description": "Substantial players with meaningful activity across at least three formats.",
            },
        ]

        outcome_style = []
        for fmt in ["daily", "rapid", "blitz", "bullet"]:
            total_col = f"total_{fmt}"
            wins = f"{fmt}_wins"
            draws = f"{fmt}_draws"
            subset = df[df[total_col] >= 20]
            if subset.empty:
                outcome_style.append({"format": fmt.title(), "median_win_rate": 0.0, "median_draw_rate": 0.0})
                continue
            win_rate = subset[wins].div(subset[total_col]).fillna(0)
            draw_rate = subset[draws].div(subset[total_col]).fillna(0)
            outcome_style.append(
                {
                    "format": fmt.title(),
                    "median_win_rate": round(float(win_rate.median()), 4),
                    "median_draw_rate": round(float(draw_rate.median()), 4),
                }
            )

        snapshot = {
            "tracked_players": total_players,
            "total_games": int(total_games),
            "median_games": int(nonzero_games.median()),
            "mean_games": round(float(nonzero_games.mean()), 1),
            "p90_games": int(nonzero_games.quantile(0.9)),
            "p99_games": int(nonzero_games.quantile(0.99)),
            "active_7d": int((df["days_since_online"] <= 7).sum()),
            "active_30d": int((df["days_since_online"] <= 30).sum()),
            "active_90d": int((df["days_since_online"] <= 90).sum()),
            "dormant_365d": int((df["days_since_online"] > 365).sum()),
            "active_share_90d": round(float((df["days_since_online"] <= 90).mean()), 4),
        }

        return {
            "snapshot": snapshot,
            "recency_buckets": recency_buckets,
            "concentration": {
                "top_shares": top_shares,
                "curve": curve,
                "volume_tiers": volume_tiers,
            },
            "format_identity": {
                "participation": participation,
                "dominance": dominance,
                "format_mix": format_mix,
                "rapid_blitz_gap": rapid_blitz_gap,
            },
            "cohorts": cohorts,
            "puzzle_culture": {
                "segments": puzzle_segments,
                "correlations": puzzle_correlations,
            },
            "archetypes": archetypes,
            "outcome_style": outcome_style,
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
