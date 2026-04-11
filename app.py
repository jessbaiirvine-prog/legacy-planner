import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import json

st.set_page_config(layout="wide", page_title="Legacy Master 16.0")

# --- 0. HISTORICAL DATASET (Monte Carlo Source) ---
hist_data = [
    {"Year": 1994, "Stocks": 0.013, "RE": 0.020, "Inf": 0.026},
    {"Year": 2000, "Stocks": -0.091, "RE": 0.080, "Inf": 0.034},
    {"Year": 2008, "Stocks": -0.385, "RE": -0.120, "Inf": 0.038},
    {"Year": 2022, "Stocks": -0.181, "RE": 0.060, "Inf": 0.080},
    {"Year": 2023, "Stocks": 0.242, "RE": 0.050, "Inf": 0.041},
    {"Year": 2024, "Stocks": 0.250, "RE": 0.040, "Inf": 0.032}
]
df_hist = pd.DataFrame(hist_data)

# --- 1. SIDEBAR: PROFESSIONAL INPUTS ---
sb = st.sidebar
sb.title("⚙️ Strategic Planning")

with sb.expander("🎲 Simulation Engine", expanded=True):
    use_monte = st.toggle("Historical Stress Test (Monte Carlo)", value=True)
    n_sims = st.slider("Simulations", 10, 500, 100) if use_monte else 1

with sb.expander("💰 Tax & Liquid Assets", expanded=True):
    v_c = st.number_input("Starting Cash/Brokerage", value=200000.0)
    v_d = st.number_input("401k (Pre-Tax)", value=1200000.0)
    v_r = st.number_input("Roth/HSA (Tax-Free)", value=500000.0)
    tax_work = st.slider("Income Tax (Working) %", 10, 50, 30) / 100
    tax_ret = st.slider("Income Tax (Retire) %", 0, 40, 20) / 100
    cap_gains = st.slider("Capital Gains Tax %", 0, 30, 20) / 100
    target_roi = st.slider("Target Market ROI %", 0.0, 15.0, 7.0) / 100

with sb.expander("🏠 Real Estate & Liquidation", expanded=False):
    liq_strategy = st.radio("Strategy", ["Hold/1031 (Step-up)", "Sell & Move to Brokerage"])
    liq_age = st.number_input("Liquidation Age", 45, 80, 55)
    n_prop = st.number_input("Property Count", 1, 5, 1)
    p_tax_rate, p_maint, p_mgmt = 0.012, 0.01, 0.08
    p_inputs = []
    for i in range(int(n_prop)):
        st.markdown(f"**Prop {i+1}**")
        v = st.number_input(f"Value P{i+1}", 1700000.0, key=f"v{i}")
        b = st.number_input(f"Basis P{i+1}", 1000000.0, key=f"b{i}")
        l = st.number_input(f"Loan P{i+1}", 800000.0, key=f"l{i}")
        r = st.number_input(f"Rent P{i+1}/mo", 6500.0, key=f"r{i}")
        rate = st.number_input(f"Rate % P{i+1}", 4.5, key=f"rate{i}") / 100
        term = st.number_input(f"Years Left P{i+1}", 20, key=f"term{i}")
        a = st.number_input(f"Appr % P{i+1}", 3.0, key=f"a{i}") / 100
        p_mtg = (l * (rate/12 * (1+rate/12)**(term*12)) / ((1+rate/12)**(term*12) - 1)) * 12 if l > 0 else 0
        p_inputs.append({"v":v,"b":b,"l":l,"m":p_mtg,"r":r*12,"a":a,"term":term})

with sb.expander("👩‍💼 Household", expanded=False):
    ca, ea = st.number_input("Current Age", 42), st.number_input("End Age", 95)
    hp, hr = st.number_input("Husband Salary", 145000.0), st.number_input("Husband Retire Age", 58)
    yp, yr = st.number_input("Your Salary", 110000.0), st.number_input("Your Retire Age", 55)
    ew, er = st.number_input("Spend (Work)", 150000.0), st.number_input("Spend (Retire)", 120000.0)

