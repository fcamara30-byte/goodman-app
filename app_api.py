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
    L_m = st.number_input("Profundidad (m)", 500, 5000, 1800)
    H_m = st.number_input("Nivel dinámico (m)", 100, 4000, 1500)
    G = st.slider("Gravedad específica", 0.6, 1.2, 0.96)

with c2:
    D = st.selectbox("Diámetro bomba (in)", [1.5,1.75,2,2.25,2.5,2.75,3.5])
    S = st.slider("Carrera (in)", 50, 200, 100)
    N = st.slider("SPM", 1, 20, 5)

# ======================
# PROPIEDADES
# ======================
areas = {"1":0.786, "7/8":0.601, "3/4":0.442}

UTS = 30
b = 0.5625

def goodman(smin):
    return UTS + b*smin

# ======================
# CARGAS
# ======================
L_ft = L_m * 3.28084
H_ft = H_m * 3.28084

A_pump = np.pi * D**2 / 4
Fo = 0.433 * G * H_ft * A_pump

W = L_ft * 2.0
Wri = W * (1 - 0.128 * G)

Fi = Fo * (1.1 + 0.01*N)
F2 = Fo * 0.6

PPRL = Wri + Fi
MPRL = Wri - F2

# ======================
# GOODMAN %
# ======================
def calc(area):

    Smax = PPRL / area / 1000
    Smin = MPRL / area / 1000

    Sadm = goodman(Smin)

    pct = ((Smax - Smin)/(Sadm - Smin))*100

    return Smin, Smax, pct

# ======================
# DISTRIBUCION BASE
# ======================
tabla = {
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

    for _ in range(30):

        g_vals = {}

        for d in pct:
            if pct[d] <= 0:
                continue
            _,_,g = calc(areas[d])
            g_vals[d] = g

        if len(g_vals) < 2:
            return pct

        d_max = max(g_vals, key=g_vals.get)
        d_min = min(g_vals, key=g_vals.get)

        # mover material
        transf = 0.02

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

pct = tabla[D].copy()

if usar_auto:
    pct = balancear(pct)

# ======================
# RESULTADOS
# ======================
st.subheader("Distribución y solicitaciones")

g_lista = []
puntos = []

for d in ["1","7/8","3/4"]:

    if pct[d] <= 0.01:
        continue

    Smin, Smax, g = calc(areas[d])

    g_lista.append(g)
    puntos.append((Smin,Smax,d))

    st.markdown(f"### {d}\" → {pct[d]*100:.0f}%")

    c1,c2,c3 = st.columns(3)
    c1.metric("Smin", f"{Smin:.1f} ksi")
    c2.metric("Smax", f"{Smax:.1f} ksi")
    c3.metric("Goodman", f"{g:.1f} %")

    if g < 80:
        st.info("Holgado")
    elif g <= 100:
        st.success("OK")
    else:
        st.error("SOBRECARGA")

# ======================
# BALANCE GENERAL
# ======================
if len(g_lista) > 1:

    delta = max(g_lista) - min(g_lista)

    st.subheader("Balance")

    if delta < 10:
        st.success(f"Excelente Δ={delta:.1f}%")
    elif delta < 20:
        st.warning(f"Aceptable Δ={delta:.1f}%")
    else:
        st.error(f"Desbalanceado Δ={delta:.1f}%")

# ======================
# GRAFICO
# ======================
if len(puntos) > 0:

    st.subheader("Diagrama Goodman")

    x = np.linspace(0,150,200)
    y = goodman(x)

    fig, ax = plt.subplots()

    ax.plot(x,y,label="DA78")
    ax.plot(x,x,'k--')

    for p in puntos:
        ax.scatter(p[0],p[1])
        ax.text(p[0],p[1],p[2])

    ax.set_xlabel("Smin (ksi)")
    ax.set_ylabel("Smax (ksi)")
    ax.grid()
    ax.legend()

    st.pyplot(fig)

# ======================
# CARGAS
# ======================
st.subheader("Cargas")

c1,c2 = st.columns(2)



