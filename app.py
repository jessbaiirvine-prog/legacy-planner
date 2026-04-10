import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Legacy 7.7")

# --- UI STYLING ---
st.markdown("""
<style>
div[data-testid="metric-container"] {
    background-color: #1e1e2e; border: 1px solid #2b2b40;
    padding: 15px; border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# --- 1. SIDEBAR SETTINGS ---
sb = st.sidebar
sb.header("Timeline")
c_age = sb.slider("Current Age", 30, 65, 42)
y_ret = sb.slider("Your Retire Age", 45, 75, 55)
h_ret = sb.slider("Husband Retire Age", 45, 75, 58)
d_age = sb.slider("End Age", 80, 110, 95)

sb.header("Portfolio ($)")
v_tax = sb.number_input("Taxable Cash", 200000)
v_def = sb.number_input("Deferred 401k", 1200000)
v_rot = sb.number_input("Roth", 300000)

sb.header("Inflows & Outflows")
rate = sb.slider("Market Return %", 1, 10, 6) / 100
h_net = sb.number_input("Husband Net Salary", 145000)
y_net = sb.number_input("Your Net Salary", 110000)
e_wrk = sb.number_input("Work Exp (Excl Mtg)", 150000)
e_ret = sb.number_input("Retire Exp (Excl Mtg)", 120000)

sb.header("Education")
n_kid = sb.number_input("Kids", 0, 5, 2)
tui = sb.number_input("Tuition/Yr", 50000)
k_sts = []
for i in range(int(n_kid)):
    k_sts.append(sb.sidebar.number_input(f"K{i+1} Start Age", 40, 75, 52+(i*6)))

st.title("✨ Legacy Master v7.7")

# --- 2. ASSET INPUTS (HIDDEN FOR MATH) ---
# We define these here so the math can see them, 
# but they will be displayed in columns at the bottom.
p_data = []
for i in range(3):
    # Default values for initial load
    v_def_val = 950000 if i==0 else 0
    l_def_val = 700000 if i==0 else 0
    y_def_val = 2020 if i==0 else 2026
    
    # We use session state to bridge the "bottom of page" inputs to the math engine
    p_val = st.session_state.get(f"v{i}", v_def_val)
    p_loan = st.session_state.get(f"l{i}", l_def_val)
    p_yr = st.session_state.get(f"y{i}", y_def_val)
    p_term = st.session_state.get(f"t{i}", 30)
    p_int = st.session_state.get(f"i{i}", 4.5) / 100
    p_app
