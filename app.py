import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import json
import re

st.set_page_config(layout="wide", page_title="Legacy Master 46.2", page_icon="🏦")

# --- 1. GLOBAL DEFAULTS & SCHEMA ---
DEFAULT_PROP = {
    "v": 1500000.0, "b": 1000000.0, "l": 800000.0, "p_year": 2024, "term": 30, "rate": 0.065, 
    "rent": 8500.0, "a": 0.04, "tax_rate": 0.012, "ins": 2500.0, "maint": 0.01, "mgmt": 0.05,
    "liq_age": 65, "liq_active": False, "is_california": True, "is_nnn": False
}

DEFAULTS = {
    "v_cash": 250000.0, "v_brokerage": 600000.0, "v_401k": 1500000.0, "v_residence": 2000000.0,
    "tax_work": 0.35, "tax_ret": 0.25, "cap_gains": 0.20, "inflation": 0.03, "salary_growth": 0.035,
    "target_roi": 0.08, "volatility": 0.15, "cash_roi": 0.04,
    "props": [DEFAULT_PROP.copy()],
    "k1_s_yr": 2038, "k1_e_yr": 2042, "k1_cost": 65000.0, 
    "k2_s_yr": 2040, "k2_e_yr": 2044, "k2_cost": 65000.0,
    "ca": 42, "ea": 95, "hp": 200000.0, "hr": 60, "yp": 250000.0, "yr": 55, 
    "ew": 180000.0, "er": 140000.0, "ss": 90000.0, "n_sims": 300
}

if "inputs" not in st.session_state:
    st.session_state.inputs = DEFAULTS.copy()
inp = st.session_state.inputs

# --- 2. AI INTERPRETER ---
def ai_interpret_scenario(user_query):
    overrides = {"bonus": 0, "start_yr": 9999, "active": False, "desc": ""}
    numbers = re.findall(r'\d+', user_query.replace(',', ''))
    if any(x in user_query.lower() for x in ["additional", "earn", "salary", "bonus", "extra"]):
        if len(numbers) >= 2:
            val, yr = (float(numbers[0]), int(numbers[1])) if float(numbers[0]) > 1000 else (float(numbers[1]), int(numbers[0]))
            overrides.update({"bonus": val, "start_yr": yr, "active": True, "desc": f"Added ${val:,.0f}/yr income from {yr}"})
    return overrides

