import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import json
import re

st.set_page_config(layout="wide", page_title="Legacy Master 45.3", page_icon="🏦")

# ─────────────────────────────────────────────
# CUSTOM CSS: Clean & Modern Fintech Theme
# ─────────────────────────────────────────────
st.markdown("""
<style>
  /* Base */
  html, body, [class*="css"] { font-family: 'Inter', 'Segoe UI', sans-serif; }
  .main { background: #f5f7fa; }

  /* Sidebar */
  section[data-testid="stSidebar"] {
    background: #1a1f2e;
    color: #e2e8f0;
  }
  section[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
  section[data-testid="stSidebar"] .stSlider > div > div { background: #2d3748; }
  section[data-testid="stSidebar"] input { background: #2d3748 !important; border: 1px solid #4a5568 !important; }
  section[data-testid="stSidebar"] h1 { font-size: 1.1rem !important; font-weight: 700; letter-spacing: 0.05em; color: #63b3ed !important; }

  /* Cards */
  .card {
    background: white;
    border-radius: 16px;
    padding: 24px 28px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.07), 0 4px 16px rgba(0,0,0,0.04);
    margin-bottom: 16px;
    border: 1px solid #edf2f7;
  }
  .card-title {
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #718096;
    margin-bottom: 8px;
  }
  .card-value {
    font-size: 2rem;
    font-weight: 700;
    color: #1a202c;
    line-height: 1;
  }
  .card-delta {
    font-size: 0.875rem;
    color: #48bb78;
    margin-top: 4px;
    font-weight: 500;
  }
  .card-delta.negative { color: #fc8181; }

  /* Hero metric bar */
  .metric-bar {
    display: flex;
    gap: 16px;
    margin-bottom: 24px;
  }
  .metric-pill {
    flex: 1;
    background: white;
    border-radius: 12px;
    padding: 20px 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    border: 1px solid #edf2f7;
  }
  .metric-pill .label {
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: #a0aec0;
  }
  .metric-pill .value {
    font-size: 1.6rem;
    font-weight: 700;
    color: #1a202c;
    margin-top: 4px;
  }
  .metric-pill .sub {
    font-size: 0.78rem;
    color: #68d391;
    margin-top: 2px;
    font-weight: 500;
  }
  .metric-pill .sub.warn { color: #f6ad55; }
  .metric-pill .sub.bad  { color: #fc8181; }

  /* Section headers */
  .section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 28px 0 12px;
  }
  .section-header h2 {
    font-size: 1.05rem;
    font-weight: 700;
    color: #2d3748;
    margin: 0;
  }
  .section-badge {
    background: #ebf4ff;
    color: #3182ce;
    font-size: 0.65rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 20px;
    letter-spacing: 0.06em;
    text-transform: uppercase;
  }

  /* FIRE progress bar */
  .fire-track { background: #edf2f7; border-radius: 100px; height: 12px; margin: 12px 0; overflow: hidden; }
  .fire-fill {
    height: 100%;
    border-radius: 100px;
    background: linear-gradient(90deg, #48bb78, #38a169);
    transition: width 0.5s ease;
  }
  .fire-fill.warn { background: linear-gradient(90deg, #f6ad55, #ed8936); }
  .fire-fill.bad  { background: linear-gradient(90deg, #fc8181, #e53e3e); }

  /* Scenario buttons */
  .stButton > button {
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    border: 1.5px solid #e2e8f0 !important;
    background: white !important;
    color: #2d3748 !important;
    transition: all 0.15s !important;
  }
  .stButton > button:hover {
    border-color: #3182ce !important;
    color: #3182ce !important;
    box-shadow: 0 2px 8px rgba(49,130,206,0.15) !important;
  }

  /* Property comparison table */
  .prop-table { width: 100%; border-collapse: collapse; font-size: 0.87rem; }
  .prop-table th { background: #f7fafc; color: #718096; font-weight: 600; font-size: 0.72rem;
    text-transform: uppercase; letter-spacing: 0.06em; padding: 10px 14px; text-align: left;
    border-bottom: 2px solid #edf2f7; }
  .prop-table td { padding: 12px 14px; border-bottom: 1px solid #f0f4f8; color: #2d3748; }
  .prop-table tr:last-child td { border-bottom: none; }
  .prop-table tr:hover td { background: #f7fafc; }
  .badge-green { background: #f0fff4; color: #276749; border-radius: 6px; padding: 2px 8px; font-weight: 600; font-size: 0.78rem; }
  .badge-yellow { background: #fffff0; color: #744210; border-radius: 6px; padding: 2px 8px; font-weight: 600; font-size: 0.78rem; }
  .badge-red { background: #fff5f5; color: #742a2a; border-radius: 6px; padding: 2px 8px; font-weight: 600; font-size: 0.78rem; }

  /* Page title */
  .page-title { font-size: 1.6rem; font-weight: 800; color: #1a202c; margin-bottom: 4px; }
  .page-sub { font-size: 0.9rem; color: #a0aec0; margin-bottom: 24px; }

  /* Tab styling */
  .stTabs [data-baseweb="tab-list"] { gap: 4px; background: #f7fafc; border-radius: 12px; padding: 4px; }
  .stTabs [data-baseweb="tab"] { border-radius: 8px; font-weight: 600; font-size: 0.85rem; }
  .stTabs [aria-selected="true"] { background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }

  /* Hide default streamlit metric boxes */
  div[data-testid="metric-container"] { display: none; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 1. DEFAULTS
# ─────────────────────────────────────────────
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
    "ew": 180000.0, "er": 140000.0, "n_sims": 300,
    "fire_target_multiple": 25.0, "roth_start_age": 55, "roth_annual": 50000.0,
}

if "inputs" not in st.session_state:
    st.session_state.inputs = DEFAULTS.copy()
if "scenario_override" not in st.session_state:
    st.session_state.scenario_override = None

inp = st.session_state.inputs

# ─────────────────────────────────────────────
# 2. PRODUCTION ENGINE (unchanged)
# ─────────────────────────────────────────────
def run_v45_engine(p_in):
    all_results = []
    for _ in range(int(p_in["n_sims"])):
        curr_cash = p_in["v_cash"]
        curr_brok = p_in["v_brokerage"]
        curr_ret  = p_in["v_401k"]
        residence_v = p_in["v_residence"]
        sim_props = [pr.copy() for pr in p_in["props"]]
        path = []
        for age in range(p_in["ca"], p_in["ea"] + 1):
            year_idx = age - p_in["ca"]
            curr_yr  = 2026 + year_idx
            ann_market_return = np.random.normal(p_in["target_roi"], p_in["volatility"])
            total_re_equity = total_ann_noi = total_ann_debt = total_ann_ncf = 0
            for p in sim_props:
                if p["v"] > 0:
                    m_rate = p["rate"] / 12
                    m_term_mos = p["term"] * 12
                    pmt_mo = p["l"] * (m_rate * (1+m_rate)**m_term_mos) / ((1+m_rate)**m_term_mos - 1) if p["l"] > 0 else 0
                    months_since_purchase = (curr_yr - p.get("p_year", 2024)) * 12
                    if months_since_purchase < m_term_mos:
                        rem_loan = p["l"] * ((1+m_rate)**m_term_mos - (1+m_rate)**months_since_purchase) / ((1+m_rate)**m_term_mos - 1)
                        ann_mortgage = pmt_mo * 12
                    else:
                        rem_loan = 0; ann_mortgage = 0
                    prop_v_current  = p["v"] * ((1 + p["a"])**year_idx)
                    gross_rent_ann  = (p["rent"] * 12) * ((1 + p_in["inflation"])**year_idx)
                    assessment_v    = p["v"] * ((1.02)**year_idx) if p.get("is_california") else prop_v_current
                    if age == p["liq_age"] and p["liq_active"]:
                        sale_proceeds = prop_v_current - rem_loan
                        capital_gains_tax = max(0, (prop_v_current - p.get("b", p["v"])) * p_in["cap_gains"])
                        curr_cash += (sale_proceeds - capital_gains_tax)
                        p["v"] = 0
                    else:
                        if p.get("is_nnn"):
                            op_ex = gross_rent_ann * (p["mgmt"] + p["vacancy"])
                        else:
                            op_ex = (assessment_v * p["tax_rate"] + p["ins"] * ((1+p_in["inflation"])**year_idx) +
                                     prop_v_current * p["maint"] + gross_rent_ann * (p["mgmt"] + p["vacancy"]))
                        noi = gross_rent_ann - op_ex
                        total_ann_noi  += noi
                        total_ann_debt += ann_mortgage
                        total_ann_ncf  += (noi - ann_mortgage)
                        total_re_equity += (prop_v_current - rem_loan)
            salary_h = p_in["hp"] * ((1+p_in["salary_growth"])**year_idx) if age < p_in["hr"] else 0
            salary_y = p_in["yp"] * ((1+p_in["salary_growth"])**year_idx) if age < p_in["yr"] else 0
            soc_sec  = p_in["ss_amt"] if age >= 67 else 0
            total_income = salary_h + salary_y + soc_sec + max(0, total_ann_noi)
            edu_cost = 0
            if p_in["k1_s_yr"] <= curr_yr <= p_in["k1_e_yr"]: edu_cost += p_in["k1_cost"]
            if p_in["k2_s_yr"] <= curr_yr <= p_in["k2_e_yr"]: edu_cost += p_in["k2_cost"]
            effective_tax_rate = p_in["tax_work"] if (salary_h + salary_y) > 0 else p_in["tax_ret"]
            tax_bill = total_income * effective_tax_rate
            lifestyle_spend = (p_in["ew"] if (age < p_in["hr"] or age < p_in["yr"]) else p_in["er"]) * ((1+p_in["inflation"])**year_idx)
            net_cash_flow = (salary_h + salary_y + soc_sec + total_ann_ncf) - (lifestyle_spend + edu_cost + tax_bill)
            if net_cash_flow < 0:
                deficit = abs(net_cash_flow)
                from_cash = min(curr_cash, deficit); curr_cash -= from_cash; deficit -= from_cash
                from_brok = min(curr_brok, deficit); curr_brok -= from_brok; deficit -= from_brok
                if deficit > 0:
                    curr_ret -= deficit / (1 - p_in["tax_ret"]); net_cash_flow = 0
            else:
                curr_cash += net_cash_flow
            curr_brok   *= (1 + ann_market_return)
            curr_ret    *= (1 + ann_market_return)
            curr_cash   *= (1 + p_in["cash_roi"])
            residence_v *= (1 + p_in["inflation"])
            path.append({
                "Age": age, "Year": curr_yr,
                "NW":  curr_cash + curr_brok + curr_ret + total_re_equity + residence_v,
                "Liq": curr_cash + curr_brok + curr_ret,
                "NCF": net_cash_flow, "Salary": salary_h + salary_y,
                "NOI": total_ann_noi, "Debt": total_ann_debt,
                "Edu": edu_cost, "Spend": lifestyle_spend,
                "Cash": curr_cash, "Brok": curr_brok, "Ret": curr_ret, "RE": total_re_equity,
            })
        all_results.append(path)
    return all_results

# ─────────────────────────────────────────────
# 3. SIDEBAR
# ─────────────────────────────────────────────
sb = st.sidebar
sb.markdown("### ⚙️ Control Suite")

with sb.expander("🎲 Macro & Simulation", expanded=True):
    inp["n_sims"]       = st.number_input("Simulation Iterations", 50, 1000, int(inp["n_sims"]))
    inp["inflation"]    = st.slider("Inflation %", 0.0, 10.0, float(inp["inflation"]*100)) / 100
    inp["salary_growth"]= st.slider("Salary Growth %", 0.0, 10.0, float(inp["salary_growth"]*100)) / 100
    inp["target_roi"]   = st.slider("Target ROI %", 0.0, 15.0, float(inp["target_roi"]*100)) / 100
    inp["volatility"]   = st.slider("Volatility %", 0.0, 40.0, float(inp["volatility"]*100)) / 100

with sb.expander("💰 Balance Sheet", expanded=True):
    inp["v_401k"]      = st.number_input("Retirement (401k/IRA)",   value=float(inp["v_401k"]))
    inp["v_brokerage"] = st.number_input("Brokerage Account",        value=float(inp["v_brokerage"]))
    inp["v_cash"]      = st.number_input("Cash / Emergency Fund",    value=float(inp["v_cash"]))
    inp["v_residence"] = st.number_input("Primary Residence Value",  value=float(inp["v_residence"]))

with sb.expander("🏠 Real Estate", expanded=False):
    prop_count = st.number_input("Number of Properties", 1, 10, len(inp["props"]))
    while len(inp["props"]) < prop_count: inp["props"].append(DEFAULT_PROP.copy())
    inp["props"] = inp["props"][:prop_count]
    for i, p in enumerate(inp["props"]):
        st.markdown(f"**📍 Property {i+1}**")
        p["v"]    = st.number_input(f"Current Value",   value=float(p["v"]),    key=f"pv_{i}")
        p["b"]    = st.number_input(f"Cost Basis",      value=float(p.get("b", p["v"])), key=f"pb_{i}")
        p["l"]    = st.number_input(f"Loan Balance",    value=float(p["l"]),    key=f"pl_{i}")
        p["rent"] = st.number_input(f"Monthly Rent",    value=float(p["rent"]), key=f"pr_{i}")
        c1, c2 = st.columns(2)
        p["is_california"] = c1.checkbox("Prop 13?",  value=p["is_california"], key=f"c_ca_{i}")
        p["is_nnn"]        = c2.checkbox("NNN?",       value=p["is_nnn"],        key=f"c_nnn_{i}")
        with st.expander(f"Advanced ##{i}"):
            p["rate"]      = st.number_input("Mortgage Int %", 0.0, 10.0, float(p["rate"]*100), key=f"prate_{i}") / 100
            p["term"]      = st.number_input("Loan Term (Yrs)", 5, 40, int(p["term"]),          key=f"pterm_{i}")
            p["a"]         = st.number_input("Appreciation %", 0.0, 10.0, float(p["a"]*100),   key=f"pa_{i}") / 100
            p["tax_rate"]  = st.number_input("Tax Rate %", 0.0, 3.0, float(p["tax_rate"]*100), key=f"ptax_{i}") / 100
            p["mgmt"]      = st.number_input("Mgmt Fee %", 0.0, 20.0, float(p["mgmt"]*100),    key=f"pmg_{i}") / 100
            p["vacancy"]   = st.number_input("Vacancy %", 0.0, 20.0, float(p["vacancy"]*100),  key=f"pvc_{i}") / 100
            p["liq_active"]= st.checkbox("Sell at Target Age?", value=p["liq_active"],          key=f"psa_{i}")
            p["liq_age"]   = st.number_input("Selling Age", 45, 95, int(p["liq_age"]),          key=f"pag_{i}")

with sb.expander("💵 Income & Retirement", expanded=False):
    inp["hp"]     = st.number_input("Yichi Annual Salary",  value=float(inp["hp"]))
    inp["hr"]     = st.number_input("Yichi Retirement Age", value=int(inp["hr"]))
    inp["yp"]     = st.number_input("Lu Annual Salary",     value=float(inp["yp"]))
    inp["yr"]     = st.number_input("Lu Retirement Age",    value=int(inp["yr"]))
    inp["ss_amt"] = st.number_input("Social Security (Combined)", value=float(inp["ss_amt"]))

with sb.expander("🎓 Education & Lifestyle", expanded=False):
    inp["k1_cost"] = st.number_input("Aaron Annual Cost",       value=float(inp["k1_cost"]))
    inp["k2_cost"] = st.number_input("Alvin Annual Cost",       value=float(inp["k2_cost"]))
    inp["ew"]      = st.number_input("Current Annual Spend",    value=float(inp["ew"]))
    inp["er"]      = st.number_input("Retirement Annual Spend", value=float(inp["er"]))

with sb.expander("🔥 FIRE & Tax Settings", expanded=False):
    inp["fire_target_multiple"] = st.number_input("FIRE Multiple (25x = 4% rule)", 10.0, 40.0, float(inp.get("fire_target_multiple", 25.0)))
    inp["roth_start_age"]       = st.number_input("Roth Conversion Start Age", 45, 75, int(inp.get("roth_start_age", 55)))
    inp["roth_annual"]          = st.number_input("Annual Roth Conversion $",  value=float(inp.get("roth_annual", 50000.0)))

# ─────────────────────────────────────────────
# 4. RUN ENGINE
# ─────────────────────────────────────────────
# Apply scenario override if active
active_inp = inp.copy()
ov = st.session_state.scenario_override
if ov:
    active_inp.update(ov)

results_v45 = run_v45_engine(active_inp)
nw_curves   = np.array([[yr["NW"]  for yr in run] for run in results_v45])
liq_curves  = np.array([[yr["Liq"] for yr in run] for run in results_v45])
p50  = np.median(nw_curves, axis=0)
p5, p95 = np.percentile(nw_curves, [5, 95], axis=0)
liq50 = np.median(liq_curves, axis=0)
median_df = pd.DataFrame(results_v45[0])

# Baseline for scenario comparison
baseline_p50 = None

# ─────────────────────────────────────────────
# 5. FIRE CALCULATIONS
# ─────────────────────────────────────────────
fire_target   = inp["er"] * inp.get("fire_target_multiple", 25.0)
current_liq   = inp["v_cash"] + inp["v_brokerage"] + inp["v_401k"]
fire_progress = min(current_liq / fire_target, 1.0)
fire_pct      = fire_progress * 100

# When does median liq cross fire_target?
fire_age = None
for i, liq in enumerate(liq50):
    if liq >= fire_target:
        fire_age = median_df["Age"].iloc[i]
        break

# ─────────────────────────────────────────────
# 6. MAIN DASHBOARD
# ─────────────────────────────────────────────
st.markdown('<div class="page-title">🏦 Legacy Master v45.3</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">Monte Carlo Financial Planning Dashboard</div>', unsafe_allow_html=True)

# Hero metrics (custom HTML cards)
success_rate = (nw_curves[:, -1] > 0).mean() * 100
peak_nw = p50.max()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""
    <div class="metric-pill">
      <div class="label">Median NW @ Age {inp['ea']}</div>
      <div class="value">${p50[-1]/1e6:.2f}M</div>
      <div class="sub">{'✅ On track' if p50[-1] > 0 else '⚠️ At risk'}</div>
    </div>""", unsafe_allow_html=True)

