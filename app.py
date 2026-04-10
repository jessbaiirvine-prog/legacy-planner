import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Legacy Master 9.8")

# --- 1. SIDEBAR MODULES (LHS) ---
sb = st.sidebar
sb.title("⚙️ Strategic Planning")

with sb.expander("🏠 RE INVESTMENT", expanded=True):
    np = sb.number_input("Property Count", value=1, min_value=0)
    plist = []
    for i in range(int(np)):
        st.markdown(f"**Property {i+1}**")
        v = sb.number_input("Current Value", value=1700000.0, key=f"re_v{i}")
        l = sb.number_input("Loan Balance", value=0.0, key=f"re_l{i}")
        y = sb.number_input("Year Purchased", value=2020, key=f"re_y{i}")
        t = sb.number_input("Loan Term (Yrs)", value=30, key=f"re_t{i}")
        r = sb.number_input("Int. Rate %", value=4.5, key=f"re_r{i}") / 100
        a = sb.number_input("Annual Appr %", value=3.0, key=f"re_a{i}") / 100
        n = sb.number_input("Monthly Net Rent", value=4000.0, key=f"re_n{i}")
        p = 0
        if l > 0 and r > 0:
            mi, mt = r/12, t*12
            pw = (1 + mi)**mt
            p = l * (mi * pw) / (pw - 1)
        plist.append({"v":v,"l":l,"y":y,"t":t,"r":r,"a":a,"p":p*12,"n":n*12})

with sb.expander("🏦 RETIREMENT", expanded=False):
    v_d = sb.number_input("401k (Deferred)", value=1200000.0)
    v_r = sb.number_input("Roth/HSA (Tax-Free)", value=500000.0)
    roi = sb.number_input("Market ROI %", value=6.0) / 100

with sb.expander("🎓 KIDS TUITION", expanded=False):
    nk = sb.number_input("Number of Kids", value=2, min_value=0)
    tui_yr = sb.number_input("Annual Tuition per Kid", value=50000.0)
    k_ages = []
    for i in range(int(nk)):
        k_ages.append(sb.number_input(f"Child {i+1} College Start Age", value=52+(i*5)))

with sb.expander("💵 CASH & TIMELINE", expanded=False):
    v_c = sb.number_input("Current Savings", value=200000.0)
    hp = sb.number_input("Husband Net Salary", value=145000.0)
    yp = sb.number_input("Your Net Salary", value=110000.0)
    ca = sb.number_input("Current Age", 42)
    yr = sb.number_input("Retire Age", 55)
    ea = sb.number_input("End Age", 95)
    ew = sb.number_input("Annual Exp (Work)", 150000.0)
    er = sb.number_input("Annual Exp (Retire)", 120000.0)

# --- 2. MATH ENGINE ---
res, res_cashflow = [], []
cc, cd, cr = v_c, v_d, v_r
fail_yr, num_insolvent_yrs = None, 0

for age in range(int(ca), int(ea) + 1):
    sim_yr = 2026 + (age - int(ca))
    cc *= 1.02 
    cd *= (1 + roi)
    cr *= (1 + roi)
    
    inc_salary = (hp + yp) if age < yr else 0
    inc_ss = 85000 if age >= 67 else 0
    exp_life = -(ew if age < yr else er) 
    
    edu_cost = 0
    for start_age in k_ages:
        if start_age <= age < (start_age + 4):
            edu_cost -= tui_yr 

    re_eq, exp_pmt, inc_noi = 0, 0, 0
    for o in plist:
        h = sim_yr - o["y"]
        if h < 0: continue
        val = o["v"] * ((1 + o["a"]) ** h)
        noi = o["n"] * ((1 + o["a"]) ** h)
        if h < o["t"]:
            m, mt, dn = o["r"]/12, o["t"]*12, h*12
            deb = o["l"] * ((1+m)**mt - (1+m)**dn) / ((1+m)**mt - 1)
            exp_pmt -= o["p"] 
        else: deb = 0
        re_eq += (val - deb)
        inc_noi += noi

    total_inc = inc_salary + inc_ss + inc_noi
    total_exp = exp_life + exp_pmt + edu_cost
    cc += (total_inc + total_exp)
    
    if cc < 0 and fail_yr is None:
        fail_yr = sim_yr
    if cc < 0:
        num_insolvent_yrs += 1
        
    res.append({
        "Age": age, "Year": sim_yr, "Cash": max(0, cc), 
        "401k": cd, "Roth": cr, "RE": re_eq, 
        "NW": max(0, cc) + cd + cr + re_eq
    })
    
    res_cashflow.append({
        "Age": age, "Salary": inc_salary, "SS": inc_ss, "Rent": inc_noi,
        "Lifestyle": exp_life, "Tuition": edu_cost, "Mortgage": exp_pmt
    })

