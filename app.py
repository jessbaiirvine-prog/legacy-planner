import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import json
import re

st.set_page_config(layout="wide", page_title="Legacy Master 45.1", page_icon="📈")

# --- 1. THE V45.0 CORE SCHEMA & DEFAULTS ---
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

# --- 2. MATH ENGINE (v45 Core) ---
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
                        a_noi += (inf_rent-op_ex); a_mort += (pmt*12 if mos < mt else 0); t_re_eq += (cur_v-rem_l)
                        a_ncf += (inf_rent - op_ex - (pmt*12 if mos < mt else 0))

            # AI Logic (only active in AI runs)
            bonus = ai_overrides["bonus"] if (ai_overrides and ai_overrides["active"] and curr_yr >= ai_overrides["start_yr"]) else 0
            inc_h = p_in["hp"]*((1+p_in["salary_growth"])**year_idx) if age < p_in["hr"] else 0
            inc_y = p_in["yp"]*((1+p_in["salary_growth"])**year_idx) if age < p_in["yr"] else 0
            edu = (p_in["k1_cost"] if p_in["k1_s_yr"] <= curr_yr <= p_in["k1_e_yr"] else 0) + (p_in["k2_cost"] if p_in["k2_s_yr"] <= curr_yr <= p_in["k2_e_yr"] else 0)
            
            # Scenario specific: Bonus offsets education
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
            path.append({"Age": age, "Year": curr_yr, "NW": cash+brok+ret+t_re_eq+p_in["v_residence"], "NCF": a_ncf, "NOI": a_noi, "Debt": a_mort, "Spend": spend, "Tax": tax, "Salary": inc_h+inc_y, "SS": (p_in["ss"] if age >= 67 else 0), "Edu": edu, "Bonus": bonus})
        results.append(path)
    return results

# --- 3. FULL LHS SIDEBAR (V45 RESTORED) ---
sb = st.sidebar
sb.title("⚙️ Scenario Parameters")
with sb.expander("🎲 Market Risk & Macro", expanded=True):
    inp["n_sims"] = st.slider("Simulations", 100, 1000, int(inp["n_sims"]))
    inp["target_roi"] = st.slider("Equities ROI %", 0.0, 15.0, float(inp["target_roi"]*100))/100
    inp["volatility"] = st.slider("Volatility %", 0.0, 40.0, float(inp["volatility"]*100))/100
    inp["inflation"] = st.slider("Inflation %", 0.0, 10.0, float(inp["inflation"]*100))/100
    inp["salary_growth"] = st.slider("Salary Growth %", 0.0, 10.0, float(inp["salary_growth"]*100))/100

with sb.expander("💰 Balance Sheet", expanded=True):
    inp["v_401k"] = st.number_input("401k/IRA", value=float(inp["v_401k"]))
    inp["v_brokerage"] = st.number_input("Brokerage", value=float(inp["v_brokerage"]))
    inp["v_cash"] = st.number_input("Cash", value=float(inp["v_cash"]))
    inp["v_residence"] = st.number_input("Residence", value=float(inp["v_residence"]))

with sb.expander("🏠 Real Estate Assets", expanded=True):
    n_p = st.number_input("Properties", 1, 10, len(inp["props"]))
    while len(inp["props"]) < n_p: inp["props"].append(DEFAULT_PROP.copy())
    inp["props"] = inp["props"][:n_p]
    for i, p in enumerate(inp["props"]):
        st.markdown(f"**📍 Prop {i+1}**")
        p["v"] = st.number_input(f"Value ##{i}", value=float(p["v"]))
        p["l"] = st.number_input(f"Loan ##{i}", value=float(p["l"]))
        p["rent"] = st.number_input(f"Monthly Rent ##{i}", value=float(p["rent"]))
        p["is_california"] = st.checkbox("Prop 13 Cap", value=p["is_california"], key=f"c{i}")
        p["is_nnn"] = st.checkbox("NNN Lease", value=p["is_nnn"], key=f"n{i}")
        with st.expander(f"RE Advanced ##{i}"):
            p["rate"] = st.number_input("Mortgage %", 0.0, 10.0, float(p["rate"]*100), key=f"rt{i}")/100
            p["term"] = st.number_input("Term (Yrs)", 5, 40, int(p["term"]), key=f"tm{i}")
            p["a"] = st.number_input("Appreciation %", 0.0, 10.0, float(p["a"]*100), key=f"ap{i}")/100
            p["tax_rate"] = st.number_input("Tax Rate %", 0.0, 4.0, float(p["tax_rate"]*100), key=f"tx{i}")/100
            p["ins"] = st.number_input("Insurance $", value=float(p["ins"]), key=f"in{i}")
            p["maint"] = st.number_input("Maint %", 0.0, 5.0, float(p["maint"]*100), key=f"mn{i}")/100
            p["mgmt"] = st.number_input("Mgmt %", 0.0, 20.0, float(p["mgmt"]*100), key=f"mg{i}")/100
            p["liq_active"] = st.checkbox("Sell?", value=p["liq_active"], key=f"la{i}")
            p["liq_age"] = st.number_input("Sale Age", 45, 95, int(p["liq_age"]), key=f"lage{i}")

