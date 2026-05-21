#-----------------------------------------------------
# GOAM 2026 Season Dashboard
# Displays:
# - Season-long IPS leaderboard and trends      
# - Gross/Nett averages
# - OX Nau leaderboard
# - LIV team standings
# - Monthly results browser
#-----------------------------------------------------

import streamlit as st
import pandas as pd
from utils.json_utils import load_json

def run():
    st.header("🏆 GOAM 2026 Season Dashboard")

    scores = load_json("data/goam_scores.json")
    if not scores:
        st.error("No GOAM scores found. Upload via Data Manager.")
        return

    # Convert JSON → DataFrame for season analysis
    season_rows = []
    for month, data in scores.items():
        for p in data["players"]:
            season_rows.append({
                "month": month,
                "course": data["course"],
                "name": p["name"],
                "strokes": p.get("strokes"),
                "nett": p.get("nett"),
                "ips": p.get("ips"),
                "team": p.get("team"),
                "ox_nau": 1 if data.get("ox_nau") == p["name"] else 0
            })

    df = pd.DataFrame(season_rows)

    # -----------------------------
    # Season IPS Leaderboard
    # -----------------------------
    st.subheader("🔥 Season IPS Leaderboard")

    ips_leaderboard = (
        df.groupby("name")["ips"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )

    st.dataframe(ips_leaderboard)

    # -----------------------------
    # Season Gross/Nett Leaderboard
    # -----------------------------
    st.subheader("📉 Season Gross & Nett Averages")

    gross_nett = (
        df.groupby("name")[["strokes", "nett"]]
        .mean()
        .sort_values("nett")
        .reset_index()
    )

    st.dataframe(gross_nett)

    # -----------------------------
    # OX Nau Leaderboard
    # -----------------------------
    st.subheader("🐂 OX Nau Leaderboard")

    ox_nau = (
        df.groupby("name")["ox_nau"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )

    st.dataframe(ox_nau)

    # -----------------------------
    # LIV Team Standings
    # -----------------------------
    st.subheader("🏁 LIV Team Standings")

    liv_totals = {}
    for month, data in scores.items():
        for team, pts in data.get("liv_totals", {}).items():
            liv_totals[team] = liv_totals.get(team, 0) + pts

    liv_df = (
        pd.DataFrame(list(liv_totals.items()), columns=["team", "points"])
        .sort_values("points", ascending=False)
    )

    st.dataframe(liv_df)

    # -----------------------------
    # Player IPS Trend
    # -----------------------------
    st.subheader("📈 Player IPS Trend")

    player = st.selectbox("Select player", sorted(df["name"].unique()))

    trend = df[df["name"] == player][["month", "ips"]].sort_values("month")

    st.line_chart(trend.set_index("month"))

    # -----------------------------
    # Monthly Results Browser
    # -----------------------------
    st.subheader("📅 Monthly Results")

    month = st.selectbox("Select month", sorted(scores.keys()))

    month_data = scores[month]
    players_df = pd.DataFrame(month_data["players"])
    st.dataframe(players_df)
