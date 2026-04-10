import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Legacy Master 9.1")

# --- 1. SIDEBAR MODULES (LHS) ---
st.sidebar.title("⚙️ Strategic Planning")

# -- MODULE 1: RE INVESTMENT --
with st.sidebar.expander("🏠 RE INVESTMENT", expanded=True):
    # Default based on your portfolio: SoCal Home + 3 rentals
    n_p = st.number_input("Property Count", value=4, min_value=0)
    p_list = []
    for i in range(int(n_p)):
        st.markdown(f"**Property {i+1}**")
        # Pre-filling based on your $1.7M SoCal + $480k FL + $700k TX portfolio
        def_v = 1700000.0 if i==0 else 480000.0 if i==1 else 350000.0
        v = st.number_input("Market Value", value=def_v, key=f"re_v{i}")
        l = st.number_input("Loan Balance", value=0.0, key=f"re_l{i}")
        y = st.number_input("Year Purchased", value=2020, key=f"re_y{i}")
        t = st.number_input("Loan Term (Yrs)", value=30, key=f"re_t{i}")
        r = st.number_input("Interest Rate %", value=4.5, key=f"re_r{i}") / 100
        a = st.number_input("Annual Appr %", value=3.0, key=f"re_a{i}") / 100
        n = st.number_input("Monthly Net Rent (NOI)", value=0.0, key=f"re_n{i}")
        
        ann_pmt = 0
        if l > 0 and r > 0:
            mi, mt = r/12, t*12
            pw = (1 + mi)**mt
            mp = l * (mi * pw) / (pw - 1)
            ann_pmt = mp * 12
        p_list.append({"v":v,"l":l,"y":y,"t":t,"r":r,"a":a,"p":ann_pmt,"n":n*12})

# -- MODULE 2: RETIREMENT SAVINGS --
with st.sidebar.expander("🏦 RETIREMENT SAVINGS", expanded=False):
    # Pre-filling based on your $1.7M liquid asset total
    v_401k = st.number_input("401k (Pre-Tax)", value=1200000.0)
    v_roth = st.number_input("Roth Accounts", value=500000.0)
    m_roi = st.number_input("Portfolio Return %", value=6.0) / 100

# -- MODULE 3: CASH ASSETS --
with st.sidebar.expander("💵 CASH ASSETS", expanded=False):
    v_csh = st.number_input("Checking/Savings Account", value=200000.0)
    h_pay = st.number_input("Husband Net Salary", value=145000.0)
    y_pay = st.number_input("Your Net Salary", value=110000.0)

# -- MODULE 4: KIDS TUITION --
with st.sidebar.expander("🎓 KIDS TUITION", expanded=False):
    n_k = st.number_input("Number of Kids", value=2)
    tui = st.number_input("Tuition per Year", value=50000.0)
    k_s = [st.number_input(f"K{i+1} College Start Age", value=52+(i*6)) for i in range(int(n_k))]

# -- MODULE 5: TIMELINE & EXPENSES --
with st.sidebar.expander("📅 TIMELINE & EXPENSES", expanded=False):
    c_a = st.number_input("Current Age", value=42)
    y_r = st.number_input("Your Retire Age", value=55)
    h_r = st.number_input("Husband Retire Age", value=58)
    e_a = st.number_input("Simulation End Age", value=95)
    ex_w = st.number_input("Annual Expense (Working)", value=150000.0)
    ex_r = st.number_input("Annual Expense (Retired)", value=120000.0)

# --- 2. MATH ENGINE ---
data_rows = []
cur_c, cur_d, cur_r = v_csh, v_401k, v_roth
ruin_yr = None

for age in range(int(c_a), int(e_a) + 1):
    yr = 2026 + (age - int(c_a))
    
    # Simple Growth
    cur_c *= 1.02 # Cash inflation adjustment
    cur_d *= (1 + m_roi)
    cur_r *= (1 + m_roi)
    
    # Inflow
    inc = (h_pay if age < h_r else 0) + (y_pay if age < y_r else 0)
    if age >= 67: inc += 85000 # Social Security
    
    # Outflow
    exp = ex_r if (age >= y_r and age >= h_r) else ex_w
    edu = sum(tui for s_age in k_s if s_age <= age < s_age + 4)
    
    re_eq, re_pmt, re_noi = 0, 0, 0
    for p in p_list:
        h = yr - p["y"]
        if h < 0: continue
        val = p["v"] * ((1.0 + p["a"]) ** h)
        noi = p["n"] * ((1.0 + p["a"]) ** h)
        if h >= p["t"]:
            deb = 0
        else:
            mi, mt, dn = p["r"]/12, p["t"]*12, h*12
            pm, pd = (1+mi)**mt, (1+mi)**dn
            deb = p["l"] * (pm - pd) / (pm - 1)
            re_pmt += p["p"]
        re_eq += (val - deb)
        re_noi += noi

    cur_c += (inc + re_noi - exp - edu - re_pmt)
    if cur_c < 0 and ruin_yr is None:
        ruin_yr = yr

    data_rows.append({
        "Age": age, "Year": yr, "Cash": cur_c, 
        "Deferred": cur_d, "Roth": cur_r, 
        "RE": re_eq, "NW": (cur_c + cur_d + cur_r + re_eq)
    })

# --- 3. DISPLAY ---
st.title("✨ Legacy Master v9.1")

if not data_rows:
    st.error("Engine failed to generate data. Please check Age settings.")
else:
    df = pd.DataFrame(data_rows)
    
    if ruin_yr:
        st.warning(f"⚠️ **Cash Depleted:** Simulation shows cashflow deficit in {ruin_yr}.")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Current NW", f"${df.iloc[0]['NW']:,.0f}")
    ret_nw = df[df['Age'] == y_r]['NW'].values[0] if not df[df['Age'] == y_r].empty else 0
    m2.metric("NW @ Retirement", f"${ret_nw:,.0f}")
    m3.metric("Final Estate", f"${df.iloc[-1]['NW']:,.0f}")
    m4.metric("Status", "Solvent" if not ruin_yr else "Deficit")

    # Stacked Bar Chart
    fig = go.Figure()
    for col, clr in [("Cash","#3b82f6"), ("Roth","#10b981"), ("Deferred","#8b5cf6"), ("RE","#f59e0b")]:
        fig.add_trace(go.Bar(x=df["Age"], y=df[col], name=col, marker_color=clr))
    
    fig.update_layout(barmode='stack', template="plotly_dark", height=500, margin=dict(t=20,b=20))
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("📊 ANNUAL LEDGER"):
        st.dataframe(df.style.format("${:,.0f}"))
