import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import json

st.set_page_config(layout="wide", page_title="Legacy Master 19.0")

# --- 1. DATA PERSISTENCE ---
if "inputs" not in st.session_state:
    st.session_state.inputs = {
        "v_c": 200000.0, "v_d": 1200000.0, "v_r": 500000.0, "tax_work": 0.30, "tax_ret": 0.20,
        "cap_gains": 0.20, "target_roi": 0.07, "liq_age": 55, "liq_strategy": "Hold/1031 (Step-up)",
        "props": [{"v": 1700000, "b": 1000000, "l": 800000, "r": 6500, "rate": 0.045, "term": 20, "a": 0.03}],
        "k1_start": 18, "k1_cost": 40000.0, "k2_start": 18, "k2_cost": 40000.0,
        "ca": 42, "ea": 95, "hp": 145000.0, "hr": 58, "yp": 110000.0, "yr": 55, "ew": 150000.0, "er": 120000.0
    }

sb = st.sidebar
uploaded_file = sb.file_uploader("📂 Upload Scenario", type="json")
if uploaded_file: st.session_state.inputs = json.load(uploaded_file)
inp = st.session_state.inputs

# --- 2. SIDEBAR INPUTS ---
with sb.expander("🎲 Simulations", expanded=True):
    use_monte = st.toggle("Monte Carlo Mode", value=True)
    n_sims = st.slider("Simulations", 10, 500, 100)
    inp["target_roi"] = st.slider("Target ROI %", 0.0, 15.0, int(inp["target_roi"]*100)) / 100

with sb.expander("🏠 Real Estate", expanded=False):
    inp["liq_strategy"] = st.radio("Strategy", ["Hold/1031 (Step-up)", "Sell & Move to Brokerage"])
    inp["liq_age"] = st.number_input("Liquidation Age", 45, 80, inp["liq_age"])
    n_p = st.number_input("Prop Count", 1, 10, len(inp["props"]))
    while len(inp["props"]) < n_p: inp["props"].append(inp["props"][0].copy())
    inp["props"] = inp["props"][:n_p]
    for i, p in enumerate(inp["props"]):
        st.caption(f"Prop {i+1}")
        p["v"] = st.number_input(f"Val {i+1}", value=p["v"], key=f"v{i}")
        p["r"] = st.number_input(f"Rent {i+1}/mo", value=p["r"], key=f"r{i}")
        p["l"] = st.number_input(f"Loan {i+1}", value=p["l"], key=f"l{i}")

# --- 3. MATH ENGINE ---
@st.cache_data
def run_sim(params, sims, monte):
    hist = [{"S": 0.12, "R": 0.05, "I": 0.02}, {"S": -0.15, "R": -0.05, "I": 0.04}, {"S": 0.05, "R": 0.02, "I": 0.01}]
    all_results = []
    for _ in range(sims):
        cc, cd, cr = params["v_c"], params["v_d"], params["v_r"]
        props = [p.copy() for p in params["props"]]
        path = []
        for age in range(params["ca"], params["ea"]+1):
            env = np.random.choice(hist) if monte else {"S": params["target_roi"], "R": 0.03, "I": 0.02}
            
            # RE & Income
            re_eq, re_cf = 0, 0
            for p in props:
                if p["v"] > 0:
                    cv = p["v"] * (1.03**(age-params["ca"]))
                    re_eq += (cv - p["l"]); re_cf += (p["r"]*12 - (cv*0.022))

            sal = (params["hp"] if age < params["hr"] else 0) + (params["yp"] if age < params["yr"] else 0)
            tax = (sal + max(0, re_cf)) * (params["tax_work"] if age < params["yr"] else params["tax_ret"])
            
            # Education (Aaron/Alvin)
            edu = (params["k1_cost"] + params["k2_cost"]) if 55 <= age <= 60 else 0 # Simplified age trigger
            spend = (params["ew"] if age < params["yr"] else params["er"]) + edu
            gap = spend - (sal + re_cf - tax)
            
            # Withdrawals
            draw_401 = 0
            if gap > 0:
                fc = min(cc, gap); cc -= fc; gap -= fc
                if gap > 0:
                    d = min(cd, gap/(1-params["tax_ret"])); cd -= d; gap -= (d*(1-params["tax_ret"])); draw_401 = d
            else: cc += abs(gap)
            
            cd *= (1+env["S"]); cc *= 1.02
            path.append({"Age": age, "NW": cc+cd+cr+re_eq, "CashFlow": sal+re_cf-tax-spend, "Draw401": draw_401})
        all_results.append(path)
    return all_results

results = run_sim(inp, n_sims, use_monte)

# --- 4. VISUALIZATION ---
st.title("🛡️ Legacy Master v19.0")
c1, c2 = st.columns(2)
c1.download_button("📥 Save JSON", data=json.dumps(inp), file_name="scenario.json")
c2.download_button("📊 Export CSV", data=pd.DataFrame(results[0]).to_csv(), file_name="audit.csv")

# A. MONTE CARLO PROBABILITY BANDS
nw_data = np.array([[y["NW"] for y in path] for path in results])
ages = [y["Age"] for y in results[0]]
p5, p50, p95 = np.percentile(nw_data, [5, 50, 95], axis=0)

fig_nw = go.Figure()
fig_nw.add_trace(go.Scatter(x=ages, y=p95, line=dict(width=0), showlegend=False))
fig_nw.add_trace(go.Scatter(x=ages, y=p5, line=dict(width=0), fill='tonexty', fillcolor='rgba(16, 185, 129, 0.2)', name="90% Confidence"))
fig_nw.add_trace(go.Scatter(x=ages, y=p50, line=dict(color='#10b981', width=4), name="Median Outlook"))
fig_nw.update_layout(title="Net Worth Probability Bands", template="plotly_dark")
st.plotly_chart(fig_nw, use_container_width=True)

# B. ANNUAL CASH FLOW BARS (Median Path)
med_path = pd.DataFrame(results[len(results)//2])
fig_cf = go.Figure()
fig_cf.add_trace(go.Bar(x=med_path["Age"], y=med_path["CashFlow"], name="Surplus/Deficit", marker_color="#3b82f6"))
fig_cf.add_trace(go.Bar(x=med_path["Age"], y=med_path["Draw401"], name="401k Injection", marker_color="#f59e0b"))
fig_cf.update_layout(title="Annual Cash Flow & Withdrawal Strategy", barmode='relative', template="plotly_dark")
st.plotly_chart(fig_cf, use_container_width=True)

st.expander("📑 View Full Audit Log").dataframe(med_path.style.format("{:,.0f}"))
