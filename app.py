import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import json

st.set_page_config(layout="wide", page_title="Legacy Master 41.0", page_icon="🛡️")

# --- 1. GLOBAL DEFAULTS & DEEP SCHEMA MIGRATION ---
DEFAULT_PROP = {
    "v": 1000000.0, "b": 800000.0, "l": 600000.0, "p_year": 2020, "term": 30, "rate": 0.045, 
    "rent": 5000.0, "a": 0.03, "tax_rate": 0.012, "ins": 1500.0, "maint": 0.01, "mgmt": 0.08,
    "liq_age": 65, "liq_active": False
}

DEFAULTS = {
    "v_cash": 200000.0, "v_brokerage": 500000.0, "v_401k": 1200000.0, "v_residence": 1500000.0,
    "tax_work": 0.30, "tax_ret": 0.20, "cap_gains": 0.20, "inflation": 0.025,
    "target_roi": 0.07, "volatility": 0.15, "cash_roi": 0.035,
    "props": [DEFAULT_PROP.copy()],
    "k1_s_yr": 2038, "k1_e_yr": 2042, "k1_cost": 50000.0, 
    "k2_s_yr": 2040, "k2_e_yr": 2044, "k2_cost": 50000.0,
    "ca": 42, "ea": 95, "hp": 145000.0, "hr": 58, "yp": 110000.0, "yr": 55, 
    "ew": 150000.0, "er": 120000.0, "ss": 85000.0, "n_sims": 500
}

if "inputs" not in st.session_state:
    st.session_state.inputs = DEFAULTS.copy()

inp = st.session_state.inputs

# CRITICAL: Deep Migration Fix for KeyError
# This block ensures every single key in DEFAULTS exists in st.session_state
for key, val in DEFAULTS.items():
    if key not in inp:
        inp[key] = val

for p in inp["props"]:
    if "r" in p and "rent" not in p: p["rent"] = p.pop("r") # Legacy key mapping
    for k_prop, v_prop in DEFAULT_PROP.items():
        if k_prop not in p: p[k_prop] = v_prop

# --- 2. SIDEBAR (LHS) ---
sb = st.sidebar
sb.title("💾 Legacy Controller")
uploaded_file = sb.file_uploader("Upload Saved Scenario", type="json")
if uploaded_file:
    try:
        new_data = json.load(uploaded_file)
        # Deep merge instead of direct update to prevent key loss
        for k, v in new_data.items():
            inp[k] = v
        st.success("Scenario Loaded! Keys migrated.")
        st.rerun()
    except Exception as e:
        st.error(f"Load Error: {e}")

with sb.expander("🎲 Market Risk & Simulation", expanded=True):
    n_sims = st.slider("Simulations", 100, 2000, int(inp["n_sims"]))
    inp["target_roi"] = st.slider("Equities ROI %", 0, 15, int(inp["target_roi"]*100))/100
    inp["volatility"] = st.slider("Volatility %", 0, 40, int(inp["volatility"]*100))/100
    inp["cash_roi"] = st.slider("Cash Yield %", 0.0, 8.0, float(inp["cash_roi"]*100))/100
    inp["inflation"] = st.slider("Inflation %", 0.0, 10.0, float(inp["inflation"]*100))/100

with sb.expander("💰 Balance Sheet", expanded=True):
    inp["v_401k"] = st.number_input("401k/IRA Total", value=float(inp["v_401k"]), step=10000.0)
    inp["v_brokerage"] = st.number_input("Brokerage Account", value=float(inp["v_brokerage"]), step=10000.0)
    inp["v_cash"] = st.number_input("Total Cash", value=float(inp["v_cash"]), step=5000.0)
    inp["v_residence"] = st.number_input("Home Equity/Value", value=float(inp["v_residence"]), step=50000.0)

