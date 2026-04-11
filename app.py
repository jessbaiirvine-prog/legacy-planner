import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import json
from io import BytesIO

st.set_page_config(layout="wide", page_title="Legacy Master 13.3")

# --- 0. HISTORICAL DATA ENGINE (S&P 500, US Real Estate, US CPI) ---
# A representative 30-year block of actual macroeconomic data
hist_data = [
    {"Year": 1994, "Stocks": 0.013, "RE": 0.020, "Inflation": 0.026},
    {"Year": 1995, "Stocks": 0.376, "RE": 0.015, "Inflation": 0.028},
    {"Year": 1996, "Stocks": 0.230, "RE": 0.020, "Inflation": 0.030},
    {"Year": 1997, "Stocks": 0.334, "RE": 0.030, "Inflation": 0.023},
    {"Year": 1998, "Stocks": 0.286, "RE": 0.050, "Inflation": 0.016},
    {"Year": 1999, "Stocks": 0.210, "RE": 0.060, "Inflation": 0.022},
    {"Year": 2000, "Stocks": -0.091, "RE": 0.080, "Inflation": 0.034}, # Tech bubble bursts
    {"Year": 2001, "Stocks": -0.119, "RE": 0.075, "Inflation": 0.028},
    {"Year": 2002, "Stocks": -0.221, "RE": 0.090, "Inflation": 0.016},
    {"Year": 2003, "Stocks": 0.287, "RE": 0.100, "Inflation": 0.023},
    {"Year": 2004, "Stocks": 0.109, "RE": 0.130, "Inflation": 0.027},
    {"Year": 2005, "Stocks": 0.049, "RE": 0.140, "Inflation": 0.034},
    {"Year": 2006, "Stocks": 0.158, "RE": 0.070, "Inflation": 0.032},
    {"Year": 2007, "Stocks": 0.055, "RE": -0.030, "Inflation": 0.028},
    {"Year": 2008, "Stocks": -0.385, "RE": -0.120, "Inflation": 0.038}, # GFC
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
    {"Year": 2020, "Stocks": 0.184, "RE": 0.100, "Inflation": 0.012}, # Pandemic
    {"Year": 2021, "Stocks": 0.287, "RE": 0.190, "Inflation": 0.047},
    {"Year": 2022, "Stocks": -0.181, "RE": 0.060, "Inflation": 0.080}, # Inflation shock
    {"Year": 2023, "Stocks": 0.242, "RE": 0.050, "Inflation": 0.041}
]
df_hist = pd.DataFrame(hist_data)

# --- 1. PERSISTENCE ---
if "init" not in st.session_state:
    st.session_state.init = True

def get_v(key, default):
    return st.session_state[key] if key in st.session_state else default

# --- 2. SIDEBAR ---
sb = st.sidebar
sb.title("⚙️ Strategic Planning")

with sb.expander("💾 SAVE, LOAD & EXPORT", expanded=True):
    uploaded_config = st.file_uploader("📂 Import Config (.json)", type="json")
    if uploaded_config:
        config_data = json.load(uploaded_config)
        for k, v in config_data.items():
            st.session_state[k] = v
    state_json = json.dumps({k: v for k, v in st.session_state.items() if k != "init"}, indent=4)
    st.download_button("📥 Save Inputs (.json)", state_json, file_name="planner_config.json")

sb.markdown("### 🎲 SIMULATION ENGINE")
use_monte = sb.toggle("Historical Bootstrapping (1,000 Runs)", value=True)
if use_monte:
    st.sidebar.info("Using 1994-2023 macroeconomic data for stress testing.")

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
        a = c4.number_input(f"Base Appr% P{i+1}", value=get_v(f"a{i}", 3.0), key=f"a{i}") / 100
        do_sell = st.checkbox(f"Sell P{i+1}?", value=get_v(f"sell{i}", False), key=f"sell{i}")
        s_age = st.number_input(f"Sell Age P{i+1}", value=get_v(f"sa{i}", 65), key=f"sa{i}") if do_sell else 999
        p_mtg = 0
        if l > 0 and r > 0:
            mi, mt = r/12, t*12
            pw = (1 + mi)**mt; p_mtg = l * (mi * pw) / (pw - 1)
        plist.append({"v":v,"l":l,"y":y,"t":t,"r":r,"a":a,"p":p_mtg*12,"n":n*12,"sell":do_sell,"age":s_age})

sb.markdown("### 🏦 LIQUID ASSETS")
with sb.expander("💰 Cash & ROI", expanded=False):
    v_c = st.number_input("Cash/Savings", value=get_v("v_c", 200000.0), key="v_c")
    v_d = st.number_input("401k", value=get_v("v_d", 1200000.0), key="v_d")
    v_r = st.number_input("Roth/HSA", value=get_v("v_r", 500000.0), key="v_r")
    roi = st.number_input("Base Market ROI %", value=get_v("roi", 6.0), key="roi") / 100

