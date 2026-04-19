import pandas as pd

from chesske_platform.chesske.config import Settings
from chesske_platform.chesske.db import get_conn, init_db


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

    df.to_csv("cleaned_master_chess_players.csv", index=False)
    print(f"Exported cleaned_master_chess_players.csv ({len(df)} rows)")


if __name__ == "__main__":
    main()