with sb.expander("💵 Income & Education", expanded=True):
    inp["hp"], inp["hr"] = st.number_input("Yichi Salary", value=float(inp["hp"])), st.number_input("Yichi Retire", value=int(inp["hr"]))
    inp["yp"], inp["yr"] = st.number_input("Lu Salary", value=float(inp["yp"])), st.number_input("Lu Retire", value=int(inp["yr"]))
    inp["ss"] = st.number_input("Est SS", value=float(inp["ss"]))
    c1, c2 = st.columns(2)
    inp["k1_cost"] = st.number_input("Aaron Cost", value=float(inp["k1_cost"]))
    inp["k2_cost"] = st.number_input("Alvin Cost", value=float(inp["k2_cost"]))

with sb.expander("🛡️ Expenses & Taxes", expanded=False):
    inp["ew"], inp["er"] = st.number_input("Working Exp", value=float(inp["ew"])), st.number_input("Retired Exp", value=float(inp["er"]))
    inp["tax_work"] = st.slider("Work Tax %", 10.0, 50.0, float(inp["tax_work"]*100))/100

# --- 4. RHS DASHBOARD (V45 Core Charts) ---
st.title("🛡️ Legacy Master v45.1: The Reality Engine")
sim_data = run_simulation(inp)
nw_curves = np.array([[yr["NW"] for yr in run] for run in sim_data])
p5, p50, p95 = np.percentile(nw_curves, [5, 50, 95], axis=0)
median_run = pd.DataFrame(sim_data[0])

m1, m2, m3, m4 = st.columns(4)
m1.metric("Median Estate @ 95", f"${p50[-1]:,.0f}")
m2.metric("Success Rate", f"{(nw_curves[:,-1] > 0).mean()*100:.1f}%")
m3.metric("Worst-Case (5%)", f"${p5[-1]:,.0f}")
m4.metric("Peak RE NCF", f"${median_run['NCF'].max():,.0f}/yr")

st.plotly_chart(go.Figure([
    go.Scatter(x=median_run["Age"], y=p95, line=dict(width=0), showlegend=False),
    go.Scatter(x=median_run["Age"], y=p5, fill='tonexty', fillcolor='rgba(239, 68, 68, 0.15)', name="Downside Risk (5%)"),
    go.Scatter(x=median_run["Age"], y=p50, line=dict(color="#10b981", width=4), name="Median Forecast")
]).update_layout(title="Estate Value Probability", template="plotly_dark"), use_container_width=True)

st.header("🏢 Real Estate & Cash Flow Deep Dive")
re_fig = go.Figure()
re_fig.add_trace(go.Bar(x=median_run["Age"], y=median_run["NOI"], name="True NOI", marker_color="#34d399"))
re_fig.add_trace(go.Bar(x=median_run["Age"], y=-median_run["Debt"], name="Debt Service", marker_color="#f87171"))
st.plotly_chart(re_fig.update_layout(barmode='relative', template="plotly_dark"), use_container_width=True)

# --- 5. STANDALONE AI SCENARIO LAB (BOTTOM SECTION) ---
st.divider()
st.header("🤖 AI Scenario Lab (Experimental)")
query = st.text_input("Ask a 'What-If' Scenario", placeholder="What if I earn an additional 50000 per year starting 2030?")

def ai_parse(user_query):
    overrides = {"bonus": 0, "start_yr": 9999, "active": False, "desc": ""}
    nums = re.findall(r'\d+', user_query.replace(',', ''))
    if any(x in user_query.lower() for x in ["additional", "earn", "salary"]):
        if len(nums) >= 2:
            val, yr = (float(nums[0]), int(nums[1])) if float(nums[0]) > 1000 else (float(nums[1]), int(nums[0]))
            overrides.update({"bonus": val, "start_yr": yr, "active": True, "desc": f"Testing ${val:,.0f}/yr extra income from {yr}"})
    return overrides

ai_res = ai_parse(query) if query else None

if ai_res and ai_res["active"]:
    ai_sim = run_simulation(inp, ai_overrides=ai_res)
    ai_nw = np.array([[yr["NW"] for yr in r] for r in ai_sim])
    ai_med = pd.DataFrame(ai_sim[0])
    
    st.info(f"**AI Mode Active:** {ai_res['desc']}")
    c1, c2 = st.columns(2)
    c1.metric("Scenario Estate Impact", f"+${ai_nw.mean(axis=0)[-1] - nw_curves.mean(axis=0)[-1]:,.0f}")
    
    # Comparison Chart
    comp = go.Figure()
    comp.add_trace(go.Scatter(x=median_run["Age"], y=nw_curves.mean(axis=0), name="Baseline v45.0", line=dict(color="gray", dash="dot")))
    comp.add_trace(go.Scatter(x=ai_med["Age"], y=ai_nw.mean(axis=0), name="Scenario Path", line=dict(color="#10b981", width=4)))
    st.plotly_chart(comp.update_layout(title="Wealth Gap: Baseline vs Scenario", template="plotly_dark"), use_container_width=True)
    
    # Logic Proof
    proof = go.Figure()
    proof.add_trace(go.Bar(x=ai_med["Age"], y=ai_med["Edu"], name="Tuition Liability", marker_color="#fbbf24"))
    proof.add_trace(go.Bar(x=ai_med["Age"], y=-ai_med["Bonus"], name="Scenario Income Offset", marker_color="#3b82f6"))
    st.plotly_chart(proof.update_layout(title="Logic Proof: How Income Offsets Education", barmode="relative", template="plotly_dark"), use_container_width=True)
else:
    st.write("The Scenario Lab is currently idle. Type a 'What-if' query above to run a side-by-side comparison.")
