import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(layout="wide", page_title="Legacy 7.5")

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
curr_yr = 2026
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
h_net = sb.number_input("Husband Net", 145000)
y_net = sb.number_input("Your Net", 110000)
e_wrk = sb.number_input("Work Exp (Excl Mtg)", 150000)
e_ret = sb.number_input("Retire Exp (Excl Mtg)", 120000)

st.title("✨ Legacy Master v7.5")

# --- 2. REAL ESTATE INPUTS (AT BOTTOM IN UI, BUT DEFINED HERE) ---
# Using placeholders for the loop, actual values come from inputs at the bottom
prop_configs = []
st.info("💡 Real Estate inputs are now at the bottom of the page.")

# --- 3. MATH ENGINE ---
sim_data = []
t_tax, t_def, t_rot = v_tax, v_def, v_rot

# We will collect the RE inputs here (even though they display at the bottom)
# This uses Streamlit's ability to reference widgets defined later
for i in range(3):
    with st.container(): # Dummy container for logic
        p_val = st.session_state.get(f"v_in_{i}", 950000 if i==0 else 0)
        p_loan = st.session_state.get(f"l_in_{i}", 700000 if i==0 else 0)
        p_yr = st.session_state.get(f"y_in_{i}", 2020 if i==0 else 2026)
        p_term = st.session_state.get(f"t_in_{i}", 30)
        p_int = st.session_state.get(f"i_in_{i}", 4.5) / 100
        p_appr = st.session_state.get(f"g_in_{i}", 3.0) / 100
        
        # Calculate Monthly Payment (PI)
        if p_loan > 0 and p_int > 0:
            m_int = p_int / 12
            m_term = p_term * 12
            m_pmt = p_loan * (m_int * (1+m_int)**m_term) / ((1+m_int)**m_term - 1)
        else:
            m_pmt = 0
            
        prop_configs.append({
            "val": p_val, "loan_orig": p_loan, "yr_start": p_yr,
            "term": p_term, "rate": p_int, "appr": p_appr, "pmt": m_pmt * 12
        })

for age in range(c_age, d_age + 1):
    sim_yr = curr_yr + (age - c_age)
    
    # Growth
    t_tax *= (1 + rate)
    t_def *= (1 + rate)
    t_rot *= (1 + rate)
    
    # Income
    inc = (h_net if age < h_ret else 0) + (y_net if age < y_ret else 0)
    if age >= 67: inc += 85000
    
    # Expenses
