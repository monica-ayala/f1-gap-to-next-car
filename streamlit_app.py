import os
import warnings
warnings.filterwarnings('ignore')

import streamlit as st
import fastf1
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# -------------------------
# CONFIG
# -------------------------
st.set_page_config(page_title="F1 Gap to Car Ahead", layout="centered")

CACHE_DIR = "./f1_cache"
os.makedirs(CACHE_DIR, exist_ok=True)
fastf1.Cache.enable_cache(CACHE_DIR)

CURRENT_YEAR = 2026

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

st.title("🏎️ Gap to Car Ahead Visualizer")

year = st.selectbox("Year", list(range(2018, CURRENT_YEAR + 1))[::-1])

# Load events
@st.cache_data
def load_schedule(year):
    return fastf1.get_event_schedule(year, include_testing=False)

schedule = load_schedule(year)

event_names = {
    f"Rd {int(row['RoundNumber'])} - {row['EventName']}": int(row['RoundNumber'])
    for _, row in schedule.iterrows()
}

event_label = st.selectbox("Event", list(event_names.keys()))
event_round = event_names[event_label]

session_type = st.selectbox("Session", ["R", "S"])  # Race or Sprint

# Load session
@st.cache_data
def load_session(year, rnd, session_type):
    session = fastf1.get_session(year, rnd, session_type)
    session.load()
    return session

if "session_obj" not in st.session_state:
    st.session_state.session_obj = None
if "session_key" not in st.session_state:
    st.session_state.session_key = None

current_key = (year, event_round, session_type)

if st.button("Load Session"):
    with st.spinner("Loading session data..."):
        st.session_state.session_obj = load_session(year, event_round, session_type)
        st.session_state.session_key = current_key

if st.session_state.session_obj is not None and st.session_state.session_key == current_key:
    session = st.session_state.session_obj
    drivers = sorted(session.laps['Driver'].unique())
    driver = st.selectbox("Driver", drivers)

    if st.button("Generate Plot"):
        df = compute_gap_by_position(session, driver)

        if df.empty:
            st.warning("No data available.")
        else:
            fig, ax = plt.subplots()
            ax.plot(df["Lap"], df["Gap"])
            ax.set_title(f"{driver} - Gap to Car Ahead")
            ax.set_xlabel("Lap")
            ax.set_ylabel("Gap (s)")
            ax.grid(True)

            st.pyplot(fig)
elif st.session_state.session_obj is not None and st.session_state.session_key != current_key:
    st.info("Year/Event/Session changed — click **Load Session** again to load the new selection.")