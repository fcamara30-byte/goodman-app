import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("Diseño SRP + Goodman (correcto)")

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
# CONVERSION
# ======================
L_ft = L_m * 3.28084
H_ft = H_m * 3.28084

# ======================
# CARGAS EN VASTAGO
# ======================
A_pump = np.pi * D**2 / 4
Fo = 0.433 * G * H_ft * A_pump

W_total = L_ft * 2.3
Wri = W_total * (1 - 0.128 * G)

ratio = Fo/(Fo+12000)

Fi = Fo*(2.0 - 1.2*ratio)
F2 = Fo*(0.5 + 0.2*ratio)

PPRL = Wri + Fi
MPRL = Wri - F2

# ======================
# DISTRIBUCION
# ======================
pct = {"1":0.35,"7/8":0.40,"3/4":0.25}

# ======================
# CALCULO REAL
# ======================
def evaluar(pct):

    L1 = pct["1"] * L_ft
    L78 = pct["7/8"] * L_ft
    L34 = pct["3/4"] * L_ft

    W1 = L1 * peso["1"]
    W78 = L78 * peso["7/8"]
    W34 = L34 * peso["3/4"]

    W_up = {
        "1": 0,
        "7/8": W1,
        "3/4": W1 + W78
    }

    res = {}

    for d in ["1","7/8","3/4"]:

        Pmax = PPRL - W_up[d]
        Pmin = MPRL - W_up[d]

        A = areas[d]

        Smax = Pmax/A/1000
        Smin = Pmin/A/1000

        # Goodman solo si hay tracción
        if Pmin > 0:
            Sadm = goodman(Smin)
            g = ((Smax - Smin)/(Sadm - Smin))*100
        else:
            g = None

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

res = evaluar(pct)

# ======================
# OUTPUT
# ======================
st.subheader("Cargas")

c1,c2,c3 = st.columns(3)
c1.metric("PPRL",f"{PPRL:,.0f} lb")
c2.metric("MPRL",f"{MPRL:,.0f} lb")
c3.metric("Fo",f"{Fo:,.0f} lb")

# ======================
# RESULTADOS
# ======================
st.subheader("Resultados por tramo")

for d in res:

    r = res[d]

    st.write(f'### {d}" → {r["n"]} varillas')

    c1,c2,c3,c4 = st.columns(4)
    c1.write(f"Pmax: {r['Pmax']:.0f} lb")
    c2.write(f"Pmin: {r['Pmin']:.0f} lb")
    c3.write(f"Smax: {r['Smax']:.1f} ksi")
    c4.write(f"Smin: {r['Smin']:.1f} ksi")

    if r["g"] is None:
        st.error("Compresión → tramo inválido")
    else:
        st.write(f"Goodman: {r['g']:.1f}%")

# ======================
# GRAFICO GOODMAN
# ======================
st.subheader("Diagrama de Goodman")

x = np.linspace(0,150,200)
y = goodman(x)

fig, ax = plt.subplots()

# curvas
ax.plot(x,y,label="Límite Goodman")
ax.plot(x,x,'--',label="Línea 45°")

# puntos
for d in res:

    Smin = res[d]["Smin"]
    Smax = res[d]["Smax"]

    if res[d]["g"] is None:
        ax.scatter(Smin, Smax, color='red', s=40)
        ax.text(Smin, Smax, d+" (comp)", fontsize=8)
    else:
        ax.scatter(Smin, Smax, s=40)
        ax.text(Smin, Smax, d, fontsize=8)

ax.set_xlabel("Smin (ksi)")
ax.set_ylabel("Smax (ksi)")
ax.grid()
ax.legend()

st.pyplot(fig)
