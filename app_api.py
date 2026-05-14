import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

# ======================
# TITULO
# ======================
st.title("API RP 11L – Cálculo de Cargas en Varillas")

# ======================
# INPUTS
# ======================
col1, col2 = st.columns(2)

with col1:
    st.subheader("Datos del pozo")

    L_m = st.number_input("Profundidad (m)", 500, 5000, 2000)
    H_m = st.number_input("Nivel dinámico (m)", 100, 4000, 1500)
    G = st.slider("Gravedad específica", 0.6, 1.2, 1.0)

with col2:
    st.subheader("Bomba y operación")

    D = st.slider("Diámetro bomba (in)", 1.0, 3.0, 1.5)
    S = st.slider("Carrera (in)", 50, 200, 100)
    N = st.slider("SPM", 1, 20, 10)

# ======================
# PROPIEDADES VARILLAS (API)
# ======================
rods = {
    "1":   {"area":0.786, "peso":2.90},
    "7/8": {"area":0.601, "peso":2.22},
    "3/4": {"area":0.442, "peso":1.63}
}

# ======================
# CALCULO STRING
# ======================
def calcular_string(L_m, G):

    L_ft = L_m * 3.28084

    # distribución típica
    frac_sup = 0.3
    frac_mid = 0.4
    frac_fondo = 0.3

    L_sup = L_ft * frac_sup
    L_mid = L_ft * frac_mid
    L_fondo = L_ft * frac_fondo

    W = (
        L_sup * rods["1"]["peso"] +
        L_mid * rods["7/8"]["peso"] +
        L_fondo * rods["3/4"]["peso"]
    )

    Wri = W * (1 - 0.128 * G)

    A_min = rods["3/4"]["area"]
    A_top = rods["1"]["area"]

    return W, Wri, A_min, A_top

# ======================
# CALCULO API
# ======================
def calcular_cargas(L_m, H_m, D, S, N, G):

    L_ft = L_m * 3.28084
    H_ft = H_m * 3.28084

    W, Wri, A_min, A_top = calcular_string(L_m, G)

    # área bomba
    A_pump = np.pi * (D**2) / 4

    # carga fluido API
    Fo = 0.433 * G * H_ft * A_pump

    # ======================
    # APROX DINAMICA (provisional)
    # ======================
    Fi = Fo * (1.1 + 0.01 * N)
    F2 = Fo * (0.6)

    PPRL = Wri + Fi
    MPRL = Wri - F2

    # tensiones
    Smax = PPRL / A_min / 1000
    Smin = MPRL / A_min / 1000

    Stress_top = PPRL / A_top / 1000

    return PPRL, MPRL, Smax, Smin, Stress_top, W, Wri

# ======================
# CALCULAR
# ======================
PPRL, MPRL, Smax, Smin, Stress_top, W, Wri = calcular_cargas(L_m, H_m, D, S, N, G)

# ======================
# RESULTADOS
# ======================
st.subheader("Resultados")

c1, c2, c3 = st.columns(3)

c1.metric("PPRL (lb)", f"{PPRL:,.0f}")
c2.metric("MPRL (lb)", f"{MPRL:,.0f}")
c3.metric("Peso varillas (lb)", f"{W:,.0f}")

c4, c5, c6 = st.columns(3)

c4.metric("Smax (ksi)", f"{Smax:.1f}")
c5.metric("Smin (ksi)", f"{Smin:.1f}")
c6.metric("Stress cabeza (ksi)", f"{Stress_top:.1f}")

# ======================
# GRAFICO SIMPLE
# ======================
st.subheader("Condición de carga")

fig, ax = plt.subplots()

ax.scatter(Smin, Smax, color="red")
ax.set_xlabel("Smin (ksi)")
ax.set_ylabel("Smax (ksi)")

ax.set_xlim(0, max(Smax*1.2, 1))
ax.set_ylim(0, max(Smax*1.2, 1))

ax.grid()

st.pyplot(fig)

# ======================
# INFO STRING
# ======================
st.subheader("Configuración de varillas")

df = pd.DataFrame({
    "Tramo": ["Superficie", "Medio", "Fondo"],
    "Diámetro": ['1"', '7/8"', '3/4"']
})

st.dataframe(df, use_container_width=True)
