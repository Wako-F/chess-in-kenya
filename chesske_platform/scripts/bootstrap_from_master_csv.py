import argparse
import os
from datetime import datetime, timezone
from typing import Optional

import pandas as pd

from chesske_platform.chesske.config import Settings
from chesske_platform.chesske.db import get_conn, init_db
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

    df = pd.read_csv(csv_path, low_memory=False)
    df = _normalize_columns(df)
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
        df = df.head(limit)

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
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("BEGIN")
        for _, row in df.iterrows():
            record = {
                "join_date": _to_iso(row.get("join_date")),
                "last_online": _to_iso(row.get("last_online")),
                "total_games": row.get("total_games"),
                "total_daily": row.get("total_daily"),
                "total_rapid": row.get("total_rapid"),
                "total_bullet": row.get("total_bullet"),
                "total_blitz": row.get("total_blitz"),
                "daily_rating": row.get("daily_rating"),
                "rapid_rating": row.get("rapid_rating"),
                "bullet_rating": row.get("bullet_rating"),
                "blitz_rating": row.get("blitz_rating"),
                "highest_puzzle_rating": row.get("highest_puzzle_rating"),
                "highest_puzzle_date": _to_iso(row.get("highest_puzzle_date")),
                "daily_wins": row.get("daily_wins"),
                "daily_losses": row.get("daily_losses"),
                "daily_draws": row.get("daily_draws"),
                "rapid_wins": row.get("rapid_wins"),
                "rapid_losses": row.get("rapid_losses"),
                "rapid_draws": row.get("rapid_draws"),
                "bullet_wins": row.get("bullet_wins"),
                "bullet_losses": row.get("bullet_losses"),
                "bullet_draws": row.get("bullet_draws"),
                "blitz_wins": row.get("blitz_wins"),
                "blitz_losses": row.get("blitz_losses"),
                "blitz_draws": row.get("blitz_draws"),
            }
            upsert_user_and_stats(conn, row["username"], record, seen_in_active=False, commit=False)
            loaded += 1
            if loaded % 2000 == 0:
                conn.commit()
                conn.execute("BEGIN")
            if loaded % 10000 == 0:
                print(f"Loaded {loaded} users...")
        conn.commit()

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
