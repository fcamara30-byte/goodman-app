import streamlit as st
import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

# =========================
# UI COMPACTA
# =========================
st.markdown("""
<style>
div[data-testid="stNumberInput"] {
    width: 220px;
}
</style>
""", unsafe_allow_html=True)

st.title("📊 PCP + Sarta (Von Mises - Diseño Real)")

# =========================
# INPUTS
# =========================
col1, col2 = st.columns(2)

with col1:
    st.subheader("Datos PCP")

    profundidad = st.number_input("Profundidad (m)", value=600, step=100)
    rpm = st.number_input("RPM", value=350)
    prod = st.number_input("Producción (m3/d)", value=150.0)
    pres_linea = st.number_input("Presión línea (kg/cm2)", value=14.1)
    nivel = st.number_input("Nivel (m)", value=570, step=50)
    densidad = st.number_input("Densidad (kg/m3)", value=840.0)
    eficiencia = st.number_input("Eficiencia", value=0.6)

with col2:
    st.subheader("Fluido y Sarta")

    viscosidad = st.number_input("Viscosidad (cP)", value=300, step=40)
    solidos = st.number_input("% Sólidos", value=5.0)

    rod = st.selectbox("Diámetro varilla", ["7/8", "1", "1 1/8"])

    material = st.selectbox(
        "Tipo de varilla",
        ["DA 78", "HS97", "Alpha CS", "Alpha HS", "D New", "DSK75", "HA96"]
    )

# =========================
# BASE DATOS
# =========================
RODS = {
    "7/8": {"d": 0.875, "peso": 2.22},
    "1": {"d": 1.0, "peso": 2.67},
    "1 1/8": {"d": 1.125, "peso": 3.37}
}

YIELD = {
    "DA 78": 85,
    "HS97": 115,
    "Alpha CS": 110,
    "Alpha HS": 135,
    "D New": 85,
    "DSK75": 85,
    "HA96": 115
}

# =========================
# BOTON CALCULO
# =========================
if st.button("CALCULAR"):

    # -------------------------
    # TORQUE FINAL
    # -------------------------
    pres_nivel = (nivel * densidad) / 10000
    pres_total = pres_linea + pres_nivel

    pot_h = prod * pres_total * 0.0014
    pot_c = pot_h / eficiencia

    torque = (5252 * pot_c) / rpm

    # factor fluido
    f_fluido = (1 + viscosidad / 1000) * (1 + solidos / 100)
    torque *= f_fluido

    # -------------------------
    # VARILLA
    # -------------------------
    d = RODS[rod]["d"] * 0.0254
    r = d / 2

    A = math.pi * d**2 / 4
    J = math.pi * d**4 / 32

    peso_lineal = RODS[rod]["peso"] * 47.88
    peso_total = peso_lineal * profundidad

    carga_fluido = densidad * 9.81 * profundidad * A
    F = peso_total + carga_fluido

    # -------------------------
    # ESFUERZOS (KSI)
    # -------------------------
    sigma = (F / A) / 6894757
    tau = ((torque * 1.35582 * r) / J) / 6894757

    von = math.sqrt(sigma**2 + 3 * tau**2)

    sigma_y = YIELD[material]
    uso = (von / sigma_y) * 100
    fs = sigma_y / von

    # -------------------------
    # RESULTADOS
    # -------------------------
    st.markdown("---")
    st.subheader("Resultados Mecánicos")

    col3, col4, col5 = st.columns(3)
    col3.metric("Torque (lb-ft)", f"{torque:.1f}")
    col4.metric("Tensión Axial (ksi)", f"{sigma:.2f}")
    col5.metric("Tensión Torsional (ksi)", f"{tau:.2f}")

    col6, col7, col8 = st.columns(3)
    col6.metric("Von Mises (ksi)", f"{von:.2f}")
    col7.metric("Von Mises (%)", f"{uso:.1f}%")
    col8.metric("FS", f"{fs:.2f}")

    # =========================
    # DESVIACION
    # =========================
    st.markdown("---")
    st.subheader("Trayectoria de Pozo")

    df = pd.DataFrame({
        "md": [5,165,199,226,245,263,276,323,379,417,442,498,507,517,538,585,639,714,807,873,930],
        "inc": [0,2.25,2.75,6.25,9.25,11.25,11.25,12,12.75,12.5,16,22,23.75,26,26.25,27.25,29.75,30.5,33,34,34],
        "az": [0,192,187,120,95,78,62,64,64,63,62,76,76,75,67,73,67,68,67,68,68]
    })

    df = st.data_editor(df, num_rows="dynamic")

    # -------------------------
    # CALCULO DESVIO
    # -------------------------
    inc_rad = np.radians(df["inc"])

    peso_lbft = RODS[rod]["peso"]

    carga_lat = peso_lbft * np.sin(inc_rad) * df["md"] * 0.05

    clasificacion = []
    colores = []

    for c in carga_lat:
        if c < 30:
            clasificacion.append("Bajo contacto")
            colores.append("green")
        elif c < 60:
            clasificacion.append("1 Centralizador")
            colores.append("yellow")
        elif c < 100:
            clasificacion.append("3 Centralizadores")
            colores.append("orange")
        else:
            clasificacion.append("Black Mamba")
            colores.append("red")

    df["Carga lateral (lb)"] = carga_lat
    df["Recomendación"] = clasificacion

    # torque afectado por desvío
    factor_desvio = 1 + np.mean(np.sin(inc_rad)) * 0.4
    torque_desviado = torque * factor_desvio

    st.write("### Torque con desviación:", round(torque_desviado,1), "lb-ft")

    # -------------------------
    # PLOT
    # -------------------------
    fig, ax = plt.subplots()

    ax.scatter(df["md"], df["inc"], c=colores)

    ax.set_xlabel("MD (m)")
    ax.set_ylabel("Inclinación (°)")
    ax.set_title("Perfil con Contacto")

    st.pyplot(fig)

    st.dataframe(df)
