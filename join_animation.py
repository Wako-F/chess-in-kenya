import pandas as pd
import plotly.graph_objects as go

# Load the data
dfi = pd.read_csv('cleaned_master_chess_players.csv')

# Ensure 'Join Date' is in datetime format
dfi['Join Date'] = pd.to_datetime(dfi['Join Date'])

# Sort by Join Date
dfi = dfi.sort_values('Join Date').reset_index(drop=True)

# Aggregate data by monthly intervals
df_monthly = (
    dfi.groupby(dfi['Join Date'].dt.to_period('M'))
    .size()
    .reset_index(name='Monthly Count')
    .sort_values('Join Date')
)
df_monthly['Join Date'] = df_monthly['Join Date'].dt.to_timestamp()  # Convert to timestamp

# Create animation frames
frames = []
for i in range(len(df_monthly)):
    frames.append(go.Frame(
        data=[
            go.Bar(
                x=df_monthly['Join Date'][:i+1],
                y=df_monthly['Monthly Count'][:i+1],
                name='Monthly Join Count',
                marker=dict(color='blue')
            )
        ],
        name=f"Frame {i}"
    ))

# Create the figure
fig = go.Figure(
    data=[
        go.Bar(
            x=[df_monthly['Join Date'].iloc[0]],
            y=[df_monthly['Monthly Count'].iloc[0]],
            name='Monthly Join Count',
            marker=dict(color='blue')
        )
    ],
    layout=go.Layout(
        title='Animated Monthly Join Counts of Chess Players',
        xaxis=dict(
            title='Join Date',
            rangeslider=dict(visible=True),  # Add a range slider for date selection
            type='date'
        ),
        yaxis=dict(title='Number of Players Joined'),
        width=1000,
        height=600,
        updatemenus=[
            dict(
                type='buttons',
                showactive=False,
                buttons=[
                    dict(
                        label='Play',
                        method='animate',
                        args=[None, dict(frame=dict(duration=500, redraw=True), fromcurrent=True)]
                    ),
                    dict(
                        label='Pause',
                        method='animate',
                        args=[[None], dict(frame=dict(duration=0, redraw=False), mode='immediate')]
                    )
                ]
            )
        ]
    ),
    frames=frames
)

# Show the figure
fig.show()
