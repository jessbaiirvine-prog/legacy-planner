import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import json
from io import BytesIO

st.set_page_config(layout="wide", page_title="Legacy Master 13.1")

# --- 1. PERSISTENCE & UTILS ---
if "init" not in st.session_state:
    st.session_state.init = True

def get_v(key, default):
    return st.session_state[key] if key in st.session_state else default

# --- 2. SIDEBAR CONFIGURATION ---
sb = st.sidebar
sb.title("⚙️ Strategic Planning")

with sb.expander("💾 SAVE, LOAD & EXPORT", expanded=True):
    uploaded_config = st.file_uploader("📂 Import Saved Work (.json)", type="json")
    if uploaded_config:
        config_data = json.load(uploaded_config)
        for k, v in config_data.items():
            st.session_state[k] = v
    state_json = json.dumps({k: v for k, v in st.session_state.items() if k != "init"}, indent=4)
    st.download_button("📥 Save Inputs (.json)", state_json, file_name="planner_config.json")

# MODULE: MONTE CARLO
sb.markdown("### 🎲 SIMULATION SETTINGS")
use_monte = sb.toggle("Enable Monte Carlo (1,000 runs)", value=False)
mkt_vol = sb.slider("Market Volatility (Std Dev %)", 5, 25, 15) / 100 if use_monte else 0
re_vol = sb.slider("RE Volatility (Std Dev %)", 1, 10, 3) / 100 if use_monte else 0

# MODULE: REAL ESTATE
sb.markdown("### 🏠 REAL ESTATE")
np_count = sb.number_input("Property Count", value=get_v("np", 1), min_value=0, key="np")
plist = []
for i in range(int(np_count)):
    with sb.expander(f"📍 Property {i+1}", expanded=(i==0)):
        v = st.number_input(f"Value P{i+1}", value=get_v(f"v{i}", 1700000.0), key=f"v{i}")
        l = st.number_input(f"Loan P{i+1}", value=get_v(f"l{i}", 0.0), key=f"l{i}")
        n = st.number_input(f"Rent P{i+1}", value=get_v(f"n{i}", 4000.0), key=f"n{i}")
        c1, c2 = st.columns(2)
        y = c1.number_input(f"Year P{i+1}", value=get_v(f"y{i}", 2020), key=f"y{i}")
        t = c2.number_input(f"Term P{i+1}", value=get_v(f"t{i}", 30), key=f"t{i}")
        c3, c4 = st.columns(2)
        r = c3.number_input(f"Rate% P{i+1}", value=get_v(f"r{i}", 4.5), key=f"r{i}") / 100
        a = c4.number_input(f"Appr% P{i+1}", value=get_v(f"a{i}", 3.0), key=f"a{i}") / 100
        do_sell = st.checkbox(f"Sell P{i+1}?", value=get_v(f"sell{i}", False), key=f"sell{i}")
        s_age = st.number_input(f"Sell Age P{i+1}", value=get_v(f"sa{i}", 65), key=f"sa{i}") if do_sell else 999
        p_mtg = 0
        if l > 0 and r > 0:
            mi, mt = r/12, t*12
            pw = (1 + mi)**mt
            p_mtg = l * (mi * pw) / (pw - 1)
        plist.append({"v":v,"l":l,"y":y,"t":t,"r":r,"a":a,"p":p_mtg*12,"n":n*12,"sell":do_sell,"age":s_age})

# MODULE: LIQUID ASSETS (DEFINED HERE)
sb.markdown("### 🏦 LIQUID ASSETS")
with sb.expander("💰 Cash & ROI", expanded=False):
    v_c = st.number_input("Cash/Savings", value=get_v("v_c", 200000.0), key="v_c")
    v_d = st.number_input("401k", value=get_v("v_d", 1200000.0), key="v_d")
    v_r = st.number_input("Roth/HSA", value=get_v("v_r", 500000.0), key="v_r")
    roi = st.number_input("Market ROI %", value=get_v("roi", 6.0), key="roi") / 100

with sb.expander("👩‍💼 Profile & Timeline", expanded=False):
    ca = st.number_input("Current Age", value=get_v("ca", 42), key="ca")
    ea = st.number_input("End Age", value=get_v("ea", 95), key="ea")
    hp = st.number_input("Husband Salary", value=get_v("hp", 145000.0), key="hp")
    hr = st.number_input("Husband Retire Age", value=get_v("hr", 58), key="hr")
    yp = st.number_input("Your Salary", value=get_v("yp", 110000.0), key="yp")
    yr = st.number_input("Your Retire Age", value=get_v("yr", 55), key="yr")
    ew = st.number_input("Spend (Work)", value=get_v("ew", 150000.0), key="ew")
    er = st.number_input("Spend (Retire)", value=get_v("er", 120000.0), key="er")

