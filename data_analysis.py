import pandas as pd
import matplotlib.pyplot as plt

file_path = "cleaned_kenyan_chess_players.csv"
data = pd.read_csv(file_path)

#Sort according to format ratings

bullet_players = data.sort_values(by="Bullet Rating", ascending=False)
rapid_players = data.sort_values(by="Rapid Rating", ascending=False)
blitz_players = data.sort_values(by="Blitz Rating", ascending=False)
daily_players = data.sort_values(by="Daily Rating", ascending=False)


bullet_players.to_csv("bullet_players_sorted.csv", index=False)
rapid_players.to_csv("rapid_players_sorted.csv", index=False)
blitz_players.to_csv("blitz_players_sorted.csv", index=False)
daily_players.to_csv("daily_players_sorted.csv", index=False)

#Sort data by total games played
by_games_played = data.sort_values(by="Total Games Played", ascending=False)
by_games_played.to_csv("games_played_sorted.csv", index=False)

#Sort by join date
by_join_date = data.sort_values(by="join_date", ascending=False)
by_join_date.to_csv("join_date_sorted.csv", index=False)

#Some visualizations for each format
#Rapid:

sorted_rapid_file = "rapid_players_sorted.csv"
sorted_rapid_data = pd.read_csv(sorted_rapid_file)

#Bar chart for top 10 Kenyan rapid players
top_n = 10
top_rapid_players = sorted_rapid_data.head(top_n)

plt.figure(figsize=(10,6))
plt.bar(top_rapid_players["username"], top_rapid_players["Rapid Rating"], color="#69923e")
plt.title("Top 10 Kenyan Players by Rapid Rating")
plt.xlabel("Player Username")
plt.ylabel("Rapid Rating")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

#Histogram for Kenyan rapid player ratings
plt.figure(figsize=(10,6))
plt.hist(sorted_rapid_data["Rapid Rating"], bins=20, color="#69923e", edgecolor="black", alpha=0.7)
plt.title("Distribution of Kenyan Rapid Ratings")
plt.xlabel("Rapid Rating")
plt.ylabel("Number of Players")
plt.tight_layout()
plt.show()

#Scatter plot for ratinngs vs players 
# Scatter plot: Total games vs. Rapid rating
# # Scatter plot with adjusted spacing
plt.figure(figsize=(12, 8))
plt.scatter(data['Total Rapid Games'], data['Rapid Rating'], s=10, color="#69923e", alpha=0.5, edgecolor='k')

# Log scale for better distribution
plt.xscale('log')

# Adding labels and title
plt.title("Correlation between Total Rapid Games and Rapid Rating", fontsize=16)
plt.xlabel("Total Rapid Games (Log Scale)", fontsize=12)
plt.ylabel("Rapid Rating", fontsize=12)

# Adding grid for readability
plt.grid(alpha=0.3)

# Show the plot
plt.tight_layout()
plt.show()

#Classifying players into clusters and plotting scatter plot
# # Define clusters
low_game_beginners = data[(data['Total Rapid Games'] < 10) & (data['Rapid Rating'] < 1000)]
intermediate_players = data[(data['Total Rapid Games'] >= 10) & (data['Total Rapid Games'] <= 100) & 
                            (data['Rapid Rating'] >= 1000) & (data['Rapid Rating'] <= 1800)]
advanced_players = data[(data['Total Rapid Games'] > 100) & (data['Rapid Rating'] > 1800)]
outliers = data[(data['Rapid Rating'] > 2000) & (data['Total Rapid Games'] < 50)]

# # Scatter plot with clusters
plt.figure(figsize=(12, 8))
plt.scatter(low_game_beginners['Total Rapid Games'], low_game_beginners['Rapid Rating'], 
            label="Low-Game Beginners", alpha=0.6, s=30, color='blue')
plt.scatter(intermediate_players['Total Rapid Games'], intermediate_players['Rapid Rating'], 
            label="Intermediate Players", alpha=0.6, s=30, color='green')
plt.scatter(advanced_players['Total Rapid Games'], advanced_players['Rapid Rating'], 
            label="Advanced Players", alpha=0.6, s=30, color='orange')
plt.scatter(outliers['Total Rapid Games'], outliers['Rapid Rating'], 
            label="Outliers", alpha=0.9, s=50, edgecolor='k', color='red')

# Log scale for X-axis
plt.xscale('log')

# Add labels and title
plt.title("Highlighting Clusters in Total Rapid Games vs Rapid Rating", fontsize=16)
plt.xlabel("Total Rapid Games (Log Scale)", fontsize=12)
plt.ylabel("Rapid Rating", fontsize=12)

# Add legend and grid
plt.legend()
plt.grid(alpha=0.3)

# Show the plot
plt.tight_layout()
plt.show()

# print("Sorted lists saved to respective files.")
