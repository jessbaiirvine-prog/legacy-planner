import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Legacy Planner v5.7", layout="wide")

# --- 1. SIDEBAR INPUTS ---
with st.sidebar:
    st.header("Milestones")
    c_a = st.slider("Current Age", 30, 65, 42)
    y_r = st.slider("Your Retire Age", 45, 75, 55)
    h_r = st.slider("Husband Retire Age", 45, 75, 58)
    ss_a = st.slider("SS Age", 62, 72, 67)
    d_a = st.slider("End Age", 80, 110, 95)
    
    st.header("Returns")
    r4 = st.slider("40s %", 0.0, 15.0, 7.0)/100
    r5 = st.slider("50s %", 0.0, 15.0, 5.0)/100
    r6 = st.slider("60+ %", 0.0, 10.0, 4.0)/100

    st.header("Education & Finance")
    n_k = st.number_input("Kids", 0, 5, 2)
    tui = st.number_input("Tuition ($)", 50000)
    k_s = [st.number_input(f"K{i+1} Start", 40, 75, 52+(i*6), key=f"k{i}") for i in range(n_k)]
    h_n = st.number_input("Husband Net ($)", 145000)
    y_n = st.number_input("Your Net ($)", 110000)
    ex_w = st.number_input("Work Exp ($)", 210000)
    ex_r = st.number_input("Retire Exp ($)", 150000)

# --- 2. BOTTOM SECTION DATA (RE) ---
st.title("🌏 Legacy Master v5.7")
st.subheader("🏠 Real Estate Asset Management")
re_data = []
cols = st.columns(3)
for i in range(6):
    with cols[i % 3]:
        with st.expander(f"Property {i+1}", expanded=(i<4)):
            is_p = st.checkbox("Primary?", i==0, key=f"p{i}")
            p_cf = 0 if is_p else st.number_input("Cashflow", 7800 if i<4 else 0, key=f"c{i}")
            p_s = st.number_input("Mtg Start", 35, key=f"s{i}")
            p_t = st.number_input("Term", 30, key=f"t{i}")
            p_m = st.number_input("Payment", 15000 if i<4 else 0, key=f"m{i}")
            re_data.append({"cf": p_cf, "s": p_s, "e": p_s+p_t, "m": p_m})

#
