import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import json
from datetime import datetime

st.set_page_config(layout="wide", page_title="Legacy Master 18.0", page_icon="📈")

# --- 0. DATA PERSISTENCE & UPLOAD ---
def export_json(data):
    return json.dumps(data, indent=4)

st.sidebar.title("💾 Data Management")
uploaded_file = st.sidebar.file_uploader("Upload Saved Scenario (.json)", type="json")

# Initialize default session state if not present
if "inputs" not in st.session_state:
    st.session_state.inputs = {
        "v_c": 200000.0, "v_d": 1200000.0, "v_r": 500000.0,
        "tax_work": 0.30, "tax_ret": 0.20, "cap_gains": 0.20,
        "target_roi": 0.07, "liq_age": 55, "liq_strategy": "Hold/1031 (Step-up)",
        "props": [{"v": 1700000, "b": 1000000, "l": 800000, "r": 6500, "rate": 0.045, "term": 20, "a": 0.03}],
        "k1_start": 18, "k1_cost": 40000.0, "k2_start": 18, "k2_cost": 40000.0,
        "ca": 42, "ea": 95, "hp": 145000.0, "hr": 58, "yp": 110000.0, "yr": 55, "ew": 150000.0, "er": 120000.0
    }

if uploaded_file:
    st.session_state.inputs = json.load(uploaded_file)
    st.sidebar.success("Scenario Loaded!")

# --- 1. SIDEBAR INPUTS ---
sb = st.sidebar
inp = st.session_state.inputs

with sb.expander("🎲 Simulation Engine", expanded=True):
    use_monte = st.toggle("Historical Stress Test", value=True)
    n_sims = st.slider("Simulations", 10, 500, 100) if use_monte else 1
    inp["target_roi"] = st.slider("Target ROI %", 0.0, 15.0, inp["target_roi"]*100) / 100

with sb.expander("💰 Assets & Taxes", expanded=False):
    inp["v_c"] = st.number_input("Cash/Brokerage", value=inp["v_c"])
    inp["v_d"] = st.number_input("401k (Pre-Tax)", value=inp["v_d"])
    inp["v_r"] = st.number_input("Roth (Tax-Free)", value=inp["v_r"])
    inp["tax_work"] = st.slider("Tax (Work) %", 10, 50, int(inp["tax_work"]*100)) / 100
    inp["tax_ret"] = st.slider("Tax (Retire) %", 0, 40, int(inp["tax_ret"]*100)) / 100

with sb.expander("🏠 Real Estate Portfolio", expanded=False):
    inp["liq_strategy"] = st.radio("Strategy", ["Hold/1031 (Step-up)", "Sell & Move to Brokerage"], 
                                   index=0 if inp["liq_strategy"]=="Hold/1031 (Step-up)" else 1)
    inp["liq_age"] = st.number_input("Liquidation Age", 45, 80, inp["liq_age"])
    n_prop = st.number_input("Property Count", 1, 10, len(inp["props"]))
    
    # Adjust props list length
    while len(inp["props"]) < n_prop: inp["props"].append(inp["props"][0].copy())
    if len(inp["props"]) > n_prop: inp["props"] = inp["props"][:n_prop]
    
    for i in range(n_prop):
        st.markdown(f"**Prop {i+1}**")
        p = inp["props"][i]
        p["v"] = st.number_input(f"Value P{i+1}", value=p["v"], key=f"v{i}")
        p["l"] = st.number_input(f"Loan P{i+1}", value=p["l"], key=f"l{i}")
        p["r"] = st.number_input(f"Rent P{i+1}/mo", value=p["r"], key=f"r{i}")
        p["a"] = st.number_input(f"Appr % P{i+1}", value=p["a"]*100, key=f"a{i}") / 100

with sb.expander("🎓 Education & Household", expanded=False):
    inp["k1_cost"] = st.number_input("Aaron College/yr", value=inp["k1_cost"])
    inp["k2_cost"] = st.number_input("Alvin College/yr", value=inp["k2_cost"])
    inp["ca"] = st.number_input("Current Age", value=inp["ca"])
    inp["ea"] = st.number_input("End Age", value=inp["ea"])

# --- 2. MATH ENGINE ---
@st.cache_data
def engine(params, sims, monte):
    hist_pool = [{"S": 0.01, "R": 0.02, "I": 0.02}, {"S": -0.38, "R": -0.10, "I": 0.03}, {"S": 0.24, "R": 0.05, "I": 0.04}]
    all_runs = []
    for _ in range(sims):
        cc, cd, cr = params["v_c"], params["v_d"], params["v_r"]
        props = [p.copy() for p in params["props"]]
        path = []
        for age in range(int(params["ca"]), int(params["ea"]) + 1):
            h = age - params["ca"]
            env = np.random.choice(hist_pool) if monte else {"S": 0.08, "R": 0.04, "I": 0.02}
            m_yield = params["target_roi"] + (env["S"] - 0.08)
            
            # Liquidation
            if age == params["liq_age"] and params["liq_strategy"] == "Sell & Move to Brokerage":
                for p in props:
                    if p["v"] > 0:
                        fv = p["v"] * (1.03**h); tax = max(0, (fv - p["b"]) * params["cap_gains"])
                        cc += (fv - p["l"] - tax); p["v"] = 0
            
            # Cashflow
            re_cf, re_eq = 0, 0
            for p in props:
                if p["v"] > 0:
                    cv = p["v"] * (1.03**h); re_eq += (cv - p["l"])
                    re_cf += (p["r"]*12 - (cv * 0.022)) # 2.2% for tax/maint/mgmt
            
            inc = (params["hp"] if age < params["hr"] else 0) + (params["yp"] if age < params["yr"] else 0) + (85000 if age >= 67 else 0)
            tax = (inc + max(0, re_cf)) * (params["tax_work"] if age < params["yr"] else params["tax_ret"])
            
            # Education (Sample logic: 18 years from now for 4 years)
            edu = (params["k1_cost"] + params["k2_cost"]) if 60 <= age <= 64 else 0
            
            gap = (params["ew"] if age < params["yr"] else params["er"]) + edu - (inc + re_cf - tax)
            
            # Withdrawals
            if gap > 0:
                fc = min(cc, gap); cc -= fc; gap -= fc
                if gap > 0:
                    actual = min(cd, gap/(1-params["tax_ret"])); cd -= actual; gap -= (actual*(1-params["tax_ret"]))
            else: cc += abs(gap)
            
            cd *= (1+m_yield); cr *= (1+m_yield); cc *= 1.02
            path.append({"Age": age, "NW": cc+cd+cr+re_eq, "Cash": cc, "401k": cd, "RE": re_eq})
        all_runs.append(path)
    return all_runs

results = engine(inp, n_sims, use_monte)
med_df = pd.DataFrame(results[len(results)//2])

# --- 3. UI & DOWNLOADS ---
st.title("🛡️ Legacy Master v18.0")

# Download row
c1, c2, c3 = st.columns(3)
c1.download_button("📥 Download JSON Scenario", data=export_json(inp), file_name="scenario.json")
c2.download_button("📊 Download CSV Audit Log", data=med_df.to_csv(index=False), file_name="audit_log.csv")

fig = go.Figure()
fig.add_trace(go.Scatter(x=med_df["Age"], y=med_df["NW"], name="Median Path", line=dict(color="#10b981", width=4)))
fig.update_layout(template="plotly_dark", height=450)
st.plotly_chart(fig, use_container_width=True)

st.dataframe(med_df.style.format("{:,.0f}"))
