import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Legacy Master 11.1")

# --- 0. PERSISTENCE ENGINE ---
# This block ensures that if the app reruns, it checks for existing values first.
def get_val(key, default):
    return st.session_state[key] if key in st.session_state else default

# --- 1. SIDEBAR MODULES ---
sb = st.sidebar
sb.title("⚙️ Strategic Planning")

# --- PROPERTY MODULE ---
with sb.expander("🏠 REAL ESTATE PORTFOLIO", expanded=True):
    np = sb.number_input("Number of Properties", value=get_val("np", 1), min_value=0, key="np")
    plist = []
    
    for i in range(int(np)):
        st.markdown(f"### 📍 Property {i+1}")
        v = st.number_input(f"Value P{i+1}", value=get_val(f"v{i}", 1700000.0), key=f"v{i}")
        l = st.number_input(f"Loan P{i+1}", value=get_val(f"l{i}", 0.0), key=f"l{i}")
        n = st.number_input(f"Rent P{i+1}", value=get_val(f"n{i}", 4000.0), key=f"n{i}")
        
        col_a, col_b = st.columns(2)
        y = col_a.number_input(f"Year Purchased P{i+1}", value=get_val(f"y{i}", 2020), key=f"y{i}")
        t = col_b.number_input(f"Loan Term P{i+1}", value=get_val(f"t{i}", 30), key=f"t{i}")
        
        col_c, col_d = st.columns(2)
        r = col_c.number_input(f"Rate % P{i+1}", value=get_val(f"r{i}", 4.5), key=f"r{i}") / 100
        a = col_d.number_input(f"Appr. % P{i+1}", value=get_val(f"a{i}", 3.0), key=f"a{i}") / 100
        
        do_sell = st.checkbox(f"Sell P{i+1}?", value=get_val(f"sell_check{i}", False), key=f"sell_check{i}")
        s_age = st.number_input(f"Sell at age P{i+1}", value=get_val(f"sell_age{i}", 65), key=f"sell_age{i}") if do_sell else 999
        
        p = 0
        if l > 0 and r > 0:
            mi, mt = r/12, t*12
            pw = (1 + mi)**mt
            p = l * (mi * pw) / (pw - 1)
        
        plist.append({"v":v,"l":l,"y":y,"t":t,"r":r,"a":a,"p":p*12,"n":n*12,"sell":do_sell,"age":s_age})
        st.markdown("---")

with sb.expander("🏦 RETIREMENT BUCKETS", expanded=False):
    v_d = sb.number_input("401k (Deferred)", value=get_val("v_d", 1200000.0), key="v_d")
    v_r = sb.number_input("Roth/HSA (Tax-Free)", value=get_val("v_r", 500000.0), key="v_r")
    roi = sb.number_input("Market ROI %", value=get_val("roi_pct", 6.0), key="roi_pct") / 100

with sb.expander("🎓 KIDS TUITION", expanded=False):
    nk = sb.number_input("Number of Kids", value=get_val("nk", 2), key="nk")
    tui_yr = sb.number_input("Annual Tuition", value=get_val("tui_yr", 50000.0), key="tui_yr")
    k_ages = [sb.number_input(f"K{i+1} College Start", value=get_val(f"k{i}", 52+(i*5)), key=f"k{i}") for i in range(int(nk))]

with sb.expander("💵 CASH & DUAL TIMELINE", expanded=True):
    v_c = sb.number_input("Current Savings", value=get_val("v_c", 200000.0), key="v_c")
    ca = sb.number_input("Your Current Age", value=get_val("ca", 42), key="ca")
    hp = sb.number_input("Husband Salary", value=get_val("hp", 145000.0), key="hp")
    yp = sb.number_input("Your Salary", value=get_val("yp", 110000.0), key="yp")
    yr = sb.number_input("Your Retire Age", value=get_val("yr", 55), key="yr")
    hr = sb.number_input("Husband Retire Age", value=get_val("hr", 58), key="hr")
    # FLEXIBLE END AGE (NO MINIMUM)
    ea = sb.number_input("End Age (Simulation)", value=get_val("ea", 95), key="ea")
    ew = sb.number_input("Exp (Working)", value=get_val("ew", 150000.0), key="ew")
    er = sb.number_input("Exp (Retired)", value=get_val("er", 120000.0), key="er")

