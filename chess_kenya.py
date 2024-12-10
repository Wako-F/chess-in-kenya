import requests
import pandas as pd
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
SAVE_INTERVAL = 100  # Save progress every 100 players
RATE_LIMIT_DELAY = 1  # Delay between API calls to respect rate limits

# Function to fetch Kenyan player usernames
def fetch_kenyan_players():
    try:
        response = requests.get(COUNTRY_PLAYERS_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json().get('players', [])
    except Exception as e:
        logging.error(f"Error fetching Kenyan players: {e}")
        return []

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

# Fetch join date for a player
def fetch_join_date(username):
    try:
        profile_url = f"{BASE_URL}/player/{username}"
        response = requests.get(profile_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        join_date_unix = response.json().get("joined", None)
        if join_date_unix:
            return pd.to_datetime(join_date_unix, unit='s')
        return None
    except Exception as e:
        logging.error(f"Error fetching join date for {username}: {e}")
        return None
def fetch_last_online(username):
    try:
        profile_url = f"{BASE_URL}/player/{username}"
        response = requests.get(profile_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        last_online_unix = response.json().get("last_online", None)
        if last_online_unix:
            return pd.to_datetime(last_online_unix, unit='s')
        return None
    except Exception as e:
        logging.error(f"Error fetching last online for {username}: {e}")
        return None

# Load existing data
def load_existing_data(filename):
    if not os.path.exists(filename):
        return pd.DataFrame(columns=[
            "username", "join_date", "last_online", "total_games", "total_daily", "total_rapid", "total_bullet", "total_blitz",
            "daily_rating", "rapid_rating", "bullet_rating", "blitz_rating",
            "daily_wins", "daily_losses", "daily_draws",
            "rapid_wins", "rapid_losses", "rapid_draws",
            "bullet_wins", "bullet_losses", "bullet_draws",
            "blitz_wins", "blitz_losses", "blitz_draws"
        ])
    try:
        return pd.read_csv(filename)
    except Exception as e:
        logging.error(f"Error loading existing data from {filename}: {e}")
        return pd.DataFrame()

# Save data to CSV incrementally
def save_to_csv(data, filename):
    try:
        data.to_csv(filename, index=False)
        logging.info(f"Data successfully saved to {filename}")
    except Exception as e:
        logging.error(f"Error saving data to CSV: {e}")

# Extract data for each player
def extract_data(stats, category):
    record = stats.get(category, {}).get("record", {})
    last = stats.get(category, {}).get("last", {})
    wins = record.get("win", 0)
    losses = record.get("loss", 0)
    draws = record.get("draw", 0)
    rating = last.get("rating", 0)
    total = wins + losses + draws
    return total, wins, losses, draws, rating

# Main function
def main():
    # Fetch Kenyan players
    logging.info("Starting to fetch Kenyan players")
    players = fetch_kenyan_players()
    if not players:
        logging.error("No players found. Exiting.")
        return

    # Load existing data
    data = load_existing_data(CSV_FILENAME)

    # Update logic
    existing_usernames = set(data["username"])
    recent_usernames = set(players)
    dropped_players = existing_usernames - recent_usernames
    new_players = recent_usernames - existing_usernames

    # Log dropped and new players
    logging.info(f"Found {len(dropped_players)} players to drop.")
    logging.info(f"Found {len(new_players)} new players to add.")

    # Remove dropped players
    data = data[~data["username"].isin(dropped_players)]

    # Process players
    for count, username in enumerate(players, 1):
        logging.info(f"Processing player: {username}")
        stats = fetch_player_stats(username)

        # Extract stats for all formats
        total_daily, daily_wins, daily_losses, daily_draws, daily_rating = extract_data(stats, "chess_daily")
        total_rapid, rapid_wins, rapid_losses, rapid_draws, rapid_rating = extract_data(stats, "chess_rapid")
        total_bullet, bullet_wins, bullet_losses, bullet_draws, bullet_rating = extract_data(stats, "chess_bullet")
        total_blitz, blitz_wins, blitz_losses, blitz_draws, blitz_rating = extract_data(stats, "chess_blitz")

        # Aggregate total games played
        total_games = total_daily + total_rapid + total_bullet + total_blitz
         # Fetch join date and last online for the player
        join_date = fetch_join_date(username)
        last_online = fetch_last_online(username)
        # Update or add player
        if username in data["username"].values:
            # Update existing player
            data.loc[data["username"] == username, "join_date"] = join_date
            data.loc[data["username"] == username, "last_online"] = last_online
            data.loc[data["username"] == username, "total_games"] = total_games
            data.loc[data["username"] == username, "total_daily"] = total_daily
            data.loc[data["username"] == username, "total_rapid"] = total_rapid
            data.loc[data["username"] == username, "total_bullet"] = total_bullet
            data.loc[data["username"] == username, "total_blitz"] = total_blitz
            data.loc[data["username"] == username, "daily_rating"] = daily_rating
            data.loc[data["username"] == username, "rapid_rating"] = rapid_rating
            data.loc[data["username"] == username, "bullet_rating"] = bullet_rating
            data.loc[data["username"] == username, "blitz_rating"] = blitz_rating
            data.loc[data["username"] == username, "daily_wins"] = daily_wins
            data.loc[data["username"] == username, "daily_losses"] = daily_losses
            data.loc[data["username"] == username, "daily_draws"] = daily_draws
            data.loc[data["username"] == username, "rapid_wins"] = rapid_wins
            data.loc[data["username"] == username, "rapid_losses"] = rapid_losses
            data.loc[data["username"] == username, "rapid_draws"] = rapid_draws
            data.loc[data["username"] == username, "bullet_wins"] = bullet_wins
            data.loc[data["username"] == username, "bullet_losses"] = bullet_losses
            data.loc[data["username"] == username, "bullet_draws"] = bullet_draws
            data.loc[data["username"] == username, "blitz_wins"] = blitz_wins
            data.loc[data["username"] == username, "blitz_losses"] = blitz_losses
            data.loc[data["username"] == username, "blitz_draws"] = blitz_draws
        else:
            # Add new player
            new_row = {
                "username": username,
                "join_date": join_date,
                "last_online": last_online,
                "total_games": total_games,
                "total_daily": total_daily,
                "total_rapid": total_rapid,
                "total_bullet": total_bullet,
                "total_blitz": total_blitz,
                "daily_rating": daily_rating,
                "rapid_rating": rapid_rating,
                "bullet_rating": bullet_rating,
                "blitz_rating": blitz_rating,
                "daily_wins": daily_wins,
                "daily_losses": daily_losses,
                "daily_draws": daily_draws,
                "rapid_wins": rapid_wins,
                "rapid_losses": rapid_losses,
                "rapid_draws": rapid_draws,
                "bullet_wins": bullet_wins,
                "bullet_losses": bullet_losses,
                "bullet_draws": bullet_draws,
                "blitz_wins": blitz_wins,
                "blitz_losses": blitz_losses,
                "blitz_draws": blitz_draws
            }
            data = pd.concat([data, pd.DataFrame([new_row])], ignore_index=True)

        # Respect API rate limits
        time.sleep(RATE_LIMIT_DELAY)

        # Staggered saving: Save after every SAVE_INTERVAL players
        if count % SAVE_INTERVAL == 0:
            save_to_csv(data, CSV_FILENAME)
            logging.info(f"Intermediate save: {count} players processed")

    # Final save
    save_to_csv(data, CSV_FILENAME)
    logging.info("All data updated and saved successfully")

if __name__ == "__main__":
    main()
