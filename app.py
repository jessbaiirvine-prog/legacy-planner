import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import json

st.set_page_config(layout="wide", page_title="Legacy Master 45.0", page_icon="📈")

# --- 1. GLOBAL DEFAULTS & DEEP SCHEMA MIGRATION ---
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
    "ew": 180000.0, "er": 140000.0, "ss": 90000.0, "n_sims": 500
}

if "inputs" not in st.session_state:
    st.session_state.inputs = DEFAULTS.copy()

inp = st.session_state.inputs

for key, val in DEFAULTS.items():
    if key not in inp: inp[key] = val

for p in inp["props"]:
    if "r" in p and "rent" not in p: p["rent"] = p.pop("r") 
    for k_prop, v_prop in DEFAULT_PROP.items():
        if k_prop not in p: p[k_prop] = v_prop

# --- 2. SIDEBAR (LHS) ---
sb = st.sidebar
sb.title("⚙️ Scenario Parameters")
uploaded_file = sb.file_uploader("Upload Saved Scenario", type="json")
if uploaded_file:
    new_data = json.load(uploaded_file)
    for k, v in new_data.items(): inp[k] = v
    st.rerun()

with sb.expander("🎲 Market Risk & Macro", expanded=True):
    inp["n_sims"] = st.slider("Monte Carlo Iterations", 100, 2000, int(inp["n_sims"]))
    inp["target_roi"] = st.slider("Equities ROI %", 0.0, 15.0, float(inp["target_roi"]*100))/100
    inp["volatility"] = st.slider("Volatility %", 0.0, 40.0, float(inp["volatility"]*100))/100
    inp["cash_roi"] = st.slider("Cash Yield %", 0.0, 8.0, float(inp["cash_roi"]*100))/100
    st.markdown("---")
    inp["inflation"] = st.slider("Expense Inflation %", 0.0, 10.0, float(inp["inflation"]*100))/100
    inp["salary_growth"] = st.slider("Salary Growth %", 0.0, 10.0, float(inp["salary_growth"]*100))/100

with sb.expander("💰 Balance Sheet", expanded=True):
    inp["v_401k"] = st.number_input("401k/IRA Total", value=float(inp["v_401k"]), step=10000.0)
    inp["v_brokerage"] = st.number_input("Brokerage Account", value=float(inp["v_brokerage"]), step=10000.0)
    inp["v_cash"] = st.number_input("Total Cash", value=float(inp["v_cash"]), step=5000.0)
    inp["v_residence"] = st.number_input("Primary Residence Value", value=float(inp["v_residence"]), step=50000.0)

with sb.expander("🏠 Real Estate Assets", expanded=True):
    n_p = st.number_input("Property Count", 1, 50, len(inp["props"]))
    while len(inp["props"]) < n_p: inp["props"].append(DEFAULT_PROP.copy())
    inp["props"] = inp["props"][:n_p]
    
    for i, p in enumerate(inp["props"]):
        st.markdown(f"---")
        st.markdown(f"**📍 Property {i+1}**")
        p["v"] = st.number_input(f"Current Value ##{i+1}", value=float(p["v"]), key=f"v{i}")
        p["l"] = st.number_input(f"Loan Balance ##{i+1}", value=float(p["l"]), key=f"l{i}")
        p["rent"] = st.number_input(f"Monthly Rent ##{i+1}", value=float(p["rent"]), key=f"r{i}")
        
        with st.expander(f"⚙️ Details & Leases ##{i+1}"):
            c1, c2 = st.columns(2)
            p["is_california"] = c1.checkbox("Prop 13 Tax Cap", value=p.get("is_california", True), key=f"ca{i}")
            p["is_nnn"] = c2.checkbox("NNN Lease (Tenant pays OpEx)", value=p.get("is_nnn", False), key=f"nnn{i}")
            
            p["rate"] = c1.number_input("Mortgage Rate %", 0.0, 15.0, float(p["rate"]*100), key=f"rt{i}")/100
            p["term"] = c2.number_input("Loan Term (Yrs)", 5, 40, int(p["term"]), key=f"tm{i}")
            p["tax_rate"] = c1.number_input("Prop Tax Rate %", 0.0, 4.0, float(p["tax_rate"]*100), key=f"tx{i}")/100
            p["ins"] = c2.number_input("Annual Insurance $", value=float(p["ins"]), key=f"in{i}")
            p["maint"] = c1.number_input("Maintenance %", 0.0, 5.0, float(p["maint"]*100), key=f"mn{i}")/100
            p["mgmt"] = c2.number_input("Mgmt Fee %", 0.0, 20.0, float(p["mgmt"]*100), key=f"mg{i}")/100
            p["a"] = st.number_input("Appreciation %", 0.0, 10.0, float(p["a"]*100), key=f"ap{i}")/100
            p["liq_active"] = st.checkbox("Sell Property?", value=p["liq_active"], key=f"la{i}")
            p["liq_age"] = st.number_input("Target Sale Age", 45, 95, int(p["liq_age"]), key=f"lage{i}")

