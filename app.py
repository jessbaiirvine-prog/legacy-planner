import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Legacy Master 9.6")

# --- 1. SIDEBAR MODULES ---
sb = st.sidebar
sb.title("⚙️ Strategic Planning")

with sb.expander("🏠 RE INVESTMENT", expanded=True):
    np = sb.number_input("Property Count", value=1)
    plist = []
    for i in range(int(np)):
        st.markdown(f"**Property {i+1}**")
        v = st.number_input("Current Value", value=950000.0, key=f"v{i}")
        l = st.number_input("Loan Balance", value=700000.0, key=f"l{i}")
        y = st.number_input("Year Purchased", value=2020, key=f"y{i}")
        t = st.number_input("Loan Term (Yrs)", value=30, key=f"t{i}")
        r = st.number_input("Int. Rate %", value=4.5, key=f"r{i}") / 100
        a = st.number_input("Annual Appr %", value=3.0, key=f"a{i}") / 100
        n = st.number_input("Monthly Net Rent", value=0.0, key=f"n{i}")
        p = 0
        if l > 0 and r > 0:
            mi = r / 12
            mt = t * 12
            pw = (1 + mi)**mt
            p = l * (mi * pw) / (pw - 1)
        plist.append({"v":v,"l":l,"y":y,"t":t,"r":r,"a":a,"p":p*12,"n":n*12})

with sb.expander("🏦 RETIREMENT", expanded=False):
    v_d = st.number_input("401k (Pre-Tax)", value=1200000.0)
    v_r = st.number_input("Roth/HSA", value=150000.0)
    roi = st.number_input("Market ROI %", value=6.0) / 100

with sb.expander("🎓 KIDS TUITION", expanded=False):
    nk = st.number_input("Number of Kids", value=2)
    tui_yr = st.number_input("Annual Tuition per Kid", value=50000.0)
    # Using specific ages for Aaron (8) and Alvin (3) logic
    k_ages = []
    for i in range(int(nk)):
        k_ages.append(st.number_input(f"Child {i+1} College Start Age", value=52+(i*5)))

with sb.expander("💵 CASH & TIMELINE", expanded=False):
    v_c = st.number_input("Current Savings", value=200000.0)
    hp, yp = st.number_input("Husband Net", 145000.0), st.number_input("Your Net", 110000.0)
    ca, yr, ea = st.number_input("Current Age", 42), st.number_input("Retire Age", 55), st.number_input("End Age", 95)
    ew, er = st.number_input("Exp (Work)", 150000.0), st.number_input("Exp (Retire)", 120000.0)

# --- 2. MATH ENGINE ---
res, cc, cd, cr, fyr = [], v_c, v_d, v_r, None

for age in range(int(ca), int(ea) + 1):
    sim_yr = 2026 + (age - int(ca))
    cc *= 1.02 # Cash stays at 2%
    cd *= (1 + roi)
    cr *= (1 + roi)
    
    inc = (hp + yp) if age < yr else 85000
