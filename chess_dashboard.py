import streamlit as st
import pandas as pd
import plotly.express as px
import time
from datetime import datetime
import os
from streamlit_autorefresh import st_autorefresh
import plotly.graph_objects as go

# Custom CSS
st.markdown(
    """
    <style>
    .main {
        background-color: #f9f9f9;
        font-family: 'Arial', sans-serif;
    }
    .css-18ni7ap.e8zbici2 {
        background-color: #6c63ff;
        color: white;
        font-weight: bold;
    }
    .metric-container {
        background-color: #ffffff;
        border-radius: 1000px;
        padding: 1000px;
        box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
        margin: 10px 0;
    }
    .info-icon {
        color: #6c63ff;
        font-size: 0.8rem;
        margin-left: 5px;
        cursor: pointer;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Load Data
@st.cache_data(ttl=300)  # Cache data for 5 minutes
def load_data(filename):
    try:
        # Add timestamp to URL to prevent caching
        timestamp = int(time.time())
        url = f"https://raw.githubusercontent.com/Wako-F/chess-in-kenya/main/cleaned_master_chess_players.csv?t={timestamp}"
        return pd.read_csv(url)
    except Exception as e:
        st.error(f"Error loading data: {e}")
        # Fallback to local file if GitHub fetch fails
        return pd.read_csv(filename)

# Get current refresh time
refresh_flag = "refresh.flag"
current_refresh_time = os.path.getmtime(refresh_flag) if os.path.exists(refresh_flag) else 0

# Clear cache and reload data when refresh flag changes
if "last_refresh_time" not in st.session_state or current_refresh_time > st.session_state["last_refresh_time"]:
    st.cache_data.clear()
    data = load_data("cleaned_master_chess_players.csv")
    st.session_state["last_refresh_time"] = current_refresh_time
else:
    data = load_data("cleaned_master_chess_players.csv")

# # Connect to the database
# db_file = "chess_players.db"
# conn = sqlite3.connect(db_file)

# # Query data
# query = "SELECT * FROM players"
# data = pd.read_sql_query(query, conn)

# Close the connection
# # conn.close()
# # Ensure numeric columns are converted properly
# numeric_columns = [
#     "Bullet Rating", "Blitz Rating", "Rapid Rating", "Daily Rating", "Total Games Played",
#     "Total Daily Games", "Total Rapid Games", "Total Bullet Games", "Total Blitz Games",
#     "Puzzle Rating", "Daily Wins", "Daily Losses", "Daily Draws", "Rapid Wins", "Rapid Losses",
#     "Rapid Draws", "Bullet Wins", "Bullet Losses", "Bullet Draws", "Blitz Wins", "Blitz Losses",
#     "Blitz Draws", "Daily Win Percentage", "Daily Loss Percentage", "Daily Draw Percentage",
#     "Rapid Win Percentage", "Rapid Loss Percentage", "Rapid Draw Percentage",
#     "Bullet Win Percentage", "Bullet Loss Percentage", "Bullet Draw Percentage",
#     "Blitz Win Percentage", "Blitz Loss Percentage", "Blitz Draw Percentage"
# ]

# # Convert columns to numeric, coercing errors to NaN
# data[numeric_columns] = data[numeric_columns].apply(pd.to_numeric, errors="coerce")

# data.set_index('Username', inplace=True)
# def load_data_from_github():
#     url = "https://raw.githubusercontent.com/Wako-F/chess-in-kenya/refs/heads/main/cleaned_chess_players.csv"
#     return pd.read_csv(url)
# data = load_data_from_github()
# Ensure 'Join Date' is in datetime format
# data['Join Date'] = pd.to_datetime(data['Join Date'], errors='coerce')

# # Drop rows with invalid or missing join dates
# data = data.dropna(subset=['Join Date'])
st.markdown("# Online Chess in Kenya ♚")

#Auto refresh
refresh_flag = "refresh.flag"

# Function to get the last modified time of a file
def get_last_modified_time(file_path):
    return os.path.getmtime(file_path) if os.path.exists(file_path) else 0

# Monitor the refresh flag for changes
last_refresh_time = st.session_state.get("last_refresh_time", 0)
current_refresh_time = get_last_modified_time(refresh_flag)

if current_refresh_time > last_refresh_time:
    st.session_state["last_refresh_time"] = current_refresh_time
    st.rerun()  # Trigger a refresh when the marker file updates

#Last update caption
try:
    with open("refresh.flag", "r") as f:
        last_update = f.read().strip()
except FileNotFoundError:
    last_update = "Unknown (no update record found)"

st.caption(f"{last_update}")
# Tabs for Navigation

tab1, tab2, tab3 = st.tabs(["Overview", "Leaderboards", "Search"])

# Tab 1: Overview
with tab1:
    
    # st.markdown("## 🌟 Overview Metrics")
    # st.markdown("---")

    # Calculate metrics
    total_players = data["Username"].nunique()
    total_games = data["Total Games Played"].sum()

    # Exclude 0 ratings for each format and calculate averages
    average_rapid_rating = data.loc[data["Rapid Rating"] > 0, "Rapid Rating"].mean()
    average_blitz_rating = data.loc[data["Blitz Rating"] > 0, "Blitz Rating"].mean()
    average_bullet_rating = data.loc[data["Bullet Rating"] > 0, "Bullet Rating"].mean()

   # Centered Total Games Played
    st.markdown(
        f"""
        <div style="text-align: center; font-size: 2.2rem; font-weight: bold; margin-bottom: 1rem;">
            Total Games Played: {total_games:,.0f}
        </div>
        """,
        unsafe_allow_html=True,
    )
    # st.markdown("<br>", unsafe_allow_html=True)
    # st.markdown("<br>", unsafe_allow_html=True)

    # Custom CSS for responsive and aligned metrics
    st.markdown(
        """
        <style>
        /* Responsive container for metrics */
        .metrics-container {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 20px;
            margin-bottom: 30px;
        }
        .metric-box {
            
            border-radius: 10px;
            padding: 15px 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            text-align: center;
            font-family: Arial, sans-serif;
        }
        .metric-box h3 {
            margin: 0;
            font-size: 18px;
            
        }
        .metric-box p {
            margin: 0;
            font-size: 24px;
            font-weight: bold;
            
        }
        /* Adjust layout for smaller screens */
        @media (max-width: 768px) {
            .metrics-container {
                flex-direction: column;
            }
            .metric-box {
                width: 100%;
            }
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # HTML structure for metrics
    st.markdown(
        f"""
        <div class="metrics-container">
            <div class="metric-box">
                <h3>Total Players ♟️</h3>
                <p>{total_players:,}</p>
            </div>
            <div class="metric-box">
                <h3>Avg. Rapid Rating 🕐</h3>
                <p>{average_rapid_rating:.0f}</p>
            </div>
            <div class="metric-box">
                <h3>Avg. Blitz Rating ⚡</h3>
                <p>{average_blitz_rating:.0f}</p>
            </div>
            <div class="metric-box">
                <h3>Avg. Bullet Rating 🚀</h3>
                <p>{average_bullet_rating:.0f}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


    # st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")
    # st.markdown("<br>", unsafe_allow_html=True)

        # Joining Trend Over Time
    st.markdown(
        f"""
        <div style="font-size: 1.6rem; font-weight: bold; margin-bottom: 1rem;">
            Joining Trend Over Time
        </div>
        """,
        unsafe_allow_html=True,
    )
    # st.markdown("## Joining Trend Over Time")

    # Ensure 'Join Date' is in datetime format
    data['Join Date'] = pd.to_datetime(data['Join Date'], errors='coerce')

    # Drop rows with invalid or missing join dates
    data = data.dropna(subset=['Join Date'])

    # Group data by month
    join_trend = data['Join Date'].dt.to_period("M").value_counts().sort_index()

    # Convert to DataFrame
    join_trend_df = join_trend.reset_index()
    join_trend_df.columns = ["Date", "Player Count"]
    join_trend_df['Date'] = join_trend_df['Date'].dt.to_timestamp()

    # Get min and max date as `datetime.date` objects for the slider
    min_date = join_trend_df['Date'].min().date()
    max_date = join_trend_df['Date'].max().date()

    # Add a slider for date range selection
    st.markdown(
        f"""
        <div style="font-size: 1.2rem; font-weight: bold; margin-bottom: 1rem;">
            Filter by Date Range
        </div>
        """,
        unsafe_allow_html=True,
    )
    # st.markdown("### Filter by Date Range")
    start_date, end_date = st.slider(
        "Select date range",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),
    )

    # Convert the selected range back to `pd.Timestamp` for filtering
    start_date = pd.Timestamp(start_date)
    end_date = pd.Timestamp(end_date)

    # Filter the DataFrame
    filtered_join_trend_df = join_trend_df[
        (join_trend_df['Date'] >= start_date) & (join_trend_df['Date'] <= end_date)
    ]

    # Plot the data
    fig_join_trend = px.line(
        filtered_join_trend_df,
        x="Date",
        y="Player Count",
        title="Trend of Players Joining Over Time",
        labels={"Date": "Date", "Player Count": "Number of Players"},
        template="plotly_white",
    )

    st.plotly_chart(fig_join_trend, use_container_width=True)

    st.markdown("---")

    st.markdown(
        f"""
        <div style="font-size: 1.6rem; font-weight: bold; margin-bottom: 1rem;">
            Recently Active Player Distribution Across Africa
        </div>
        """,
        unsafe_allow_html=True,
    )
    #African players heatmap
    country_df = pd.read_csv("african_country_player_counts.csv")
    fig = px.choropleth(
        country_df,
        locations="ISO-3",
        color="Player Count",
        hover_name="Country Name",
        hover_data={"Player Count": True, "ISO-3": False},
        color_continuous_scale="Viridis",
        locationmode="ISO-3",
        # title="Player Distribution Across Africa",
    )

    # Update layout for better fit and centering
    fig.update_geos(
        showframe=False,
        showcoastlines=False,
        projection_type="mercator",
        center={"lat": 0, "lon": 20},  # Centering on Africa
        projection_scale=4.5,  # Zoom level
        bgcolor="rgba(0,0,0,0)"
    )

    # Update figure layout
    fig.update_layout(
        # margin={"r": 10, "t": 50, "l": 10, "b": 10},
        title={
            # "text": "Number of recently active players per country"
           
        },
        coloraxis_colorbar=dict(
            title="Players",
            title_font=dict(size=14),
            tickfont=dict(size=12),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )

    # Display the map
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Games Played Per Format
    st.markdown("### Games Played Per Format")
    game_formats = ["Total Daily Games", "Total Rapid Games", "Total Blitz Games", "Total Bullet Games"]
    games_summary = data[game_formats].sum().rename("Total Games Played")
    fig_games = px.bar(
        games_summary,
        x=games_summary.index,
        y=games_summary.values,
        title="Games Played Across Formats",
        labels={"x": "Game Format", "y": "Total Games Played"},
        template="plotly_white",
    )
    st.plotly_chart(fig_games, use_container_width=True)
    # Rating Distribution
    st.markdown("## Rating Distribution")
    rating_format = st.selectbox("Select Rating Format", ['Daily Rating', 'Rapid Rating', 'Blitz Rating', 'Bullet Rating'])
    fig = px.histogram(
        data.dropna(subset=[rating_format]),
        x=rating_format,
        nbins=20,
        title=f"{rating_format.capitalize()} Distribution",
        labels={rating_format: "Rating"},
        template="plotly_white",
    )
    st.plotly_chart(fig, use_container_width=True)

# Tab 2: Leaderboards
with tab2:
    st.markdown("## 🏆 Rating Leaderboards")
    # Slider for number of top players
    top_n = st.slider("Select Number of Top Players", 1, 50, 10)

    # Dropdown to select the rating format
    format_to_rank = st.selectbox("Select Format", ['Daily Rating', 'Rapid Rating', 'Blitz Rating', 'Bullet Rating'])

    # Determine the corresponding games column based on the selected format
    if format_to_rank == 'Daily Rating':
        games_column = "Total Daily Games"
    elif format_to_rank == 'Rapid Rating':
        games_column = "Total Rapid Games"
    elif format_to_rank == 'Blitz Rating':
        games_column = "Total Blitz Games"
    else:  # Bullet Rating
        games_column = "Total Bullet Games"

    # Filter players with more than 0 rating and at least 50 games played
    filtered_players = data[(data[format_to_rank] > 0) & (data[games_column] >= 50)]

    # Sort and select the top players
    top_players = filtered_players.nlargest(top_n, format_to_rank)

    # Add a rank column
    top_players = top_players.reset_index(drop=True)
    top_players.index += 1  # Set rank as 1, 2, 3...

    # Display additional stats for the selected format
    display_columns = ["Username", format_to_rank, games_column]
    if format_to_rank == 'Daily Rating':
        display_columns += ["Daily Wins", "Daily Losses", "Daily Draws"]
    elif format_to_rank == 'Rapid Rating':
        display_columns += ["Rapid Wins", "Rapid Losses", "Rapid Draws"]
    elif format_to_rank == 'Blitz Rating':
        display_columns += ["Blitz Wins", "Blitz Losses", "Blitz Draws"]
    else:  # Bullet Rating
        display_columns += ["Bullet Wins", "Bullet Losses", "Bullet Draws"]

    # Format numeric columns to display whole numbers
    top_players[display_columns[1:]] = top_players[display_columns[1:]].astype(int)

    # Display the DataFrame
    st.table(top_players[display_columns])

        # Most Games Played Leaderboard
    st.markdown("## 🏅 Most Games Played Leaderboard")
    # Slider to select the number of top players
    top_n_games = st.slider(f"Select Number of Top Players by Games Played", 1, 50, 10)
    # Select the format for leaderboard
    game_format = st.selectbox(
        "Select Format ",
        ["Total Games Played", "Daily Games", "Rapid Games", "Blitz Games", "Bullet Games"]
    )

    # Map the format to column names
    format_to_column_map = {
        "Total Games Played": "Total Games Played",
        "Daily Games": "Total Daily Games",
        "Rapid Games": "Total Rapid Games",
        "Blitz Games": "Total Blitz Games",
        "Bullet Games": "Total Bullet Games"
    }

    # Corresponding Win, Loss, and Draw columns for win percentage
    win_loss_draw_map = {
        "Total Games Played": None,  # No specific win/loss/draw stats for total games
        "Daily Games": ["Daily Wins", "Daily Losses", "Daily Draws"],
        "Rapid Games": ["Rapid Wins", "Rapid Losses", "Rapid Draws"],
        "Blitz Games": ["Blitz Wins", "Blitz Losses", "Blitz Draws"],
        "Bullet Games": ["Bullet Wins", "Bullet Losses", "Bullet Draws"]
    }

    selected_column = format_to_column_map[game_format]
    win_loss_draw_columns = win_loss_draw_map[game_format]

    

    # Filter players with at least 10 games played in the selected format
    valid_players = data[data[selected_column] >= 10]

    # Calculate Win Percentage if applicable
    if win_loss_draw_columns:
        valid_players["Win Percentage"] = (
            valid_players[win_loss_draw_columns[0]] / 
            (valid_players[win_loss_draw_columns[0]] +
            valid_players[win_loss_draw_columns[1]] +
            valid_players[win_loss_draw_columns[2]]) * 100
        ).fillna(0).round(2)  # Avoid division by zero and round to 2 decimal places

    # Sort by the selected column and pick the top players
    top_games_players = valid_players.nlargest(top_n_games, selected_column)

    # Add a rank column
    top_games_players = top_games_players.reset_index(drop=True)
    top_games_players.index += 1  # Set rank as 1, 2, 3...

    # Columns to display
    columns_to_display = ["Username", selected_column]
    if win_loss_draw_columns:
        columns_to_display += ["Win Percentage"]

    columns_to_display.append("Join Date")  # Add Join Date for context

    # Format numeric columns to display whole numbers
    top_games_players[selected_column] = top_games_players[selected_column].astype(int)
    if "Win Percentage" in top_games_players:
        top_games_players["Win Percentage"] = top_games_players["Win Percentage"].astype(int)

    # Display the leaderboard
    st.table(top_games_players[columns_to_display])

        # Puzzle Rating Leaderboard
    st.markdown("## 🧩 Puzzle Rating Leaderboard")

    # Slider for number of top players
    top_n_puzzle = st.slider("Select Number of Top Players", 1, 50, 10, key="puzzle_top_n")

    # Filter players with valid puzzle ratings
    filtered_puzzle_players = data[data['Puzzle Rating'] > 0]

    # Sort and select the top players by puzzle rating
    top_puzzle_players = filtered_puzzle_players.nlargest(top_n_puzzle, 'Puzzle Rating')

    # Add a rank column
    top_puzzle_players = top_puzzle_players.reset_index(drop=True)
    top_puzzle_players.index += 1  # Set rank as 1, 2, 3...

    # Format numeric columns to display whole numbers
    top_puzzle_players['Puzzle Rating'] = top_puzzle_players['Puzzle Rating'].astype(int)

    st.table(
        top_puzzle_players[["Username", "Puzzle Rating", "Date",]]

    )



# Tab 3: Search & Comparison
with tab3:
    st.markdown("## 🔎 Search Player Stats")
    
    # Text input for searching a player's username
    search_username = st.text_input("Search username", placeholder="Type a username...", key="search", label_visibility="collapsed")
    start_time = time.time()
    
    if search_username:
        player_data = data[data["Username"].str.contains(search_username, case=False, na=False)]
        
        if not player_data.empty:
            player = player_data.iloc[0]
            
            # Quick Ratings Overview using the same CSS as tab1
            st.markdown(
                """
                <style>
                .metrics-container {
                    display: flex;
                    flex-wrap: wrap;
                    justify-content: center;
                    gap: 20px;
                    margin-bottom: 30px;
                }
                .metric-box {
                    border-radius: 10px;
                    padding: 15px 20px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    text-align: center;
                    flex: 1;
                    min-width: 120px;
                }
                .metric-box h3 {
                    margin: 0;
                    color: #666;
                    font-size: 1em;
                }
                .metric-box h2 {
                    margin: 5px 0;
                    
                    font-size: 1.5em;
                }
                @media (max-width: 768px) {
                    .metric-box {
                        min-width: 100px;
                    }
                }
                </style>
                """,
                unsafe_allow_html=True
            )

            # Display ratings using the same style as tab1
            st.markdown(
                f"""
                <div class="metrics-container">
                    <div class="metric-box">
                        <h3>Bullet</h3>
                        <h2>{int(player['Bullet Rating']) if player['Bullet Rating'] > 0 else 'N/A'}</h2>
                    </div>
                    <div class="metric-box">
                        <h3>Blitz</h3>
                        <h2>{int(player['Blitz Rating']) if player['Blitz Rating'] > 0 else 'N/A'}</h2>
                    </div>
                    <div class="metric-box">
                        <h3>Rapid</h3>
                        <h2>{int(player['Rapid Rating']) if player['Rapid Rating'] > 0 else 'N/A'}</h2>
                    </div>
                    <div class="metric-box">
                        <h3>Daily</h3>
                        <h2>{int(player['Daily Rating']) if player['Daily Rating'] > 0 else 'N/A'}</h2>
                    </div>
                    <div class="metric-box">
                        <h3>Puzzle</h3>
                        <h2>{int(player['Puzzle Rating']) if player['Puzzle Rating'] > 0 else 'N/A'}</h2>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Player Rankings Summary
            def get_ranking(username, column):
                # Filter for valid ratings and sort in descending order
                valid_data = data[data[column] > 0].sort_values(column, ascending=False)
                # Get the player's position
                player_data = valid_data[valid_data['Username'] == username]
                if not player_data.empty and player_data[column].iloc[0] > 0:
                    rank = valid_data.index.get_loc(player_data.index[0]) + 1
                    return (rank, len(valid_data))
                return (None, len(valid_data))

            # Games ranking needs special handling
            def get_games_ranking(username):
                games_data = data.sort_values('Total Games Played', ascending=False)
                player_data = games_data[games_data['Username'] == username]
                if not player_data.empty:
                    rank = games_data.index.get_loc(player_data.index[0]) + 1
                    return rank, len(games_data)
                return None, len(data)

            def format_ranking(rank, total, format_name):
                if rank:
                    percentile = 100 * ((total - rank + 1) / total)
                    return f"{rank} in {format_name} (Top {percentile:.1f}% of {total:,} players)"
                return None

            # Get rankings
            bullet_rank, bullet_total = get_ranking(player['Username'], 'Bullet Rating')
            blitz_rank, blitz_total = get_ranking(player['Username'], 'Blitz Rating')
            rapid_rank, rapid_total = get_ranking(player['Username'], 'Rapid Rating')
            daily_rank, daily_total = get_ranking(player['Username'], 'Daily Rating')
            puzzle_rank, puzzle_total = get_ranking(player['Username'], 'Puzzle Rating')
            games_rank, total_players = get_games_ranking(player['Username'])

            # Create ranking summary
            rankings = []
            if bullet_rank:
                rankings.append(format_ranking(bullet_rank, bullet_total, "Bullet"))
            if blitz_rank:
                rankings.append(format_ranking(blitz_rank, blitz_total, "Blitz"))
            if rapid_rank:
                rankings.append(format_ranking(rapid_rank, rapid_total, "Rapid"))
            if daily_rank:
                rankings.append(format_ranking(daily_rank, daily_total, "Daily"))
            if puzzle_rank:
                rankings.append(format_ranking(puzzle_rank, puzzle_total, "Puzzles"))
            if games_rank:
                rankings.append(format_ranking(games_rank, total_players, "total games played"))

            # Display summary if there are any rankings
            if rankings:
                summary = f"{player['Username']} is ranked: "
                if len(rankings) > 1:
                    summary += ", ".join(rankings[:-1]) + f", and {rankings[-1]}"
                else:
                    summary += rankings[0]
                
                st.markdown(
                    f"""
                    <div style='padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin: 20px 0;'>
                        <h4>🏆 Rankings Summary</h4>
                        <p style='font-size: 1.1em; line-height: 1.5;'>
                            {summary}
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            # Create two columns for layout
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"### 📊 Stats for {player['Username']}")
                
                # Rating Overview - Radar Chart
                ratings = {
                    'Bullet': player['Bullet Rating'],
                    'Blitz': player['Blitz Rating'],
                    'Rapid': player['Rapid Rating'],
                    'Daily': player['Daily Rating'],
                    'Puzzle': player['Puzzle Rating']
                }
                
                # Filter out zero ratings
                ratings = {k: v for k, v in ratings.items() if v > 0}
                
                if ratings:
                    fig_radar = go.Figure()
                    fig_radar.add_trace(go.Scatterpolar(
                        r=list(ratings.values()),
                        theta=list(ratings.keys()),
                        fill='toself',
                        name='Ratings'
                    ))
                    
                    fig_radar.update_layout(
                        polar=dict(
                            radialaxis=dict(
                                visible=True,
                                range=[0, max(ratings.values()) * 1.1]
                            )
                        ),
                        showlegend=False,
                        title="Rating Overview"
                    )
                    st.plotly_chart(fig_radar, use_container_width=True)
            
            with col2:
                # Join Date and Total Games
                st.markdown(
                    f"""
                    <div style='padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                        <h4>Profile Overview</h4>
                        <p>📅 Joined: {player['Join Date']}</p>
                        <p>🎮 Total Games: {player['Total Games Played']:,}</p>
                        <p>🧩 Puzzle Rating: {int(player['Puzzle Rating']) if player['Puzzle Rating'] > 0 else 'N/A'}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            # Performance Charts
            st.markdown("### 📈 Performance Analysis")
            
            # Create tabs for different performance views
            perf_tab1, perf_tab2 = st.tabs(["Game Distribution", "Win Rates"])
            
            with perf_tab1:
                # Games Distribution Pie Chart
                games_data = {
                    'Bullet': player['Total Bullet Games'],
                    'Blitz': player['Total Blitz Games'],
                    'Rapid': player['Total Rapid Games'],
                    'Daily': player['Total Daily Games']
                }
                
                fig_games = px.pie(
                    values=list(games_data.values()),
                    names=list(games_data.keys()),
                    title="Games Distribution by Format",
                    template="plotly_white"
                )
                fig_games.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_games, use_container_width=True)
            
            with perf_tab2:
                # Win rates bar chart
                formats = ['Bullet', 'Blitz', 'Rapid', 'Daily']
                win_rates = []
                
                for fmt in formats:
                    wins = player[f'{fmt} Wins']
                    total = player[f'Total {fmt} Games']
                    win_rate = (wins / total * 100) if total > 0 else 0
                    win_rates.append(win_rate)
                
                fig_wins = go.Figure()
                fig_wins.add_trace(go.Bar(
                    x=formats,
                    y=win_rates,
                    text=[f"{rate:.1f}%" for rate in win_rates],
                    textposition='auto',
                ))
                
                fig_wins.update_layout(
                    title="Win Rates by Format",
                    yaxis_title="Win Rate (%)",
                    yaxis_range=[0, 100],
                    template="plotly_white"
                )
                st.plotly_chart(fig_wins, use_container_width=True)
            
            # Detailed Stats Tables
            st.markdown("### 📊 Detailed Statistics")
            
            def format_stats(format_name, total, wins, losses, draws):
                win_rate = (wins / total * 100) if total > 0 else 0
                loss_rate = (losses / total * 100) if total > 0 else 0
                draw_rate = (draws / total * 100) if total > 0 else 0
                
                return pd.DataFrame({
                    'Metric': ['Total Games', 'Wins', 'Losses', 'Draws', 'Win Rate', 'Loss Rate', 'Draw Rate'],
                    'Value': [
                        f"{total:,}",
                        f"{wins:,}",
                        f"{losses:,}",
                        f"{draws:,}",
                        f"{win_rate:.1f}%",
                        f"{loss_rate:.1f}%",
                        f"{draw_rate:.1f}%"
                    ]
                })
            
            # Create tabs for different game formats
            stat_tabs = st.tabs(['Bullet', 'Blitz', 'Rapid', 'Daily'])
            
            for tab, format_name in zip(stat_tabs, ['Bullet', 'Blitz', 'Rapid', 'Daily']):
                with tab:
                    stats_df = format_stats(
                        format_name,
                        player[f'Total {format_name} Games'],
                        player[f'{format_name} Wins'],
                        player[f'{format_name} Losses'],
                        player[f'{format_name} Draws']
                    )
                    
                    st.dataframe(
                        stats_df,
                        column_config={
                            "Metric": st.column_config.TextColumn("Metric", width="medium"),
                            "Value": st.column_config.TextColumn("Value", width="medium")
                        },
                        hide_index=True
                    )
            
            end_time = time.time()
            st.caption(f"Search completed in {end_time - start_time:.2f} seconds")
        else:
            st.error(f"No player found with username: {search_username}")

# Auto-refresh triggered at 2025-03-05T06:13:59.318427

# Auto-refresh triggered at 2025-04-20T09:36:24.699877

# Auto-refresh triggered at 2025-05-22T09:38:41.912160

# Auto-refresh triggered at 2025-06-23T16:59:28.081312

# Auto-refresh triggered at 2025-07-25T13:46:51.396020

# Auto-refresh triggered at 2025-08-30T20:26:01.335565
