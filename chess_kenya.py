import requests
import csv
import time
import logging
import os

# Configure logging
logging.basicConfig(
    filename="chess_kenya.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Constants
BASE_URL = "https://api.chess.com/pub"
COUNTRY_PLAYERS_URL = f"{BASE_URL}/country/KE/players"
CSV_FILENAME = "kenyan_chess_players_partial.csv"
HEADERS = {
    "User-Agent": "Chess-in-Kenya (Contact: wakokunu@gmail.com)"
}

# Function to fetch Kenyan player usernames
def fetch_kenyan_players():
    try:
        response = requests.get(COUNTRY_PLAYERS_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json().get('players', [])
    except Exception as e:
        logging.error(f"Error fetching Kenyan players: {e}")
        return []

# Function to fetch player profile data
def fetch_player_profile(username):
    try:
        profile_url = f"{BASE_URL}/player/{username}"
        response = requests.get(profile_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"Error fetching profile for {username}: {e}")
        return {}

# Function to fetch player stats data
def fetch_player_stats(username):
    try:
        stats_url = f"{BASE_URL}/player/{username}/stats"
        response = requests.get(stats_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"Error fetching stats for {username}: {e}")
        return {}

# Function to save data to a CSV file
def save_to_csv(data, filename):
    try:
        fieldnames = [
            "username", "title", "join_date", "last_online",
            "bullet_rating", "blitz_rating", "rapid_rating", "fide_rating"
        ]
        write_header = not os.path.exists(filename)  # Write header only if file doesn't exist
        with open(filename, "a", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if write_header:
                writer.writeheader()
            writer.writerows(data)
        logging.info(f"Saved {len(data)} records to {filename}")
    except Exception as e:
        logging.error(f"Error saving data to CSV: {e}")

# Function to load existing data to avoid duplicates
def load_existing_data(filename):
    if not os.path.exists(filename):
        return set()
    try:
        with open(filename, "r") as csvfile:
            reader = csv.DictReader(csvfile)
            return {row["username"] for row in reader}
    except Exception as e:
        logging.error(f"Error loading existing data from {filename}: {e}")
        return set()

# Main function
def main():
    # Fetch Kenyan players
    logging.info("Starting to fetch Kenyan players")
    players = fetch_kenyan_players()
    if not players:
        logging.error("No players found. Exiting.")
        return

    # Load existing data
    existing_usernames = load_existing_data(CSV_FILENAME)
    logging.info(f"Loaded {len(existing_usernames)} existing players")

    # List to store processed data
    data = []

    # Process each player
    for count, username in enumerate(players, 1):
        if username in existing_usernames:
            logging.info(f"Skipping already processed player: {username}")
            continue

        logging.info(f"Processing player: {username}")
        profile = fetch_player_profile(username)
        stats = fetch_player_stats(username)

        # Extract relevant details
        username = profile.get("username", "N/A")
        join_date = profile.get("joined", "N/A")
        last_online = profile.get("last_online", "N/A")
        title = profile.get("title", "N/A")
        bullet_rating = stats.get("chess_bullet", {}).get("last", {}).get("rating", "N/A")
        blitz_rating = stats.get("chess_blitz", {}).get("last", {}).get("rating", "N/A")
        rapid_rating = stats.get("chess_rapid", {}).get("last", {}).get("rating", "N/A")
        fide_rating = stats.get("fide", "N/A")

        # Append to data list
        data.append({
            "username": username,
            "title": title,
            "join_date": join_date,
            "last_online": last_online,
            "bullet_rating": bullet_rating,
            "blitz_rating": blitz_rating,
            "rapid_rating": rapid_rating,
            "fide_rating": fide_rating
        })

        # Save to a partial CSV file every 100 players or at the end
        if count % 100 == 0 or count == len(players):
            save_to_csv(data, CSV_FILENAME)
            data = []  # Clear the data list to avoid duplication

        # Respect API rate limits
        time.sleep(1)

    # Final save if there's unsaved data
    if data:
        save_to_csv(data, CSV_FILENAME)

if __name__ == "__main__":
    main()
