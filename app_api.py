import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

st.title("Diseño automático de varillas + Goodman (DA78)")

# ======================
# INPUTS
# ======================
c1, c2 = st.columns(2)

with c1:
    L_m = st.number_input("Profundidad (m)", 500, 5000, 2000)
    H_m = st.number_input("Nivel dinámico (m)", 100, 4000, 1500)
    G = st.slider("Gravedad específica", 0.6, 1.2, 1.0)

with c2:
    D = st.selectbox("Diámetro bomba (in)", [1.5,1.75,2,2.25,2.5,2.75,3.5])
    S = st.slider("Carrera (in)", 50, 200, 100)
    N = st.slider("SPM", 1, 20, 10)

# ======================
# PROPIEDADES VARILLAS
# ======================
areas = {"3/4":0.442, "7/8":0.601, "1":0.786}
peso = {"3/4":1.63, "7/8":2.22, "1":2.90}

# ======================
# GOODMAN
# ======================
UTS = 30
b = 0.5625
FS = 1

def goodman(smin):
    return (UTS + b * smin) * FS

# ======================
# CARGAS
# ======================
L_ft = L_m * 3.28084
H_ft = H_m * 3.28084

A_pump = np.pi * D**2 / 4
Fo = 0.433 * G * H_ft * A_pump

# peso promedio
W = L_ft * 2.0
Wri = W * (1 - 0.128 * G)

Fi = Fo * (1.1 + 0.01 * N)
F2 = Fo * 0.6

PPRL = Wri + Fi
MPRL = Wri - F2

# ======================
# CALCULO GOODMAN %
# ======================
def calc(g_area):

    Smax = PPRL / g_area / 1000
    Smin = MPRL / g_area / 1000

    Sadm = goodman(Smin)

    if Sadm != Smin:
        pct = ((Smax - Smin)/(Sadm - Smin))*100
    else:
        pct = 0

    return Smin, Smax, pct

# ======================
# DISTRIBUCION BASE
# ======================
tabla_base = {
    1.5: {"1":0.0,"7/8":0.4,"3/4":0.6},
    1.75:{"1":0.2,"7/8":0.35,"3/4":0.45},
    2.0: {"1":0.25,"7/8":0.40,"3/4":0.35},
    2.25:{"1":0.30,"7/8":0.40,"3/4":0.30},
    2.5: {"1":0.35,"7/8":0.40,"3/4":0.25},
    2.75:{"1":0.40,"7/8":0.35,"3/4":0.25},
    3.5: {"1":0.6,"7/8":0.4,"3/4":0.0}
}

# ======================
# BALANCE INTELIGENTE
# ======================
def balancear(pct):

    diam = ["1","7/8","3/4"]

    for _ in range(40):

        valores = []

        for d in diam:
            if pct[d] <= 0:
                valores.append(0)
                continue

            _,_,g = calc(areas[d])
            valores.append(g)

        max_i = valores.index(max(valores))
        min_i = valores.index(min(valores))

        d_max = diam[max_i]
        d_min = diam[min_i]

        # si el máximo está en falla, forzar corrección
        if valores[max_i] > 100:

            transf = 0.03

            if pct[d_min] > transf:
                pct[d_min] -= transf
                pct[d_max] += transf

        else:
            transf = 0.015

            if pct[d_min] > transf:
                pct[d_min] -= transf
                pct[d_max] += transf

        # normalizar
        total = sum(pct.values())
        for d in pct:
            pct[d] /= total

    return pct

# ======================
# CONTROL
# ======================
usar_auto = st.checkbox("Balance automático")

base = tabla_base[D]

if usar_auto:
    pct = balancear(base.copy())
else:
    pct = base

# ======================
# RESULTADOS
# ======================
st.subheader("Distribución y solicitaciones")

g_vals = []
resultados = []

for d in ["1","7/8","3/4"]:

    if pct[d] <= 0:
        continue

    A = areas[d]

    Smin, Smax, g = calc(A)

    g_vals.append(g)
    resultados.append((d,Smin,Smax))


