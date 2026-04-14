import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import json
import re

st.set_page_config(layout="wide", page_title="Legacy Master 46.0", page_icon="🤖")

# --- 1. CORE DATA SCHEMA ---
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

# --- 2. THE AI INTERPRETER ENGINE ---
def ai_interpret_scenario(user_query):
    """
    In production, this would be an LLM API call.
    This logic-based parser handles the user's specific 'What If' request.
    """
    overrides = {"bonus": 0, "start_yr": 9999, "active": False, "desc": ""}
    
    # Extract numbers (e.g., 50000)
    numbers = re.findall(r'\d+', user_query.replace(',', ''))
    
    if "additional" in user_query.lower() or "earn" in user_query.lower():
        if len(numbers) >= 2:
            overrides["bonus"] = float(numbers[0])
            overrides["start_yr"] = int(numbers[1])
            overrides["active"] = True
            overrides["desc"] = f"Adding ${overrides['bonus']:,.0f}/yr income starting {overrides['start_yr']}"
    return overrides

# --- 3. UPDATED MATH ENGINE ---
def run_simulation(p_in, ai_overrides=None):
    sims = int(p_in["n_sims"])
    results = []
    for _ in range(sims):
        cash, brok, ret = p_in["v_cash"], p_in["v_brokerage"], p_in["v_401k"]
        props = [pr.copy() for pr in p_in["props"]]
        path = []
        for age in range(p_in["ca"], p_in["ea"] + 1):
            year_idx = age - p_in["ca"]
            curr_yr = 2026 + year_idx
            
            # Real Estate & Market Logic (Preserved from v45)
            eq_return = np.random.normal(p_in["target_roi"], p_in["volatility"])
            total_re_eq, ann_noi, ann_mort, ann_ncf = 0, 0, 0, 0
            for pr in props:
                if pr["v"] > 0:
                    mi, mt = pr["rate"]/12, pr["term"]*12
                    pmt = pr["l"]*(mi*(1+mi)**mt)/((1+mi)**mt-1) if pr["l"]>0 else 0
                    mos = (curr_yr - pr.get("p_year", 2024))*12
                    rem_l = pr["l"]*((1+mi)**mt-(1+mi)**mos)/((1+mi)**mt-1) if mos < mt else 0
                    cur_v = pr["v"]*((1+pr["a"])**year_idx)
                    
                    inf_rent = (pr["rent"]*12)*((1+p_in["inflation"])**year_idx)
                    t_val = pr["v"]*((1.02)**year_idx) if pr.get("is_california") else cur_v
                    op_ex = inf_rent*pr["mgmt"] if pr.get("is_nnn") else (t_val*pr["tax_rate"])+pr["ins"]+(cur_v*pr["maint"])+(inf_rent*pr["mgmt"])
                    
                    ann_noi += (inf_rent - op_ex)
                    ann_mort += (pmt*12 if mos < mt else 0)
                    ann_ncf += (inf_rent - op_ex - (pmt*12 if mos < mt else 0))
                    total_re_eq += (cur_v - rem_l)

            # AI Bonus Logic
            ai_bonus = ai_overrides["bonus"] if (ai_overrides and ai_overrides["active"] and curr_yr >= ai_overrides["start_yr"]) else 0

            # Income & Expenses
            inc_h = p_in["hp"]*((1+p_in["salary_growth"])**year_idx) if age < p_in["hr"] else 0
            inc_y = p_in["yp"]*((1+p_in["salary_growth"])**year_idx) if age < p_in["yr"] else 0
            ss = p_in["ss"] if age >= 67 else 0
            
            # Education Logic
            edu = 0
            if p_in["k1_s_yr"] <= curr_yr <= p_in["k1_e_yr"]: edu += p_in["k1_cost"]
            if p_in["k2_s_yr"] <= curr_yr <= p_in["k2_e_yr"]: edu += p_in["k2_cost"]
            
            # The 'Save for Education' Offset: The AI bonus reduces education liability first
            effective_edu = max(0, edu - ai_bonus)
            unused_bonus = max(0, ai_bonus - edu)
            
            tax = (inc_h + inc_y + max(0, ann_noi) + ss + unused_bonus) * (p_in["tax_work"] if (inc_h+inc_y)>0 else p_in["tax_ret"])
            spend = (p_in["ew"] if (age < p_in["hr"] or age < p_in["yr"]) else p_in["er"]) * ((1+p_in["inflation"])**year_idx)
            
            # Net Cash Flow Calculation
            ncf = (inc_h + inc_y + ss + ann_ncf + unused_bonus) - (spend + effective_edu + tax)
            
            # Liquidity Drawdown
            if ncf < 0:
                defic = abs(ncf)
                from_c = min(cash, defic); cash -= from_c; defic -= from_c
                from_b = min(brok, defic); brok -= from_b; defic -= from_b
                if defic > 0:
                    drw = defic/(1-p_in["tax_ret"]); ret -= drw; ncf = 0
            else:
                cash += ncf

            brok *= (1+eq_return); ret *= (1+eq_return); cash *= (1+p_in["cash_roi"])
            path.append({"Age": age, "Year": curr_yr, "NW": cash+brok+ret+total_re_eq+p_in["v_residence"], "NCF": ncf, "Edu": edu, "Bonus": ai_bonus})
        results.append(path)
    return results

