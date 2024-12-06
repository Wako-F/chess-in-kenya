import pandas as pd
import requests
import logging
import os

# Configure logging
logging.basicConfig(
    filename="update_existing_data.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Constants
BASE_URL = "https://api.chess.com/pub"
CSV_FILENAME = "kenyan_chess_players_partial.csv"
HEADERS = {
    "User-Agent": "Chess-in-Kenya (Contact: wakokunu@gmail.com)"
}
SAVE_INTERVAL = 100  # Save progress after every 100 players

# Function to fetch join date for a player
def fetch_join_date(username):
    try:
        profile_url = f"{BASE_URL}/player/{username}"
        response = requests.get(profile_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        join_date_unix = response.json().get("joined", None)
        if join_date_unix:
            # Convert UNIX timestamp to human-readable date
            join_date = pd.to_datetime(join_date_unix, unit='s')
            return join_date
        return None
    except Exception as e:
        logging.error(f"Error fetching join date for {username}: {e}")
        return None

def save_progress(data, filename):
    try:
        data.to_csv(filename, index=False)
        logging.info(f"Data successfully saved to {filename}")
    except Exception as e:
        logging.error(f"Error saving data to CSV: {e}")

def main():
    if not os.path.exists(CSV_FILENAME):
        logging.error(f"{CSV_FILENAME} does not exist. Exiting.")
        return

    # Load existing data
    data = pd.read_csv(CSV_FILENAME)

    # Ensure 'join_date' is datetime-compatible
    if 'join_date' in data.columns:
        # Convert Unix timestamps to datetime
        data['join_date'] = pd.to_datetime(data['join_date'], unit='s', errors='coerce')

    # Create 'join_date' column if it doesn't exist
    else:
        data['join_date'] = pd.NaT  # Initialize as Not a Time (NaT) for datetime values

    # Fetch and add missing join dates
    for idx, row in data.iterrows():
        if pd.isnull(row.get('join_date')):
            logging.info(f"Fetching join date for player: {row['username']}")
            join_date = fetch_join_date(row['username'])
            if join_date:
                data.at[idx, 'join_date'] = join_date  # Assign fetched datetime value

        # Staggered saving: Save progress every SAVE_INTERVAL rows
        if idx > 0 and idx % SAVE_INTERVAL == 0:
            save_progress(data, CSV_FILENAME)
            logging.info(f"Staggered save: Processed {idx} players so far")

    # Final save to ensure all data is written
    save_progress(data, CSV_FILENAME)
    logging.info("All data updated and saved successfully.")

if __name__ == "__main__":
    main()
