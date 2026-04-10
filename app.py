import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Legacy 7.2")

# --- UI STYLING ---
st.markdown("""
<style>
div[data-testid="metric-container"] {
    background-color: #1e1e2e;
    border: 1px solid #2b2b40;
    padding: 15px;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# --- 1. SETTINGS ---
sb = st.sidebar
sb.header("Timeline")
c_age = sb.slider("Current Age", 30, 65, 42)
y_ret = sb.slider("Your Retire", 45, 75, 55)
h_ret = sb.slider("Hus Retire", 45, 75, 58)
d_age = sb.slider("End Age", 80, 110, 95)

sb.header("Portfolio Breakdown ($)")
v_tax = sb.number_input("Taxable (Cash/Broker)", 200000)
v_def = sb.number_input("Deferred (401k)", 1200000)
v_rot = sb.number_input("Tax-Free (Roth)", 300000)

sb.header("Inflows & Outflows")
rate = sb.slider("Market Return %", 1, 10, 6) / 100
h_net = sb.number_input("Husband Net", 145000)
y_net = sb.number_input("Your Net", 110000)
e_wrk = sb.number_input("Work Exp", 210000)
e_ret = sb.number_input("Retire Exp", 150000)

sb.header("Education")
n_kid = sb.number_input("Number of Kids", 0, 5, 2)
tuition = sb.number_input("Annual Tuition ($)", 50000)
k_starts = []
for i in range(int(n_kid)):
    k_starts.append(sb.number_input(f"K{i+1} Start", 40, 75, 52+(i*6)))

st.title("✨ Legacy Master v7.2")

# --- 2. REAL ESTATE EQUITY ---
props = []
st.subheader("🏠 Real Estate Asset Portfolio")
cols = st.columns(3)
for i in range(3):
    with cols[i]:
        with st.expander(f"Property {i+1}", expanded=(i==0)):
            val = st.number_input("Current Value", 950000, key=f"v{i}")
            debt = st.number_input("Mtg Balance", 600000, key=f"b{i}")
            appr = st.slider("Appreciation %", 1, 10, 3, key=f"a{i}")/100
            pay = st.number_input("Annual Principal Paydown", 12000, key=f"p{i}")
            props.append({"v": val, "d": debt, "g": appr, "p": pay})

# --- 3. MATH ENGINE ---
sim_data = []
t_tax, t_def, t_rot = v_tax, v_def, v_rot

for age in range(c_age, d_age + 1):
    # Grow Portfolio
    t_tax += (t_tax * rate)
    t_def += (t_def * rate)
    t_rot += (t_rot * rate)
    
    # Incomes & SS
    inc_h = h_net if age < h_ret else 0
    inc_y = y_net if age < y_ret else 0
    inc_s = 85000 if age >= 67 else 0
    
    # Expenses
    exp_l = e_ret if (age >= y_ret and age >=
