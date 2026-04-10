import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide")

# --- 1. SETTINGS ---
sb = st.sidebar
sb.header("Milestones")
ca = sb.slider("Current Age", 30, 65, 42)
yr = sb.slider("Your Retire", 45, 75, 55)
hr = sb.slider("Husband Retire", 45, 75, 58)
sa = sb.slider("SS Age", 62, 72, 67)
da = sb.slider("End Age", 80, 110, 95)
rt = sb.slider("Return %", 1, 10, 6) / 100

sb.header("Finance")
hn = sb.number_input("Husband Net", 145000)
yn = sb.number_input("Your Net", 110000)
ew = sb.number_input("Work Exp", 210000)
er = sb.number_input("Retire Exp", 150000)

sb.header("Education")
nk = sb.number_input("Kids", 0, 5, 2)
tui = sb.number_input("Annual Tuition ($)", 50000)
ks = []
for i in range(nk):
    ks.append(sb.number_input(f"K{i+1} Start", 40, 75, 52+(i*6)))

st.title("🌏 Legacy Master v6.1")

# --- 2. REAL ESTATE ---
re = []
cl = st.columns(3)
for i in range(6):
    with cl[i % 3]:
        with st.expander(f"Property {i+1}", i < 4):
            ip = st.checkbox("Primary?", i == 0, key=f"p{i}")
            cf = 0 if ip else st.number_input(
                "Rent", 7800 if i < 4 else 0, key=f"c{i}"
            )
            ms = st.number_input("Mtg Start", 35, key=f"s{i}")
            mt = st.number_input("Term", 30, key=f"t{i}")
            mp = st.number_input(
                "Pay", 15000 if i < 4 else 0, key=f"m{i}"
            )
            re.append({"f":cf, "s":ms, "e":ms+mt, "p":mp})

# --- 3. MATH ---
p = 1700000 
res = []
for a in range(ca, da + 1):
    g = p * rt
    hi = hn if a < hr else 0
    yi = yn if a < yr else 0
    ss = 85000 if a >= sa else 0
    
    rf = sum(x["f"] for x in re)
    py = sum(x["p"] for x in re if x["s"] <= a < x["e"])
    ed = sum(tui for s in ks if s <= a < s + 4)
    
    lv = er if (a >= yr and a >= hr) else ew
    net = (hi + yi + ss + rf + g) - (lv + py + ed)
    p += net
    
    res.append({
        "Age": a, 
        "Growth": g, 
        "Inc": hi + yi + ss + rf, 
        "Exp": -(lv + py + ed), 
        "Port": p
    })

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
f.add_trace(go.Bar(
    x=df["Age"], y=df["Inc"], name="Income", marker_color="green"
))
f.add_trace(go.Bar(
    x=df["Age"], y=df["Growth"], name="Growth", marker_color="blue"
))
f.add_trace(go.Bar(
    x=df["Age"], y=df["Exp"], name="Outflow", marker_color="red"
))
f.add_trace(go.Scatter(
    x=df["Age"], y=df["Port"], name="Wealth", yaxis="y2", 
    line=dict(color="black")
))

f.update_layout(
    barmode="relative", 
    yaxis2=dict(overlaying="y", side="right"), 
    height=450, 
    margin=dict(t=0, b=0)
)
st.plotly_chart(f, use_container_width=True)
st.dataframe(df)
