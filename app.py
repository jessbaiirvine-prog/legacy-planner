import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(page_title="Global Legacy Master v5", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("🌏 Global Legacy Master v5")
st.markdown("Restored V3 Logic + Split Retirement + Fixed Scaling")

# --- SIDEBAR: MULTI-STAGE CONTROLS ---
with st.sidebar:
    st.header("1. Critical Milestones")
    current_age = st.slider("Your Current Age", 30, 65, 42)
    your_retire_age = st.slider("Age YOU Stop Working", 45, 75, 55)
    husband_retire_age = st.slider("Age HUSBAND Stops Working", 45, 75, 58)
    ss_start_age = st.slider("Social Security Start Age", 62, 72, 67)
    death_age = st.slider("Simulation End (Death)", 80, 110, 95)
    
    st.header("2. Return Schedule (Restored)")
    ret_40s = st.slider("Returns in 40s (%)", 0.0, 15.0, 7.0) / 100
    ret_50s = st.slider("Returns in 50s (%)", 0.0, 15.0, 5.0) / 100
    ret_60plus = st.slider("Returns 60+ (%)", 0.0, 10.0, 4.0) / 100

    st.header("3. Education Logic (Restored)")
    num_kids = st.number_input("Number of Children", 0, 5, 2)
    tuition = st.number_input("Annual Tuition ($)", value=50000)
    kid_starts = [st.number_input(f"Child {i+1} Start Age", 45, 70, 52+(i*6), key=f"k{i}") for i in range(num_kids)]

    st.header("4. Direct Income Inputs")
    husband_net_ann = st.number_input("Husband Annual Net ($)", value=145000)
    your_net_ann = st.number_input("Your Annual Net ($)", value=110000)
    
    st.header("5. Living Expenses")
    exp_working = st.number_input("Expenses while Working ($)", value=210000)
    exp_retired = st.number_input("Expenses in Retirement ($)", value=150000)

# --- REAL ESTATE ENGINE ---
st.header("🏠 Real Estate Portfolio")
re_data = []
re_cols = st.columns(3)
for i in range(6):
    with re_cols[i % 3]:
        with st.expander(f"Property {i+1}", expanded=(i < 4)):
            is_pri = st.checkbox("Primary?", value=(i==0), key=f"p{i}")
            cf = 0 if is_pri else st.number_input("Annual Cashflow", value=7800 if i<4 else 0, key=f"c{i}")
            m_start = st.number_input("Mtg Start Age", value=35, key=f"s{i}")
            m_term = st.number_input("Term (Yrs)", value=30, key=f"t{i}")
            m_pay = st.number_input("Mtg Payment", value=15000 if i<4 else 0, key=f"m{i}")
            re_data.append({"income": cf, "start": m_start, "end": m_start+m_term, "pay": m_pay})

# --- MATH ENGINE ---
def run_master_model():
    portfolio = 1700000
    data = []
    
    for a in range(current_age, death_age + 1):
        # 1. Returns
        if a < 50: r = ret_40s
        elif a < 60: r = ret_50s
        else: r = ret_60plus
        growth = portfolio * r
        
        # 2. Income Logic
        h_inc = husband_net_ann if a < husband_retire_age else 0
        y_inc = your_net_ann if a < your_retire_age else 0
        ss_inc = 85000 if a >= ss_start_age else 0
        
        # 3. Real Estate
        re_inc, re_mtg = 0, 0
        re_milestones = []
        for prop in re_data:
            re_inc += prop["income"]
            if prop["start"] <= a < prop["end"]:
                re_mtg += prop["pay"]
            if a == prop["end"]: re_milestones.append("RE Paid")
            
        # 4. Education
        edu_cost = sum([tuition for start in kid_starts if start <= a < start+4])
        
        # 5. Expenses
        is_retired = (a >= your_retire_age) and (a >= husband_retire_age)
        living = exp_retired if is_retired else exp_working
        
        # Calculate
        net_cf = (h_inc + y_inc + ss_inc + re_inc + growth) - (living + re_mtg + edu_cost)
        portfolio += net_cash_flow = net_cf
        
        data.append({
            "Age": a, "Growth": growth, "Husband": h_inc, "You": y_inc, 
            "SS": ss_inc, "Rentals": re_inc, "Living": -living, "Mtg": -re_mtg, 
            "Edu": -edu_cost, "Portfolio": portfolio, "Tags": ", ".join(re_milestones)
        })
    return pd.DataFrame(data)

df = run_master_model()

# --- RE-OPTIMIZED VISUALIZATION ---
st.subheader("Interactive Cash Flow & Legacy Tracker")

fig = go.Figure()

# Add Income Bars
fig.add_trace(go.Bar(name="Growth", x=df["Age"], y=df["Growth"], marker_color='#1f77b4'))
fig.add_trace(go.Bar(name="Husband", x=df["Age"], y=df["Husband"], marker_color='#aec7e8'))
fig.add_trace(go.Bar(name="You", x=df["Age"], y=df["You"], marker_color='#ff7f0e'))
fig.add_trace(go.Bar(name="SS/Rentals", x=df["Age"], y=df["SS"]+df["Rentals"], marker_color='#2ca02c'))

# Add Expense Bars
fig.add_trace(go.Bar(name="Expenses", x=df["Age"], y=df["Living"]+df["Mtg"]+df["Edu"], marker_color='#d62728'))

# Add Portfolio Line on SECONDARY Y-AXIS to fix scaling
fig.add_trace(go.Scatter(name="Total Portfolio", x=df["Age"], y=df["Portfolio"], 
                         yaxis="y2", line=dict(color='black', width=3)))

fig.update_layout(
    barmode='relative',
    yaxis=dict(title="Annual Cash Flow ($)", side="left"),
    yaxis2=dict(title="Total Net Worth ($)", side="right", overlaying="y", showgrid=False),
    template="plotly_white", height=650,
    legend=dict(orientation="h", y=1.1)
)

st.plotly_chart(fig, use_container_width=True)

with st.expander("Ledger Data"):
    st.write(df)
