import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import json

st.set_page_config(layout="wide", page_title="Legacy Master 40.0", page_icon="📈")

# --- 1. GLOBAL DEFAULTS & SCHEMA MIGRATION ---
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

# Data Integrity Check: Ensure no keys were lost during previous session errors
for p in inp["props"]:
    if "r" in p and "rent" not in p: p["rent"] = p.pop("r")
    for key, val in DEFAULT_PROP.items():
        if key not in p: p[key] = val

# --- 2. SIDEBAR: THE LHS (INPUTS) ---
sb = st.sidebar
sb.title("⚙️ Simulation LHS")
uploaded_file = sb.file_uploader("Upload Scenario JSON", type="json")
if uploaded_file:
    inp.update(json.load(uploaded_file))
    st.rerun()

with sb.expander("🎲 Market & Simulation Controls", expanded=True):
    n_sims = st.slider("Monte Carlo Iterations", 100, 2000, int(inp.get("n_sims", 500)))
    inp["target_roi"] = st.slider("Equities Target ROI %", 0, 15, int(inp["target_roi"]*100))/100
    inp["volatility"] = st.slider("Equities Volatility %", 0, 40, int(inp["volatility"]*100))/100
    inp["cash_roi"] = st.slider("Cash/HYSA Yield %", 0.0, 8.0, float(inp["cash_roi"]*100))/100
    inp["inflation"] = st.slider("Long-term Inflation %", 0.0, 10.0, float(inp["inflation"]*100))/100

with sb.expander("💰 Liquid Assets & Retirement", expanded=True):
    inp["v_401k"] = st.number_input("401k / IRA Balance", value=float(inp["v_401k"]), step=10000.0)
    inp["v_brokerage"] = st.number_input("Taxable Brokerage", value=float(inp["v_brokerage"]), step=10000.0)
    inp["v_cash"] = st.number_input("Liquid Cash / HYSA", value=float(inp["v_cash"]), step=5000.0)
    inp["v_residence"] = st.number_input("Primary Residence Value", value=float(inp["v_residence"]), step=50000.0)

with sb.expander("🏢 Real Estate Portfolio", expanded=True):
    n_p = st.number_input("Number of Properties", 1, 100, len(inp["props"]))
    while len(inp["props"]) < n_p: inp["props"].append(DEFAULT_PROP.copy())
    inp["props"] = inp["props"][:n_p]
    
    for i, p in enumerate(inp["props"]):
        st.markdown(f"---")
        st.subheader(f"Property {i+1}")
        p["v"] = st.number_input(f"Current Value ##{i+1}", value=float(p["v"]), key=f"v{i}")
        p["l"] = st.number_input(f"Current Loan ##{i+1}", value=float(p["l"]), key=f"l{i}")
        p["rent"] = st.number_input(f"Monthly Rent ##{i+1}", value=float(p["rent"]), key=f"r{i}")
        
        with st.expander(f"🛠️ P&L Details ##{i+1}"):
            c1, c2 = st.columns(2)
            p["rate"] = c1.number_input("Mortgage Rate %", 0.0, 15.0, float(p["rate"]*100), key=f"rt{i}")/100
            p["term"] = c2.number_input("Loan Term (Yrs)", 5, 40, int(p["term"]), key=f"tm{i}")
            p["tax_rate"] = c1.number_input("Prop Tax Rate %", 0.0, 4.0, float(p["tax_rate"]*100), key=f"tx{i}")/100
            p["ins"] = c2.number_input("Annual Insurance $", value=float(p["ins"]), key=f"in{i}")
            p["maint"] = c1.number_input("Maintenance % of Value", 0.0, 5.0, float(p["maint"]*100), key=f"mn{i}")/100
            p["mgmt"] = c2.number_input("Mgmt Fee % of Rent", 0.0, 20.0, float(p["mgmt"]*100), key=f"mg{i}")/100
            p["a"] = st.number_input("Annual Appreciation %", 0.0, 10.0, float(p["a"]*100), key=f"ap{i}")/100
            p["liq_active"] = st.checkbox("Liquidation Trigger", value=p["liq_active"], key=f"la{i}")
            p["liq_age"] = st.number_input("Sell at Age", 45, 95, int(p["liq_age"]), key=f"lage{i}")

