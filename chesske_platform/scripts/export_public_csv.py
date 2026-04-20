import pandas as pd

from chesske_platform.chesske.config import Settings
from chesske_platform.chesske.db import get_conn, init_db


LEDGER_PATH = "cleaned_master_chess_players.csv"


def _merge_with_existing_ledger(fresh_df: pd.DataFrame, ledger_path: str = LEDGER_PATH) -> pd.DataFrame:
    fresh = fresh_df.copy()
    if "Username" in fresh.columns:
        fresh["Username"] = fresh["Username"].astype(str)

    try:
        existing = pd.read_csv(ledger_path)
    except FileNotFoundError:
        return fresh
    except pd.errors.EmptyDataError:
        return fresh

    if existing.empty:
        return fresh
    if "Username" not in existing.columns:
        return fresh

    existing = existing.copy()
    existing["Username"] = existing["Username"].astype(str)

    # Keep schema stable while allowing drift in either source.
    all_columns = list(existing.columns)
    for col in fresh.columns:
        if col not in all_columns:
            all_columns.append(col)
    for col in all_columns:
        if col not in existing.columns:
            existing[col] = pd.NA
        if col not in fresh.columns:
            fresh[col] = pd.NA

    existing = existing[all_columns]
    fresh = fresh[all_columns]

    merged = pd.concat([existing, fresh], ignore_index=True)
    merged = merged.drop_duplicates(subset=["Username"], keep="last")

    return merged


def main() -> None:
    settings = Settings()
    init_db(settings)
    with get_conn(settings) as conn:
        df = pd.read_sql_query(
            """
            SELECT
                u.username AS "Username",
                u.joined_at AS "Join Date",
                u.last_online AS "Last Online",
                s.total_games AS "Total Games Played",
                s.total_daily AS "Total Daily Games",
                s.total_rapid AS "Total Rapid Games",
                s.total_bullet AS "Total Bullet Games",
                s.total_blitz AS "Total Blitz Games",
                s.daily_rating AS "Daily Rating",
                s.rapid_rating AS "Rapid Rating",
                s.bullet_rating AS "Bullet Rating",
                s.blitz_rating AS "Blitz Rating",
                s.highest_puzzle_rating AS "Puzzle Rating",
                s.highest_puzzle_date AS "Date",
                s.daily_wins AS "Daily Wins",
                s.daily_losses AS "Daily Losses",
                s.daily_draws AS "Daily Draws",
                s.rapid_wins AS "Rapid Wins",
                s.rapid_losses AS "Rapid Losses",
                s.rapid_draws AS "Rapid Draws",
                s.bullet_wins AS "Bullet Wins",
                s.bullet_losses AS "Bullet Losses",
                s.bullet_draws AS "Bullet Draws",
                s.blitz_wins AS "Blitz Wins",
                s.blitz_losses AS "Blitz Losses",
                s.blitz_draws AS "Blitz Draws"
            FROM users u
            JOIN user_stats_latest s ON s.username = u.username
            WHERE u.status = 'active'
            ORDER BY u.username
            """,
            conn,
        )

    for fmt in ["Daily", "Rapid", "Bullet", "Blitz"]:
        total_col = f"Total {fmt} Games"
        df[f"{fmt} Win Percentage"] = ((df[f"{fmt} Wins"] / df[total_col].replace(0, pd.NA)) * 100).fillna(0).round(0).astype(int)
        df[f"{fmt} Loss Percentage"] = ((df[f"{fmt} Losses"] / df[total_col].replace(0, pd.NA)) * 100).fillna(0).round(0).astype(int)
        df[f"{fmt} Draw Percentage"] = ((df[f"{fmt} Draws"] / df[total_col].replace(0, pd.NA)) * 100).fillna(0).round(0).astype(int)

    merged_df = _merge_with_existing_ledger(df, LEDGER_PATH)
    merged_df.to_csv(LEDGER_PATH, index=False)
    print(f"Exported {LEDGER_PATH}: refreshed={len(df)} total={len(merged_df)}")


if __name__ == "__main__":
    main()