# --- 3. OUTPUT & VISUALS ---
st.title("🛡️ Legacy Master: Executive Summary v9.8")

df = pd.DataFrame(res)
df_cf = pd.DataFrame(res_cashflow)

# --- THE SUMMARY METRICS (RESTORED) ---
st.markdown("### 📊 Financial Overview")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Current Net Worth", f"${df.iloc[0]['NW']:,.0f}")
c2.metric(f"NW at Retire (Age {yr})", f"${df[df['Age']==yr]['NW'].values[0]:,.0f}")
c3.metric("Final Estate (Age 95)", f"${df.iloc[-1]['NW']:,.0f}")
status = "HEALTHY" if not fail_yr else "DEFICIT"
c4.metric("Liquidity Status", status, delta=None if not fail_yr else f"-{num_insolvent_yrs} Yrs", delta_color="inverse")

if fail_yr:
    st.error(f"⚠️ **Cash Depletion Alert:** Liquid reserves hit zero in the year {fail_yr}.")

# --- THE ORIGINAL CHART (RESTORED TOTAL NW BAR CHART) ---
st.markdown("### 📈 Total Wealth Projection")
fig1 = go.Figure()
fig1.add_trace(go.Bar(x=df["Age"], y=df["NW"], name="Total Net Worth", marker_color="#0ea5e9"))
fig1.update_layout(template="plotly_dark", height=450, yaxis_title="Total Assets ($)", margin=dict(l=20, r=20, t=20, b=20))
st.plotly_chart(fig1, use_container_width=True)

# --- ASSET DISTRIBUTION (GROUPED BARS) ---
st.markdown("### 📂 Asset Portfolio Breakdown")
fig2 = go.Figure()
for col, clr in [("RE","#f59e0b"), ("401k","#8b5cf6"), ("Roth","#10b981"), ("Cash","#3b82f6")]:
    fig2.add_trace(go.Bar(x=df["Age"], y=df[col], name=col, marker_color=clr))
fig2.update_layout(barmode='group', template="plotly_dark", height=450, yaxis_title="Asset Value ($)")
st.plotly_chart(fig2, use_container_width=True)

# --- ANNUAL FLOW (INCOME VS SPENDING PEAKS) ---
st.markdown("### 💸 Annual Inflow vs. Spending Peaks")
fig3 = go.Figure()
# Inflows
for col, clr in [("Salary","#1e3a8a"), ("Rent","#1d4ed8"), ("SS","#3b82f6")]:
    fig3.add_trace(go.Bar(x=df_cf["Age"], y=df_cf[col], name=col, marker_color=clr))
# Outflows
for col, clr in [("Lifestyle","#991b1b"), ("Mortgage","#dc2626"), ("Tuition","#ef4444")]:
    fig3.add_trace(go.Bar(x=df_cf["Age"], y=df_cf[col], name=col, marker_color=clr))

fig3.update_layout(barmode='relative', template="plotly_dark", height=450, yaxis_title="Annual Flow ($)")
st.plotly_chart(fig3, use_container_width=True)

with st.expander("🔎 View Annual Audit Ledger"):
    st.dataframe(df.style.format("${:,.0f}"))
