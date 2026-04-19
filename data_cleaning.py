import pandas as pd

MASTER_FILE = "master_chess_players.csv"
OUTPUT_FILE = "cleaned_master_chess_players.csv"

SOURCE_COLUMNS = [
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
]

RENAMED_COLUMNS = {
    "username": "Username",
    "join_date": "Join Date",
    "last_online": "Last Online",
    "total_games": "Total Games Played",
    "total_daily": "Total Daily Games",
    "total_rapid": "Total Rapid Games",
    "total_bullet": "Total Bullet Games",
    "total_blitz": "Total Blitz Games",
    "daily_rating": "Daily Rating",
    "rapid_rating": "Rapid Rating",
    "bullet_rating": "Bullet Rating",
    "blitz_rating": "Blitz Rating",
    "highest_puzzle_rating": "Puzzle Rating",
    "highest_puzzle_date": "Date",
    "daily_wins": "Daily Wins",
    "daily_losses": "Daily Losses",
    "daily_draws": "Daily Draws",
    "rapid_wins": "Rapid Wins",
    "rapid_losses": "Rapid Losses",
    "rapid_draws": "Rapid Draws",
    "bullet_wins": "Bullet Wins",
    "bullet_losses": "Bullet Losses",
    "bullet_draws": "Bullet Draws",
    "blitz_wins": "Blitz Wins",
    "blitz_losses": "Blitz Losses",
    "blitz_draws": "Blitz Draws",
}


def _sanitize_source(df: pd.DataFrame) -> pd.DataFrame:
    for col in SOURCE_COLUMNS:
        if col not in df.columns:
            df[col] = None
    df = df[SOURCE_COLUMNS].copy()

    df["username"] = df["username"].astype(str).str.strip().str.lower()
    df = df[df["username"].ne("")]
    df = df[~df["username"].str.contains(r"<<<<<<<|=======|>>>>>>>", regex=True, na=False)]

    last_online_dt = pd.to_datetime(df["last_online"], errors="coerce")
    df = df.assign(_last_online=last_online_dt)
    df = df.sort_values(["username", "_last_online"], ascending=[True, False])
    df = df.drop_duplicates(subset=["username"], keep="first").drop(columns=["_last_online"])
    return df


def main() -> None:
    data = pd.read_csv(MASTER_FILE)
    data = _sanitize_source(data)

    if "highest_puzzle_date" in data.columns:
        data["highest_puzzle_date"] = pd.to_datetime(
            data["highest_puzzle_date"], errors="coerce"
        )

    data.rename(columns=RENAMED_COLUMNS, inplace=True)

    for fmt in ["Daily", "Rapid", "Bullet", "Blitz"]:
        total_col = f"Total {fmt} Games"
        wins_col = f"{fmt} Wins"
        losses_col = f"{fmt} Losses"
        draws_col = f"{fmt} Draws"

        total = pd.to_numeric(data[total_col], errors="coerce").fillna(0)
        wins = pd.to_numeric(data[wins_col], errors="coerce").fillna(0)
        losses = pd.to_numeric(data[losses_col], errors="coerce").fillna(0)
        draws = pd.to_numeric(data[draws_col], errors="coerce").fillna(0)

        data[f"{fmt} Win Percentage"] = ((wins / total.replace(0, pd.NA)) * 100).fillna(0).round(0).astype(int)
        data[f"{fmt} Loss Percentage"] = ((losses / total.replace(0, pd.NA)) * 100).fillna(0).round(0).astype(int)
        data[f"{fmt} Draw Percentage"] = ((draws / total.replace(0, pd.NA)) * 100).fillna(0).round(0).astype(int)

    data = data.sort_values("Username").reset_index(drop=True)
    data.to_csv(OUTPUT_FILE, index=False)
    print(f"Wrote {len(data)} rows to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
