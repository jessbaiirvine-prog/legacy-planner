import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(page_title="Global Legacy Master v5.2", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("🌏 Global Legacy Master v5.2")
st.markdown("Fixed Variable Errors + Updated Streamlit Syntax")

# --- SIDEBAR: MULTI-STAGE CONTROLS ---
with st.sidebar:
    st.header("1. Critical Milestones")
    current_age = st.slider("Your Current Age", 30, 65, 42)
    your_retire_age = st.slider("Age YOU Stop Working", 45, 75, 55)
    husband_retire_age = st.slider("Age HUSBAND Stops Working", 45, 75, 58)
    ss_start_age = st.slider("Social Security Start Age", 62, 72, 67)
    death_age = st.slider("Simulation End (Death)", 80, 110, 95)
    
    st.header("2. Return Schedule")
    ret_40s = st.slider("Returns in 40s (%)", 0.0, 15.0, 7.0) / 100
    ret_50s = st.slider("Returns in 50s (%)", 0.0, 15.0, 5.0) / 100
    ret_60plus = st.slider("Returns 60+ (%)", 0.0, 10.0, 4.0) / 100

    st.header("3. Education Logic")
    num_kids = st.number_input("Number of Children", 0, 5, 2)
    tuition = st.number_input("Annual Tuition ($)", value=50000)
    kid_starts = [st.number_input(f"Child {i+1} Start Age", 40, 75, 52+(i*6), key=f"k{i}") for i in range(num_kids)]

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
        # 1. Select Return Rate
        if a < 50: r = ret_40s
        elif a < 60: r = ret_50s
        else: r = ret_60plus
        
        # 2. Growth
        growth = portfolio * r
        
        # 3. Income Logic
        h_inc = husband_net_ann if a < husband_retire_age else 0
        y_inc = your_net_ann if a < your_retire_age else 0
        ss_inc = 85000 if a >= ss_start_age else 0
        
        # 4. Real Estate Logic
        re_inc, re_mtg = 0, 0
        re_milestones = []
        for prop in re_data:
            re_inc += prop["income"]
            if prop["start"] <= a < prop["end"]:
                re_mtg += prop["pay"]
            if a == prop["end"]: 
                re_milestones.append("RE Paid Off")
            
        # 5. Education Logic
        edu_cost = sum([tuition for start in kid_starts if start <= a < (start + 4)])
        
        # 6. Expenses Logic
        # Retired level starts once BOTH stop working
        is_retired = (a >= your_retire_age) and (a >= husband_retire_age)
        living = exp_retired if is_retired else exp_working
        
        # 7. Update Portfolio
        net_cf = (h_inc + y_inc + ss_inc + re_inc + growth) - (living + re_mtg + edu_cost)
        portfolio += net_cf
        
        data.append({
            "Age": a, 
            "Investment Growth": growth, 
            "Husband Income": h_inc, 
            "Your Income": y_inc, 
            "Social Security": ss_inc, 
            "Rental Income": re_inc, 
            "Living Expenses": -living, 
            "Mortgage Payments": -re_mtg, 
            "Education": -edu_cost, 
            "Portfolio": portfolio, 
            "Tags": ", ".join(re_milestones)
        })
    return pd.DataFrame(data)

df = run_master_model()

# --- VISUALIZATION ---
st.subheader("Interactive Cash Flow & Legacy Tracker")
st.info("Bars: Annual Flow (Left Axis). Line: Total Wealth (Right Axis).")

fig = go.Figure()

# Income & Expenses
fig.add_trace(go.Bar(name="Growth", x=df["Age"], y=df["Investment Growth"], marker_color='#1f77b4'))
fig.add_trace(go.Bar(name="Husband", x=df["Age"], y=df["Husband Income"], marker_color='#aec7e8'))
fig.add_trace(go.Bar(name="You", x=df["Age"], y=df["Your Income"], marker_color='#ff7f0e'))
fig.add_trace(go.Bar(name="SS/Rentals", x=df["Age"], y=df["Social Security"]+df["Rental Income"], marker_color='#2ca02c'))
fig.add_trace(go.Bar(name="Expenses", x=df["Age"], y=df["Living Expenses"]+df["Mortgage Payments"]+df["Education"], marker_color='#d62728'))

# Wealth Line (Secondary Axis)
fig.add_trace(go.Scatter(name="Total Net Worth", x=df["Age"], y=df["Portfolio"], 
                         yaxis="y2", line=dict(color='black', width=4)))

fig.update_layout(
    barmode='relative',
    yaxis=dict(title="Annual Cash Flow ($)", side="left", zeroline=True),
    yaxis2=dict(title="Total Net Worth ($)", side="right", overlaying="y", showgrid=False),
    template="plotly_white", 
    height=650,
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig, width='stretch')

# --- METRICS ---
m1, m2, m3 = st.columns(3)
m1.metric("Final Estate", f"${df.iloc[-1]['Portfolio']:,.0f}")
m2.metric("Portfolio @ Retirement", f"${df[df['Age']==your_retire_age]['Portfolio'].values[0]:,.0f}")
m3.metric("Year 1 Total Income", f"${df.iloc[0]['Investment Growth'] + df.iloc[0]['Husband Income'] + df.iloc[0]['Your Income
