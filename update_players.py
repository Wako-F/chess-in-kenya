import pandas as pd
import time
import logging
import os
from datetime import datetime, timezone
from chess_kenya import fetch_kenyan_players, fetch_player_stats, save_to_csv, load_existing_data

# Constants
CSV_FILENAME = "cleaned_kenyan_chess_players.csv"
LOG_FILENAME = "chess_kenya_update.log"
logging.basicConfig(
    filename=LOG_FILENAME,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Function to convert Unix timestamp to datetime
def convert_to_datetime(unix_time):
    if unix_time is not None:
        # Convert Unix timestamp to a timezone-aware UTC datetime
        return datetime.fromtimestamp(unix_time, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    return None


# Function to update player data
def update_player_data():
    # Load existing data
    logging.info("Loading existing data...")
    data = load_existing_data(CSV_FILENAME)

    # Ensure 'username' column exists and normalize
    if 'username' not in data.columns:
        logging.error("The 'username' column is missing in the dataset.")
        return
    data['username'] = data['username'].str.lower()

    # Fetch recent players from the API
    logging.info("Fetching recent Kenyan players...")
    recent_players = fetch_kenyan_players()
    recent_players = [player.lower() for player in recent_players]  # Normalize case

    if not recent_players:
        logging.info("No players fetched. Exiting update process.")
        return

    # Identify new and existing players
    existing_usernames = set(data['username'])
    new_usernames = set(recent_players) - existing_usernames
    existing_usernames_to_update = existing_usernames.intersection(recent_players)

    logging.info(f"Found {len(new_usernames)} new players and {len(existing_usernames_to_update)} existing players to update.")

    # Update existing players
    for count, username in enumerate(existing_usernames_to_update, 1):
        logging.info(f"Updating stats for existing player: {username}")
        stats = fetch_player_stats(username)
        if stats:
            data = update_existing_player(data, username, stats)
        if count % 100 == 0:
            save_to_csv(data, CSV_FILENAME)
            logging.info(f"Intermediate save after {count} updates.")
        time.sleep(1)

    # Add new players
    new_data = []
    for count, username in enumerate(new_usernames, 1):
        logging.info(f"Fetching stats for new player: {username}")
        stats = fetch_player_stats(username)
        if stats:
            new_data.append(extract_player_data(username, stats))
        if count % 100 == 0:
            save_to_csv(data, CSV_FILENAME)
            logging.info(f"Intermediate save after {count} new players.")
        time.sleep(1)

    # Append new data to DataFrame
    if new_data:
        new_df = pd.DataFrame(new_data)
        # Align columns to avoid dropping fields
        for col in data.columns:
            if col not in new_df.columns:
                new_df[col] = None
        data = pd.concat([data, new_df], ignore_index=True)

    # Final save
    save_to_csv(data, CSV_FILENAME)
    logging.info("All data updated and saved successfully.")

# Function to extract player data (matches your field names)
def extract_player_data(username, stats):
    return {
        "username": username,
        "total_games": stats.get("chess_daily", {}).get("record", {}).get("win", 0) +
                       stats.get("chess_daily", {}).get("record", {}).get("loss", 0) +
                       stats.get("chess_daily", {}).get("record", {}).get("draw", 0),
        "daily_rating": stats.get("chess_daily", {}).get("last", {}).get("rating", None),
        "rapid_rating": stats.get("chess_rapid", {}).get("last", {}).get("rating", None),
        "last_online": convert_to_datetime(stats.get("last_online", None)),  # Converttime
        
    }

# Function to update an existing player's data
def update_existing_player(data, username, stats):
    index = data[data['username'] == username].index[0]
    logging.info(f"Updating player {username}. Before: {data.loc[index].to_dict()}")

    # Update fields one by one and log changes
    new_total_games = stats.get("chess_daily", {}).get("record", {}).get("win", 0) + \
                      stats.get("chess_daily", {}).get("record", {}).get("loss", 0) + \
                      stats.get("chess_daily", {}).get("record", {}).get("draw", 0)
    logging.info(f"Updating total_games: {data.at[index, 'total_games']} -> {new_total_games}")
    data.at[index, 'total_games'] = new_total_games

    new_daily_rating = stats.get("chess_daily", {}).get("last", {}).get("rating", None)
    logging.info(f"Updating daily_rating: {data.at[index, 'daily_rating']} -> {new_daily_rating}")
    data.at[index, 'daily_rating'] = new_daily_rating

    new_rapid_rating = stats.get("chess_rapid", {}).get("last", {}).get("rating", None)
    logging.info(f"Updating rapid_rating: {data.at[index, 'rapid_rating']} -> {new_rapid_rating}")
    data.at[index, 'rapid_rating'] = new_rapid_rating

    # Handle last_online
    last_online = stats.get("last_online", None)
    if last_online is not None:
        new_last_online = convert_to_datetime(last_online)
        logging.info(f"Updating last_online: {data.at[index, 'last_online']} -> {new_last_online}")
        data.at[index, 'last_online'] = new_last_online

    logging.info(f"After: {data.loc[index].to_dict()}")
    return data


if __name__ == "__main__":
    update_player_data()