# --- 3. MATH ENGINE ---
def run_simulation(p_in, ai_overrides=None):
    results = []
    for _ in range(int(p_in["n_sims"])):
        cash, brok, ret = p_in["v_cash"], p_in["v_brokerage"], p_in["v_401k"]
        props = [pr.copy() for pr in p_in["props"]]
        path = []
        for age in range(p_in["ca"], p_in["ea"] + 1):
            year_idx = age - p_in["ca"]
            curr_yr = 2026 + year_idx
            eq_ret = np.random.normal(p_in["target_roi"], p_in["volatility"])
            
            t_re_eq, a_noi, a_mort, a_ncf = 0, 0, 0, 0
            for pr in props:
                if pr["v"] > 0:
                    mi, mt = pr["rate"]/12, pr["term"]*12
                    pmt = pr["l"]*(mi*(1+mi)**mt)/((1+mi)**mt-1) if pr["l"]>0 else 0
                    mos = (curr_yr - pr.get("p_year", 2024))*12
                    rem_l = pr["l"]*((1+mi)**mt-(1+mi)**mos)/((1+mi)**mt-1) if mos < mt else 0
                    cur_v = pr["v"]*((1+pr["a"])**year_idx)
                    
                    if age == pr["liq_age"] and pr["liq_active"]:
                        cash += (cur_v - rem_l) - max(0, (cur_v - pr.get("b", 1000000)) * p_in["cap_gains"])
                        pr["v"] = 0
                    else:
                        inf_rent = (pr["rent"]*12)*((1+p_in["inflation"])**year_idx)
                        t_val = pr["v"]*((1.02)**year_idx) if pr.get("is_california") else cur_v
                        op_ex = inf_rent*pr["mgmt"] if pr.get("is_nnn") else (t_val*pr["tax_rate"])+pr["ins"]+(cur_v*pr["maint"])+(inf_rent*pr["mgmt"])
                        p_noi = inf_rent - op_ex
                        p_mort = pmt*12 if mos < mt else 0
                        a_noi += p_noi; a_mort += p_mort; a_ncf += (p_noi - p_mort); t_re_eq += (cur_v - rem_l)

            bonus = ai_overrides["bonus"] if (ai_overrides and ai_overrides["active"] and curr_yr >= ai_overrides["start_yr"]) else 0
            inc_h = p_in["hp"]*((1+p_in["salary_growth"])**year_idx) if age < p_in["hr"] else 0
            inc_y = p_in["yp"]*((1+p_in["salary_growth"])**year_idx) if age < p_in["yr"] else 0
            edu = (p_in["k1_cost"] if p_in["k1_s_yr"] <= curr_yr <= p_in["k1_e_yr"] else 0) + (p_in["k2_cost"] if p_in["k2_s_yr"] <= curr_yr <= p_in["k2_e_yr"] else 0)
            
            eff_edu = max(0, edu - bonus)
            un_bonus = max(0, bonus - edu)
            tax = (inc_h + inc_y + max(0, a_noi) + (p_in["ss"] if age >= 67 else 0) + un_bonus) * (p_in["tax_work"] if (inc_h+inc_y)>0 else p_in["tax_ret"])
            spend = (p_in["ew"] if (age < p_in["hr"] or age < p_in["yr"]) else p_in["er"]) * ((1+p_in["inflation"])**year_idx)
            
            ncf = (inc_h + inc_y + (p_in["ss"] if age >= 67 else 0) + a_ncf + un_bonus) - (spend + eff_edu + tax)
            if ncf < 0:
                defic = abs(ncf)
                f_c = min(cash, defic); cash -= f_c; defic -= f_c
                f_b = min(brok, defic); brok -= f_b; defic -= f_b
                if defic > 0: ret -= (defic/(1-p_in["tax_ret"])); ncf = 0
            else: cash += ncf

            brok *= (1+eq_ret); ret *= (1+eq_ret); cash *= (1+p_in["cash_roi"])
            path.append({"Age": age, "Year": curr_yr, "NW": cash+brok+ret+t_re_eq+p_in["v_residence"], "Liq": cash+brok+ret, "Edu": edu, "Bonus": bonus})
        results.append(path)
    return results

# --- 4. FULL LHS SIDEBAR (RESTORED) ---
sb = st.sidebar
sb.title("⚙️ Full Control Panel")
uploaded = sb.file_uploader("📂 Load Scenario", type="json")
if uploaded: st.session_state.inputs.update(json.load(uploaded)); st.rerun()

with sb.expander("🎲 Market Risk & Macro", expanded=True):
    inp["inflation"] = st.slider("Inflation %", 0.0, 8.0, float(inp["inflation"]*100))/100
    inp["salary_growth"] = st.slider("Salary Growth %", 0.0, 8.0, float(inp["salary_growth"]*100))/100
    inp["target_roi"] = st.slider("Equities ROI %", 0.0, 15.0, float(inp["target_roi"]*100))/100
    inp["volatility"] = st.slider("Volatility %", 0.0, 30.0, float(inp["volatility"]*100))/100
    inp["n_sims"] = st.number_input("Simulations", 50, 1000, int(inp["n_sims"]))

with sb.expander("💰 Balance Sheet", expanded=True):
    inp["v_401k"] = st.number_input("401k Total", value=float(inp["v_401k"]))
    inp["v_brokerage"] = st.number_input("Brokerage", value=float(inp["v_brokerage"]))
    inp["v_cash"] = st.number_input("Cash", value=float(inp["v_cash"]))
    inp["v_residence"] = st.number_input("Residence Value", value=float(inp["v_residence"]))

