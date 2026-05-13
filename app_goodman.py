import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# ======================
# CONFIG
# ======================
st.set_page_config(layout="wide")

# ======================
# HEADER
# ======================
col_title, col_brand = st.columns([5,2])

with col_title:
    st.markdown("### Goodman – Fatiga y Corrosión")

with col_brand:
    st.markdown("#### *Powered by Apex*")

# ======================
# DATOS
# ======================
materiales = {
    "DA78": {"uts_a": 30.0, "b": 0.5625},
    "HS97": {"uts_a": 50.0, "b": 0.375},
    "CS propietario": {"uts_a": 44.64, "b": 0.375},
    "HS propietario": {"uts_a": 55.36, "b": 0.375},
    "D New": {"uts_a": 42.86, "b": 0.357}
}

CO2 = {"Nada":1.0,"Bajo":1.0,"Medio":0.9,"Alto":0.8}
H2S = {"Nada":1.0,"Bajo":0.95,"Medio":0.8,"Alto":0.75}

BSR = {
    "0": 1.0,
    "1": 1.0,
    "2": 0.95,
    "3": 0.9,
    "4": 0.82,
    "5": 0.74,
    "6": 0.65
}

CLORUROS = {
    "0 ppm": 1.0,
    "Bajo": 1.0,
    "Medio": 0.9,
    "Alto": 0.8
}

def goodman(smin, uts_a, b, f):
    return (uts_a + b*smin) * f

# ======================
# LAYOUT
# ======================
col1, col2 = st.columns([1,2])

# ======================
# INPUTS COMPACTOS
# ======================
with col1:

    st.markdown("#### Inputs")

    r1c1, r1c2 = st.columns(2)
    material = r1c1.selectbox("Material", list(materiales.keys()))
    co2 = r1c2.selectbox("CO₂", list(CO2.keys()))

    r2c1, r2c2 = st.columns(2)
    h2s = r2c1.selectbox("H₂S", list(H2S.keys()))
    bsr = r2c2.selectbox("BSR", list(BSR.keys()))

    cl = st.selectbox("Cloruros", list(CLORUROS.keys()))

    smin_user = st.slider("Smin", 0, 150, 30)
    smax_user = st.slider("Smax", 0, 150, 50)

# ======================
# CALCULO
# ======================
f = CO2[co2] * H2S[h2s] * BSR[bsr] * CLORUROS[cl]

uts_a = materiales[material]["uts_a"]
b = materiales[material]["b"]

smin = np.linspace(0,150,200)

# ======================
# GRAFICO
# ======================
with col2:

    fig, ax = plt.subplots(figsize=(8,5))

    for mat in materiales:

        y = (materiales[mat]["uts_a"] + materiales[mat]["b"] * smin) * f

        if mat == material:
            ax.plot(smin, y, linewidth=3, color='blue')
            ax.text(smin[-1], y[-1], mat,
                    fontsize=10, color='blue', weight='bold')
        else:
            ax.plot(smin, y, alpha=0.2, color='gray')
            ax.text(smin[-1], y[-1], mat,
                    fontsize=7, color='gray', alpha=0.5)

    # línea 45°
    ax.plot(smin, smin, 'k--')

    # punto operativo
    ax.scatter(smin_user, smax_user, color="red", s=80)

    # ejes desde origen
    ax.set_xlim(0,150)
    ax.set_ylim(0,150)

    ax.set_xlabel("Smin (ksi)")
    ax.set_ylabel("Smax (ksi)")
    ax.grid()

    st.pyplot(fig)

    # ======================
    # RESULTADOS
    # ======================
    st.markdown("### Resultados")

    sadm_user = goodman(smin_user, uts_a, b, f)
    FS = sadm_user / smax_user if smax_user > 0 else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Factor", round(f,3))
    c2.metric("Sadm", round(sadm_user,2))
    c3.metric("FS", round(FS,2))

    # ======================
    # CLASIFICACION AMBIENTE (TU LOGICA)
    # ======================

    if f >= 0.95:
        ambiente = "Normal"
        st.success("Ambiente Normal")
    elif f >= 0.80:
        ambiente = "Moderado"
        st.info("Ambiente Moderado")
    elif f >= 0.70:
        ambiente = "Severo"
        st.warning("Ambiente Severo")
    else:
        ambiente = "Crítico"
        st.error("Ambiente Crítico")