with sb.expander("💵 Income, SS & Education", expanded=True):
    st.markdown("**Employment Income**")
    inp["hp"], inp["hr"] = st.number_input("Yichi's Gross Salary", value=float(inp["hp"])), st.number_input("Yichi's Retire Age", value=int(inp["hr"]))
    inp["yp"], inp["yr"] = st.number_input("Lu's Gross Salary", value=float(inp["yp"])), st.number_input("Lu's Retire Age", value=int(inp["yr"]))
    
    st.markdown("**Social Security**")
    inp["ss"] = st.number_input("Est. Total SS/yr", value=float(inp["ss"]))
    
    st.markdown("**Education Costs**")
    c1, c2 = st.columns(2)
    inp["k1_s_yr"], inp["k1_e_yr"] = c1.number_input("Aaron Start", value=int(inp["k1_s_yr"])), c2.number_input("Aaron End", value=int(inp["k1_e_yr"]))
    inp["k1_cost"] = st.number_input("Aaron Annual Cost $", value=float(inp["k1_cost"]))
    inp["k2_s_yr"], inp["k2_e_yr"] = c1.number_input("Alvin Start", value=int(inp["k2_s_yr"])), c2.number_input("Alvin End", value=int(inp["k2_e_yr"]))
    inp["k2_cost"] = st.number_input("Alvin Annual Cost $", value=float(inp["k2_cost"]))

with sb.expander("🛡️ Living Expenses & Taxes", expanded=True):
    inp["ew"] = st.number_input("Current Yearly Living Expense", value=float(inp["ew"]))
    inp["er"] = st.number_input("Post-Retirement Expense", value=float(inp["er"]))
    inp["tax_work"] = st.slider("Work Tax Rate %", 10.0, 50.0, float(inp["tax_work"]*100))/100
    inp["tax_ret"] = st.slider("Retirement Tax Rate %", 10.0, 50.0, float(inp["tax_ret"]*100))/100

