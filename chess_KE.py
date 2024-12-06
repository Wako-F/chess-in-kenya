import pandas as pd
import time
import logging
from datetime import datetime, timezone
from chess_kenya import fetch_kenyan_players, fetch_player_stats

# Constants
CSV_FILENAME = "kenyan_players.csv"
LOG_FILENAME = "chess_data_collection.log"
SAVE_INTERVAL = 50  # Save progress after every 50 players

# Logging setup
logging.basicConfig(
    filename=LOG_FILENAME,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Convert Unix timestamp to readable datetime
def convert_to_datetime(unix_time):
    if unix_time:
        return datetime.fromtimestamp(unix_time, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    return None

# Fetch player stats with error handling
def fetch_player_stats_safe(username):
    # headers = {"User-Agent": "ChessKenyaDataCollector/1.0"}
    for attempt in range(3):  # Retry up to 3 times
        try:
            stats = fetch_player_stats(username)
            logging.info(f"Fetched stats for {username}")
            return stats
        except Exception as e:
            logging.warning(f"Error fetching stats for {username} (Attempt {attempt + 1}): {e}")
            time.sleep(2)  # Short delay before retrying
    logging.error(f"Failed to fetch stats for {username} after 3 attempts.")
    return None

# Fetch list of recently active Kenyan players
def fetch_recent_players():
    try:
        players = fetch_kenyan_players()
        logging.info(f"Fetched {len(players)} recently active players.")
        return players
    except Exception as e:
        logging.error(f"Error fetching recent players: {e}")
        return []

# Extract and structure player data
def extract_player_data(username, stats):
    return {
        "username": username,
        "join_date": convert_to_datetime(stats.get("join_date")),
        "last_online": convert_to_datetime(stats.get("last_online")),
        "daily_games": stats.get("chess_daily", {}).get("record", {}).get("win", 0) +
                       stats.get("chess_daily", {}).get("record", {}).get("loss", 0) +
                       stats.get("chess_daily", {}).get("record", {}).get("draw", 0),
        "daily_rating": stats.get("chess_daily", {}).get("last", {}).get("rating"),
        "rapid_games": stats.get("chess_rapid", {}).get("record", {}).get("win", 0) +
                       stats.get("chess_rapid", {}).get("record", {}).get("loss", 0) +
                       stats.get("chess_rapid", {}).get("record", {}).get("draw", 0),
        "rapid_rating": stats.get("chess_rapid", {}).get("last", {}).get("rating"),
        "blitz_games": stats.get("chess_blitz", {}).get("record", {}).get("win", 0) +
                       stats.get("chess_blitz", {}).get("record", {}).get("loss", 0) +
                       stats.get("chess_blitz", {}).get("record", {}).get("draw", 0),
        "blitz_rating": stats.get("chess_blitz", {}).get("last", {}).get("rating"),
        "bullet_games": stats.get("chess_bullet", {}).get("record", {}).get("win", 0) +
                        stats.get("chess_bullet", {}).get("record", {}).get("loss", 0) +
                        stats.get("chess_bullet", {}).get("record", {}).get("draw", 0),
        "bullet_rating": stats.get("chess_bullet", {}).get("last", {}).get("rating")
    }

# Save collected data to a CSV file
def save_data(data, filename):
    try:
        data.to_csv(filename, index=False)
        logging.info(f"Saved data for {len(data)} players to {filename}")
    except Exception as e:
        logging.error(f"Error saving data to {filename}: {e}")

# Main data collection and update function
def collect_and_update_data():
    logging.info("Starting data collection process.")

    # Step 1: Load existing data
    try:
        existing_data = pd.read_csv(CSV_FILENAME)
        existing_usernames = set(existing_data["username"])
        logging.info(f"Loaded existing data: {len(existing_usernames)} players.")
    except FileNotFoundError:
        logging.info(f"No existing data found. Starting fresh.")
        existing_data = pd.DataFrame(columns=[
            "username", "join_date", "last_online", "daily_games", "daily_rating",
            "rapid_games", "rapid_rating", "blitz_games", "blitz_rating", "bullet_games", "bullet_rating"
        ])
        existing_usernames = set()

    # Step 2: Fetch recent players
    recent_players = fetch_recent_players()
    if not recent_players:
        logging.warning("No players fetched. Exiting data collection process.")
        return

    recent_usernames = set(recent_players)
    updated_data = existing_data.copy()

    # Step 3: Update or add player stats
    requests_count = 0
    for i, username in enumerate(recent_players):
        if username in existing_usernames:
            # Update existing player stats
            stats = fetch_player_stats_safe(username)
            if stats:
                player_data = extract_player_data(username, stats)
                updated_data.loc[updated_data["username"] == username] = player_data
        else:
            # Add new player
            stats = fetch_player_stats_safe(username)
            if stats:
                player_data = extract_player_data(username, stats)
                updated_data = pd.concat([updated_data, pd.DataFrame([player_data])], ignore_index=True)

        requests_count += 1
        # Staggered save
        if (i + 1) % SAVE_INTERVAL == 0:
            logging.info(f"Saving progress after processing {i + 1} players.")
            save_data(updated_data, CSV_FILENAME)

    # Step 4: Drop players not in the recent list
    updated_data = updated_data[updated_data["username"].isin(recent_usernames)]
    logging.info(f"Removed players not in the recent list. Remaining: {len(updated_data)} players.")

    # Final save
    logging.info("Final save after data collection.")
    save_data(updated_data, CSV_FILENAME)
    logging.info("Data collection and update process completed successfully.")

# Run the script
if __name__ == "__main__":
    collect_and_update_data()
