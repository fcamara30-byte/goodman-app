import streamlit as st
import numpy as np

st.set_page_config(layout="wide")

st.title("Diseño de sarta SRP (Goodman balanceado real)")

# ======================
# INPUTS
# ======================
c1, c2 = st.columns(2)

with c1:
    L_m = st.number_input("Profundidad (m)", 500, 5000, 1800)
    H_m = st.number_input("Nivel dinámico (m)", 100, 4000, 1500)
    G = st.slider("Gravedad específica", 0.6, 1.2, 0.95)

with c2:
    D = st.selectbox("Bomba (in)", [1.5, 1.75, 2, 2.25, 2.5])
    N = st.slider("SPM", 1, 20, 8)

# ======================
# PROPIEDADES
# ======================
areas = {"1": 0.786, "7/8": 0.601, "3/4": 0.442}
peso  = {"1": 2.90, "7/8": 2.22, "3/4": 1.63}

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
# CARGAS
# ======================
A_pump = np.pi * D**2 / 4
Fo = 0.433 * G * H_ft * A_pump

# peso varillas (promedio)
W = L_ft * 2.3
Wri = W * (1 - 0.128 * G)

# dinámica (estable y coherente)
ratio = Fo / (Fo + 12000)

Fi = Fo * (2.0 - 1.2 * ratio)
F2 = Fo * (0.5 + 0.2 * ratio)

PPRL = Wri + Fi
MPRL = Wri - F2

# ======================
# DISTRIBUCION INICIAL
# ======================
pct = {"1": 0.35, "7/8": 0.40, "3/4": 0.25}

# ======================
# FUNCION DE EVALUACION REAL
# ======================
def evaluar(pct):

    L1 = pct["1"] * L_ft
    L78 = pct["7/8"] * L_ft
    L34 = pct["3/4"] * L_ft

    # pesos acumulados
    W1 = L1 * peso["1"]
    W78 = L78 * peso["7/8"]

    # cargas reales por tramo
    P = {
        "1": PPRL,
        "7/8": PPRL - W1,
        "3/4": PPRL - (W1 + W78)
    }

    resultados = {}

    for d in P:

        A = areas[d]

        Smax = P[d] / A / 1000
        Smin = MPRL / A / 1000

        Sadm = goodman(Smin)

        g = ((Smax - Smin) / (Sadm - Smin)) * 100

        resultados[d] = g

    return resultados

# ======================
# BALANCE REAL DE GOODMAN
# ======================
for _ in range(80):

    g_vals = evaluar(pct)

    d_max = max(g_vals, key=g_vals.get)
    d_min = min(g_vals, key=g_vals.get)

    step = 0.01

    if pct[d_min] > 0.10:   # evita desaparecer tramos
        pct[d_min] -= step
        pct[d_max] += step

    # normalizar
    total = sum(pct.values())
    for d in pct:
        pct[d] /= total

# ======================
# RESULTADOS FINALES
# ======================
res = evaluar(pct)

# ======================
# OUTPUT
# ======================
st.subheader("Cargas")

c1, c2, c3 = st.columns(3)
c1.metric("PPRL", f"{PPRL:,.0f} lb")
c2.metric("MPRL", f"{MPRL:,.0f} lb")
c3.metric("Fo", f"{Fo:,.0f} lb")

# ======================
# DISEÑO DE SARTA
# ======================
st.subheader("Diseño de sarta (balanceado)")

for d in pct:

    L_tramo = pct[d] * L_ft
    n = int(L_tramo / 25)

    st.write(f'{d}" → {pct[d]*100:.1f}% | {n} varillas | Goodman: {res[d]:.1f}%')

# ======================
# CONTROL DE CALIDAD
# ======================
st.subheader("Chequeo de equilibrio")

gvals = list(res.values())

st.write(f"mín Goodman: {min(gvals):.1f}%")
st.write(f"máx Goodman: {max(gvals):.1f}%")
st.write(f"diferencia: {(max(gvals)-min(gvals)):.1f}%")

