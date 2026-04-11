import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import json
from io import BytesIO

st.set_page_config(layout="wide", page_title="Legacy Master 13.2")

# --- 1. PERSISTENCE ---
if "init" not in st.session_state:
    st.session_state.init = True

def get_v(key, default):
    return st.session_state[key] if key in st.session_state else default

# --- 2. SIDEBAR ---
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

sb.markdown("### 🎲 SIMULATION SETTINGS")
use_monte = sb.toggle("Enable Monte Carlo (1,000 runs)", value=True)
mkt_vol = sb.slider("Market Volatility (Std Dev %)", 5, 25, 15) / 100 if use_monte else 0
re_vol = sb.slider("RE Volatility (Std Dev %)", 1, 10, 3) / 100 if use_monte else 0

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

sb.markdown("### 🎓 EDUCATION")
nk = sb.number_input("Number of Kids", value=get_v("nk", 2), min_value=0, key="nk")
kids = []
for i in range(int(nk)):
    with sb.expander(f"🧒 Child {i+1}", expanded=False):
        cost = st.number_input(f"Annual Cost C{i+1}", value=get_v(f"tc{i}", 50000.0), key=f"tc{i}")
        start = st.number_input(f"Start Age C{i+1}", value=get_v(f"ts{i}", 52+(i*5)), key=f"ts{i}")
        kids.append({"cost": cost, "start": start})

# --- 3. DUAL MATH ENGINE ---
def run_simulation(is_random=False):
    cc, cd, cr = v_c, v_d, v_r
    path_nw = []
    path_details = []
    
    for age in range(int(ca), int(ea) + 1):
        sim_yr = 2026 + (age - int(ca))
        
        yr_roi = np.random.normal(roi, mkt_vol) if is_random else roi
        yr_re_appr = np.random.normal(0, re_vol) if is_random else 0
        
        cc *= 1.02 # Inflation
        cd *= (1 + yr_roi); cr *= (1 + yr_roi)
        
        inc_h = hp if age < hr else 0
        inc_y = yp if age < yr else 0
        inc_ss = 85000 if age >= 67 else 0
        exp_l = -(ew if (age < yr or age < hr) else er)
        edu = sum(-k["cost"] for k in kids if k["start"] <= age < k["start"] + 4)
        
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

        net_flow = inc_h + inc_y + inc_ss + re_noi + re_sale + exp_l + re_pmt + edu
        cc += net_flow
        current_nw = max(0, cc) + cd + cr + re_eq
        
        path_nw.append(current_nw)
        if not is_random: # Only save deep details for the baseline run
            path_details.append({
                "Age": age, "Year": sim_yr, "Total Net Worth": current_nw,
                "Cash Component": max(0, cc), "401k": cd, "Roth": cr, "RE Equity": re_eq,
                "Husband Salary": inc_h, "Your Salary": inc_y, "Rent In": re_noi, "SocSec": inc_ss, "Sales In": re_sale,
                "Lifestyle Out": exp_l, "Tuition Out": edu, "Mortgage Out": re_pmt, "Net Flow": net_flow
            })
            
    return path_nw, path_details

# 1. Run Baseline (Deterministic) for Ledger & Bar Charts
_, baseline_details = run_simulation(is_random=False)
df_base = pd.DataFrame(baseline_details)

# 2. Run Monte Carlo for Percentiles
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

# --- 4. OUTPUT & VISUALIZATION ---
st.title("🛡️ Legacy Master v13.2")

c1, c2, c3 = st.columns(3)
c1.metric("Median Final Estate", f"${p50[-1]:,.0f}")
c2.metric("Success Probability", f"{success_rate:.1f}%")
c3.metric("Status", "STABLE" if success_rate > 85 else "RISKY")

ages = np.arange(int(ca), int(ea) + 1)

# CHART 1: Monte Carlo Trajectory
st.markdown("### Trajectory & Probabilities")
fig1 = go.Figure()
if use_monte:
    fig1.add_trace(go.Scatter(x=ages, y=p90, line=dict(width=0), name="90th Pctl"))
    fig1.add_trace(go.Scatter(x=ages, y=p10, line=dict(width=0), fill='tonexty', fillcolor='rgba(59, 130, 246, 0.2)', name="Confidence Zone"))
    fig1.add_trace(go.Scatter(x=ages, y=p50, line=dict(color='#3b82f6', width=3), name="Median Path"))
else:
    fig1.add_trace(go.Scatter(x=ages, y=df_base["Total Net Worth"], line=dict(color='#10b981', width=3), name="Fixed Projection"))
fig1.update_layout(template="plotly_dark", hovermode="x unified", margin=dict(l=0, r=0, t=30, b=0))
st.plotly_chart(fig1, width="stretch")

# CHART 2: Wealth Distribution
st.markdown("### Wealth Distribution (Baseline)")
fig2 = go.Figure()
for c, clr in [("RE Equity","#f59e0b"),("401k","#8b5cf6"),("Roth","#10b981"),("Cash Component","#3b82f6")]:
    fig2.add_trace(go.Bar(x=df_base["Age"], y=df_base[c], name=c, marker_color=clr))
fig2.update_layout(barmode='stack', template="plotly_dark", hovermode="x unified", margin=dict(l=0, r=0, t=30, b=0))
st.plotly_chart(fig2, width="stretch")

# CHART 3: Cash Flow Audit
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
    
