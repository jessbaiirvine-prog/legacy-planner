import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(page_title="Global Legacy Planner v3", layout="wide")

# Custom CSS for a professional look
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("🌏 Global Legacy Planner: Strategic Cash Flow & Education")
st.markdown("Detailed year-by-year breakdown of income, outflows, and long-term wealth trajectory.")
st.divider()

# --- SIDEBAR: INPUTS ---
with st.sidebar:
    st.header("1. Return Schedule")
    st.info("Set real return rates (adjusted for inflation) for each life stage.")
    ret_40s = st.slider("Returns in 40s (%)", 0.0, 15.0, 7.0) / 100
    ret_50s = st.slider("Returns in 50s (%)", 0.0, 15.0, 5.0) / 100
    ret_60plus = st.slider("Returns 60+ (%)", 0.0, 10.0, 4.0) / 100

    st.header("2. Asset Transition")
    current_age = st.slider("Current Age", 30, 65, 42)
    move_age = st.slider("Move Age", 45, 70, 55)
    liquid_assets = st.number_input("Starting Portfolio ($)", value=1700000, step=50000)
    re_equity = st.number_input("Real Estate Equity ($)", value=1450000, step=50000)

    st.header("3. Education Planning")
    num_kids = st.number_input("Number of Children", min_value=0, max_value=5, value=2)
    tuition_per_year = st.number_input("Annual Tuition per Child ($)", value=50000, step=5000)
    
    kid_starts = []
    for i in range(int(num_kids)):
        # Defaulting based on typical 8yr and 2yr old scenario
        default_start = 52 if i == 0 else 58
        start_age = st.number_input(f"Child
