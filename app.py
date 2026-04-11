import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import json
from io import BytesIO

st.set_page_config(layout="wide", page_title="Legacy Master 13.6")

# --- 0. HISTORICAL DATASET ---
hist_data = [
    {"Year": 1994, "Stocks": 0.013, "RE": 0.020, "Inflation": 0.026},
    {"Year": 1995, "Stocks": 0.376, "RE": 0.015, "Inflation": 0.028},
    {"Year": 1996, "Stocks": 0.230, "RE": 0.020, "Inflation": 0.030},
    {"Year": 1997, "Stocks": 0.334, "RE": 0.030, "Inflation": 0.023},
    {"Year": 1998, "Stocks": 0.286, "RE": 0.050, "Inflation": 0.016},
    {"Year": 1999, "Stocks": 0.210, "RE": 0.060, "Inflation": 0.022},
    {"Year": 2000, "Stocks": -0.091, "RE": 0.080, "Inflation": 0.034},
    {"Year": 2001, "Stocks": -0.119, "RE": 0.075, "Inflation": 0.028},
    {"Year": 2002, "Stocks": -0.221, "RE": 0.090, "Inflation": 0.016},
    {"Year": 2003, "Stocks": 0.287, "RE": 0.100, "Inflation": 0.023},
    {"Year": 2004, "Stocks": 0.109, "RE": 0.130, "Inflation": 0.027},
    {"Year": 2005, "Stocks": 0.049, "RE": 0.140, "Inflation": 0.034},
    {"Year": 2006, "Stocks": 0.158, "RE": 0.070, "Inflation": 0.032},
    {"Year": 2007, "Stocks": 0.055, "RE": -0.030, "Inflation": 0.028},
    {"Year": 2008, "Stocks": -0.385, "RE": -0.120, "Inflation": 0.038},
    {"Year": 2009, "Stocks": 0.265, "RE": -0.040, "Inflation": -0.004},
    {"Year": 2010, "Stocks": 0.151, "RE": -0.020, "Inflation": 0.016},
    {"Year": 2011, "Stocks": 0.021, "RE": -0.040, "Inflation": 0.032},
    {"Year": 2012, "Stocks": 0.160, "RE": 0.060, "Inflation": 0.021},
    {"Year": 2013, "Stocks": 0.324, "RE": 0.110, "Inflation": 0.015},
    {"Year": 2014, "Stocks": 0.137, "RE": 0.050, "Inflation": 0.016},
    {"Year": 2015, "Stocks": 0.014, "RE": 0.050, "Inflation": 0.001},
    {"Year": 2016, "Stocks": 0.120, "RE": 0.050, "Inflation": 0.013},
    {"Year": 2017, "Stocks": 0.218, "RE": 0.060, "Inflation": 0.021},
    {"Year": 2018, "Stocks": -0.044, "RE": 0.050, "Inflation": 0.024},
    {"Year": 2019, "Stocks": 0.315, "RE": 0.040, "Inflation": 0.018},
    {"Year": 2020, "Stocks": 0.184, "RE": 0.100, "Inflation": 0.012},
    {"Year": 2021, "Stocks": 0.287, "RE": 0.190, "Inflation": 0.047},
    {"Year": 2022, "Stocks": -0.181, "RE": 0.060, "Inflation": 0.080},
    {"Year": 2023, "Stocks": 0.242, "RE": 0.050, "Inflation": 0.041}
]
df_hist = pd.DataFrame(hist_data)

# --- 1. UTILS ---
def get_v(key, default):
    return st.session_state[key] if key in st.session_state else default

# --- 2. SIDEBAR ---
sb = st.sidebar
sb.title("⚙️ Strategic Planning")

# Persistence Hub
with sb.expander("💾 SAVE & LOAD", expanded=False):
    uploaded = st.file_uploader("Import JSON", type="json")
    if uploaded:
        data = json.load(uploaded)
        for k, v in data.items(): st.session_state[k] = v
    state = json.dumps({k: v for k, v in st.session_state.items() if k != "init"}, indent=4)
    st.download_button("Export JSON", state, file_name="planner.json")

# Simulation Settings
sb.markdown("### 🎲 ENGINE")
use_monte = sb.toggle("Historical Stress Test", value=True)
run_btn = sb.button("🚀 Run Analysis", type="primary", use_container_width=True)

# Assets
with sb.expander("💰 Liquid Assets", expanded=True):
    v_c = st.number_input("Cash", value=get_v("v_c", 200000.0), key="v_c")
    v_d = st.number_input("401k", value=get_v("v_d", 1200000.0), key="v_d")
    v_r = st.number_input("Roth", value=get_v("v_r", 500000.0), key="v_r")
    input_roi = st.slider("Market ROI %", 0.0, 12.0, get_v("roi_raw", 7.0), key="roi_raw")
    active_roi = input_roi / 100

# Profile
with sb.expander("👩‍💼 Profile & Timeline", expanded=False):
    ca = st.number_input("Current Age", value=get_v("ca", 42), key="ca")
    ea = st.number_input("End Age", value=get_v("ea", 95), key="ea")
    hp = st.number_input("Husband Salary", value=get_v("hp", 145000.0), key="hp")
    hr = st.number_input("Husband Retire Age", value=get_v("hr", 58), key="hr")
    yp = st.number_input("Your Salary", value=get_v("yp", 110000.0), key="yp")
    yr = st.number_input("Your Retire Age", value=get_v("yr", 55), key="yr")
    ew = st.number_input("Spend (Work)", value=get_v("ew", 150000.0), key="ew")
    er = st.number_input("Spend (Retire)", value=get_v("er", 120000.0), key="er")

