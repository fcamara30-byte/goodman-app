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
# PROPIEDADES VARILLAS
# ======================
areas = {"1":0.786, "7/8":0.601, "3/4":0.442}
peso = {"1":2.90, "7/8":2.22, "3/4":1.63}

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
# CARGAS (REALISTAS)
# ======================
A_pump = np.pi * D**2 / 4

# carga de fluido
Fo = 0.433 * G * H_ft * A_pump

# peso varillas promedio
W = L_ft * 2.2
Wri = W * (1 - 0.128 * G)

# dinámica simplificada (coherente)
Fi = Fo * (1.15 + 0.01*N)
F2 = Fo * 0.6

# ✅ CARGAS PRINCIPALES
PPRL = Wri + Fi
MPRL = Wri - F2

# ======================
# MOSTRAR CARGAS
# ======================
st.subheader("Cargas de diseño")

c1, c2, c3 = st.columns(3)

c1.metric("PPRL", f"{PPRL:,.0f} lb")
c2.metric("MPRL", f"{MPRL:,.0f} lb")
c3.metric("Fo", f"{Fo:,.0f} lb")

# ======================
# DISTRIBUCION INICIAL
# ======================
pct = {"1":0.35, "7/8":0.40, "3/4":0.25}

# ======================
# EVALUACION REAL
# ======================
def evaluar(pct):

    L1 = pct["1"] * L_ft
    L78 = pct["7/8"] * L_ft
    L34 = pct["3/4"] * L_ft

    # pesos por tramo
    W1 = L1 * peso["1"]
    W78 = L78 * peso["7/8"]
    W34 = L34 * peso["3/4"]

    # ✅ cargas reales por tramo (clave)
    P_1 = PPRL
    P_7_8 = PPRL - W1
    P_3_4 = PPRL - (W1 + W78)

    cargas = {"1":P_1, "7/8":P_7_8, "3/4":P_3_4}

    resultados = {}

    for d in ["1","7/8","3/4"]:

        if pct[d] <= 0:
            continue

        A = areas[d]

        Smax = cargas[d] / A / 1000
        Smin = MPRL / A / 1000

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
# BALANCE REAL
# ======================
def balancear(pct):

    for _ in range(50):

        res = evaluar(pct)
        g_vals = {d:res[d]["g"] for d in res}

        d_max = max(g_vals, key=g_vals.get)
        d_min = min(g_vals, key=g_vals.get)

        # ajuste más fuerte si hay fallo
        if g_vals[d_max] > 100:
            t = 0.03
        else:
            t = 0.01

        if pct[d_min] > t:
            pct[d_min] -= t
            pct[d_max] += t

        # normalizar
        total = sum(pct.values())
        for d in pct:
            pct[d] /= total

    return pct

# ======================
# BALANCE AUTOMATICO
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

    st.write(f'{d}" → {pct[d]*100:.1f}% | {n} varillas')

    c1,c2,c3 = st.columns(3)

    c1.write(f"Smin: {res[d]['Smin']:.1f} ksi")
    c2.write(f"Smax: {res[d]['Smax']:.1f} ksi")
    c3.write(f"Goodman: {res[d]['g']:.1f}%")

# ======================
# GRAFICO
# ======================
st.subheader("Diagrama de Goodman")

x = np.linspace(0,150,200)
y = goodman(x)

fig, ax = plt.subplots()

ax.plot(x,y,label="DA78")
ax.plot(x,x,'--')

for d in res:
    ax.scatter(res[d]["Smin"],res[d]["Smax"])
    ax.text(res[d]["Smin"],res[d]["Smax"],d)

ax.set_xlabel("Smin (ksi)")
ax.set_ylabel("Smax (ksi)")
ax.grid()
ax.legend()

st.pyplot(fig)




