import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import json

st.set_page_config(layout="wide", page_title="Legacy Master 37.0", page_icon="💰")

# --- 1. GLOBAL DEFAULTS & PERSISTENCE ---
DEFAULT_PROP = {"v": 1700000.0, "b": 1000000.0, "l": 800000.0, "p_year": 2020, "term": 30, "rate": 0.045, "r": 6500.0, "a": 0.03, "liq_age": 55, "liq_active": True}
DEFAULTS = {
    "v_cash": 200000.0, "v_brokerage": 500000.0, "v_401k": 1200000.0,
    "tax_work": 0.30, "tax_ret": 0.20, "cap_gains": 0.20, "target_roi": 0.07, "volatility": 0.15,
    "p_tax": 0.012, "p_maint": 0.01, "p_mgmt": 0.08,
    "props": [DEFAULT_PROP.copy()],
    "k1_s_yr": 2038, "k1_e_yr": 2042, "k1_cost": 50000.0, 
    "k2_s_yr": 2040, "k2_e_yr": 2044, "k2_cost": 50000.0,
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

# Define n_sims and use_monte outside of expanders to ensure they are always initialized
n_sims = 500
use_monte = True

with sb.expander("📈 Investments & 401k", expanded=True):
    inp["v_401k"] = st.number_input("401k / Tax-Deferred", value=float(inp["v_401k"]))
    inp["v_brokerage"] = st.number_input("Brokerage (Taxable)", value=float(inp["v_brokerage"]))
    inp["v_cash"] = st.number_input("Cash / HYSA", value=float(inp["v_cash"]))
    st.markdown("---")
    use_monte = st.toggle("Monte Carlo Mode", value=True)
    n_sims = st.slider("Simulations", 10, 2000, 500)
    inp["target_roi"] = st.slider("Expected ROI %", 0, 15, int(inp.get("target_roi", 0.07)*100))/100
    inp["volatility"] = st.slider("Volatility %", 5, 30, int(inp.get("volatility", 0.15)*100))/100

with sb.expander("🏠 Real Estate Portfolio", expanded=True):
    n_p = st.number_input("Property Count", 1, 10, len(inp["props"]))
    while len(inp["props"]) < n_p: inp["props"].append(DEFAULT_PROP.copy())
    inp["props"] = inp["props"][:n_p]
    for i, p in enumerate(inp["props"]):
        st.markdown(f"**Prop {i+1}**")
        p["v"] = st.number_input(f"Value {i+1}", value=float(p["v"]), key=f"v{i}")
        p["l"] = st.number_input(f"Loan {i+1}", value=float(p["l"]), key=f"l{i}")
        p["rate"] = st.number_input(f"Rate % {i+1}", 0.1, 15.0, float(p.get("rate", 0.045)*100), key=f"r_rate{i}") / 100
        c1, c2 = st.columns(2)
        p["liq_active"] = c1.checkbox("Sell?", value=p.get("liq_active", True), key=f"la{i}")
        p["liq_age"] = c2.number_input("Age", 45, 95, int(p.get("liq_age", 55)), key=f"lage{i}")

with sb.expander("💵 Income & Retirement", expanded=True):
    inp["hp"] = st.number_input("Husband Salary", value=float(inp["hp"]))
    inp["hr"] = st.number_input("Husband Retire Age", value=int(inp["hr"]))
    inp["yp"] = st.number_input("Your Salary", value=float(inp["yp"]))
    inp["yr"] = st.number_input("Your Retire Age", value=int(inp["yr"]))
    inp["ss"] = st.number_input("Social Security/yr", value=float(inp["ss"]))

with sb.expander("🎓 Education Timing", expanded=True):
    c1, c2 = st.columns(2)
    inp["k1_s_yr"] = c1.number_input("Aaron Start", 2026, 2050, int(inp["k1_s_yr"]))
    inp["k1_e_yr"] = c2.number_input("Aaron End", 2026, 2060, int(inp["k1_e_yr"]))
    c3, c4 = st.columns(2)
    inp["k2_s_yr"] = c3.number_input("Alvin Start", 2026, 2050, int(inp["k2_s_yr"]))
    inp["k2_e_yr"] = c4.number_input("Alvin End", 2026, 2060, int(inp["k2_e_yr"]))
    inp["k1_cost"] = st.number_input("Aaron $/yr", value=float(inp["k1_cost"]))
    inp["k2_cost"] = st.number_input("Alvin $/yr", value=float(inp["k2_cost"]))
    st.markdown("---")
    inp["ew"] = st.number_input("Working Spend", value=float(inp["ew"]))
    inp["er"] = st.number_input("Retired Spend", value=float(inp["er"]))

# --- 3. MATH ENGINE ---
@st.cache_data
def run_engine(p_in, sims, monte):
    all_runs = []
    for _ in range(sims):
        cash, brok, ret = p_in["v_cash"], p_in["v_brokerage"], p_in["v_401k"]
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
                    cv = pr["v"] * ((1 + pr.get("a", 0.03))**h)
                    if age == pr.get("liq_age", 55) and pr.get("liq_active"):
                        cash += (cv - rem_bal - (max(0, cv - pr.get("b", 1000000)) * p_in["cap_gains"])); pr["v"] = 0
                    else:
                        re_val += cv; re_eq += (cv - rem_bal)
                        re_cf += (pr["r"]*12) - (cv*(p_in["p_tax"]+p_in["p_maint"])) - (pr["r"]*12*p_in["p_mgmt"]) - (pmt_mo * 12)

            sal = (p_in["hp"] if age < p_in["hr"] else 0) + (p_in["yp"] if age < p_in["yr"] else 0)
            taxable_inc = sal + max(0, re_cf) + (p_in["ss"] if age >= 67 else 0)
            tax = taxable_inc * (p_in["tax_work"] if sal > 0 else p_in["tax_ret"])
            edu = (p_in["k1_cost"] if p_in["k1_s_yr"] <= yr <= p_in["k1_e_yr"] else 0) + (p_in["k2_cost"] if p_in["k2_s_yr"] <= yr <= p_in["k2_e_yr"] else 0)
            spend = (p_in["ew"] if (age < p_in["yr"] or age < p_in["hr"]) else p_in["er"]) + edu
            net_flow = (taxable_inc - tax) - spend
            
            draw_401k = 0
            if net_flow < 0:
                gap = abs(net_flow)
                f_cash = min(cash, gap); cash -= f_cash; gap -= f_cash
                if gap > 0: f_brok = min(brok, gap); brok -= f_brok; gap -= f_brok
                if gap > 0:
                    d = min(ret, gap / (1 - p_in["tax_ret"])); ret -= d; draw_401k = d
            else: cash += net_flow

            brok *= (1 + market_return); ret *= (1 + market_return); cash *= 1.02
            path.append({"Age": age, "Year": yr, "NW": cash+brok+ret+re_eq, "Sal": sal, "RE_NOI": re_cf, "Tax": -tax, "Spend": -spend, "Draw": draw_401k, "Liq": cash+brok+ret})
        all_runs.append(path)
    return all_runs

# --- 4. RHS DASHBOARD ---
results = run_engine(inp, n_sims, use_monte)
nw_mat = np.array([[y["NW"] for y in path] for path in results])
p5, p50, p95 = np.percentile(nw_mat, [5, 50, 95], axis=0)
med_path = pd.DataFrame(results[len(results)//2])

st.title("🛡️ Legacy Master v37.0")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Median Estate", f"${p50[-1]:,.0f}"); m2.metric("Success Rate", f"{(nw_mat[:,-1]>0).mean()*100:.1f}%"); m3.metric("Worst Case (5%)", f"${p5[-1]:,.0f}"); m4.metric("Simulations", n_sims)

st.plotly_chart(go.Figure([
    go.Scatter(x=med_path["Age"], y=p95, line=dict(width=0), showlegend=False),
    go.Scatter(x=med_path["Age"], y=p5, fill='tonexty', fillcolor='rgba(239, 68, 68, 0.15)', name="Downside Risk (5%)"),
    go.Scatter(x=med_path["Age"], y=p50, line=dict(color="#10b981", width=4), name="Median Estate")
]).update_layout(title="Wealth Probability (Full Balance Sheet Engine)", template="plotly_dark"), use_container_width=True)

fig_cf = go.Figure()
for col, color, name in [("Sal", "#34d399", "Salary"), ("RE_NOI", "#60a5fa", "Rent (Net)"), ("Tax", "#f87171", "Taxes"), ("Spend", "#fbbf24", "Expenses/Education"), ("Draw", "#8b5cf6", "401k Draw")]:
    fig_cf.add_trace(go.Bar(x=med_path["Age"], y=med_path[col], name=name, marker_color=color))
st.plotly_chart(fig_cf.update_layout(barmode='relative', title="Annual Cash Flow Spikes", template="plotly_dark"), use_container_width=True)

# --- 5. AUDIT & DIAGNOSTIC ---
st.markdown("---")
st.header("📋 Financial Audit & Strategic Recommendation")
crisis = med_path[med_path["Draw"] > 0]
c1, c2 = st.columns(2)
with c1:
    st.subheader("🚩 Risk Analysis")
    if not crisis.empty:
        st.error(f"Drawdown detected: Ages {crisis['Age'].min()} to {crisis['Age'].max()}")
        st.write("This period corresponds to peak tuition costs while employment income has ceased.")
    else: st.success("Liquidity is stable in the median scenario.")
with c2:
    st.subheader("💡 Action Plan")
    st.write("1. **Sequence of Returns:** Protect the 401k engine; use the Brokerage/Cash buffers first.")
    st.write("2. **Asset Sale Timing:** Selling Property 1 early provides a significant liquidity bridge if market volatility hits.")

st.download_button("📥 Save JSON", data=json.dumps(inp), file_name="scenario.json")
