import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import json
import re

st.set_page_config(layout="wide", page_title="Legacy Master 45.3", page_icon="🏦")

# --- 1. THE V45.0 SOURCE DEFAULTS ---
# Re-establishing the high-fidelity property schema
DEFAULT_PROP = {
    "v": 1500000.0, "b": 1000000.0, "l": 800000.0, "p_year": 2024, "term": 30, "rate": 0.065, 
    "rent": 8500.0, "a": 0.04, "tax_rate": 0.012, "ins": 2500.0, "maint": 0.01, "mgmt": 0.05,
    "vacancy": 0.05, "liq_age": 65, "liq_active": False, "is_california": True, "is_nnn": False
}

DEFAULTS = {
    "v_cash": 250000.0, "v_brokerage": 600000.0, "v_401k": 1500000.0, "v_residence": 2000000.0,
    "tax_work": 0.35, "tax_ret": 0.25, "cap_gains": 0.20, "inflation": 0.03, "salary_growth": 0.035,
    "target_roi": 0.08, "volatility": 0.15, "cash_roi": 0.04, "ss_amt": 90000.0,
    "props": [DEFAULT_PROP.copy()],
    "k1_s_yr": 2038, "k1_e_yr": 2042, "k1_cost": 65000.0, 
    "k2_s_yr": 2040, "k2_e_yr": 2044, "k2_cost": 65000.0,
    "ca": 42, "ea": 95, "hp": 200000.0, "hr": 60, "yp": 250000.0, "yr": 55, 
    "ew": 180000.0, "er": 140000.0, "n_sims": 300
}

if "inputs" not in st.session_state:
    st.session_state.inputs = DEFAULTS.copy()
inp = st.session_state.inputs

