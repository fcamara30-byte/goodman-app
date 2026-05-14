import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

st.title("Diseño de varillas + Goodman (DA78)")

# ======================
# INPUTS
# ======================
c1, c2 = st.columns(2)

with c1:
    L_m = st.number_input("Profundidad (m)", 500, 5000, 1800)
    H_m = st.number_input("Nivel dinámico (m)", 100, 4000, 1500)
    G = st.slider("Gravedad específica", 0.6, 1.2, 0.96)

with c2:
    D = st.selectbox("Diámetro bomba (in)", [1.5,1.75,2,2.25,2.5,2.75,3.5])
    N = st.slider("SPM", 1, 20, 8)

# ======================
# PROPIEDADES
# ======================
areas = {"1":0.786, "7/8":0.601, "3/4":0.442}
peso  = {"1":2.90, "7/8":2.22, "3/4":1.63}

UTS = 30
b = 0.5625

def goodman(smin):
    return UTS + b * smin

# ======================
# CONVERSIONES
# ======================
L_ft = L_m * 3.28084
H_ft = H_m * 3.28084

# ======================
# CARGAS REALES
# ======================
A_pump = np.pi * D**2 / 4
Fo = 0.433 * G * H_ft * A_pump

W = L_ft * 2.2
Wri = W * (1 - 0.128 * G)

Fi = Fo * (1.15 + 0.01*N)
F2 = Fo * 0.6

PPRL = Wri + Fi
MPRL = Wri - F2

# ======================
# MOSTRAR CARGAS
# ======================
st.subheader("Cargas de diseño")

cc1, cc2, cc3 = st.columns(3)
cc1.metric("PPRL", f"{PPRL:,.0f} lb")
cc2.metric("MPRL", f"{MPRL:,.0f} lb")
cc3.metric("Fo", f"{Fo:,.0f} lb")

# ======================
# DISTRIBUCION INICIAL
# ======================
pct = {"1":0.35, "7/8":0.40, "3/4":0.25}

# ======================
# EVALUACION CORRECTA
# ======================
def evaluar(pct):

    L1 = pct["1"] * L_ft
    L78 = pct["7/8"] * L_ft
    L34 = pct["3/4"] * L_ft

    W1 = L1 * peso["1"]
    W78 = L78 * peso["7/8"]

    # cargas máximas
    Pmax = {
        "1": PPRL,
        "7/8": PPRL - W1,
        "3/4": PPRL - (W1 + W78)
    }

    # cargas mínimas
    Pmin = {
        "1": MPRL,
        "7/8": MPRL - W1,
        "3/4": MPRL - (W1 + W78)
    }

    resultados = {}

    for d in ["1","7/8","3/4"]:

        if pct[d] <= 0:
            continue

        A = areas[d]

        Smax = Pmax[d] / A / 1000
        Smin = Pmin[d] / A / 1000

        Sadm = goodman(Smin)
        g = ((Smax - Smin)/(Sadm - Smin))*100

        resultados[d] = {
            "Smin":Smin,
            "Smax":Smax,
            "g":g,
            "L":pct[d]*L_ft
        }

    return resultados

# ======================
# BALANCE
# ======================
def balancear(pct):

    for _ in range(40):

        res = evaluar(pct)
        g_vals = {d:res[d]["g"] for d in res}

        d_max = max(g_vals, key=g_vals.get)
        d_min = min(g_vals, key=g_vals.get)

        if g_vals[d_max] > 100:
            t = 0.03
        else:
            t = 0.01

        if pct[d_min] > t:
            pct[d_min] -= t
            pct[d_max] += t

        total = sum(pct.values())
        for d in pct:
            pct[d] /= total

    return pct

# ======================
# BOTON BALANCE
# ======================
if st.checkbox("Balance automático"):
    pct = balancear(pct)

# ======================
# RESULTADOS
# ======================
st.subheader("Resultados por tramo")

res = evaluar(pct)

for d in res:

    L_tramo = res[d]["L"]
    n = int(L_tramo / 25)

    st.markdown(f"<span style='font-size:14px'>{d}\" → {pct[d]*100:.1f}% | {n} varillas</span>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    col1.markdown(f"<b style='font-size:18px'>Smin: {res[d]['Smin']:.1f} ksi</b>", unsafe_allow_html=True)
    col2.markdown(f"<b style='font-size:20px'>Smax: {res[d]['Smax']:.1f} ksi</b>", unsafe_allow_html=True)
    col3.markdown(f"<span style='font-size:14px'>Goodman: {res[d]['g']:.1f}%</span>", unsafe_allow_html=True)

# ======================
# GRAFICO GOODMAN
# ======================
st.subheader("Diagrama de Goodman")

x = np.linspace(0,150,200)
y = goodman(x)

fig, ax = plt.subplots()

ax.plot(x, y, linewidth=2)
ax.plot(x, x, '--', linewidth=1)

for d in res:




