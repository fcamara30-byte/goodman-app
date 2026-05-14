import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("SRP Diseño + Goodman (calibrado tipo QRod)")

# ======================
# INPUTS
# ======================
c1, c2 = st.columns(2)

with c1:
    L_m = st.number_input("Profundidad (m)", 500, 5000, 1800)
    H_m = st.number_input("Nivel dinámico (m)", 100, 4000, 1500)
    G = st.slider("Gravedad específica", 0.6, 1.2, 0.95)

with c2:
    D = st.selectbox("Bomba (in)", [1.5,1.75,2,2.25,2.5])
    N = st.slider("SPM", 1, 20, 8)

# ======================
# PROPIEDADES
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
# CARGA FLUIDO
# ======================
A_pump = np.pi * D**2 / 4
Fo = 0.433 * G * H_ft * A_pump

# ======================
# PESO TOTAL VARILLAS
# ======================
W_total = L_ft * 2.3
Wri = W_total * (1 - 0.128 * G)

# ======================
# DINAMICA DEPENDIENTE DE SPM
# ======================
ratio = Fo / (Fo + 12000)

Fi = Fo * (2.0 - 1.2 * ratio)

# 🔥 FACTOR DE VELOCIDAD (CLAVE)
f_speed = min(N/10, 1)

F2 = Fo * (0.5 + 0.2 * ratio) * f_speed

PPRL = Wri + Fi
MPRL = Wri - F2

# ======================
# DISTRIBUCION DE SARTA
# ======================
pct = {"1":0.35,"7/8":0.40,"3/4":0.25}

# ======================
# EVALUACION REAL
# ======================
def evaluar():

    L1 = pct["1"] * L_ft
    L78 = pct["7/8"] * L_ft
    L34 = pct["3/4"] * L_ft

    W1 = L1 * peso["1"]
    W78 = L78 * peso["7/8"]

    W_up = {
        "1": 0,
        "7/8": W1,
        "3/4": W1 + W78
    }

    # 🔥 ATENUACION DINAMICA
    beta = {
        "1": 1.0,
        "7/8": 0.7,
        "3/4": 0.4
    }

    res = {}

    for d in ["1","7/8","3/4"]:

        Pmax = PPRL - W_up[d]

        Pmin = MPRL - beta[d] * W_up[d]

        # evitar compresión ficticia
        Pmin = max(Pmin, 0)

        A = areas[d]

        Smax = Pmax / A / 1000
        Smin = Pmin / A / 1000

        Sadm = goodman(Smin)

        g = ((Smax - Smin)/(Sadm - Smin))*100

        res[d] = {
            "Pmax":Pmax,
            "Pmin":Pmin,
            "Smax":Smax,
            "Smin":Smin,
            "g":g,
            "L":pct[d]*L_ft,
            "n":int((pct[d]*L_ft)/25)
        }

    return res

res = evaluar()

# ======================
# OUTPUT CARGAS
# ======================
st.subheader("Cargas vástago")

c1,c2,c3 = st.columns(3)
c1.metric("PPRL",f"{PPRL:,.0f} lb")
c2.metric("MPRL",f"{MPRL:,.0f} lb")
c3.metric("Fo",f"{Fo:,.0f} lb")

# ======================
# RESULTADOS POR TRAMO
# ======================
st.subheader("Resultados por tramo")

for d in res:

    r = res[d]

    st.write(f'### {d}" → {r["n"]} varillas')

    c1,c2,c3,c4,c5 = st.columns(5)

    c1.write(f"Pmax: {r['Pmax']:.0f}")
    c2.write(f"Pmin: {r['Pmin']:.0f}")
    c3.write(f"Smax: {r['Smax']:.1f}")
    c4.write(f"Smin: {r['Smin']:.1f}")
    c5.write(f"Goodman: {r['g']:.1f}%")

# ======================
# GRAFICO GOODMAN
# ======================
st.subheader("Diagrama Goodman")

x = np.linspace(0,150,200)
y = goodman(x)

fig, ax = plt.subplots()

ax.plot(x, y, label="Límite Goodman")
ax.plot(x, x, '--', label="45°")

for d in res:
    ax.scatter(res[d]["Smin"], res[d]["Smax"], s=50)
    ax.text(res[d]["Smin"], res[d]["Smax"], d)

ax.set_xlabel("Smin (ksi)")
ax.set_ylabel("Smax (ksi)")
ax.grid()
ax.legend()

st.pyplot(fig)

