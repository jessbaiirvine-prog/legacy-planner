import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide")

# --- INPUTS ---
with st.sidebar:
    st.header("Settings")
    ca = st.slider("Current Age", 30, 65, 42)
    yr = st.slider("Your Retire", 45, 75, 55)
    hr = st.slider("Husband Retire", 45, 75, 58)
    sa = st.slider("SS Age", 62, 72, 67)
    da = st.slider("End Age", 80, 110, 95)
    rt = st.slider("Return %", 1, 10, 6) / 100
    hn = st.number_input("Husband Net", 145000)
    yn = st.number_input("Your Net", 110000)
    ew = st.number_input("Work Exp", 210000)
    er = st.number_input("Retire Exp", 150000)

st.title("🌏 Legacy Master v5.9")

# --- REAL ESTATE ---
re = []
cl = st.columns(3)
for i in range(6):
    with cl[i%3]:
        with st.expander(f"RE {i+1}", i<4):
            ip = st.checkbox("Primary?", i==0, key=f"p{i}")
            cf = 0 if ip else st.number_input("Rent", 7800 if i<4 else 0, key=f"c{i}")
            ms = st.number_input("Mtg Start", 35, key=f"s{i}")
            mt = st.number_input("Term", 30, key=f"t{i}")
            mp = st.number_input("Pay", 15000 if i<4 else 0, key=f"m{i}")
            re.append({"f":cf,"s":ms,"e":ms+mt,"p":mp})

# --- MATH ---
p, res = 1700000, []
for a in range(ca, da + 1):
    g = p * rt
    hi = hn if a < hr else 0
    yi = yn if a < yr else 0
    ss = 85000 if a >= sa else 0
    rf = sum([x["f"] for x in re])
    py = sum([x["p"] for x in re if x["s"] <= a < x["e"]])
    lv = er if (a >= yr and a >= hr) else ew
    
    net = (hi + yi + ss + rf + g) - (lv + py)
    p += net
    res.append({"Age":a, "Growth":g, "Inc":hi+yi+ss+rf, "Exp":-(lv+py), "Port":p})

df = pd.DataFrame(res)

# --- OUTPUTS ---
st.divider()
c1, c2, c3 = st.columns(3)
c1.metric("Final Legacy", f"${df.iloc[-1]['Port']:,.0f}")
c2.metric("At Retire", f"${df[df['Age']==yr]['Port'].values[0]:,.0f}")
c3.metric("Peak Growth", f"${df['Growth'].max():,.0f}")

st.subheader("Visual Projections")
f = go.Figure()
f.add_trace(go.Bar(x=df["Age"], y=df["Inc"], name="Income", marker_color="green"))
f.add_trace(go.Bar(x=df["Age"], y=df["Growth"], name="Growth", marker_color="blue"))
f.add_trace(go.Bar(x=df["Age"], y=df["Exp"], name="Expenses", marker_color="red"))
f.add_trace(go.Scatter(x=df["Age"], y=df["Port"], name="Wealth", yaxis="y2", line=dict(color="black")))
f.update_layout(barmode="relative", yaxis2=dict(overlaying="y", side="right"), height=400, margin=dict(t=0,b=0))
st.plotly_chart(f, width='stretch')

st.dataframe(df)
