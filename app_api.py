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
# DATOS VARILLAS
# ======================
areas = {"1":0.786, "7/8":0.601, "3/4":0.442}
peso  = {"1":2.90, "7/8":2.22, "3/4":1.63}

# ======================
# GOODMAN
# ======================
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
# CARGAS PRINCIPALES
# ======================
A_pump = np.pi * D**2 / 4

# carga fluido
Fo = 0.433 * G * H_ft * A_pump

# peso varillas
W = L_ft * 2.2
Wri = W * (1 - 0.128 * G)

# dinámica razonable
Fi = Fo * (1.2 + 0.02 * N)
F2 = Fo * 0.6

PPRL = Wri + Fi
MPRL = max(Wri - F2, 0)

# ======================
# MOSTRAR CARGAS
# ======================
st.subheader("Cargas de diseño")

cA, cB, cC = st.columns(3)
cA.metric("PPRL", f"{PPRL:,.0f} lb")
cB.metric("MPRL", f"{MPRL:,.0f} lb")
cC.metric("Fo", f"{Fo:,.0f} lb")

# ======================
# DISTRIBUCION INICIAL
# ======================
pct = {"1":0.35, "7/8":0.40, "3/4":0.25}

# ======================
# EVALUACIÓN REAL
# ======================
def evaluar(pct):

    # longitudes
    L1 = pct["1"] * L_ft
    L78 = pct["7/8"] * L_ft
    L34 = pct["3/4"] * L_ft

    # pesos por tramo
    W1 = L1 * peso["1"]
    W78 = L78 * peso["7/8"]
    W34 = L34 * peso["3/4"]

    # ----------------------
    # CARGA MAXIMA (CORRECTA)
    # ----------------------
    Pmax = {
        "1": PPRL,
        "7/8": PPRL - W1,
        "3/4": PPRL - (W1 + W78)
    }

    # ----------------------
    # CARGA MINIMA REAL (CLAVE)
    # nunca cero, nunca negativa
    # ----------------------
    W_below = {
        "1": W78 + W34,
        "7/8": W34,
        "3/4": 0
    }

    Pmin = {}

    for d in ["1","7/8","3/4"]:
        Pmin[d] = W_below[d] + 0.3 * Fo   # ← CORRECCION REAL

    resultados = {}

    for d in ["1","7/8","3/4"]:

        if pct[d] <= 0:
            continue

        A = areas[d]

        Smax = Pmax[d] / A / 1000
        Smin = Pmin[d] / A / 1000

        Sadm = goodman(Smin)

        g = ((Smax - Smin) / (Sadm - Smin)) * 100

        resultados[d] = {
            "Smin": Smin,
            "Smax": Smax,
            "g": g,
            "L": pct[d] * L_ft
        }

    return resultados

# ======================
# BALANCE AUTOMATICO
# ======================
def balancear(pct):

    for _ in range(40):

        res = evaluar(pct)
        g_vals = {d: res[d]["g"] for d in res}

        d_max = max(g_vals, key=g_vals.get)
        d_min = min(g_vals, key=g_vals.get)

        t = 0.02

        if pct[d_min] > t:
            pct[d_min] -= t
            pct[d_max] += t

        # normalizar
        total = sum(pct.values())
        for d in pct:
            pct[d] /= total

    return pct

if st.checkbox("Balance automático"):
    pct = balancear(pct)

# ======================
# RESULTADOS
# ======================
st.subheader("Resultados por tramo")

res = evaluar(pct)

for d in res:

    n = int(res[d]["L"] / 25)





