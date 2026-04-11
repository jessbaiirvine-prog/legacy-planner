import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import json

st.set_page_config(layout="wide", page_title="Legacy Master 22.0", page_icon="🏦")

# --- 1. ROBUST INITIALIZATION (Prevents KeyErrors) ---
DEFAULT_INPUTS = {
    "v_c": 200000.0, "v_d": 1200000.0, "v_r": 500000.0,
    "tax_work": 0.30, "tax_ret": 0.20, "cap_gains": 0.20, "target_roi": 0.07,
    "p_tax": 0.012, "p_maint": 0.01, "p_mgmt": 0.08,
    "liq_age": 55, "liq_strategy": "Hold/1031 (Step-up)",
    "props": [{"v": 1700000.0, "b": 1000000.0, "l": 800000.0, "r": 6500.0, "rate": 0.045, "term": 20, "a": 0.03}],
    "k1_start": 18, "k1_cost": 40000.0, "k2_start": 18, "k2_cost": 40000.0,
    "ca": 42, "ea": 95, "hp": 145000.0, "hr": 58, "yp": 110000.0, "yr": 55, "ew": 150000.0, "er": 120000.0, "ss": 85000.0
}

if "inputs" not in st.session_state:
    st.session_state.inputs = DEFAULT_INPUTS.copy()

sb = st.sidebar
sb.title("💾 Data Management")
uploaded_file = sb.file_uploader("Upload Scenario (.json)", type="json")

if uploaded_file:
    # Use update to merge uploaded data into the full default set
    uploaded_data = json.load(uploaded_file)
    st.session_state.inputs.update(uploaded_data)
    st.sidebar.success("Scenario Synced!")

inp = st.session_state.inputs

# --- 2. SIDEBAR INPUTS ---
with sb.expander("🎲 Simulation Engine", expanded=True):
    use_monte = st.toggle("Monte Carlo Mode", value=True)
    n_sims = st.slider("Simulations", 10, 500, 100)
    inp["target_roi"] = st.slider("Target ROI %", 0.0, 15.0, float(inp.get("target_roi", 0.07)*100)) / 100

with sb.expander("💰 Assets & Taxes", expanded=False):
    inp["v_c"] = st.number_input("Cash/Brokerage", value=float(inp.get("v_c", 200000)))
    inp["v_d"] = st.number_input("401k (Pre-Tax)", value=float(inp.get("v_d", 1200000)))
    inp["tax_work"] = st.slider("Work Tax %", 10, 50, int(inp.get("tax_work", 0.3)*100)) / 100
    inp["tax_ret"] = st.slider("Retire Tax %", 0, 40, int(inp.get("tax_ret", 0.2)*100)) / 100

with sb.expander("🏠 Real Estate Portfolio", expanded=False):
    inp["liq_strategy"] = st.radio("Strategy", ["Hold/1031 (Step-up)", "Sell & Move to Brokerage"])
    inp["liq_age"] = st.number_input("Liquidation Age", 45, 85, int(inp.get("liq_age", 55)))
    inp["p_tax"] = st.number_input("Prop Tax %", 0.0, 3.0, float(inp.get("p_tax", 0.012)*100)) / 100
    inp["p_maint"] = st.number_input("Maint %", 0.0, 3.0, float(inp.get("p_maint", 0.01)*100)) / 100
    inp["p_mgmt"] = st.number_input("Mgmt %", 0, 15, int(inp.get("p_mgmt", 0.08)*100)) / 100
    
    n_p = st.number_input("Property Count", 1, 10, len(inp.get("props", [1])))
    if len(inp["props"]) < n_p: inp["props"].extend([inp["props"][0].copy()] * (n_p - len(inp["props"])))
    inp["props"] = inp["props"][:n_p]
    
    for i, p in enumerate(inp["props"]):
        st.caption(f"Prop {i+1}")
        p["v"] = st.number_input(f"Val {i+1}", value=float(p.get("v", 1700000)), key=f"v{i}")
        p["r"] = st.number_input(f"Rent {i+1}/mo", value=float(p.get("r", 6500)), key=f"r{i}")
        p["l"] = st.number_input(f"Loan {i+1}", value=float(p.get("l", 800000)), key=f"l{i}")

with sb.expander("👨‍👩‍👧‍👦 Household & Education", expanded=False):
    inp["hp"] = st.number_input("Husband Salary", value=float(inp.get("hp", 145000)))
    inp["yp"] = st.number_input("Your Salary", value=float(inp.get("yp", 110000)))
    inp["ss"] = st.number_input("Social Security", value=float(inp.get("ss", 85000)))
    inp["k1_cost"] = st.number_input("Aaron Tuition", value=float(inp.get("k1_cost", 40000)))
    inp["k2_cost"] = st.number_input("Alvin Tuition", value=float(inp.get("k2_cost", 40000)))
    inp["er"] = st.number_input("Retire Spend", value=float(inp.get("er", 120000)))

# --- 3. MATH ENGINE ---
@st.cache_data
def engine(p_in, sims, monte):
    hist = [{"S": 0.12, "R": 0.04}, {"S": -0.15, "R": -0.08}, {"S": 0.04, "R": 0.02}]
    all_runs = []
    for _ in range(sims):
        cc, cd, cr = p_in["v_c"], p_in["v_d"], p_in["v_r"]
        props = [pr.copy() for pr in p_in["props"]]
        path = []
        for age in range(p_in["ca"], p_in["ea"] + 1):
            env = np.random.choice(hist) if monte else {"S": p_in["target_roi"], "R": 0.03}
            # Liquidation
            if age == p_in["liq_age"] and p_in["liq_strategy"] == "Sell & Move to Brokerage":
                for pr in props:
                    if pr["v"] > 0:
                        fv = pr["v"] * (1.03**(age-p_in["ca"]))
                        cc += (fv - pr["l"] - (max(0, fv-pr.get("b", 1000000))*p_in["cap_gains"])); pr["v"] = 0
            
            re_eq, re_cf = 0, 0
            for pr in props:
                if pr["v"] > 0:
                    cv = pr["v"] * (1.03**(age-p_in["ca"]))
                    re_eq += (cv - pr["l"])
                    re_cf += (pr["r"]*12 - (cv*(p_in["p_tax"]+p_in["p_maint"])) - (pr["r"]*12*p_in["p_mgmt"]))

            sal = (p_in["hp"] if age < p_in["hr"] else 0) + (p_in["yp"] if age < p_in["yr"] else 0)
            taxable = sal + max(0, re_cf) + (p_in["ss"] if age >= 67 else 0)
            tax = taxable * (p_in["tax_work"] if sal > 0 else p_in["tax_ret"])
            edu = (p_in["k1_cost"] if 18<=(age-32)<=22 else 0) + (p_in["k2_cost"] if 18<=(age-30)<=22 else 0)
            spend = (p_in["ew"] if age < p_in["yr"] else p_in["er"]) + edu
            gap = spend - (taxable - tax)
            
            draw401 = 0
            if gap > 0:
                fc = min(cc, gap); cc -= fc; gap -= fc
                if gap > 0:
                    d = min(cd, gap/(1-p_in["tax_ret"])); cd -= d; gap -= (d*(1-p_in["tax_ret"])); draw401 = d
            else: cc += abs(gap)
            
            cd *= (1+env["S"]); cc *= (1.02 if p_in["liq_strategy"]=="Hold/1031 (Step-up)" else (1+env["S"]))
            path.append({"Age": age, "NW": cc+cd+cr+re_eq, "CF": taxable-tax-spend, "Draw": draw401})
        all_runs.append(path)
    return all_runs

results = engine(inp, n_sims, use_monte)
nw_mat = np.array([[y["NW"] for y in path] for path in results])
p5, p50, p95 = np.percentile(nw_mat, [5, 50, 95], axis=0)
med_path = pd.DataFrame(results[len(results)//2])

# --- 4. DASHBOARD ---
st.title("🛡️ Legacy Master v22.0")

# Summary Metrics
c1, c2, c3, c4 = st.columns(4)
c1.metric("Median Estate", f"${p50[-1]:,.0f}")
c2.metric("Success Rate", f"{(nw_mat[:,-1] > 0).mean()*100:.0f}%")
c3.metric("Worst Case (5%)", f"${p5[-1]:,.0f}")
c4.metric("Strategy", inp["liq_strategy"])

# Main Chart (Bands + Ghosts)
fig = go.Figure()
fig.add_trace(go.Scatter(x=med_path["Age"], y=p95, line=dict(width=0), showlegend=False))
fig.add_trace(go.Scatter(x=med_path["Age"], y=p5, fill='tonexty', fillcolor='rgba(16,185,129,0.1)', name="90% Risk Band"))
for i in range(min(5, n_sims)):
    fig.add_trace(go.Scatter(x=med_path["Age"], y=nw_mat[i], line=dict(color="rgba(255,255,255,0.05)", width=1), showlegend=False))
fig.add_trace(go.Scatter(x=med_path["Age"], y=p50, line=dict(color="#10b981", width=4), name="Median NW"))
st.plotly_chart(fig, use_container_width=True)

# Cash Flow Chart
fig_cf = go.Figure()
fig_cf.add_trace(go.Bar(x=med_path["Age"], y=med_path["CF"], name="Annual Surplus/Deficit", marker_color="#3b82f6"))
fig_cf.add_trace(go.Bar(x=med_path["Age"], y=med_path["Draw"], name="401k Injection", marker_color="#f59e0b"))
fig_cf.update_layout(title="Annual Cash Flow Strategy", barmode='relative', template="plotly_dark")
st.plotly_chart(fig_cf, use_container_width=True)

st.download_button("📥 Save JSON", data=json.dumps(inp), file_name="scenario.json")
with st.expander("📊 Audit Log"): st.dataframe(med_path.style.format("{:,.0f}"))