# --- 4. UI LAYOUT ---
st.title("🤖 AI Scenario Analyst")
query = st.text_input("Ask a 'What-If' Scenario", placeholder="e.g., What if I earn an additional 50000 starting 2030 for education?")

ai_res = ai_interpret_scenario(query) if query else None

col_base, col_ai = st.columns(2)

# Run Baseline
base_data = run_simulation(inp)
base_nw = np.array([[yr["NW"] for yr in r] for r in base_data])
base_med = pd.DataFrame(base_data[0])

# Run AI Scenario
if ai_res and ai_res["active"]:
    ai_data = run_simulation(inp, ai_overrides=ai_res)
    ai_nw = np.array([[yr["NW"] for yr in r] for r in ai_data])
    ai_med = pd.DataFrame(ai_data[0])
    
    st.info(f"**AI Interpretation:** {ai_res['desc']}")
    
    # Delta Visualization
    diff = ai_nw.mean(axis=0)[-1] - base_nw.mean(axis=0)[-1]
    burnout_base = base_med[base_med["NW"] <= 0]["Year"].min()
    burnout_ai = ai_med[ai_med["NW"] <= 0]["Year"].min()

    c1, c2, c3 = st.columns(3)
    c1.metric("Estate Impact", f"+${diff:,.0f}")
    c2.metric("Baseline Burnout", "None" if pd.isna(burnout_base) else int(burnout_base))
    c3.metric("New Scenario Burnout", "None" if pd.isna(burnout_ai) else int(burnout_ai), delta="Resolved" if pd.isna(burnout_ai) and not pd.isna(burnout_base) else None)

    # Comparison Chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=base_med["Age"], y=base_nw.mean(axis=0), name="Baseline Net Worth", line=dict(color="gray", dash="dot")))
    fig.add_trace(go.Scatter(x=ai_med["Age"], y=ai_nw.mean(axis=0), name="Scenario Net Worth", line=dict(color="#10b981", width=4)))
    st.plotly_chart(fig.update_layout(title="Wealth Gap: Baseline vs. Scenario", template="plotly_dark"), use_container_width=True)

    # Logic Proof Chart
    proof = go.Figure()
    proof.add_trace(go.Bar(x=ai_med["Age"], y=ai_med["Edu"], name="Gross Edu Liability", marker_color="#fbbf24"))
    proof.add_trace(go.Bar(x=ai_med["Age"], y=-ai_med["Bonus"], name="AI Bonus Allocation", marker_color="#3b82f6"))
    st.plotly_chart(proof.update_layout(title="Proof: How Bonus Offsets Education", barmode="relative", template="plotly_dark"), use_container_width=True)
else:
    st.write("Enter a scenario above to begin calculation.")

st.divider()
st.subheader("⚙️ Primary Dashboard Control")
# (Rest of Sidebar and Charts from v45 go here...)
