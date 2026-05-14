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
    L_m = st.number_input("Profundidad (m)", 500, 5000, 1827)
    H_m = st.number_input("Nivel dinámico (m)", 100, 4000, 1701)
    G = st.slider("Gravedad específica", 0.6, 1.2, 0.94)

with c2:
    D = st.selectbox("Diámetro bomba (in)", [1.5,1.75,2,2.25,2.5,2.75,3.5])
    N = st.slider("SPM", 1, 20, 2)

# ======================
# DATOS
# ======================
areas = {"1":0.786, "7/8":0.601, "3/4":0.442}
peso  = {"1":2.90, "7/8":2.22, "3/4":1.63}

UTS = 30
b = 0.5625

def goodman(smin):
    return UTS + b*smin

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

W = L_ft * 2.2
Wri = W * (1 - 0.128 * G)

Fi = Fo * (1.2 + 0.02*N)
F2 = Fo * 0.6

PPRL = Wri + Fi
MPRL = max(Wri - F2, 0)

# ======================
# MOSTRAR CARGAS
# ======================
st.subheader("Cargas")

cA, cB, cC = st.columns(3)
cA.metric("PPRL", f"{PPRL:,.0f} lb")
cB.metric("MPRL", f"{MPRL:,.0f} lb")
cC.metric("Fo", f"{Fo:,.0f} lb")

# ======================
# DISTRIBUCION BASE
# ======================
pct = {"1":0.35, "7/8":0.40, "3/4":0.25}

MIN_PCT = 0.05

# ======================
# EVALUACION
# ======================
def evaluar(pct):

    L1 = pct["1"] * L_ft
    L78 = pct["7/8"] * L_ft
    L34 = pct["3/4"] * L_ft

    W1 = L1 * peso["1"]
    W78 = L78 * peso["7/8"]
    W34 = L34 * peso["3/4"]

    # cargas máximas
    Pmax = {
        "1": PPRL,
        "7/8": PPRL - W1,
        "3/4": PPRL - (W1 + W78)
    }

    # cargas mínimas físicas
    W_below = {
        "1": W78 + W34,
        "7/8": W34,
        "3/4": 0
    }

    Pmin = {}
    for d in pct:
        Pmin[d] = W_below[d] + 0.3 * Fo

    resultados = {}

    for d in pct:

        if pct[d] <= 0:
            continue

        A = areas[d]

        Smax = Pmax[d] / A / 1000
        Smin = Pmin[d] / A / 1000

        Sadm = goodman(Smin)
        g = ((Smax - Smin)/(Sadm - Smin))*100

        resultados[d] = {
            "Smin": Smin,
            "Smax": Smax,
            "g": g,
            "L": pct[d] * L_ft
        }

    return resultados

# ======================
# BALANCE SEGURO
# ======================
def balancear(pct):

    for _ in range(40):

        res = evaluar(pct)

        if len(res) < 2:
            return pct

        g_vals = {d:res[d]["g"] for d in res}

        d_max = max(g_vals, key=g_vals.get)
        d_min = min(g_vals, key=g_vals.get)

        t = 0.02

        # proteger mínimos
        if pct[d_min] > MIN_PCT:
            pct[d_min] -= t
            pct[d_max] += t

        # normalizar
        total = sum(pct.values())
        for d in pct:
            pct[d] = max(pct[d]/total, MIN_PCT)

        # renormalizar otra vez
        total = sum(pct.values())
        for d in pct:
            pct[d] /= total

    return pct

# ======================
# CHECKBOX
# ======================
if st.checkbox("Balance automático"):
    pct = balancear(pct)

# ======================
# RESULTADOS
# ======================
st.subheader("Resultados por tramo")

res = evaluar(pct)

if len(res) == 0:
    st.error("No se pudieron calcular los resultados (revisar distribución)")
else:

    for d in res:

        n = int(res[d]["L"] / 25)

        st.write(f'{d}" → {pct[d]*100:.1f}% | {n} varillas')

        c1,c2,c3 = st.columns(3)
        c1.write(f"Smin: {res[d]['Smin']:.1f} ksi")
        c2.write(f"Smax: {res[d]['Smax']:.1f} ksi")
        c3.write(f"Goodman: {res[d]['g']:.1f}%")

# ======================
# GRAFICO
# ======================
if len(res) > 0:

    st.subheader("Diagrama Goodman")

    x = np.linspace(0,150,200)
    y = goodman(x)

    fig, ax = plt.subplots()
    ax.plot(x,y)
    ax.plot(x,x,'--')

    for d in res:
        ax.scatter(res[d]["Smin"], res[d]["Smax"], s=20)

    st.pyplot(fig)





