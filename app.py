import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Legacy Master 9.5")

# --- 1. SIDEBAR MODULES (LHS) ---
sb = st.sidebar
sb.title("⚙️ Strategic Planning")

with sb.expander("🏠 RE INVESTMENT", expanded=True):
    np = sb.number_input("Property Count", value=1)
    plist = []
    for i in range(int(np)):
        st.markdown(f"**Property {i+1}**")
        v = st.number_input("Current Value", value=950000.0, key=f"v{i}")
        l = st.number_input("Loan Balance", value=700000.0, key=f"l{i}")
        y = st.number_input("Year Purchased", value=2020, key=f"y{i}")
        t = st.number_input("Loan Term (Yrs)", value=30, key=f"t{i}")
        r = st.number_input("Int. Rate %", value=4.5, key=f"r{i}") / 100
        a = st.number_input("Annual Appr %", value=3.0, key=f"a{i}") / 100
        n = st.number_input("Monthly Net Rent", value=0.0, key=f"n{i}")
        
        # Monthly Mortgage Calculation
        p = 0
        if l > 0 and r > 0:
            mi = r / 12
            mt = t * 12
            pw = (1 + mi)**mt
            p = l * (mi * pw) / (pw - 1)
        plist.append({"v":v,"l":l,"y":y,"t":t,"r":r,"a":a,"p":p*12,"n":n*12})

with sb.expander("🏦 RETIREMENT", expanded=False):
    v_d = st.number_input("401k (Deferred)", value=1200000.0)
    v_r = st.number_input("Roth/HSA (Tax-Free)", value=150000.0)
    roi = st.number_input("Market ROI %", value=6.0) / 100

with sb.expander("💵 CASH ASSETS", expanded=False):
    v_c = st.number_input("Current Savings", value=200000.0)
    hp = st.number_input("Husband Net Salary", value=145000.0)
    yp = st.number_input("Your Net Salary", value=110000.0)

with sb.expander("📅 TIMELINE & EXPENSES", expanded=False):
    ca = st.number_input("Current Age", 42)
    yr = st.number_input("Retire Age", 55)
    ea = st.number_input("End Age", 95)
    ew = st.number_input("Annual Exp (Work)", 150000.0)
    er = st.number_input("Annual Exp (Retire)", 120000.0)

# --- 2. MATH ENGINE ---
res = []
cc, cd, cr = v_c, v_d, v_r
fail_yr = None

for age in range(int(ca), int(ea) + 1):
    sim_yr = 2026 + (age - int(ca))
    
    # ACCURACY FIX: Cash only grows at 2% (Savings Rate), Portfolio at ROI
    cc *= 1.02 
    cd *= (1 + roi)
    cr *= (1 + roi)
    
    # Income & Social Security
    inc = (hp + yp) if age < yr else 85000 
    exp = ew if age < yr else er
    
    re_eq, re_pmt, re_noi = 0, 0, 0
    for o in plist:
        years_held = sim_yr - o["y"]
        if years_held < 0: continue
        
        # Current Value (Appreciation)
        current_val = o["v"] * ((1 + o["a"]) ** years_held)
        # Rent (Grows with appreciation/inflation)
        current_noi = o["n"] * ((1 + o["a"]) ** years_held)
        
        # Debt Calculation
        if years_held < o["t"]:
            m = o["r"] / 12
            total_mo = o["t"] * 12
            done_mo = years_held * 12
            # Remaining Balance Formula
            deb = o["l"] * ((1 + m)**total_mo - (1 + m)**done_mo) / ((1 + m)**total_mo - 1)
            re_pmt += o["p"]
        else:
            deb = 0 # House is paid off
            
        re_eq += (current_val - deb)
        re_noi += current_noi

    # Update Cash Flow
    net_flow = (inc + re_noi) - (exp + re_pmt)
    cc += net_flow
    
    if cc < 0 and fail_yr is None:
        fail_yr = sim_yr
        
    res.append({
        "Age": age, "Year": sim_yr, "Cash": cc, 
        "401k": cd, "Roth": cr, "RE_Equity": re_eq, 
        "Total_NW": cc + cd + cr + re_eq
    })

# --- 3. OUTPUT & ACCURACY CHECK ---
st.title("🛡️ Legacy 9.5: Audited Planner")

if fail_yr:
    st.warning(f"⚠️ **Cash Deficit:** Your liquid reserves hit zero in {fail_yr}. Review expenses vs. passive income.")

df = pd.DataFrame(res)

# Verification Metrics
c1, c2, c3 = st.columns(3)
c1.metric("Current NW", f"${df.iloc[0]['Total_NW']:,.0f}")
c2.metric("Age 90 NW", f"${df[df['Age']==90]['Total_NW'].values[0]:,.0f}")
c3.metric("Final Estate", f"${df.iloc[-1]['Total_NW']:,.0f}")

# Stacked Visual
fig = go.Figure()
for c, clr in [("RE_Equity","#f59e0b"), ("401k","#8b5cf6"), ("Roth","#10b981"), ("Cash","#3b82f6")]:
    fig.add_trace(go.Scatter(x=df["Age"], y=df[c], name=c, stackgroup='one', fillcolor=clr, line=dict(width=0.5)))

fig.update_layout(template="plotly_dark", height=500, yaxis_title="Wealth ($)")
st.plotly_chart(fig, use_container_width=True)

with st.expander("🔎 VIEW AUDIT LOG (Annual Breakdown)"):
    st.dataframe(df.style.format("${:,.0f}"))
