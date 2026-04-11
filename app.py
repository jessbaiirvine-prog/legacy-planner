import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import json

st.set_page_config(layout="wide", page_title="Legacy Master 20.0")

# --- 1. PERSISTENCE & TYPE SAFETY ---
if "inputs" not in st.session_state:
    st.session_state.inputs = {
        "v_c": 200000.0, "v_d": 1200000.0, "v_r": 500000.0, "tax_work": 0.30, "tax_ret": 0.20,
        "cap_gains": 0.20, "target_roi": 0.07, "liq_age": 55, "liq_strategy": "Hold/1031 (Step-up)",
        "props": [{"v": 1700000.0, "b": 1000000.0, "l": 800000.0, "r": 6500.0, "rate": 0.045, "term": 20.0, "a": 0.03}],
        "k1_start": 18, "k1_cost": 40000.0, "k2_start": 18, "k2_cost": 40000.0,
        "ca": 42, "ea": 95, "hp": 145000.0, "hr": 58, "yp": 110000.0, "yr": 55, "ew": 150000.0, "er": 120000.0
    }

sb = st.sidebar
uploaded_file = sb.file_uploader("📂 Upload Scenario (.json)", type="json")
if uploaded_file:
    st.session_state.inputs = json.load(uploaded_file)

inp = st.session_state.inputs

# --- 2. SIDEBAR INPUTS (Fixed Data Types) ---
with sb.expander("🎲 Simulations", expanded=True):
    use_monte = st.toggle("Monte Carlo Mode", value=True)
    n_sims = st.slider("Simulations", 10, 500, 100)
    # FIX: Ensure all slider values are floats to avoid StreamlitAPIException
    inp["target_roi"] = st.slider("Target ROI %", 0.0, 15.0, float(inp["target_roi"]*100)) / 100

with sb.expander("🏠 Real Estate", expanded=False):
    liq_opts = ["Hold/1031 (Step-up)", "Sell & Move to Brokerage"]
    strat_idx = liq_opts.index(inp["liq_strategy"]) if inp["liq_strategy"] in liq_opts else 0
    inp["liq_strategy"] = st.radio("Strategy", liq_opts, index=strat_idx)
    inp["liq_age"] = st.number_input("Liquidation Age", 45, 80, int(inp["liq_age"]))
    
    n_p = st.number_input("Property Count", 1, 10, len(inp["props"]))
    while len(inp["props"]) < n_p: inp["props"].append(inp["props"][0].copy())
    inp["props"] = inp["props"][:n_p]
    
    for i, p in enumerate(inp["props"]):
        st.caption(f"Property {i+1}")
        p["v"] = st.number_input(f"Value {i+1}", value=float(p["v"]), key=f"v{i}")
        p["r"] = st.number_input(f"Rent {i+1}/mo", value=float(p["r"]), key=f"r{i}")
        p["l"] = st.number_input(f"Loan {i+1}", value=float(p["l"]), key=f"l{i}")
        p["b"] = st.number_input(f"Cost Basis {i+1}", value=float(p.get("b", 1000000.0)), key=f"b{i}")

with sb.expander("🎓 Education & Timeline", expanded=False):
    inp["k1_cost"] = st.number_input("Aaron Annual Tuition", value=float(inp["k1_cost"]))
    inp["k2_cost"] = st.number_input("Alvin Annual Tuition", value=float(inp["k2_cost"]))
    inp["ca"] = st.number_input("Your Age", value=int(inp["ca"]))
    inp["yr"] = st.number_input("Your Retire Age", value=int(inp["yr"]))
    inp["hr"] = st.number_input("Husband Retire Age", value=int(inp["hr"]))

