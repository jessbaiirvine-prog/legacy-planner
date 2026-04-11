import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import json

st.set_page_config(layout="wide", page_title="Legacy Master 21.0", page_icon="🏦")

# --- 1. PERSISTENCE & SESSION STATE ---
if "inputs" not in st.session_state:
    st.session_state.inputs = {
        "v_c": 200000.0, "v_d": 1200000.0, "v_r": 500000.0,
        "tax_work": 0.30, "tax_ret": 0.20, "cap_gains": 0.20, "target_roi": 0.07,
        "p_tax": 0.012, "p_maint": 0.01, "p_mgmt": 0.08,
        "liq_age": 55, "liq_strategy": "Hold/1031 (Step-up)",
        "props": [{"v": 1700000.0, "b": 1000000.0, "l": 800000.0, "r": 6500.0, "rate": 0.045, "term": 20, "a": 0.03}],
        "k1_start": 18, "k1_cost": 40000.0, "k2_start": 18, "k2_cost": 40000.0,
        "ca": 42, "ea": 95, "hp": 145000.0, "hr": 58, "yp": 110000.0, "yr": 55, "ew": 150000.0, "er": 120000.0, "ss": 85000.0
    }

sb = st.sidebar
sb.title("💾 Data Management")
uploaded_file = sb.file_uploader("Upload Scenario (.json)", type="json")
if uploaded_file:
    st.session_state.inputs.update(json.load(uploaded_file))

inp = st.session_state.inputs

# --- 2. LHS: THE COMPREHENSIVE SIDEBAR ---
with sb.expander("🎲 Simulation Engine", expanded=True):
    use_monte = st.toggle("Monte Carlo (Historical Stress)", value=True)
    n_sims = st.slider("Simulations", 10, 500, 100)
    inp["target_roi"] = st.slider("Target Market ROI %", 0.0, 15.0, float(inp["target_roi"]*100)) / 100

with sb.expander("💰 Assets & Taxes", expanded=False):
    inp["v_c"] = st.number_input("Cash/Brokerage", value=float(inp["v_c"]))
    inp["v_d"] = st.number_input("401k (Pre-Tax)", value=float(inp["v_d"]))
    inp["v_r"] = st.number_input("Roth/HSA", value=float(inp["v_r"]))
    inp["tax_work"] = st.slider("Work Tax %", 10, 50, int(inp["tax_work"]*100)) / 100
    inp["tax_ret"] = st.slider("Retire Tax %", 0, 40, int(inp["tax_ret"]*100)) / 100
    inp["cap_gains"] = st.slider("Cap Gains %", 0, 30, int(inp["cap_gains"]*100)) / 100

with sb.expander("🏠 Real Estate Portfolio", expanded=False):
    inp["liq_strategy"] = st.radio("Retirement Strategy", ["Hold/1031 (Step-up)", "Sell & Move to Brokerage"])
    inp["liq_age"] = st.number_input("Liquidation Age", 45, 85, int(inp["liq_age"]))
    inp["p_tax"] = st.number_input("Prop Tax Rate %", 0.5, 3.0, float(inp["p_tax"]*100)) / 100
    inp["p_maint"] = st.number_input("Maint Rate %", 0.5, 3.0, float(inp["p_maint"]*100)) / 100
    inp["p_mgmt"] = st.number_input("Mgmt Fee %", 0, 15, int(inp["p_mgmt"]*100)) / 100
    
    n_p = st.number_input("Property Count", 1, 10, len(inp["props"]))
    while len(inp["props"]) < n_p: inp["props"].append(inp["props"][0].copy())
    inp["props"] = inp["props"][:n_p]
    for i, p in enumerate(inp["props"]):
        st.markdown(f"**Prop {i+1}**")
        p["v"] = st.number_input(f"Value {i+1}", value=float(p["v"]), key=f"v{i}")
        p["l"] = st.number_input(f"Loan {i+1}", value=float(p["l"]), key=f"l{i}")
        p["r"] = st.number_input(f"Rent {i+1}/mo", value=float(p["r"]), key=f"r{i}")
        p["b"] = st.number_input(f"Basis {i+1}", value=float(p.get("b", 1000000.0)), key=f"b{i}")

with sb.expander("👩‍💼 Household & Education", expanded=False):
    inp["hp"] = st.number_input("Husband Salary", value=float(inp["hp"]))
    inp["hr"] = st.number_input("Husband Retire Age", value=int(inp["hr"]))
    inp["yp"] = st.number_input("Your Salary", value=float(inp["yp"]))
    inp["yr"] = st.number_input("Your Retire Age", value=int(inp["yr"]))
    inp["ss"] = st.number_input("Combined Social Security", value=float(inp["ss"]))
    inp["k1_cost"] = st.number_input("Aaron Tuition", value=float(inp["k1_cost"]))
    inp["k2_cost"] = st.number_input("Alvin Tuition", value=float(inp["k2_cost"]))
    inp["ew"] = st.number_input("Working Spend", value=float(inp["ew"]))
    inp["er"] = st.number_input("Retire Spend", value=float(inp["er"]))

