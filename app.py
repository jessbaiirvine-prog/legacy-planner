import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(page_title="Global Legacy Master v5.3", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("🌏 Global Legacy Master v5.3")
st.markdown("Comprehensive Wealth & Milestone Tracking")

# --- SIDEBAR: MULTI-STAGE CONTROLS ---
with st.sidebar:
    st.header("1. Critical Milestones")
    curr_age = st.slider("Your Current Age", 30, 65, 42)
    your_ret_age = st.slider("Age YOU Stop Working", 45, 75, 55)
    h_ret_age = st.slider("Age HUSBAND Stops Working", 45, 75, 58)
    ss_age = st.slider("Social Security Start Age", 62, 72, 67)
    d_age = st.slider("Simulation End (Death)", 80, 110, 95)
    
    st.header("2. Return Schedule")
    r40 = st.slider("Returns in 40s (%)", 0.0, 15.0, 7.0) / 100
    r50 = st.slider("Returns in 50s (%)", 0.0, 15.0, 5.0) / 100
    r60 = st.slider("Returns 60+ (%)", 0.0, 10.0, 4.0) / 100

    st.header("3. Education Logic")
    n_kids = st.number_input("Number of Children", 0, 5, 2)
    tuition = st.number_input("Annual Tuition ($)", value=50000)
    k_starts = [st.number_input(f"Child {i+1} Start", 40, 75, 52+(i*6), key=f"k{i}") for i in range(n_kids)]

    st.header("4. Direct Income Inputs")
    h_net = st.number_input("Husband Annual Net ($)", value=145000)
    y_net = st.number_input("Your Annual Net ($)", value=110000)
    
    st.header("5. Living Expenses")
    exp_w = st.number_input("Expenses while Working ($)", value=210000)
    exp_r = st.number_input("Expenses in Retirement ($)", value=150000)

# --- REAL ESTATE ENGINE ---
st.header("🏠 Real Estate Portfolio")
re_data = []
re_cols = st.columns(3)
for i in range(6):
    with re_cols[i % 3]:
        with st.expander(f"Property {i+1}", expanded=(i < 4)):
            is_pri = st.checkbox("Primary?", value=(i==0), key=f"p{i}")
            cf = 0 if is_pri else st.number_input("Annual Cashflow", value=7800 if i<4 else 0, key=f"c{i}")
            m_s = st.number_input("Mtg Start Age", value=35, key=f"s{i}")
            m_t = st.number_input("Term (Yrs)", value=30, key=f"t{i}")
            m_p = st.number_input("Mtg Payment", value=15000 if i<4 else 0, key=f"m{i}")
            re_data.append({"inc": cf, "start": m_s, "end": m_s+m_t, "pay": m_p})

# --- MATH ENGINE ---
def run_model():
    portfolio = 1700000 
    results = []
    
    for a in range(curr_age, d_age + 1):
        # 1. Growth
        rate = r40 if a < 50 else (r50 if a < 60
