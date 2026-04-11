import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
from io import BytesIO

st.set_page_config(layout="wide", page_title="Legacy Master 12.2")

# --- 1. PERSISTENCE & PORTABILITY ---
if "init" not in st.session_state:
    st.session_state.init = True

uploaded_config = st.sidebar.file_uploader("📂 Import Saved Work (.json)", type="json")
if uploaded_config:
    config_data = json.load(uploaded_config)
    for k, v in config_data.items():
        st.session_state[k] = v

def get_v(key, default):
    return st.session_state[key] if key in st.session_state else default

# --- 2. SIDEBAR CONFIGURATION ---
sb = st.sidebar
sb.title("⚙️ Strategic Planning")

# PROPERTY MODULE (Now with individual foldable expanders)
sb.markdown("### 🏠 REAL ESTATE PORTFOLIO")
np = sb.number_input("Total Property Count", value=get_v("np", 1), min_value=0, key="np")
plist = []

for i in range(int(np)):
    # Each property gets its own fold!
    with sb.expander(f"📍 Property {i+1} Details", expanded=(i==0)):
        v = st.number_input(f"Value P{i+1}", value=get_v(f"v{i}", 1700000.0), key=f"v{i}")
        l = st.number_input(f"Loan P{i+1}", value=get_v(f"l{i}", 0.0), key=f"l{i}")
        n = st.number_input(f"Rent P{i+1}", value=get_v(f"n{i}", 4000.0), key=f"n{i}")
        
        col1, col2 = st.columns(2)
        y = col1.number_input(f"Year P{i+1}", value=get_v(f"y{i}", 2020), key=f"y{i}")
        t = col2.number_input(f"Term P{i+1}", value=get_v(f"t{i}", 30), key=f"t{i}")
        
        col3, col4 = st.columns(2)
        r = col3.number_input(f"Rate% P{i+1}", value=get_v(f"r{i}", 4.5), key=f"r{i}") / 100
        a = col4.number_input(f"Appr% P{i+1}", value=get_v(f"a{i}", 3.0), key=f"a{i}") / 100
        
        st.markdown("**Liquidation Event**")
        do_sell = st.checkbox(f"Sell P{i+1}?", value=get_v(f"sell{i}", False), key=f"sell{i}")
        s_age = st.number_input(f"Sell Age P{i+1}", value=get_v(f"sa{i}", 65), key=f"sa{i}") if do_sell else 999
        
        p = 0
        if l > 0 and r > 0:
            mi, mt = r/12, t*12
            pw = (1 + mi)**mt
            p = l * (mi * pw) / (pw - 1)
        plist.append({"v":v,"l":l,"y":y,"t":t,"r":r,"a":a,"p":p*12,"n":n*12,"sell":do_sell,"age":s_age})

with sb.expander("🏦 LIQUID ASSETS & RETIREMENT", expanded=False):
    v_c = sb.number_input("Current Cash/Savings", value=get_v("v_c", 200000.0), key="v_c")
    v_d = sb.number_input("401k (Tax-Deferred)", value=get_v("v_d", 1200000.0), key="v_d")
    v_r = sb.number_input("Roth/HSA (Tax-Free)", value=get_v("v_r", 500000.0), key="v_r")
    roi = sb.number_input("Market ROI %", value=get_v("roi", 6.0), key="roi") / 100

with sb.expander("🎓 COLLEGE TUITION", expanded=False):
    nk = sb.number_input("Kids", value=get_v("nk", 2), key="nk")
    tui = sb.number_input("Tuition/Yr", value=get_v("tui", 50000.0), key="tui")
    k_ages = [sb.number_input(f"Child {i+1} College Start (Your Age)", value=get_v(f"k{i}", 52+(i*5)), key=f"k{i}") for i in range(int(nk))]

with sb.expander("💵 INCOME, EXPENSES & TIMELINE", expanded=False):
    ca = sb.number_input("Your Current Age", value=get_v("ca", 42), key="ca")
    ea = sb.number_input("Simulation End Age", value=get_v("ea", 95), key="ea")
    st.markdown("---")
    hp = sb.number_input("Husband Salary", value=get_v("hp", 145000.0), key="hp")
    hr = sb.number_input("Husband Retire Age (Your Age)", value=get_v("hr", 58), key="hr")
    st.markdown("---")
    yp = sb.number_input("Your Salary", value=get_v("yp", 110000.0), key="yp")
    yr = sb.number_input("Your Retire Age", value=get_v("yr", 55), key="yr")
    st.markdown("---")
    ew = sb.number_input("Annual Spend (Working)", value=get_v("ew", 150000.0), key="ew")
    er = sb.number_input("Annual Spend (Retired)", value=get_v("er", 120000.0), key="er")

# --- 3. MATH ENGINE ---
res = []
cc, cd, cr = v_c, v_d, v_r
fail_yr = None

