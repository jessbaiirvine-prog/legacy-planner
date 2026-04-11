import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import json

st.set_page_config(layout="wide", page_title="Legacy Master 23.0")

# --- 1. INITIALIZATION ---
if "inputs" not in st.session_state:
    st.session_state.inputs = {
        "v_c": 200000.0, "v_d": 1200000.0, "v_r": 500000.0,
        "tax_work": 0.30, "tax_ret": 0.20, "cap_gains": 0.20, "target_roi": 0.07,
        "p_tax": 0.012, "p_maint": 0.01, "p_mgmt": 0.08,
        "liq_age": 55, "props": [{"v": 1700000.0, "b": 1000000.0, "l": 800000.0, "r": 6500.0, "liq": True}],
        "k1_cost": 40000.0, "k2_cost": 40000.0, "ca": 42, "ea": 95, 
        "hp": 145000.0, "hr": 58, "yp": 110000.0, "yr": 55, "ew": 150000.0, "er": 120000.0, "ss": 85000.0
    }

inp = st.session_state.inputs
sb = st.sidebar

# --- 2. SIDEBAR ---
with sb.expander("🎲 Simulations", expanded=True):
    use_monte = st.toggle("Monte Carlo", value=True)
    n_sims = st.slider("Sims", 10, 500, 100)
    inp["target_roi"] = st.slider("Market ROI %", 0.0, 15.0, float(inp.get("target_roi", 0.07)*100))/100

with sb.expander("🏠 Real Estate Portfolio", expanded=True):
    inp["liq_age"] = st.number_input("Liquidation Age", 45, 85, int(inp.get("liq_age", 55)))
    n_p = st.number_input("Property Count", 1, 10, len(inp["props"]))
    while len(inp["props"]) < n_p: inp["props"].append({"v": 1000000.0, "b": 800000.0, "l": 500000.0, "r": 4000.0, "liq": False})
    inp["props"] = inp["props"][:n_p]
    
    for i, p in enumerate(inp["props"]):
        st.markdown(f"--- **Property {i+1}** ---")
        p["v"] = st.number_input(f"Value {i+1}", value=float(p["v"]), key=f"v{i}")
        p["l"] = st.number_input(f"Loan {i+1}", value=float(p["l"]), key=f"l{i}")
        p["r"] = st.number_input(f"Rent {i+1}/mo", value=float(p["r"]), key=f"r{i}")
        p["liq"] = st.checkbox(f"Liquidate at age {inp['liq_age']}?", value=p.get("liq", False), key=f"liq{i}")

with sb.expander("👨‍👩‍👧‍👦 Household & Education", expanded=False):
    inp["hp"] = st.number_input("Husband Salary", value=float(inp["hp"]))
    inp["yp"] = st.number_input("Your Salary", value=float(inp["yp"]))
    inp["k1_cost"] = st.number_input("Aaron Tuition", value=float(inp["k1_cost"]))
    inp["k2_cost"] = st.number_input("Alvin Tuition", value=float(inp["k2_cost"]))

# --- 3. MATH ENGINE ---
@st.cache_data
def run_engine(p_in, sims, monte):
    hist = [{"S": 0.12, "R": 0.04}, {"S": -0.15, "R": -0.05}, {"S": 0.05, "R": 0.02}]
    all_runs = []
    for _ in range(sims):
        cc, cd, cr = p_in["v_c"], p_in["v_d"], p_in["v_r"]
        props = [pr.copy() for pr in p_in["props"]]
        path = []
        for age in range(p_in["ca"], p_in["ea"] + 1):
            h = age - p_in["ca"]; env = np.random.choice(hist) if monte else {"S": p_in["target_roi"], "R": 0.03}
            
            # Liquidation
            if age == p_in["liq_age"]:
                for pr in props:
                    if pr["liq"] and pr["v"] > 0:
                        fv = pr["v"]*(1.03**h); cc += (fv - pr["l"] - (max(0, fv-pr["b"])*p_in["cap_gains"])); pr["v"] = 0
            
            re_eq, re_cf, re_val = 0, 0, 0
            for pr in props:
                if pr["v"] > 0:
                    cv = pr["v"]*(1.03**h); re_val += cv; re_eq += (cv-pr["l"])
                    re_cf += (pr["r"]*12 - (cv*(p_in["p_tax"]+p_in["p_maint"])) - (pr["r"]*12*p_in["p_mgmt"]))

            sal = (p_in["hp"] if age < p_in["hr"] else 0) + (p_in["yp"] if age < p_in["yr"] else 0)
            taxable = sal + max(0, re_cf) + (p_in["ss"] if age >= 67 else 0)
            tax = taxable * (p_in["tax_work"] if sal > 0 else p_in["tax_ret"])
            edu = (p_in["k1_cost"] if 18<=(age-32)<=22 else 0) + (p_in["k2_cost"] if 18<=(age-30)<=22 else 0)
            spend = (p_in["ew"] if age < p_in["yr"] else p_in["er"]) + edu
            
            net_before_draw = (taxable - tax) - spend
            draw = 0
            if net_before_draw < 0:
                gap = abs(net_before_draw)
                fc = min(cc, gap); cc -= fc; gap -= fc
                if gap > 0:
                    d = min(cd, gap/(1-p_in["tax_ret"])); cd -= d; draw = d
            else: cc += net_before_draw
            
            cd *= (1+env["S"]); cc *= 1.02
            path.append({"Age": age, "NW": cc+cd+cr+re_eq, "Sal": sal, "RE_NOI": re_cf, "Tax": -tax, "Spend": -spend, "Draw": draw, "Equity": cc+cd+cr+re_eq, "RE_Val": re_val, "Liq_Assets": cc+cd+cr})
        all_runs.append(path)
    return all_runs

