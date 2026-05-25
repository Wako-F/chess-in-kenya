import os

import pandas as pd
import plotly.express as px
import requests
import streamlit as st


API_BASE = os.getenv("CHESSKE_API_BASE", "http://127.0.0.1:8000")


def get_json(path: str):
    r = requests.get(f"{API_BASE}{path}", timeout=30)
    r.raise_for_status()
    return r.json()


st.set_page_config(page_title="ChessKE Dashboard v2", layout="wide")
st.title("Online Chess in Kenya - Production Dashboard")

overview = get_json("/overview")
quality = get_json("/meta/quality")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Players", f"{overview['total_players']:,}")
col2.metric("Total Games", f"{overview['total_games']:,}")
col3.metric("Avg Rapid", f"{overview['average_ratings']['rapid'] or 0:.0f}")
col4.metric("Avg Blitz", f"{overview['average_ratings']['blitz'] or 0:.0f}")

st.caption(
    f"Latest run: {overview['latest_run']['status'] if overview['latest_run'] else 'unknown'} | "
    f"Snapshot coverage: {quality['latest_active_coverage_ratio']:.2%}"
)

tab1, tab2, tab3 = st.tabs(["Leaderboards", "Join Trends", "Player Search"])

with tab1:
    board = st.selectbox("Board", ["rapid", "blitz", "bullet", "daily", "puzzle", "games"])
    data = get_json(f"/leaderboards/{board}?limit=50&min_games=20")
    df = pd.DataFrame(data["items"])
    st.dataframe(df, use_container_width=True, hide_index=True)

with tab2:
    joins = get_json("/trends/joins?months=72")
    joins_df = pd.DataFrame(joins["items"])
    if not joins_df.empty:
        fig = px.line(joins_df, x="month", y="players", title="Monthly join trend")
        st.plotly_chart(fig, use_container_width=True)
    discovery = get_json("/trends/discovery?days=90")
    disc_df = pd.DataFrame(discovery["items"])
    if not disc_df.empty:
        fig2 = px.line(
            disc_df,
            x="day",
            y=["new_signups", "new_logins", "newly_discovered_active"],
            title="Daily signups, logins, and discovery",
        )
        st.plotly_chart(fig2, use_container_width=True)

with tab3:
    query = st.text_input("Username")
    if query:
        try:
            player = get_json(f"/players/{query.strip().lower()}")
            st.json(player)
        except Exception:
            st.error("Player not found.")

