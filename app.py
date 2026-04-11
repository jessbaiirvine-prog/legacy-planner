import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import json

st.set_page_config(layout="wide", page_title="Legacy Master 24.0", page_icon="🏦")

# --- 1. SESSION STATE INITIALIZATION ---
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

# --- 2. SIDEBAR (THE LHS) ---
sb.title("💾 Data & Setup")
uploaded_file = sb.file_uploader("Upload Scenario", type="json")
if uploaded_file: inp.update(json.load(uploaded_file))

with sb.expander("🎲 Simulation Controls", expanded=True):
    use_monte = st.toggle("Monte Carlo Mode", value=True)
    n_sims = st.slider("Number of Simulations", 10, 2000, 500)
    inp["target_roi"] = st.slider("Target ROI %", 0.0, 15.0, float(inp.get("target_roi", 0.07)*100))/100

with sb.expander("🏠 Real Estate Engine", expanded=False):
    inp["liq_age"] = st.number_input("Global Liq Age", 45, 85, int(inp["liq_age"]))
    n_p = st.number_input("Property Count", 1, 10, len(inp["props"]))
    while len(inp["props"]) < n_p: inp["props"].append({"v": 1000000.0, "b": 800000.0, "l": 500000.0, "r": 4000.0, "liq": False})
    inp["props"] = inp["props"][:n_p]
    for i, p in enumerate(inp["props"]):
        st.markdown(f"**Prop {i+1}**")
        p["v"], p["l"], p["r"] = st.number_input(f"Val {i+1}", value=float(p["v"]), key=f"v{i}"), st.number_input(f"Loan {i+1}", value=float(p["l"]), key=f"l{i}"), st.number_input(f"Rent {i+1}", value=float(p["r"]), key=f"r{i}")
        p["liq"] = st.checkbox(f"Sell at {inp['liq_age']}?", value=p.get("liq", False), key=f"liq{i}")

with sb.expander("💵 Income & Expenses (LHS)", expanded=True):
    st.subheader("Inflow")
    inp["hp"] = st.number_input("Husband Salary", value=float(inp["hp"]))
    inp["yp"] = st.number_input("Your Salary", value=float(inp["yp"]))
    inp["ss"] = st.number_input("Social Security (67+)", value=float(inp["ss"]))
    st.subheader("Outflow")
    inp["ew"] = st.number_input("Working Expenses", value=float(inp["ew"]))
    inp["er"] = st.number_input("Retirement Expenses", value=float(inp["er"]))
    inp["k1_cost"] = st.number_input("Aaron College", value=float(inp["k1_cost"]))
    inp["k2_cost"] = st.number_input("Alvin College", value=float(inp["k2_cost"]))

# --- 3. MATH ENGINE ---
@st.cache_data
def run_engine(p_in, sims, monte):
    hist = [{"S": 0.12, "R": 0.04}, {"S": -0.15, "R": -0.05}, {"S": 0.04, "R": 0.02}]
    all_runs = []
    for _ in range(sims):
        cc, cd, cr = p_in["v_c"], p_in["v_d"], p_in["v_r"]
        props = [pr.copy() for pr in p_in["props"]]
        path = []
        for age in range(p_in["ca"], p_in["ea"] + 1):
            h = age - p_in["ca"]
            env = np.random.choice(hist) if monte else {"S": p_in["target_roi"], "R": 0.03}
            # Liquidation
            if age == p_in["liq_age"]:
                for pr in props:
                    if pr.get("liq") and pr["v"] > 0:
                        fv = pr["v"]*(1.03**h)
                        cc += (fv - pr["l"] - (max(0, fv-pr.get("b", 1000000))*p_in["cap_gains"])); pr["v"] = 0
            
            re_val, re_eq, re_cf = 0, 0, 0
            for pr in props:
                if pr["v"] > 0:
                    cv = pr["v"]*(1.03**h); re_val += cv; re_eq += (cv-pr["l"])
                    re_cf += (pr["r"]*12 - (cv*(p_in["p_tax"]+p_in["p_maint"])) - (pr["r"]*12*p_in["p_mgmt"]))

            sal = (p_in["hp"] if age < p_in["hr"] else 0) + (p_in["yp"] if age < p_in["yr"] else 0)
            taxable = sal + max(0, re_cf) + (p_in["ss"] if age >= 67 else 0)
            tax = taxable * (p_in["tax_work"] if sal > 0 else p_in["tax_ret"])
            edu = (p_in["k1_cost"] if 18<=(age-32)<=22 else 0) + (p_in["k2_cost"] if 18<=(age-30)<=22 else 0)
            spend = (p_in["ew"] if (age < p_in["yr"] or age < p_in["hr"]) else p_in["er"]) + edu
            
            draw = 0
            net_flow = (taxable - tax) - spend
            if net_flow < 0:
                gap = abs(net_flow)
                fc = min(cc, gap); cc -= fc; gap -= fc
                if gap > 0:
                    d = min(cd, gap/(1-p_in["tax_ret"])); cd -= d; draw = d
            else: cc += net_flow
            
            cd *= (1+env["S"]); cc *= 1.02
            path.append({"Age": age, "NW": cc+cd+cr+re_eq, "Sal": sal, "RE_NOI": re_cf, "Tax": -tax, "Spend": -spend, "Draw": draw, "RE_Val": re_val, "Liq": cc+cd+cr})
        all_runs.append(path)
    return all_runs