with sb.expander("💵 Income, SS & Education", expanded=True):
    st.markdown("**Employment**")
    inp["hp"] = st.number_input("Husband Gross Salary", value=float(inp["hp"]))
    inp["hr"] = st.number_input("Husband Retirement Age", value=int(inp["hr"]))
    inp["yp"] = st.number_input("Your Gross Salary", value=float(inp["yp"]))
    inp["yr"] = st.number_input("Your Retirement Age", value=int(inp["yr"]))
    
    st.markdown("**Future Income**")
    inp["ss"] = st.number_input("Est. Total Social Security/yr", value=float(inp["ss"]))
    
    st.markdown("**Education Costs**")
    c1, c2 = st.columns(2)
    inp["k1_s_yr"] = c1.number_input("Aaron Start (Yr)", value=int(inp["k1_s_yr"]))
    inp["k1_e_yr"] = c2.number_input("Aaron End (Yr)", value=int(inp["k1_e_yr"]))
    inp["k2_s_yr"] = c1.number_input("Alvin Start (Yr)", value=int(inp["k2_s_yr"]))
    inp["k2_e_yr"] = c2.number_input("Alvin End (Yr)", value=int(inp["k2_e_yr"]))
    inp["k1_cost"] = st.number_input("Aaron Annual Cost $", value=float(inp["k1_cost"]))
    inp["k2_cost"] = st.number_input("Alvin Annual Cost $", value=float(inp["k2_cost"]))

with sb.expander("🛡️ Living Expenses", expanded=True):
    inp["ew"] = st.number_input("Current Yearly Living Expense", value=float(inp["ew"]))
    inp["er"] = st.number_input("Post-Retirement Expense", value=float(inp["er"]))
    inp["tax_work"] = st.slider("Work Tax Rate %", 10, 50, int(inp["tax_work"]*100))/100
    inp["tax_ret"] = st.slider("Retirement Tax Rate %", 10, 50, int(inp["tax_ret"]*100))/100

# --- 3. THE MATH ENGINE (SIMULATION) ---
@st.cache_data
def run_simulation(p_in, sims):
    results = []
    for _ in range(sims):
        cash, brok, ret = p_in["v_cash"], p_in["v_brokerage"], p_in["v_401k"]
        props = [pr.copy() for pr in p_in["props"]]
        path = []
        
        for age in range(p_in["ca"], p_in["ea"] + 1):
            year_idx = age - p_in["ca"]
            current_year = 2026 + year_idx
            
            # Market Returns
            eq_return = np.random.normal(p_in["target_roi"], p_in["volatility"])
            c_return = p_in["cash_roi"]
            
            # Real Estate P&L Logic
            total_re_val, total_re_eq, annual_re_noi, annual_mortgage = 0, 0, 0, 0
            for pr in props:
                if pr["v"] > 0:
                    # Amortization calculation
                    mi = pr["rate"] / 12
                    mt = pr["term"] * 12
                    pmt_mo = pr["l"] * (mi * (1 + mi)**mt) / ((1 + mi)**mt - 1) if pr["l"] > 0 else 0
                    
                    years_held = current_year - pr.get("p_year", 2020)
                    mos_passed = years_held * 12
                    
                    # Remaining Balance
                    if mos_passed < mt:
                        rem_bal = pr["l"] * ((1 + mi)**mt - (1 + mi)**mos_passed) / ((1 + mi)**mt - 1)
                        mortgage_ann = pmt_mo * 12
                    else:
                        rem_bal = 0
                        mortgage_ann = 0
                    
                    # Appreciation
                    cur_v = pr["v"] * ((1 + pr["a"])**year_idx)
                    
                    # Liquidation Check
                    if age == pr["liq_age"] and pr["liq_active"]:
                        proceeds = cur_v - rem_bal
                        tax_hit = max(0, (cur_v - pr.get("b", 1000000)) * p_in["cap_gains"])
                        cash += (proceeds - tax_hit)
                        pr["v"] = 0 # Property sold
                    else:
                        total_re_val += cur_v
                        total_re_eq += (cur_v - rem_bal)
                        
                        gross_rent = pr["rent"] * 12
                        ops_expenses = (cur_v * pr["tax_rate"]) + pr["ins"] + (cur_v * pr["maint"]) + (gross_rent * pr["mgmt"])
                        annual_re_noi += (gross_rent - ops_expenses - mortgage_ann)
                        annual_mortgage += mortgage_ann

            # Cash Flow Logic
            income_h = p_in["hp"] if age < p_in["hr"] else 0
            income_y = p_in["yp"] if age < p_in["yr"] else 0
            ss_income = p_in["ss"] if age >= 67 else 0
            
            gross_taxable = income_h + income_y + max(0, annual_re_noi) + ss_income
            effective_tax = gross_taxable * (p_in["tax_work"] if (income_h + income_y) > 0 else p_in["tax_ret"])
            
            # Inflation adjusted expenses
            edu_cost = 0
            if p_in["k1_s_yr"] <= current_year <= p_in["k1_e_yr"]: edu_cost += p_in["k1_cost"]
            if p_in["k2_s_yr"] <= current_year <= p_in["k2_e_yr"]: edu_cost += p_in["k2_cost"]
            
            base_spend = (p_in["ew"] if (age < p_in["hr"] or age < p_in["yr"]) else p_in["er"])
            inflated_spend = base_spend * ((1 + p_in["inflation"])**year_idx)
            
            total_outflow = inflated_spend + edu_cost + effective_tax
            net_cash_flow = gross_taxable - total_outflow
            
            # Withdrawal Sequence (Hierarchy: 1. Cash, 2. Brokerage, 3. 401k)
            draw_from_ret = 0
            if net_cash_flow < 0:
                deficit = abs(net_cash_flow)
                # Use Cash
                from_cash = min(cash, deficit)
                cash -= from_cash; deficit -= from_cash
                # Use Brokerage
                if deficit > 0:
                    from_brok = min(brok, deficit)
                    brok -= from_brok; deficit -= from_brok
                # Use 401k (Grossed for taxes)
                if deficit > 0:
                    draw_gross = deficit / (1 - p_in["tax_ret"])
                    actual_draw = min(ret, draw_gross)
                    ret -= actual_draw; draw_from_ret = actual_draw; deficit = 0
            else:
                cash += net_cash_flow

            # Growth
            brok *= (1 + eq_return)
            ret *= (1 + eq_return)
            cash *= (1 + c_return)
            
            path.append({
                "Age": age, "Year": current_year, "NW": cash + brok + ret + total_re_eq + p_in["v_residence"],
                "Liq": cash + brok + ret, "RE_Eq": total_re_eq, "NOI": annual_re_noi, 
                "Mortgage": annual_mortgage, "Draw": draw_from_ret, "Spend": inflated_spend, "Tax": effective_tax
            })
        results.append(path)
    return results