# --- 3. THE ENGINE ---
@st.cache_data
def run_engine(params, sims, monte):
    hist = [{"S": 0.14, "R": 0.05, "I": 0.02}, {"S": -0.18, "R": -0.10, "I": 0.03}, {"S": 0.06, "R": 0.02, "I": 0.02}]
    all_runs = []
    for _ in range(sims):
        cc, cd, cr = params["v_c"], params["v_d"], params["v_r"]
        props = [p.copy() for p in params["props"]]
        path = []
        for age in range(params["ca"], params["ea"] + 1):
            env = np.random.choice(hist) if monte else {"S": params["target_roi"], "R": 0.03, "I": 0.02}
            # Liquidation logic
            if age == params["liq_age"] and params["liq_strategy"] == "Sell & Move to Brokerage":
                for p in props:
                    if p["v"] > 0:
                        fv = p["v"] * (1.03**(age-params["ca"]))
                        cc += (fv - p["l"] - (max(0, fv-p["b"])*params["cap_gains"])); p["v"] = 0
            
            re_eq, re_cf = 0, 0
            for p in props:
                if p["v"] > 0:
                    cv = p["v"] * (1.03**(age-params["ca"]))
                    re_eq += (cv - p["l"]); re_cf += (p["r"]*12 - (cv*(params["p_tax"]+params["p_maint"])) - (p["r"]*12*params["p_mgmt"]))

            sal = (params["hp"] if age < params["hr"] else 0) + (params["yp"] if age < params["yr"] else 0)
            taxable = sal + max(0, re_cf) + (params["ss"] if age >= 67 else 0)
            tax = taxable * (params["tax_work"] if sal > 0 else params["tax_ret"])
            
            # Education Logic (Age 18-22 for kids)
            edu = (params["k1_cost"] if 18<=(age-32)<=22 else 0) + (params["k2_cost"] if 18<=(age-30)<=22 else 0)
            spend = (params["ew"] if age < params["yr"] else params["er"]) + edu
            gap = spend - (taxable - tax)
            
            draw401 = 0
            if gap > 0:
                fc = min(cc, gap); cc -= fc; gap -= fc
                if gap > 0:
                    draw = min(cd, gap/(1-params["tax_ret"])); cd -= draw; gap -= (draw*(1-params["tax_ret"])); draw401 = draw
            else: cc += abs(gap)
            
            cd *= (1+env["S"]); cc *= (1.02 if params["liq_strategy"]=="Hold/1031 (Step-up)" else (1+env["S"]))
            path.append({"Age": age, "NW": cc+cd+cr+re_eq, "CashFlow": taxable-tax-spend, "Draw401": draw401, "RE": re_eq})
        all_runs.append(path)
    return all_runs

results = run_engine(inp, n_sims, use_monte)
nw_data = np.array([[y["NW"] for y in path] for path in results])
p5, p50, p95 = np.percentile(nw_data, [5, 50, 95], axis=0)
med_path = pd.DataFrame(results[len(results)//2])

# --- 4. DISPLAY ---
st.title("🛡️ Legacy Master v21.0")

# Summary Metrics
m1, m2, m3, m4 = st.columns(4)
m1.metric("Median Estate", f"${p50[-1]:,.0f}")
m2.metric("Success Rate", f"{(nw_data[:,-1] > 0).mean()*100:.0f}%")
m3.metric("Worst Case (5%)", f"${p5[-1]:,.0f}")
m4.metric("Strategy", inp["liq_strategy"])

# Charts
fig_nw = go.Figure()
# Shaded Band
fig_nw.add_trace(go.Scatter(x=med_path["Age"], y=p95, line=dict(width=0), showlegend=False))
fig_nw.add_trace(go.Scatter(x=med_path["Age"], y=p5, fill='tonexty', fillcolor='rgba(16,185,129,0.1)', name="Risk Range"))
# Ghost Paths
for i in range(min(10, n_sims)):
    fig_nw.add_trace(go.Scatter(x=med_path["Age"], y=nw_data[i], line=dict(color="rgba(255,255,255,0.1)", width=1), showlegend=False))
fig_nw.add_trace(go.Scatter(x=med_path["Age"], y=p50, line=dict(color="#10b981", width=4), name="Median Path"))
st.plotly_chart(fig_nw, use_container_width=True)

st.download_button("📥 Save JSON", data=json.dumps(inp), file_name="scenario.json")
st.expander("📊 Audit Log").dataframe(med_path.style.format("{:,.0f}"))
