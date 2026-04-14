import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import json
import re

st.set_page_config(layout="wide", page_title="Legacy Master 46.1", page_icon="🏦")

# --- 1. GLOBAL DEFAULTS & PERSISTENCE ---
# These are the "Real Case" scenario defaults you requested
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
    """Parses user natural language into mathematical overrides."""
    overrides = {"bonus": 0, "start_yr": 9999, "active": False, "desc": ""}
    
    # Extract numerical values and years
    numbers = re.findall(r'\d+', user_query.replace(',', ''))
    
    # Logic for: "Additional Income" / "Salary Bump"
    if any(x in user_query.lower() for x in ["additional", "earn", "salary", "bonus", "extra"]):
        if len(numbers) >= 2:
            val = float(numbers[0])
            yr = int(numbers[1])
            # Basic validation to distinguish income from year
            if val < 1000: # Probably the year was first
                val, yr = float(numbers[1]), int(numbers[0])
            overrides["bonus"] = val
            overrides["start_yr"] = yr
            overrides["active"] = True
            overrides["desc"] = f"Adding ${val:,.0f}/yr additional income starting in {yr}."
            
    return overrides

# --- 3. THE COMPREHENSIVE MATH ENGINE ---
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
            
            # Market returns (Monte Carlo)
            eq_return = np.random.normal(p_in["target_roi"], p_in["volatility"])
            
            # Real Estate Module
            total_re_eq, ann_noi, ann_mort, ann_ncf = 0, 0, 0, 0
            for pr in props:
                if pr["v"] > 0:
                    mi, mt = pr["rate"]/12, pr["term"]*12
                    pmt = pr["l"]*(mi*(1+mi)**mt)/((1+mi)**mt-1) if pr["l"]>0 else 0
                    mos = (curr_yr - pr.get("p_year", 2024))*12
                    rem_l = pr["l"]*((1+mi)**mt-(1+mi)**mos)/((1+mi)**mt-1) if mos < mt else 0
                    cur_v = pr["v"]*((1+pr["a"])**year_idx)
                    
                    if age == pr["liq_age"] and pr["liq_active"]:
                        proceeds = cur_v - rem_l
                        tax_hit = max(0, (cur_v - pr.get("b", 1000000)) * p_in["cap_gains"])
                        cash += (proceeds - tax_hit)
                        pr["v"] = 0
                    else:
                        inf_rent = (pr["rent"]*12)*((1+p_in["inflation"])**year_idx)
                        t_val = pr["v"]*((1.02)**year_idx) if pr.get("is_california") else cur_v
                        
                        if pr.get("is_nnn"):
                            op_ex = inf_rent * pr["mgmt"]
                        else:
                            op_ex = (t_val*pr["tax_rate"]) + pr["ins"] + (cur_v*pr["maint"]) + (inf_rent*pr["mgmt"])
                        
                        p_noi = inf_rent - op_ex
                        p_mort = pmt*12 if mos < mt else 0
                        ann_noi += p_noi
                        ann_mort += p_mort
                        ann_ncf += (p_noi - p_mort)
                        total_re_eq += (cur_v - rem_l)

            # AI 'What-If' Injection
            bonus_income = ai_overrides["bonus"] if (ai_overrides and ai_overrides["active"] and curr_yr >= ai_overrides["start_yr"]) else 0

            # Salaries (with Appreciation)
            inc_h = p_in["hp"]*((1+p_in["salary_growth"])**year_idx) if age < p_in["hr"] else 0
            inc_y = p_in["yp"]*((1+p_in["salary_growth"])**year_idx) if age < p_in["yr"] else 0
            ss = p_in["ss"] if age >= 67 else 0
            
            # Education liability
            edu = 0
            if p_in["k1_s_yr"] <= curr_yr <= p_in["k1_e_yr"]: edu += p_in["k1_cost"]
            if p_in["k2_s_yr"] <= curr_yr <= p_in["k2_e_yr"]: edu += p_in["k2_cost"]
            
            # Apply Bonus to Education first (Tax-efficient netting simulation)
            effective_edu = max(0, edu - bonus_income)
            unused_bonus = max(0, bonus_income - edu)
            
            # Tax & Spend
            tax = (inc_h + inc_y + max(0, ann_noi) + ss + unused_bonus) * (p_in["tax_work"] if (inc_h+inc_y)>0 else p_in["tax_ret"])
            spend = (p_in["ew"] if (age < p_in["hr"] or age < p_in["yr"]) else p_in["er"]) * ((1+p_in["inflation"])**year_idx)
            
            # Final Cash Flow
            ncf = (inc_h + inc_y + ss + ann_ncf + unused_bonus) - (spend + effective_edu + tax)
            
            # Liquidity Algorithm
            if ncf < 0:
                deficit = abs(ncf)
                f_cash = min(cash, deficit); cash -= f_cash; deficit -= f_cash
                f_brok = min(brok, deficit); brok -= f_brok; deficit -= f_brok
                if deficit > 0:
                    draw = deficit/(1-p_in["tax_ret"]); ret -= draw; ncf = 0
            else:
                cash += ncf

            brok *= (1+eq_return); ret *= (1+eq_return); cash *= (1+p_in["cash_roi"])
            
            path.append({
                "Age": age, "Year": curr_yr, 
                "NW": cash+brok+ret+total_re_eq+p_in["v_residence"],
                "NCF": ncf, "Edu": edu, "Bonus": bonus_income, "Spend": spend,
                "Tax": tax, "Salary": inc_h + inc_y, "NOI": ann_noi, "Debt": ann_mort,
                "Liq": cash+brok+ret
            })
        results.append(path)
    return results

# --- 4. UI: SIDEBAR CONTROLS ---
sb = st.sidebar
sb.title("⚙️ Scenario Parameters")