# --- 3. MATH ENGINE ---
@st.cache_data
def run_sim(params, sims, monte):
    # Historical return pool (Simplified for stability)
    hist = [{"S": 0.12, "R": 0.05}, {"S": -0.15, "R": -0.05}, {"S": 0.05, "R": 0.02}]
    all_results = []
    
    for _ in range(sims):
        cc, cd, cr = params["v_c"], params["v_d"], params["v_r"]
        props = [p.copy() for p in params["props"]]
        path = []
        
        for age in range(params["ca"], params["ea"] + 1):
            h = age - params["ca"]
            env = np.random.choice(hist) if monte else {"S": params["target_roi"], "R": 0.03}
            m_yield = env["S"]
            
            # Liquidation Event
            if age == params["liq_age"] and params["liq_strategy"] == "Sell & Move to Brokerage":
                for p in props:
                    if p["v"] > 0:
                        fv = p["v"] * (1.03**h)
                        tax = max(0, (fv - p["b"]) * params["cap_gains"])
                        cc += (fv - p["l"] - tax)
                        p["v"] = 0 # Property sold
            
            # RE Cash Flow & Equity
            re_eq, re_cf = 0, 0
            for p in props:
                if p["v"] > 0:
                    cv = p["v"] * (1.03**h)
                    re_eq += (cv - p["l"])
                    re_cf += (p["r"]*12 - (cv * 0.025)) # 2.5% Tax/Maint/Mgmt

            # Salaries & Taxes
            sal = (params["hp"] if age < params["hr"] else 0) + (params["yp"] if age < params["yr"] else 0)
            taxable = sal + max(0, re_cf) + (85000 if age >= 67 else 0)
            tax_bill = taxable * (params["tax_work"] if sal > 0 else params["tax_ret"])
            
            # Expenses (including Education age 18-22 for kids)
            # Kids are approx 10 & 12 years younger than user
            edu = 0
            if 18 <= (age - 32) <= 22: edu += params["k1_cost"] # Aaron
            if 18 <= (age - 30) <= 22: edu += params["k2_cost"] # Alvin
            
            spend = (params["ew"] if age < params["yr"] else params["er"]) + edu
            net_income = taxable - tax_bill
            gap = spend - net_income
            
            # Withdrawal Logic
            draw_401 = 0
            if gap > 0:
                from_cash = min(cc, gap); cc -= from_cash; gap -= from_cash
                if gap > 0:
                    needed = gap / (1 - params["tax_ret"])
                    draw = min(cd, needed); cd -= draw; gap -= (draw * (1 - params["tax_ret"])); draw_401 = draw
            else:
                cc += abs(gap)

            cd *= (1 + m_yield); cc *= 1.02 # Cash growth
            path.append({"Age": age, "NW": cc+cd+cr+re_eq, "CashFlow": net_income - spend, "Draw401": draw_401})
        all_results.append(path)
    return all_results

results = run_sim(inp, n_sims, use_monte)

# --- 4. OUTPUTS & CHARTS ---
st.title("🛡️ Legacy Master v20.0")

col1, col2 = st.columns(2)
col1.download_button("📥 Save Scenario (JSON)", data=json.dumps(inp), file_name="scenario.json")
col2.download_button("📊 Export Audit (CSV)", data=pd.DataFrame(results[0]).to_csv(), file_name="audit.csv")

# A. PROBABILITY BANDS
nw_data = np.array([[y["NW"] for y in path] for path in results])
ages = [y["Age"] for y in results[0]]
p5, p50, p95 = np.percentile(nw_data, [5, 50, 95], axis=0)

fig_nw = go.Figure()
fig_nw.add_trace(go.Scatter(x=ages, y=p95, line=dict(width=0), showlegend=False))
fig_nw.add_trace(go.Scatter(x=ages, y=p5, line=dict(width=0), fill='tonexty', fillcolor='rgba(16, 185, 129, 0.2)', name="90% Confidence"))
fig_nw.add_trace(go.Scatter(x=ages, y=p50, line=dict(color='#10b981', width=4), name="Median Net Worth"))
fig_nw.update_layout(title="Net Worth Confidence Interval", template="plotly_dark", hovermode="x unified")
st.plotly_chart(fig_nw, use_container_width=True)

# B. CASH FLOW BARS
med_path = pd.DataFrame(results[len(results)//2])
fig_cf = go.Figure()
fig_cf.add_trace(go.Bar(x=med_path["Age"], y=med_path["CashFlow"], name="Surplus/Deficit", marker_color="#3b82f6"))
fig_cf.add_trace(go.Bar(x=med_path["Age"], y=med_path["Draw401"], name="401k Withdrawal", marker_color="#f59e0b"))
fig_cf.update_layout(title="Annual Cash Flow Strategy", barmode="relative", template="plotly_dark")
st.plotly_chart(fig_cf, use_container_width=True)

st.expander("📝 Detailed Audit Log").dataframe(med_path.style.format("{:,.0f}"))
