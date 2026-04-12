import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import json

st.set_page_config(layout="wide", page_title="Legacy Master 32.0", page_icon="🎓")

# --- 1. INITIALIZATION ---
DEFAULT_PROP = {
    "v": 1700000.0, "b": 1000000.0, "l": 800000.0, "p_year": 2020, 
    "term": 30, "rate": 0.045, "r": 6500.0, "a": 0.03, "liq_age": 55, "liq_active": True
}
DEFAULTS = {
    "v_c": 200000.0, "v_d": 1200000.0, "v_r": 500000.0,
    "tax_work": 0.30, "tax_ret": 0.20, "cap_gains": 0.20, "target_roi": 0.07, "volatility": 0.15,
    "p_tax": 0.012, "p_maint": 0.01, "p_mgmt": 0.08,
    "props": [DEFAULT_PROP.copy()],
    "k1_start": 18, "k1_end": 22, "k1_cost": 50000.0, 
    "k2_start": 18, "k2_end": 22, "k2_cost": 50000.0,
    "ca": 42, "ea": 95, "hp": 145000.0, "hr": 58, "yp": 110000.0, "yr": 55, 
    "ew": 150000.0, "er": 120000.0, "ss": 85000.0
}

if "inputs" not in st.session_state:
    st.session_state.inputs = DEFAULTS.copy()

inp = st.session_state.inputs
sb = st.sidebar

# --- 2. SIDEBAR (LHS) ---
sb.title("💾 Scenario Setup")
uploaded_file = sb.file_uploader("Upload Scenario", type="json")
if uploaded_file:
    inp.update(json.load(uploaded_file))
    st.rerun()

with sb.expander("🎲 Risk & Market", expanded=False):
    use_monte = st.toggle("Monte Carlo", value=True)
    n_sims = st.slider("Simulations", 10, 2000, 500)
    inp["target_roi"] = st.slider("ROI %", 0.0, 15.0, float(inp.get("target_roi", 0.07)*100))/100
    inp["volatility"] = st.slider("Volatility %", 5, 30, int(inp.get("volatility", 0.15)*100))/100

with sb.expander("🏠 Real Estate Engine", expanded=True):
    n_p = st.number_input("Property Count", 1, 10, len(inp["props"]))
    while len(inp["props"]) < n_p: inp["props"].append(DEFAULT_PROP.copy())
    inp["props"] = inp["props"][:n_p]
    for i, p in enumerate(inp["props"]):
        st.markdown(f"**Prop {i+1}**")
        p["v"] = st.number_input(f"Val {i+1}", value=float(p["v"]), key=f"v{i}")
        p["l"]
