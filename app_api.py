import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ======================
# CONFIG
# ======================
st.set_page_config(layout="wide")
st.title("Calculo de Solicitaciones (Versión Beta)")

# ======================
# INPUTS
# ======================
c1, c2 = st.columns(2)

with c1:
    L_m = st.number_input("Profundidad (m)", 500, 5000, 1800)
    G = st.slider("Gravedad específica", 0.6, 1.2, 0.95)

with c2:
    D = st.selectbox("Bomba (in)", [1.5,1.75,2,2.25,2.5])
    S = st.slider("Carrera vástago (in)", 50, 200, 168)
    N = st.slider("SPM", 1, 20, 6)

# ======================
# PROPIEDADES
# ======================
areas = {"1":0.786,"7/8":0.601,"3/4":0.442}
peso  = {"1":2.90,"7/8":2.22,"3/4":1.63}

UTS = 30
b = 0.5625

def goodman(smin):
    return UTS + b * smin

L_ft = L_m * 3.28084

# ======================
# CARGA FLUIDO
# ======================
A = np.pi * D**2 / 4
Fo = 0.433 * G * L_ft * A

# ======================
# PESO
# ======================
W_total = L_ft * 2.3
Wri = W_total * (1 - 0.128 * G)

# ======================
# DINÁMICA
# ======================
ratio = Fo / (Fo + 12000)

f_speed = min(N/10,1)
f_stroke = (S/100)**0.8

Fi = Fo * (2.0 - 1.2*ratio) * f_stroke
F2 = Fo * (0.5 + 0.2*ratio) * f_speed * f_stroke

PPRL = Wri + Fi
MPRL = Wri - F2

# ======================
# MODO
# ======================
modo = st.radio("Modo diseño", ["Automático","Manual"])

# ======================
# SARTA
# ======================
if modo == "Manual":
    n1 = st.number_input('Varillas 1"',10,300,80)
    n78 = st.number_input('Varillas 7/8"',10,300,80)
    n34 = st.number_input('Varillas 3/4"',10,300,80)

    L1 = n1 * 25
    L78 = n78 * 25
    L34 = n34 * 25

    total = L1 + L78 + L34

    pct = {
        "1": L1/total,
        "7/8": L78/total,
        "3/4": L34/total
    }

else:
    pct = {"1":0.33,"7/8":0.33,"3/4":0.34}

# ======================
# EVALUACIÓN
# ======================
def evaluar(pct):

    L1 = pct["1"] * L_ft
    L78 = pct["7/8"] * L_ft

    W1 = L1 * peso["1"]
    W78 = L78 * peso["7/8"]

    W_up = {
        "1": 0,
        "7/8": W1,
        "3/4": W1 + W78
    }

    beta = {"1":1.0,"7/8":0.7,"3/4":0.4}

    res = {}

    for d in pct:
        Pmax = PPRL - W_up[d]
        Pmin = max(MPRL - beta[d]*W_up[d],0)

        Smax = Pmax / areas[d] / 1000
        Smin = Pmin / areas[d] / 1000

        Sadm = goodman(Smin)
        G = ((Smax - Smin)/(Sadm - Smin))*100

        res[d] = {
            "Pmax":Pmax,
            "Pmin":Pmin,
            "Smax":Smax,
            "Smin":Smin,
            "G":G,
            "L":pct[d]*L_ft,
            "n":int((pct[d]*L_ft)/25)
        }

    return res

# ======================
# OPTIMIZACIÓN
# ======================
if modo == "Automático":
    for _ in range(100):
        res_tmp = evaluar(pct)

        g_vals = {d:res_tmp[d]["G"] for d in res_tmp}

        d_max = max(g_vals, key=g_vals.get)
        d_min = min(g_vals, key=g_vals.get)

        step = 0.01

        if pct[d_min] > 0.25:
            pct[d_min] -= step
            pct[d_max] += step

        total = sum(pct.values())
        for d in pct:
            pct[d] /= total

res = evaluar(pct)

# ======================
# CARGAS
# ======================
st.subheader("Cargas vástago")

c1,c2,c3 = st.columns(3)
c1.metric("PPRL",f"{PPRL:,.0f} lb")
c2.metric("MPRL",f"{MPRL:,.0f} lb")
c3.metric("Fo",f"{Fo:,.0f} lb")

# ======================
# TABLA
# ======================
data = []

for d in res:
    r = res[d]
    data.append({
        "Diámetro": d,
        "Varillas": r["n"],
        "Longitud (m)": r["L"] * 0.3048,
        "Pmax (lb)": int(r["Pmax"]),
        "Pmin (lb)": int(r["Pmin"]),
        "Smax (ksi)": round(r["Smax"],1),
        "Smin (ksi)": round(r["Smin"],1),
        "Goodman (%)": f"<b>{int(r['G'])}</b>"
    })

df = pd.DataFrame(data)

# centrado
st.markdown("""
<style>
table {text-align: center;}
thead th {text-align: center !important;}
tbody td {text-align: center !important;}
</style>
""", unsafe_allow_html=True)

st.subheader("Resultados por tramo")
st.write(df.to_html(index=False), unsafe_allow_html=True)

# ======================
# BALANCE
# ======================
gvals = [res[d]["G"] for d in res]

st.subheader("Balance de Goodman")
st.write(f"Mínimo: **{int(min(gvals))}%**")
st.write(f"Máximo: **{int(max(gvals))}%**")
st.write(f"Diferencia: **{int(max(gvals)-min(gvals))}%**")

# ======================
# GOODMAN GRAPH
# ======================
st.subheader("Diagrama de Goodman")

x = np.linspace(0,150,200)
y = goodman(x)

fig, ax = plt.subplots()

ax.plot(x,y,label="Goodman")
ax.plot(x,x,'--')

for d in res:
    ax.scatter(res[d]["Smin"], res[d]["Smax"])
    ax.text(
        res[d]["Smin"],
        res[d]["Smax"],
        d,
        fontsize=8
    )

ax.set_xlabel("Smin (ksi)")
ax.set_ylabel("Smax (ksi)")

ax.grid(alpha=0.3)
ax.legend()

st.pyplot(fig)

