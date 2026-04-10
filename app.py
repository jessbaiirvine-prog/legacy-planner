import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Legacy 8.1")

# --- UI STYLING ---
st.markdown("""
<style>
div[data-testid="metric-container"] {
    background-color: #1e1e2e; border: 1px solid #2b2b40;
    padding: 15px; border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# --- 1. SIDEBAR: TIMELINE & LIQUID ASSETS ---
sb = st.sidebar
sb.title("⚙️ Global Settings")
c_age = sb.slider("Current Age", 30, 65, 42)
y_ret = sb.slider("Your Retire Age", 45, 75, 55)
h_ret = sb.slider("Husband Retire Age", 45, 75, 58)
d_age = sb.slider("End Age", 80, 110, 95)

sb.subheader("💰 Liquid Portfolio")
v_tax = sb.number_input("Taxable Cash", 200000)
v_401k = sb.number_input("Deferred 401k", 1200000)
v_roth = sb.number_input("Roth IRA", 300000)
m_rate = sb.slider("Market Return %", 1, 10, 6) / 100

sb.subheader("📈 Careers & Kids")
h_net = sb.number_input("Husband Salary (Net)", 145000)
y_net = sb.number_input("Your Salary (Net)", 110000)
e_wrk = sb.number_input("Lifestyle Exp (Work)", 150000)
e_ret = sb.number_input("Lifestyle Exp (Retire)", 120000)
n_kid = sb.number_input("Number of Kids", 0, 5, 2)
tui = sb.number_input("Tuition/Year/Kid", 50000)
k_ages = [sb.number_input(f"K{i+1} College Start Age", 40, 75, 52+(i*6)) for i in range(int(n_kid))]

st.title("✨ Legacy Master v8.1")

# --- 2. REAL ESTATE ASSETS (DYNAMIC) ---
st.subheader("🏠 Real Estate Portfolio")
n_props = st.number_input("Number of Properties", 1, 10, 1)
p_data = []

# Using columns for the property inputs
for i in range(int(n_props)):
    with st.expander(f"Property {i+1} Details", expanded=(i==0)):
        c1, c2, c3 = st.columns(3)
        with c1:
            pv = st.number_input("Purchase Price", 0, 10**7, 950000 if i==0 else 0, key=f"pv{i}")
            pl = st.number_input("Loan Amount", 0, 10**7, 700000 if i==0 else 0, key=f"pl{i}")
        with c2:
            py = st.number_input("Year Bought", 1990, 2040, 2020 if i==0 else 2026, key=f"py{i}")
            pt = st.number_input("Term (Yrs)", 5, 50, 30, key=f"pt{i}")
        with c3:
            pi = st.number_input("Int. Rate %", 0.0, 15.0, 4.5, key=f"pi{i}") / 100
            pa = st.slider("Appreciation %", 0, 10, 3, key=f"pa{i}") / 100
        
        # New Feature: Cash Flow (NOI)
        p_noi = st.number_input("Monthly Net Rental Income (NOI)", -10000, 50000, 0, key=f"pnoi{i}")
        
        # Mtg Calculation
        ann_pmt = 0
        if pl > 0 and pi > 0:
            mi = pi / 12
            mt = pt * 12
            pwr = (1 + mi) ** mt
            mpmt = pl * (mi * pwr) / (pwr - 1)
            ann_pmt = mpmt * 12
        
        p_data.append({"v":pv, "l":pl, "y":py, "t":pt, "r":pi, "a":pa, "pmt":ann_pmt, "noi":p_noi * 12})

# --- 3. MATH ENGINE ---
sim = []
t_tax, t_401, t_rot = v_tax, v_401k, v_roth
now_y = 2026

for a in range(c_age, d_age + 1):
    yr = now_y + (a - c_age)
    
    # Portfolio Growth
    t_tax *= (1 + m_rate)
    t_401 *= (1 + m_rate)
    t_rot *= (1 + m_rate)
    
    # Inflow (Salary + SS)
    inc = (h_net if a < h_ret else 0) + (y_net if a < y_ret else 0)
    if a >= 67: inc += 85000
    
    # Outflow (Lifestyle + College)
    exp = e_ret if (a >= y_ret and a >= h_ret) else e_wrk
    edu = sum(tui for s in k_ages if s <= a < s + 4)
    
    # Real Estate Processing
    r_eq, r_pmt, r_inc = 0, 0, 0
    for p in p_data:
        h = yr - p["y"]
        if h < 0: continue
        
        # Value & Rental Income Appreciation
        cur_v = p["v"] * ((1 + p["a"]) ** h)
        cur_noi = p["noi"] * ((1 + p["a"]) ** h) # Rents grow with property
        
        # Debt Amortization
        if h >= p["t"]:
            cur_d = 0
        else:
            mi, mt, dn = p["r"]/12, p["