# --- 2. THE PRODUCTION ENGINE (V45.0 CORE) ---
def run_v45_engine(p_in):
    """ 
    This is the original, verbose math loop. 
    No AI modifications or bonus logic is allowed inside this function.
    """
    all_results = []
    for _ in range(int(p_in["n_sims"])):
        # Initialize Balance Sheet
        curr_cash = p_in["v_cash"]
        curr_brok = p_in["v_brokerage"]
        curr_ret = p_in["v_401k"]
        residence_v = p_in["v_residence"]
        
        # Local copies of properties for liquidation tracking
        sim_props = [pr.copy() for pr in p_in["props"]]
        
        path = []
        for age in range(p_in["ca"], p_in["ea"] + 1):
            year_idx = age - p_in["ca"]
            curr_yr = 2026 + year_idx
            
            # 1. Market Growth (Monte Carlo)
            ann_market_return = np.random.normal(p_in["target_roi"], p_in["volatility"])
            
            # 2. Real Estate Cash Flow & Equity Calculation
            total_re_equity = 0
            total_ann_noi = 0
            total_ann_debt = 0
            total_ann_ncf = 0
            
            for p in sim_props:
                if p["v"] > 0:
                    # Mortgage Math (Verbose)
                    m_rate = p["rate"] / 12
                    m_term_mos = p["term"] * 12
                    pmt_mo = p["l"] * (m_rate * (1 + m_rate)**m_term_mos) / ((1 + m_rate)**m_term_mos - 1) if p["l"] > 0 else 0
                    
                    months_since_purchase = (curr_yr - p.get("p_year", 2024)) * 12
                    if months_since_purchase < m_term_mos:
                        rem_loan = p["l"] * ((1 + m_rate)**m_term_mos - (1 + m_rate)**months_since_purchase) / ((1 + m_rate)**m_term_mos - 1)
                        ann_mortgage = pmt_mo * 12
                    else:
                        rem_loan = 0
                        ann_mortgage = 0
                    
                    # Valuation & Rental Growth
                    prop_v_current = p["v"] * ((1 + p["a"])**year_idx)
                    gross_rent_ann = (p["rent"] * 12) * ((1 + p_in["inflation"])**year_idx)
                    
                    # Tax Assessment (Prop 13 vs Fair Market)
                    if p.get("is_california"):
                        assessment_v = p["v"] * ((1.02)**year_idx)
                    else:
                        assessment_v = prop_v_current
                    
                    # Liquidation Check
                    if age == p["liq_age"] and p["liq_active"]:
                        sale_proceeds = prop_v_current - rem_loan
                        tax_basis = p.get("b", p["v"])
                        capital_gains_tax = max(0, (prop_v_current - tax_basis) * p_in["cap_gains"])
                        curr_cash += (sale_proceeds - capital_gains_tax)
                        p["v"] = 0 # Property removed from portfolio
                    else:
                        # Expense Logic (NNN vs Gross)
                        if p.get("is_nnn"):
                            # Tenant pays Taxes, Ins, Maint. Landlord pays Mgmt + Vacancy
                            exp_mgmt = gross_rent_ann * p["mgmt"]
                            exp_vacancy = gross_rent_ann * p["vacancy"]
                            op_ex = exp_mgmt + exp_vacancy
                        else:
                            exp_taxes = assessment_v * p["tax_rate"]
                            exp_ins = p["ins"] * ((1 + p_in["inflation"])**year_idx)
                            exp_maint = prop_v_current * p["maint"]
                            exp_mgmt = gross_rent_ann * p["mgmt"]
                            exp_vacancy = gross_rent_ann * p["vacancy"]
                            op_ex = exp_taxes + exp_ins + exp_maint + exp_mgmt + exp_vacancy
                        
                        noi = gross_rent_ann - op_ex
                        total_ann_noi += noi
                        total_ann_debt += ann_mortgage
                        total_ann_ncf += (noi - ann_mortgage)
                        total_re_equity += (prop_v_current - rem_loan)

            # 3. Household Income
            salary_h = p_in["hp"] * ((1 + p_in["salary_growth"])**year_idx) if age < p_in["hr"] else 0
            salary_y = p_in["yp"] * ((1 + p_in["salary_growth"])**year_idx) if age < p_in["yr"] else 0
            soc_sec = p_in["ss_amt"] if age >= 67 else 0
            total_income = salary_h + salary_y + soc_sec + max(0, total_ann_noi)
            
            # 4. Education Liability
            edu_cost = 0
            if p_in["k1_s_yr"] <= curr_yr <= p_in["k1_e_yr"]: edu_cost += p_in["k1_cost"]
            if p_in["k2_s_yr"] <= curr_yr <= p_in["k2_e_yr"]: edu_cost += p_in["k2_cost"]
            
            # 5. Taxes & Expenses
            effective_tax_rate = p_in["tax_work"] if (salary_h + salary_y) > 0 else p_in["tax_ret"]
            tax_bill = total_income * effective_tax_rate
            lifestyle_spend = (p_in["ew"] if (age < p_in["hr"] or age < p_in["yr"]) else p_in["er"]) * ((1 + p_in["inflation"])**year_idx)
            
            # 6. Final Net Cash Flow & Liquidity Drawdown
            net_cash_flow = (salary_h + salary_y + soc_sec + total_ann_ncf) - (lifestyle_spend + edu_cost + tax_bill)
            
            if net_cash_flow < 0:
                deficit = abs(net_cash_flow)
                # Waterfall: Cash -> Brokerage -> 401k
                from_cash = min(curr_cash, deficit); curr_cash -= from_cash; deficit -= from_cash
                from_brok = min(curr_brok, deficit); curr_brok -= from_brok; deficit -= from_brok
                if deficit > 0:
                    tax_adj_draw = deficit / (1 - p_in["tax_ret"])
                    curr_ret -= tax_adj_draw
                    net_cash_flow = 0
            else:
                curr_cash += net_cash_flow

            # 7. Asset Appreciation
            curr_brok *= (1 + ann_market_return)
            curr_ret *= (1 + ann_market_return)
            curr_cash *= (1 + p_in["cash_roi"])
            residence_v *= (1 + p_in["inflation"]) # Residence grows with inflation
            
            path.append({
                "Age": age, "Year": curr_yr, "NW": curr_cash + curr_brok + curr_ret + total_re_equity + residence_v,
                "Liq": curr_cash + curr_brok + curr_ret, "NCF": net_cash_flow, "Salary": salary_h + salary_y,
                "NOI": total_ann_noi, "Debt": total_ann_debt, "Edu": edu_cost, "Spend": lifestyle_spend
            })
        all_results.append(path)
    return all_results

# --- 3. THE RESTORED SIDEBAR (LHS) ---
sb = st.sidebar
sb.title("⚙️ Full v45.0 Control Suite")

