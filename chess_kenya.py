import requests
import pandas as pd
import time
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
from datetime import datetime, timedelta
from requests.exceptions import HTTPError

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
RATE_LIMIT_DELAY = 2  # Increased delay between requests

# Add new constants
MAX_WORKERS = 5  # Reduced from 10 to lower concurrent requests
MASTER_CSV_FILENAME = "master_chess_players.csv"
REQUEST_TIMEOUT = 30  # Increased timeout
MAX_RETRIES = 3
FULL_UPDATE = False  # Set to True for monthly full updates
LAST_FULL_UPDATE_FILE = "last_full_update.txt"
PROGRESS_FILE = "data_collection_progress.txt"  # To store processing progress

class RateLimiter:
    def __init__(self, calls_per_second=0.5):  # Reduced to 1 request per 2 seconds
        self.calls_per_second = calls_per_second
        self.timestamps = Queue()
        
    def wait(self):
        current_time = time.time()
        
        # Remove timestamps older than 2 seconds
        while not self.timestamps.empty():
            if current_time - self.timestamps.queue[0] >= (1/self.calls_per_second):
                self.timestamps.get()
            else:
                break
                
        # If we've made too many calls, wait
        if self.timestamps.qsize() >= 1:
            sleep_time = (1/self.calls_per_second) - (current_time - self.timestamps.queue[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
                
        self.timestamps.put(time.time())

rate_limiter = RateLimiter(calls_per_second=0.5)  # One request per 2 seconds

def fetch_with_retry(url, max_retries=MAX_RETRIES):
    for attempt in range(max_retries):
        try:
            rate_limiter.wait()
            response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            
            # Specifically handle 404s
            if response.status_code == 404:
                logging.info(f"User not found (404) for URL: {url}")
                return None
            
            response.raise_for_status()
            return response.json()
        except HTTPError as he:
            if response.status_code == 404:  # Double check for 404
                return None
            if attempt == max_retries - 1:
                logging.error(f"Failed after {max_retries} attempts for {url}: {he}")
                raise
            time.sleep(2 ** attempt)
        except Exception as e:
            if attempt == max_retries - 1:
                logging.error(f"Failed after {max_retries} attempts for {url}: {e}")
                raise
            time.sleep(2 ** attempt)
    return None

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
            "daily_rating", "rapid_rating", "bullet_rating", "blitz_rating", "highest_puzzle_rating", "highest_puzzle_date",
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
    
        # If "tactics" is passed as the category, handle it differently
    if category == "tactics":
        tactics = stats.get("tactics", {})
        highest_puzzle_rating = tactics.get("highest", {}).get("rating", None)
        highest_puzzle_date = tactics.get("highest", {}).get("date", None)
        return highest_puzzle_rating, highest_puzzle_date
    
    total = wins + losses + draws
    return total, wins, losses, draws, rating

def process_player(username):
    try:
        # First check if player still exists
        profile_url = f"https://api.chess.com/pub/player/{username}"
        profile_data = fetch_with_retry(profile_url)
        
        if profile_data is None:  # User doesn't exist (404)
            logging.info(f"Player {username} no longer exists on Chess.com")
            return {'username': username, 'status': 'deleted'}
            
        stats = fetch_player_stats(username)
        join_date = fetch_join_date(username)
        last_online = fetch_last_online(username)
        
        # Extract all stats
        total_daily, daily_wins, daily_losses, daily_draws, daily_rating = extract_data(stats, "chess_daily")
        total_rapid, rapid_wins, rapid_losses, rapid_draws, rapid_rating = extract_data(stats, "chess_rapid")
        total_bullet, bullet_wins, bullet_losses, bullet_draws, bullet_rating = extract_data(stats, "chess_bullet")
        total_blitz, blitz_wins, blitz_losses, blitz_draws, blitz_rating = extract_data(stats, "chess_blitz")
        highest_puzzle_rating, highest_puzzle_date = extract_data(stats, "tactics")
        
        total_games = total_daily + total_rapid + total_bullet + total_blitz
        
        return {
            "username": username,
            "status": "active",
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
            "highest_puzzle_rating": highest_puzzle_rating,
            "highest_puzzle_date": highest_puzzle_date,
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
    except Exception as e:
        logging.error(f"Error processing player {username}: {e}")
        return None

def should_run_full_update():
    """Check if we should run a full update based on last update time"""
    if not os.path.exists(LAST_FULL_UPDATE_FILE):
        return True
        
    with open(LAST_FULL_UPDATE_FILE, 'r') as f:
        try:
            last_update = datetime.fromisoformat(f.read().strip())
            return (datetime.now() - last_update) > timedelta(days=30)
        except:
            return True

def record_full_update():
    """Record the time of the full update"""
    with open(LAST_FULL_UPDATE_FILE, 'w') as f:
        f.write(datetime.now().isoformat())

def main():
    logging.info("Starting data collection process")
    
    # Determine update mode
    run_full_update = FULL_UPDATE or should_run_full_update()
    logging.info(f"Running {'full' if run_full_update else 'partial'} update")
    
    # Initialize player set
    all_usernames = set()
    
    # Load players based on update type
    if run_full_update:
        # Load master data for full update
        if os.path.exists(MASTER_CSV_FILENAME):
            master_df = pd.read_csv(MASTER_CSV_FILENAME)
            all_usernames.update(master_df['username'].unique())
            logging.info(f"Loaded {len(all_usernames)} players from master file")
    
    # Always fetch current Kenyan players
    kenyan_players = set(fetch_kenyan_players())
    all_usernames.update(kenyan_players)
    
    logging.info(f"Total players to process: {len(all_usernames)}")
    
    # Process players using ThreadPoolExecutor
    processed_data = []
    deleted_users = []
    
    # Load already processed users if exists
    processed_usernames = set()
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r') as f:
                processed_usernames = set(line.strip() for line in f.readlines())
            logging.info(f"Resuming from previous run. Already processed {len(processed_usernames)} users.")
            
            # Also load partial data if available
            if os.path.exists(CSV_FILENAME):
                partial_df = pd.read_csv(CSV_FILENAME)
                processed_data = partial_df.to_dict('records')
                logging.info(f"Loaded {len(processed_data)} records from partial data file.")
        except Exception as e:
            logging.error(f"Error loading progress data: {e}")
            processed_usernames = set()
    
    # Filter out already processed usernames
    usernames_to_process = all_usernames - processed_usernames
    logging.info(f"Remaining users to process: {len(usernames_to_process)}")
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_username = {
            executor.submit(process_player, username): username 
            for username in usernames_to_process
        }
        
        completed = 0
        for future in as_completed(future_to_username):
            username = future_to_username[future]
            try:
                player_data = future.result()
                if player_data:
                    if player_data.get('status') == 'deleted':
                        deleted_users.append(username)
                    else:
                        processed_data.append(player_data)
                
                # Record this username as processed
                with open(PROGRESS_FILE, 'a') as f:
                    f.write(f"{username}\n")
                
                completed += 1
                if completed % 50 == 0:
                    logging.info(f"Processed {completed}/{len(usernames_to_process)} players")
                    logging.info(f"Found {len(deleted_users)} deleted accounts so far")
                    
                    # Create intermediate DataFrame and save
                    if processed_data:
                        interim_df = pd.DataFrame(processed_data)
                        save_to_csv(interim_df, CSV_FILENAME)
                        
            except Exception as e:
                logging.error(f"Error processing {username}: {e}")
    
    # Final save
    if processed_data:
        final_df = pd.DataFrame(processed_data)
        
        # Update both files for full updates
        if run_full_update:
            save_to_csv(final_df, MASTER_CSV_FILENAME)
            record_full_update()
            logging.info("Full update completed and recorded")
            
        # Always update current file
        save_to_csv(final_df, CSV_FILENAME)
        
        logging.info(f"Successfully processed {len(processed_data)} active players")
        logging.info(f"Found {len(deleted_users)} deleted accounts")
        
        if deleted_users:
            with open('deleted_users.txt', 'a') as f:
                f.write(f"\n# Deleted users found on {datetime.now().isoformat()}\n")
                f.write('\n'.join(deleted_users) + '\n')
    else:
        logging.error("No data was processed successfully")
    
    # After successful completion, clear the progress file
    if os.path.exists(PROGRESS_FILE) and completed == len(usernames_to_process):
        try:
            os.remove(PROGRESS_FILE)
            logging.info("Cleared progress file after successful completion")
        except Exception as e:
            logging.error(f"Error removing progress file: {e}")

if __name__ == "__main__":
    main()