# --- 2. MATH ENGINE ---
@st.cache_data
def calculate_all(n_iters, is_monte):
    all_results = []
    for _ in range(n_iters):
        cc, cd, cr = v_c, v_d, v_r
        current_props = [p.copy() for p in p_inputs]
        path = []
        for age in range(int(ca), int(ea) + 1):
            h = age - ca
            # Environment: Stress Test vs Static
            if is_monte:
                env = df_hist.sample(1).iloc[0]
                mkt_yield = target_roi + (env["Stocks"] - 0.08) # Center hist volatility on target
                re_yield = 0.03 + (env["RE"] - 0.04)
                inf = env["Inf"]
            else:
                mkt_yield, re_yield, inf = target_roi, 0.03, 0.02
            
            # Liquidation
            if age == liq_age and liq_strategy == "Sell & Move to Brokerage":
                for p in current_props:
                    if p["v"] > 0:
                        fv = p["v"] * ((1 + p["a"])**h)
                        tax = max(0, (fv - p["b"]) * cap_gains)
                        cc += (fv - p["l"] - tax)
                        p["v"], p["l"], p["r"] = 0, 0, 0

            # Real Estate Math
            re_eq, re_cf = 0, 0
            for p in current_props:
                if p["v"] > 0:
                    cv = p["v"] * ((1 + (re_yield if is_monte else p["a"]))**h)
                    noi = (p["r"] * (1+inf)**h) - (cv * (p_tax_rate + p_maint)) - (p["r"] * p_mgmt)
                    debt = p["m"] if h < p["term"] else 0
                    re_cf += (noi - debt)
                    re_eq += (cv - (p["l"] if h < p["term"] else 0))

            # Income & Tax
            sal = (hp if age < hr else 0) + (yp if age < yr else 0)
            ss = 85000 if age >= 67 else 0
            t_inc = sal + max(0, re_cf) + ss
            tax = t_inc * (tax_work if sal > 0 else tax_ret)
            net = t_inc - tax
            
            # Cash Flow
            spend = ew if (age < yr or age < hr) else er
            gap = spend - net
            draw_401k = 0
            if gap > 0:
                fc = min(cc, gap); cc -= fc; gap -= fc
                if gap > 0:
                    gross_401 = gap / (1 - tax_ret)
                    actual = min(cd, gross_401)
                    cd -= actual; gap -= (actual * (1 - tax_ret))
                    draw_401k = actual
                if gap > 0:
                    fr = min(cr, gap); cr -= fr; gap -= fr
            else: cc += abs(gap)

            # Growth
            cd *= (1 + mkt_yield); cr *= (1 + mkt_yield)
            cc *= (1 + mkt_yield if (age >= liq_age and liq_strategy != "Hold/1031 (Step-up)") else 1.01)
            
            path.append({"Age": age, "NW": cc+cd+cr+re_eq, "Cash": cc, "401k": cd, "RE": re_eq, "Tax": tax, "Draw401": draw_401k})
        all_results.append(path)
    return all_results

results = calculate_all(n_sims, use_monte)

# --- 3. UI & VISUALIZATION ---
st.title("🛡️ Legacy Master v16.0")

# Percentile Calculation
final_nws = [p[-1]["NW"] for p in results]
p50_idx = np.argsort(final_nws)[len(final_nws)//2]
median_path = pd.DataFrame(results[p50_idx])

c1, c2, c3 = st.columns(3)
c1.metric("Median Estate", f"${final_nws[p50_idx]:,.0f}")
c2.metric("Success Rate", f"{(np.array(final_nws) > 0).mean()*100:.1f}%")
c3.metric("Simulations", len(results))

fig = go.Figure()
for p in results[::max(1, len(results)//20)]: # Plot sample paths
    p_df = pd.DataFrame(p)
    fig.add_trace(go.Scatter(x=p_df["Age"], y=p_df["NW"], line=dict(width=1, color="rgba(100,100,100,0.2)"), showlegend=False))

fig.add_trace(go.Scatter(x=median_path["Age"], y=median_path["NW"], name="Median Scenario", line=dict(color="#10b981", width=4)))
fig.update_layout(template="plotly_dark", title="Net Worth Stress Test", hovermode="x unified")
st.plotly_chart(fig, use_container_width=True)

with st.expander("📊 Audit Log (Median Scenario)"):
    st.dataframe(median_path.style.format({
        "NW": "${:,.0f}", "Cash": "${:,.0f}", "401k": "${:,.0f}", "RE": "${:,.0f}", "Tax": "${:,.0f}", "Draw401": "${:,.0f}"
    }))

with st.expander("🔬 Strategy Analysis"):
    st.markdown(f"""
    * **Strategy:** {liq_strategy}
    * **Growth Engine:** {'Physical Real Estate + NOI' if liq_strategy == 'Hold/1031 (Step-up)' else f'Liquid Portfolio @ {target_roi*100}%'}
    * **Tax Behavior:** 401k withdrawals are grossed up to cover a **{tax_ret*100}%** retirement tax liability.
    """)