with sb.expander("🎲 Macro & Simulation Settings", expanded=True):
    inp["n_sims"] = st.number_input("Simulation Iterations", 50, 1000, int(inp["n_sims"]))
    inp["inflation"] = st.slider("Inflation %", 0.0, 10.0, float(inp["inflation"]*100))/100
    inp["salary_growth"] = st.slider("Salary Growth %", 0.0, 10.0, float(inp["salary_growth"]*100))/100
    inp["target_roi"] = st.slider("Target ROI %", 0.0, 15.0, float(inp["target_roi"]*100))/100
    inp["volatility"] = st.slider("Volatility %", 0.0, 40.0, float(inp["volatility"]*100))/100

with sb.expander("💰 Current Assets (Balance Sheet)", expanded=True):
    inp["v_401k"] = st.number_input("Retirement (401k/IRA)", value=float(inp["v_401k"]))
    inp["v_brokerage"] = st.number_input("Brokerage Account", value=float(inp["v_brokerage"]))
    inp["v_cash"] = st.number_input("Cash / Emergency Fund", value=float(inp["v_cash"]))
    inp["v_residence"] = st.number_input("Primary Residence Value", value=float(inp["v_residence"]))

with sb.expander("🏠 Real Estate Detail (v45.0 Module)", expanded=True):
    prop_count = st.number_input("Number of Properties", 1, 10, len(inp["props"]))
    while len(inp["props"]) < prop_count: inp["props"].append(DEFAULT_PROP.copy())
    inp["props"] = inp["props"][:prop_count]
    
    for i, p in enumerate(inp["props"]):
        st.markdown(f"**📍 Property {i+1} Configuration**")
        p["v"] = st.number_input(f"Current Value ##{i}", value=float(p["v"]))
        p["b"] = st.number_input(f"Cost Basis ##{i}", value=float(p.get("b", p["v"])))
        p["l"] = st.number_input(f"Loan Balance ##{i}", value=float(p["l"]))
        p["rent"] = st.number_input(f"Monthly Gross Rent ##{i}", value=float(p["rent"]))
        
        c1, c2 = st.columns(2)
        p["is_california"] = c1.checkbox("Prop 13 Cap?", value=p["is_california"], key=f"c_ca_{i}")
        p["is_nnn"] = c2.checkbox("Triple Net (NNN)?", value=p["is_nnn"], key=f"c_nnn_{i}")
        
        with st.expander(f"Advanced Property Metrics ##{i}"):
            p["rate"] = st.number_input("Mortgage Int %", 0.0, 10.0, float(p["rate"]*100), key=f"pr_{i}")/100
            p["term"] = st.number_input("Loan Term (Yrs)", 5, 40, int(p["term"]), key=f"pt_{i}")
            p["a"] = st.number_input("Appreciation %", 0.0, 10.0, float(p["a"]*100), key=f"pa_{i}")/100
            p["tax_rate"] = st.number_input("Tax Rate %", 0.0, 3.0, float(p["tax_rate"]*100), key=f"ptr_{i}")/100
            p["mgmt"] = st.number_input("Mgmt Fee %", 0.0, 20.0, float(p["mgmt"]*100), key=f"pmg_{i}")/100
            p["vacancy"] = st.number_input("Vacancy Loss %", 0.0, 20.0, float(p["vacancy"]*100), key=f"pvc_{i}")/100
            p["liq_active"] = st.checkbox("Sell Property at Target Age?", value=p["liq_active"], key=f"psa_{i}")
            p["liq_age"] = st.number_input("Selling Age", 45, 95, int(p["liq_age"]), key=f"pag_{i}")

with sb.expander("💵 Household Income & Retirement", expanded=True):
    inp["hp"], inp["hr"] = st.number_input("Yichi Annual Salary", value=float(inp["hp"])), st.number_input("Yichi Retirement Age", value=int(inp["hr"]))
    inp["yp"], inp["yr"] = st.number_input("Lu Annual Salary", value=float(inp["yp"])), st.number_input("Lu Retirement Age", value=int(inp["yr"]))
    inp["ss_amt"] = st.number_input("Est. Social Security (Combined)", value=float(inp["ss_amt"]))

with sb.expander("🎓 Education & Lifestyle", expanded=True):
    inp["k1_cost"] = st.number_input("Aaron Annual Cost", value=float(inp["k1_cost"]))
    inp["k2_cost"] = st.number_input("Alvin Annual Cost", value=float(inp["k2_cost"]))
    inp["ew"] = st.number_input("Current Annual Spend", value=float(inp["ew"]))
    inp["er"] = st.number_input("Retirement Annual Spend", value=float(inp["er"]))

