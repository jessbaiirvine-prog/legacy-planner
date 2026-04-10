import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(page_title="Legacy Planner v5.5", layout="wide")

st.title("🌏 Global Legacy Master v5.5")
st.markdown("Chart Logic Reset & Stability Patch")

# --- SIDEBAR: CONTROLS ---
with st.sidebar:
    st.header("1. Milestones")
    curr_age = st.slider("Current Age", 30, 65, 42)
    y_ret_age = st.slider("Your Retirement Age", 45, 75, 55)
    h_ret_age = st.slider("Husband Retirement Age", 45, 75, 58)
    ss_age = st.slider("Social Security Age", 62, 72, 67)
    d_age = st.slider("Simulation End", 80, 110, 95)
    
    st.header("2. Returns")
    r40 = st.slider("Returns 40s (%)", 0.0, 15.0, 7.0) / 100
    r50 = st.slider("Returns 50s (%)", 0.0, 15.0, 5.0) / 100
    r60 = st.slider("Returns 60+ (%)", 0.0, 10.0, 4.0) / 100

    st.header("3. Education")
    n_kids = st.number_input("Children", 0, 5, 2)
    tui = st.number_input("Annual Tuition ($)", value=50000)
    k_starts = [st.number_input(f"Child {i+1} Start", 40, 75, 52+(i*6), key=f"k{i}") for i in range(n_kids)]

    st.header("4. Finance")
    h_net = st.number_input("Husband Net ($)", value=145000)
    y_net = st.number_input("Your Net ($)", value=110000)
    exp_w = st.number_input("Working Expenses ($)", value=210000)
    exp_r = st.number_input("Retirement Expenses ($)", value=150000)

# --- REAL ESTATE ---
st.header("🏠 Real Estate Portfolio")
re_data = []
cols = st.columns(3)
for i in range(6):
    with cols[i % 3]:
        with st.expander(f"Property {i+1}", expanded=(i < 4)):
            is_pri = st.checkbox("Primary?", value=(i==0), key=f"p{i}")
            cf = 0 if is_pri else st.number_input("Cashflow", value=7800 if i<4 else 0, key=f"c{i}")
            m_s = st.number_input("Mtg Start", value=35, key=f"s{i}")
            m_t = st.number_input("Term", value=30, key=f"t{i}")
            m_p = st.number_input("Payment", value=15000 if i<4 else 0, key=f"m{i}")
            re_data.append({"inc": cf, "start": m_s, "end": m_s+m_t, "pay": m_p})

# --- MATH ENGINE ---
def run_model():
    port = 1700000 
    res = []
    for a in range(curr_age, d_age + 1):
        rate = r60
        if a < 50: rate = r40
        elif a < 60: rate = r50
        
        growth = port * rate
        h_inc = h_net if a < h_ret_age else 0
        y_inc = y_net if a < y_ret_age else 0
        ss_inc = 85000 if a >= ss_age else 0
        rent_inc = sum([p["inc"] for p in re_data])
        mtg_pay = sum([p["pay"] for p in re_data if p["start"] <= a < p["end"]])
        edu = sum([tui for s in k_starts if s <= a < (s + 4)])
        liv = exp_r if (a >= y_ret_age and a >= h_ret_age) else exp_w
        
        net_cf = (h_inc + y_inc + ss_inc + rent_inc + growth) - (liv + mtg_pay + edu)
        port += net_cf
        res.append({"Age": a, "Growth": growth, "H": h_inc, "Y": y_inc, "SR": ss_inc+rent_inc, "Ex": -(liv+mtg_pay+edu), "Port": port})
    return pd.DataFrame(res)

df = run_model()

# --- RE-BUILT CHART ---
st.subheader("Annual Cash Flow Tracker")
fig = go.Figure()

fig.add_trace(go.Bar(x=df["Age"], y=df["Growth"], name="Investment Growth", marker_color='royalblue'))
fig.add_trace(go.Bar(x=df["Age"], y=df["H"], name="Husband Income", marker_color='lightblue'))
fig.add_trace(go.Bar(x=df["Age"], y=df["Y"], name="Your Income", marker_color='orange'))
fig.add_trace(go.Bar(x=df["Age"], y=df["SR"], name="SS & Rentals", marker_color='green'))
fig.add_trace(go.Bar(x=df["Age"], y=df["Ex"], name="Total Expenses", marker_color='crimson'))

fig.update_layout(
    barmode='relative',
    xaxis_title="Age",
    yaxis_title="Annual Amount ($)",
    template="plotly_white",
    height=500,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig, width='stretch')

# --- PORTFOLIO CHART (Separated for visibility) ---
st.subheader("Total Net Worth Projection")
fig2 = go.Figure()
fig2.add_trace(go.Scatter(x=df["Age"], y=df["Port"], name="Portfolio Value", line=dict(color='black', width=4)))
fig2.update_layout(height=400, template="plotly_white", yaxis_title="Total Wealth ($)")
st.plotly_chart(fig2, width='stretch')

# --- DATA ---
st.write(df)
