import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide")

# --- 1. SETTINGS ---
with st.sidebar:
    st.header("Milestones")
    ca, yr, hr = st.slider("Current Age",30,65,42), st.slider("Your Retire",45,75,55), st.slider("Husband Retire",45,75,58)
    sa, da = st.slider("SS Age",62,72,67), st.slider("End Age",80,110,95)
    rt = st.slider("Return %",1,10,6)/100
    st.header("Finance")
    hn, yn = st.number_input("Husband Net",145000), st.number_input("Your Net",110000)
    ew, er = st.number_input("Work Exp",210000), st.number_input("Retire Exp",150000)
    st.header("Education")
    nk = st.number_input("Kids",0,5,2)
    tui = st.number_input("Annual Tuition ($)", 50000)
    ks = [st.number_input(f"K{i+1} Start Age",40,75,52+(i*6),key=f"k{i}") for i in range(nk)]

st.title("🌏 Legacy Master v6.0")

# --- 2. REAL ESTATE ---
re = []
cl = st.columns(3)
for i in range(6):
    with cl[i%3]:
        with st.expander(f"RE {i+1}", i<4):
            ip = st.checkbox("Primary?", i==0, key=f"p{i}")
            cf = 0 if ip else st.number_input("Rent", 7800 if i<4 else 0, key=f"c{i}")
            ms, mt = st.number_input("Mtg Start",35,key=f"s{i}"), st.number_input("Term",30,key=f"t{i}")
            mp = st.number_input("Pay", 15000 if i<4 else 0, key=f"m{i}")
            re.append({"f":cf,"s":ms,"e":ms+mt,"p":mp})

# --- 3. MATH ---
p, res = 1700000, []
for a in range(ca, da + 1):
    g = p * rt
    hi = hn if a < hr else 0
    yi = yn if a < yr else 0
    ss = 85000 if a >= sa else 0
    rf = sum([x["f"] for x in re])
    py = sum([x["p"] for x in re if x["s"] <= a < x["e"]])
    ed = sum([tui for s in ks if s <= a < s+4]) # Tuition Logic
    lv = er if (a >= yr and a >= hr) else ew
    
    net = (hi + yi + ss + rf + g) - (lv + py + ed)
    p += net
    res.append({"Age":a, "Growth":g, "Inc":hi+yi+ss+rf, "Exp":-(lv+py+ed), "Port":p})

df = pd.DataFrame(res)

# --- 4. OUTPUTS ---
st.divider()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Final Legacy", f"${df.iloc[-1]['Port']:,.0f}")
c2.metric("At Retire", f"${df[df['Age']==yr]['Port'].values[0]:,.0f}")
c3.metric("Peak Growth", f"${df['Growth'].max():,.0f}")
c4.metric("Total Tuition", f"${nk * tui * 4:,.0f}")

st.subheader("Visual Projections")
f = go.Figure()
f.add_trace(go.Bar(x=df["Age"], y=df["Inc"], name="Income", marker_color="green"))
f.add_trace(go.Bar(x=df["Age"], y=df["Growth"], name="Growth", marker_color="blue"))
f.add_trace(go.Bar(x=df["Age"], y=df["Exp"], name="Outflow", marker_color="red"))
f.add_trace(go.Scatter(x=df["Age"], y=df["Port"], name="Wealth", yaxis="y2", line=dict(color="black")))
f.update_layout(barmode="relative", yaxis2=dict(overlaying="y", side
