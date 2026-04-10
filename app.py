import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Legacy 7.0")

# --- PROJECTIONLAB STYLING ---
st.markdown("""
<style>
div[data-testid="metric-container"] {
    background-color: #1e1e2e;
    border: 1px solid #2b2b40;
    padding: 15px;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# --- 1. SETTINGS ---
sb = st.sidebar
sb.header("Timeline")
ca = sb.slider("Current Age", 30, 65, 42)
yr = sb.slider("Your Retire", 45, 75, 55)
hr = sb.slider("Hus Retire", 45, 75, 58)
da = sb.slider("End Age", 80, 110, 95)

sb.header("Portfolio Breakdown ($)")
v_tx = sb.number_input("Taxable (Cash/Broker)", 200000)
v_td = sb.number_input("Tax-Deferred (401k)", 1200000)
v_ro = sb.number_input("Tax-Free (Roth)", 300000)

sb.header("Inflows & Outflows")
rt = sb.slider("Market Return %", 1, 10, 6) / 100
hn = sb.number_input("Husband Net", 145000)
yn = sb.number_input("Your Net", 110000)
ew = sb.number_input("Work Exp", 210000)
er = sb.number_input("Retire Exp", 150000)

st.title("✨ Legacy Master v7.0")
st.markdown("### Advanced Equity & Tax Projection")

# --- 2. REAL ESTATE EQUITY MODULE ---
re = []
cl = st.columns(3)
for i in range(3): # Reduced to 3 for clean UI, add more as needed
    with cl[i]:
        with st.expander(f"Property {i+1} Equity", i==0):
            pp = st.number_input("Purchase Price", 800000, key=f"p{i}")
            pa = st.number_input("Purchase Age", 35, key=f"a{i}")
            cv = st.number_input("Current Value", 950000, key=f"v{i}")
            mb = st.number_input("Mtg Balance", 600000, key=f"b{i}")
            ag = st.slider("Appreciation %", 1, 10, 3, key=f"g{i}")/100
            
            # Simple annual principal paydown estimation
            pd = st.number_input("Annual Principal Paydown", 12000, key=f"d{i}")
            
            re.append({
                "val": cv, "debt": mb, "appr": ag, "paydown": pd
            })

# --- 3. MATH ENGINE ---
res = []
tx, td, ro = v_tx, v_td, v_ro

for a in range(ca, da + 1):
    # Grow Portfolio (Simplified uniform growth)
    tx += (tx * rt)
    td += (td * rt)
    ro += (ro * rt)
    
    # Income & Living
    hi = hn if a < hr else 0
    yi = yn if a < yr else 0
    ss = 85000 if a >= 67 else 0
    lv = er if (a >= yr and a >= hr) else ew
    
    # Net Cashflow goes to Taxable
    net_cf = (hi + yi + ss) - lv
    tx += net_cf
    
    # Grow Real Estate & Pay Down Debt
    re_val = 0
    re_dbt = 0
    for p in re:
        p["val"] += (p["val"] * p["appr"])
        p["debt"] = max(0, p["debt"] - p["paydown"])
        re_val += p["val"]
        re_dbt += p["debt"]
        
    re_eq = re_val - re_dbt
    total_nw = tx + td + ro + re_eq
    
    res.append({
        "Age": a, "Taxable": tx, "Deferred": td, "Roth": ro,
        "RE_Value": re_val, "RE_Debt": re_dbt, "RE_Equity": re_eq,
        "NetWorth": total_nw
    })

df = pd.DataFrame(res)

# --- 4. PROJECTIONLAB STYLE OUTPUTS ---
st.divider()
m1, m2, m3, m4 = st.columns(4)
m1.metric("Current Net Worth", f"${df.iloc[0]['NetWorth']:,.0f}")
m2.metric("NW at Retirement", f"${df[df['Age']==yr]['NetWorth'].values[0]:,.0f}")
m3.metric("Final Estate Value", f"${df.iloc[-1]['NetWorth']:,.0f}")
m4.metric("Current RE Equity", f"${df.iloc[0]['RE_Equity']:,.0f}")

st.subheader("Net Worth Composition Over Time")

# Stacked Area Chart for smooth ProjectionLab aesthetic
f = go.Figure()
f.add_trace(go.Scatter(
    x=df["Age"], y=df["Taxable"], name="Taxable/Cash", 
    stackgroup='one', fillcolor='#3b82f6', line=dict(width=0)
))
f.add_trace(go.Scatter(
    x=df["Age"], y=df["Roth"], name="Roth (Tax-Free)", 
    stackgroup='one', fillcolor='#10b981', line=dict(width=0)
))
f.add_trace(go.Scatter(
    x=df["Age"], y=df["Deferred"], name="Tax-Deferred", 
    stackgroup='one', fillcolor='#8b5cf6', line=dict(width=0)
))
f.add_trace(go.Scatter(
    x=df["Age"], y=df["RE_Equity"], name="Real Estate Equity", 
    stackgroup='one', fillcolor='#f59e0b', line=dict(width=0)
))

f.update_layout(
    template="plotly_dark", # Forces the sleek dark mode
    hovermode="x unified",
    height=500,
    margin=dict(t=20, b=0),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)
st.plotly_chart(f, use_container_width=True)

with st.expander("View Raw Ledger"):
    st.dataframe(df)
