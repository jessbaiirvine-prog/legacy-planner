import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(page_title="Global Legacy Planner v3", layout="wide")

# Custom CSS for a professional look
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("🌏 Global Legacy Planner: Strategic Cash Flow & Education")
st.markdown("Detailed year-by-year breakdown of income, outflows, and long-term wealth trajectory.")
st.divider()

# --- SIDEBAR: INPUTS ---
with st.sidebar:
    st.header("1. Return Schedule")
    st.info("Set real return rates (adjusted for inflation) for each life stage.")
    ret_40s = st.slider("Returns in 40s (%)", 0.0, 15.0, 7.0) / 100
    ret_50s = st.slider("Returns in 50s (%)", 0.0, 15.0, 5.0) / 100
    ret_60plus = st.slider("Returns 60+ (%)", 0.0, 10.0, 4.0) / 100

    st.header("2. Asset Transition")
    current_age = st.slider("Current Age", 30, 65, 42)
    move_age = st.slider("Move Age", 45, 70, 55)
    liquid_assets = st.number_input("Starting Portfolio ($)", value=1700000, step=50000)
    re_equity = st.number_input("Real Estate Equity ($)", value=1450000, step=50000)

    st.header("3. Education Planning")
    num_kids = st.number_input("Number of Children", min_value=0, max_value=5, value=2)
    tuition_per_year = st.number_input("Annual Tuition per Child ($)", value=50000, step=5000)
    
    kid_starts = []
    for i in range(int(num_kids)):
        # Defaulting based on typical 8yr and 2yr old scenario
        default_start = 52 if i == 0 else 58
        start_age = st.number_input(f"Child {i+1} College Start (At Your Age)", value=default_start, key=f"kid_{i}")
        kid_starts.append(start_age)

    st.header("4. Monthly Income (Net)")
    husband_income = st.number_input("Husband Monthly Net ($)", value=12000)
    partner_income = st.number_input("Your Target Monthly Net ($)", value=9200)
    rental_income = st.number_input("Rental Monthly Net ($)", value=1300)

# --- MATH ENGINE ---
def run_strategic_model():
    portfolio = liquid_assets
    data = []
    
    for a in range(current_age, 91):
        # 1. Determine Return Rate
        if a < 50: current_ret = ret_40s
        elif a < 60: current_ret = ret_50s
        else: current_ret = ret_60plus
        
        growth = portfolio * current_ret
        
        # 2. Income Logic
        if a < move_age:
            inc_h, inc_p, inc_r = husband_income*12, partner_income*12, rental_income*12
            inc_ss, inc_re_sale = 0, 0
        else:
            inc_h, inc_p, inc_r = 0, 0, 0
            inc_ss = 85000 if a >= 67 else 0
            inc_re_sale = re_equity if a == move_age else 0
        
        # 3. Expense Logic
        exp_living = 150000
        exp_mortgage = 60000 if a < move_age else 0
            
        # 4. Multi-Child College Logic
        exp_college = 0
        for start_year in kid_starts:
            if start_year <= a < (start_year + 4): # 4 years of college
                exp_college += tuition_per_year
        
        # 5. Portfolio Update
        total_inc = inc_h + inc_p + inc_r + inc_ss + inc_re_sale + growth
        total_exp = exp_living + exp_mortgage + exp_college
        portfolio += (total_inc - total_exp)
        
        data.append({
            "Age": a,
            "Investment Growth": growth,
            "Husband Income": inc_h,
            "Your Income": inc_p,
            "Rentals": inc_r,
            "Social Security": inc_ss,
            "RE Liquidation": inc_re_sale,
            "Living Expenses": -exp_living,
            "Mortgage": -exp_mortgage,
            "College": -exp_college,
            "Total Portfolio": portfolio
        })
    return pd.DataFrame(data)

df = run_strategic_model()

# --- TOP LEVEL METRICS ---
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Total Legacy (Age 90)", f"${df.iloc[-1]['Total Portfolio']:,.0f}")
with c2:
    peak_college = abs(df["College"].min())
    st.metric("Peak Tuition Burn (Yearly)", f"${peak_college:,.0f}")
with c3:
    st.metric("Net Worth at Move", f"${df[df['Age']==move_age]['Total Portfolio'].values[0]:,.0f}")

st.divider()

# --- STACKED BAR CHART ---
st.subheader("Annual Cash Flow Breakdown")
fig = go.Figure()

# Income Stacks (Positive)
income_cols = ["Investment Growth", "Husband Income", "Your Income", "Rentals", "Social Security", "RE Liquidation"]
colors_inc = ['#1f77b4', '#aec7e8', '#ff7f0e', '#ffbb78', '#2ca02c', '#98df8a']

for i, col in enumerate(income_cols):
    fig.add_trace(go.Bar(name=col, x=df["Age"], y=df[col], marker_color=colors_inc[i]))

# Expense Stacks (Negative)
expense_cols = ["Living Expenses", "Mortgage", "College"]
colors_exp = ['#d62728', '#ff9896', '#9467bd']

for i, col in enumerate(expense_cols):
    fig.add_trace(go.Bar(name=col, x=df["Age"], y=df[col], marker_color=colors_exp[i]))

fig.update_layout(
    barmode='relative', 
    xaxis_title="Age", 
    yaxis_title="Annual Value (Today's USD)",
    template="plotly_white", 
    height=600, 
    margin=dict(t=20),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)
st.plotly_chart(fig, use_container_width=True)

# --- PORTFOLIO LINE CHART ---
st.subheader("Cumulative Wealth Trajectory")
st.line_chart(df.set_index("Age")["Total Portfolio"], use_container_width=True)

# --- DATA TABLE ---
with st.expander("View Year-by-Year Ledger Data"):
    st.dataframe(df, use_container_width=True)
