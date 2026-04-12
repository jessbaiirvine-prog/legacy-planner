import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import json

st.set_page_config(layout="wide", page_title="Legacy Master 31.0", page_icon="🏠")

# --- 1. DEEP INITIALIZATION ---
DEFAULT_PROP = {
    "v": 1700000.0, "b": 1000000.0, "l": 800000.0, "p_year": 2020, 
    "term": 30, "rate": 0.045, "r": 6500.0, "a": 0.03, "liq_age": 55, "liq_active": True
}
DEFAULTS = {
    "v_c": 200000.0, "v_d": 1200000.0, "v_r": 500000.0,
    "tax_work": 0.30, "tax_ret": 0.20, "cap_gains": 0.20, "target_roi": 0.07, "volatility": 0.15,
    "p_tax": 0.012, "p_maint": 0.01, "p_mgmt": 0.08,
    "props": [DEFAULT_PROP.copy()],
    "k1_start": 18, "k1_end": 22, "k1_cost": 45000.0, 
    "k2_start": 18, "k2_end": 22, "k2_cost": 45000.0,
    "ca": 42, "ea": 95, "hp": 145000.0, "hr": 58, "yp": 110000.0, "yr": 55, 
    "ew": 150000.0, "er": 120000.0, "ss": 85000.0
}

if "inputs" not in st.session_state:
    st.session_state.inputs = DEFAULTS.copy()

inp = st.session_state.inputs
sb = st.sidebar

# --- 2. SIDEBAR (LHS) ---
sb.title("💾 Scenario Setup")
uploaded_file = sb.file_uploader("Upload Scenario", type="json")
if uploaded_file:
    inp.update(json.load(uploaded_file))
    st.rerun()

with sb.expander("🎲 Simulations & Market Risk", expanded=True):
    use_monte = st.toggle("Monte Carlo", value=True)
    n_sims = st.slider("Simulations", 10, 2000, 500)
    inp["target_roi"] = st.slider("Target ROI %", 0.0, 15.0, float(inp.get("target_roi", 0.07)*100))/100
    inp["volatility"] = st.slider("Market Volatility %", 5, 30, int(inp.get("volatility", 0.15)*100))/100

with sb.expander("🏠 Real Estate Engine", expanded=True):
    n_p = st.number_input("Property Count", 1, 10, len(inp["props"]))
    while len(inp["props"]) < n_p: inp["props"].append(DEFAULT_PROP.copy())
    inp["props"] = inp["props"][:n_p]
    for i, p in enumerate(inp["props"]):
        st.markdown(f"**Prop {i+1}**")
        p["v"] = st.number_input(f"Val {i+1}", value=float(p["v"]), key=f"v{i}")
        p["l"] = st.number_input(f"Loan {i+1}", value=float(p["l"]), key=f"l{i}")
        p["p_year"] = st.number_input(f"Yr Bought {i+1}", 1990, 2026, int(p.get("p_year", 2020)), key=f"py{i}")
        p["r"] = st.number_input(f"Rent {i+1}", value=float(p["r"]), key=f"rent{i}")
        c1, c2 = st.columns(2)
        p["liq_active"] = c1.checkbox("Sell?", value=p.get("liq_active", True), key=f"la{i}")
        p["liq_age"] = c2.number_input("Age", 45, 95, int(p.get("liq_age", 55)), key=f"lage{i}")

with sb.expander("💵 Income & Social Security", expanded=True):
    inp["hp"] = st.number_input("Husband Salary", value=float(inp["hp"]))
    inp["hr"] = st.number_input("Husband Retire Age", value=int(inp["hr"]))
    inp["yp"] = st.number_input("Your Salary", value=float(inp["yp"]))
    inp["yr"] = st.number_input("Your Retire Age", value=int(inp["yr"]))
    inp["ss"] = st.number_input("Annual Social Security", value=float(inp["ss"]))

with sb.expander("🛒 Lifestyle & Education", expanded=True):
    inp["ew"] = st.number_input("Work Lifestyle Spend", value=float(inp["ew"]))
    inp["er"] = st.number_input("Retire Lifestyle Spend", value=float(inp["er"]))
    st.markdown("---")
    inp["k1_cost"] = st.number_input("Aaron Tuition/yr", value=float(inp["k1_cost"]))
    inp["k2_cost"] = st.number_input("Alvin Tuition/yr", value=float(inp["k2_cost"]))

