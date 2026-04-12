import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import json

st.set_page_config(layout="wide", page_title="Legacy Master 39.0", page_icon="🏦")

# --- 1. GLOBAL DEFAULTS & MIGRATION ---
DEFAULT_PROP = {
    "v": 1000000.0, "b": 800000.0, "l": 600000.0, "p_year": 2020, "term": 30, "rate": 0.045, 
    "rent": 5000.0, "a": 0.03, "tax_rate": 0.012, "ins": 1500.0, "maint": 0.01, "mgmt": 0.08,
    "liq_age": 65, "liq_active": False
}
DEFAULTS = {
    "v_cash": 200000.0, "v_brokerage": 500000.0, "v_401k": 1200000.0,
    "tax_work": 0.30, "tax_ret": 0.20, "cap_gains": 0.20, "target_roi": 0.07, "volatility": 0.15,
    "props": [DEFAULT_PROP.copy()],
    "k1_s_yr": 2038, "k1_e_yr": 2042, "k1_cost": 50000.0, 
    "k2_s_yr": 2040, "k2_e_yr": 2044, "k2_cost": 50000.0,
    "ca": 42, "ea": 95, "hp": 145000.0, "hr": 58, "yp": 110000.0, "yr": 55, 
    "ew": 150000.0, "er": 120000.0, "ss": 85000.0
}

if "inputs" not in st.session_state:
    st.session_state.inputs = DEFAULTS.copy()

inp = st.session_state.inputs

# CRITICAL: Data Migration Layer
for p in inp["props"]:
    if "r" in p and "rent" not in p: p["rent"] = p.pop("r")
    for key, val in DEFAULT_PROP.items():
        if key not in p: p[key] = val

sb = st.sidebar
sb.title("💾 Scenario Setup")
uploaded_file = sb.file_uploader("Upload Scenario", type="json")
if uploaded_file:
    inp.update(json.load(uploaded_file))
    st.rerun()

# --- 2. SIDEBAR (LHS) ---
with sb.expander("📈 Portfolio & Risk", expanded=False):
    inp["v_401k"] = st.number_input("401k Balance", value=float(inp["v_401k"]))
    inp["v_brokerage"] = st.number_input("Brokerage", value=float(inp["v_brokerage"]))
    inp["v_cash"] = st.number_input("Cash", value=float(inp["v_cash"]))
    n_sims = st.slider("Simulations", 10, 1000, 500)
    inp["target_roi"] = st.slider("Market ROI %", 0, 15, int(inp.get("target_roi", 0.07)*100))/100

with sb.expander("🏠 Real Estate Engine", expanded=True):
    n_p = st.number_input("Properties", 1, 50, len(inp["props"]))
    while len(inp["props"]) < n_p: inp["props"].append(DEFAULT_PROP.copy())
    inp["props"] = inp["props"][:n_p]
    
    for i, p in enumerate(inp["props"]):
        st.markdown(f"**Asset {i+1}**")
        c1, c2, c3 = st.columns(3)
        p["v"] = c1.number_input(f"Value ##{i+1}", value=float(p["v"]), key=f"v{i}")
        p["l"] = c2.number_input(f"Loan ##{i+1}", value=float(p["l"]), key=f"l{i}")
        p["rent"] = c3.number_input(f"Rent/Mo ##{i+1}", value=float(p["rent"]), key=f"r{i}")
        
        with st.expander(f"Details ##{i+1}"):
            x1, x2, x3 = st.columns(3)
            p["rate"] = x1.number_input("Rate %", 0.1, 15.0, float(p["rate"]*100), key=f"rt{i}")/100
            p["tax_rate"] = x2.number_input("Tax %", 0.0, 3.0, float(p["tax_rate"]*100), key=f"tx{i}")/100
            p["ins"] = x3.number_input("Ins ($)", value=float(p["ins"]), key=f"in{i}")
            p["liq_active"] = st.checkbox("Sell?", value=p["liq_active"], key=f"la{i}")
            p["liq_age"] = st.number_input("Sale Age", 45, 95, int(p["liq_age"]), key=f"lage{i}")

with sb.expander("🎓 Education & Life", expanded=False):
    inp["hp"], inp["hr"] = st.number_input("Husband Salary", value=float(inp["hp"])), st.number_input("Husband Retire", value=int(inp["hr"]))
    inp["yp"], inp["yr"] = st.number_input("Your Salary", value=float(inp["yp"])), st.number_input("Your Retire", value=int(inp["yr"]))
    st.divider()
    inp["k1_s_yr"], inp["k1_e_yr"] = st.number_input("Aaron Start", value=int(inp["k1_s_yr"])), st.number_input("Aaron End", value=int(inp["k1_e_yr"]))
    inp["k2_s_yr"], inp["k2_e_yr"] = st.number_input("Alvin Start", value=int(inp["k2_s_yr"])), st.number_input("Alvin End", value=int(inp["k2_e_yr"]))