with sb.expander("👩‍💼 Profile & Timeline", expanded=False):
    ca = st.number_input("Current Age", value=get_v("ca", 42), key="ca")
    ea = st.number_input("End Age", value=get_v("ea", 95), key="ea")
    hp = st.number_input("Husband Salary", value=get_v("hp", 145000.0), key="hp")
    hr = st.number_input("Husband Retire Age", value=get_v("hr", 58), key="hr")
    yp = st.number_input("Your Salary", value=get_v("yp", 110000.0), key="yp")
    yr = st.number_input("Your Retire Age", value=get_v("yr", 55), key="yr")
    ew = st.number_input("Spend (Work) Base", value=get_v("ew", 150000.0), key="ew")
    er = st.number_input("Spend (Retire) Base", value=get_v("er", 120000.0), key="er")

sb.markdown("### 🎓 EDUCATION")
nk = sb.number_input("Number of Kids", value=get_v("nk", 2), min_value=0, key="nk")
kids = []
for i in range(int(nk)):
    with sb.expander(f"🧒 Child {i+1}", expanded=False):
        cost = st.number_input(f"Annual Cost C{i+1}", value=get_v(f"tc{i}", 50000.0), key=f"tc{i}")
        start = st.number_input(f"Start Age C{i+1}", value=get_v(f"ts{i}", 52+(i*5)), key=f"ts{i}")
        kids.append({"cost": cost, "start": start})

# --- 3. THE HISTORICAL MATH ENGINE ---
def run_simulation(is_random=False):
    cc, cd, cr = v_c, v_d, v_r
    current_ew, current_er = ew, er # Lifestyles subject to inflation compounding
    
    path_nw = []
    path_details = []
    
    for age in range(int(ca), int(ea) + 1):
        sim_yr = 2026 + (age - int(ca))
        
        if is_random:
            # Pull one historical year to define this simulated year's economy
            env = df_hist.sample(1).iloc[0]
            yr_roi = env["Stocks"]
            yr_re_appr = env["RE"]
            yr_inflation = env["Inflation"]
        else:
            # Clean baseline using sidebar inputs
            yr_roi = roi
            yr_re_appr = 0.03 # Base assumption
            yr_inflation = 0.02 # Base 2% inflation assumption
        
        # Apply Economic Environment
        # 1. Inflation inflates your lifestyle costs
        current_ew *= (1 + yr_inflation)
        current_er *= (1 + yr_inflation)
        
        # 2. Cash yields a fixed 2% (assuming T-bills), but purchasing power drops
        cc *= 1.02 
        
        # 3. Market returns applied to retirement accounts
        cd *= (1 + yr_roi); cr *= (1 + yr_roi)
        
        inc_h = hp if age < hr else 0
        inc_y = yp if age < yr else 0
        inc_ss = 85000 if age >= 67 else 0
        exp_l = -(current_ew if (age < yr or age < hr) else current_er)
        edu = sum(-k["cost"] for k in kids if k["start"] <= age < k["start"] + 4)
        
        re_eq, re_pmt, re_noi, re_sale = 0, 0, 0, 0
        for o in plist:
            h = sim_yr - o["y"]
            if h < 0: continue
            
            # Real Estate Compound Growth using the environment's appreciation
            val = o["v"] * ((1 + yr_re_appr) ** h) 
            is_sold = o["sell"] and (age >= o["age"])
            deb = 0
            if h < o["t"]:
                m, mt, dn = o["r"]/12, o["t"]*12, h*12
                deb = o["l"] * ((1+m)**mt - (1+m)**dn) / ((1+m)**mt - 1)
            if is_sold:
                if age == o["age"]: re_sale += (val - deb) * 0.90
                continue
            
            re_eq += (val - deb)
            # Commercial rent typically scales with inflation (or CPI-tied escalations)
            re_noi += o["n"] * ((1 + yr_inflation) ** h) 
            if h < o["t"]: re_pmt -= o["p"]

        net_flow = inc_h + inc_y + inc_ss + re_noi + re_sale + exp_l + re_pmt + edu
        cc += net_flow
        current_nw = max(0, cc) + cd + cr + re_eq
        
        path_nw.append(current_nw)
        if not is_random:
            path_details.append({
                "Age": age, "Year": sim_yr, "Total Net Worth": current_nw,
                "Cash Component": max(0, cc), "401k": cd, "Roth": cr, "RE Equity": re_eq,
                "Husband Salary": inc_h, "Your Salary": inc_y, "Rent In": re_noi, "SocSec": inc_ss, "Sales In": re_sale,
                "Lifestyle Out": exp_l, "Tuition Out": edu, "Mortgage Out": re_pmt, "Net Flow": net_flow
            })
            
    return path_nw, path_details