# --- 3. THE MATH ENGINE ---
@st.cache_data
def run_engine(p_in, sims, monte):
    all_runs = []
    for _ in range(sims):
        cc, cd, cr = p_in["v_c"], p_in["v_d"], p_in["v_r"]
        props = [pr.copy() for pr in p_in["props"]]
        path = []
        for age in range(p_in["ca"], p_in["ea"] + 1):
            h = age - p_in["ca"]; yr = 2026 + h
            market_return = np.random.normal(p_in["target_roi"], p_in["volatility"]) if monte else p_in["target_roi"]
            
            re_val, re_eq, re_cf = 0, 0, 0
            for pr in props:
                if pr["v"] > 0:
                    mi, mt = pr.get("rate", 0.045)/12, pr.get("term", 30)*12
                    pmt_mo = pr["l"] * (mi * (1 + mi)**mt) / ((1 + mi)**mt - 1) if pr["l"] > 0 else 0
                    mos_passed = (yr - pr.get("p_year", 2020)) * 12
                    rem_bal = pr["l"] * ((1 + mi)**mt - (1 + mi)**max(0, mos_passed)) / ((1 + mi)**mt - 1) if mos_passed < mt else 0
                    pmt_ann = (pmt_mo * 12) if mos_passed < mt else 0
                    cv = pr["v"] * ((1 + pr.get("a", 0.03))**h)
                    
                    if age == pr.get("liq_age", 55) and pr.get("liq_active"):
                        cc += (cv - rem_bal - (max(0, cv - pr.get("b", 1000000)) * p_in["cap_gains"])); pr["v"] = 0
                    else:
                        re_val += cv; re_eq += (cv - rem_bal)
                        re_cf += (pr["r"]*12) - (cv*(p_in["p_tax"]+p_in["p_maint"])) - (pr["r"]*12*p_in["p_mgmt"]) - pmt_ann

            sal = (p_in["hp"] if age < p_in["hr"] else 0) + (p_in["yp"] if age < p_in["yr"] else 0)
            taxable = sal + max(0, re_cf) + (p_in["ss"] if age >= 67 else 0)
            tax = taxable * (p_in["tax_work"] if sal > 0 else p_in["tax_ret"])
            edu = (p_in["k1_cost"] if p_in["k1_start"]<=(age-32)<=p_in["k1_end"] else 0) + (p_in["k2_cost"] if p_in["k2_start"]<=(age-30)<=p_in["k2_end"] else 0)
            spend = (p_in["ew"] if (age < p_in["yr"] or age < p_in["hr"]) else p_in["er"]) + edu
            net_flow = (taxable - tax) - spend
            
            draw = 0
            if net_flow < 0:
                gap = abs(net_flow); fc = min(cc, gap); cc -= fc; gap -= fc
                if gap > 0: d = min(cd, gap/(1-p_in["tax_ret"])); cd -= d; draw = d
            else: cc += net_flow

            cd *= (1 + market_return); cc *= 1.02
            path.append({"Age": age, "NW": cc+cd+cr+re_eq, "Sal": sal, "RE_NOI": re_cf, "Tax": -tax, "Spend": -spend, "Draw": draw, "RE_Val": re_val, "Liq": cc+cd+cr})
        all_runs.append(path)
    return all_runs

results = run_engine(inp, n_sims, use_monte)
nw_mat = np.array([[y["NW"] for y in path] for path in results])
p5, p50, p95 = np.percentile(nw_mat, [5, 50, 95], axis=0)
med_path = pd.DataFrame(results[len(results)//2])

# --- 4. RHS DASHBOARD ---
st.title("🛡️ Legacy Master v31.0")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Median Estate", f"${p50[-1]:,.0f}"); m2.metric("Success Rate", f"{(nw_mat[:,-1]>0).mean()*100:.1f}%"); m3.metric("Worst Case (5%)", f"${p5[-1]:,.0f}"); m4.metric("Simulations", n_sims)

st.plotly_chart(go.Figure([
    go.Scatter(x=med_path["Age"], y=p95, line=dict(width=0), showlegend=False),
    go.Scatter(x=med_path["Age"], y=p5, fill='tonexty', fillcolor='rgba(239, 68, 68, 0.15)', name="Downside Risk (5%)"),
    go.Scatter(x=med_path["Age"], y=p50, line=dict(color="#10b981", width=4), name="Median Estate Path")
]).update_layout(title="Wealth Probability (Pinned Logic)", template="plotly_dark"), use_container_width=True)

fig_cf = go.Figure()
for col, color, name in [("Sal", "#34d399", "Inflow"), ("RE_NOI", "#60a5fa", "Rent (Net)"), ("Tax", "#f87171", "Taxes"), ("Spend", "#fbbf24", "Expenses"), ("Draw", "#8b5cf6", "Withdrawals")]:
    fig_cf.add_trace(go.Bar(x=med_path["Age"], y=med_path[col], name=name, marker_color=color))
st.plotly_chart(fig_cf.update_layout(barmode='relative', title="Annual Cash Flow", template="plotly_dark"), use_container_width=True)

fig_eq = go.Figure()
fig_eq.add_trace(go.Bar(x=med_path["Age"], y=med_path["RE_Val"], name="RE Value", marker_color="#1e40af"))
fig_eq.add_trace(go.Bar(x=med_path["Age"], y=med_path["Liq"], name="Liquid", marker_color="#047857"))
fig_eq.add_trace(go.Scatter(x=med_path["Age"], y=med_path["NW"], name="Total Equity", line=dict(color="#fbbf24", width=3)))
st.plotly_chart(fig_eq.update_layout(barmode='stack', title="Asset Composition", template="plotly_dark"), use_container_width=True)

st.download_button("📥 Save JSON", data=json.dumps(inp), file_name="scenario.json")
