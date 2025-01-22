import subprocess
import logging
import os
from datetime import datetime
# Configure logging
logging.basicConfig(
    filename="automation_log.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Define your scripts and files
SCRIPTS = {
    "update_data": "chess_kenya.py",
    "update_master_ledger": "update_master_ledger.py",
    "update_african_players": "africa_count.py",
    "clean_data": "data_cleaning.py"
}
CLEANED_DATA_FILE = "cleaned_master_chess_players.csv"
AFRICA_PLAYER_COUNT = "african_country_player_counts.csv"
DASHBOARD_FILE= "chess_dashboard.py"

GIT_COMMIT_MESSAGE = "Automated update of chess players data"


def run_script(script_name):
    """Run a Python script and log the outcome."""
    try:
        logging.info(f"Executing script: {script_name}")
        subprocess.run(["python", script_name], check=True)
        logging.info(f"Script executed successfully: {script_name}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error executing script {script_name}: {e}")
        raise


def push_to_github():
    """Push updated data to GitHub."""
    try:
        logging.info("Adding files to GitHub...")
        subprocess.run(["git", "add", CLEANED_DATA_FILE, DASHBOARD_FILE, AFRICA_PLAYER_COUNT], check=True)
        subprocess.run(["git", "commit", "-m", GIT_COMMIT_MESSAGE], check=True)
        subprocess.run(["git", "push"], check=True)
        logging.info("Changes pushed to GitHub successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error pushing to GitHub: {e}")
        raise

def add_comment_to_dashboard(file_path):
    """Add a comment to the end of the Streamlit dashboard file to trigger auto-refresh."""
    try:
        with open(file_path, "a") as f:
            f.write(f"\n# Auto-refresh triggered at {datetime.now().isoformat()}\n")
        logging.info(f"Comment added to {file_path} for auto-refresh.")
    except Exception as e:
        logging.error(f"Error adding comment to {file_path}: {e}")
        raise
def save_last_update_timestamp(file_path="last_update.txt"):
    """Save the current timestamp to a file."""
    try:
        with open(file_path, "w") as f:
            f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        logging.info(f"Last update timestamp saved to {file_path}.")
    except Exception as e:
        logging.error(f"Error saving timestamp: {e}")
        raise

def main():
    """Main automation workflow."""
    try:
        # Step 1: Update data
        run_script(SCRIPTS["update_data"])
        # # Step 2: Update master ledger
        run_script(SCRIPTS["update_master_ledger"])
        # Step 3: Update African player count
        run_script(SCRIPTS["update_african_players"])
        # Step 4: Clean data
        run_script(SCRIPTS["clean_data"])

        add_comment_to_dashboard(DASHBOARD_FILE)
        save_last_update_timestamp()

        # Step 5: Push cleaned data to GitHub
        # push_to_github()
    except Exception as e:
        logging.error(f"Automation workflow failed: {e}")

if __name__ == "__main__":
    main()