with sb.expander("🏠 Real Estate Assets", expanded=True):
    n_p = st.number_input("Asset Count", 1, 100, len(inp["props"]))
    while len(inp["props"]) < n_p: inp["props"].append(DEFAULT_PROP.copy())
    inp["props"] = inp["props"][:n_p]
    
    for i, p in enumerate(inp["props"]):
        st.markdown(f"**Asset ##{i+1}**")
        p["v"] = st.number_input(f"Value ##{i+1}", value=float(p["v"]), key=f"v{i}")
        p["l"] = st.number_input(f"Loan ##{i+1}", value=float(p["l"]), key=f"l{i}")
        p["rent"] = st.number_input(f"Rent ##{i+1}", value=float(p["rent"]), key=f"r{i}")
        with st.expander(f"⚙️ P&L Details ##{i+1}"):
            c1, c2 = st.columns(2)
            p["rate"] = c1.number_input("Rate %", 0.0, 15.0, float(p["rate"]*100), key=f"rt{i}")/100
            p["term"] = c2.number_input("Term", 5, 40, int(p["term"]), key=f"tm{i}")
            p["tax_rate"] = c1.number_input("Tax %", 0.0, 4.0, float(p["tax_rate"]*100), key=f"tx{i}")/100
            p["ins"] = c2.number_input("Ins $", value=float(p["ins"]), key=f"in{i}")
            p["liq_active"] = st.checkbox("Sell?", value=p["liq_active"], key=f"la{i}")
            p["liq_age"] = st.number_input("Sale Age", 45, 95, int(p["liq_age"]), key=f"lage{i}")

with sb.expander("💵 Income & Education", expanded=True):
    inp["hp"], inp["hr"] = st.number_input("Husband Salary", value=float(inp["hp"])), st.number_input("Husband Retire Age", value=int(inp["hr"]))
    inp["yp"], inp["yr"] = st.number_input("Your Salary", value=float(inp["yp"])), st.number_input("Your Retire Age", value=int(inp["yr"]))
    st.divider()
    c1, c2 = st.columns(2)
    inp["k1_s_yr"], inp["k1_e_yr"] = c1.number_input("Aaron Start", value=int(inp["k1_s_yr"])), c2.number_input("Aaron End", value=int(inp["k1_e_yr"]))
    inp["k1_cost"] = st.number_input("Aaron Cost/yr", value=float(inp["k1_cost"]))
    inp["k2_s_yr"], inp["k2_e_yr"] = c1.number_input("Alvin Start", value=int(inp["k2_s_yr"])), c2.number_input("Alvin End", value=int(inp["k2_e_yr"]))
    inp["k2_cost"] = st.number_input("Alvin Cost/yr", value=float(inp["k2_cost"]))

