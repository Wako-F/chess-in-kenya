import pandas as pd
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    filename="master_ledger_log.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# File paths
MASTER_LEDGER_FILE = "master_chess_players.csv"
PARTIAL_DATA_FILE = "kenyan_chess_players_partial.csv"

# Define the required columns based on the partial file's structure
REQUIRED_COLUMNS = [
    "username", "join_date", "last_online", "total_games", "total_daily", "total_rapid", 
    "total_bullet", "total_blitz", "daily_rating", "rapid_rating", "bullet_rating", 
    "blitz_rating", "highest_puzzle_rating", "highest_puzzle_date",
    "daily_wins", "daily_losses", "daily_draws", "rapid_wins", "rapid_losses", 
    "rapid_draws", "bullet_wins", "bullet_losses", "bullet_draws", 
    "blitz_wins", "blitz_losses", "blitz_draws"
]

def load_master_ledger():
    """Load the master ledger (all-time record of players)."""
    if not os.path.exists(MASTER_LEDGER_FILE):
        # Create an empty DataFrame if the ledger doesn't exist
        return pd.DataFrame(columns=REQUIRED_COLUMNS)
    return pd.read_csv(MASTER_LEDGER_FILE)

def save_master_ledger(ledger):
    """Save the master ledger to a CSV file."""
    ledger.to_csv(MASTER_LEDGER_FILE, index=False)

def update_master_ledger(partial_data, master_ledger):
    """Update the master ledger with new and updated players."""
    # Ensure partial_data has all required columns
    for col in REQUIRED_COLUMNS:
        if col not in partial_data.columns:
            partial_data[col] = None  # Add missing columns with default None

    # Align columns
    partial_data = partial_data[REQUIRED_COLUMNS]
    master_ledger = master_ledger[REQUIRED_COLUMNS]

    # Set 'username' as the index for both DataFrames
    master_ledger.set_index("username", inplace=True)
    partial_data.set_index("username", inplace=True)

    # Update existing players
    master_ledger.update(partial_data)

    # Add new players
    new_players = partial_data.loc[~partial_data.index.isin(master_ledger.index)]
    updated_ledger = pd.concat([master_ledger, new_players]).reset_index()

    # Ensure the updated ledger has all required columns
    updated_ledger = updated_ledger[REQUIRED_COLUMNS]

    # Log changes
    new_players_count = len(new_players)
    logging.info(f"Master ledger updated: {new_players_count} new players added.")
    return updated_ledger, new_players_count

def main():
    """Main function to update the master ledger."""
    # Step 1: Load the master ledger
    master_ledger = load_master_ledger()

    # Step 2: Load the partial data
    if not os.path.exists(PARTIAL_DATA_FILE):
        logging.error(f"Partial data file not found: {PARTIAL_DATA_FILE}")
        return
    partial_data = pd.read_csv(PARTIAL_DATA_FILE)

    # Step 3: Update the master ledger
    master_ledger, new_players_count = update_master_ledger(partial_data, master_ledger)

    # Step 4: Save the updated master ledger
    save_master_ledger(master_ledger)

    # Step 5: Log the summary
    logging.info(f"Master ledger saved. Total players: {len(master_ledger)}, New players added: {new_players_count}")

if __name__ == "__main__":
    main()