# Kids
with sb.expander("🎓 Education", expanded=False):
    nk = st.number_input("Number of Kids", value=get_v("nk", 2), min_value=0, key="nk")
    kids = []
    for i in range(int(nk)):
        kc = st.number_input(f"Cost K{i+1}", value=get_v(f"kc{i}", 50000.0), key=f"kc{i}")
        ks = st.number_input(f"Start Age K{i+1}", value=get_v(f"ks{i}", 52), key=f"ks{i}")
        kids.append({"c": kc, "s": ks})

# Real Estate
sb.markdown("### 🏠 PROPERTIES")
np_count = sb.number_input("Count", value=get_v("np", 1), min_value=0, key="np")
plist = []
for i in range(int(np_count)):
    with sb.expander(f"Property {i+1}"):
        v = st.number_input(f"Val P{i+1}", value=get_v(f"v{i}", 1700000.0), key=f"v{i}")
        l = st.number_input(f"Loan P{i+1}", value=get_v(f"l{i}", 0.0), key=f"l{i}")
        n = st.number_input(f"Rent P{i+1}", value=get_v(f"n{i}", 4000.0), key=f"n{i}")
        y = st.number_input(f"Year P{i+1}", value=get_v(f"y{i}", 2020), key=f"y{i}")
        t = st.number_input(f"Term P{i+1}", value=get_v(f"t{i}", 30), key=f"t{i}")
        r = st.number_input(f"Rate % P{i+1}", value=get_v(f"r{i}", 4.5), key=f"r{i}") / 100
        a = st.number_input(f"Appr % P{i+1}", value=get_v(f"a{i}", 3.0), key=f"a{i}") / 100
        p_mtg = 0
        if l > 0:
            mi, mt = r/12, t*12
            p_mtg = l * (mi * (1+mi)**mt) / ((1+mi)**mt - 1)
        plist.append({"v":v,"l":l,"y":y,"t":t,"r":r,"a":a,"p":p_mtg*12,"n":n*12})

# --- 3. MATH ENGINE ---
@st.cache_data
def calculate(v_c, v_d, v_r, active_roi, ca, ea, hp, hr, yp, yr, ew, er, kids_json, plist_json, is_rand=False):
    kids = json.loads(kids_json); plist = json.loads(plist_json)
    iters = 500 if is_rand else 1
    all_nw = []
    
    for _ in range(iters):
        cc, cd, cr = v_c, v_d, v_r
        path = []
        for age in range(int(ca), int(ea) + 1):
            yr_idx = 2026 + (age - int(ca))
            env = df_hist.sample(1).iloc[0] if is_rand else {"Stocks": active_roi, "RE": 0.03, "Inflation": 0.02}
            
            cd *= (1 + env["Stocks"]); cr *= (1 + env["Stocks"])
            cc *= (1.02)
            
            inc = (hp if age < hr else 0) + (yp if age < yr else 0) + (85000 if age >= 67 else 0)
            exp = -(ew if (age < yr or age < hr) else er)
            edu = sum(-k["c"] for k in kids if k["s"] <= age < k["s"]+4)
            
            re_eq, re_flow = 0, 0
            for o in plist:
                h = yr_idx - o["y"]
                val = o["v"] * ((1 + env["RE"]) ** h)
                deb = 0
                if h < o["t"]:
                    m, mt, dn = o["r"]/12, o["t"]*12, h*12
                    deb = o["l"] * ((1+m)**mt - (1+m)**dn) / ((1+m)**mt - 1)
                    re_flow -= o["p"]
                re_eq += (val - deb)
                re_flow += o["n"] * ((1 + env["Inflation"]) ** h)
            
            cc += (inc + exp + edu + re_flow)
            path.append(max(0, cc) + cd + cr + re_eq)
        all_nw.append(path)
    return np.array(all_nw)

# Execute
kids_s, plist_s = json.dumps(kids), json.dumps(plist)
if run_btn or "res" not in st.session_state:
    st.session_state.res = calculate(v_c, v_d, v_r, active_roi, ca, ea, hp, hr, yp, yr, ew, er, kids_s, plist_s, use_monte)

# --- 4. DASHBOARD ---
res = st.session_state.res
p10, p50, p90 = np.percentile(res, 10, axis=0), np.percentile(res, 50, axis=0), np.percentile(res, 90, axis=0)
ages = np.arange(int(ca), int(ea) + 1)

st.title("🛡️ Legacy Master v13.6")
c1, c2, c3 = st.columns(3)
c1.metric("Median Estate", f"${p50[-1]:,.0f}")
c2.metric("Success Rate", f"{(res[:,-1] > 0).mean()*100:.1f}%")
c3.metric("ROI Applied", f"{input_roi}%")

fig = go.Figure()
if use_monte:
    fig.add_trace(go.Scatter(x=ages, y=p90, line=dict(width=0), name="High"))
    fig.add_trace(go.Scatter(x=ages, y=p10, line=dict(width=0), fill='tonexty', name="Confidence Zone"))
fig.add_trace(go.Scatter(x=ages, y=p50, line=dict(color='#10b981', width=4), name="Median Path"))
fig.update_layout(template="plotly_dark", title="Wealth Projection")
st.plotly_chart(fig, use_container_width=True)
