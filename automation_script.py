import subprocess
import logging
import os
import time

# Configure logging
logging.basicConfig(
    filename="automation_log.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Define your scripts and files
SCRIPTS = {
    "update_data": "chess_kenya.py",
    "clean_data": "data_cleaning.py",
    # "dashboard": "chess_dashboard.py"
}
CLEANED_DATA_FILE = "cleaned_chess_players.csv"
REPO_PATH = r"C:\Users\Datac\OneDrive\Desktop\New folder (2)"
GIT_COMMIT_MESSAGE = "Automated update of chess players data"

def run_script(automation_script):
    """Run a Python script and log the outcome."""
    try:
        logging.info(f"Running script: {automation_script}")
        subprocess.run(["python", automation_script], check=True)
        logging.info(f"Successfully ran: {automation_script}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running {automation_script}: {e}")
        raise

def push_to_github():
    """Push updated data to GitHub."""
    try:
        os.chdir(REPO_PATH)
        logging.info("Adding files to GitHub...")
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", GIT_COMMIT_MESSAGE], check=True)
        subprocess.run(["git", "push"], check=True)
        logging.info("Changes pushed to GitHub successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error pushing to GitHub: {e}")
        raise

def main():
    """Main automation workflow."""
    try:
        # Step 1: Update Data?

        # Step 3: Run Dashboard (Optional - for local testing)
        # run_script(SCRIPTS["dashboard"])

        # Step 4: Push to GitHub
        push_to_github()

        logging.info("Automation completed successfully.")
    except Exception as e:
        logging.error(f"Automation failed: {e}")

if __name__ == "__main__":
    main()