# 1. Baseline Mode
_, baseline_details = run_simulation(is_random=False)
df_base = pd.DataFrame(baseline_details)

# 2. Historical Monte Carlo Mode
all_sim_nw = []
iterations = 1000 if use_monte else 1

if use_monte:
    for _ in range(iterations):
        path_nw, _ = run_simulation(is_random=True)
        all_sim_nw.append(path_nw)
    nw_matrix = np.array(all_sim_nw)
else:
    nw_matrix = np.array([df_base["Total Net Worth"].values])

p10 = np.percentile(nw_matrix, 10, axis=0)
p50 = np.percentile(nw_matrix, 50, axis=0)
p90 = np.percentile(nw_matrix, 90, axis=0)
success_rate = (nw_matrix[:, -1] > 0).mean() * 100

# --- 4. VISUALIZATION DASHBOARD ---
st.title("🛡️ Legacy Master v13.3 (Historical)")

c1, c2, c3 = st.columns(3)
c1.metric("Median Final Estate", f"${p50[-1]:,.0f}")
c2.metric("Success Probability", f"{success_rate:.1f}%")
c3.metric("Status", "STABLE" if success_rate > 85 else "RISKY")

ages = np.arange(int(ca), int(ea) + 1)

st.markdown("### Trajectory under Historical Stress (1994-2023)")
fig1 = go.Figure()
if use_monte:
    fig1.add_trace(go.Scatter(x=ages, y=p90, line=dict(width=0), name="90th Pctl"))
    fig1.add_trace(go.Scatter(x=ages, y=p10, line=dict(width=0), fill='tonexty', fillcolor='rgba(59, 130, 246, 0.2)', name="Confidence Zone"))
    fig1.add_trace(go.Scatter(x=ages, y=p50, line=dict(color='#3b82f6', width=3), name="Median Path"))
else:
    fig1.add_trace(go.Scatter(x=ages, y=df_base["Total Net Worth"], line=dict(color='#10b981', width=3), name="Fixed Projection"))
fig1.update_layout(template="plotly_dark", hovermode="x unified", margin=dict(l=0, r=0, t=30, b=0))
st.plotly_chart(fig1, width="stretch")

st.markdown("### Wealth Distribution (Baseline)")
fig2 = go.Figure()
for c, clr in [("RE Equity","#f59e0b"),("401k","#8b5cf6"),("Roth","#10b981"),("Cash Component","#3b82f6")]:
    fig2.add_trace(go.Bar(x=df_base["Age"], y=df_base[c], name=c, marker_color=clr))
fig2.update_layout(barmode='stack', template="plotly_dark", hovermode="x unified", margin=dict(l=0, r=0, t=30, b=0))
st.plotly_chart(fig2, width="stretch")

st.markdown("### Cash Flow Audit (Baseline)")
fig3 = go.Figure()
for c, clr in [("Husband Salary","#1e3a8a"),("Your Salary","#3b82f6"),("Rent In","#1d4ed8"),("SocSec","#60a5fa"),("Sales In","#10b981")]:
    fig3.add_trace(go.Bar(x=df_base["Age"], y=df_base[c], name=c, marker_color=clr))
for c, clr in [("Lifestyle Out","#991b1b"),("Mortgage Out","#dc2626"),("Tuition Out","#ef4444")]:
    fig3.add_trace(go.Bar(x=df_base["Age"], y=df_base[c], name=c, marker_color=clr))
fig3.update_layout(barmode='relative', template="plotly_dark", hovermode="x unified", margin=dict(l=0, r=0, t=30, b=0))
st.plotly_chart(fig3, width="stretch")

# --- 5. EXPORT HUB ---
col_exp, _ = st.columns([2, 8])
with col_exp:
    try:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_base.to_excel(writer, index=False, sheet_name='MasterLedger')
        st.download_button("📊 Download Excel", output.getvalue(), file_name="retirement_model.xlsx", width="stretch")
    except Exception:
        csv = df_base.to_csv(index=False).encode('utf-8')
        st.download_button("📄 Download CSV", csv, "model.csv", "text/csv", width="stretch")

with st.expander("🔎 View Baseline Master Ledger", expanded=False):
    format_dict = {col: "${:,.0f}" for col in df_base.columns if col not in ["Age", "Year"]}
    st.dataframe(df_base.style.format(format_dict), width="stretch")
