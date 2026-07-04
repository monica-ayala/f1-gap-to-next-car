import os
import warnings
warnings.filterwarnings('ignore')

import streamlit as st
import fastf1
import pandas as pd
import matplotlib.pyplot as plt

# -------------------------
# PAGE CONFIG
# -------------------------
st.set_page_config(
    page_title="F1 Gap to Car Ahead",
    layout="centered"
)

st.markdown("""
    <style>
        body {
            background-color: #0e1117;
            color: #ffffff;
        }
        .stApp {
            background-color: #0e1117;
        }
        h1, h2, h3 {
            color: #e10600;
        }
    </style>
""", unsafe_allow_html=True)

# -------------------------
# FASTF1 CACHE
# -------------------------
CACHE_DIR = "./f1_cache"
os.makedirs(CACHE_DIR, exist_ok=True)
fastf1.Cache.enable_cache(CACHE_DIR)

CURRENT_YEAR = 2026

# -------------------------
# FUNCTIONS
# -------------------------
def compute_gap_by_position(session, driver):
    laps = session.laps
    driver_laps = laps.pick_driver(driver).copy()
    driver_laps = driver_laps.sort_values('LapNumber')

    rows = []

    for _, lap in driver_laps.iterrows():
        lap_num = lap['LapNumber']
        position = lap['Position']
        lap_time_abs = lap['Time']

        if pd.isna(position) or pd.isna(lap_time_abs):
            continue

        if position <= 1:
            gap = 0.0
        else:
            same_lap = laps[laps['LapNumber'] == lap_num]
            ahead = same_lap[same_lap['Position'] == position - 1]

            if ahead.empty:
                continue

            ahead_time = ahead.iloc[0]['Time']
            gap = (lap_time_abs - ahead_time).total_seconds()

        rows.append({
            "Lap": lap_num,
            "Gap": gap
        })

    return pd.DataFrame(rows)


@st.cache_data
def load_schedule(year):
    return fastf1.get_event_schedule(year, include_testing=False)


@st.cache_data
def load_session(year, rnd, session_type):
    session = fastf1.get_session(year, rnd, session_type)
    session.load()
    return session

st.title("🏎️ Gap to Car Ahead")

# YEAR
year = st.selectbox(
    "Season",
    list(range(2018, CURRENT_YEAR + 1))[::-1]
)

# EVENT
schedule = load_schedule(year)

event_names = {
    f"Rd {int(row['RoundNumber'])} - {row['EventName']}": int(row['RoundNumber'])
    for _, row in schedule.iterrows()
}

event_label = st.selectbox("Grand Prix", list(event_names.keys()))
event_round = event_names[event_label]

# SESSION
session_type = st.selectbox(
    "Session",
    {
        "Race": "R",
        "Sprint": "S"
    }
)

# LOAD SESSION (auto)
with st.spinner("Loading session data..."):
    session = load_session(year, event_round, session_type)

drivers = sorted(session.laps['Driver'].unique())
driver = st.selectbox("Driver", drivers)

try:
    driver_info = session.get_driver(driver)
    team_color = f"#{driver_info['TeamColor']}"
except:
    team_color = "#ffffff"

df = compute_gap_by_position(session, driver)

if df.empty:
    st.warning("No data available.")
else:
    fig, ax = plt.subplots()

    ax.plot(
        df["Lap"],
        df["Gap"],
        color=team_color,
        linewidth=2
    )

    ax.set_title(f"{driver} — Gap to Car Ahead", color="white")
    ax.set_xlabel("Lap", color="white")
    ax.set_ylabel("Gap (s)", color="white")

    ax.grid(True, alpha=0.3)

    fig.patch.set_facecolor('#0e1117')
    ax.set_facecolor('#0e1117')
    ax.tick_params(colors='white')

    st.pyplot(fig)