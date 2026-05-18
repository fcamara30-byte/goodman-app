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

    profundidad = st.number_input("Profundidad (m)", 600, step=100)
    rpm = st.number_input("RPM", 350)
    prod = st.number_input("Producción (m3/d)", 150.0)
    pres_linea = st.number_input("Presión línea (kg/cm2)", 14.1)
    nivel = st.number_input("Nivel (m)", 570, step=50)
    densidad = st.number_input("Densidad (kg/m3)", 840.0)
    eficiencia = st.number_input("Eficiencia", 0.6)

with col2:
    st.subheader("Fluido y Sarta")

    viscosidad = st.number_input("Viscosidad (cP)", 300, step=40)
    solidos = st.number_input("% Sólidos", 5.0)

    rod = st.selectbox("Diámetro varilla", ["7/8", "1", "1 1/8"])

    material = st.selectbox(
        "Material",
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
# CALCULO PRINCIPAL
# =========================
pres_nivel = (nivel * densidad) / 10000
pres_total = pres_linea + pres_nivel

pot_h = prod * pres_total * 0.0014
pot_c = pot_h / eficiencia

torque = (5252 * pot_c) / rpm

# fluido
f_fluido = (1 + viscosidad / 1000) * (1 + solidos / 100)
torque *= f_fluido

# varilla
d = RODS[rod]["d"] * 0.0254
r = d / 2

A = math.pi * d**2 / 4
J = math.pi * d**4 / 32

peso_lineal = RODS[rod]["peso"] * 47.88
peso_total = peso_lineal * profundidad

carga_fluido = densidad * 9.81 * profundidad * A
F = peso_total + carga_fluido

# esfuerzos
sigma = (F / A) / 6894757
tau = ((torque * 1.35582 * r) / J) / 6894757

von = math.sqrt(sigma**2 + 3 * tau**2)
sigma_y = YIELD[material]

uso = (von / sigma_y) * 100
fs = sigma_y / von

# =========================
# RESULTADOS
# =========================
st.markdown("---")
st.subheader("Resultados")

c1, c2, c3 = st.columns(3)
c1.metric("Torque (lb-ft)", f"{torque:.1f}")
c2.metric("Tensión Axial (ksi)", f"{sigma:.2f}")
c3.metric("Tensión Torsional (ksi)", f"{tau:.2f}")

c4, c5, c6 = st.columns(3)
c4.metric("Von Mises (ksi)", f"{von:.2f}")
c5.metric("Von Mises (%)", f"{uso:.1f}%")
c6.metric("FS", f"{fs:.2f}")

# =========================
# MODO POZO
# =========================
st.markdown("---")
modo = st.selectbox("Modo de Pozo", ["Vertical", "Desviado"])

if modo == "Desviado":

    st.subheader("Trayectoria (Copiar/Pegar columnas md-inc-az)")

    df = st.data_editor(
        pd.DataFrame(columns=["md", "inc", "az"]),
        height=250,
        num_rows="dynamic",
        use_container_width=True
    )

    if len(df) > 1:

        # =====================
        # DLS
        # =====================
        dls = [0]

        for i in range(1, len(df)):
            md1, md2 = df.loc[i-1, "md"], df.loc[i, "md"]
            inc1, inc2 = np.radians(df.loc[i-1, "inc"]), np.radians(df.loc[i, "inc"])
            az1, az2 = np.radians(df.loc[i-1, "az"]), np.radians(df.loc[i, "az"])

            delta_md = (md2 - md1) * 3.28084

            cos_dogleg = (
                np.sin(inc1)*np.sin(inc2)*np.cos(az2-az1) +
                np.cos(inc1)*np.cos(inc2)
            )

            cos_dogleg = np.clip(cos_dogleg, -1, 1)
            dogleg = np.arccos(cos_dogleg)

            dls.append(np.degrees(dogleg) * (100 / delta_md))

        df["DLS"] = dls

        # =====================
        # COORDENADAS 3D
        # =====================
        df["inc_rad"] = np.radians(df["inc"])
        df["az_rad"] = np.radians(df["az"])

        df["X"] = np.cumsum(np.sin(df["inc_rad"]) * np.cos(df["az_rad"]))
        df["Y"] = np.cumsum(np.sin(df["inc_rad"]) * np.sin(df["az_rad"]))
        df["Z"] = -df["md"]

        # =====================
        # CONTACTO
        # =====================
        carga_lat = RODS[rod]["peso"] * np.sin(df["inc_rad"]) * df["md"] * 0.05

        colores = []
        rec = []

        for c in carga_lat:
            if c < 30:
                colores.append("green")
                rec.append("Bajo contacto")
            elif c < 60:
                colores.append("yellow")
                rec.append("1 centralizador")
            elif c < 100:
                colores.append("orange")
                rec.append("3 centralizadores")
            else:
                colores.append("red")
                rec.append("Black Mamba")

        df["Carga lateral"] = carga_lat
        df["Recomendación"] = rec

        # torque ajustado
        factor_desvio = 1 + np.mean(np.sin(df["inc_rad"])) * 0.4
        torque_desviado = torque * factor_desvio

        st.write("### Torque con desviación:", round(torque_desviado,1), "lb-ft")

        # =====================
        # PLOT 3D
        # =====================
        fig = plt.figure()
