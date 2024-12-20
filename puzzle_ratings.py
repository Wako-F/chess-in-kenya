import requests
import pandas as pd
import time
import logging

# Configure logging
logging.basicConfig(
    filename="update_puzzle_data.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

BASE_URL = "https://api.chess.com/pub"
HEADERS = {"User-Agent": "ChessPuzzleRatingsUpdater (contact: wakokunu@gmail.com)"}

# Function to fetch puzzle data for a single username
def fetch_puzzle_data(username):
    try:
        stats_url = f"{BASE_URL}/player/{username}/stats"
        response = requests.get(stats_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        stats = response.json()

        # Extract puzzle data
        tactics = stats.get("tactics", {})
        highest_puzzle_rating = tactics.get("highest", {}).get("rating", None)
        highest_puzzle_date = tactics.get("highest", {}).get("date", None)

        return highest_puzzle_rating, highest_puzzle_date
    except Exception as e:
        logging.error(f"Error fetching puzzle data for {username}: {e}")
        return None, None

# Load the existing CSV file
def load_data(filename):
    try:
        return pd.read_csv(filename)
    except Exception as e:
        logging.error(f"Error loading {filename}: {e}")
        return pd.DataFrame()

# Save the updated data back to the CSV
def save_data(data, filename):
    try:
        data.to_csv(filename, index=False)
        logging.info(f"Data saved to {filename}")
    except Exception as e:
        logging.error(f"Error saving data to {filename}: {e}")

# Main script
def main():
    input_file = "kenyan_chess_players_partial.csv"
    output_file = "kenyan_chess_players_partial.csv"

    # Load existing data
    data = load_data(input_file)

    if data.empty:
        logging.error("No data loaded. Exiting.")
        return

    # Ensure the columns for puzzle data exist
    if "highest_puzzle_rating" not in data.columns:
        data["highest_puzzle_rating"] = None
    if "highest_puzzle_date" not in data.columns:
        data["highest_puzzle_date"] = None

    # Iterate over usernames and fetch puzzle data
    for idx, row in data.iterrows():
        username = row["username"]
        if pd.isna(row["highest_puzzle_rating"]):  # Skip if data already exists
            logging.info(f"Fetching puzzle data for {username}")
            highest_puzzle_rating, highest_puzzle_date = fetch_puzzle_data(username)

            # Update the DataFrame
            data.at[idx, "highest_puzzle_rating"] = highest_puzzle_rating
            data.at[idx, "highest_puzzle_date"] = highest_puzzle_date

            # Respect API rate limits
            time.sleep(1)

    # Save updated data
    save_data(data, output_file)

if __name__ == "__main__":
    main()
