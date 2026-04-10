import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Legacy Master 10.0")

# --- 1. SIDEBAR MODULES ---
sb = st.sidebar
sb.title("⚙️ Strategic Planning")

with sb.expander("🏠 RE INVESTMENT & SALES", expanded=True):
    np = sb.number_input("Total Properties Owned", value=1, min_value=0)
    # LIQUIDATION INPUTS
    st.markdown("---")
    st.markdown("**Liquidation Strategy**")
    n_sell = sb.number_input("Number of Properties to Sell", value=0, min_value=0, max_value=int(np))
    sell_age = sb.number_input("Sell at Your Age", value=65)
    sell_cost = sb.number_input("Sales Costs/Tax %", value=10.0) / 100
    st.markdown("---")
    
    plist = []
    for i in range(int(np)):
        st.markdown(f"**Property {i+1}**")
        v = sb.number_input("Current Value", value=1700000.0, key=f"re_v{i}")
        l = sb.number_input("Loan Balance", value=0.0, key=f"re_l{i}")
        y = sb.number_input("Year Purchased", value=2020, key=f"re_y{i}")
        t = sb.number_input("Loan Term (Yrs)", value=30, key=f"re_t{i}")
        r = sb.number_input("Int. Rate %", value=4.5, key=f"re_r{i}") / 100
        a = sb.number_input("Annual Appr %", value=3.0, key=f"re_a{i}") / 100
        n = sb.number_input("Monthly Net Rent", value=4000.0, key=f"re_n{i}")
        p = 0
        if l > 0 and r > 0:
            mi, mt = r/12, t*12
            pw = (1 + mi)**mt
            p = l * (mi * pw) / (pw - 1)
        plist.append({"v":v,"l":l,"y":y,"t":t,"r":r,"a":a,"p":p*12,"n":n*12})

with sb.expander("🏦 RETIREMENT BUCKETS", expanded=False):
    v_d = sb.number_input("401k (Deferred)", value=1200000.0)
    v_r = sb.number_input("Roth/HSA (Tax-Free)", value=500000.0)
    roi = sb.number_input("Market ROI %", value=6.0) / 100

with sb.expander("🎓 KIDS TUITION", expanded=False):
    nk = sb.number_input("Number of Kids", value=2)
    tui_yr = sb.number_input("Annual Tuition", value=50000.0)
    k_ages = [sb.number_input(f"K{i+1} College Start (Age)", value=52+(i*5)) for i in range(int(nk))]

with sb.expander("💵 CASH & DUAL TIMELINE", expanded=False):
    v_c = sb.number_input("Current Savings", value=200000.0)
    ca = sb.number_input("Your Current Age", 42)
    hp, yp = sb.number_input("Husband Salary", 145000.0), sb.number_input("Your Salary", 110000.0)
    yr, hr = sb.number_input("Your Retire Age", 55), sb.number_input("Husband Retire Age", 58)
    ea = sb.number_input("End Age", 95)
    ew, er = sb.number_input("Exp (Working)", 150000.0), sb.number_input("Exp (Retired)", 120000.0)

# --- 2. MATH ENGINE ---
res, res_cf = [], []
cc, cd, cr = v_c, v_d, v_r
fail_yr = None

for age in range(int(ca), int(ea) + 1):
    sim_yr = 2026 + (age - int(ca))
    cc *= 1.02; cd *= (1 + roi); cr *= (1 + roi)
    
    # Incomes
    inc_h, inc_y = (hp if age < hr else 0), (yp if age < yr else 0)
    inc_ss = 85000 if age >= 67 else 0
    exp_life = -(ew if (age < yr or age < hr) else er)
    
    edu = sum(-tui_yr for s in k_ages if s <= age < s + 4)

    re_eq, re_pmt, re_noi, re_sale_gain = 0, 0, 0, 0
    
    for i, o in enumerate(plist):
        h = sim_yr - o["y"]
        if h < 0: continue
        
        val = o["v"] * ((1 + o["a"]) ** h)
        
        # Determine if property is sold
        is_sold = (i < n_sell) and (age >= sell_age)
        was_sold_this_year = (i < n_sell) and (age == sell_age)
        
        # Remaining Debt Logic
        deb = 0
        if h < o["t"]:
            m, mt, dn = o["r"]/12, o["t"]*12, h*12
            deb = o["l"] * ((1+m)**mt - (1+m)**dn) / ((1+m)**mt - 1)
        
        if is_sold:
            if was_sold_this_year:
                # Capture net proceeds after debt and sales cost
                re_sale_gain += (val - deb) * (1 - sell_cost)
            continue # Property no longer provides equity/rent/debt in future years
        
        re_eq += (val - deb)
        re_noi += o["n"] * ((1 + o["a"]) ** h)
        if h < o["t"]: re_pmt -= o["p"]

    cc += (inc_h + inc_y + inc_ss + re_noi + exp_life + re_pmt + edu + re_sale_gain)
    if cc < 0 and fail_yr is None: fail_yr = sim_yr
        
    res.append({"Age": age, "Year": sim_yr, "Cash": max(0, cc), "401k": cd, "Roth": cr, "RE": re_eq, "NW": max(0, cc) + cd + cr + re_eq})
    res_cf.append({"Age": age, "Income": inc_h+inc_y+inc_ss+re_noi, "Spend": exp_life+re_pmt+edu, "Sale": re_sale_gain})

# --- 3. OUTPUT ---
st.title("🛡️ Legacy Master v10.0: Liquidation Ready")
df, df_cf = pd.DataFrame(res), pd.DataFrame(res_cf)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Current NW", f"${df.iloc[0]['NW']:,.0f}")
c2.metric(f"NW @ Age {yr}", f"${df[df['Age']==yr]['NW'].values[0]:,.0f}")
c3.metric("Final Estate", f"${df.iloc[-1]['NW']:,.0f}")
c4.metric("Status", "HEALTHY" if not fail_yr else "DEFICIT", delta=None if not fail_yr else f"Hits Zero {fail_yr}", delta_color="inverse")

st.markdown("### 📈 Total Wealth Projection")
st.plotly_chart(go.Figure(data=[go.Bar(x=df["Age"], y=df["NW"], marker_color="#0ea5e9")], layout=dict(template="plotly_dark", height=400)), use_container_width=True)

st.markdown("### 📂 Asset Portfolio Breakdown")
fig2 = go.Figure()
for c, clr in [("RE","#f59e0b"),("401k","#8b5cf6"),("Roth","#10b981"),("Cash","#3b82f6")]:
    fig2.add_trace(go.Bar(x=df["Age"], y=df[c], name=c, marker_color=clr))
st.plotly_chart(fig2.update_layout(barmode='group', template="plotly_dark", height=400), use_container_width=True)

st.markdown("### 💸 Cash Flow Audit (Income vs. Spending Peaks)")
fig3 = go.Figure()
fig3.add_trace(go.Bar(x=df_cf["Age"], y=df_cf["Income"], name="Total Inflow", marker_color="#3b82f6"))
fig3.add_trace(go.Bar(x=df_cf["Age"], y=df_cf["Spend"], name="Total Outflow", marker_color="#ef4444"))
fig3.add_trace(go.Bar(x=df_cf["Age"], y=df_cf["Sale"], name="Property Sale Proceeds", marker_color="#10b981"))
st.plotly_chart(fig3.update_layout(barmode='relative', template="plotly_dark", height=400), use_container_width=True)

with st.expander("🔎 View Annual Audit Ledger"):
    st.dataframe(df.style.format("${:,.0f}"))
