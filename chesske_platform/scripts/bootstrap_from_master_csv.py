import argparse
import os
from datetime import datetime, timezone
from typing import Iterable, Optional

import pandas as pd

from chesske_platform.chesske.analytics import refresh_cached_analytics
from chesske_platform.chesske.config import Settings
from chesske_platform.chesske.db import get_conn, init_db, utc_now_iso
from chesske_platform.chesske.repository import upsert_user_and_stats


COLUMN_ALIASES = {
    "username": "username",
    "join_date": "join_date",
    "join date": "join_date",
    "last_online": "last_online",
    "last online": "last_online",
    "total_games": "total_games",
    "total games played": "total_games",
    "total_daily": "total_daily",
    "total daily games": "total_daily",
    "total_rapid": "total_rapid",
    "total rapid games": "total_rapid",
    "total_bullet": "total_bullet",
    "total bullet games": "total_bullet",
    "total_blitz": "total_blitz",
    "total blitz games": "total_blitz",
    "daily_rating": "daily_rating",
    "daily rating": "daily_rating",
    "rapid_rating": "rapid_rating",
    "rapid rating": "rapid_rating",
    "bullet_rating": "bullet_rating",
    "bullet rating": "bullet_rating",
    "blitz_rating": "blitz_rating",
    "blitz rating": "blitz_rating",
    "highest_puzzle_rating": "highest_puzzle_rating",
    "puzzle_rating": "highest_puzzle_rating",
    "puzzle rating": "highest_puzzle_rating",
    "highest_puzzle_date": "highest_puzzle_date",
    "date": "highest_puzzle_date",
    "daily_wins": "daily_wins",
    "daily wins": "daily_wins",
    "daily_losses": "daily_losses",
    "daily losses": "daily_losses",
    "daily_draws": "daily_draws",
    "daily draws": "daily_draws",
    "rapid_wins": "rapid_wins",
    "rapid wins": "rapid_wins",
    "rapid_losses": "rapid_losses",
    "rapid losses": "rapid_losses",
    "rapid_draws": "rapid_draws",
    "rapid draws": "rapid_draws",
    "bullet_wins": "bullet_wins",
    "bullet wins": "bullet_wins",
    "bullet_losses": "bullet_losses",
    "bullet losses": "bullet_losses",
    "bullet_draws": "bullet_draws",
    "bullet draws": "bullet_draws",
    "blitz_wins": "blitz_wins",
    "blitz wins": "blitz_wins",
    "blitz_losses": "blitz_losses",
    "blitz losses": "blitz_losses",
    "blitz_draws": "blitz_draws",
    "blitz draws": "blitz_draws",
}


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {}
    for col in df.columns:
        key = str(col).strip().lower().replace("-", "_")
        key = " ".join(key.split())
        canonical = COLUMN_ALIASES.get(key) or COLUMN_ALIASES.get(key.replace("_", " "))
        if canonical:
            rename_map[col] = canonical
    return df.rename(columns=rename_map)


def _to_iso(value):
    if pd.isna(value):
        return None
    parsed = pd.to_datetime(value, errors="coerce", utc=True)
    if pd.isna(parsed):
        return None
    return parsed.to_pydatetime().isoformat()


def _iter_clean_chunks(csv_path: str, limit: Optional[int], chunk_size: int = 5000) -> Iterable[pd.DataFrame]:
    yielded = 0
    for chunk in pd.read_csv(csv_path, low_memory=False, chunksize=chunk_size):
        df = _normalize_columns(chunk)
        for col in [
            "username",
            "join_date",
            "last_online",
            "total_games",
            "total_daily",
            "total_rapid",
            "total_bullet",
            "total_blitz",
            "daily_rating",
            "rapid_rating",
            "bullet_rating",
            "blitz_rating",
            "highest_puzzle_rating",
            "highest_puzzle_date",
            "daily_wins",
            "daily_losses",
            "daily_draws",
            "rapid_wins",
            "rapid_losses",
            "rapid_draws",
            "bullet_wins",
            "bullet_losses",
            "bullet_draws",
            "blitz_wins",
            "blitz_losses",
            "blitz_draws",
        ]:
            if col not in df.columns:
                df[col] = None

        df["username"] = df["username"].astype(str).str.strip().str.lower()
        df = df[df["username"].ne("")]
        df = df[~df["username"].str.contains(r"<<<<<<<|=======|>>>>>>>", regex=True, na=False)]
        df["_last_online_sort"] = pd.to_datetime(df["last_online"], errors="coerce", utc=True)
        df = df.sort_values(["username", "_last_online_sort"], ascending=[True, False])
        df = df.drop_duplicates(subset=["username"], keep="first")
        if limit is not None and limit > 0:
            remaining = limit - yielded
            if remaining <= 0:
                break
            df = df.head(remaining)
        if df.empty:
            continue
        yielded += len(df)
        yield df
        if limit is not None and yielded >= limit:
            break


