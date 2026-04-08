import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(page_title="Global Legacy Planner", layout="wide")

# --- CUSTOM CSS FOR MCKINSEY AESTHETIC ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("🌏 Global Legacy & Retirement Planner")
st.markdown("### Strategic Wealth Modeling for Cross-Border Families")
st.divider()

# --- SIDEBAR INPUTS ---
with st.sidebar:
    st.header("1. Current Profile")
    age = st.slider("Current Age", 30, 65, 42)
    liquid_assets = st.number_input("Current Portfolio ($)", value=1700000, step=50000)
    
    st.header("2. The 'Pivot' (Transition)")
    move_age = st.slider("Age of Move to China", 45, 70, 55)
    re_equity = st.number_input("Real Estate Liquidation Net ($)", value=1450000, step=50000)
    
    st.header("3. Annual Cash Flow")
    husband_net = st.number_input("Husband Annual Net Income ($)", value=145000)
    lu_net_target = st.number_input("Target Partner Net Income ($)", value=110000)
    rentals_net = st.number_input("Rental Net Income ($)", value=15600)
    
    st.header("4. Expenses & Goals")
    ca_mortgage = st.number_input("Current Mortgage P&I ($/yr)", value=60000)
    ca_living = st.number_input("Current Living Expenses ($/yr)", value=150000)
    china_living = st.number_input("Post-Move Living Budget ($/yr)", value=150000)
    college_cost = st.number_input("Annual College Cost (Staggered)", value=50000)

# --- MATH ENGINE ---
def calculate_wealth():
    portfolio = liquid_assets
    real_growth = 0.05  # 5% real return
    ss_benefit = 85000
    data = []
    
    for a in range(age, 91):
        start_bal = portfolio
        growth = portfolio * real_growth
        portfolio += growth
        
        # Operational Cash Flow
        if a < move_age:
            income = husband_net + lu_net_target + rentals_net
            expenses = ca_mortgage + ca_living
            portfolio += (income - expenses)
        else:
            # Retirement Phase
            portfolio -= china_living
            if a >= 67:
                portfolio += ss_benefit
                
        # Education Milestones (Assumes kids are 8 and 2 at age 42)
        if (age + 10 <= a <= age + 13) or (age + 16 <= a <= age + 19):
            portfolio -= college_cost
            
        # Liquidation Event
        if a == move_age:
            portfolio += re_equity
            
        data.append({"Age": a, "Portfolio": round(portfolio)})
    return pd.DataFrame(data)

df = calculate_wealth()

# --- DASHBOARD LAYOUT ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Portfolio at Move", f"${df[df['Age']==move_age]['Portfolio'].values[0]:,.0f}")
with col2:
    st.metric("Final Estate (Age 90)", f"${df.iloc[-1]['Portfolio']:,.0f}")
with col3:
    st.metric("Safe Annual Withdrawal", f"${df[df['Age']==move_age]['Portfolio'].values[0] * 0.04:,.0f}")

# --- CHARTING ---
fig = go.Figure()
fig.add_trace(go.Scatter(x=df['Age'], y=df['Portfolio'], mode='lines', 
                         line=dict(color='#1f77b4', width=4), fill='tozeroy'))
fig.update_layout(title="Wealth Projection (Inflation Adjusted)", 
                  xaxis_title="Age", yaxis_title="Portfolio Value ($)",
                  template="plotly_white")
st.plotly_chart(fig, use_container_width=True)

# --- DATA TABLE ---
with st.expander("View Year-by-Year Ledger"):
    st.dataframe(df, use_container_width=True)