with sb.expander("🎲 Market Risk & Macro", expanded=True):
    inp["inflation"] = st.slider("Expense Inflation %", 0.0, 10.0, float(inp["inflation"]*100))/100
    inp["salary_growth"] = st.slider("Salary Growth %", 0.0, 10.0, float(inp["salary_growth"]*100))/100
    inp["target_roi"] = st.slider("Equities ROI %", 0.0, 15.0, float(inp["target_roi"]*100))/100
    inp["volatility"] = st.slider("Volatility %", 0.0, 40.0, float(inp["volatility"]*100))/100

with sb.expander("🏠 Real Estate Assets", expanded=False):
    for i, p in enumerate(inp["props"]):
        st.markdown(f"**📍 Property {i+1}**")
        p["v"] = st.number_input(f"Value ##{i+1}", value=float(p["v"]), key=f"v{i}")
        p["rent"] = st.number_input(f"Monthly Rent ##{i+1}", value=float(p["rent"]), key=f"r{i}")
        p["is_california"] = st.checkbox("Prop 13 Cap", value=p.get("is_california", True), key=f"ca{i}")
        p["is_nnn"] = st.checkbox("NNN (Tenant OpEx)", value=p.get("is_nnn", False), key=f"nnn{i}")

with sb.expander("💵 Income & Education", expanded=False):
    inp["hp"] = st.number_input("Yichi Salary", value=float(inp["hp"]))
    inp["yp"] = st.number_input("Lu Salary", value=float(inp["yp"]))
    inp["k1_cost"] = st.number_input("Aaron Annual Tuition", value=float(inp["k1_cost"]))
    inp["k2_cost"] = st.number_input("Alvin Annual Tuition", value=float(inp["k2_cost"]))

# --- 5. MAIN DASHBOARD ---
st.title("🤖 AI Scenario Analyst")
query = st.text_input("Describe a 'What-If' Scenario", placeholder="e.g., What if I earn an additional 50000 per year starting 2030 to save for college?")

ai_res = ai_interpret_scenario(query) if query else None

# Run Engines
base_sim = run_simulation(inp)
base_nw_curves = np.array([[yr["NW"] for yr in r] for r in base_sim])
base_med = pd.DataFrame(base_sim[0])

if ai_res and ai_res["active"]:
    ai_sim = run_simulation(inp, ai_overrides=ai_res)
    ai_nw_curves = np.array([[yr["NW"] for yr in r] for r in ai_sim])
    ai_med = pd.DataFrame(ai_sim[0])
    
    st.success(f"**Scenario Active:** {ai_res['desc']}")
    
    # KPIs
    c1, c2, c3 = st.columns(3)
    diff = ai_nw_curves.mean(axis=0)[-1] - base_nw_curves.mean(axis=0)[-1]
    c1.metric("Estate Delta @ 95", f"+${diff:,.0f}")
    
    b_burn = base_med[base_med["Liq"] <= 0]["Year"].min()
    a_burn = ai_med[ai_med["Liq"] <= 0]["Year"].min()
    c2.metric("Baseline Burnout", "None" if pd.isna(b_burn) else int(b_burn))
    c3.metric("Scenario Burnout", "None" if pd.isna(a_burn) else int(a_burn), delta="IMPROVED" if (pd.isna(a_burn) and not pd.isna(b_burn)) or a_burn > b_burn else None)

    # Comparison Plot
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=base_med["Age"], y=base_nw_curves.mean(axis=0), name="Baseline", line=dict(color="gray", dash="dot")))
    fig.add_trace(go.Scatter(x=ai_med["Age"], y=ai_nw_curves.mean(axis=0), name="With Scenario", line=dict(color="#10b981", width=4)))
    st.plotly_chart(fig.update_layout(title="Wealth Accumulation Comparison", template="plotly_dark"), use_container_width=True)
    
    # Proof Plot
    proof = go.Figure()
    proof.add_trace(go.Bar(x=ai_med["Age"], y=ai_med["Edu"], name="Tuition Costs", marker_color="#fbbf24"))
    proof.add_trace(go.Bar(x=ai_med["Age"], y=-ai_med["Bonus"], name="Scenario Income Offset", marker_color="#3b82f6"))
    st.plotly_chart(proof.update_layout(title="Logic Proof: Income vs. Education Liability", barmode="relative", template="plotly_dark"), use_container_width=True)

else:
    # Standard Dashboard (v45 Charts)
    p50 = np.percentile(base_nw_curves, 50, axis=0)
    st.plotly_chart(go.Figure(go.Scatter(x=base_med["Age"], y=p50, name="Median NW", line=dict(color="#10b981", width=4))).update_layout(title="Median Net Worth Forecast", template="plotly_dark"), use_container_width=True)

    # Inflow/Outflow Deep Dive
    io = go.Figure()
    io.add_trace(go.Bar(x=base_med["Age"], y=base_med["Salary"], name="Salaries", marker_color="#10b981"))
    io.add_trace(go.Bar(x=base_med["Age"], y=base_med["NOI"], name="RE Income", marker_color="#06b6d4"))
    io.add_trace(go.Bar(x=base_med["Age"], y=-base_med["Spend"]-base_med["Edu"], name="Expenses & Edu", marker_color="#fbbf24"))
    io.add_trace(go.Bar(x=base_med["Age"], y=-base_med["Debt"], name="RE Mortgages", marker_color="#f87171"))
    st.plotly_chart(io.update_layout(barmode="relative", title="Annual Cash Flow Dynamics", template="plotly_dark"), use_container_width=True)

st.download_button("📥 Export Case Scenario (JSON)", data=json.dumps(inp), file_name="legacy_master_v46.json")