results = run_engine(inp, n_sims, use_monte)
med_path = pd.DataFrame(results[len(results)//2])

# --- 4. DASHBOARD ---
st.title("🛡️ Legacy Master v23.0")

# CHART 1: NET WORTH BANDS
fig_nw = go.Figure()
nw_mat = np.array([[y["NW"] for y in path] for path in results])
p5, p50, p95 = np.percentile(nw_mat, [5, 50, 95], axis=0)
fig_nw.add_trace(go.Scatter(x=med_path["Age"], y=p5, fill=None, line_color='rgba(0,0,0,0)', showlegend=False))
fig_nw.add_trace(go.Scatter(x=med_path["Age"], y=p95, fill='tonexty', fillcolor='rgba(16,185,129,0.1)', name="90% Confidence"))
fig_nw.add_trace(go.Scatter(x=med_path["Age"], y=p50, line=dict(color="#10b981", width=4), name="Median NW"))
st.plotly_chart(fig_nw, use_container_width=True)

# CHART 2: CATEGORICAL CASH FLOW + NET CURVE
fig_cf = go.Figure()
fig_cf.add_trace(go.Bar(x=med_path["Age"], y=med_path["Sal"], name="Salaries", marker_color="#34d399"))
fig_cf.add_trace(go.Bar(x=med_path["Age"], y=med_path["RE_NOI"], name="Rental NOI", marker_color="#60a5fa"))
fig_cf.add_trace(go.Bar(x=med_path["Age"], y=med_path["Tax"], name="Taxes", marker_color="#f87171"))
fig_cf.add_trace(go.Bar(x=med_path["Age"], y=med_path["Spend"], name="Expenses", marker_color="#fbbf24"))
fig_cf.add_trace(go.Bar(x=med_path["Age"], y=med_path["Draw"], name="401k Injection", marker_color="#8b5cf6"))
# The Net Curve
net_flow = med_path["Sal"] + med_path["RE_NOI"] + med_path["Tax"] + med_path["Spend"]
fig_cf.add_trace(go.Scatter(x=med_path["Age"], y=net_flow, name="Net Annual Flow", line=dict(color="#ffffff", width=2, dash='dot')))
fig_cf.update_layout(barmode='relative', title="Granular Cash Flow & Net Survival Curve", template="plotly_dark")
st.plotly_chart(fig_cf, use_container_width=True)

# CHART 3: ASSETS VS EQUITY
fig_eq = go.Figure()
fig_eq.add_trace(go.Bar(x=med_path["Age"], y=med_path["RE_Val"], name="Real Estate Assets", marker_color="#1e40af"))
fig_eq.add_trace(go.Bar(x=med_path["Age"], y=med_path["Liq_Assets"], name="Liquid Assets (Cash/401k)", marker_color="#047857"))
fig_eq.add_trace(go.Scatter(x=med_path["Age"], y=med_path["NW"], name="Total Equity (Net Worth)", line=dict(color="#fbbf24", width=3)))
fig_eq.update_layout(barmode='stack', title="Asset Composition vs. Net Equity", template="plotly_dark")
st.plotly_chart(fig_eq, use_container_width=True)

st.download_button("📥 Save Scenario", data=json.dumps(inp), file_name="scenario.json")