# --- 3. MATH ENGINE ---
@st.cache_data
def run_engine(p_in, sims):
    all_runs = []
    for _ in range(sims):
        cash, brok, ret = p_in["v_cash"], p_in["v_brokerage"], p_in["v_401k"]
        props = [pr.copy() for pr in p_in["props"]]
        path = []
        for age in range(p_in["ca"], p_in["ea"] + 1):
            h, yr = age - p_in["ca"], 2026 + (age - p_in["ca"])
            m_ret = np.random.normal(p_in["target_roi"], p_in["volatility"])
            
            re_val, re_eq, re_cf, re_ds = 0, 0, 0, 0
            for pr in props:
                if pr["v"] > 0:
                    mi, mt = pr["rate"]/12, pr["term"]*12
                    pmt_mo = pr["l"] * (mi * (1 + mi)**mt) / ((1 + mi)**mt - 1) if pr["l"] > 0 else 0
                    mos_passed = (yr - pr.get("p_year", 2020)) * 12
                    rem_bal = pr["l"] * ((1 + mi)**mt - (1 + mi)**max(0, mos_passed)) / ((1 + mi)**mt - 1) if mos_passed < mt else 0
                    cv = pr["v"] * ((1 + pr["a"])**h)
                    
                    if age == pr["liq_age"] and pr["liq_active"]:
                        cash += (cv - rem_bal - (max(0, cv - pr.get("b", 1000000)) * p_in["cap_gains"])); pr["v"] = 0
                    else:
                        re_val += cv; re_eq += (cv - rem_bal)
                        noi = (pr["rent"]*12) - (cv*pr["tax_rate"]) - pr["ins"] - (cv*pr["maint"]) - (pr["rent"]*12*pr["mgmt"])
                        ds = (pmt_mo * 12) if mos_passed < mt else 0
                        re_cf += (noi - ds); re_ds += ds

            sal = (p_in["hp"] if age < p_in["hr"] else 0) + (p_in["yp"] if age < p_in["yr"] else 0)
            tax_inc = sal + max(0, re_cf) + (p_in["ss"] if age >= 67 else 0)
            tax = tax_inc * (p_in["tax_work"] if sal > 0 else p_in["tax_ret"])
            edu = (p_in["k1_cost"] if p_in["k1_s_yr"] <= yr <= p_in["k1_e_yr"] else 0) + (p_in["k2_cost"] if p_in["k2_s_yr"] <= yr <= p_in["k2_e_yr"] else 0)
            spend = (p_in["ew"] if (age < p_in["yr"] or age < p_in["hr"]) else p_in["er"]) + edu
            net = (tax_inc - tax) - spend
            
            draw = 0
            if net < 0:
                gap = abs(net)
                f_cash = min(cash, gap); cash -= f_cash; gap -= f_cash
                if gap > 0: f_brok = min(brok, gap); brok -= f_brok; gap -= f_brok
                if gap > 0: d = min(ret, gap / (1 - p_in["tax_ret"])); ret -= d; draw = d
            else: cash += net

            brok *= (1 + m_ret); ret *= (1 + m_ret); cash *= 1.02
            path.append({"Age": age, "Year": yr, "NW": cash+brok+ret+re_eq, "RE_NOI": re_cf, "RE_DS": re_ds, "Draw": draw, "Liq": cash+brok+ret})
        all_runs.append(path)
    return all_runs

# --- 4. RHS DASHBOARD ---
results = run_engine(inp, n_sims)
nw_mat = np.array([[y["NW"] for y in path] for path in results])
p5, p50, p95 = np.percentile(nw_mat, [5, 50, 95], axis=0)
med_path = pd.DataFrame(results[len(results)//2])

st.title("🛡️ Legacy Master v39.0")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Median Estate", f"${p50[-1]:,.0f}"); m2.metric("Success Rate", f"{(nw_mat[:,-1]>0).mean()*100:.1f}%"); m3.metric("Year 1 Liquidity", f"${med_path['Liq'].iloc[0]:,.0f}"); m4.metric("Simulations", n_sims)

st.plotly_chart(go.Figure([
    go.Scatter(x=med_path["Age"], y=p95, line=dict(width=0), showlegend=False),
    go.Scatter(x=med_path["Age"], y=p5, fill='tonexty', fillcolor='rgba(239, 68, 68, 0.15)', name="Crash Risk"),
    go.Scatter(x=med_path["Age"], y=p50, line=dict(color="#10b981", width=4), name="Median Estate")
]).update_layout(title="Wealth Probability (Auto-Migration Active)", template="plotly_dark"), use_container_width=True)

# RE Portfolio Health
st.header("🏢 RE Portfolio Performance")
fig_re = go.Figure()
fig_re.add_trace(go.Scatter(x=med_path["Age"], y=med_path["RE_NOI"], name="Net Rental CF", line=dict(color="#34d399", width=3)))
fig_re.add_trace(go.Bar(x=med_path["Age"], y=med_path["RE_DS"], name="Mortgage Payment", marker_color="#f87171", opacity=0.5))
st.plotly_chart(fig_re.update_layout(title="Rent vs. Debt Service Over Time", template="plotly_dark"), use_container_width=True)

st.divider()
st.header("📋 Final Audit")
crisis = med_path[med_path["Draw"] > 0]
if not crisis.empty: st.error(f"🚩 Liquidity Gap: Ages {crisis['Age'].min()} to {crisis['Age'].max()} (Tuition + Retirement Transition)")
else: st.success("✅ Portfolio is self-sustaining.")

st.download_button("📥 Save JSON", data=json.dumps(inp), file_name="scenario.json")
