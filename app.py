import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Legacy Master 9.2")

# --- 1. SIDEBAR MODULES (LHS) ---
st.sidebar.title("⚙️ Strategic Planning")

# -- MODULE 1: RE INVESTMENT (NOW TOP) --
with st.sidebar.expander("🏠 RE INVESTMENT", expanded=True):
    n_p = st.number_input("Property Count", value=1, min_value=0)
    p_list = []
    for i in range(int(n_p)):
        st.markdown(f"**Property {i+1}**")
        v = st.number_input("Market Value", value=1000000.0, key=f"re_v{i}")
        l = st.number_input("Loan Balance", value=700000.0, key=f"re_l{i}")
        y = st.number_input("Year Purchased", value=2020, key=f"re_y{i}")
        t = st.number_input("Loan Term (Yrs)", value=30, key=f"re_t{i}")
        r = st.number_input("Interest Rate %", value=4.5, key=f"re_r{i}") / 100
        a = st.number_input("Annual Appr %", value=3.0, key=f"re_a{i}") / 100
        n = st.number_input("Monthly Net Rent (NOI)", value=0.0, key=f"re_n{i}")
        
        # Amortization calculation
        ann_pmt = 0
        if l > 0 and r > 0:
            mi, mt = r/12, t*12
            pw = (1 + mi)**mt
            mp = l * (mi * pw) / (pw - 1)
            ann_pmt = mp * 12
        p_list.append({"v":v,"l":l,"y":y,"t":t,"r":r,"a":a,"p":ann_pmt,"n":n*12})

# -- MODULE 2: RETIREMENT SAVINGS --
with st.sidebar.expander("🏦 RETIREMENT SAVINGS", expanded=False):
    v_pre = st.number_input("401k Pre-tax", value=1200000.0)
    v_roth = st.number_input("Roth (401k/IRA)", value=100000.0)
    v_hsa = st.number_input("HSA Balance", value=50000.0)
    m_roi = st.number_input("Portfolio Return %", value=6.0) / 100

# -- MODULE 3: CASH ASSETS --
with st.sidebar.expander("💵 CASH ASSETS", expanded=False):
    v_csh = st.number_input("Checking/Savings", value=200000.0)
    h_pay = st.number_input("Husband Net Salary", value=145000.0)
    y_pay = st.number_input("Your Net Salary", value=110000.0)

# -- MODULE 4: KIDS TUITION --
with st.sidebar.expander("🎓 KIDS TUITION", expanded=False):
    n_k = st.number_input("Number of Kids", value=2, min_value=0)
    tui = st.number_input("Annual Tuition", value=50000.0)
    k_s = []
    for i in range(int(n_k)):
        ks_val = st.number_input(f"K{i+1} College Start Age", value=52+(i*6))
        k_s.append(ks_val)

# -- MODULE 5: ANNUAL EXPENSES (FOLDABLE) --
with st.sidebar.expander("📅 TIMELINE & EXPENSES", expanded=False):
    c_a = st.number_input("Current Age", value=42)
    y_r = st.number_input("Your Retire Age", value=55)
    h_r = st.number_input("Husband Retire Age", value=58)
    e_a = st.number_input("End Simulation Age", value=95)
    ex_w = st.number_input("Annual Exp (Working)", value=150000.0)
    ex_r = st.number_input("Annual Exp (Retired)", value=120000.0)

# --- 2. MATH ENGINE ---
data_rows = []
cur_c, cur_d, cur_r = v_csh, v_pre, (v_roth + v_hsa)
ruin_yr, ruin_msg = None, ""

# Force valid simulation range
s_age = int(c_a)
f_age = int(max(c_a + 1, e_a))

for age in range(s_age, f_age + 1):
    yr = 2026 + (age - s_age)
    
    # Growth
    cur_c *= 1.01 # Nominal cash growth
    cur_d *= (1 + m_roi)
    cur_r *= (1 + m_roi)
    
    # Income/Expenses
    inc = (h_pay if age < h_r else 0) + (y_pay if age < y_r else 0)
    if age >= 67: inc += 85000 # SS Estimate
    
    exp = ex_r if (age >= y_r and age >= h_r) else ex_w
    edu = sum(tui for start_age in k_s if start_age <= age < start_age + 4)
    
    re_eq, re_pmt, re_noi = 0, 0, 0
    for p in p_list:
        h = yr - p["y"]
        if h < 0: continue
        val = p["v"] * ((1 + p["a"]) ** h)
        noi = p["n"] * ((1 + p["a"]) ** h)
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
        ruin_yr = age
        ruin_msg = f"Math won't work out starting in {yr} (Age {age}) because lifestyle/mortgage exceeds cash."

    nw = cur_c + cur_d + cur_r + re_eq
    data_rows.append({
        "Age": age, "Year": yr, "Cash": cur_c, 
        "Deferred": cur_d, "Roth_HSA": cur_r, 
        "RE_Equity": re_eq, "NW": nw
    })

# --- 3. FINAL RENDERING ---
st.title("✨ Legacy Master v9.2")

if len(data_rows) > 0:
    df = pd.DataFrame(data_rows)
    
    if ruin_yr:
        st.warning(f"⚠️ {ruin_msg}")

    # Metrics Row
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Current NW", f"${df.iloc[0]['NW']:,.0f}")
    ret_row = df[df['Age'] == y_r]
    ret_val = ret_row['NW'].values[0] if not ret_row.empty else 0
    m2.metric("NW @ Retirement", f"${ret_val:,.0f}")
    m3.metric("Final Estate", f"${df.iloc[-1]['NW']:,.0f}")
    m4.metric("Status", "Solvent" if not ruin_yr else "Deficit")

    # Stacked Bar Chart
    fig = go.Figure()
    cats = [("Cash","#3b82f6"), ("Roth_HSA","#10b981"), ("Deferred","#8b5cf6"), ("RE_Equity","#f59e0b")]
    for col, clr in cats:
        fig.add_trace(go.Bar(x=df["Age"], y=df[col], name=col, marker_color=clr))
    
    fig.update_layout(barmode='stack', template="plotly_dark", height=500, margin
