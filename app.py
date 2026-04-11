import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
from io import BytesIO

st.set_page_config(layout="wide", page_title="Legacy Master 12.3")

# --- 1. PERSISTENCE & PORTABILITY ---
if "init" not in st.session_state:
    st.session_state.init = True

def get_v(key, default):
    return st.session_state[key] if key in st.session_state else default

# --- 2. SIDEBAR CONFIGURATION ---
sb = st.sidebar
sb.title("⚙️ Strategic Planning")

# IMPORT/EXPORT AT TOP
with sb.expander("💾 SAVE, LOAD & EXPORT", expanded=True):
    uploaded_config = st.file_uploader("📂 Import Saved Work (.json)", type="json")
    if uploaded_config:
        config_data = json.load(uploaded_config)
        for k, v in config_data.items():
            st.session_state[k] = v
            
    state_json = json.dumps({k: v for k, v in st.session_state.items() if k != "init"}, indent=4)
    st.download_button("📥 Save Inputs (.json)", state_json, file_name="planner_config.json")

# MODULE: REAL ESTATE
sb.markdown("### 🏠 REAL ESTATE PORTFOLIO")
np = sb.number_input("Total Property Count", value=get_v("np", 1), min_value=0, key="np")
plist = []
for i in range(int(np)):
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
        p = 0
        if l > 0 and r > 0:
            mi, mt = r/12, t*12
            pw = (1 + mi)**mt; p = l * (mi * pw) / (pw - 1)
        plist.append({"v":v,"l":l,"y":y,"t":t,"r":r,"a":a,"p":p*12,"n":n*12,"sell":do_sell,"age":s_age})

# MODULE: LIQUID ASSETS
sb.markdown("### 🏦 LIQUID ASSETS")
with sb.expander("💰 Current Balances & ROI", expanded=False):
    v_c = st.number_input("Cash/Savings", value=get_v("v_c", 200000.0), key="v_c")
    v_d = st.number_input("401k (Tax-Deferred)", value=get_v("v_d", 1200000.0), key="v_d")
    v_r = st.number_input("Roth/HSA (Tax-Free)", value=get_v("v_r", 500000.0), key="v_r")
    roi = st.number_input("Market ROI %", value=get_v("roi", 6.0), key="roi") / 100

# MODULE: CAREER & TIMELINE
sb.markdown("### 💼 CAREER & SPENDING")
with sb.expander("👩‍💼 Your Profile", expanded=False):
    ca = st.number_input("Your Current Age", value=get_v("ca", 42), key="ca")
    yp = st.number_input("Your Net Salary", value=get_v("yp", 110000.0), key="yp")
    yr = st.number_input("Your Retire Age", value=get_v("yr", 55), key="yr")

with sb.expander("👨‍💼 Husband Profile", expanded=False):
    hp = st.number_input("Husband Net Salary", value=get_v("hp", 145000.0), key="hp")
    hr = st.number_input("His Retire Age (At Your Age)", value=get_v("hr", 58), key="hr")

with sb.expander("📉 Global Spending", expanded=False):
    ew = st.number_input("Annual Spend (Working)", value=get_v("ew", 150000.0), key="ew")
    er = st.number_input("Annual Spend (Retired)", value=get_v("er", 120000.0), key="er")
    ea = st.number_input("Simulation End Age", value=get_v("ea", 95), key="ea")

