# chess-in-kenya
# Kenyan Chess Dashboard Project

This project is a comprehensive data-driven dashboard showcasing the state of online chess in Kenya. The dashboard leverages data collected from the Chess.com API, analyzes it, and presents it visually to provide insights into player activities, ratings, and trends.

---

## Features

### 1. **Dashboard Overview**
- **Total Players**: Displays the total number of unique players.
- **Total Games Played**: Summarizes the number of games played across all formats.
- **Average Ratings**: Calculates average ratings for Rapid, Blitz, Bullet, and Puzzle formats, excluding zero values.
- **Player Rankings**: Displays leaderboards for top players based on various formats and criteria, including total games played, puzzle ratings, and format-specific rankings.
- **Player Search**: Enables searching for individual players to view detailed statistics and rankings.

### 2. **Visualizations**
- **Joining Trends**: A timeline showing when players joined Chess.com.
- **African Heatmap**: A choropleth map displaying the distribution of active players across African countries.
- **Rating Distributions**: Histograms for player ratings across formats.
---

## Project Workflow

### 1. **Data Collection**
- Uses the Chess.com API to fetch data for players in Kenya.
- Stores data in `kenyan_chess_players_partial.csv`.

### 2. **Data Cleaning**
- Removes inactive players and formats columns for uniformity.
- Cleans the data to ensure accuracy and completeness, saving results to `cleaned_master_chess_players.csv`.

### 3. **Dashboard Development**
- Built with **Streamlit** for interactive data visualization.
- Data loaded from `cleaned_master_chess_players.csv` for simplicity and ease of updates.

### 4. **Automation**
- Automates data updates and pushes to GitHub.
- Python scripts handle data collection, cleaning, and uploading to the repository for seamless updates to the dashboard.

---

## Author
Kunu Fugicha Wako

For inquiries, contact: wakokunu@gmail.com

