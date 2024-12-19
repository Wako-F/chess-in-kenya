import pandas as pd
import plotly.graph_objects as go

# Load the data
dfi = pd.read_csv('cleaned_master_chess_players.csv')

# Ensure 'Join Date' is in datetime format
dfi['Join Date'] = pd.to_datetime(dfi['Join Date'])

# Extract the hour of the day
dfi['Hour'] = dfi['Join Date'].dt.hour

# Group by hour and calculate the number of joins
hourly_counts = dfi.groupby('Hour').size().reset_index(name='Join Count')

# Add a column for hour ranges (e.g., "0-1", "1-2")
hourly_counts['Hour Range'] = hourly_counts['Hour'].apply(lambda x: f"{x}:00-{x+1}:00")

# Create the polar bar chart
fig = go.Figure()

# Add the bars
fig.add_trace(go.Barpolar(
    r=hourly_counts['Join Count'],
    theta=hourly_counts['Hour'] * 15,  # Convert hour to angular position (360° = 24 hours)
    width=[15] * len(hourly_counts),  # Each bar spans 15 degrees
    marker_color=hourly_counts['Join Count'],
    marker_colorscale='Viridis',  # Use a smooth gradient for colors
    opacity=0.8,
    name='Join Count'
))

# Update the layout for aesthetics and readability
fig.update_layout(
    title='Peak Join Times (24-Hour Distribution)',
    polar=dict(
        angularaxis=dict(
            tickmode='array',
            tickvals=[i * 15 for i in range(24)],  # One tick per hour
            ticktext=[f"{h}:00" for h in range(24)],  # Labels formatted as "HH:00"
            direction='clockwise',
            rotation=90,  # Rotate the chart so midnight (0:00) is at the top
            tickfont=dict(size=12)
        ),
        radialaxis=dict(
            showticklabels=True,
            tickfont=dict(size=10),
            ticks='outside'
        )
    ),
    width=900,
    height=900,
    showlegend=False,
    margin=dict(l=50, r=50, t=80, b=50)
)

# Show the plot
fig.show()
