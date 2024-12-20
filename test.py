import sqlite3
import pandas as pd

# Connect to the database
conn = sqlite3.connect("chess_players.db")

# Query the data
df = pd.read_sql_query("SELECT * FROM players", conn)
print(df.describe())  # Summary statistics
print(df.head())      # First few rows
conn.close()
