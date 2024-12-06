import pandas as pd

# Path to your CSV file
file_path = "kenyan_chess_players_partial.csv"

# Load the CSV file
data = pd.read_csv(file_path)

# Columns to remove
columns_to_remove = [
    "fide_rating", "games_bullet", "games_blitz", "games_rapid",
    "total_games", "wins", "losses", "draws", "title"
]

# Drop the columns
data = data.drop(columns=[col for col in columns_to_remove if col in data.columns], errors='ignore')

# Save the updated CSV
data.to_csv(file_path, index=False)

print("Columns removed and file updated successfully!")
