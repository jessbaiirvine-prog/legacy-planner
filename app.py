import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Legacy 8.3")

# --- 1. TOP LAYOUT ---
t_head = st.container()
t_chart = st.container()

# --- 2. MODULAR LHS PARAMETERS ---
sb = st.sidebar
sb.title("⚙️ Dashboard Controls")

# -- MODULE: RE INVESTMENT --
with sb.expander("🏠 RE INVESTMENT", expanded=True):
    n_p = st.number_input("Property Count", 0, 15, 1)
    p_list = []
    for i in range(int(n_p)):
        st.markdown(f"**Prop {i+1}**")
        v = st.number_input("Price", value=950000.0, key=f"v{i}")
        l = st.number_input("Loan", value=700000.0, key=f"l{i}")
        y = st.number_input("Year Bought", value=2020, key=f"y{i}")
        t = st.number_input("Term", value=30, key=f"t{i}")
        r = st.number_input("Rate %", value=4.5, key=f"r{i}") / 100
        a = st.number_input("Appr %", value=3.0, key=f"a{i}") / 100
        n = st.number_input("Mo. Net Rent", value=0.0, key=f"n{i}")
        
        pmt = 0
        if l > 0 and r > 0:
            mi, mt = r/12, t*12
            pw = (1+mi)**mt
            mp = l*(mi*pw)/(pw-1)
            pmt = mp*12
        p_list.append({"v":v,"l":l,"y":y,"t":t,"r":r,"a":a,"p":pmt,"n":n*12})

# -- MODULE: RETIREMENT SAVINGS --
with sb.expander("🏦 RETIREMENT SAVINGS", expanded=False):
    v_401 = st.number_input("401k Pre-Tax", value=1200000.0)
    v_roth = st.number_input("Roth 401k", value=100000.0)
    v_r_ira = st.number_input("Roth IRA", value=200000.0)
    v_hsa = st.number_input("HSA Balance", value=50000.0)
    roi = st.number_input("Market Return %", value=6.0) / 100

# -- MODULE: CASH ASSETS --
with sb.expander("💵 CASH ASSETS", expanded=False):
    v_cash = st.number_input("Checking/Savings", value=200000.0)
    h_net = st.number_input("Husband Net Pay", value=145000.0)
    y_net = st.number_input("Your Net Pay", value=110000.0)

# -- MODULE: TIMELINE & EXPENSES --
with sb.expander("📅 TIMELINE & EXPENSES", expanded=False):
    age = st.number_input("Current Age", value=42)
    y_r = st.number_input("Your Retire Age", value=55)
    h_r = st.number_input("Husband Retire Age", value=58)
    e_a = st.number_input("End Age", value=95)
    ex_w = st.number_input("Annual Exp (Working)", value=150000.0)
    ex_r = st.number_input("Annual Exp (Retired)", value=120000.0)

# -- MODULE: KIDS TUITION --
with sb.expander("🎓 KIDS TUITION", expanded=False):
    n_k = st.number_input("Number of Kids", 0, 5, 2)
    tui = st.number_input("Annual Tuition", value=50000.0)
    k_s = [st.number_input(f"K{i+1} Start Age", value=52+(i*6)) for i in range(int(n_k))]

# --- 3. MATH ENGINE ---
data, ruin_yr, ruin_msg = [], None, ""
c_c = v_cash
c_d = v_401
c_r = v_roth + v_r_ira + v_hsa
now = 2026

for a in range(age, e_a + 1):
    yr = now + (a - age)
    c_c *= (1 + (roi*0.5)) # Cash grows slower
    c_d *= (1 + roi)
    c_r *= (1 + roi)
    
    inc = (h_net if a < h_r else 0) + (y_net if a < y_r else 0)
    if a >= 67: inc += 85000
    
    exp = ex_r if (a >= y_r and a >= h_r) else ex_w
    edu = sum(tui for s in k_s if s <= a < s + 4)
    
    re_eq, re_pm, re_in = 0, 0, 0
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
            re_pm += p["p"]
        re_eq += (val - deb)
        re_in += noi

    c_c += (inc + re_in - exp - edu - re_pm)
    
    # Sustainability Check
    if c_c < 0 and ruin_yr is None:
        ruin_yr = a
        ruin_msg = f"In year {yr} (Age {a}), lifestyle/mortgage costs exceed cash reserves."

    nw = c_c + c_d + c_r + re_eq
    data.append({"Age":a,"Year":yr,"Cash":c_c,"Def":c_d,"Roth":c_r,"RE":re_eq,"NW":nw})

df = pd.DataFrame(data)

# --- 4. OUTPUTS ---
with t_head:
    st.title("✨ Legacy Master v8.3")
    if ruin_yr:
        st.error(f"⚠️ **UNSUSTAINABLE MATH:** {ruin_msg}")
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Current NW", f"${df.iloc[0]['NW']:,.0f}")
    df_r = df[df['Age'] == y_r]
    v2 = df_r['NW'].values[0] if not df_r.empty else 0
    m2.metric("At Retire", f"${v2:,.0f}")
    m3.metric("Final Estate", f"${df.iloc[-1]['NW']:,.0f}")
    m4.metric("Sim Status", "Healthy" if not ruin_yr else "Deficit")

with t_chart:
    fig = go.Figure()
    ly = [("Cash","#3b82f6"),("Roth","#10b981"),("Def","#8b5cf6"),("RE","#f59e0b")]
    for c, cl in ly:
        fig.add_trace(go.Bar(x=df["Age"], y=df[c], name=c, marker_color=cl))
    
    fig.update_layout(barmode='stack', template="plotly_dark", height=450, 
                      margin=dict(t=10,b=10), legend=dict(orientation="h",y=1.1))
    st.plotly_chart(fig, use_container_width=True)

# -- MODULE: ANNUAL EXPENSE TABLE --
with st.expander("📊 ANNUAL EXPENSE & CASHFLOW TABLE"):
    # Calculate simple cashflow view
    df_view = df.copy()
    df_view['Total_Liquid'] = df_view['Cash'] + df_view['Def'] + df_view['Roth']
    st.dataframe(df_view[['Age', 'Year', 'Cash', 'Total_Liquid', 'RE', 'NW']].style.format("${:,.0f}"))