with sb.expander("🏠 Real Estate (Prop 13 & NNN)", expanded=True):
    n_p = st.number_input("Property Count", 1, 10, len(inp["props"]))
    while len(inp["props"]) < n_p: inp["props"].append(DEFAULT_PROP.copy())
    inp["props"] = inp["props"][:n_p]
    for i, p in enumerate(inp["props"]):
        st.markdown(f"**Property {i+1}**")
        p["v"], p["l"] = st.number_input(f"Value ##{i}", value=float(p["v"])), st.number_input(f"Loan ##{i}", value=float(p["l"]))
        p["rent"] = st.number_input(f"Monthly Rent ##{i}", value=float(p["rent"]))
        p["is_california"] = st.checkbox("Prop 13 Cap", value=p["is_california"], key=f"c{i}")
        p["is_nnn"] = st.checkbox("NNN Lease", value=p["is_nnn"], key=f"n{i}")
        with st.expander(f"Advanced RE Metrics ##{i}"):
            p["rate"] = st.number_input("Mortgage %", 0.0, 10.0, float(p["rate"]*100), key=f"r{i}")/100
            p["a"] = st.number_input("Appreciation %", 0.0, 10.0, float(p["a"]*100), key=f"a{i}")/100
            p["liq_active"] = st.checkbox("Sell Property?", value=p["liq_active"], key=f"s{i}")
            p["liq_age"] = st.number_input("Sale Age", 45, 95, int(p["liq_age"]), key=f"la{i}")

with sb.expander("💵 Income & Education", expanded=True):
    inp["hp"], inp["hr"] = st.number_input("Yichi Salary", value=float(inp["hp"])), st.number_input("Yichi Retire Age", value=int(inp["hr"]))
    inp["yp"], inp["yr"] = st.number_input("Lu Salary", value=float(inp["yp"])), st.number_input("Lu Retire Age", value=int(inp["yr"]))
    inp["k1_cost"], inp["k2_cost"] = st.number_input("Aaron Tuition", value=float(inp["k1_cost"])), st.number_input("Alvin Tuition", value=float(inp["k2_cost"]))

with sb.expander("🛡️ Living Expenses & Taxes", expanded=False):
    inp["ew"], inp["er"] = st.number_input("Working Expense", value=float(inp["ew"])), st.number_input("Retired Expense", value=float(inp["er"]))
    inp["tax_work"] = st.slider("Tax Rate %", 10.0, 50.0, float(inp["tax_work"]*100))/100

# --- 5. MAIN UI ---
st.title("🤖 AI Scenario Lab + Full Portfolio Engine")
query = st.text_input("Describe a 'What-If' Scenario", placeholder="e.g., What if I earn an extra 50000 starting 2030?")
ai_res = ai_interpret_scenario(query) if query else None

base_sim = run_simulation(inp)
base_nw = np.array([[yr["NW"] for yr in r] for r in base_sim])
base_med = pd.DataFrame(base_sim[0])

if ai_res and ai_res["active"]:
    ai_sim = run_simulation(inp, ai_overrides=ai_res)
    ai_nw = np.array([[yr["NW"] for yr in r] for r in ai_sim])
    ai_med = pd.DataFrame(ai_sim[0])
    st.success(f"**Scenario:** {ai_res['desc']}")
    c1, c2 = st.columns(2)
    c1.metric("Estate Delta", f"+${ai_nw.mean(axis=0)[-1] - base_nw.mean(axis=0)[-1]:,.0f}")
    a_b = ai_med[ai_med["Liq"] <= 0]["Year"].min()
    c2.metric("Burnout Year", "None" if pd.isna(a_b) else int(a_b))
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=base_med["Age"], y=base_nw.mean(axis=0), name="Baseline", line=dict(color="gray", dash="dot")))
    fig.add_trace(go.Scatter(x=ai_med["Age"], y=ai_nw.mean(axis=0), name="Scenario", line=dict(color="#10b981", width=4)))
    st.plotly_chart(fig.update_layout(title="Wealth Impact", template="plotly_dark"), use_container_width=True)
else:
    st.plotly_chart(go.Figure(go.Scatter(x=base_med["Age"], y=np.median(base_nw, axis=0), name="Median NW", line=dict(color="#10b981", width=4))).update_layout(title="Portfolio Forecast", template="plotly_dark"), use_container_width=True)

st.download_button("📥 Save All Parameters", data=json.dumps(inp), file_name="legacy_v46_2.json")
