import math
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional

from .config import Settings
from .db import get_conn
from .repository import get_cached_payload, query_all, query_one, upsert_cached_payload


RATING_COLUMNS = [
    "rapid_rating",
    "blitz_rating",
    "bullet_rating",
    "daily_rating",
    "highest_puzzle_rating",
]

FORMAT_COLUMNS = {
    "daily": "total_daily",
    "rapid": "total_rapid",
    "blitz": "total_blitz",
    "bullet": "total_bullet",
}

PERCENTILE_POINTS = [10, 25, 50, 75, 90, 99]
PROFILE_RANK_MIN_GAMES = 20


def _iso_days_ago(days: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


def _round(value: Optional[float], places: int = 4) -> float:
    return round(float(value or 0.0), places)


def _calc_correlation(conn: Any, left: str, right: str) -> float:
    row = query_one(
        conn,
        f"""
        SELECT
            COUNT(*) AS n,
            SUM(CAST({left} AS REAL)) AS sum_x,
            SUM(CAST({right} AS REAL)) AS sum_y,
            SUM(CAST({left} AS REAL) * CAST({left} AS REAL)) AS sum_x2,
            SUM(CAST({right} AS REAL) * CAST({right} AS REAL)) AS sum_y2,
            SUM(CAST({left} AS REAL) * CAST({right} AS REAL)) AS sum_xy
        FROM user_stats_latest
        WHERE COALESCE({left}, 0) > 0
          AND COALESCE({right}, 0) > 0
        """,
    )
    if not row or int(row["n"] or 0) < 2:
        return 0.0

    n = float(row["n"])
    sum_x = float(row["sum_x"] or 0.0)
    sum_y = float(row["sum_y"] or 0.0)
    sum_x2 = float(row["sum_x2"] or 0.0)
    sum_y2 = float(row["sum_y2"] or 0.0)
    sum_xy = float(row["sum_xy"] or 0.0)
    numerator = (n * sum_xy) - (sum_x * sum_y)
    denom_left = (n * sum_x2) - (sum_x * sum_x)
    denom_right = (n * sum_y2) - (sum_y * sum_y)
    denominator = math.sqrt(max(denom_left, 0.0) * max(denom_right, 0.0))
    if denominator <= 0:
        return 0.0
    return numerator / denominator


def _select_percentile(conn: Any, column: str, pct: int) -> Optional[int]:
    count_row = query_one(
        conn,
        f"SELECT COUNT(*) AS c FROM user_stats_latest WHERE COALESCE({column}, 0) > 0",
    )
    count = int(count_row["c"] or 0) if count_row else 0
    if count == 0:
        return None
    offset = max(0, math.ceil(count * (pct / 100.0)) - 1)
    row = query_one(
        conn,
        f"""
        SELECT {column} AS value
        FROM user_stats_latest
        WHERE COALESCE({column}, 0) > 0
        ORDER BY {column}
        LIMIT 1 OFFSET ?
        """,
        (offset,),
    )
    if not row:
        return None
    return int(row["value"] or 0)


def build_correlation_matrix_payload(conn: Any) -> Dict[str, List[Dict[str, object]]]:
    items: List[Dict[str, object]] = []
    for row_name in RATING_COLUMNS:
        for col_name in RATING_COLUMNS:
            if row_name == col_name:
                value = 1.0
            else:
                value = _calc_correlation(conn, row_name, col_name)
            items.append({"x": row_name, "y": col_name, "value": round(value, 4)})
    return {"items": items}


def build_percentile_bands_payload(conn: Any) -> Dict[str, List[Dict[str, object]]]:
    mapping = {
        "rapid_rating": "rapid",
        "blitz_rating": "blitz",
        "bullet_rating": "bullet",
        "daily_rating": "daily",
        "highest_puzzle_rating": "puzzle",
    }
    items: List[Dict[str, object]] = []
    for column, label in mapping.items():
        for pct in PERCENTILE_POINTS:
            rating = _select_percentile(conn, column, pct)
            if rating is None:
                continue
            items.append({"format": label, "percentile": pct, "rating": rating})
    return {"items": items}


def build_cohort_retention_payload(conn: Any, months: int = 24) -> Dict[str, List[Dict[str, object]]]:
    cutoff = _iso_days_ago(90)
    rows = query_all(
        conn,
        """
        SELECT
            SUBSTR(joined_at, 1, 7) AS cohort,
            COUNT(*) AS total_players,
            SUM(CASE WHEN COALESCE(last_seen_active_at, '') >= ? THEN 1 ELSE 0 END) AS retained_90d
        FROM users
        WHERE status = 'active'
          AND joined_at IS NOT NULL
        GROUP BY SUBSTR(joined_at, 1, 7)
        ORDER BY cohort DESC
        LIMIT ?
        """,
        (cutoff, months),
    )
    items = []
    for row in reversed(rows):
        total_players = int(row["total_players"] or 0)
        retained_90d = int(row["retained_90d"] or 0)
        items.append(
            {
                "cohort": str(row["cohort"]),
                "total_players": total_players,
                "retained_90d": retained_90d,
                "retention_rate": _round(retained_90d / total_players if total_players else 0.0),
            }
        )
    return {"items": items}


def _count(conn: Any, where_sql: str = "1=1", params: Iterable[object] = ()) -> int:
    row = query_one(conn, f"SELECT COUNT(*) AS c FROM users u JOIN user_stats_latest s ON s.username = u.username WHERE u.status = 'active' AND {where_sql}", tuple(params))
    return int(row["c"] or 0) if row else 0


def _median_ratio(conn: Any, wins_col: str, draws_col: str, total_col: str) -> Dict[str, float]:
    count_row = query_one(
        conn,
        f"SELECT COUNT(*) AS c FROM user_stats_latest WHERE COALESCE({total_col}, 0) >= 20",
    )
    count = int(count_row["c"] or 0) if count_row else 0
    if count == 0:
        return {"median_win_rate": 0.0, "median_draw_rate": 0.0}
    offset = max(0, math.ceil(count * 0.5) - 1)
    win_row = query_one(
        conn,
        f"""
        SELECT CAST({wins_col} AS REAL) / NULLIF({total_col}, 0) AS value
        FROM user_stats_latest
        WHERE COALESCE({total_col}, 0) >= 20
        ORDER BY value
        LIMIT 1 OFFSET ?
        """,
        (offset,),
    )
    draw_row = query_one(
        conn,
        f"""
        SELECT CAST({draws_col} AS REAL) / NULLIF({total_col}, 0) AS value
        FROM user_stats_latest
        WHERE COALESCE({total_col}, 0) >= 20
        ORDER BY value
        LIMIT 1 OFFSET ?
        """,
        (offset,),
    )
    return {
        "median_win_rate": _round(float(win_row["value"] or 0.0) if win_row else 0.0),
        "median_draw_rate": _round(float(draw_row["value"] or 0.0) if draw_row else 0.0),
    }


def build_story_report_payload(conn: Any) -> Dict[str, object]:
    active_7d = _iso_days_ago(7)
    active_30d = _iso_days_ago(30)
    active_90d = _iso_days_ago(90)
    dormant_365d = _iso_days_ago(365)
    recent_join_cutoff = _iso_days_ago(365)
    veteran_cutoff = _iso_days_ago(730)

    snapshot_row = query_one(
        conn,
        """
        SELECT
            COUNT(*) AS tracked_players,
            SUM(COALESCE(s.total_games, 0)) AS total_games,
            AVG(COALESCE(s.total_games, 0)) AS mean_games,
            SUM(CASE WHEN COALESCE(u.last_online, '') >= ? THEN 1 ELSE 0 END) AS active_7d,
            SUM(CASE WHEN COALESCE(u.last_online, '') >= ? THEN 1 ELSE 0 END) AS active_30d,
            SUM(CASE WHEN COALESCE(u.last_online, '') >= ? THEN 1 ELSE 0 END) AS active_90d,
            SUM(CASE WHEN COALESCE(u.last_online, '') < ? OR u.last_online IS NULL THEN 1 ELSE 0 END) AS dormant_365d
        FROM users u
        JOIN user_stats_latest s ON s.username = u.username
        WHERE u.status = 'active'
        """,
        (active_7d, active_30d, active_90d, dormant_365d),
    )
    total_players = int(snapshot_row["tracked_players"] or 0) if snapshot_row else 0
    if total_players == 0:
        return {
            "snapshot": {},
            "recency_buckets": [],
            "concentration": {"top_shares": [], "curve": [], "volume_tiers": []},
            "format_identity": {"participation": [], "dominance": [], "format_mix": [], "rapid_blitz_gap": {}},
            "cohorts": [],
            "puzzle_culture": {"segments": [], "correlations": []},
            "archetypes": [],
            "outcome_style": [],
        }

    percentile_total_games = {
        50: _select_percentile(conn, "total_games", 50) or 0,
        90: _select_percentile(conn, "total_games", 90) or 0,
        99: _select_percentile(conn, "total_games", 99) or 0,
    }

    recency_buckets = [
        {"label": "Active 7d", "players": int(snapshot_row["active_7d"] or 0)},
        {"label": "Active 30d", "players": int(snapshot_row["active_30d"] or 0)},
        {"label": "Active 90d", "players": int(snapshot_row["active_90d"] or 0)},
        {"label": "Dormant 365d+", "players": int(snapshot_row["dormant_365d"] or 0)},
    ]

    total_games_sum = float(snapshot_row["total_games"] or 0.0)
    curve_rows = query_all(
        conn,
        """
        WITH ordered AS (
            SELECT
                COALESCE(s.total_games, 0) AS total_games,
                ROW_NUMBER() OVER (ORDER BY COALESCE(s.total_games, 0)) AS rn,
                COUNT(*) OVER () AS total_players,
                SUM(COALESCE(s.total_games, 0)) OVER (
                    ORDER BY COALESCE(s.total_games, 0)
                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                ) AS cumulative_games
            FROM users u
            JOIN user_stats_latest s ON s.username = u.username
            WHERE u.status = 'active'
        )
        SELECT player_percentile, cumulative_games
        FROM (
            SELECT 10 AS player_percentile UNION ALL
            SELECT 20 UNION ALL
            SELECT 30 UNION ALL
            SELECT 40 UNION ALL
            SELECT 50 UNION ALL
            SELECT 60 UNION ALL
            SELECT 70 UNION ALL
            SELECT 80 UNION ALL
            SELECT 90 UNION ALL
            SELECT 100
        ) p
        JOIN ordered o
          ON o.rn = CASE
              WHEN CAST(((o.total_players * p.player_percentile) + 99) / 100 AS INTEGER) < 1 THEN 1
              ELSE CAST(((o.total_players * p.player_percentile) + 99) / 100 AS INTEGER)
          END
        GROUP BY player_percentile, cumulative_games
        ORDER BY player_percentile
        """,
    )
    curve = [
        {
            "player_percentile": int(row["player_percentile"]),
            "game_share": _round(float(row["cumulative_games"] or 0.0) / total_games_sum if total_games_sum else 0.0),
        }
        for row in curve_rows
    ]

    top_shares = []
    for pct in (1, 5, 10):
        limit = max(1, math.ceil(total_players * (pct / 100.0)))
        row = query_one(
            conn,
            """
            SELECT SUM(total_games) AS total_games
            FROM (
                SELECT COALESCE(s.total_games, 0) AS total_games
                FROM users u
                JOIN user_stats_latest s ON s.username = u.username
                WHERE u.status = 'active'
                ORDER BY COALESCE(s.total_games, 0) DESC
                LIMIT ?
            )
            """,
            (limit,),
        )
        share = float(row["total_games"] or 0.0) / total_games_sum if total_games_sum else 0.0
        top_shares.append({"group": f"Top {pct}%", "share": _round(share)})

    volume_rows = query_all(
        conn,
        """
        SELECT
            CASE
                WHEN COALESCE(s.total_games, 0) = 0 THEN '0'
                WHEN COALESCE(s.total_games, 0) < 10 THEN '1-9'
                WHEN COALESCE(s.total_games, 0) < 50 THEN '10-49'
                WHEN COALESCE(s.total_games, 0) < 200 THEN '50-199'
                WHEN COALESCE(s.total_games, 0) < 1000 THEN '200-999'
                WHEN COALESCE(s.total_games, 0) < 5000 THEN '1k-4.9k'
                ELSE '5k+'
            END AS tier,
            COUNT(*) AS players
        FROM users u
        JOIN user_stats_latest s ON s.username = u.username
        WHERE u.status = 'active'
        GROUP BY tier
        """,
    )
    tier_order = {"0": 1, "1-9": 2, "10-49": 3, "50-199": 4, "200-999": 5, "1k-4.9k": 6, "5k+": 7}
    volume_tiers = [
        {"tier": str(row["tier"]), "players": int(row["players"] or 0)}
        for row in sorted(volume_rows, key=lambda r: tier_order.get(str(r["tier"]), 99))
    ]

    participation = []
    for label, total_col in FORMAT_COLUMNS.items():
        row = query_one(
            conn,
            f"""
            SELECT
                SUM(CASE WHEN COALESCE({total_col}, 0) > 0 THEN 1 ELSE 0 END) AS players,
                COUNT(*) AS total_players
            FROM user_stats_latest
            """,
        )
        players = int(row["players"] or 0) if row else 0
        total = int(row["total_players"] or 0) if row else 0
        participation.append(
            {
                "format": label.title(),
                "players": players,
                "share": _round(players / total if total else 0.0),
            }
        )

    dominance_rows = query_all(
        conn,
        """
        WITH totals AS (
            SELECT
                total_daily,
                total_rapid,
                total_blitz,
                total_bullet,
                (COALESCE(total_daily, 0) + COALESCE(total_rapid, 0) + COALESCE(total_blitz, 0) + COALESCE(total_bullet, 0)) AS format_total
            FROM user_stats_latest
        )
        SELECT dominant_format, COUNT(*) AS players
        FROM (
            SELECT
                CASE
                    WHEN format_total = 0 THEN NULL
                    WHEN total_rapid >= total_blitz AND total_rapid >= total_bullet AND total_rapid >= total_daily AND CAST(total_rapid AS REAL) / format_total >= 0.8 THEN 'rapid'
                    WHEN total_blitz >= total_rapid AND total_blitz >= total_bullet AND total_blitz >= total_daily AND CAST(total_blitz AS REAL) / format_total >= 0.8 THEN 'blitz'
                    WHEN total_bullet >= total_rapid AND total_bullet >= total_blitz AND total_bullet >= total_daily AND CAST(total_bullet AS REAL) / format_total >= 0.8 THEN 'bullet'
                    WHEN total_daily >= total_rapid AND total_daily >= total_blitz AND total_daily >= total_bullet AND CAST(total_daily AS REAL) / format_total >= 0.8 THEN 'daily'
                    ELSE NULL
                END AS dominant_format
            FROM totals
        )
        WHERE dominant_format IS NOT NULL
        GROUP BY dominant_format
        """,
    )
    dominance_map = {str(row["dominant_format"]): int(row["players"] or 0) for row in dominance_rows}
    dominance = [{"format": fmt.title(), "players": dominance_map.get(fmt, 0)} for fmt in ["rapid", "blitz", "bullet", "daily"]]

    format_mix_rows = query_all(
        conn,
        """
        SELECT formats_played, COUNT(*) AS players
        FROM (
            SELECT
                (CASE WHEN COALESCE(total_daily, 0) > 0 THEN 1 ELSE 0 END) +
                (CASE WHEN COALESCE(total_rapid, 0) > 0 THEN 1 ELSE 0 END) +
                (CASE WHEN COALESCE(total_blitz, 0) > 0 THEN 1 ELSE 0 END) +
                (CASE WHEN COALESCE(total_bullet, 0) > 0 THEN 1 ELSE 0 END) AS formats_played
            FROM user_stats_latest
        )
        GROUP BY formats_played
        ORDER BY formats_played
        """,
    )
    format_mix = [{"formats": str(row["formats_played"]), "players": int(row["players"] or 0)} for row in format_mix_rows]

    gap_items = []
    for pct in (50,):
        count_row = query_one(
            conn,
            """
            SELECT COUNT(*) AS c
            FROM user_stats_latest
            WHERE COALESCE(rapid_rating, 0) > 0
              AND COALESCE(blitz_rating, 0) > 0
              AND COALESCE(total_rapid, 0) >= 20
              AND COALESCE(total_blitz, 0) >= 20
            """,
        )
        count = int(count_row["c"] or 0) if count_row else 0
        if count == 0:
            gap_items.append(0)
            continue
        offset = max(0, math.ceil(count * (pct / 100.0)) - 1)
        row = query_one(
            conn,
            """
            SELECT (blitz_rating - rapid_rating) AS gap
            FROM user_stats_latest
            WHERE COALESCE(rapid_rating, 0) > 0
              AND COALESCE(blitz_rating, 0) > 0
              AND COALESCE(total_rapid, 0) >= 20
              AND COALESCE(total_blitz, 0) >= 20
            ORDER BY gap
            LIMIT 1 OFFSET ?
            """,
            (offset,),
        )
        gap_items.append(int(row["gap"] or 0) if row else 0)

    rapid_blitz_gap = {
        "median_gap": gap_items[0],
        "blitz_200_plus": _count(conn, "(COALESCE(total_rapid, 0) >= 20 AND COALESCE(total_blitz, 0) >= 20 AND (blitz_rating - rapid_rating) >= 200)"),
        "rapid_200_plus": _count(conn, "(COALESCE(total_rapid, 0) >= 20 AND COALESCE(total_blitz, 0) >= 20 AND (blitz_rating - rapid_rating) <= -200)"),
    }

    cohort_rows = query_all(
        conn,
        """
        SELECT
            SUBSTR(joined_at, 1, 4) AS cohort,
            COUNT(*) AS players,
            SUM(CASE WHEN COALESCE(last_online, '') >= ? THEN 1 ELSE 0 END) AS active_90d
        FROM users
        WHERE status = 'active'
          AND joined_at IS NOT NULL
        GROUP BY SUBSTR(joined_at, 1, 4)
        ORDER BY cohort DESC
        LIMIT 8
        """,
        (active_90d,),
    )
    cohorts = []
    for row in reversed(cohort_rows):
        year = str(row["cohort"])
        cohort_count_row = query_one(
            conn,
            """
            SELECT COUNT(*) AS c
            FROM users u
            JOIN user_stats_latest s ON s.username = u.username
            WHERE u.status = 'active'
              AND SUBSTR(u.joined_at, 1, 4) = ?
            """,
            (year,),
        )
        cohort_count = int(cohort_count_row["c"] or 0) if cohort_count_row else 0
        offset = max(0, math.ceil(cohort_count * 0.5) - 1)
        median_row = query_one(
            conn,
            """
            SELECT COALESCE(s.total_games, 0) AS total_games
            FROM users u
            JOIN user_stats_latest s ON s.username = u.username
            WHERE u.status = 'active'
              AND SUBSTR(u.joined_at, 1, 4) = ?
            ORDER BY COALESCE(s.total_games, 0)
            LIMIT 1 OFFSET ?
            """,
            (year, offset),
        )
        players = int(row["players"] or 0)
        active_players = int(row["active_90d"] or 0)
        cohorts.append(
            {
                "cohort": year,
                "players": players,
                "median_games": int(median_row["total_games"] or 0) if median_row else 0,
                "active_90d": active_players,
                "active_rate_90d": _round(active_players / players if players else 0.0),
            }
        )

    puzzle_row = query_one(
        conn,
        """
        SELECT
            SUM(CASE WHEN COALESCE(highest_puzzle_rating, 0) > 0 THEN 1 ELSE 0 END) AS puzzle_rated,
            SUM(CASE WHEN COALESCE(highest_puzzle_rating, 0) > 0 AND COALESCE(total_games, 0) < 10 THEN 1 ELSE 0 END) AS puzzle_under_10_games,
            SUM(CASE WHEN COALESCE(highest_puzzle_rating, 0) > 0 AND COALESCE(total_games, 0) >= 200 THEN 1 ELSE 0 END) AS puzzle_200_plus_games
        FROM user_stats_latest
        """,
    )
    top_puzzle_cutoff = _select_percentile(conn, "highest_puzzle_rating", 90) or 0
    puzzle_segments = [
        {"segment": "Puzzle rated", "players": int(puzzle_row["puzzle_rated"] or 0) if puzzle_row else 0},
        {"segment": "Puzzle rated, <10 games", "players": int(puzzle_row["puzzle_under_10_games"] or 0) if puzzle_row else 0},
        {"segment": "Top 10% puzzle, <50 games", "players": _count(conn, "COALESCE(s.highest_puzzle_rating, 0) >= ? AND COALESCE(s.total_games, 0) < 50", (top_puzzle_cutoff,))},
        {"segment": "Puzzle rated, 200+ games", "players": int(puzzle_row["puzzle_200_plus_games"] or 0) if puzzle_row else 0},
    ]
    puzzle_correlations = [
        {"format": "Rapid", "correlation": round(_calc_correlation(conn, "rapid_rating", "highest_puzzle_rating"), 4)},
        {"format": "Blitz", "correlation": round(_calc_correlation(conn, "blitz_rating", "highest_puzzle_rating"), 4)},
        {"format": "Bullet", "correlation": round(_calc_correlation(conn, "bullet_rating", "highest_puzzle_rating"), 4)},
        {"format": "Daily", "correlation": round(_calc_correlation(conn, "daily_rating", "highest_puzzle_rating"), 4)},
    ]

    archetypes = [
        {
            "name": "New, low volume",
            "count": _count(conn, "COALESCE(u.joined_at, '') >= ? AND COALESCE(s.total_games, 0) < 50", (recent_join_cutoff,)),
            "description": "Joined within the last year, but still light-touch participants.",
        },
        {
            "name": "New, high volume",
            "count": _count(conn, "COALESCE(u.joined_at, '') >= ? AND COALESCE(s.total_games, 0) >= 500", (recent_join_cutoff,)),
            "description": "Recent arrivals who converted quickly into committed play.",
        },
        {
            "name": "Veteran, still active",
            "count": _count(conn, "COALESCE(u.joined_at, '') < ? AND COALESCE(u.last_online, '') >= ?", (veteran_cutoff, active_90d)),
            "description": "Longer-tenured players who still appear in the recent activity window.",
        },
        {
            "name": "Veteran, dormant",
            "count": _count(conn, "COALESCE(u.joined_at, '') < ? AND (u.last_online IS NULL OR COALESCE(u.last_online, '') < ?)", (veteran_cutoff, dormant_365d)),
            "description": "Older accounts that still expand the talent base but have gone quiet.",
        },
        {
            "name": "Rapid specialists",
            "count": _count(conn, "COALESCE(s.total_games, 0) >= 200 AND CAST(COALESCE(s.total_rapid, 0) AS REAL) / NULLIF(COALESCE(s.total_daily, 0) + COALESCE(s.total_rapid, 0) + COALESCE(s.total_blitz, 0) + COALESCE(s.total_bullet, 0), 0) >= 0.7"),
            "description": "Committed players whose game volume is overwhelmingly rapid.",
        },
        {
            "name": "All-rounders",
            "count": _count(conn, "((CASE WHEN COALESCE(s.total_daily, 0) > 0 THEN 1 ELSE 0 END) + (CASE WHEN COALESCE(s.total_rapid, 0) > 0 THEN 1 ELSE 0 END) + (CASE WHEN COALESCE(s.total_blitz, 0) > 0 THEN 1 ELSE 0 END) + (CASE WHEN COALESCE(s.total_bullet, 0) > 0 THEN 1 ELSE 0 END)) >= 3 AND COALESCE(s.total_games, 0) >= 200"),
            "description": "Substantial players with meaningful activity across at least three formats.",
        },
    ]

    outcome_style = []
    for label in ["daily", "rapid", "blitz", "bullet"]:
        rates = _median_ratio(conn, f"{label}_wins", f"{label}_draws", f"total_{label}")
        outcome_style.append({"format": label.title(), **rates})

    snapshot = {
        "tracked_players": total_players,
        "total_games": int(snapshot_row["total_games"] or 0) if snapshot_row else 0,
        "median_games": int(percentile_total_games[50]),
        "mean_games": round(float(snapshot_row["mean_games"] or 0.0), 1) if snapshot_row else 0.0,
        "p90_games": int(percentile_total_games[90]),
        "p99_games": int(percentile_total_games[99]),
        "active_7d": int(snapshot_row["active_7d"] or 0) if snapshot_row else 0,
        "active_30d": int(snapshot_row["active_30d"] or 0) if snapshot_row else 0,
        "active_90d": int(snapshot_row["active_90d"] or 0) if snapshot_row else 0,
        "dormant_365d": int(snapshot_row["dormant_365d"] or 0) if snapshot_row else 0,
        "active_share_90d": _round(float(snapshot_row["active_90d"] or 0) / total_players if total_players else 0.0),
    }

    return {
        "snapshot": snapshot,
        "recency_buckets": recency_buckets,
        "concentration": {"top_shares": top_shares, "curve": curve, "volume_tiers": volume_tiers},
        "format_identity": {
            "participation": participation,
            "dominance": dominance,
            "format_mix": format_mix,
            "rapid_blitz_gap": rapid_blitz_gap,
        },
        "cohorts": cohorts,
        "puzzle_culture": {"segments": puzzle_segments, "correlations": puzzle_correlations},
        "archetypes": archetypes,
        "outcome_style": outcome_style,
    }


def build_player_benchmark_payload(conn: Any, username: str) -> Optional[Dict[str, object]]:
    target = query_one(
        conn,
        """
        SELECT
            s.rapid_rating,
            s.blitz_rating,
            s.bullet_rating,
            s.daily_rating,
            s.highest_puzzle_rating,
            s.total_rapid,
            s.total_blitz,
            s.total_bullet,
            s.total_daily,
            s.total_games
        FROM users u
        JOIN user_stats_latest s ON s.username = u.username
        WHERE u.username = ? AND u.status = 'active'
        """,
        (username,),
    )
    if not target:
        return None

    rank_rules = {
        "rapid_rating": ("s.rapid_rating", "s.total_rapid", PROFILE_RANK_MIN_GAMES),
        "blitz_rating": ("s.blitz_rating", "s.total_blitz", PROFILE_RANK_MIN_GAMES),
        "bullet_rating": ("s.bullet_rating", "s.total_bullet", PROFILE_RANK_MIN_GAMES),
        "daily_rating": ("s.daily_rating", "s.total_daily", PROFILE_RANK_MIN_GAMES),
        "highest_puzzle_rating": ("s.highest_puzzle_rating", "s.total_games", PROFILE_RANK_MIN_GAMES),
        "total_games": ("s.total_games", "s.total_games", PROFILE_RANK_MIN_GAMES),
    }

    metrics: Dict[str, Dict[str, Optional[float]]] = {}
    for key in rank_rules:
        value = float(target[key] or 0)
        count_row = query_one(conn, f"SELECT COUNT(*) AS c FROM user_stats_latest WHERE {key} IS NOT NULL")
        le_row = query_one(conn, f"SELECT COUNT(*) AS c FROM user_stats_latest WHERE COALESCE({key}, 0) <= ?", (value,))
        total = int(count_row["c"] or 0) if count_row else 0
        le_count = int(le_row["c"] or 0) if le_row else 0
        percentile = round((le_count / total) * 100.0, 2) if total else None

        score_col, games_col, min_games = rank_rules[key]
        rank_row = query_one(
            conn,
            f"""
            SELECT
                CASE
                    WHEN ? > 0 AND ? >= ? THEN
                        1 + SUM(CASE WHEN COALESCE({score_col}, 0) > ? THEN 1 ELSE 0 END)
                    ELSE NULL
                END AS rank,
                SUM(
                    CASE
                        WHEN COALESCE({score_col}, 0) > 0
                         AND COALESCE({games_col}, 0) >= ?
                        THEN 1 ELSE 0
                    END
                ) AS total_ranked
            FROM users u
            JOIN user_stats_latest s ON s.username = u.username
            WHERE u.status = 'active'
            """,
            (value, float(target[games_col.replace("s.", "")] or 0), min_games, value, min_games),
        )
        rank = int(rank_row["rank"]) if rank_row and rank_row["rank"] is not None else None
        total_ranked = int(rank_row["total_ranked"] or 0) if rank_row else 0

        metrics[key] = {
            "value": value,
            "percentile": percentile,
            "rank": rank,
            "total_ranked": total_ranked,
            "rank_min_games": min_games,
        }
    return {"username": username, "metrics": metrics}


def build_analytics_pack_payload(conn: Any) -> Dict[str, object]:
    distribution_rows = query_all(
        conn,
        """
        SELECT
            (CAST(s.rapid_rating / 100 AS INT) * 100) AS bucket,
            COUNT(*) AS players
        FROM users u
        JOIN user_stats_latest s ON s.username = u.username
        WHERE u.status='active' AND s.rapid_rating > 0
        GROUP BY bucket
        ORDER BY bucket
        """,
    )
    format_summary_row = query_one(
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
        """,
    )
    activity_bucket_rows = query_all(
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
        """,
    )
    scatter_rows = query_all(
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
        LIMIT 1200
        """,
    )

    return {
        "distribution": {"items": [dict(r) for r in distribution_rows]},
        "formatSummary": {
            "items": [
                {"format": "rapid", "games": int(format_summary_row["rapid_games"] or 0), "avg_rating": float(format_summary_row["rapid_avg"] or 0)},
                {"format": "blitz", "games": int(format_summary_row["blitz_games"] or 0), "avg_rating": float(format_summary_row["blitz_avg"] or 0)},
                {"format": "bullet", "games": int(format_summary_row["bullet_games"] or 0), "avg_rating": float(format_summary_row["bullet_avg"] or 0)},
                {"format": "daily", "games": int(format_summary_row["daily_games"] or 0), "avg_rating": float(format_summary_row["daily_avg"] or 0)},
                {"format": "puzzle", "games": 0, "avg_rating": float(format_summary_row["puzzle_avg"] or 0)},
            ]
        },
        "activityBuckets": {"items": [dict(r) for r in activity_bucket_rows]},
        "scatter": {"items": [dict(r) for r in scatter_rows]},
        "correlation": build_correlation_matrix_payload(conn),
        "percentileBands": build_percentile_bands_payload(conn),
        "cohorts": build_cohort_retention_payload(conn, months=24),
        "story": build_story_report_payload(conn),
    }


def refresh_cached_analytics(settings: Settings, source: str) -> List[str]:
    refreshed: List[str] = []
    with get_conn(settings) as conn:
        payloads = {
            "stats:correlation-matrix": build_correlation_matrix_payload(conn),
            "stats:percentile-bands": build_percentile_bands_payload(conn),
            "stats:cohort-retention:24": build_cohort_retention_payload(conn, months=24),
            "stats:story-report": build_story_report_payload(conn),
            "stats:analytics-pack": build_analytics_pack_payload(conn),
        }
        conn.execute("BEGIN")
        for cache_key, payload in payloads.items():
            upsert_cached_payload(conn, cache_key, payload, source=source, commit=False)
            refreshed.append(cache_key)
        conn.commit()
    return refreshed


def get_or_build_cached_payload(
    settings: Settings,
    cache_key: str,
    builder,
    source: str,
) -> Dict[str, object]:
    with get_conn(settings) as conn:
        cached = get_cached_payload(conn, cache_key)
        if cached:
            return cached["payload"]
        payload = builder(conn)
        upsert_cached_payload(conn, cache_key, payload, source=source)
        return payload
