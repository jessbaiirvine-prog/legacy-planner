import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Legacy Master 9.5b")

# --- 1. SIDEBAR MODULES (LHS) ---
sb = st.sidebar
sb.title("⚙️ Strategic Planning")

# -- MODULE 1: RE INVESTMENT --
with sb.expander("🏠 RE INVESTMENT", expanded=True):
    np = sb.number_input("Property Count", value=1)
    plist = []
    for i in range(int(np)):
        st.markdown(f"**Property {i+1}**")
        v = sb.number_input("Current Value", value=950000.0, key=f"v{i}")
        l = sb.number_input("Loan Balance", value=700000.0, key=f"l{i}")
        y = sb.number_input("Year Purchased", value=2020, key=f"y{i}")
        t = sb.number_input("Loan Term (Yrs)", value=30, key=f"t{i}")
        r = sb.number_input("Int. Rate %", value=4.5, key=f"r{i}") / 100
        a = sb.number_input("Annual Appr %", value=3.0, key=f"a{i}") / 100
        n = sb.number_input("Monthly Net Rent", value=0.0, key=f"n{i}")
        
        p = 0
        if l > 0 and r > 0:
            mi, mt = r/12, t*12
            pw = (1 + mi)**mt
            p = l * (mi * pw) / (pw - 1)
        plist.append({"v":v,"l":l,"y":y,"t":t,"r":r,"a":a,"p":p*12,"n":n*12})

# -- MODULE 2: RETIREMENT SAVINGS --
with sb.expander("🏦 RETIREMENT", expanded=False):
    v_d = sb.number_input("401k (Deferred)", value=1200000.0)
    v_r = sb.number_input("Roth/HSA (Tax-Free)", value=150000.0)
    roi = sb.number_input("Market ROI %", value=6.0) / 100

# -- MODULE 3: KIDS TUITION (RE-ADDED) --
with sb.expander("🎓 KIDS TUITION", expanded=False):
    nk = sb.number_input("Number of Kids", value=2)
    tui_yr = sb.number_input("Annual Tuition per Kid", value=50000.0)
    k_ages = []
    for i in range(int(nk)):
        k_ages.append(sb.number_input(f"Child {i+1} College Start Age", value=52+(i*5)))

# -- MODULE 4: CASH & TIMELINE --
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
res = []
cc, cd, cr = v_c, v_d, v_r
fail_yr = None

for age in range(int(ca), int(ea) + 1):
    sim_yr = 2026 + (age - int(ca))
    cc *= 1.02 # Cash inflation hedge
    cd *= (1 + roi)
    cr *= (1 + roi)
    
    inc = (hp + yp) if age < yr else 85000 
    exp = ew if age < yr else er
    
    # TUITION CALCULATION
    edu_cost = 0
    for start_age in k_ages:
        if start_age <= age < (start_age + 4):
            edu_cost += tui_yr

    re_eq, re_pmt, re_noi = 0, 0, 0
    for o in plist:
        h = sim_yr - o["y"]
        if h < 0: continue
        val = o["v"] * ((1 + o["a"]) ** h)
        noi = o["n"] * ((1 + o["a"]) ** h)
        if h < o["t"]:
            m, mt, dn = o["r"]/12, o["t"]*12, h*12
            deb = o["l"] * ((1+m)**mt - (1+m)**dn) / ((1+m)**mt - 1)
            re_pmt += o["p"]
        else: deb = 0
        re_eq += (val - deb)
        re_noi += noi

    cc += (inc + re_noi - exp - re_pmt - edu_cost)
    if cc < 0 and fail_yr is None: fail_yr = sim_yr
        
    res.append({
        "Age": age, "Year": sim_yr, "Cash": cc, 
        "401k": cd, "Roth": cr, "RE": re_eq, 
        "NW": cc + cd + cr + re_eq
    })

# --- 3. OUTPUT & RENDERING ---
st.title("🛡️ Legacy Master: Audited v9.5b")

if res:
    df = pd.DataFrame(res)
    if fail_yr:
        st.warning(f"⚠️ **Cash Deficit:** Liquid reserves hit zero in {fail_yr}.")

    m1, m2, m3 = st.columns(3)
    m1.metric("Current NW", f"${df.iloc[0]['NW']:,.0f}")
    m2.metric("Age 90 NW", f"${df[df['Age']==90]['NW'].values[0]:,.0f}")
    m3.metric("Final Estate", f"${df.iloc[-1]['NW']:,.0f}")

    # Stacked Area Visual
    fig = go.Figure()
    for col, clr in [("RE","#f59e0b"), ("401k","#8b5cf6"), ("Roth","#10b981"), ("Cash","#3b82f6")]:
        fig.add_trace(go.Scatter(x=df["Age"], y=df[col], name=col, stackgroup='one', fillcolor=clr, line=dict(width=0.5)))
    fig.update_layout(template="plotly_dark", height=500, yaxis_title="Total Wealth ($)")
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("🔎 VIEW ANNUAL AUDIT LOG"):
        st.dataframe(df.style.format("${:,.0f}"))
