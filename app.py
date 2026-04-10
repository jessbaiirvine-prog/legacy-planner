import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Legacy 7.9")

# --- UI STYLING ---
st.markdown("""
<style>
div[data-testid="metric-container"] {
    background-color: #1e1e2e; border: 1px solid #2b2b40;
    padding: 15px; border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# --- 1. RESERVED TOP SPACE (The "Placeholder" Strategy) ---
# This creates empty slots at the top of the page that we fill later.
header_area = st.container()
chart_area = st.container()

# --- 2. SIDEBAR SETTINGS ---
sb = st.sidebar
sb.header("Timeline")
c_age = sb.slider("Current Age", 30, 65, 42)
y_ret = sb.slider("Your Retire Age", 45, 75, 55)
h_ret = sb.slider("Husband Retire Age", 45, 75, 58)
d_age = sb.slider("End Age", 80, 110, 95)

sb.header("Liquid Portfolio ($)")
v_tax = sb.number_input("Taxable Cash", 200000)
v_def = sb.number_input("Deferred 401k", 1200000)
v_rot = sb.number_input("Roth", 300000)

sb.header("Income & Expenses")
rate = sb.slider("Market Return %", 1, 10, 6) / 100
h_net = sb.number_input("Husband Net Salary", 145000)
y_net = sb.number_input("Your Net Salary", 110000)
e_wrk = sb.number_input("Work Lifestyle Exp (Excl Mtg)", 150000)
e_ret = sb.number_input("Retire Lifestyle Exp (Excl Mtg)", 120000)

sb.header("Education")
n_kid = sb.number_input("Number of Kids", 0, 5, 2)
tui = sb.number_input("Annual Tuition ($)", 50000)
k_sts = [sb.number_input(f"K{i+1} Start Age", 40, 75, 52+(i*6)) for i in range(int(n_kid))]

# --- 3. BOTTOM INPUTS (Real Estate) ---
# We place these in the code BEFORE the math so the math can see them.
st.divider()
st.subheader("🏠 Real Estate Asset Details")
cols = st.columns(3)
p_data = []

for i in range(3):
    with cols[i]:
        with st.container(border=True):
            st.write(f"**Property {i+1}**")
            v = st.number_input("Purchase Price", 0, 10000000, 950000 if i==0 else 0, key=f"v{i}")
            l = st.number_input("Orig. Loan Amount", 0, 10000000, 700000 if i==0 else 0, key=f"l{i}")
            y = st.number_input("Year of Purchase", 1990, 2040, 2020 if i==0 else 2026, key=f"y{i}")
            t = st.number_input("Term (Years)", 5, 50, 30, key=f"t{i}")
            r = st.number_input("Interest Rate (%)", 0.0, 15.0, 4.5, key=f"i{i}") / 100
            a = st.slider("Appreciation %", 0, 10, 3, key=f"g{i}") / 100

            # Calc Annual Mortgage Payment
            ann_pmt = 0
            if l > 0 and r > 0:
                mi = r / 12
                mt = t * 12
                pwr = (1 + mi) ** mt
                mpmt = l * (mi * pwr) / (pwr - 1)
                ann_pmt = mpmt * 12
            
            p_data.append({"v": v, "l": l, "y": y, "t": t, "r": r, "a": a, "pmt": ann_pmt})

# --- 4. MATH ENGINE ---
sim_data = []
t_tax, t_def, t_rot = v_tax, v_def, v_rot
curr_yr = 2026

for age in range(c_age, d_age + 1):
    yr = curr_yr + (age - c_age)
    
    # Portfolio Growth
    t_tax *= (1 + rate)
    t_def *= (1 + rate)
    t_rot *= (1 + rate)
    
    # Inflow
    inc = (h_net if age < h_ret else 0) + (y_net if age < y_ret else 0)
    if age >= 67: inc += 85000 # SS Estimate
    
    # Outflow
    exp_l = e_ret if (age >= y_ret and age >= h_ret) else e_wrk
    exp_e = sum(tui for s in k_sts if s <= age < s + 4)
    
    # Real Estate
    re_eq, re_pmts = 0, 0
    for p in p_data:
        held = yr - p["y"]
        if held < 0: continue
        
        cur_v = p["v"] * ((1 + p["a"]) ** held)
        
        if held >= p["t"]:
            cur_d = 0
        else:
            mi, mt, done = p["r"]/12, p["t"]*12, held*12
            p_mt, p_dn = (1+mi)**mt, (1+mi)**done
            cur_d = p["l"] * ((p_mt - p_dn) / (p_mt - 1))
            re_pmts += p["pmt"]
        
        re_eq += (cur_v - cur_d)

    t_tax += (inc - exp_l - exp_e - re_pmts)
    nw = t_tax + t_def + t_rot + re_eq
    
    sim_data.append({
        "Age": age, "Year": yr, "Taxable": t_tax, "Deferred": t_def,
        "Roth": t_rot, "RE_Equity": re_eq, "NetWorth": nw
    })

df = pd.DataFrame(sim_data)

# --- 5. FILL THE PLACEHOLDERS (Pushing data to the top) ---
with header_area:
    st.title("✨ Legacy Master v7.9")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Current
