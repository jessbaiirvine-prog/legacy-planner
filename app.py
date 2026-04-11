import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import json

st.set_page_config(layout="wide", page_title="Legacy Master 15.0")

# --- 1. SIDEBAR: PROFESSIONAL ASSUMPTIONS ---
sb = st.sidebar
sb.title("⚙️ Strategic Planning")

with sb.expander("💰 Tax & Liquid Assets", expanded=True):
    v_c = st.number_input("Starting Cash/Brokerage", value=200000.0)
    v_d = st.number_input("401k (Pre-Tax)", value=1200000.0)
    v_r = st.number_input("Roth/HSA (Tax-Free)", value=500000.0)
    
    st.markdown("---")
    tax_work = st.slider("Income Tax (Working) %", 10, 50, 30) / 100
    tax_ret = st.slider("Income Tax (Retire) %", 0, 40, 20) / 100
    cap_gains = st.slider("Capital Gains Tax %", 0, 30, 20) / 100
    roi = st.slider("Market ROI %", 0.0, 12.0, 7.0) / 100

with sb.expander("🏠 Real Estate & Liquidation", expanded=False):
    liq_strategy = st.radio("Retirement Strategy", ["Hold/1031 Exchange", "Sell & Move to Brokerage"])
    liq_age = st.number_input("Liquidation Age", 45, 80, 55)
    
    n_prop = st.number_input("Property Count", 1, 5, 1)
    p_list = []
    # Standard Operating Assumptions
    p_tax_rate = 0.012  # 1.2% Property Tax
    p_maint = 0.01     # 1% Maint/Ins
    p_mgmt = 0.08      # 8% Management Fee
    
    for i in range(n_prop):
        st.markdown(f"**Property {i+1}**")
        val = st.number_input(f"Current Value P{i+1}", 1700000.0, key=f"val{i}")
        basis = st.number_input(f"Cost Basis (for Tax) P{i+1}", 1000000.0, key=f"basis{i}")
        loan = st.number_input(f"Current Loan P{i+1}", 800000.0, key=f"loan{i}")
        rent = st.number_input(f"Monthly Rent P{i+1}", 6500.0, key=f"rent{i}")
        rate = st.number_input(f"Interest Rate % P{i+1}", 4.5, key=f"rate{i}") / 100
        term = st.number_input(f"Years Remaining P{i+1}", 20, key=f"term{i}")
        appr = st.number_input(f"Appreciation % P{i+1}", 3.0, key=f"appr{i}") / 100
        
        # Amortization calc
        p_mtg = 0
        if loan > 0:
            mi, mt = rate/12, term*12
            p_mtg = loan * (mi * (1+mi)**mt) / ((1+mi)**mt - 1)
        
        p_list.append({
            "v": val, "b": basis, "l": loan, "m": p_mtg * 12, 
            "r": rent * 12, "a": appr, "term": term
        })

with sb.expander("👩‍💼 Household Timeline", expanded=False):
    ca, ea = st.number_input("Current Age", 42), st.number_input("End Age", 95)
    hp, hr = st.number_input("Husband Salary", 145000.0), st.number_input("Husband Retire Age", 58)
    yp, yr = st.number_input("Your Salary", 110000.0), st.number_input("Your Retire Age", 55)
    ew, er = st.number_input("Spend (Work)", 150000.0), st.number_input("Spend (Retire)", 120000.0)

