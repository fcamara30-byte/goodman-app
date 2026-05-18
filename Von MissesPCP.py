import streamlit as st

st.set_page_config(layout="wide")

st.title("📊 Cálculo de Torque PCP (Replica Excel)")

# -------------------------------
# INPUTS (lado izquierdo)
# -------------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("Datos de Entrada")

    rpm = st.number_input("RPM", value=350)
    produccion = st.number_input("Producción (m3/d)", value=150.0)
    presion_linea = st.number_input("Presión de Línea (kg/cm2)", value=200.0)
    nivel = st.number_input("Nivel dinámico (m)", value=600.0)
    densidad = st.number_input("Densidad (kg/m3)", value=950.0)
    eficiencia = st.number_input("Rendimiento bomba", value=0.6)

with col2:
    st.subheader("Variables del Modelo")

    k = 5252

    presion_nivel = (nivel * densidad) / 10000
    presion_total = presion_linea + presion_nivel
    pot_h = produccion * presion_total * 0.0014
    pot_c = pot_h / eficiencia
    torque_lbft = (k * pot_c) / rpm
    torque_nm = torque_lbft * 1.35582

    st.write("Presión de Nivel:", round(presion_nivel, 2))
    st.write("Presión Total:", round(presion_total, 2))
    st.write("Potencia Hidráulica:", round(pot_h, 2))
    st.write("Potencia Consumida:", round(pot_c, 2))

# -------------------------------
# RESULTADOS (abajo como Excel)
# -------------------------------
st.markdown("---")
st.subheader("Resultados")

col3, col4 = st.columns(2)

with col3:
    st.metric("Torque [lb-ft]", round(torque_lbft, 2))

with col4:
    st.metric("Torque [Nm]", round(torque_nm, 2))

# -------------------------------
# FORMULAS (como tu Excel)
# -------------------------------
st.markdown("---")
st.subheader("Formulación (igual al Excel)")

st.text("""
Torque = (k * Potencia Consumida) / RPM
Potencia Consumida = Potencia Hidráulica / Eficiencia
Potencia Hidráulica = Producción * Presión Total * 0.0014
Presión Total = Presión Línea + Presión Nivel
Presión Nivel = (Nivel * Densidad) / 10
""")