for age in range(int(ca), int(ea) + 1):
    sim_yr = 2026 + (age - int(ca))
    cc *= 1.02; cd *= (1 + roi); cr *= (1 + roi)
    
    inc_h, inc_y = (hp if age < hr else 0), (yp if age < yr else 0)
    inc_ss = 85000 if age >= 67 else 0
    exp_l = -(ew if (age < yr or age < hr) else er)
    edu = sum(-tui for s in k_ages if s <= age < s + 4)
    
    re_eq, re_pmt, re_noi, re_sale = 0, 0, 0, 0
    for i, o in enumerate(plist):
        h = sim_yr - o["y"]
        if h < 0: continue
        val = o["v"] * ((1 + o["a"]) ** h)
        is_sold = o["sell"] and (age >= o["age"])
        
        deb = 0
        if h < o["t"]:
            m, mt, dn = o["r"]/12, o["t"]*12, h*12
            deb = o["l"] * ((1+m)**mt - (1+m)**dn) / ((1+m)**mt - 1)
            
        if is_sold:
            if age == o["age"]: re_sale += (val - deb) * 0.90 # 10% sales cost
            continue
            
        re_eq += (val - deb)
        re_noi += o["n"] * ((1 + o["a"]) ** h)
        if h < o["t"]: re_pmt -= o["p"]

    # Calculate net flow for the year
    total_in = inc_h + inc_y + inc_ss + re_noi + re_sale
    total_out = exp_l + re_pmt + edu
    net_flow = total_in + total_out
    
    cc += net_flow
    if cc < 0 and fail_yr is None: fail_yr = sim_yr
    
    # Unified Ledger Row
    res.append({
        "Age": age, "Year": sim_yr, 
        "Total Net Worth": max(0, cc) + cd + cr + re_eq,
        "Cash Component": max(0, cc), "401k": cd, "Roth": cr, "RE Equity": re_eq,
        "Husband Salary": inc_h, "Your Salary": inc_y, "Rent In": re_noi, "SocSec": inc_ss, "Sales In": re_sale,
        "Lifestyle Out": exp_l, "Tuition Out": edu, "Mortgage Out": re_pmt,
        "Net Flow": net_flow
    })

# --- 4. OUTPUT ---
st.title("🛡️ Legacy Master v12.2")
df = pd.DataFrame(res)

with sb.expander("💾 SAVE & EXPORT (JSON & Excel)", expanded=True):
    state_json = json.dumps({k: v for k, v in st.session_state.items() if k != "init"}, indent=4)
    st.download_button("📥 Save Model Inputs (.json)", state_json, file_name="planner_config.json")
    try:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='MasterLedger')
        st.download_button("📊 Export Audit to Excel", output.getvalue(), file_name="retirement_model.xlsx")
    except Exception:
        st.warning("Excel Engine not found. (Run: pip install xlsxwriter)")

# Top Metrics
c1, c2, c3 = st.columns(3)
c1.metric("Current NW", f"${df.iloc[0]['Total Net Worth']:,.0f}")
c2.metric("Final Estate", f"${df.iloc[-1]['Total Net Worth']:,.0f}")
c3.metric("Liquidity Status", "SAFE" if not fail_yr else f"Shortage {fail_yr}")

# Chart 1: Wealth Stack
fig1 = go.Figure()
for c, clr in [("RE Equity","#f59e0b"),("401k","#8b5cf6"),("Roth","#10b981"),("Cash Component","#3b82f6")]:
    fig1.add_trace(go.Bar(x=df["Age"], y=df[c], name=c, marker_color=clr))
fig1.update_layout(
    barmode='stack', template="plotly_dark", title="Total Wealth Distribution", 
    hovermode="x unified", # Turns on the detailed hover breakdown
    margin=dict(l=0, r=0, t=40, b=0)
)
st.plotly_chart(fig1, use_container_width=True)

# Chart 2: Cash Flow Audit
fig2 = go.Figure()
for c, clr in [("Husband Salary","#1e3a8a"),("Your Salary","#3b82f6"),("Rent In","#1d4ed8"),("SocSec","#60a5fa"),("Sales In","#10b981")]:
    fig2.add_trace(go.Bar(x=df["Age"], y=df[c], name=c, marker_color=clr))
for c, clr in [("Lifestyle Out","#991b1b"),("Mortgage Out","#dc2626"),("Tuition Out","#ef4444")]:
    fig2.add_trace(go.Bar(x=df["Age"], y=df[c], name=c, marker_color=clr))
fig2.update_layout(
    barmode='relative', template="plotly_dark", title="Cash Flow Peaks (Audit)",
    hovermode="x unified", # Turns on the detailed hover breakdown
    margin=dict(l=0, r=0, t=40, b=0)
)
st.plotly_chart(fig2, use_container_width=True)

# Master Ledger with Fixed Formatting
with st.expander("🔎 View Master Audit Ledger"):
    # Apply format ONLY to financial columns, leaving Age and Year as normal integers
    format_dict = {col: "${:,.0f}" for col in df.columns if col not in ["Age", "Year"]}
    st.dataframe(df.style.format(format_dict), use_container_width=True)