# --- 2. MATH ENGINE ---
res, res_cf = [], []
cc, cd, cr = v_c, v_d, v_r
fail_yr = None

for age in range(int(ca), int(ea) + 1):
    sim_yr = 2026 + (age - int(ca))
    cc *= 1.02; cd *= (1 + roi); cr *= (1 + roi)
    
    inc_h, inc_y = (hp if age < hr else 0), (yp if age < yr else 0)
    inc_ss = 85000 if age >= 67 else 0
    exp_life = -(ew if (age < yr or age < hr) else er)
    edu = sum(-tui_yr for s in k_ages if s <= age < s + 4)

    re_eq, re_pmt, re_noi, re_sale_gain = 0, 0, 0, 0
    for i, o in enumerate(plist):
        h = sim_yr - o["y"]
        if h < 0: continue
        val = o["v"] * ((1 + o["a"]) ** h)
        is_sold = o["sell"] and (age >= o["age"])
        was_sold_now = o["sell"] and (age == o["age"])
        
        deb = 0
        if h < o["t"]:
            m, mt, dn = o["r"]/12, o["t"]*12, h*12
            deb = o["l"] * ((1+m)**mt - (1+m)**dn) / ((1+m)**mt - 1)
        
        if is_sold:
            if was_sold_now: re_sale_gain += (val - deb) * 0.90
            continue
        re_eq += (val - deb); re_noi += o["n"] * ((1 + o["a"]) ** h)
        if h < o["t"]: re_pmt -= o["p"]

    cc += (inc_h + inc_y + inc_ss + re_noi + exp_life + re_pmt + edu + re_sale_gain)
    if cc < 0 and fail_yr is None: fail_yr = sim_yr
        
    res.append({"Age": age, "Year": sim_yr, "Cash": max(0, cc), "401k": cd, "Roth": cr, "RE": re_eq, "NW": max(0, cc) + cd + cr + re_eq})
    res_cf.append({"Age": age, "Husband": inc_h, "You": inc_y, "Rent": re_noi, "SS": inc_ss, "Sales": re_sale_gain, "Life": exp_life, "Tui": edu, "Mort": re_pmt})

# --- 3. OUTPUT ---
st.title("🛡️ Legacy Master v11.1")
df, df_cf = pd.DataFrame(res), pd.DataFrame(res_cf)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Current NW", f"${df.iloc[0]['NW']:,.0f}")
c2.metric(f"NW @ Age {yr}", f"${df[df['Age']==yr]['NW'].values[0]:,.0f}")
c3.metric("Final Estate", f"${df.iloc[-1]['NW']:,.0f}")
c4.metric("Status", "HEALTHY" if not fail_yr else "DEFICIT", delta=None if not fail_yr else f"Shortage {fail_yr}", delta_color="inverse")

# Main Charts
st.plotly_chart(go.Figure(data=[go.Bar(x=df["Age"], y=df[c], name=c, marker_color=clr) for c, clr in [("RE","#f59e0b"),("401k","#8b5cf6"),("Roth","#10b981"),("Cash","#3b82f6")]], layout=dict(barmode='stack', template="plotly_dark", title="Total Wealth Stack")), use_container_width=True)

# Stacked Cash Flow
fig2 = go.Figure()
for c, clr in [("Husband","#1e3a8a"),("You","#3b82f6"),("Rent","#1d4ed8"),("SS","#60a5fa"),("Sales","#10b981")]:
    fig2.add_trace(go.Bar(x=df_cf["Age"], y=df_cf[c], name=c, marker_color=clr))
for c, clr in [("Life","#991b1b"),("Mort","#dc2626"),("Tui","#ef4444")]:
    fig2.add_trace(go.Bar(x=df_cf["Age"], y=df_cf[c], name=c, marker_color=clr))
st.plotly_chart(fig2.update_layout(barmode='relative', template="plotly_dark", title="Annual Inflow/Outflow Peaks"), use_container_width=True)

with st.expander("🔎 View Annual Audit Ledger"):
    st.dataframe(df.style.format("${:,.0f}"))
