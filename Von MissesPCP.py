import streamlit as st
import math

st.set_page_config(layout="wide")

st.title("📊 PCP + Sarta (Von Mises - Diseño Real)")

# =========================
# INPUTS PRINCIPALES
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
# BOTON
# =========================
if st.button("CALCULAR"):

    # -------------------------
    # TORQUE FINAL
    # -------------------------
    pres_nivel = (nivel * densidad) / 10000
    pres_total = pres_linea + pres_nivel

    pot_h = prod * pres_total * 0.0014
    pot_c = pot_h / 0.6
    torque = (5252 * pot_c) / rpm

    # factor fluido
    f = (1 + viscosidad/1000) * (1 + solidos/100)
    torque *= f

    # -------------------------
    # VARILLAS
    # -------------------------
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

    von = math.sqrt(sigma**2 + 3*tau**2)

    sigma_y = YIELD[material]
    uso = (von / sigma_y) * 100

    # -------------------------
    # RESULTADOS
    # -------------------------
    st.markdown("---")
    st.subheader("Resultados")

    col3, col4, col5 = st.columns(3)

    col3.metric("Torque (lb-ft)", f"{torque:.1f}")
    col4.metric("Tensión Axial (ksi)", f"{sigma:.2f}")
    col5.metric("Tensión Torsional (ksi)", f"{tau:.2f}")

    col6, col7 = st.columns(2)

    col6.metric("Von Mises (ksi)", f"{von:.2f}")

    # color criterio
    if uso < 70:
        color = "green"
    elif uso < 100:
        color = "orange"
    else:
        color = "red"

    col7.markdown(f"### Von Mises (%): **:{color}[{uso:.1f}%]**")

    fs = sigma_y / von
    st.metric("Factor de Seguridad", f"{fs:.2f}")
``
