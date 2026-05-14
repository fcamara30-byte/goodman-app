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
    N = st.slider("SPM", 1, 20, 5)

# ======================
# DATOS
# ======================
areas = {"1":0.786, "7/8":0.601, "3/4":0.442}
UTS = 30
b = 0.5625

def goodman(smin):
    return UTS + b*smin

# ======================
# CARGAS BASE
# ======================
L_ft = L_m * 3.28084
H_ft = H_m * 3.28084

A_pump = np.pi * D**2 / 4
Fo = 0.433 * G * H_ft * A_pump

W_total = L_ft * 2.0
Wri = W_total * (1 - 0.128 * G)

Fi = Fo * (1.1 + 0.01*N)
F2 = Fo * 0.6

PPRL = Wri + Fi
MPRL = Wri - F2

# ======================
# DISTRIBUCION BASE
# ======================
tabla = {
    2.0: {"1":0.25,"7/8":0.40,"3/4":0.35},
    2.5: {"1":0.35,"7/8":0.40,"3/4":0.25},
}

pct = tabla.get(D, {"1":0.3,"7/8":0.4,"3/4":0.3}).copy()

# ======================
# CALCULO REAL POR TRAMO
# ======================
def evaluar(pct):

    niveles = ["1","7/8","3/4"]

    resultados = {}
    carga_acum = 0

    for d in reversed(niveles):

        frac = pct[d]
        L_tramo = frac * L_ft

        peso_tramo = L_tramo * 2.0
        carga = carga_acum + (peso_tramo)

        carga_acum += peso_tramo

        # aproximación carga
        Pmax = carga
        Pmin = carga * 0.6

        A = areas[d]

        Smax = Pmax / A / 1000
        Smin = Pmin / A / 1000

        Sadm = goodman(Smin)

        g = ((Smax - Smin)/(Sadm - Smin))*100

        resultados[d] = {
            "Smin":Smin,
            "Smax":Smax,
            "g":g,
            "L":L_tramo
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

        # SI HAY FALLA → reforzar
        if g_vals[d_max] > 100:
            transf = 0.03
        else:
            transf = 0.01

        if pct[d_min] > transf:
            pct[d_min] -= transf
            pct[d_max] += transf

        # normalizar
        total = sum(pct.values())
        for d in pct:
            pct[d] /= total

    return pct

usar_auto = st.checkbox("Balance automático")

if usar_auto:
    pct = balancear(pct)

# ======================
# RESULTADOS
# ======================
st.subheader("Resultados")

res = evaluar(pct)

for d in ["1","7/8","3/4"]:

    if pct[d] < 0.01:
        continue

    L_tramo = res[d]["L"]
    n = int(L_tramo / 25)

    st.markdown(f"**{d}\" | {pct[d]*100:.0f}% | {n} varillas**")

    c1,c2,c3 = st.columns(3)

    c1.write(f"Smin: {res[d]['Smin']:.1f} ksi")
    c2.write(f"Smax: {res[d]['Smax']:.1f} ksi")
    c3.write(f"Goodman: {res[d]['g']:.0f} %")

# ======================
# GRAFICO
# ======================
st.subheader("Goodman")

x = np.linspace(0,150,200)
y = goodman(x)

fig, ax = plt.subplots()

ax.plot(x,y)
ax.plot(x,x,'--')

for d in res:
    ax.scatter(res[d]["Smin"],res[d]["Smax"])
    ax.text(res[d]["Smin"],res[d]["Smax"],d)

st.pyplot(fig)


