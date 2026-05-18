import streamlit as st
import math

st.set_page_config(layout="wide")

st.title("📊 PCP + Sarta + Von Mises")

# -------------------------
# INPUTS
# -------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("Datos PCP")

    rpm = st.number_input("RPM", value=350)
    produccion = st.number_input("Producción (m3/d)", value=150.0)
    presion_linea = st.number_input("Presión línea (kg/cm2)", value=14.1)
    nivel = st.number_input("Nivel (m)", value=570.0)
    densidad = st.number_input("Densidad (kg/m3)", value=840.0)
    eficiencia = st.number_input("Eficiencia", value=0.6)

with col2:
    st.subheader("Fluido + Sarta")

    viscosidad = st.number_input("Viscosidad (cP)", value=300.0)
    solidos = st.number_input("% Sólidos", value=5.0)
    profundidad = st.number_input("Profundidad (m)", value=600.0)

    rod = st.selectbox("Diámetro varilla", ["7/8", "1", "1 1/8"])

# -------------------------
# BOTON
# -------------------------
if st.button("CALCULAR"):

    # -------------------------
    # PCP
    # -------------------------
    pres_nivel = (nivel * densidad) / 10000
    pres_total = presion_linea + pres_nivel

    pot_h = produccion * pres_total * 0.0014
    pot_c = pot_h / eficiencia
    torque = (5252 * pot_c) / rpm

    # -------------------------
    # FLUIDO
    # -------------------------
    f_visc = 1 + viscosidad / 1000
    f_sol = 1 + solidos / 100
    f_total = f_visc * f_sol

    torque_corr = torque * f_total

    # -------------------------
    # VARILLAS
    # -------------------------
    RODS = {
        "7/8": {"d": 0.875, "peso": 2.22},
        "1": {"d": 1.0, "peso": 2.67},
        "1 1/8": {"d": 1.125, "peso": 3.37}
    }

    d = RODS[rod]["d"] * 0.0254
    r = d / 2

    A = math.pi * d**2 / 4
    J = math.pi * d**4 / 32

    peso = RODS[rod]["peso"] * 47.88
    peso_total = peso * profundidad

    carga_fluido = densidad * 9.81 * profundidad * A
    F = peso_total + carga_fluido

    sigma = F / A / 1e6
    tau = (torque_corr * 1.35582 * r) / J / 1e6

    von = math.sqrt(sigma**2 + 3 * tau**2)

    # -------------------------
    # OUTPUT
    # -------------------------
    st.markdown("---")
    st.subheader("Resultados")

    col3, col4, col5 = st.columns(3)

    col3.metric("Torque base", f"{torque:.1f} lb-ft")
    col4.metric("Torque corregido", f"{torque_corr:.1f} lb-ft")
    col5.metric("Von Mises", f"{von:.1f} MPa")

    st.write("Esfuerzo axial:", round(sigma, 1), "MPa")
    st.write("Esfuerzo torsión:", round(tau, 1), "MPa")
    st.write("Factor fluido:", round(f_total, 2))
