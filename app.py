import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Legacy 7.1")

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
ca = sb.slider("Current Age", 30, 65, 42)
yr = sb.slider("Your Retire", 45, 75, 55)
hr = sb.slider("Hus Retire", 45, 75, 58)
da = sb.slider("End Age", 80, 110, 95)

sb.header("Portfolio Breakdown ($)")
v_tx = sb.number_input("Taxable (Cash/Broker)", 200000)
v_td = sb.number_input("Tax-Deferred (401k)", 1200000)
v_ro = sb.number_input("Tax-Free (Roth)", 300000)

sb.header("Inflows & Outflows")
rt = sb.slider("Market Return %", 1, 10, 6) / 100
hn = sb.number_input("Husband Net", 145000)
yn = sb.number_input("Your Net", 110000)
ew = sb.number_input("Work Exp", 210000)
er = sb.number_input("Retire Exp", 150000)

sb.header("Education")
nk = sb.number_input("Number of Kids", 0, 5, 2)
tui = sb.number_input("Annual Tuition ($)", 50000)
ks = [sb.number_input(f"K{i+1} Start", 40, 75, 52+(i*6), key=f"k{i}") for i in range(nk)]

st.title("✨ Legacy Master v7.1")

# --- 2. REAL ESTATE EQUITY ---
re_list = []
st.subheader("🏠 Real Estate Asset Portfolio")
cl = st.columns(3)
for i in range(3):
    with cl[i]:
        with st.expander(f"Property {i+1}", expanded=(i==0)):
            cv = st.number_input("Current Value", 950000, key=f"v{i}")
            mb = st.number_input("Mtg Balance", 600000, key=f"b{i}")
            ag = st.slider("Appreciation %", 1, 10, 3, key=f"g{i}")/100
            pd_amt = st.number_input("Annual Principal Paydown", 12000, key=f"d{i}")
            re_list.append({"val": cv, "debt": mb, "appr": ag, "pay": pd_amt})

# --- 3. MATH ENGINE ---
res = []
tx, td, ro = v_tx, v_td, v_ro

# Ensure simulation runs even if ages are close
sim_range = range(ca, max(ca + 1, da + 1))

for a in range(ca, da + 1):
    # Grow Portfolio
    tx += (tx * rt)
    td += (td * rt)
    ro += (ro * rt)
    
    # Incomes & SS (Age 67)
    hi = hn if a < hr else 0
    yi = yn if a < yr else 0
    ss = 85000 if a >= 67 else 0
    
    # Expenses (Work vs Retire)
    lv = er if (a >= yr and a >= hr) else ew
    
    # Tuition Logic
    ed = sum([tui for s in ks if s <= a < s + 4])
    
    # Net Cashflow
    net_cf = (hi + yi + ss) - (lv + ed)
    tx += net_cf
    
    # Real Estate Growth
    re