# --- 2. THE ENGINE ---
def run_simulation():
    cc, cd, cr = v_c, v_d, v_r
    current_properties = [p.copy() for p in p_list]
    history = []
    
    for age in range(ca, ea + 1):
        yr_idx = 2026 + (age - ca)
        is_liquidated = (age >= liq_age)
        
        # 1. Real Estate Phase
        re_equity, re_cash_flow = 0, 0
        
        if is_liquidated and liq_strategy == "Sell & Move to Brokerage":
            # Event: Sell all and move to Cash/Brokerage
            for p in current_properties:
                if p["v"] > 0:
                    growth_yrs = age - ca
                    final_v = p["v"] * ((1 + p["a"]) ** growth_yrs)
                    # Capital Gains Tax = (Sale Price - Basis) * Rate
                    tax_hit = max(0, (final_v - p["b"]) * cap_gains)
                    net_proceeds = final_v - p["l"] - tax_hit
                    cc += net_proceeds
                    p["v"], p["l"], p["r"] = 0, 0, 0 # Property is gone
        
        # Calculate ongoing RE (if not sold or if using 1031 logic)
        for p in current_properties:
            if p["v"] > 0:
                h = age - ca
                curr_v = p["v"] * ((1 + p["a"]) ** h)
                noi = p["r"] - (curr_v * (p_tax_rate + p_maint)) - (p["r"] * p_mgmt)
                debt = p["m"] if h < p["term"] else 0
                re_cash_flow += (noi - debt)
                re_equity += (curr_v - (p["l"] if h < p["term"] else 0))

        # 2. Income & Taxes
        salary = (hp if age < hr else 0) + (yp if age < yr else 0)
        ss = 85000 if age >= 67 else 0
        taxable_income = salary + max(0, re_cash_flow) + ss
        
        current_tax_rate = tax_work if salary > 0 else tax_ret
        tax_bill = taxable_income * current_tax_rate
        net_income = taxable_income - tax_bill
        
        # 3. Cash Flow & Withdrawal
        spend = ew if (age < yr or age < hr) else er
        gap = spend - net_income
        
        withdraw_401k = 0
        if gap > 0:
            from_cash = min(cc, gap); cc -= from_cash; gap -= from_cash
            if gap > 0:
                # 401k withdrawal is taxed as ordinary income
                gross_401k = gap / (1 - tax_ret)
                actual_draw = min(cd, gross_401k)
                cd -= actual_draw; gap -= (actual_draw * (1 - tax_ret))
                withdraw_401k = actual_draw
            if gap > 0:
                from_roth = min(cr, gap); cr -= from_roth; gap -= from_roth
        else:
            cc += abs(gap) # Save surplus

        # 4. Growth
        cd *= (1 + roi); cr *= (1 + roi); cc *= (1 + roi if is_liquidated else 1.02)
        
        history.append({
            "Age": age, "Net Worth": (cc + cd + cr + re_equity),
            "Cash/Brokerage": cc, "401k": cd, "RE Equity": re_equity,
            "Net Income": net_income, "Withdraw 401k": withdraw_401k, "RE CashFlow": re_cash_flow
        })
        
    return pd.DataFrame(history)

# --- 3. UI ---
df = run_simulation()
st.title("🛡️ Legacy Master v15.0")

# Summary Metrics
m1, m2, m3 = st.columns(3)
m1.metric("Final Estate", f"${df['Net Worth'].iloc[-1]:,.0f}")
m2.metric("Peak Liquid Capital", f"${df['Cash/Brokerage'].max():,.0f}")
m3.metric("Strategy", liq_strategy)

# Chart
fig = go.Figure()
fig.add_trace(go.Scatter(x=df["Age"], y=df["Net Worth"], name="Total Net Worth", line=dict(width=4, color="#10b981")))
fig.add_trace(go.Scatter(x=df["Age"], y=df["RE Equity"], name="RE Equity", fill='tozeroy', line=dict(width=0)))
fig.add_trace(go.Scatter(x=df["Age"], y=df["Cash/Brokerage"], name="Cash/Brokerage", fill='tonexty', line=dict(width=0)))
fig.update_layout(template="plotly_dark", hovermode="x unified")
st.plotly_chart(fig, use_container_width=True)

# The Audit Log
with st.expander("📝 The Audit Log (Full Assumption Trace)"):
    st.dataframe(df.style.format({
        "Net Worth": "${:,.0f}", "Cash/Brokerage": "${:,.0f}", "401k": "${:,.0f}", 
        "RE Equity": "${:,.0f}", "Net Income": "${:,.0f}", "Withdraw 401k": "${:,.0f}", "RE CashFlow": "${:,.0f}"
    }))

with st.expander("🔬 Strategy Analysis"):
    st.markdown(f"""
    ### **Strategy: {liq_strategy}**
    * **Tax Efficiency:** {'High (Deals with basis later or via Step-up)' if liq_strategy == 'Hold/1031 Exchange' else 'Lower (Immediate Cap Gains Hit)'}
    * **Liquidity:** {'Locked in Physical Assets' if liq_strategy == 'Hold/1031 Exchange' else 'High (All Market-Accessible)'}
    * **Growth Engine:** {'Driven by Real Estate Appreciation & NOI' if li_strategy == 'Hold/1031 Exchange' else f'Driven by {roi*100}% Market ROI'}
    """)
