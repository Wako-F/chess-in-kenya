import streamlit as st
import pandas as pd
import plotly.express as px

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
@st.cache_data
# def load_data(filename):
#     return pd.read_csv(filename)

# data = load_data("cleaned_chess_players.csv")

def load_data_from_github():
    url = "https://raw.githubusercontent.com/Wako-F/chess-in-kenya/refs/heads/main/cleaned_chess_players.csv"
    return pd.read_csv(url)
data = load_data_from_github()
# Ensure 'Join Date' is in datetime format
data['Join Date'] = pd.to_datetime(data['Join Date'], errors='coerce')

# Drop rows with invalid or missing join dates
data = data.dropna(subset=['Join Date'])
st.markdown("# Online Chess in Kenya ♚")

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
                <h3>Recently Active Players ♟️</h3>
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
    st.markdown("## 🏆 Leaderboards")
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

# Tab 3: Search & Comparison
with tab3:
            # Player Search
    st.markdown("## 🔎 Search Player Stats")

    # Text input for searching a player's username
    search_username = st.text_input("", placeholder="Type a username...")

    # Check if the user has entered a username
    if search_username:
        # Filter the data for the entered username (case-insensitive)
        player_data = data[data["Username"].str.contains(search_username, case=False, na=False)]

        if not player_data.empty:
            # Extract the first matched player's stats
            player = player_data.iloc[0]

            # Display player's stats with styling
            st.markdown(f"### 📊 Stats for **{player['Username']}**")
            #Custom css for overview
            st.markdown(
                """
                <style>
                /* Responsive container for search overview metrics */
                .search-metrics-container {
                    display: flex;
                    flex-wrap: wrap;
                    justify-content: center;
                    gap: 20px;
                    margin-bottom: 30px;
                }
                .search-metric-box {
                    
                    border-radius: 10px;
                    padding: 15px 20px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    text-align: center;
                    font-family: Arial, sans-serif;
                    width: 180px; /* Consistent width for all metric boxes */
                    max-width: 100%; /* Ensure responsiveness */
                }
                .search-metric-box h3 {
                    margin: 0;
                    font-size: 18px;
                    
                }
                .search-metric-box p {
                    margin: 0;
                    font-size: 24px;
                    font-weight: bold;
                    
                }
                /* Adjust layout for smaller screens */
                @media (max-width: 768px) {
                    .search-metrics-container {
                        justify-content: center; /* Properly center-align all items */
                        align-items: center; /* Center items vertically */
                        flex-direction: row; /* Allow row alignment */
                    }
                    .search-metric-box {
                        width: calc(50% - 20px); /* Two columns for mobile */
                        margin-bottom: 10px;
                    }
                }
                @media (max-width: 480px) {
                    .search-metric-box {
                        width: 100%; /* Full width for very small screens */
                    }
                }
                </style>
                """,
                unsafe_allow_html=True
            )

            # Render the search overview metrics
            st.markdown("#### 🏆 Overview")

            st.markdown(
                f"""
                <div class="search-metrics-container">
                    <div class="search-metric-box">
                        <h3>Total Games 🎮</h3>
                        <p>{int(player["Total Games Played"]):,}</p>
                    </div>
                    <div class="search-metric-box">
                        <h3>Daily Rating ☀️</h3>
                        <p>{int(player["Daily Rating"]) if player["Daily Rating"] > 0 else "N/A"}</p>
                    </div>
                    <div class="search-metric-box">
                        <h3>Rapid Rating 🕐</h3>
                        <p>{int(player["Rapid Rating"]) if player["Rapid Rating"] > 0 else "N/A"}</p>
                    </div>
                    <div class="search-metric-box">
                        <h3>Blitz Rating ⚡</h3>
                        <p>{int(player["Blitz Rating"]) if player["Blitz Rating"] > 0 else "N/A"}</p>
                    </div>
                    <div class="search-metric-box">
                        <h3>Bullet Rating 🚀</h3>
                        <p>{int(player["Bullet Rating"]) if player["Bullet Rating"] > 0 else "N/A"}</p>
                    </div>
                    <div class="search-metric-box">
                        <h3>Join Date 🗓️</h3>
                        <p>{player["Join Date"] if pd.notna(player["Join Date"]) else "Unknown"}</p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )


            st.markdown("---")
            
            #Calculate rankings for sentence summary
            rankings = {}
            formats = ["Daily Rating", "Rapid Rating", "Blitz Rating", "Bullet Rating"]
            for fmt in formats:
                if player[fmt] > 0:
                    rankings[fmt] = (
                        data[data[fmt] > 0]
                        .sort_values(by=fmt, ascending=False)
                        .reset_index()
                        .query(f"Username == '{player['Username']}'")
                        .index[0]
                        +1
                    )
                else:
                    rankings[fmt] = "N/A"
            #Rank for total games played
            total_games_rank = (
                data.sort_values(by="Total Games Played", ascending=False)
                .reset_index()
                .query(f"Username == '{player['Username']}'")
                .index[0]
                + 1
            )
            #Display one sentence summary
            summary = (
                f"{player['Username']} is ranked "
                f"{total_games_rank} in Total Games Played, "
                f"{rankings['Daily Rating']} in Daily, "
                f"{rankings['Rapid Rating']} in Rapid, "
                f"{rankings['Blitz Rating']} in Blitz, "
                f"and {rankings['Bullet Rating']} in Bullet."
            )

            st.markdown(
                f"""
                <div style="font-size: 18px; line-height: 1.5; text-align: left;">
                    🏅 Rankings Summary: {summary}
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown("---")
            # Display detailed stats for each format
            st.markdown("#### 🎯 Format-Specific Stats")

            def format_stats(stats_name, games, wins, losses, draws):
                st.markdown(f"##### {stats_name}")
                st.write({
                    "Games Played": int(games),
                    "Wins": int(wins),
                    "Losses": int(losses),
                    "Draws": int(draws),
                })

            format_stats(
                "Daily Games",
                player["Total Daily Games"],
                player["Daily Wins"],
                player["Daily Losses"],
                player["Daily Draws"]
            )

            format_stats(
                "Rapid Games",
                player["Total Rapid Games"],
                player["Rapid Wins"],
                player["Rapid Losses"],
                player["Rapid Draws"]
            )

            format_stats(
                "Blitz Games",
                player["Total Blitz Games"],
                player["Blitz Wins"],
                player["Blitz Losses"],
                player["Blitz Draws"]
            )

            format_stats(
                "Bullet Games",
                player["Total Bullet Games"],
                player["Bullet Wins"],
                player["Bullet Losses"],
                player["Bullet Draws"]
            )
        else:
            st.error(f"No player found with username: {search_username}")