# --- 3. MATH ENGINE ---
@st.cache_data
def run_simulation(p_in, sims):
    results = []
    for _ in range(sims):
        cash, brok, ret = p_in["v_cash"], p_in["v_brokerage"], p_in["v_401k"]
        props = [pr.copy() for pr in p_in["props"]]
        path = []
        for age in range(p_in["ca"], p_in["ea"] + 1):
            h, yr = age - p_in["ca"], 2026 + (age - p_in["ca"])
            m_ret = np.random.normal(p_in["target_roi"], p_in["volatility"])
            
            re_val, re_eq, re_noi, re_ds = 0, 0, 0, 0
            for pr in props:
                if pr["v"] > 0:
                    mi, mt = pr["rate"]/12, pr["term"]*12
                    pmt_mo = pr["l"] * (mi * (1 + mi)**mt) / ((1 + mi)**mt - 1) if pr["l"] > 0 else 0
                    mos_p = (yr - pr.get("p_year", 2020)) * 12
                    rem_bal = pr["l"] * ((1 + mi)**mt - (1 + mi)**max(0, mos_p)) / ((1 + mi)**mt - 1) if mos_p < mt else 0
                    cv = pr["v"] * ((1 + pr["a"])**h)
                    
                    if age == pr["liq_age"] and pr["liq_active"]:
                        cash += (cv - rem_bal - (max(0, cv - pr.get("b", 1000000)) * p_in["cap_gains"])); pr["v"] = 0
                    else:
                        re_val += cv; re_eq += (cv - rem_bal)
                        noi = (pr["rent"]*12) - (cv*pr["tax_rate"]) - pr["ins"] - (cv*pr["maint"]) - (pr["rent"]*12*pr["mgmt"])
                        ds = (pmt_mo * 12) if mos_p < mt else 0
                        re_noi += (noi - ds); re_ds += ds

            sal = (p_in["hp"] if age < p_in["hr"] else 0) + (p_in["yp"] if age < p_in["yr"] else 0)
            tax_inc = sal + max(0, re_noi) + (p_in["ss"] if age >= 67 else 0)
            tax = tax_inc * (p_in["tax_work"] if sal > 0 else p_in["tax_ret"])
            
            edu = (p_in["k1_cost"] if p_in["k1_s_yr"] <= yr <= p_in["k1_e_yr"] else 0) + (p_in["k2_cost"] if p_in["k2_s_yr"] <= yr <= p_in["k2_e_yr"] else 0)
            spend = (p_in["ew"] if (age < p_in["hr"] or age < p_in["yr"]) else p_in["er"]) * ((1 + p_in["inflation"])**h)
            net = (tax_inc - tax) - spend - edu
            
            draw = 0
            if net < 0:
                gap = abs(net)
                f_cash = min(cash, gap); cash -= f_cash; gap -= f_cash
                if gap > 0: f_brok = min(brok, gap); brok -= f_brok; gap -= f_brok
                if gap > 0: d = min(ret, gap / (1 - p_in["tax_ret"])); ret -= d; draw = d
            else: cash += net

            brok *= (1 + m_ret); ret *= (1 + m_ret); cash *= (1 + p_in["cash_roi"])
            path.append({"Age": age, "Year": yr, "NW": cash+brok+ret+re_eq+p_in["v_residence"], "RE_NOI": re_noi, "Draw": draw, "Liq": cash+brok+ret})
        results.append(path)
    return results

# --- 4. RHS DASHBOARD ---
st.title("🛡️ Legacy Master v41.0")
sim_data = run_simulation(inp, n_sims)
nw_curves = np.array([[yr["NW"] for yr in run] for run in sim_data])
p5, p50, p95 = np.percentile(nw_curves, [5, 50, 95], axis=0)
median_run = pd.DataFrame(sim_data[len(sim_data)//2])

m1, m2, m3, m4 = st.columns(4)
m1.metric("Median Estate", f"${p50[-1]:,.0f}"); m2.metric("Success Rate", f"{(nw_curves[:,-1]>0).mean()*100:.1f}%"); m3.metric("Crash Risk", f"${p5[-1]:,.0f}"); m4.metric("Sims", n_sims)

st.plotly_chart(go.Figure([
    go.Scatter(x=median_run["Age"], y=p95, line=dict(width=0), showlegend=False),
    go.Scatter(x=median_run["Age"], y=p5, fill='tonexty', fillcolor='rgba(239, 68, 68, 0.15)', name="Downside Risk"),
    go.Scatter(x=median_run["Age"], y=p50, line=dict(color="#10b981", width=4), name="Median Estate Forecast")
]).update_layout(title="Wealth Probability Analysis", template="plotly_dark"), use_container_width=True)

st.header("📊 Liquidity & Asset Breakdown")
c1, c2 = st.columns(2)
with c1:
    fig_liq = go.Figure()
    fig_liq.add_trace(go.Scatter(x=median_run["Age"], y=median_run["Liq"], fill='tozeroy', name="Liquid Reserves", line=dict(color="#60a5fa")))
    st.plotly_chart(fig_liq.update_layout(title="Total Cash/Brokerage/401k", template="plotly_dark"), use_container_width=True)
with c2:
    st.markdown("**Strategic Audit**")
    crisis = median_run[median_run["Draw"] > 0]
    if not crisis.empty: st.warning(f"Liquidity gap found between {crisis['Age'].min()} and {crisis['Age'].max()}.")
    else: st.success("Safe trajectory confirmed.")

st.download_button("📥 Export JSON", data=json.dumps(inp), file_name="legacy_v41.json")
