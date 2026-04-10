import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Legacy Master 9.5c")

# --- 1. SIDEBAR MODULES (LHS) ---
sb = st.sidebar
sb.title("⚙️ Strategic Planning")

with sb.expander("🏠 RE INVESTMENT", expanded=True):
    np = sb.number_input("Property Count", value=1, min_value=0)
    plist = []
    for i in range(int(np)):
        st.markdown(f"**Property {i+1}**")
        v = sb.number_input("Current Value", value=950000.0, key=f"re_v{i}")
        l = sb.number_input("Loan Balance", value=700000.0, key=f"re_l{i}")
        y = sb.number_input("Year Purchased", value=2020, key=f"re_y{i}")
        t = sb.number_input("Loan Term (Yrs)", value=30, key=f"re_t{i}")
        r = sb.number_input("Int. Rate %", value=4.5, key=f"re_r{i}") / 100
        a = sb.number_input("Annual Appr %", value=3.0, key=f"re_a{i}") / 100
        n = sb.number_input("Monthly Net Rent", value=0.0, key=f"re_n{i}")
        p = 0
        if l > 0 and r > 0:
            mi, mt = r/12, t*12
            pw = (1 + mi)**mt
            p = l * (mi * pw) / (pw - 1)
        plist.append({"v":v,"l":l,"y":y,"t":t,"r":r,"a":a,"p":p*12,"n":n*12})

with sb.expander("🏦 RETIREMENT", expanded=False):
    v_d = sb.number_input("401k (Deferred)", value=1200000.0)
    v_r = sb.number_input("Roth/HSA (Tax-Free)", value=150000.0)
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
    cc *= 1.02 # Cash stays at 2%
    cd *= (1 + roi)
    cr *= (1 + roi)
    
    inc_salary = (hp + yp) if age < yr else 0
    inc_ss = 85000 if age >= 67 else 0
    exp_life = -(ew if age < yr else er) # Lifestyle spending (negative)
    
    edu_cost = 0
    for start_age in k_ages:
        if start_age <= age < (start_age + 4):
            edu_cost -= tui_yr # Tuition spending (negative)

    re_eq, exp_pmt, inc_noi = 0, 0, 0
    for o in plist:
        h = sim_yr - o["y"]
        if h < 0: continue
        val = o["v"] * ((1 + o["a"]) ** h)
        noi = o["n"] * ((1 + o["a"]) ** h)
        if h < o["t"]:
            m, mt, dn = o["r"]/12, o["t"]*12, h*12
            deb = o["l"] * ((1+m)**mt - (1+m)**dn) / ((1+m)**mt - 1)
            exp_pmt -= o["p"] # Mortgage spending (negative)
        else: deb = 0
        re_eq += (val - deb)
        inc_noi += noi

    # Current year net flow and update total cash
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
    
    # New breakdown list for expenses chart
    res_cashflow.append({
        "Age": age, "Salary_Income": inc_salary, "SS_Income": inc_ss, "Rent_NOI_Income": inc_noi,
        "Lifestyle_Spend": exp_life, "Tuition_Spend": edu_cost, "Mortgage_Spend": exp_pmt,
        "Net_Flow": total_inc + total_exp
    })

# --- 3. OUTPUT & VISUALS ---
st.title("🛡️ Legacy Master: Visual Audit v9.5c")
df = pd.DataFrame(res)
df_cf = pd.DataFrame(res_cashflow)

# Liquidity Check Mechanism
if fail_yr:
    st.error(f"🛑 **Zero Liquidity Warning:** Your liquid reserves hit zero in {fail_yr}. You face {num_insolvent_yrs} years of math failure.")
    
    # Special Visualization for Insolvency
    st.subheader("⚠️ Insolvency Tracker")
    l_c1, l_c2 = st.columns(2)
    l_c1.metric("First Year of Failure", fail_yr)
    l_c2.metric("Total Years with Deficit", f"{num_insolvent_yrs} Yrs")
    
    # Special Insolvency Chart (focused only on the critical 'Cash' years)
    fig_i = go.Figure()
    fig_i.add_trace(go.Scatter(x=df["Age"], y=df["Cash"], name="Liquid Reserves ($)", mode='lines+markers', line=dict(color="#3b82f6", width=2)))
    fig_i.add_hline(y=0, line_dash="dash", line_color="#ef4444", annotation_text="Mathematical Bankruptcy Line", annotation_position="bottom right")
    fig_i.update_layout(template="plotly_dark", height=300, yaxis_title="Cash Reserves ($)")
    st.plotly_chart(fig_i, use_container_width=True)
    
else:
    # Key Metrics (Solvent Case)
    m1, m2, m3 = st.columns(3)
    m1.metric("Current NW", f"${df.iloc[0]['NW']:,.0f}")
    m2.metric("Age 90 NW", f"${df[df['Age']==90]['NW'].values[0]:,.0f}")
    m3.metric("Final Estate", f"${df.iloc[-1]['NW']:,.0f}")

    # Main Chart: Grouped Bar Chart of Assets
    st.subheader("Asset Breakdown over Time")
    fig = go.Figure()
    for col, clr in [("RE","#f59e0b"), ("401k","#8b5cf6"), ("Roth","#10b981"), ("Cash","#3b82f6")]:
        fig.add_trace(go.Bar(x=df["Age"], y=df[col], name=col, marker_color=clr))
    
    fig.update_layout(barmode='group', template="plotly_dark", height=500, yaxis_title="Wealth ($)")
    st.plotly_chart(fig, use_container_width=True)

# New Chart 2: Annual Expenses and Income Peaks
st.subheader("Spending Peaks vs. Income Bridges (Audit View)")
st.info("💡 spending bars are negative, income bars are positive. Locate large negative bars to see major costs.")

fig2 = go.Figure()
# Positive Inflows
fig2.add_trace(go.Bar(x=df_cf["Age"], y=df_cf["Salary_Income"], name="Salary In", marker_color="#1e3a8a", legendgroup="I"))
fig2.add_trace(go.Bar(x=df_cf["Age"], y=df_cf["Rent_NOI_Income"], name="Net Rent In", marker_color="#1d4ed8", legendgroup="I"))
fig2.add_trace(go.Bar(x=df_cf["Age"], y=df_cf["SS_Income"], name="SS In", marker_color="#3b82f6", legendgroup="I"))

# Negative Outflows (Expenses)
fig2.add_trace(go.Bar(x=df_cf["Age"], y=df_cf["Lifestyle_Spend"], name="Lifestyle Spend", marker_color="#991b1b", legendgroup="S"))
fig2.add_trace(go.Bar(x=df_cf["Age"], y=df_cf["Mortgage_Spend"], name="Mortgage Spend", marker_color="#dc2626", legendgroup="S"))
fig2.add_trace(go.Bar(x=df_cf["Age"], y=df_cf["Tuition_Spend"], name="College Spend (⚠️)", marker_color="#ef4444", legendgroup="S"))

fig2.update_layout(barmode='relative', template="plotly_dark", height=500, yaxis_title="Annual Flow ($)")
fig2.add_hline(y=0, line_dash="solid", line_color="#444444")
st.plotly_chart(fig2, use_container_width=True)

# --- LEDGER expander remains ---
with st.expander("🔎 VIEW AUDIT LOG (Annual Breakdown)"):
    st.dataframe(df.style.format("${:,.0f}"))