# --- 4. RHS: THE OUTPUT DASHBOARD ---
st.title("🛡️ Legacy Master v40.0: Wealth & Estate Advisory")

sim_data = run_simulation(inp, n_sims)
nw_curves = np.array([[yr["NW"] for yr in run] for run in sim_data])
p5, p50, p95 = np.percentile(nw_curves, [5, 50, 95], axis=0)
median_run = pd.DataFrame(sim_data[len(sim_data)//2])

# Summary Metrics
c1, c2, c3, c4 = st.columns(4)
c1.metric("Median Estate @ 95", f"${p50[-1]:,.0f}")
c2.metric("Success Rate", f"{(nw_curves[:,-1] > 0).mean()*100:.1f}%")
c3.metric("Worst-Case (5%)", f"${p5[-1]:,.0f}")
c4.metric("Peak RE Income", f"${median_run['NOI'].max():,.0f}/yr")

# Wealth Chart
st.plotly_chart(go.Figure([
    go.Scatter(x=median_run["Age"], y=p95, line=dict(width=0), showlegend=False),
    go.Scatter(x=median_run["Age"], y=p5, fill='tonexty', fillcolor='rgba(239, 68, 68, 0.15)', name="Downside Risk (5%)"),
    go.Scatter(x=median_run["Age"], y=p50, line=dict(color="#10b981", width=4), name="Median Forecast")
]).update_layout(title="Estate Value Probability (Net Worth)", template="plotly_dark", hovermode="x unified"), use_container_width=True)

# Real Estate Deep Dive
st.header("🏢 Real Estate Portfolio Health")
re_fig = go.Figure()
re_fig.add_trace(go.Bar(x=median_run["Age"], y=median_run["NOI"], name="Net Rental Cash Flow", marker_color="#34d399"))
re_fig.add_trace(go.Bar(x=median_run["Age"], y=-median_run["Mortgage"], name="Mortgage Debt Service", marker_color="#f87171"))
st.plotly_chart(re_fig.update_layout(barmode='relative', title="Net Rent vs Debt Service", template="plotly_dark"), use_container_width=True)

# Cash Flow Audit
st.header("📋 Cash Flow & Audit Trail")
cf_fig = go.Figure()
for col, color, lbl in [("Spend", "#fbbf24", "Expenses"), ("Tax", "#ef4444", "Taxes"), ("Draw", "#8b5cf6", "401k Withdrawals")]:
    cf_fig.add_trace(go.Scatter(x=median_run["Age"], y=median_run[col], name=lbl, fill='tozeroy', line=dict(color=color)))
st.plotly_chart(cf_fig.update_layout(title="Annual Outflows & Liquidity Relief", template="plotly_dark"), use_container_width=True)

# Diagnostic Recommendations
st.divider()
st.header("🧐 Strategic Diagnostic")
c1, c2 = st.columns(2)
with c1:
    st.subheader("🚩 Crisis Periods")
    crisis = median_run[median_run["Draw"] > 0]
    if not crisis.empty:
        st.error(f"Drawdown Detected: Ages {crisis['Age'].min()} to {crisis['Age'].max()}")
        st.write("This period requires 401k intervention to cover the tuition/retirement gap.")
    else:
        st.success("Your portfolio is currently self-funding in the median scenario.")

with c2:
    st.subheader("💡 Optimization Advice")
    if p5[-1] < 0:
        st.warning("Sequence of Returns Risk: In 5% of market crashes, your liquidity fails. Consider a larger cash bridge.")
    st.info("The mortgage burn-off in your mid-70s creates a significant surplus. Consider gifting or reinvesting during this phase.")

st.download_button("📥 Export Simulation Data (JSON)", data=json.dumps(inp), file_name="legacy_v40.json")
