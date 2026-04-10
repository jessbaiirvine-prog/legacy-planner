import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Legacy 8.4")

# --- 1. TOP DISPLAY SLOTS ---
t_head = st.container()
t_chart = st.container()

# --- 2. MODULAR SIDEBAR (LHS) ---
sb = st.sidebar
sb.title("⚙️ Strategic Planning")

# -- MODULE: RE INVESTMENT --
with sb.expander("🏠 RE INVESTMENT", expanded=True):
    n_p = st.number_input("Property Count", value=1)
    p_list = []
    for i in range(int(n_p)):
        st.markdown(f"**Property {i+1}**")
        v = st.number_input("Market Value", value=950000.0, key=f"v{i}")
        l = st.number_input("Loan Balance", value=700000.0, key=f"l{i}")
        y = st.number_input("Year Purchased", value=2020, key=f"y{i}")
        t = st.number_input("Loan Term (Yrs)", value=30, key=f"t{i}")
        r = st.number_input("Interest Rate %", value=4.5, key=f"r{i}") / 100
        a = st.number_input("Annual Appr %", value=3.0, key=f"a{i}") / 100
        n = st.number_input("Monthly Net Rent (NOI)", value=0.0, key=f"n{i}")
        
        pmt = 0
        if l > 0 and r > 0:
            mi, mt = r/12, t*12
            pw = (1 + mi)**mt
            mp = l * (mi * pw) / (pw - 1)
            pmt = mp * 12
        p_list.append({"v":v,"l":l,"y":y,"t":t,"r":r,"a":a,"p":pmt,"n":n*12})

# -- MODULE: RETIREMENT SAVINGS --
with sb.expander("🏦 RETIREMENT SAVINGS", expanded=False):
    v_401k = st.number_input("401k (Pre-Tax)", value=1200000.0)
    v_roth_401 = st.number_input("Roth 401k", value=100000.0)
    v_roth_ira = st.number_input("Roth IRA", value=200000.0)
    v_hsa = st.number_input("HSA Balance", value=50000.0)
    m_roi = st.number_input("Portfolio Return %", value=6.0) / 100

# -- MODULE: CASH ASSETS --
with sb.expander("💵 CASH ASSETS", expanded=False):
    v_cash = st.number_input("Checking/Savings Account", value=200000.0)
    h_pay = st.number_input("Husband Net Salary", value=145000.0)
    y_pay = st.number_input("Your Net Salary", value=110000.0)

# -- MODULE: KIDS TUITION --
with sb.expander("🎓 KIDS TUITION", expanded=False):
    n_k = st.number_input("Number of Kids", value=2)
    tui = st.number_input("Tuition per Year", value=50000.0)
    k_s = [st.number_input(f"K{i+1} College Start Age", value=52+(i*6)) for i in range(int(n_k))]

# -- MODULE: TIMELINE & EXPENSES --
with sb.expander("📅 TIMELINE & EXPENSES", expanded=False):
    c_a = st.number_input("Current Age", value=42)
    y_r = st.number_input("Your Retire Age", value=55)
    h_r = st.number_input("Husband Retire Age", value=58)
    e_a = st.number_input("Simulation End Age", value=95)
    ex_w = st.number_input("Annual Expense (Working)", value=150000.0)
    ex_r = st.number_input("Annual Expense (Retired)", value=120000.0)

# --- 3. MATH ENGINE ---
results = []
# Combined buckets for logic
curr_cash = v_cash
curr_def