# --- 4. MAIN DASHBOARD UI ---
st.title("🏦 Legacy Master v45.0: Production Dashboard")

# Run Engine
results_v45 = run_v45_engine(inp)
nw_curves = np.array([[yr["NW"] for yr in run] for run in results_v45])
p50 = np.median(nw_curves, axis=0)
p5, p95 = np.percentile(nw_curves, [5, 95], axis=0)
median_df = pd.DataFrame(results_v45[0])

# Top Metrics
m1, m2, m3 = st.columns(3)
m1.metric("Median Net Worth @ 95", f"${p50[-1]:,.0f}")
m2.metric("Portfolio Success Rate", f"{(nw_curves[:,-1] > 0).mean()*100:.1f}%")
m3.metric("Peak Education Burden", f"${median_df['Edu'].max():,.0f}")

# Main Chart
fig = go.Figure()
fig.add_trace(go.Scatter(x=median_df["Age"], y=p95, line=dict(width=0), showlegend=False))
fig.add_trace(go.Scatter(x=median_df["Age"], y=p5, fill='tonexty', fillcolor='rgba(239, 68, 68, 0.1)', name="95% Confidence Interval"))
fig.add_trace(go.Scatter(x=median_df["Age"], y=p50, line=dict(color="#10b981", width=4), name="Median Wealth Path"))
st.plotly_chart(fig.update_layout(title="Estate Accumulation Forecast", template="plotly_dark"), use_container_width=True)

# Cash Flow Sub-Chart
io = go.Figure()
io.add_trace(go.Bar(x=median_df["Age"], y=median_df["Salary"], name="W-2 Income", marker_color="#10b981"))
io.add_trace(go.Bar(x=median_df["Age"], y=median_df["NOI"], name="RE Net Operating Income", marker_color="#06b6d4"))
io.add_trace(go.Bar(x=median_df["Age"], y=-median_df["Spend"]-median_df["Edu"], name="Expenses & Education", marker_color="#fbbf24"))
st.plotly_chart(io.update_layout(barmode="relative", title="Annual Cash Flow Analysis", template="plotly_dark"), use_container_width=True)

# --- 5. THE AI SCENARIO LAB (APPENDED / SEPARATE MODULE) ---
st.markdown("---")
st.header("🤖 AI Scenario Lab (Standalone Module)")
st.caption("This module runs an independent simulation based on your Baseline v45.0 inputs above plus natural language overrides.")

def run_ai_sandbox(p_in, extra_inc, start_yr):
    """Separate engine to ensure zero interference with production math."""
    res = []
    for _ in range(100):
        c, b, r = p_in["v_cash"], p_in["v_brokerage"], p_in["v_401k"]
        path = []
        for age in range(p_in["ca"], p_in["ea"] + 1):
            y_idx = age - p_in["ca"]
            yr = 2026 + y_idx
            
            # Simple Delta Logic
            inc = (p_in["hp"] + p_in["yp"]) * ((1+p_in["salary_growth"])**y_idx) if age < 60 else 0
            bonus = extra_inc if yr >= start_yr else 0
            
            ncf = (inc + bonus) - (p_in["ew"] * ((1.03)**y_idx))
            c += ncf
            path.append({"Age": age, "NW": c + b + r})
        res.append(path)
    return res

q = st.text_input("Describe a 'What-If' (e.g., 'What if I earn an extra 75000 starting in 2032?')")
if q:
    nums = re.findall(r'\d+', q.replace(',', ''))
    if len(nums) >= 2:
        val, yr = (float(nums[0]), int(nums[1])) if float(nums[0]) > 1000 else (float(nums[1]), int(nums[0]))
        ai_sim = run_ai_sandbox(inp, val, yr)
        ai_df = pd.DataFrame(ai_sim[0])
        
        st.info(f"AI Scoping: Visualizing a +${val:,.0f} impact from {yr}")
        comp = go.Figure()
        comp.add_trace(go.Scatter(x=median_df["Age"], y=p50, name="v45.0 Baseline", line=dict(color="gray", dash="dot")))
        comp.add_trace(go.Scatter(x=ai_df["Age"], y=ai_df["NW"], name="AI Projection", line=dict(color="#3b82f6", width=4)))
        st.plotly_chart(comp.update_layout(title="Wealth Gap Comparison", template="plotly_dark"), use_container_width=True)