# MODULE: COLLEGE
sb.markdown("### 🎓 EDUCATION FUNDING")
nk = sb.number_input("Number of Kids", value=get_v("nk", 2), min_value=0, key="nk")
kids = []
for i in range(int(nk)):
    with sb.expander(f"🧒 Child {i+1}", expanded=False):
        cost = st.number_input(f"Annual Cost C{i+1}", value=get_v(f"tc{i}", 50000.0), key=f"tc{i}")
        start = st.number_input(f"College Start (Your Age) C{i+1}", value=get_v(f"ts{i}", 52+(i*5)), key=f"ts{i}")
        kids.append({"cost": cost, "start": start})

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
    
    # Independent kid tuition logic
    edu = sum(-k["cost"] for k in kids if k["start"] <= age < k["start"] + 4)
    
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
            if age == o["age"]: re_sale += (val - deb) * 0.90
            continue
        re_eq += (val - deb); re_noi += o["n"] * ((1 + o["a"]) ** h)
        if h < o["t"]: re_pmt -= o["p"]

    net_flow = inc_h + inc_y + inc_ss + re_noi + re_sale + exp_l + re_pmt + edu
    cc += net_flow
    if cc < 0 and fail_yr is None: fail_yr = sim_yr
    
    res.append({
        "Age": age, "Year": sim_yr, "Total Net Worth": max(0, cc) + cd + cr + re_eq,
        "Cash Component": max(0, cc), "401k": cd, "Roth": cr, "RE Equity": re_eq,
        "Husband Salary": inc_h, "Your Salary": inc_y, "Rent In": re_noi, "SocSec": inc_ss, "Sales In": re_sale,
        "Lifestyle Out": exp_l, "Tuition Out": edu, "Mortgage Out": re_pmt, "Net Flow": net_flow
    })

# --- 4. OUTPUT ---
st.title("🛡️ Legacy Master v12.4")
df = pd.DataFrame(res)

# Summary Metrics
c1, c2, c3 = st.columns(3)
c1.metric("Current NW", f"${df.iloc[0]['Total Net Worth']:,.0f}")
c2.metric("Final Estate", f"${df.iloc[-1]['Total Net Worth']:,.0f}")
c3.metric("Liquidity Status", "SAFE" if not fail_yr else f"Shortage {fail_yr}")

# Chart 1: Wealth Distribution
fig1 = go.Figure()
for c, clr in [("RE Equity","#f59e0b"),("401k","#8b5cf6"),("Roth","#10b981"),("Cash Component","#3b82f6")]:
    fig1.add_trace(go.Bar(x=df["Age"], y=df[c], name=c, marker_color=clr))
fig1.update_layout(barmode='stack', template="plotly_dark", title="Total Wealth Distribution", hovermode="x unified", margin=dict(l=0, r=0, t=40, b=0))
st.plotly_chart(fig1, use_container_width=True)

# Chart 2: Cash Flow Audit
fig2 = go.Figure()
df_cf = pd.DataFrame(res) # Using the same df for the audit breakdown
for c, clr in [("Husband Salary","#1e3a8a"),("Your Salary","#3b82f6"),("Rent In","#1d4ed8"),("SocSec","#60a5fa"),("Sales In","#10b981")]:
    fig2.add_trace(go.Bar(x=df["Age"], y=df[c], name=c, marker_color=clr))
for c, clr in [("Lifestyle Out","#991b1b"),("Mortgage Out","#dc2626"),("Tuition Out","#ef4444")]:
    fig2.add_trace(go.Bar(x=df["Age"], y=df[c], name=c, marker_color=clr))
fig2.update_layout(barmode='relative', template="plotly_dark", title="Cash Flow Peaks (Audit)", hovermode="x unified", margin=dict(l=0, r=0, t=40, b=0))
st.plotly_chart(fig2, use_container_width=True)

# --- EXPORT & LEDGER SECTION ---
# This creates the columns to fix the NameError
col_export, col_empty = st.columns([2, 8]) 

with col_export:
    try:
        # Try Excel (Openpyxl or Xlsxwriter)
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='MasterLedger')
        st.download_button("📊 Download Excel", output.getvalue(), file_name="retirement_model.xlsx", use_container_width=True)
    except Exception:
        # Fallback to CSV if Excel engine is missing
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📄 Download CSV", csv, "retirement_model.csv", "text/csv", use_container_width=True)
        st.caption("Excel engine not found; providing CSV.")

with st.expander("🔎 View Master Audit Ledger", expanded=False):
    format_dict = {col: "${:,.0f}" for col in df.columns if col not in ["Age", "Year"]}
    st.dataframe(df.style.format(format_dict), use_container_width=True)
