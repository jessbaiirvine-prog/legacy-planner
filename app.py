import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(
    layout="wide", 
    page_title="Legacy 7.3"
)

# --- UI STYLING ---
st.markdown(
    "<style>"
    "div[data-testid='metric-container'] {"
    "background-color: #1e1e2e;"
    "border: 1px solid #2b2b40;"
    "padding: 15px;"
    "border-radius: 8px;"
    "}"
    "</style>", 
    unsafe_allow_html=True
)

# --- 1. SETTINGS ---
sb = st.sidebar
sb.header("Timeline")
c_age = sb.slider("Current Age", 30, 65, 42)
y_ret = sb.slider("Your Retire", 45, 75, 55)
h_ret = sb.slider("Hus Retire", 45, 75, 58)
d_age = sb.slider("End Age", 80, 110, 95)

sb.header("Portfolio Breakdown ($)")
v_tax = sb.number_input("Taxable Cash", 200000)
v_def = sb.number_input("Deferred 401k", 1200000)
v_rot = sb.number_input("Roth", 300000)

sb.header("Inflows & Outflows")
rate = sb.slider("Return %", 1, 10, 6) / 100
h_net = sb.number_input("Hus Net", 145000)
y_net = sb.number_input("Your Net", 110000)
e_wrk = sb.number_input("Work Exp", 210000)
e_ret = sb.number_input("Retire Exp", 150000)

sb.header("Education")
n_kid = sb.number_input("Kids", 0, 5, 2)
tui = sb.number_input("Tuition/Yr", 50000)
k_sts = []
for i in range(int(n_kid)):
    k_sts.append(
        sb.number_input(
            f"K{i+1} Start", 40, 75, 52+(i*6)
        )
    )

st.title("✨ Legacy Master v7.3")

# --- 2. REAL ESTATE EQUITY ---
props = []
st.subheader("🏠 Real Estate Asset Portfolio")
cols = st.columns(3)
for i in range(3):
    with cols[i]:
        exp = st.expander(
            f"Property {i+1}", expanded=(i==0)
        )
        with exp:
            val = st.number_input(
                "Value", 950000, key=f"v{i}"
            )
            debt = st.number_input(
                "Debt", 600000, key=f"b{i}"
            )
            appr = st.slider(
                "Appr %", 1, 10, 3, key=f"a{i}"
            ) / 100
            pay = st.number_input(
                "Paydown", 12000, key=f"p{i}"
            )
            props.append({
                "v": val, 
                "d": debt, 
                "g": appr, 
                "p": pay
            })

# --- 3. MATH ENGINE (VERTICAL REWRITE) ---
sim_data = []
t_tax = v_tax
t_def = v_def
t_rot = v_rot

for age in range(c_age, d_age + 1):
    
    # 3a. Portfolio Growth
    t_tax += (t_tax * rate)
    t_def += (t_def * rate)
    t_rot += (t_rot * rate)
    
    # 3b. Income
    inc_h = 0
    if age < h_ret:
        inc_h = h_net
        
    inc_y = 0
    if age < y_ret:
        inc_y = y_net
        
    inc_s = 0
    if age >= 67:
        inc_s = 85000
        
    total_inc = inc_h + inc_y + inc_s
    
    # 3c. Living Expenses
    exp_l = e_wrk
    if age >= y_ret:
        if age >= h_ret:
            exp_l = e_ret
            
    # 3d. Education Expenses
    exp_e = 0
    for s in k_sts:
        if age >= s:
            if age < s + 4:
                exp_e += tui
                
    total_exp = exp_l + exp_e
    
    # 3e. Cashflow Application
    net_cf = total_inc - total_exp
    t_tax += net_cf
    
    # 3f. Real Estate Processing
    p_val = 0
    p_dbt = 0
    
    for p in props:
        growth = p["v"] * p["g"]
        p["v"] += growth
        
        p["d"] -= p["p"]
        if p["d"] < 0:
            p["d"] = 0
            
        p_val += p["v"]
        p_dbt += p["d"]
        
    p_eq = p_val - p_dbt
    nw = t_tax + t_def + t_rot + p_eq
    
    # 3g. Save Row
    sim_data.append({
        "Age": age, 
        "Taxable": t_tax, 
        "Deferred": t_def, 
        "Roth": t_rot,
        "RE_Equity": p_eq, 
        "NetWorth": nw
    })

df = pd.DataFrame(sim_data)

# --- 4. OUTPUTS ---
st.divider()
if not df.empty:
    m1, m2, m3, m4 = st.columns(4)
    
    nw_now = df.iloc[0]['NetWorth']
    m1.metric("Current NW", f"${nw_now:,.0f}")
    
    ret_df = df[df['Age'] == y_ret]
    if not ret_df.empty:
        r_nw = ret_df['NetWorth'].values[0]
        m2.metric("NW @ Retire", f"${r_nw:,.0f}")
    else:
        m2.metric("NW @ Retire", "$0")
        
    nw_end = df.iloc[-1]['NetWorth']
    m3.metric("Final Estate", f"${nw_end:,.0f}")
    
    tot_edu = n_kid * tui * 4
    m4.metric("Total Tuition", f"${tot_edu:,.0f}")

    # Area Chart
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df["Age"], y=df["Taxable"], 
        name="Taxable", stackgroup='1', 
        fillcolor='#3b82f6', line=dict(width=0)
    ))
    
    fig.add_trace(go.Scatter(
        x=df["Age"], y=df["Roth"], 
        name="Roth", stackgroup='1', 
        fillcolor='#10b981', line=dict(width=0)
    ))
    
    fig.add_trace(go.Scatter(
        x=df["Age"], y=df["Deferred"], 
        name="Deferred", stackgroup='1', 
        fillcolor='#8b5cf6', line=dict(width=0)
    ))
    
    fig.add_trace(go.Scatter(
        x=df["Age"], y=df["RE_Equity"], 
        name="RE Equity", stackgroup='1', 
        fillcolor='#f59e0b', line=dict(width=0)
    ))
    
    fig.update_layout(
        template="plotly_dark", 
        hovermode="x unified", 
        height=500, 
        margin=dict(t=20, b=0), 
        legend=dict(
            orientation="h", y=1.1
        )
    )
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Raw Ledger"):
        st.dataframe(df)
