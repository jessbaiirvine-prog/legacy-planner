import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import json
from io import BytesIO

st.set_page_config(layout="wide", page_title="Legacy Master 13.0")

# --- 1. PERSISTENCE ---
def get_v(key, default):
    return st.session_state[key] if key in st.session_state else default

# --- 2. SIDEBAR ---
sb = st.sidebar
sb.title("⚙️ Strategic Planning")

# MONTE CARLO CONTROLS
sb.markdown("### 🎲 SIMULATION SETTINGS")
use_monte = sb.toggle("Enable Monte Carlo", value=False)
if use_monte:
    iterations = sb.select_slider("Simulations", options=[100, 500, 1000], value=500)
    mkt_vol = sb.slider("Market Volatility (Std Dev %)", 5, 25, 15) / 100
    re_vol = sb.slider("RE Volatility (Std Dev %)", 1, 10, 3) / 100
else:
    iterations = 1

# [Standard inputs for Real Estate, Assets, and Career follow the v12.5 structure...]
# (I'll keep the logic lean here so you can paste it into your existing file)

# [Placeholder for existing Sidebar logic from v12.5: RE, Assets, Career, College]
# Make sure to include 'roi', 'a' (appreciation), and 'plist' from previous version.

# --- 3. MONTE CARLO ENGINE ---
all_sims = []

# We wrap the math in a loop for iterations
for sim_id in range(iterations):
    res = []
    cc, cd, cr = v_c, v_d, v_r
    
    for age in range(int(ca), int(ea) + 1):
        sim_yr = 2026 + (age - int(ca))
        
        # RANDOMIZATION STEP
        if use_monte:
            # We "roll the dice" for this specific year in this specific simulation
            yr_roi = np.random.normal(roi, mkt_vol)
            yr_appr = np.random.normal(0.03, re_vol) # Mean 3% appreciation
        else:
            yr_roi = roi
            yr_appr = 0.03
            
        cc *= 1.02 # Inflation on cash
        cd *= (1 + yr_roi); cr *= (1 + yr_roi)
        
        # [Insert Income/Expense Logic from v12.5 here...]
        # Ensure re_noi and re_eq use 'yr_appr' instead of a static 'o["a"]'
        
        # Calculate Net Worth for this year/sim
        # nw = cc + cd + cr + re_eq
        res.append(nw)
    
    all_sims.append(res)

# --- 4. DATA PROCESSING ---
sim_matrix = np.array(all_sims)
ages = np.arange(int(ca), int(ea) + 1)

# Calculate Percentiles
p10 = np.percentile(sim_matrix, 10, axis=0)
p50 = np.percentile(sim_matrix, 50, axis=0)
p90 = np.percentile(sim_matrix, 90, axis=0)

# Success Rate (Percentage of sims ending > 0)
final_balances = sim_matrix[:, -1]
success_rate = (final_balances > 0).mean() * 100

# --- 5. OUTPUT ---
st.title("🛡️ Legacy Master v13.0")

# Metrics
c1, c2, c3 = st.columns(3)
c1.metric("Median Final Estate", f"${p50[-1]:,.0f}")
c2.metric("Success Probability", f"{success_rate:.1f}%")
c3.metric("Status", "OPTIMAL" if success_rate > 90 else "VULNERABLE")

# Monte Carlo Chart
fig = go.Figure()
if use_monte:
    # Shaded Area for Confidence Interval
    fig.add_trace(go.Scatter(x=ages, y=p90, line=dict(width=0), name="Top 10% (Best Case)"))
    fig.add_trace(go.Scatter(x=ages, y=p10, line=dict(width=0), fill='tonexty', fillcolor='rgba(59, 130, 246, 0.2)', name="Confidence Zone"))
    fig.add_trace(go.Scatter(x=ages, y=p50, line=dict(color='#3b82f6', width=3), name="Median Outcome"))
else:
    fig.add_trace(go.Scatter(x=ages, y=p50, line=dict(color='#10b981', width=4), name="Deterministic Path"))

fig.update_layout(template="plotly_dark", title="Wealth Projection (Confidence Intervals)", hovermode="x unified")
st.plotly_chart(fig, width="stretch")

# [Insert Master Ledger and Export code from v12.5 here...]
