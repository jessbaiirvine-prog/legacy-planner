import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Legacy 7.6")

# --- UI STYLING ---
st.markdown("""
<style>
div[data-testid="metric-container"] {
    background-color: #1e1e2e; border: 1px solid #2b2b40;
    padding: 15px; border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# --- 1. SETTINGS & TIMELINE ---
sb = st.sidebar
sb.header("Timeline")
c_age = sb.slider("Current Age", 30, 65, 42)
y_ret = sb.slider("Your Retire Age", 45, 75, 55)
h_ret = sb.slider("Husband Retire Age", 45, 75, 58)
d_age = sb.slider("End Age", 80, 110, 95)

sb.header("Portfolio ($)")
v_tax = sb.number_input("Taxable Cash/Brokerage", 200000)
v_def = sb.number_input("Tax-Deferred (401k)", 1200000)
v_rot = sb.number_input("Tax-Free (Roth)", 300000)

sb.header("Inflows & Outflows")
rate = sb.slider("Market Return %", 1, 10, 6) / 100
h_net = sb.number_input("Husband Net Salary", 145000)
y_net = sb.number_input("Your Net Salary", 110000)
e_wrk = sb.number_input("Work Lifestyle Exp (Excl Mtg)", 150000)
e_ret = sb.number_input("Retire Lifestyle Exp (Excl Mtg)", 120000)

sb.header("Education")
n_kid = sb.number_input("Number of Kids", 0, 5, 2)
tui = sb.number_input("Annual Tuition ($)", 50000)
k_sts = [sb.number_input(f"K{i+1} Start Age", 40, 75, 52+(i*6)) for i in range(int(n_kid))]

st.title("✨ Legacy Master v7.6")

# --- 2. REAL ESTATE ENGINE (VISIBLE INPUTS) ---
st.subheader("🏠 Real Estate Asset Portfolio")
props = []
cols = st.columns(3)
for i in range(3):
    with cols[i]:
        with st.expander(f"Property {i+1}", expanded=(i==0)):
            p_val = st.number_input("Purchase Price", 950000 if i==0 else 0, key=f"v{i}")
            p_loan = st.number_input("Orig. Loan", 700000 if i==0 else 0, key=f"l{i}")
            p_yr = st.number_input("Year Bought", 1990, 2030, 2020 if i==0 else 2026, key=f"y{i}")
            p_term = st.number_input("Term (Yrs)", 5, 50, 30, key=f"t{i}")
            p_int = st.number_input("Int. Rate (%)", 0.0, 15.0, 4.5, key=f"i{i}") / 100
            p_appr = st.slider("Appreciation %", 0, 10, 3, key=f"g{i}") / 100
            
            # Amortization Formula for Annual Payment
            if p_loan > 0 and p_int > 0:
                m_int = p_int / 12
                m_months = p_term * 12
                m_pmt = p_loan * (m_int * (1+m_int)**m_months) / ((1+m_int)**m_months - 1)
                ann_pmt =
