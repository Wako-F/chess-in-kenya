import pandas as pd

file_path = "kenyan_chess_players_partial.csv"

data = pd.read_csv(file_path)

#Convert Unix timestamps
data['join_date'] = pd.to_datetime(data['join_date'], unit='s', errors='coerce')
data['last_online'] = pd.to_datetime(data['last_online'], unit='s', errors='coerce')

#Renaming columns for readability
renamed_columns = {
    "bullet_rating": "Bullet Rating",
    "blitz_rating": "Blitz Rating",
    "rapid_rating": "Rapid Rating",
    "daily_rating": "Daily Rating",
    "total_games": "Total Games Played",
    "total_daily": "Total Daily Games",
    "total_rapid": "Total Rapid Games",
    "total_bullet": "Total Bullet Games",
    "total_blitz": "Total Blitz Games",
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
data.rename(columns=renamed_columns, inplace=True)

#Remove players with all zero ratings from these columns:
rating_columns = ["Bullet Rating", "Blitz Rating", "Rapid Rating", "Daily Rating"]
game_count_columns = [
    "Total Games Played",
    "Total Daily Games",
    "Total Rapid Games",
    "Total Bullet Games",
    "Total Blitz Games",
]

valid_rows = ~((data[rating_columns] == 0).all(axis=1) & (data[game_count_columns] == 0).all(axis=1))
data = data[valid_rows]

#Some derived metrics
formats = ["Daily", "Rapid", "Bullet", "Blitz"]
for fmt in formats:
    data[f"{fmt} Win Percentage"] = (
        data[f"{fmt} Wins"] / data[f"Total {fmt} Games"] * 100
    ).fillna(0).round(0).astype(int)
    data[f"{fmt} Loss Percentage"] = (
        data[f"{fmt} Losses"] / data[f"Total {fmt} Games"] * 100
    ).fillna(0).round(0).astype(int)
    data[f"{fmt} Draw Percentage"] = (
        data[f"{fmt} Draws"] / data[f"Total {fmt} Games"] * 100
    ).fillna(0).round(0).astype(int)

cleaned_file = "cleaned_kenyan_chess_players.csv"
data.to_csv(cleaned_file, index=False)
print("Success!")

print(data.head())