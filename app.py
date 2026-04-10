import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Legacy 5.8", layout="wide")

# 1. SIDEBAR
with st.sidebar:
    st.header("Milestones")
    c_a = st.slider("Current Age", 30, 65, 42)
    y_r = st.slider("Your Retire", 45, 75, 55)
    h_r = st.slider("Husband Retire", 45, 75, 58)
    ss_a = st.slider("SS Age", 62, 72, 67)
    d_a = st.slider("End Age", 80, 110, 95)
    st.header("Finance")
    r_rt = st.slider("Avg Return %", 1, 12, 6) / 100
    h_n = st.number_input("Husband Net", 145000)
    y_n = st.number_input("Your Net", 110000)
    ex_w = st.number_input("Work Exp", 210000)
    ex_r = st.number_input("Retire Exp", 150000)

# 2. ASSETS (Moved to expander at bottom)
st.title("🌏 Legacy Master v5.8")

# 3. MATH ENGINE
def calc():
    port, res = 1700000, []
    for a in range(c_a, d_a + 1):
        growth = port * r_rt
        h_inc = h_n if a < h_r else 0
        y_inc = y_n if a < y_r else 0
        ss = 85000 if a >= ss_a else 0
        lv = ex_r if (a >= y_r and a >= h_r) else ex_w
        cf = (h_inc + y_inc + ss + growth) - lv
        port += cf
        res.append({"Age": a, "Growth": growth, "Inc": h_inc+y_inc+ss, "Exp": -lv, "Port": port})
    return pd.DataFrame(res)

df = calc()

# 4. TOP SUMMARY (METRICS)
st.subheader("Executive Summary")
c1, c2, c3 = st.columns(3)
c1.metric("Final Legacy", f"${df.iloc[-1]['Port']:,.0f}")
c2.metric("At Retirement", f"${df[df['Age']==y_r]['Port'].values[0]:,.0f}")
c3.metric("Year 1 CF", f"${df.iloc[0]['Inc']+df.iloc[0]['Growth']+df.iloc[0]['Exp']:,.0f}")

# 5. CHARTS (Simple Plotly)
st.subheader("Projections")
f1 = go.Figure()
f1.add_trace(go.Bar(x=df["Age"], y=df["Inc"], name="Income", marker_color="green"))
f1.add_trace(go.Bar(x=df["Age"], y=df["Growth"], name="Growth", marker_color="blue"))
f1.add_trace(go.Bar(x=df["Age"], y=df["Exp"], name="Expenses", marker_color="red"))
f1.add_trace(go.Scatter(x=