results = run_engine(inp, n_sims, use_monte)
nw_mat = np.array([[y["NW"] for y in path] for path in results])
p5, p50, p95 = np.percentile(nw_mat, [5, 50, 95], axis=0)
med_path = pd.DataFrame(results[len(results)//2])

# --- 4. RHS DASHBOARD ---
st.title("🛡️ Legacy Master v24.0")

# Summary Metrics (RHS Top)
m1, m2, m3, m4 = st.columns(4)
m1.metric("Median Estate", f"${p50[-1]:,.0f}")
m2.metric("Success Rate", f"{(nw_mat[:,-1] > 0).mean()*100:.1f}%")
m3.metric("Worst Case (5%)", f"${p5[-1]:,.0f}")
m4.metric("Simulations", n_sims)

# NW Probability Chart
fig_nw = go.Figure()
fig_nw.add_trace(go.Scatter(x=med_path["Age"], y=p5, line=dict(width=0), showlegend=False))
fig_nw.add_trace(go.Scatter(x=med_path["Age"], y=p95, fill='tonexty', fillcolor='rgba(16,185,129,0.1)', name="90% Risk Band"))
fig_nw.add_trace(go.Scatter(x=med_path["Age"], y=p50, line=dict(color="#10b981", width=4), name="Median Path"))
st.plotly_chart(fig_nw, use_container_width=True)

# Stacked Cash Flow + Net Curve
fig_cf = go.Figure()
for col, color, name in [("Sal", "#34d399", "Income"), ("RE_NOI", "#60a5fa", "Rent"), ("Tax", "#f87171", "Taxes"), ("Spend", "#fbbf24", "Expenses"), ("Draw", "#8b5cf6", "401k Draw")]:
    fig_cf.add_trace(go.Bar(x=med_path["Age"], y=med_path[col], name=name, marker_color=color))
fig_cf.add_trace(go.Scatter(x=med_path["Age"], y=med_path["Sal"]+med_path["RE_NOI"]+med_path["Tax"]+med_path["Spend"], name="Net Flow", line=dict(color="white", width=2, dash='dot')))
fig_cf.update_layout(barmode='relative', title="Annual Cash Flow Breakdown", template="plotly_dark")
st.plotly_chart(fig_cf, use_container_width=True)

# Asset/Equity Chart
fig_eq = go.Figure()
fig_eq.add_trace(go.Bar(x=med_path["Age"], y=med_path["RE_Val"], name="RE Asset Value", marker_color="#1e40af"))
fig_eq.add_trace(go.Bar(x=med_path["Age"], y=med_path["Liq"], name="Liquid Assets", marker_color="#047857"))
fig_eq.add_trace(go.Scatter(x=med_path["Age"], y=med_path["NW"], name="Total Net Worth", line=dict(color="#fbbf24", width=3)))
fig_eq.update_layout(barmode='stack', title="Asset Composition vs. Net Worth", template="plotly_dark")
st.plotly_chart(fig_eq, use_container_width=True)

st.download_button("📥 Save JSON", data=json.dumps(inp), file_name="scenario.json")
