import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- 1. CORE CONFIG ---
st.set_page_config(layout="wide", page_title="Legacy Master 9.7")
st.title("✨ Legacy Master v9.7")

# --- 2. INPUTS (FLAT LIST FOR STABILITY) ---
sb = st.sidebar
sb.header("⚙️ Strategic Inputs")

# Real Estate Defaults
v1 = sb.number_input("Property 1 Value", value=1700000.0)
l1 = sb.number_input("Property 1 Loan", value=0.0)
n1 = sb.number_input("Property 1 Monthly Rent", value=4000.0)
appr = sb.number_input("Annual Appr %", value=3.0) / 100

# Portfolio Defaults
v_401 = sb.number_input("401k Balance", value=1200000.0)
v_roth = sb.number_input("Roth/HSA Balance", value=500000.0)
roi = sb.number_input("Portfolio ROI %", value=6.0) / 100

# Cash Flow
v_cash = sb.number_input("Checking/Savings", value=200000.0)
h_inc = sb.number_input("Husband Net Salary", value=145000.0)
y_inc = sb.number_input("Your Net Salary", value=110000.0)

# Tuition
tui = sb.number_input("Annual Tuition (per kid)", value=50000.0)
k1_age = sb.number_input("Child 1 College Start Age", value=52)
k2_age = sb.number_input("Child 2 College Start Age", value=57)

# Timeline
cur_age = sb.number_input("Current Age", value=42)
ret_age = sb.number_input("Retirement Age", value=55)
end_age = sb.number_input("Simulation End Age", value=95)
exp_w = sb.number_input("Annual Exp (Working)", value=150000.0)
exp_r = sb.number_input("Annual Exp (Retired)", value=120000.0)

# --- 3. MATH ENGINE ---
data = []
c_cash, c_401, c_roth = v_cash, v_401, v_roth
fail_yr = None

for a in range(int(cur_age), int(end_age) + 1):
    yr = 2026 + (a - int(cur_age))
    
    # Growth
    c_cash *= 1.02 # Cash inflation
    c_401 *= (1 + roi)
    c_roth *= (1 + roi)
    
    # Active Income vs SS
    inc = (h_inc + y_inc) if a < ret_age else 85000
    exp = exp_w if a < ret_age else exp_r
    
    # Tuition Check
    edu = 0
    if k1_age <= a < k1_age + 4: edu += tui
    if k2_age <= a < k2_age + 4: edu += tui
    
    # Simple RE Growth (1 Property for stability check)
    h = yr - 2026
    re_val = v1 * ((1 + appr) ** h)
    re_noi = (n1 * 12) * ((1 + appr) ** h)
    
    # Net Flow
    c_cash += (inc + re_noi - exp - edu)
    
    if c_cash < 0 and fail_yr is None:
        fail_yr = yr
        
    data.append({
        "Age": a, "Year": yr, "Cash": c_cash, 
        "401k": c_401, "Roth": c_roth, "RE": re_val,
        "NW": (c_cash + c_401 + c_roth + re_val)
    })

# --- 4. OUTPUT ---
if data:
    df = pd.DataFrame(data)
    
    if fail_yr:
        st.warning(f"⚠️ Cash Deficit in {fail_yr}")

    col1, col2 = st.columns(2)
    col1.metric("Current NW", f"${df.iloc[0]['NW']:,.0f}")
    col2.metric("Final Estate", f"${df.iloc[-1]['NW']:,.0f}")

    # Visual
    fig = go.Figure()
    for col, clr in [("RE","#f59e0b"),("401k","#8b5cf6"),("Roth","#10b981"),("Cash","#3b82f6")]:
        fig.add_trace(go.Scatter(x=df["Age"], y=df[col], name=col, stackgroup='one', fillcolor=clr))
    
    fig.update_layout(template="plotly_dark", height=500)
    st.plotly_chart(fig, use_container_width=True)
    
    st.dataframe(df.style.format("${:,.0f}"))
else:
    st.error("No data produced. Check sidebar age settings.")
