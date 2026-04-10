import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Legacy Master 9.0")

# --- 1. SIDEBAR MODULES (LHS) ---
st.sidebar.title("⚙️ Strategic Planning")

# -- MODULE 1: RE INVESTMENT (TOP) --
with st.sidebar.expander("🏠 RE INVESTMENT", expanded=True):
    n_p = st.number_input("Property Count", value=1, min_value=0)
    p_list = []
    for i in range(int(n_p)):
        st.markdown(f"**Property {i+1}**")
        v = st.number_input("Market Value", value=950000.0, key=f"re_v{i}")
        l = st.number_input("Loan Balance", value=700000.0, key=f"re_l{i}")
        y = st.number_input("Year Purchased", value=2020, key=f"re_y{i}")
        t = st.number_input("Loan Term (Yrs)", value=30, key=f"re_t{i}")
        r = st.number_input("Interest Rate %", value=4.5, key=f"re_r{i}") / 100
        a = st.number_input("Annual Appr %", value=3.0, key=f"re_a{i}") / 100
        n = st.number_input("Monthly Net Rent (NOI)", value=0.0, key=f"re_n{i}")
        
        ann_pmt = 0
        if l > 0 and r > 0:
            mi, mt = r/12, t*12
            pw = (1 + mi)**mt
            mp = l * (mi * pw) / (pw - 1)
            ann_pmt = mp * 12
        p_list.append({"v":v,"l":l,"y":y,"t":t,"r":r,"a":a,"p":ann_pmt,"n":n*12})

# -- MODULE 2: RETIREMENT SAVINGS --
with st.sidebar.expander("🏦 RETIREMENT SAVINGS", expanded=False):
    v_401k = st.number_input("401k (Pre-Tax)", value=1200000.0)
    v_r401 = st.number_input("Roth 401k", value=100000.0)
    v_rira = st.number_input("Roth IRA", value=200000.0)
    v_hsa = st.number_input("HSA Balance", value=50000.0)
    m_roi = st.number_input("Portfolio Return %", value=6.0) / 100

# -- MODULE 3: CASH ASSETS --
with st.sidebar.expander("💵 CASH ASSETS", expanded=False):
    v_csh = st.number_input("Checking/Savings Account", value=200000.0)
    h_pay = st.number_input("Husband Net Salary", value=145000.0)
    y_pay = st.number_input("Your Net Salary", value=110000.0)

# -- MODULE 4: KIDS TUITION --
with st.sidebar.expander("🎓 KIDS TUITION", expanded=False):
    n_k = st.number_input("Number of Kids", value=2, min_value=0)
    tui = st.number_input("Tuition per Year", value=50000.0)
    k_s = [st.number_input(f"K{i+1} College Start Age", value=52+(i*6)) for i in range(int(n_k))]

# -- MODULE 5: TIMELINE & EXPENSES --
with st.sidebar.expander("📅 TIMELINE & EXPENSES", expanded=False):
    c_a = st.number_input("Current Age", value=42)
    y_r = st.number_input("Your Retire Age", value=55)
    h_r = st.number_input("Husband Retire Age", value=58)
    e_a = st.number_input("Simulation End Age", value=95)
    ex_w = st.number_input("Annual Expense (Working)", value=150000.0)
    ex_r = st.number_input("Annual Expense (Retired)", value=120000.0)

# --- 2. MATH ENGINE ---
results = []
cur_c, cur_d, cur_r = v_csh, v_401k, (v_r401 + v_rira + v_hsa)
ruin_yr = None

# Force a valid loop range
start_age = int(c_a)
end_age = int(max(c_a + 1, e_a))

for age in range(start_age, end_age + 1):
    yr = 2026 + (age - start_age)
    cur_c *= (1 + (m_roi * 0.2)) 
    cur_d *= (1 + m_roi)
    cur_r *= (1 + m_roi)
    
    inc = (h_pay if age < h_r else 0) + (y_pay if age < y_r else 0)
    if age >= 67: inc += 85000 
    
    exp = ex_r if (age >= y_r and age >= h_r) else ex_w
    edu = sum(tui for s_age in k_s if s_age <= age < s_age + 4)
    
    re_eq, re_pmt, re_noi = 0, 0, 0
    for p in p_list:
        h = yr - p["y"]
        if h < 0: continue
        val = p["v"] * ((1 + p["a"]) ** h)
        noi = p["n"] * ((1 + p["a"]) ** h)
        if h >= p["t"]:
            deb = 0
        else:
            mi, mt, dn = p["r"]/12, p["t"]*12, h*12
            pm, pd = (1+mi)**mt, (1+mi)**dn
            deb = p["l"] * (pm - pd) / (pm - 1)
            re_pmt += p["p"]
        re_eq += (val - deb)
        re_noi += noi
