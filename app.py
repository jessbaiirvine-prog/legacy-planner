import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(
    layout="wide", 
    page_title="Legacy 8.0"
)

# --- 1. THE LAYOUT SLOTS ---
# These hold the top spots 
# for the chart/metrics.
t_head = st.container()
t_chart = st.container()

# --- 2. SIDEBAR ---
sb = st.sidebar
sb.header("Timeline")
age = sb.slider("Age", 30, 65, 42)
y_r = sb.slider("You Ret", 45, 75, 55)
h_r = sb.slider("Hus Ret", 45, 75, 58)
e_a = sb.slider("End", 80, 110, 95)

sb.header("Portfolio")
v_t = sb.number_input("Tax", 200000)
v_d = sb.number_input("401k", 1200000)
v_r = sb.number_input("Roth", 300000)

sb.header("Cashflow")
m_r = sb.slider("Return %", 1, 10, 6)
m_r = m_r / 100
h_i = sb.number_input("Hus Net", 145000)
y_i = sb.number_input("You Net", 110000)
e_w = sb.number_input("Work Exp", 150000)
e_r = sb.number_input("Ret Exp", 120000)

sb.header("Kids")
n_k = sb.number_input("Count", 0, 5, 2)
tui = sb.number_input("Tuit", 50000)
k_s = []
for i in range(int(n_k)):
    k_v = sb.number_input(f"K{i+1} Start", 40, 75, 52+(i*6))
    k_s.append(k_v)

# --- 3. BOTTOM INPUTS ---
st.divider()
st.subheader("🏠 Real Estate")
cols = st.columns(3)
p_list = []

for i in range(3):
    with cols[i]:
        with st.container(border=True):
            st.write(f"P{i+1}")
            v = st.number_input("Price", 0, 10**7, 950000 if i==0 else 0, key=f"v{i}")
            l = st.number_input("Loan", 0, 10**7, 700000 if i==0 else 0, key=f"l{i}")
            y = st.number_input("Year", 1990, 2040, 2020 if i==0 else 2026, key=f"y{i}")
            t = st.number_input("Term", 5, 50, 30, key=f"t{i}")
            r = st.number_input("Rate %", 0.0, 15.0, 4.5, key=f"i{i}")
            r = r / 100
            g = st.slider("Appr %", 0, 10, 3, key=f"g{i}")
            g = g / 100

            pmt = 0