with col2:
    color_class = "sub" if success_rate >= 80 else ("sub warn" if success_rate >= 60 else "sub bad")
    st.markdown(f"""
    <div class="metric-pill">
      <div class="label">Portfolio Success Rate</div>
      <div class="value">{success_rate:.1f}%</div>
      <div class="{color_class}">{'✅ Strong' if success_rate >= 80 else ('⚠️ Moderate' if success_rate >= 60 else '🔴 Risky')}</div>
    </div>""", unsafe_allow_html=True)

with col3:
    fire_label = f"Age {fire_age}" if fire_age else "Not reached"
    fire_color = "sub" if fire_age and fire_age <= min(inp["hr"], inp["yr"]) else "sub warn"
    st.markdown(f"""
    <div class="metric-pill">
      <div class="label">FIRE Date (Median)</div>
      <div class="value">{fire_label}</div>
      <div class="{fire_color}">Target: ${fire_target/1e6:.2f}M</div>
    </div>""", unsafe_allow_html=True)

with col4:
    edu_burden = median_df["Edu"].max()
    st.markdown(f"""
    <div class="metric-pill">
      <div class="label">Peak Education Burden</div>
      <div class="value">${edu_burden:,.0f}</div>
      <div class="sub">Annual peak year</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Wealth Forecast",
    "🔥 FIRE Tracker",
    "🏠 Property Analysis",
    "🤖 Scenario Lab",
    "🧾 Tax Optimizer"
])

# ── TAB 1: Wealth Forecast ──────────────────
with tab1:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=median_df["Age"], y=p95, line=dict(width=0), showlegend=False, name="P95"
    ))
    fig.add_trace(go.Scatter(
        x=median_df["Age"], y=p5, fill='tonexty',
        fillcolor='rgba(99,179,237,0.12)', line=dict(width=0),
        name="90% Confidence Band"
    ))
    fig.add_trace(go.Scatter(
        x=median_df["Age"], y=p50,
        line=dict(color="#3182ce", width=3.5),
        name="Median Path"
    ))
    fig.add_trace(go.Scatter(
        x=median_df["Age"], y=liq50,
        line=dict(color="#38a169", width=2, dash="dot"),
        name="Liquid Assets Only"
    ))
    if fire_target:
        fig.add_hline(y=fire_target, line=dict(color="#e53e3e", width=1.5, dash="dash"),
                      annotation_text=f"FIRE Target ${fire_target/1e6:.1f}M",
                      annotation_position="bottom right")
    fig.update_layout(
        template="plotly_white",
        title=dict(text="Estate Accumulation Forecast", font=dict(size=15, color="#2d3748")),
        xaxis=dict(title="Age", showgrid=True, gridcolor="#f0f4f8"),
        yaxis=dict(title="Net Worth ($)", tickformat="$,.0f", showgrid=True, gridcolor="#f0f4f8"),
        legend=dict(orientation="h", y=-0.15),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(t=60, b=60)
    )
    st.plotly_chart(fig, use_container_width=True)

    # Cash flow chart
    io = go.Figure()
    io.add_trace(go.Bar(x=median_df["Age"], y=median_df["Salary"], name="W-2 Income",       marker_color="#48bb78"))
    io.add_trace(go.Bar(x=median_df["Age"], y=median_df["NOI"],    name="RE Net Op. Income", marker_color="#4299e1"))
    io.add_trace(go.Bar(x=median_df["Age"], y=-(median_df["Spend"]+median_df["Edu"]),
                        name="Expenses + Education", marker_color="#fc8181"))
    io.update_layout(
        barmode="relative", template="plotly_white",
        title=dict(text="Annual Cash Flow Analysis", font=dict(size=15, color="#2d3748")),
        xaxis=dict(title="Age", showgrid=False),
        yaxis=dict(title="$ / Year", tickformat="$,.0f", showgrid=True, gridcolor="#f0f4f8"),
        legend=dict(orientation="h", y=-0.18),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(t=60, b=60)
    )
    st.plotly_chart(io, use_container_width=True)

    # Asset allocation over time (median path)
    alloc = go.Figure()
    alloc.add_trace(go.Scatter(x=median_df["Age"], y=median_df["Cash"], name="Cash",       stackgroup="one", fillcolor="#68d391", line=dict(width=0)))
    alloc.add_trace(go.Scatter(x=median_df["Age"], y=median_df["Brok"], name="Brokerage",  stackgroup="one", fillcolor="#63b3ed", line=dict(width=0)))
    alloc.add_trace(go.Scatter(x=median_df["Age"], y=median_df["Ret"],  name="Retirement", stackgroup="one", fillcolor="#f6ad55", line=dict(width=0)))
    alloc.add_trace(go.Scatter(x=median_df["Age"], y=median_df["RE"],   name="Real Estate",stackgroup="one", fillcolor="#b794f4", line=dict(width=0)))
    alloc.update_layout(
        template="plotly_white",
        title=dict(text="Asset Allocation Over Time (Median Path)", font=dict(size=15, color="#2d3748")),
        xaxis=dict(title="Age"), yaxis=dict(title="$", tickformat="$,.0f", showgrid=True, gridcolor="#f0f4f8"),
        legend=dict(orientation="h", y=-0.18),
        plot_bgcolor="white", paper_bgcolor="white", margin=dict(t=60, b=60)
    )
    st.plotly_chart(alloc, use_container_width=True)

# ── TAB 2: FIRE Tracker ──────────────────────
with tab2:
    st.markdown('<div class="section-header"><h2>🔥 FIRE Number Tracker</h2><span class="section-badge">4% Rule</span></div>', unsafe_allow_html=True)

    fc1, fc2 = st.columns([2, 1])
    with fc1:
        bar_color = "fire-fill" if fire_pct >= 80 else ("fire-fill warn" if fire_pct >= 50 else "fire-fill bad")
        st.markdown(f"""
        <div class="card">
          <div class="card-title">Progress to FIRE</div>
          <div style="display:flex; justify-content:space-between; align-items:baseline; margin-bottom:6px;">
            <span style="font-size:1.4rem;font-weight:700;color:#1a202c;">${current_liq/1e6:.2f}M liquid</span>
            <span style="font-size:1rem;color:#718096;">of ${fire_target/1e6:.2f}M target</span>
          </div>
          <div class="fire-track"><div class="{bar_color}" style="width:{fire_pct:.1f}%"></div></div>
          <div style="display:flex;justify-content:space-between;margin-top:6px;">
            <span style="font-size:0.8rem;color:#718096;">{fire_pct:.1f}% funded</span>
            <span style="font-size:0.8rem;color:#718096;">Gap: ${max(0,fire_target-current_liq)/1e6:.2f}M</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # FIRE milestones
        milestones = [25, 50, 75, 100]
        rows = ""
        for m in milestones:
            target_m = fire_target * m / 100
            reached_age = None
            for i, liq in enumerate(liq50):
                if liq >= target_m:
                    reached_age = int(median_df["Age"].iloc[i])
                    break
            status = "✅" if (reached_age and reached_age <= inp["ca"] + 5) else ("🔄" if reached_age else "⏳")
            label  = f"Age {reached_age}" if reached_age else "Not in range"
            rows  += f"<tr><td>{m}% funded (${target_m/1e6:.2f}M)</td><td>{label}</td><td>{status}</td></tr>"

        st.markdown(f"""
        <div class="card" style="margin-top:0;">
          <div class="card-title">Funding Milestones (Median Path)</div>
          <table class="prop-table">
            <thead><tr><th>Milestone</th><th>Projected Age</th><th>Status</th></tr></thead>
            <tbody>{rows}</tbody>
          </table>
        </div>""", unsafe_allow_html=True)

    with fc2:
        # Safe withdrawal rate analysis
        swr_rates = [0.03, 0.035, 0.04, 0.045, 0.05]
        swr_data = []
        for r in swr_rates:
            target = inp["er"] / r
            a = None
            for i, liq in enumerate(liq50):
                if liq >= target:
                    a = int(median_df["Age"].iloc[i]); break
            swr_data.append({"SWR": f"{r*100:.1f}%", "Target": f"${target/1e6:.2f}M", "FIRE Age": str(a) if a else "—"})

        st.markdown("""<div class="card"><div class="card-title">SWR Sensitivity</div>""", unsafe_allow_html=True)
        swr_rows = "".join(
            f"<tr><td><b>{d['SWR']}</b></td><td>{d['Target']}</td><td>{d['FIRE Age']}</td></tr>"
            for d in swr_data
        )
        st.markdown(f"""
          <table class="prop-table">
            <thead><tr><th>Rate</th><th>Target</th><th>FIRE Age</th></tr></thead>
            <tbody>{swr_rows}</tbody>
          </table>
        </div>""", unsafe_allow_html=True)

        # Coast FIRE
        coast_target = fire_target / ((1 + inp["target_roi"]) ** (min(inp["hr"], inp["yr"]) - inp["ca"]))
        coast_pct    = min(current_liq / coast_target, 1.0) * 100
        coast_bar    = "fire-fill" if coast_pct >= 100 else ("fire-fill warn" if coast_pct >= 60 else "fire-fill bad")
        st.markdown(f"""
        <div class="card">
          <div class="card-title">Coast FIRE</div>
          <div style="font-size:0.85rem;color:#718096;margin-bottom:10px;">
            Amount needed NOW so investments grow to FIRE target by retirement — no more saving required.
          </div>
          <div style="font-weight:700;font-size:1.1rem;color:#1a202c;">${coast_target/1e6:.2f}M coast target</div>
          <div class="fire-track" style="margin:8px 0;"><div class="{coast_bar}" style="width:{min(coast_pct,100):.1f}%"></div></div>
          <div style="font-size:0.8rem;color:#718096;">{coast_pct:.1f}% of coast number funded</div>
          {('<div style="color:#48bb78;font-size:0.85rem;font-weight:600;margin-top:6px;">✅ You have hit Coast FIRE!</div>') if coast_pct >= 100 else ''}
        </div>""", unsafe_allow_html=True)

# ── TAB 3: Property Analysis ─────────────────
with tab3:
    st.markdown('<div class="section-header"><h2>🏠 Property Comparison</h2><span class="section-badge">Portfolio View</span></div>', unsafe_allow_html=True)

    prop_rows = ""
    chart_data = []
    for i, p in enumerate(inp["props"]):
        if p["v"] == 0: continue
        gross_ann  = p["rent"] * 12
        m_rate     = p["rate"] / 12
        m_term     = p["term"] * 12
        pmt_mo     = p["l"] * (m_rate * (1+m_rate)**m_term) / ((1+m_rate)**m_term - 1) if p["l"] > 0 else 0

        if p.get("is_nnn"):
            op_ex = gross_ann * (p["mgmt"] + p["vacancy"])
        else:
            op_ex = (p["v"] * p["tax_rate"] + p["ins"] + p["v"] * p["maint"] +
                     gross_ann * (p["mgmt"] + p["vacancy"]))

        noi      = gross_ann - op_ex
        cap_rate = noi / p["v"] * 100
        equity   = p["v"] - p["l"]
        coc      = (noi - pmt_mo * 12) / max(equity, 1) * 100 if equity > 0 else 0
        dscr     = noi / max(pmt_mo * 12, 1)

        cap_badge  = "badge-green" if cap_rate >= 5 else ("badge-yellow" if cap_rate >= 3.5 else "badge-red")
        coc_badge  = "badge-green" if coc >= 6    else ("badge-yellow" if coc >= 3    else "badge-red")
        dscr_badge = "badge-green" if dscr >= 1.25 else ("badge-yellow" if dscr >= 1.0 else "badge-red")
        nnn_label  = " <span class='badge-green'>NNN</span>" if p.get("is_nnn") else ""
        ca_label   = " <span class='badge-yellow'>Prop13</span>" if p.get("is_california") else ""

        prop_rows += f"""
        <tr>
          <td><b>Property {i+1}</b>{nnn_label}{ca_label}</td>
          <td>${p['v']/1e6:.2f}M</td>
          <td>${gross_ann:,.0f}</td>
          <td>${noi:,.0f}</td>
          <td><span class="{cap_badge}">{cap_rate:.2f}%</span></td>
          <td><span class="{coc_badge}">{coc:.2f}%</span></td>
          <td><span class="{dscr_badge}">{dscr:.2f}x</span></td>
          <td>${equity/1e6:.2f}M</td>
        </tr>"""

        chart_data.append({"Property": f"Prop {i+1}", "Cap Rate": cap_rate, "CoC Return": coc, "DSCR": dscr * 10})

    st.markdown(f"""
    <div class="card">
      <div class="card-title">Portfolio Metrics (Current Year)</div>
      <table class="prop-table">
        <thead>
          <tr>
            <th>Property</th><th>Value</th><th>Gross Rent</th><th>NOI</th>
            <th>Cap Rate</th><th>Cash-on-Cash</th><th>DSCR</th><th>Equity</th>
          </tr>
        </thead>
        <tbody>{prop_rows}</tbody>
      </table>
    </div>""", unsafe_allow_html=True)

    if chart_data:
        pcomp_df = pd.DataFrame(chart_data)
        pfig = go.Figure()
        pfig.add_trace(go.Bar(x=pcomp_df["Property"], y=pcomp_df["Cap Rate"],   name="Cap Rate %",     marker_color="#63b3ed"))
        pfig.add_trace(go.Bar(x=pcomp_df["Property"], y=pcomp_df["CoC Return"], name="Cash-on-Cash %", marker_color="#68d391"))
        pfig.update_layout(
            barmode="group", template="plotly_white",
            title=dict(text="Property Return Comparison", font=dict(size=15, color="#2d3748")),
            yaxis=dict(title="%", showgrid=True, gridcolor="#f0f4f8"),
            legend=dict(orientation="h", y=-0.18),
            plot_bgcolor="white", paper_bgcolor="white", margin=dict(t=60, b=60)
        )
        st.plotly_chart(pfig, use_container_width=True)

    # Equity build over time per property
    if len(inp["props"]) > 1:
        eq_fig = go.Figure()
        colors = ["#63b3ed", "#68d391", "#f6ad55", "#b794f4", "#fc8181"]
        for i, p in enumerate(inp["props"]):
            if p["v"] == 0: continue
            ages, equities = [], []
            for age in range(inp["ca"], inp["ea"]+1):
                year_idx = age - inp["ca"]
                curr_yr  = 2026 + year_idx
                m_rate   = p["rate"] / 12
                m_term   = p["term"] * 12
                months   = (curr_yr - p.get("p_year", 2024)) * 12
                if months < m_term and p["l"] > 0:
                    rem = p["l"] * ((1+m_rate)**m_term - (1+m_rate)**months) / ((1+m_rate)**m_term - 1)
                else:
                    rem = 0
                prop_v = p["v"] * ((1+p["a"])**year_idx)
                equities.append(prop_v - rem)
                ages.append(age)
            eq_fig.add_trace(go.Scatter(x=ages, y=equities, name=f"Property {i+1}",
                                        line=dict(width=2.5, color=colors[i % len(colors)])))
        eq_fig.update_layout(
            template="plotly_white",
            title=dict(text="Equity Build-Up by Property", font=dict(size=15, color="#2d3748")),
            xaxis=dict(title="Age"), yaxis=dict(title="Equity ($)", tickformat="$,.0f", showgrid=True, gridcolor="#f0f4f8"),
            legend=dict(orientation="h", y=-0.18),
            plot_bgcolor="white", paper_bgcolor="white", margin=dict(t=60, b=60)
        )
        st.plotly_chart(eq_fig, use_container_width=True)

# ── TAB 4: Scenario Lab ──────────────────────
with tab4:
    st.markdown('<div class="section-header"><h2>🤖 Scenario Lab</h2><span class="section-badge">What-If</span></div>', unsafe_allow_html=True)

    # Preset scenarios
    sc1, sc2 = st.columns(2)
    scenarios = {
        "💼 Job Loss (Yichi, 2 years)": {"hp": 0.0, "_note": "Yichi loses income for ~2 years (set salary to 0)"},
        "📉 Market Crash (−40%)": {"v_401k": inp["v_401k"]*0.6, "v_brokerage": inp["v_brokerage"]*0.6, "_note": "Simulates a 40% drawdown in liquid assets"},
        "🏖️ Early Retirement (both age 50)": {"hr": 50, "yr": 50, "_note": "Both retire 5+ years earlier"},
        "🏠 Rental Boost (+$2k/mo each)": {"props": [{**p, "rent": p["rent"]+2000} for p in inp["props"]], "_note": "+$2,000/mo rent per property"},
        "📈 Salary Windfall (+$100k/yr)": {"hp": inp["hp"]+100000, "_note": "Yichi gets a $100k raise"},
        "💸 Spend More in Retirement (+$50k)": {"er": inp["er"]+50000, "_note": "Upgrade retirement lifestyle"},
    }

    cols = st.columns(3)
    active_scenario_name = st.session_state.get("active_scenario_name", None)

    for idx, (name, override) in enumerate(scenarios.items()):
        with cols[idx % 3]:
            note = override.pop("_note", "")
            is_active = active_scenario_name == name
            if st.button(f"{'✓ ' if is_active else ''}{name}", key=f"sc_{idx}", use_container_width=True):
                if is_active:
                    st.session_state.scenario_override = None
                    st.session_state.active_scenario_name = None
                else:
                    st.session_state.scenario_override = override
                    st.session_state.active_scenario_name = name
                st.rerun()
            st.caption(note)

    st.markdown("---")

    # Show comparison if scenario active
    if st.session_state.scenario_override:
        scenario_inp = inp.copy()
        scenario_inp.update(st.session_state.scenario_override)
        scenario_results = run_v45_engine(scenario_inp)
        sc_curves = np.array([[yr["NW"] for yr in run] for run in scenario_results])
        sc_p50    = np.median(sc_curves, axis=0)

        delta_at_end = sc_p50[-1] - p50[-1]
        delta_color  = "#48bb78" if delta_at_end >= 0 else "#e53e3e"
        delta_sign   = "+" if delta_at_end >= 0 else ""

        st.markdown(f"""
        <div class="card">
          <div class="card-title">Scenario: {active_scenario_name}</div>
          <div style="display:flex;gap:32px;align-items:center;">
            <div>
              <div style="font-size:0.78rem;color:#a0aec0;">Baseline NW @ {inp['ea']}</div>
              <div style="font-size:1.3rem;font-weight:700;">${p50[-1]/1e6:.2f}M</div>
            </div>
            <div style="font-size:1.5rem;color:#a0aec0;">→</div>
            <div>
              <div style="font-size:0.78rem;color:#a0aec0;">Scenario NW @ {inp['ea']}</div>
              <div style="font-size:1.3rem;font-weight:700;">${sc_p50[-1]/1e6:.2f}M</div>
            </div>
            <div style="margin-left:auto;text-align:right;">
              <div style="font-size:0.78rem;color:#a0aec0;">Net Impact</div>
              <div style="font-size:1.4rem;font-weight:700;color:{delta_color};">{delta_sign}${abs(delta_at_end)/1e6:.2f}M</div>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

        comp = go.Figure()
        comp.add_trace(go.Scatter(x=median_df["Age"], y=p50,    name="Baseline",
                                  line=dict(color="#a0aec0", width=2, dash="dot")))
        comp.add_trace(go.Scatter(x=median_df["Age"], y=sc_p50, name=active_scenario_name,
                                  line=dict(color="#3182ce", width=3.5)))
        comp.update_layout(
            template="plotly_white",
            title=dict(text="Baseline vs Scenario Comparison", font=dict(size=15, color="#2d3748")),
            xaxis=dict(title="Age"), yaxis=dict(title="Net Worth ($)", tickformat="$,.0f", showgrid=True, gridcolor="#f0f4f8"),
            legend=dict(orientation="h", y=-0.15),
            plot_bgcolor="white", paper_bgcolor="white", margin=dict(t=60, b=60)
        )
        st.plotly_chart(comp, use_container_width=True)
    else:
        st.info("Select a scenario above to compare it against your baseline.")

    # Natural language what-if (original feature, improved)
    st.markdown("**Or describe a custom scenario:**")
    q = st.text_input("e.g. 'What if I earn an extra 75000 starting in 2032?'", key="nl_query")
    if q:
        nums = re.findall(r'\d+', q.replace(',', ''))
        if len(nums) >= 2:
            n0, n1 = float(nums[0]), float(nums[1])
            val, yr_val = (n0, int(n1)) if n0 > 1000 else (n1, int(n0))
            start_idx = max(0, yr_val - 2026)
            modified_curves = nw_curves.copy()
            for sim in range(len(results_v45)):
                for t in range(start_idx, len(results_v45[sim])):
                    modified_curves[sim][t] += val * (t - start_idx + 1)
            custom_p50 = np.median(modified_curves, axis=0)
            st.info(f"Modeling +${val:,.0f}/yr starting {yr_val}")
            cf = go.Figure()
            cf.add_trace(go.Scatter(x=median_df["Age"], y=p50,        name="Baseline", line=dict(color="#a0aec0", dash="dot")))
            cf.add_trace(go.Scatter(x=median_df["Age"], y=custom_p50, name="Custom",   line=dict(color="#805ad5", width=3)))
            cf.update_layout(template="plotly_white", plot_bgcolor="white", paper_bgcolor="white",
                             xaxis=dict(title="Age"), yaxis=dict(tickformat="$,.0f"), margin=dict(t=40, b=40))
            st.plotly_chart(cf, use_container_width=True)

# ── TAB 5: Tax Optimizer ─────────────────────
with tab5:
    st.markdown('<div class="section-header"><h2>🧾 Tax Optimization</h2><span class="section-badge">Strategy</span></div>', unsafe_allow_html=True)

    tc1, tc2 = st.columns([3, 2])

    with tc1:
        # Roth conversion ladder
        st.markdown('<div class="card"><div class="card-title">Roth Conversion Ladder</div>', unsafe_allow_html=True)

        roth_start  = inp.get("roth_start_age", 55)
        roth_annual = inp.get("roth_annual", 50000.0)
        ages_list   = list(range(inp["ca"], inp["ea"]+1))

        # Estimate 401k balance over time (simplified, median path)
        ret_balances = [r["Ret"] for r in results_v45[0]]

        roth_savings = []
        for age in ages_list:
            year_idx = age - inp["ca"]
            ret_bal  = ret_balances[year_idx]
            if age >= roth_start and age < min(inp["hr"], inp["yr"]):
                # Roth conversion: pay tax at work rate now vs higher rate later
                roth_tax_now   = roth_annual * inp["tax_work"]
                roth_tax_later = roth_annual * (inp["tax_ret"] + 0.05)  # estimate RMD bracket bump
                savings = max(0, roth_tax_later - roth_tax_now)
                roth_savings.append({"Age": age, "Converted": roth_annual, "Tax Now": roth_tax_now, "Savings": savings})
            else:
                roth_savings.append({"Age": age, "Converted": 0, "Tax Now": 0, "Savings": 0})

        roth_df = pd.DataFrame(roth_savings)
        total_savings = roth_df["Savings"].sum()

        roth_fig = go.Figure()
        roth_fig.add_trace(go.Bar(x=roth_df["Age"], y=roth_df["Converted"], name="Annual Conversion", marker_color="#4299e1"))
        roth_fig.add_trace(go.Scatter(x=roth_df["Age"], y=roth_df["Savings"].cumsum(), name="Cumulative Tax Savings",
                                      line=dict(color="#48bb78", width=2.5), yaxis="y2"))
        roth_fig.update_layout(
            template="plotly_white",
            title=dict(text=f"Roth Conversions starting Age {roth_start} · Est. lifetime tax savings: ${total_savings:,.0f}", font=dict(size=13, color="#2d3748")),
            xaxis=dict(title="Age", showgrid=False),
            yaxis=dict(title="Conversion Amount ($)", tickformat="$,.0f", showgrid=True, gridcolor="#f0f4f8"),
            yaxis2=dict(title="Cumulative Savings ($)", tickformat="$,.0f", overlaying="y", side="right"),
            legend=dict(orientation="h", y=-0.18),
            plot_bgcolor="white", paper_bgcolor="white", margin=dict(t=60, b=60)
        )
        st.plotly_chart(roth_fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Capital gains timing
        st.markdown("""<div class="card"><div class="card-title">Capital Gains Harvest Opportunities</div>""", unsafe_allow_html=True)
        cg_rows = ""
        for i, p in enumerate(inp["props"]):
            if p["v"] == 0: continue
            unrealized = p["v"] - p.get("b", p["v"])
            tax_bill   = max(0, unrealized * inp["cap_gains"])
            net_proc   = p["v"] - p["l"] - tax_bill
            strategy   = "Consider 1031 exchange" if unrealized > 500000 else ("Harvest gains" if unrealized > 0 else "No gain")
            badge      = "badge-yellow" if unrealized > 500000 else ("badge-green" if unrealized > 0 else "badge-red")
            cg_rows   += f"""<tr>
              <td>Property {i+1}</td>
              <td>${unrealized:,.0f}</td>
              <td>${tax_bill:,.0f}</td>
              <td>${net_proc:,.0f}</td>
              <td><span class="{badge}">{strategy}</span></td>
            </tr>"""
        st.markdown(f"""
          <table class="prop-table">
            <thead><tr><th>Property</th><th>Unrealized Gain</th><th>Tax Exposure</th><th>Net Proceeds</th><th>Strategy</th></tr></thead>
            <tbody>{cg_rows}</tbody>
          </table>
        </div>""", unsafe_allow_html=True)

    with tc2:
        # Withdrawal sequencing
        st.markdown("""<div class="card"><div class="card-title">Optimal Withdrawal Order</div>
        <div style="font-size:0.82rem;color:#718096;line-height:1.6;">
          In retirement, drawing from accounts in the right order minimizes your lifetime tax burden:
        </div>
        <br>
        <div style="display:flex;flex-direction:column;gap:10px;">
          <div style="background:#f0fff4;border-radius:10px;padding:12px 16px;border-left:4px solid #48bb78;">
            <div style="font-weight:700;color:#276749;">① Taxable Brokerage First</div>
            <div style="font-size:0.78rem;color:#276749;margin-top:4px;">Long-term cap gains rate (0–20%). Let tax-deferred accounts keep compounding.</div>
          </div>
          <div style="background:#ebf4ff;border-radius:10px;padding:12px 16px;border-left:4px solid #4299e1;">
            <div style="font-weight:700;color:#2b6cb0;">② 401k / Traditional IRA</div>
            <div style="font-size:0.78rem;color:#2b6cb0;margin-top:4px;">Ordinary income. Withdraw enough to fill lower brackets each year.</div>
          </div>
          <div style="background:#fff5f5;border-radius:10px;padding:12px 16px;border-left:4px solid #fc8181;">
            <div style="font-weight:700;color:#742a2a;">③ Roth IRA Last</div>
            <div style="font-size:0.78rem;color:#742a2a;margin-top:4px;">100% tax-free. Leave to compound as long as possible. Best for heirs.</div>
          </div>
        </div></div>""", unsafe_allow_html=True)

        # Effective tax rate over life
        tax_data = []
        for r in results_v45[0]:
            age = r["Age"]
            sal = r["Salary"]
            rate = inp["tax_work"] if sal > 0 else inp["tax_ret"]
            tax_data.append({"Age": age, "Effective Rate": rate * 100})
        tdf = pd.DataFrame(tax_data)

        tfig = go.Figure()
        tfig.add_trace(go.Scatter(x=tdf["Age"], y=tdf["Effective Rate"],
                                  fill="tozeroy", fillcolor="rgba(252,129,129,0.15)",
                                  line=dict(color="#e53e3e", width=2), name="Effective Tax Rate"))
        tfig.update_layout(
            template="plotly_white",
            title=dict(text="Effective Tax Rate by Age", font=dict(size=13, color="#2d3748")),
            xaxis=dict(title="Age", showgrid=False),
            yaxis=dict(title="%", showgrid=True, gridcolor="#f0f4f8"),
            plot_bgcolor="white", paper_bgcolor="white",
            margin=dict(t=50, b=40), showlegend=False,
            height=250
        )
        st.plotly_chart(tfig, use_container_width=True)

        # RMD warning
        rmd_age = 73
        rmd_start_year = 2026 + (rmd_age - inp["ca"])
        rmd_bal = results_v45[0][min(rmd_age - inp["ca"], len(results_v45[0])-1)]["Ret"] if rmd_age > inp["ca"] else inp["v_401k"]
        rmd_amt = rmd_bal / 26.5  # IRS uniform lifetime table divisor at 73
        rmd_amt_fmt = f"${rmd_amt:,.0f}"
        rmd_bal_fmt = f"${rmd_bal/1e6:.2f}M"
        st.markdown(
            '<div class="card">'
            '<div class="card-title">RMD Preview (Age 73)</div>'
            '<div style="font-size:0.85rem;color:#718096;margin-bottom:8px;">Required Minimum Distributions force taxable withdrawals from your 401k starting age 73.</div>'
            f'<div style="font-weight:700;font-size:1.1rem;color:#1a202c;">Est. Annual RMD: {rmd_amt_fmt}</div>'
            f'<div style="font-size:0.78rem;color:#718096;margin-top:4px;">Based on projected 401k balance of {rmd_bal_fmt} at age 73</div>'
            '<div style="background:#fffff0;border-radius:8px;padding:10px;margin-top:10px;font-size:0.8rem;color:#744210;">'
            'Roth conversions before age 73 reduce your taxable RMD burden.'
            '</div></div>',
            unsafe_allow_html=True
        )
