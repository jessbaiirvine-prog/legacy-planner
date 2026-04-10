import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide")

# --- 1. LHS MODULES ---
sb = st.sidebar
sb.title("⚙️ Strategic Planning")

with sb.expander("🏠 RE INVESTMENT", expanded=True):
    n_p = sb.number_input("Property Count", value=1)
    p_list = []
    for i in range(int(n_p)):
        st.markdown(f"**Prop {i+1}**")
        v = st.number_input("Value", value=1000000.0, key=f"v{i}")
        l = st.number_input("Loan", value=700000.0, key=f"l{i}")
        y = st.number_input("Year", value=2020, key=f"y{i}")
        t = st.number_input("Term", value=30, key=f"t{i}")
        r = st.number_input("Rate%", value=4.5, key=f"r{i}")/100
        a = st.number_input("Appr%", value=3.0, key=f"a{i}")/100
        n = st.number_input("NetRent", value=0.0, key=f"n{i}")
        pmt = 0
        if l > 0 and r > 0:
            mi, mt = r/12, t*12
            pw = (1+mi)**mt
            mp = l*(mi*pw)/(pw-1)
            pmt = mp*12
        p_list.append({"v":v,"l":l,"y":y,"t":t,"r":r,"a":a,"p":pmt,"n":n*12})

with sb.expander("🏦 RETIREMENT", expanded=False):
    v_pre = st.number_input("401k Pre", value=1200000.0)
    v_rth = st.number_input("Roth/HSA", value=150000.0)
    m_roi = st.number_input("ROI%", value=6.0)/100

with sb.expander("💵 CASH ASSETS", expanded=False):
    v_csh = st.number_input("Cash", value=200000.0)
    h_pay = st.number_input("Husband Net", value=145000.0)
    y_pay = st.number_input("Your Net", value=110000.0)

with sb.expander("🎓 KIDS TUITION", expanded=False):
    n_k = st.number_input("Kids", value=2)
    tui = st.number_input("Annual Tui", value=50000.0)
    k_s = [st.number_input(f"K{i+1} Age", value=52+(i*6)) for i in range(int(n_k))]

with sb.expander("📅 TIMELINE", expanded=False):
    c_a = st.number_input("Age", value=42)
    y_r = st.number_input("Retire", value=55)
    e_a = st.number_input("End", value=95)
    ex_w = st.number_input("Exp Work", value=150000.0)
    ex_r = st.number_input("Exp Ret", value=120000.0)

# --- 2. MATH ---
res = []
cc, cd, cr = v_csh, v_pre, v_rth
fail_yr = None

for age in range(int(c_a), int(e_a)+1):
    yr = 2026 + (age - int(c_a))
    cd *= (1 + m_roi)
    cr *= (1 + m_roi)
    inc = (h_pay + y_pay) if age < y_r else 85000
    exp = ex_w if age < y_r else ex_r
    edu = sum(tui for s in k_s if s <= age < s+4)
    
    eq, pmt, noi = 0, 0, 0
    for p in p_list:
        h = yr - p["y"]
        if h < 0: continue
        val = p["v"] * ((1+p["a"])**h)
        noi += p["n"] * ((1+p["a"])**h)
        if h < p["t"]:
            m, t, d = p["r"]/12, p["t"]*12, h*12
            deb = p["l"]*((1+m)**t - (1+m)**d)/((1+m)**t - 1)
            pmt += p["p"]
        else: deb = 0
        eq += (val - deb)

    cc += (inc + noi - exp - edu - pmt)
    if cc < 0 and fail_yr is None: fail_yr = yr
    res.append({"Age":age,"Cash":cc,"Def":cd,"Roth":cr,"RE":eq,"NW":cc+cd+cr+eq})

# --- 3. OUTPUT ---
st.title("✨ Legacy 9.3")
if fail_yr:
    st.warning(f"Math won't work out: Cash hits zero in {fail_yr}.")

df = pd.DataFrame(res)
st.metric("Final Estate", f"${df.iloc[-1]['NW']:,.0f}")

fig = go.Figure()
for c, clr in [("Cash","#3b82f6"),("Roth","#10b981"),("Def","#8b5cf6"),("RE","#f59e0b")]:
    fig.add_trace(go.Bar(x=df["Age"], y=df[c], name=c, marker_color=clr))

fig.update_layout(barmode='stack', template="plotly_dark")
st.plotly_chart(fig, use_container_width=True)

with st.expander("📊 LEDGER"):
    st.dataframe(df.style.format("${:,.0f}"))
