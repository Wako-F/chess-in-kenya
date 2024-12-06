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
        border-radius: 10px;
        padding: 10px;
        box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
        margin: 10px 0;
    }
    .metric-container h1 {
        font-size: 20px;
        margin: 0;
    }
    
    </style>
    """,
    unsafe_allow_html=True,
)


# Load Data
@st.cache_data
def load_data(filename):
    return pd.read_csv(filename)

data = load_data("cleaned_chess_players.csv")

# Dashboard Title
st.markdown("# Online Chess in Kenya ♚")

# Overview Metrics
st.markdown("## 🌟 Overview Metrics")

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
    <div style="text-align: center; font-size: 1.5rem; font-weight: bold; margin-bottom: 1rem;">
        Total Games Played: {total_games:,}
    </div>
    """,
    unsafe_allow_html=True,
)

# Layout for other metrics
col1, col2, col3, col4 = st.columns(4)

# Display metrics
col1.metric("Total Players", total_players)
col2.metric("Avg. Rapid Rating", f"{average_rapid_rating:.2f}")
col3.metric("Avg. Blitz Rating", f"{average_blitz_rating:.2f}")
col4.metric("Avg. Bullet Rating", f"{average_bullet_rating:.2f}")

# Player Search
st.markdown("## 🔎 Search Player Stats")

# Text input for searching a player's username
search_username = st.text_input("Enter Username to Search", placeholder="Type a username...")

# Check if the user has entered a username
if search_username:
    # Filter the data for the entered username (case-insensitive)
    player_data = data[data["Username"].str.contains(search_username, case=False, na=False)]
    
    if not player_data.empty:
        # Extract the first matched player's stats
        player = player_data.iloc[0]
        
        st.markdown(f"### 📊 Stats for **{player['Username']}**")
        
        # Display overall stats in columns
        st.markdown("#### 🏆 Overview")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Games", int(player["Total Games Played"]))
        col2.metric("Daily Rating", int(player["Daily Rating"]) if player["Daily Rating"] > 0 else "N/A")
        col3.metric("Rapid Rating", int(player["Rapid Rating"]) if player["Rapid Rating"] > 0 else "N/A")
        col4.metric("Blitz Rating", int(player["Blitz Rating"]) if player["Blitz Rating"] > 0 else "N/A")

        col5, col6 = st.columns(2)
        col5.metric("Bullet Rating", int(player["Bullet Rating"]) if player["Bullet Rating"] > 0 else "N/A")
        col6.metric("Join Date", player["Join Date"] if pd.notna(player["Join Date"]) else "Unknown")
        
        # Display detailed stats for each format
        st.markdown("#### 🎯 Format-Specific Stats")
        st.markdown("##### Daily Games")
        st.write({
            "Games Played": int(player["Total Daily Games"]),
            "Wins": int(player["Daily Wins"]),
            "Losses": int(player["Daily Losses"]),
            "Draws": int(player["Daily Draws"]),
        })

        st.markdown("##### Rapid Games")
        st.write({
            "Games Played": int(player["Total Rapid Games"]),
            "Wins": int(player["Rapid Wins"]),
            "Losses": int(player["Rapid Losses"]),
            "Draws": int(player["Rapid Draws"]),
        })

        st.markdown("##### Blitz Games")
        st.write({
            "Games Played": int(player["Total Blitz Games"]),
            "Wins": int(player["Blitz Wins"]),
            "Losses": int(player["Blitz Losses"]),
            "Draws": int(player["Blitz Draws"]),
        })

        st.markdown("##### Bullet Games")
        st.write({
            "Games Played": int(player["Total Bullet Games"]),
            "Wins": int(player["Bullet Wins"]),
            "Losses": int(player["Bullet Losses"]),
            "Draws": int(player["Bullet Draws"]),
        })
    else:
        st.error(f"No player found with username: {search_username}")


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

# Top Players by Rating
st.markdown("## 🏆 Top Players by Rating")

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



# Games Played Per Format
st.markdown("## Games Played Per Format")
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

# Win/Loss/Draw Summary
st.markdown("## Win/Loss/Draw Summary")

# Extract data for win/loss/draw statistics
summary_data = {
    "Daily": data[["Daily Wins", "Daily Losses", "Daily Draws"]].sum().tolist(),
    "Rapid": data[["Rapid Wins", "Rapid Losses", "Rapid Draws"]].sum().tolist(),
    "Blitz": data[["Blitz Wins", "Blitz Losses", "Blitz Draws"]].sum().tolist(),
    "Bullet": data[["Bullet Wins", "Bullet Losses", "Bullet Draws"]].sum().tolist(),
}

# Convert summary to a DataFrame
summary_df = pd.DataFrame.from_dict(summary_data, orient="index", columns=["Wins", "Losses", "Draws"])

# Reset index for Plotly compatibility
summary_df.reset_index(inplace=True)
summary_df.rename(columns={"index": "Format"}, inplace=True)

# Plotly bar chart
fig_summary = px.bar(
    summary_df.melt(id_vars="Format", var_name="Result Type", value_name="Count"),
    x="Format",
    y="Count",
    color="Result Type",
    barmode="group",
    title="Win/Loss/Draw Summary Across Formats",
    labels={"Format": "Game Format", "Count": "Total Count", "Result Type": "Result"},
    template="plotly_white",
)

st.plotly_chart(fig_summary, use_container_width=True)

# Filter data to discard users with less than 10 games
filtered_data = data[data["Total Games Played"] >= 10]

# Player Activity Visualization with Logarithmic Scale
st.markdown("## 🎮 Player Activity")

# Create scatter plot with logarithmic scale and hover info
fig_log = px.scatter(
    filtered_data,
    x="Total Games Played",
    y=filtered_data.index,  # Use index to represent players
    # color_discrete_sequence=["#69923e"],  # Set dot color to #69923e
    labels={
        "Total Games Played": "Total Games Played",
        "index": "Player Index"
    },
    hover_data={
        "Username": True,  # Include username in hover data
        "Total Games Played": True  # Include total games in hover data
    },
    title="Player Activity Distribution (Logarithmic Scale)",
    log_x=True,  # Logarithmic scale for x-axis
    template="plotly_white"
)

# Update layout for better visualization
fig_log.update_layout(
    xaxis_title="Total Games Played (Log Scale)",
    yaxis_title="Player Index",
    # title_font=dict(size=20),
    margin=dict(l=50, r=50, t=70, b=50),

)

# Display the chart
st.plotly_chart(fig_log, use_container_width=True)






# Joining Trend Over Time
st.markdown("## Joining Trend Over Time")

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
st.markdown("### Filter by Date Range")
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

# Footer
st.markdown(
    """
    ---
    **Dashboard powered by Streamlit 🚀 | Visualizations by Plotly 📊**
    """
)

# Auto-refresh button
if st.button("Refresh Data"):
    st.cache_data.clear()
    # st.experimental_rerun()