# --- 3. MATH ENGINE ---
def run_simulation(p_in):
    sims = int(p_in["n_sims"])
    results = []
    for _ in range(sims):
        cash, brok, ret = p_in["v_cash"], p_in["v_brokerage"], p_in["v_401k"]
        props = [pr.copy() for pr in p_in["props"]]
        path = []
        for age in range(p_in["ca"], p_in["ea"] + 1):
            year_idx = age - p_in["ca"]
            current_year = 2026 + year_idx
            
            eq_return = np.random.normal(p_in["target_roi"], p_in["volatility"])
            c_return = p_in["cash_roi"]
            
            total_re_val, total_re_eq, annual_true_noi, annual_mortgage, annual_ncf = 0, 0, 0, 0, 0
            
            for pr in props:
                if pr["v"] > 0:
                    mi, mt = pr["rate"] / 12, pr["term"] * 12
                    pmt_mo = pr["l"] * (mi * (1 + mi)**mt) / ((1 + mi)**mt - 1) if pr["l"] > 0 else 0
                    
                    mos_passed = (current_year - pr.get("p_year", 2024)) * 12
                    rem_bal = pr["l"] * ((1 + mi)**mt - (1 + mi)**mos_passed) / ((1 + mi)**mt - 1) if mos_passed < mt else 0
                    mortgage_ann = pmt_mo * 12 if mos_passed < mt else 0
                    
                    cur_v = pr["v"] * ((1 + pr["a"])**year_idx)
                    
                    if age == pr["liq_age"] and pr["liq_active"]:
                        proceeds = cur_v - rem_bal
                        tax_hit = max(0, (cur_v - pr.get("b", 1000000)) * p_in["cap_gains"])
                        cash += (proceeds - tax_hit)
                        pr["v"] = 0 
                    else:
                        total_re_val += cur_v
                        total_re_eq += (cur_v - rem_bal)
                        
                        # Apply Expense Inflation to Rent
                        inflated_rent = (pr["rent"] * 12) * ((1 + p_in["inflation"])**year_idx)
                        
                        # California Prop 13 Logic: Tax Assessed Value capped at 2% growth
                        if pr.get("is_california", True):
                            taxable_val = pr["v"] * ((1 + min(pr["a"], 0.02))**year_idx)
                        else:
                            taxable_val = cur_v
                            
                        # OpEx Calculation based on NNN Lease Status
                        if pr.get("is_nnn", False):
                            # Tenant pays taxes, insurance, and maintenance. Landlord only pays management.
                            ops_expenses = inflated_rent * pr["mgmt"]
                        else:
                            ops_expenses = (taxable_val * pr["tax_rate"]) + pr["ins"] + (cur_v * pr["maint"]) + (inflated_rent * pr["mgmt"])
                            
                        prop_noi = inflated_rent - ops_expenses
                        prop_ncf = prop_noi - mortgage_ann
                        
                        annual_true_noi += prop_noi
                        annual_mortgage += mortgage_ann
                        annual_ncf += prop_ncf

            # Apply Salary Growth (Compounding)
            income_h = p_in["hp"] * ((1 + p_in["salary_growth"])**year_idx) if age < p_in["hr"] else 0
            income_y = p_in["yp"] * ((1 + p_in["salary_growth"])**year_idx) if age < p_in["yr"] else 0
            ss_income = p_in["ss"] if age >= 67 else 0
            
            gross_taxable = income_h + income_y + max(0, annual_true_noi) + ss_income
            effective_tax = gross_taxable * (p_in["tax_work"] if (income_h + income_y) > 0 else p_in["tax_ret"])
            
            edu_cost = 0
            if p_in["k1_s_yr"] <= current_year <= p_in["k1_e_yr"]: edu_cost += p_in["k1_cost"]
            if p_in["k2_s_yr"] <= current_year <= p_in["k2_e_yr"]: edu_cost += p_in["k2_cost"]
            
            base_spend = (p_in["ew"] if (age < p_in["hr"] or age < p_in["yr"]) else p_in["er"])
            inflated_spend = base_spend * ((1 + p_in["inflation"])**year_idx)
            
            total_outflow = inflated_spend + edu_cost + effective_tax
            net_cash_flow = (income_h + income_y + ss_income + annual_ncf) - total_outflow
            
            draw_from_ret = 0
            if net_cash_flow < 0:
                deficit = abs(net_cash_flow)
                from_cash = min(cash, deficit)
                cash -= from_cash; deficit -= from_cash
                if deficit > 0:
                    from_brok = min(brok, deficit)
                    brok -= from_brok; deficit -= from_brok
                if deficit > 0:
                    draw_gross = deficit / (1 - p_in["tax_ret"])
                    actual_draw = min(ret, draw_gross)
                    ret -= actual_draw; draw_from_ret = actual_draw; deficit = 0
            else:
                cash += net_cash_flow

            brok *= (1 + eq_return); ret *= (1 + eq_return); cash *= (1 + c_return)
            
            path.append({
                "Age": age, "Year": current_year, "NW": cash + brok + ret + total_re_eq + p_in["v_residence"],
                "Liq": cash + brok + ret, "RE_Eq": total_re_eq, "NOI": annual_true_noi, 
                "NCF": annual_ncf, "Mortgage": annual_mortgage, "Draw": draw_from_ret, 
                "Spend": inflated_spend, "Tax": effective_tax, "Edu": edu_cost,
                "Salary": income_h + income_y, "SS": ss_income, "Organic_Net": net_cash_flow
            })
        results.append(path)
    return results

# --- 4. RHS DASHBOARD ---
st.title("🛡️ Legacy Master v45.0: The Reality Engine")