# --- 3. MONTE CARLO ENGINE ---
iterations = 1000 if use_monte else 1
all_sim_nw = []
deterministic_res = []

for sim_i in range(iterations):
    cc, cd, cr = v_c, v_d, v_r
    sim_nw_path = []
    
    for age in range(int(ca), int(ea) + 1):
        sim_yr = 2026 + (age - int(ca))
        
        # Volatility
        yr_roi = np.random.normal(roi, mkt_vol) if use_monte else roi
        yr_re_appr = np.random.normal(0, re_vol) if use_monte else 0
        
        cc *= 1.02 # Cash inflation
        cd *= (1 + yr_roi); cr *= (1 + yr_roi)
        
        inc_h = hp if age < hr else 0
        inc_y = yp if age < yr else 0
        inc_ss = 85000 if age >= 67 else 0
        exp_l = -(ew if (age < yr or age < hr) else er)
        
        re_eq, re_pmt, re_noi, re_sale = 0, 0, 0, 0
        for o in plist:
            h = sim_yr - o["y"]
            if h < 0: continue
            val = o["v"] * ((1 + o["a"] + yr_re_appr) ** h)
            is_sold = o["sell"] and (age >= o["age"])
            deb = 0
            if h < o["t"]:
                m, mt, dn = o["r"]/12, o["t"]*12, h*12
                deb = o["l"] * ((1+m)**mt - (1+m)**dn) / ((1+m)**mt - 1)
            if is_sold:
                if age == o["age"]: re_sale += (val - deb) * 0.90
                continue
            re_eq += (val - deb)
            re_noi += o["n"] * ((1 + o["a"] + yr_re_appr) ** h)
            if h < o["t"]: re_pmt -= o["p"]

        net_flow = inc_h + inc_y + inc_ss + re_noi + re_sale + exp_l + re_pmt
        cc += net_flow
        current_nw = max(0, cc) + cd + cr + re_eq
        sim_nw_path.append(current_nw)
        
        if sim_i == 0: # Save first run as the deterministic/ledger baseline
            deterministic_res.append({"Age":age,"Year":sim_yr,"NW":current_nw,"Cash":cc,"401k":cd,"Roth":cr,"RE":re_eq,"Flow":net_flow})

    all_sim_nw.append(sim_nw_path)

# Statistics
nw_matrix = np.array(all_sim_nw)
p10 = np.percentile(nw_matrix, 10, axis=0)
p50 = np.percentile(nw_matrix, 50, axis=0)
p90 = np.percentile(nw_matrix, 90, axis=0)
success_rate = (nw_matrix[:, -1] > 0).mean() * 100

# --- 4. OUTPUT ---
st.title("🛡️ Legacy Master v13.1")
df = pd.DataFrame(deterministic_res)

c1, c2, c3 = st.columns(3)
c1.metric("Median Final Estate", f"${p50[-1]:,.0f}")
c2.metric("Success Probability", f"{success_rate:.1f}%")
c3.metric("Status", "STABLE" if success_rate > 85 else "RISKY")

# Chart
fig = go.Figure()
ages = np.arange(int(ca), int(ea) + 1)
if use_monte:
    fig.add_trace(go.Scatter(x=ages, y=p90, line=dict(width=0), name="90th Pctl"))
    fig.add_trace(go.Scatter(x=ages, y=p10, line=dict(width=0), fill='tonexty', fillcolor='rgba(59, 130, 246, 0.2)', name="Confidence Zone"))
    fig.add_trace(go.Scatter(x=ages, y=p50, line=dict(color='#3b82f6', width=3), name="Median Path"))
else:
    fig.add_trace(go.Scatter(x=ages, y=df["NW"], line=dict(color='#10b981', width=3), name="Fixed Projection"))
fig.update_layout(template="plotly_dark", title="Wealth Probability Trajectory", hovermode="x unified")
st.plotly_chart(fig, width="stretch")

# Export/Ledger
with st.expander("🔎 View Master Ledger"):
    st.dataframe(df.style.format({c: "${:,.0f}" for c in df.columns if c not in ["Age", "Year"]}), width="stretch")
