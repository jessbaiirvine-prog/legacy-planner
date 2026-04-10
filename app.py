import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(page_title="Legacy Planner v5.6", layout="wide")

# --- MATH ENGINE (Moved up to generate metrics first) ---
def run_model(curr_age, y_ret, h_ret, ss_age, d_age, r40, r50, r60, n_kids, tui, k_starts, h_net, y_net, exp_w, exp_r, re_data):
    port = 1700000 
    res = []
    for a in range(curr_age, d_age + 1):
        rate = r60
        if a < 50: rate = r40
        elif a < 60: rate = r50
        
        growth = port * rate
        h_inc = h_net if a < h_ret else 0
        y_inc = y_net if a < y_ret else 0
        ss_inc = 85000 if a >= ss_age else 0
        rent_inc = sum([p["inc"] for p in re_data])
        mtg_pay = sum([p["pay"] for p in re_data if p["start"] <= a < p["end"]])
        edu = sum([tui for s in k_starts if s <= a < (s + 4)])
        liv = exp_r if (a >= y_ret and a >= h_ret) else exp_w
        
        net_cf = (h_inc + y_inc + ss_inc + rent_inc + growth) - (liv + mtg_pay + edu)
        port += net_cf
        res.append({"Age": a, "Growth": growth, "H": h_inc, "Y": y_inc, "SR": ss_inc+rent_inc, "Ex": -(liv+mtg_pay+edu), "Port": port})
    return pd.DataFrame(res)

# --- SIDEBAR: ALL INPUTS ---
with st.sidebar:
    st.header("1. Milestones")
    curr_age = st.slider("Current Age", 30, 65, 42)
    y_ret_age = st.slider("Your Retirement Age", 45, 75, 55)
    h_ret_age = st.slider("Husband Retirement Age", 45, 75, 58)
    ss_age = st.slider("Social Security Age", 62, 72, 67)
    d_age = st.slider("Simulation End", 80, 110, 95)
    
    st.header("2. Returns")
    r40 = st.slider("Returns 40s (%)", 0.0, 15.0, 7.0) / 100
    r50 = st.slider("Returns 50s (%)", 0.0, 15.0, 5.0) / 100
    r60 = st.slider("Returns 60+ (%)", 0.0, 10.0, 4.0) / 100

    st.header("3. Education")
    n_kids = st.number_input("Children", 0, 5, 2)
    tui = st.number_input("Annual Tuition ($)", value=50000)
    k_starts = [st.number_input(f"Child {i+1} Start", 40, 75, 52+(i*6), key=f"k{i}") for i in range(n_kids)]

    st.header("4. Finance")
    h_net = st.number_input("Husband Net ($)", value=145000)
    y_net = st.number_input("Your Net ($)", value=110000)
    exp_w = st.number_input("Working Expenses ($)", value=2