sim_data = run_simulation(inp)
nw_curves = np.array([[yr["NW"] for yr in run] for run in sim_data])
p5, p50, p95 = np.percentile(nw_curves, [5, 50, 95], axis=0)
median_run = pd.DataFrame(sim_data[len(sim_data)//2])

m1, m2, m3, m4 = st.columns(4)
m1.metric("Median Estate @ 95", f"${p50[-1]:,.0f}")
m2.metric("Success Rate", f"{(nw_curves[:,-1] > 0).mean()*100:.1f}%")
m3.metric("Worst-Case (5%)", f"${p5[-1]:,.0f}")
m4.metric("Peak RE NCF", f"${median_run['NCF'].max():,.0f}/yr")

# Chart 1: Wealth Probability
st.plotly_chart(go.Figure([
    go.Scatter(x=median_run["Age"], y=p95, line=dict(width=0), showlegend=False),
    go.Scatter(x=median_run["Age"], y=p5, fill='tonexty', fillcolor='rgba(239, 68, 68, 0.15)', name="Downside Risk (5%)"),
    go.Scatter(x=median_run["Age"], y=p50, line=dict(color="#10b981", width=4), name="Median Forecast")
]).update_layout(title="Estate Value Probability (Net Worth)", template="plotly_dark", hovermode="x unified"), use_container_width=True)

# Chart 2: Real Estate Deep Dive 
st.header("🏢 Commercial/Residential Cash Flow (NOI vs Debt)")
re_fig = go.Figure()
re_fig.add_trace(go.Bar(x=median_run["Age"], y=median_run["NOI"], name="True NOI (Rent - OpEx)", marker_color="#34d399"))
re_fig.add_trace(go.Bar(x=median_run["Age"], y=-median_run["Mortgage"], name="Debt Service", marker_color="#f87171"))
re_fig.add_trace(go.Scatter(x=median_run["Age"], y=median_run["NCF"], name="Net Cash Flow (NCF)", line=dict(color="white", width=3)))
st.plotly_chart(re_fig.update_layout(barmode='relative', title="Net Operating Income vs Debt Service", template="plotly_dark"), use_container_width=True)

# Chart 3: Baseline Liquidity Trail
st.header("📋 Baseline Liquidity Trail")
cf_fig = go.Figure()
for col, color, lbl in [("Spend", "#fbbf24", "Expenses (Inflated)"), ("Tax", "#ef4444", "Taxes"), ("Draw", "#8b5cf6", "401k/IRA Withdrawals")]:
    cf_fig.add_trace(go.Scatter(x=median_run["Age"], y=median_run[col], name=lbl, fill='tozeroy', line=dict(color=color)))
st.plotly_chart(cf_fig.update_layout(title="Annual Outflows & Liquidity Relief", template="plotly_dark"), use_container_width=True)

# Chart 4: Inflow vs Outflow
st.header("📊 Comprehensive Inflow vs Outflow")
io_fig = go.Figure()
io_fig.add_trace(go.Bar(x=median_run["Age"], y=median_run["Salary"], name="Salaries", marker_color="#10b981"))
io_fig.add_trace(go.Bar(x=median_run["Age"], y=median_run["SS"], name="Social Security", marker_color="#3b82f6"))
io_fig.add_trace(go.Bar(x=median_run["Age"], y=np.maximum(0, median_run["NCF"]), name="Positive RE NCF", marker_color="#06b6d4"))
io_fig.add_trace(go.Bar(x=median_run["Age"], y=-median_run["Spend"] - median_run["Edu"], name="Living & Edu Exp", marker_color="#fbbf24"))
io_fig.add_trace(go.Bar(x=median_run["Age"], y=-median_run["Tax"], name="Taxes", marker_color="#ef4444"))
io_fig.add_trace(go.Bar(x=median_run["Age"], y=np.minimum(0, median_run["NCF"]), name="Negative RE NCF", marker_color="#f97316"))
io_fig.add_trace(go.Scatter(x=median_run["Age"], y=median_run["Organic_Net"], name="Total Net Cash Flow", line=dict(color="white", width=3, dash="dot")))
st.plotly_chart(io_fig.update_layout(barmode='relative', title="Inflow vs Outflow with Net Cash Flow Trajectory", template="plotly_dark", hovermode="x unified"), use_container_width=True)

st.divider()
st.header("🧐 Strategic Diagnostic Advisory")
c1, c2 = st.columns(2)
with c1:
    st.subheader("🚩 Liquidity Drawdown Periods")
    crisis = median_run[median_run["Organic_Net"] < 0]
    if not crisis.empty:
        st.error(f"Negative Organic Cash Flow Detected: Ages {crisis['Age'].min()} to {crisis['Age'].max()}")
        st.write("During this period, organic cash flow (salaries + RE NCF + SS) is insufficient to cover inflated expenses, taxes, and tuition. The engine is successfully pulling liquidity from your cash, brokerage, and tax-deferred accounts.")
    else:
        st.success("✅ Portfolio is self-funding. Your cash flow completely covers your expenses without drawing down principal.")

with c2:
    st.subheader("💡 Optimization Opportunities")
    if p5[-1] < 0:
        st.warning("**Sequence of Returns Risk:** In 5% of our market simulations, you exhaust your liquid assets. Consider raising your cash reserve or reducing initial retirement spending.")
    st.info("**Mortgage Burn-off:** When your 30-year terms expire, required debt service drops to zero, creating a massive monthly surplus. Consider mapping out reinvestment vehicles for this capital block.")

st.download_button("📥 Export Simulation Data (JSON)", data=json.dumps(inp), file_name="legacy_v45_reality_engine.json")
