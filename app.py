import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Legacy 8.2")

# --- 1. UI SLOTS (FOR TOP-DOWN DISPLAY) ---
# We reserve the top of the page for results.
slot_top = st.container()
slot_mid = st.container()

# --- 2. SIDEBAR ---
sb = st.sidebar
sb.title("⚙️ Global Settings")
c_a = sb.slider("Current Age", 30, 65, 42)
y_r = sb.slider("Your Retire Age", 45, 75, 55)
h_r = sb.slider("Husband Retire Age", 45, 75, 58)
e_a = sb.slider("End Age", 80, 110, 95)

sb.subheader("💰 Liquid Assets")
v_t = sb.number_input("Taxable Cash", 200000)
v_d = sb.number_input("401k", 1200000)
v_f = sb.number_input("Roth", 300000)
roi = sb.slider("Return %", 1, 10, 6) / 100

sb.subheader("💼 Careers & Kids")
h_i = sb.number_input("Husband Net", 145000)
y_i = sb.number_input("Your Net", 110000)
ex_w = sb.number_input("Exp (Work)", 150000)
ex_r = sb.number_input("Exp (Retire)", 120000)
n_k = sb.number_input("Kids", 0, 5, 2)
tui = sb.number_input("Tuition", 50000)
k_s = []
for i in range(int(n_k)):
    ks = sb.number_input(f"K{i+1} Start Age", 40, 75, 52+(i*6))
    k_s.append(ks)

# --- 3. REAL ESTATE INPUTS ---
st.header("🏠 Real Estate Portfolio")
n_p = st.number_input("Count", 1, 10, 1)
p_list = []

for i in range(int(n_p)):
    with st.expander(f"Property {i+1}", expanded=(i==0)):
        cl1, cl2, cl3 = st.columns(3)
        with cl1:
            val = st.number_input("Price", 0, 10**7, 950000 if i==0 else 0, key=f"v{i}")
            lon = st.number_input("Loan", 0, 10**7, 700000 if i==0 else 0, key=f"l{i}")
        with cl2:
            yr = st.number_input("Year", 1990, 2040, 2020 if i==0 else 2026, key=f"y{i}")
            trm = st.number_input("Term", 5, 50, 30, key=f"t{i}")
        with cl3:
            rat = st.number_input("Rate %", 0.0, 15.0, 4.5, key=f"r{i}") / 100
            apr = st.slider("Appr %", 0, 10, 3, key=f"a{i}") / 100
        
        # Cash Flow / NOI Input
        noi = st.number_input("Monthly Net Rent", -5000, 50000, 0, key=f"n{i}")
        
        # Amortization Formula (Broken into safe chunks)
        ann_p = 0
        if lon > 0 and rat > 0:
            mi = rat / 12
            mt = trm * 12
            pw = (1 + mi) ** mt
            mp = lon * (mi * pw) / (pw - 1)
            ann_p = mp * 12
        
        p_list.append({
            "v": val, "l": lon, "y": yr, "t": trm, 
            "r": rat, "a": apr, "p": ann_p, "n": noi * 12
        })

# --- 4. MATH ENGINE ---
sim = []
c_t, c_d, c_f = v_t, v_d, v_f
now = 2026

for a in range(c_a, e_a + 1):
    yr = now + (a - c_a)
    c_t *= (1 + roi)
    c_d *= (1 + roi)
    c_f *= (1 + roi)
    
    # Career Income
    inc = 0
    if a < h_r: inc += h_i
    if a < y_r: inc += y_i
    if a >= 67: inc += 85000 # SS
    
    # Lifestyle & College
    exp = ex_r if (a >= y_r and a >= h_r) else ex_w
    edu = sum(tui for s in k_s if s <= a < s + 4)
    
    # RE Assets
    r_eq, r_pm, r_in = 0, 0, 0
    for p in p_list:
        h = yr - p["y"]
        if h < 0: continue
        
        cur_v = p["v"] * ((1 + p["a"]) ** h)
        cur_n = p["n"] * ((1 + p["a"]) ** h) # Rent growth
        
        if h >= p["t"]:
            cur_d = 0
        else:
            mi = p["r"] / 12
            mt = p["t"] * 12
            dn = h * 12
            # Balance calculation (Broken lines)
            p_m = (1 + mi) ** mt
            p_d = (1 + mi) ** dn
            cur_d = p["l"] * (p_m - p_d) / (p_m - 1)
            r_pm += p["p"]
        
        r_eq += (cur_v - cur_d)
        r_in += cur_n

    c_t += (inc + r_in - exp - edu - r_pm)
    nw = c_t + c_d + c_f + r_eq
    
    sim.append({
        "Age": a, "Year": yr, "Tax": c_t, 
        "Def": c_d, "Rot": c_f, "RE": r_eq, "NW": nw
    })

df = pd.DataFrame(sim)

# --- 5. FILL TOP SLOTS ---
with slot_top:
    st.title("✨ Legacy Master v8.2")
    m1, m2, m3, m4 = st.columns(4)
    v1 = df.iloc[0]['NW']
    m1.metric("Current NW", f"${v1:,.0f}")
    
    df_r = df[df['Age'] == y_r]
    v2 = df_r['NW'].values[0] if not df_r.empty else 0
    m2.metric("At Retire", f"${v2:,.0f}")
    
    v3 = df.iloc[-1]['NW']
    m3.metric("Final Estate", f"${v3:,.0f}")
    m4.metric("Year", f"{now}")

with slot_mid:
    fig = go.Figure()
    ly = [("Tax","#3b82f6"),("Rot","#10b981"),("Def","#8b5cf6"),("RE","#f59e0b")]
    for c, cl in ly:
        fig.add_trace(go.Scatter(
            x=df["Age"], y=df[c], name=c, 
            stackgroup='1', fillcolor=cl, line=dict(width=0)
        ))
    
    fig.update_layout(
        template="plotly_dark", height=450, 
        margin=dict(t=10,b=10), legend=dict(orientation="h",y=1.1)
    )
    st.plotly_chart(fig, use_container_width=True)

with st.expander("Yearly Ledger"):
    st.dataframe(df)
