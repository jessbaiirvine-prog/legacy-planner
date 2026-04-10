import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(page_title="Global Asset & Legacy Planner", layout="wide")

# Custom CSS
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("🌏 Global Asset & Legacy Planner")
st.markdown("Dynamic Milestone Tracking & Multi-Property Portfolio Management")
st.divider()

# --- SIDEBAR: DYNAMIC MILESTONES & GLOBAL VARS ---
with st.sidebar:
    st.header("1. Critical Milestones")
    current_age = st.slider("Your Current Age", 30, 65, 42)
    stop_work_age = st.slider("Age to Stop Working", 45, 75, 55)
    ss_start_age = st.slider("Social Security Start Age", 62, 72, 67)
    death_age = st.slider("End of Simulation (Death)", 80, 110, 95)
    
    st.header("2. Living Expenses")
    # Toggling expenses for different life stages
    exp_pre_retire = st.number_input("Annual Living Expenses (Working)", value=150000, step=5000)
    exp_post_retire = st.number_input("Annual Living Expenses (Retired)", value=120000, step=5000)

    st.header("3. Investment Returns")
    ret_working = st.slider("Returns while Working (%)", 0.0, 15.0, 7.0) / 100
    ret_retired = st.slider("Returns while Retired (%)", 0.0, 10.0, 4.0) / 100

# --- MAIN PANEL: REAL ESTATE PORTFOLIO ---
st.header("🏠 Real Estate Portfolio")
st.info("Input your 6 properties. Primary Residences generate $0 income. Mortgages stop automatically after the term ends.")

re_data = []
cols = st.columns(3)
for i in range(6):
    with cols[i % 3]:
        with st.expander(f"Property {i+1}", expanded=(i < 4)):
            is_primary = st.checkbox("Primary Residence?", value=(i==0), key=f"pri_{i}")
            annual_cf = 0 if is_primary else st.number_input("Annual Net Cash Flow ($)", value=7800 if i < 4 else 0, key=f"cf_{i}")
            m_start_age = st.number_input("Mortgage Start (Your Age)", value=35, key=f"start_{i}")
            m_term = st.number_input("Mortgage Term (Years)", value=30, key=f"term_{i}")
            m_payment = st.number_input("Annual P&I Payment ($)", value=15000 if i < 4 else 0, key=f"pay_{i}")
            
            re_data.append({
                "income": annual_cf,
                "start": m_start_age,
                "end": m_start_age + m_term,
                "payment": m_payment
            })

# --- MATH ENGINE ---
def run_asset_model():
    portfolio = 1700000 # Starting liquid
    data = []
    
    for a in range(current_age, death_age + 1):
        # 1. Growth & Returns
        current_ret = ret_working if a < stop_work_age else ret_retired
        growth = portfolio * current_ret
        
        # 2. Work Income
        work_inc = (145000 + 110000) if a < stop_work_age else 0 # Combined net
        ss_inc = 85000 if a >= ss_start_age else 0
        
        # 3. Real Estate Logic
        total_re_income = 0
        total_re_mortgage = 0
        milestones = []
        
        for prop in re_data:
            total_re_income += prop["income"]
            if prop["start"] <= a < prop["end"]:
                total_re_mortgage += prop["payment"]
            if a == prop["end"]:
                milestones.append(f"RE Paid Off")
        
        # 4. Expenses
        current_living = exp_pre_retire if a < stop_work_age else exp_post_retire
        
        # 5. Milestone Check
        if a == stop_work_age: milestones.append("Stop Working")
        if a == ss_start_age: milestones.append("Social Security")
        
        # Update Portfolio
        net_cash_flow = (work_inc + ss_inc + total_re_income + growth) - (current_living + total_re_mortgage)
        portfolio += net_cash_flow
        
        data.append({
            "Age": a,
            "Portfolio Growth": growth,
            "Salaries": work_inc,
            "Social Security": ss_inc,
            "Rental Income": total_re_income,
            "Living Expenses": -current_living,
            "Mortgage Payments": -total_re_mortgage,
            "Total Portfolio": portfolio,
            "Milestone": ", ".join(milestones)
        })
    return pd.DataFrame(data)

df = run_asset_model()

# --- VISUALIZATION ---
# 1. Cash Flow Bar Chart
st.subheader("Cash Flow & Milestone Breakdown")
fig = go.Figure()

# Income
fig.add_trace(go.Bar(name="Portfolio Growth", x=df["Age"], y=df["Portfolio Growth"], marker_color='#1f77b4'))
fig.add_trace(go.Bar(name="Salaries", x=df["Age"], y=df["Salaries"], marker_color='#aec7e8'))
fig.add_trace(go.Bar(name="Rental Income", x=df["Age"], y=df["Rental Income"], marker_color='#2ca02c'))
fig.add_trace(go.Bar(name="Social Security", x=df["Age"], y=df["Social Security"], marker_color='#98df8a'))

# Expenses
fig.add_trace(go.Bar(name="Living Expenses", x=df["Age"], y=df["Living Expenses"], marker_color='#d62728'))
fig.add_trace(go.Bar(name="Mortgage Payments", x=df["Age"], y=df["Mortgage Payments"], marker_color='#ff9896'))

# Add Milestones as Text Labels
for i, row in df.iterrows():
    if row["Milestone"]:
        fig.add_annotation(x=row["Age"], y=row["Total Portfolio"], text=row["Milestone"], 
                           showarrow=True, arrowhead=1, ax=0, ay=-40)

fig.update_layout(barmode='relative', template="plotly_white", height=600, legend=dict(orientation="h", y=1.1))
st.plotly_chart(fig, use_container_width=True)

# 2. Portfolio Line
st.subheader("Total Liquid Net Worth Over Time")
st.line_chart(df.set_index("Age")["Total Portfolio"])

with st.expander("Ledger Detail"):
    st.write(df)
