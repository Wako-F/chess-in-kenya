import pandas as pd
import plotly.express as px

# Load the data
dfi = pd.read_csv('cleaned_master_chess_players.csv')

# Ensure 'Join Date' is in datetime format
dfi['Join Date'] = pd.to_datetime(dfi['Join Date'])

# Extract year and month
dfi['Year'] = dfi['Join Date'].dt.year
dfi['Month'] = dfi['Join Date'].dt.month

# Group by year and month to calculate join counts
monthly_counts = (
    dfi.groupby(['Year', 'Month'])
    .size()
    .reset_index(name='Join Count')
)

# Convert 'Month' to integer type to avoid parsing issues
monthly_counts['Month'] = monthly_counts['Month'].astype(int)

# Convert months to names for better readability
monthly_counts['Month Name'] = monthly_counts['Month'].apply(lambda x: pd.to_datetime(f'{x}', format='%m').strftime('%b'))

# Create a pivot table for the heatmap (Years x Months)
heatmap_data = monthly_counts.pivot(index='Year', columns='Month Name', values='Join Count').fillna(0)

# Sort months in calendar order
heatmap_data = heatmap_data[['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']]

# Plot the heatmap with annotations
fig = px.imshow(
    heatmap_data,
    labels=dict(x="Month", y="Year", color="Join Count"),
    
    title="Chess Players Join Activity Heatmap",
    color_continuous_scale="Viridis",
    aspect="auto",
    text_auto=True  # Annotate cells with values
)

# Customize layout for better readability
fig.update_layout(
    xaxis=dict(side="top"),  # Move month labels to the top
    title_font=dict(size=20),
    width=900,
    height=600,
    margin=dict(l=50, r=50, t=120, b=50)
)

# Show the heatmap
fig.show()
