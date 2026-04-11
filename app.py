import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
from io import BytesIO

st.set_page_config(layout="wide", page_title="Legacy Master 12.1")

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

# --- 2. SIDEBAR ---
sb = st.sidebar
sb.title("⚙️ Strategic Planning")

with sb.expander("🏠 REAL ESTATE PORTFOLIO", expanded=True):
    np = sb.number_input("Property Count", value=get_v("np", 1), min_value=0, key="np")
    plist = []
    for i in range(int(np)):
        st.markdown(f"**Property {i+1}**")
        v = st.number_input(f"Value P{i+1}", value=get_v(f"v{i}", 1700000.0), key=f"v{i}")
        l = st.number_input(f"Loan P{i+1}", value=get_v(f"l{i}", 0.0), key=f"l{i}")
        n = st.number_input(f"Rent P{i+1}", value=get_v(f"n{i}", 4000.0), key=f"n{i}")
        col1, col2 = st.columns(2)
        y = col1.number_input(f"Year P{i+1}", value=get_v(f"y{i}", 2020), key=f"y{i}")
        t = col2.number_input(f"Term P{i+1}", value=get_v(f"t{i}", 30), key=f"t{i}")
        col3, col4 = st.columns(2)
        r = col3.number_input(f"Rate% P{i+1}", value=get_v(f"r{i}", 4.5), key=f"r{i}") / 100
        a = col4.number_input(f"Appr% P{i+1}", value=get_v(f"a{i}", 3.0), key=f"a{i}") / 100
        do_sell = st.checkbox(f"Sell P{i+1}?", value=get_v(f"sell{i}", False), key=f"sell{i}")
        s_age = st.number_input(f"Sell Age P{i+1}", value=get_v(f"sa{i}", 65), key=f"sa{i}") if do_sell else 999
        
        p = 0
        if l > 0 and r > 0:
            mi, mt = r/12, t*12
            pw = (1 + mi)**mt
            p = l * (mi * pw) / (pw - 1)
        plist.append({"v":v,"l":l,"y":y,"t":t,"r":r,"a":a,"p":p*12,"n":n*12,"sell":do_sell,"age":s_age})

with sb.expander("🏦 RETIREMENT", expanded=False):
    v_d = sb.number_input("401k", value=get_v("v_d", 1200000.0), key="v_d")
    v_r = sb.number_input("Roth", value=get_v("v_r", 500000.0), key="v_r")
    roi = sb.number_input("ROI %", value=get_v("roi", 6.0), key="roi") / 100

with sb.expander("🎓 TUITION", expanded=False):
    nk = sb.number_input("Kids", value=get_v("nk", 2), key="nk")
    tui = sb.number_input("Tuition/Yr", value=get_v("tui", 50000.0), key="tui")
    k_ages = [sb.number_input(f"K{i+1} Start", value=get_v(f"k{i}", 52+(i*5)), key=f"k{i}") for i in range(int(nk))]

with sb.expander("💵 TIMELINE", expanded=True):
    v_c = sb.number_input("Current Savings", value=get_v("v_c", 200000.0), key="v_c")
    ca = sb.number_input("Your Age", value=get_v("ca", 42), key="ca")
    hp, yp = sb.number_input("H-Salary", value=get_v("hp", 145000.0), key="hp"), sb.number_input("Y-Salary", value=get_v("yp", 110000.0), key="yp")
    yr, hr = sb.number_input("Y-Retire", value=get_v("yr", 55), key="yr"), sb.number_input("H-Retire", value=get_v("hr", 58), key="hr")
    ea = sb.number_input("End Age", value=get_v("ea", 95), key="ea")
    ew, er = sb.number_input("Exp-Work", value=get_v("ew", 150000.0), key="ew"), sb.number_input("Exp-Ret", value=get_v("er", 120000.0), key="er")

# --- 3. MATH ENGINE ---
res, res_cf = [], []
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
            if age == o["age"]: re_sale += (val - deb) * 0.90
            continue
        re_eq += (val - deb); re_noi += o["n"] * ((1 + o["a"]) ** h)
        if h < o["t"]: re_pmt -= o["p"]

    cc += (inc_h + inc_y + inc_ss + re_noi + exp_l + re_pmt + edu + re_sale)
    if cc < 0 and fail_yr is None: fail_yr = sim_yr
    res.append({"Age": age, "Year": sim_yr, "Cash": max(0, cc), "401k": cd, "Roth": cr, "RE": re_eq, "NW": max(0, cc) + cd + cr + re_eq})
    res_cf.append({"Age": age, "Husband": inc_h, "You": inc_y, "Rent": re_noi, "SS": inc_ss, "Sales": re_sale, "Life": exp_l, "Tui": edu, "Mort": re_pmt})

# --- 4. OUTPUT ---
st.title("🛡️ Legacy Master v12.1")
df, df_cf = pd.DataFrame(res), pd.DataFrame(res_cf)

with sb.expander("💾 SAVE & EXPORT", expanded=True):
    state_json = json.dumps({k: v for k, v in st.session_state.items() if k != "init"}, indent=4)
    st.download_button("📥 Save Snapshot (.json)", state_json, file_name="planner_config.json")
    
    try:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='NetWorth')
            df_cf.to_excel(writer, index=False, sheet_name='CashFlowAudit')
        st.download_button("📊 Export to Excel", output.getvalue(), file_name="retirement_model.xlsx")
    except Exception:
        st.warning("Excel Engine not found. Please install xlsxwriter.")

c1, c2, c3 = st.columns(3)
c1.metric("Current NW", f"${df.iloc[0]['NW']:,.0f}")
c2.metric("Final Estate", f"${df.iloc[-1]['NW']:,.0f}")
c3.metric("Status", "SAFE" if not fail_yr else f"Shortage {fail_yr}")

st.plotly_chart(go.Figure(data=[go.Bar(x=df["Age"], y=df[c], name=c, marker_color=clr) for c, clr in [("RE","#f59e0b"),("401k","#8b5cf6"),("Roth","#10b981"),("Cash","#3b82f6")]], layout=dict(barmode='stack', template="plotly_dark", title="Total Wealth Distribution")), use_container_width=True)

fig2 = go.Figure()
for c, clr in [("Husband","#1e3a8a"),("You","#3b82f6"),("Rent","#1d4ed8"),("SS","#60a5fa"),("Sales","#10b981")]:
    fig2.add_trace(go.Bar(x=df_cf["Age"], y=df_cf[c], name=c, marker_color=clr))
for c, clr in [("Life","#991b1b"),("Mort","#dc2626"),("Tui","#ef4444")]:
    fig2.add_trace(go.Bar(x=df_cf["Age"], y=df_cf[c], name=c, marker_color=clr))
st.plotly_chart(fig2.update_layout(barmode='relative', template="plotly_dark", title="Cash Flow Peaks (Audit)"), use_container_width=True)

with st.expander("🔎 Ledger"): st.dataframe(df.style.format("${:,.0f}"))
