import sqlite3
import pandas as pd

# File paths
DB_NAME = "chess_players.db"
MASTER_FILE = "cleaned_master_chess_players.csv"

def populate_database():
    """Populate the database with data from the master file."""
    # Load the cleaned master file
    data = pd.read_csv(MASTER_FILE)

    # Connect to the database
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Insert data into the database
    for _, row in data.iterrows():
        cursor.execute("""
        INSERT OR REPLACE INTO players (
            Username, Join_Date, Last_Online, Total_Games_Played,
            Total_Daily_Games, Total_Rapid_Games, Total_Bullet_Games,
            Total_Blitz_Games, Daily_Rating, Rapid_Rating, Bullet_Rating,
            Blitz_Rating, Puzzle_Rating, Date, Daily_Wins, Daily_Losses,
            Daily_Draws, Rapid_Wins, Rapid_Losses, Rapid_Draws, Bullet_Wins,
            Bullet_Losses, Bullet_Draws, Blitz_Wins, Blitz_Losses, Blitz_Draws,
            Daily_Win_Percentage, Daily_Loss_Percentage, Daily_Draw_Percentage,
            Rapid_Win_Percentage, Rapid_Loss_Percentage, Rapid_Draw_Percentage,
            Bullet_Win_Percentage, Bullet_Loss_Percentage, Bullet_Draw_Percentage,
            Blitz_Win_Percentage, Blitz_Loss_Percentage, Blitz_Draw_Percentage
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row["Username"], row["Join Date"], row["Last Online"], row["Total Games Played"],
            row["Total Daily Games"], row["Total Rapid Games"], row["Total Bullet Games"],
            row["Total Blitz Games"], row["Daily Rating"], row["Rapid Rating"], row["Bullet Rating"],
            row["Blitz Rating"], row["Puzzle Rating"], row["Date"], row["Daily Wins"], row["Daily Losses"],
            row["Daily Draws"], row["Rapid Wins"], row["Rapid Losses"], row["Rapid Draws"], row["Bullet Wins"],
            row["Bullet Losses"], row["Bullet Draws"], row["Blitz Wins"], row["Blitz Losses"], row["Blitz Draws"],
            row["Daily Win Percentage"], row["Daily Loss Percentage"], row["Daily Draw Percentage"],
            row["Rapid Win Percentage"], row["Rapid Loss Percentage"], row["Rapid Draw Percentage"],
            row["Bullet Win Percentage"], row["Bullet Loss Percentage"], row["Bullet Draw Percentage"],
            row["Blitz Win Percentage"], row["Blitz Loss Percentage"], row["Blitz Draw Percentage"]
        ))

    conn.commit()
    conn.close()
    print(f"Database {DB_NAME} populated successfully.")

if __name__ == "__main__":
    populate_database()
