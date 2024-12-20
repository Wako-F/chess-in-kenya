import sqlite3
import pandas as pd

# Path to the cleaned master file
MASTER_FILE = "cleaned_master_chess_players.csv"
DB_FILE = "chess_players.db"

# Define column names
COLUMNS = [
    "Username", "Join Date", "Last Online", "Total Games Played", "Total Daily Games",
    "Total Rapid Games", "Total Bullet Games", "Total Blitz Games", "Daily Rating",
    "Rapid Rating", "Bullet Rating", "Blitz Rating", "Puzzle Rating", "Date",
    "Daily Wins", "Daily Losses", "Daily Draws", "Rapid Wins", "Rapid Losses",
    "Rapid Draws", "Bullet Wins", "Bullet Losses", "Bullet Draws", "Blitz Wins",
    "Blitz Losses", "Blitz Draws", "Daily Win Percentage", "Daily Loss Percentage",
    "Daily Draw Percentage", "Rapid Win Percentage", "Rapid Loss Percentage",
    "Rapid Draw Percentage", "Bullet Win Percentage", "Bullet Loss Percentage",
    "Bullet Draw Percentage", "Blitz Win Percentage", "Blitz Loss Percentage",
    "Blitz Draw Percentage"
]

# Create the database and table
def create_database():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Drop the table if it already exists
    cursor.execute("DROP TABLE IF EXISTS players")

    # Create the table with the exact column names
    cursor.execute(f"""
        CREATE TABLE players (
            {", ".join([f'"{col}" TEXT' for col in COLUMNS])}
        )
    """)
    conn.commit()
    conn.close()

# Populate the database
def populate_database():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Load data from the master CSV
    df = pd.read_csv(MASTER_FILE)

    # Insert data into the database
    for _, row in df.iterrows():
        values = tuple(row[COLUMNS].fillna("").values)
        placeholders = ", ".join(["?"] * len(COLUMNS))
        column_names = ", ".join([f'"{col}"' for col in COLUMNS])  # Escape column names
        cursor.execute(f"INSERT INTO players ({column_names}) VALUES ({placeholders})", values)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    print("Resetting database...")
    create_database()
    print("Database created successfully.")
    print("Populating database...")
    populate_database()
    print("Database populated successfully.")