def bootstrap_from_csv(
    settings: Settings,
    csv_path: str,
    reset_db: bool = False,
    limit: Optional[int] = None,
) -> int:
    reset_via_truncate = False
    if reset_db and settings.resolved_db_path.exists():
        try:
            os.remove(settings.resolved_db_path)
        except PermissionError:
            reset_via_truncate = True
    init_db(settings)

    loaded = 0
    with get_conn(settings) as conn:
        if reset_via_truncate:
            conn.executescript(
                """
                DELETE FROM run_errors;
                DELETE FROM pipeline_runs;
                DELETE FROM country_active_snapshots;
                DELETE FROM user_stats_latest;
                DELETE FROM users;
                """
            )
            conn.commit()
        if getattr(conn, "backend", "sqlite") == "sqlite":
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("BEGIN")
        for df in _iter_clean_chunks(csv_path, limit):
            for row in df.itertuples(index=False):
                record = {
                    "join_date": _to_iso(getattr(row, "join_date", None)),
                    "last_online": _to_iso(getattr(row, "last_online", None)),
                    "total_games": getattr(row, "total_games", None),
                    "total_daily": getattr(row, "total_daily", None),
                    "total_rapid": getattr(row, "total_rapid", None),
                    "total_bullet": getattr(row, "total_bullet", None),
                    "total_blitz": getattr(row, "total_blitz", None),
                    "daily_rating": getattr(row, "daily_rating", None),
                    "rapid_rating": getattr(row, "rapid_rating", None),
                    "bullet_rating": getattr(row, "bullet_rating", None),
                    "blitz_rating": getattr(row, "blitz_rating", None),
                    "highest_puzzle_rating": getattr(row, "highest_puzzle_rating", None),
                    "highest_puzzle_date": _to_iso(getattr(row, "highest_puzzle_date", None)),
                    "daily_wins": getattr(row, "daily_wins", None),
                    "daily_losses": getattr(row, "daily_losses", None),
                    "daily_draws": getattr(row, "daily_draws", None),
                    "rapid_wins": getattr(row, "rapid_wins", None),
                    "rapid_losses": getattr(row, "rapid_losses", None),
                    "rapid_draws": getattr(row, "rapid_draws", None),
                    "bullet_wins": getattr(row, "bullet_wins", None),
                    "bullet_losses": getattr(row, "bullet_losses", None),
                    "bullet_draws": getattr(row, "bullet_draws", None),
                    "blitz_wins": getattr(row, "blitz_wins", None),
                    "blitz_losses": getattr(row, "blitz_losses", None),
                    "blitz_draws": getattr(row, "blitz_draws", None),
                }
                upsert_user_and_stats(conn, getattr(row, "username"), record, seen_in_active=False, commit=False)
                loaded += 1
                if loaded % 2000 == 0:
                    conn.commit()
                    conn.execute("BEGIN")
                if loaded % 10000 == 0:
                    print(f"Loaded {loaded} users...")
        snapshot_date = datetime.now(timezone.utc).date().isoformat()
        inserted_at = utc_now_iso()
        conn.execute(
            """
            INSERT OR IGNORE INTO country_active_snapshots (snapshot_date, username, inserted_at)
            SELECT ?, username, ?
            FROM users
            WHERE status = 'active'
            """,
            (snapshot_date, inserted_at),
        )
        active_users = conn.execute("SELECT COUNT(*) AS c FROM users WHERE status='active'").fetchone()["c"]
        started_at = utc_now_iso()
        ended_at = utc_now_iso()
        conn.execute(
            """
            INSERT INTO pipeline_runs (
                started_at, ended_at, status, active_count, updated_count,
                deleted_count, refresh_count, error_count, notes
            ) VALUES (?, ?, 'success', ?, ?, 0, 0, 0, ?)
            """,
            (
                started_at,
                ended_at,
                int(active_users or 0),
                int(loaded or 0),
                f"bootstrap_from_csv:{csv_path}",
            ),
        )
        conn.commit()

    refresh_cached_analytics(settings, source=f"bootstrap-csv:{os.path.basename(csv_path)}")
    return loaded


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap ChessKE DB from master CSV.")
    parser.add_argument(
        "--csv",
        default="master_chess_players.csv",
        help="Path to legacy master csv",
    )
    parser.add_argument(
        "--reset-db",
        action="store_true",
        help="Delete existing database before bootstrap.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Optional maximum number of deduplicated users to load (0 = all).",
    )
    args = parser.parse_args()

    settings = Settings()
    loaded = bootstrap_from_csv(
        settings,
        csv_path=args.csv,
        reset_db=args.reset_db,
        limit=(args.limit if args.limit and args.limit > 0 else None),
    )
    print(
        f"Bootstrap complete: {loaded} users loaded at {datetime.now(timezone.utc).isoformat()}"
    )


if __name__ == "__main__":
    main()
