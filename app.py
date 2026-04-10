import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Legacy 8.7")

# --- 1. TOP SLOTS ---
t_head = st.container()
t_chart = st.container()

# --- 2. MODULAR SIDEBAR (LHS) ---
sb = st.sidebar
sb.title("⚙️ Strategic Planning")

# -- MODULE: RE INVESTMENT --
with sb.expander("🏠 RE INVESTMENT", expanded=True):
    n_p = st.number_input("Property Count", value=1)
    p_list = []
    for i in range(int(n_p)):
        st.markdown(f"**Property {i+1}**")
        v = st.number_input("Market Value", value=950000.0, key=f"v{i}")
        l = st.number_input("Loan Balance", value=700000.0, key=f"l{i}")
        y = st.number_input("Year Purchased", value=2020, key=f"y{i}")
        t = st.number_input("Loan Term (Yrs)", value=30, key=f"t{i}")
        r = st.number_input("Interest Rate %", value=4.5, key=f"r{i}") / 100
        a = st.number_input("Annual Appr %", value=3.0, key=f"a{i}") / 100
        n = st.number_input("Monthly Net Rent (NOI)", value=0.0, key=f"n{i}")
        
        pmt = 0
        if l > 0 and r > 0:
            mi, mt = r/12, t*12
            pw = (1 + mi)**mt
            mp = l * (mi * pw) / (pw - 1)
            pmt = mp * 12
        p_list.append({"v":v,"l":l,"y":y,"t":t,"r":r,"a":a,"p":pmt,"n":n*12})

# -- MODULE: RETIREMENT SAVINGS --
with sb.expander("🏦 RETIREMENT SAVINGS", expanded=False):
    v_401 = st.number_input("401k (Pre-Tax)", value=1200000.0)
    v_r40 = st.number_input("Roth 401k", value=100000.0)
    v_rir = st.number_input("Roth IRA", value=200000.0)
    v_hsa = st.number_input("HSA Balance", value=50000.0)
    m_roi = st.number_input("Portfolio Return %", value=6.0) / 100

# -- MODULE: CASH ASSETS --
with sb.expander("💵 CASH ASSETS", expanded=False):
    v_csh = st.number_input("Checking/Savings Account", value=200000.0)
    h_pay = st.number_input("Husband Net Salary", value=145000.0)
    y_pay = st.number_input("Your Net Salary", value=110000.0)

# -- MODULE: KIDS TUITION --
with sb.expander("🎓 KIDS TUITION", expanded=False):
    n_k = st.number_input("Number of Kids", value=2)
    tui = st.number_input("Tuition per Year", value=50000.0)
    k_s = []
    # Using a standard loop to prevent the 'SyntaxError' on list comps
    for i in range(int(n_k)):
        label = f"K{i+1} College Start Age"
        val = 52 + (i * 6)
        ks_val = st.number_input(label, value=val)
        k_s.append(ks_val)

# -- MODULE: TIMELINE & EXPENSES --
with sb.expander("📅 TIMELINE & EXPENSES", expanded=False):
    c_a = st.number_input("Current Age", value=42)
    y_r = st.number_input("Your Retire Age", value=55)
    h_r = st.number_input("Husband Retire Age", value=58)
    e_a = st.number_input("Simulation End Age", value=95)
    ex_w = st.number_input("Annual Expense (Working)", value=150000.0)
    ex_r = st.number_input("Annual Expense (Retired)", value=120000.0)

# --- 3. MATH ENGINE ---
results = []
cur_c, cur_d, cur_r = v_csh, v_401, (v_r40 + v_rir + v_hsa)
ruin_yr, ruin_msg = None, ""

s_age = int(c_a)
f_age = int(max(c_a, e_a))

for age in range(s_age, f_age + 1):
    yr = 2026 + (age - s_age)
    cur_c *= (1 + (m_roi * 0.2)) 
    cur_d *= (1 + m_roi)
    cur_r *= (1 + m_roi)
    
    inc = (h_pay if age < h_r else 0) + (y_pay if age < y_r else 0)
    if age >= 67: inc += 85000 
    
    exp = ex_r if (age >= y_r and age >= h_r) else ex_w
    edu = 0
    for start_age in k_s:
        if start_age <= age < start_age + 4:
            edu += tui
    
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
        ruin_yr, ruin_msg = age, f"Deficit starts in {yr} (Age {age})."

    nw = cur_c + cur_d + cur_r + re_eq
    results.append({
        "Age": age, "Year": yr, "Checking": cur_c, 
        "Deferred": cur_d, "Roth_HSA": cur_r, 
        "RE_Equity": re_eq, "NW": nw
    })

# --- 4. OUTPUTS ---
if len(results) > 0:
    df = pd.DataFrame(results)

    with t_head:
        st.title("✨ Legacy Master v8.7")
        if ruin_yr:
            st.error(f"🛑 **UNSUSTAINABLE:** {ruin_msg}")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Current NW", f"${df.iloc[0]['NW']:,.0f}")
        
        r_df = df[df['Age'] == y_r]
        rv = r_df['NW'].values[0] if not r_df.empty else 0
        m2.metric("At Your Retirement", f"${rv:,.0f}")
        m3.metric("Final Estate", f"${df.iloc[-1]['NW']:,.0f}")
        m4.metric("Status", "Solvent" if not ruin_yr else "Deficit")

    with t_chart:
        fig = go.Figure()
        cts = [("Checking","#3b82f6"), ("Roth_HSA","#10b981"), 
               ("Deferred","#8b5cf6"), ("RE_Equity","#f59e0b")]
        for col, clr in cts:
            fig.add_trace(go.Bar(x=df["Age"], y=df[col], name=col, marker_color=clr))
        
        fig.update_layout(barmode='stack', template="plotly_dark", height=450, 
                          margin=dict(t=10,b=10), legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("📊 ANNUAL LEDGER"):
        st.dataframe(df.style.format("${:,.0f}"))
