import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(page_title="Global Legacy Master v5.1", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("🌏 Global Legacy Master v5.1")
st.markdown("Restored V3 Logic + Split Retirement + Fixed Scaling & Syntax")

# --- SIDEBAR: MULTI-STAGE CONTROLS ---
with st.sidebar:
    st.header("1. Critical Milestones")
    current_age = st.slider("Your Current Age", 30, 65, 42)
    your_retire_age = st.slider("Age YOU Stop Working", 45, 75, 55)
    husband_retire_age = st.slider("Age HUSBAND Stops Working", 45, 75, 58)
    ss_start_age = st.slider("Social Security Start Age", 62, 72, 67)
    death_age = st.slider("Simulation End (Death)", 80, 110, 95)
    
    st.header("2. Return Schedule")
    ret_40s = st.slider("Returns in 40s (%)", 0.0, 15.0, 7.0) / 100
    ret_50s = st.slider("Returns in 50s (%)", 0.0, 15.0, 5.0) / 100
    ret_60plus = st.slider("Returns 60+ (%)", 0.0, 10.0, 4.0) / 100

    st.header("3. Education Logic")
    num_kids = st.number_input("Number of Children", 0, 5, 2)
    tuition = st.number_input("Annual Tuition ($)", value=50000)
    kid_starts = [st.number_input(f"Child {i+1} Start Age", 40, 75, 52+(i*6), key=f"k{i}") for i in range(num_kids)]

    st.header("4. Direct Income Inputs")
    husband_net_ann = st.number_input("Husband Annual Net ($)", value=145000)
    your_net_ann = st.number_input("Your Annual Net ($)", value=110000)
    
    st.header("5. Living Expenses")
    exp_working = st.number_input("Expenses while Working ($)", value=210000)
    exp_retired = st.number_input("Expenses in Retirement ($)", value=150000)

# --- REAL ESTATE ENGINE ---
st.header("🏠 Real Estate Portfolio")
re_data = []
re_cols = st.columns(3)
for i in range(6):
    with re_cols[i % 3]:
        with st.expander(f"Property {i+1}", expanded=(i < 4)):
            is_pri = st.checkbox("Primary?", value=(i==0), key=f"p{i}")
            cf = 0 if is_pri else st.number_input("Annual Cashflow", value=7800 if i<4 else 0, key=f"c{i}")
            m
