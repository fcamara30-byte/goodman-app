import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# ======================
# CONFIG
# ======================
st.set_page_config(layout="wide")

# ======================
# HEADER CON LOGO
# ======================
col_logo, col_title = st.columns([1,5])

with col_logo:
    st.image("https://i.imgur.com/8QfF0pE.png", width=120)

with col_title:
    st.title("Goodman – Fatiga & Corrosión")

# ======================
# DATOS
# ======================
materiales = {
    "DA78": {"uts_a": 30.0, "b": 0.5625},
    "HS97": {"uts_a": 50.0, "b": 0.375},
    "Alpha CS": {"uts_a": 44.64, "b": 0.375},
    "Alpha HS": {"uts_a": 55.36, "b": 0.375},
    "D New": {"uts_a": 42.86, "b": 0.357},
}

CO2 = {"Nada":1.0,"Bajo":1.0,"Medio":0.9,"Alto":0.8}
H2S = {"Nada":1.0,"Bajo":0.95,"Medio":0.8,"Alto":0.75}

BSR = {
    "0":1.0,
    "1":1.0,
    "2":0.95,
    "3":0.9,
    "4":0.82,
    "5":0.74,
    "6":0.65
}

CLORUROS = {
    "0 ppm":1.0,
    "Bajo":1.0,
    "Medio":0.9,
    "Alto":0.8
}

def goodman(smin, uts_a, b, f):
    return (uts_a + b*smin)*f

# ======================
# LAYOUT PRINCIPAL
# ======================
col1, col2 = st.columns([1,2])

# ======================
# INPUTS (IZQUIERDA)
# ======================
with col1:
    st.subheader("Inputs")

    material = st.selectbox("Material", list(materiales.keys()))
    co2 = st.selectbox("CO₂", list(CO2.keys()))
    h2s = st.selectbox("H₂S", list(H2S.keys()))
    bsr = st.selectbox("BSR", list(BSR.keys()))
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
# GRAFICO (DERECHA)
# ======================
with col2:

    fig, ax = plt.subplots(figsize=(7,6))

    for mat in materiales:
        y = (materiales[mat]["uts_a"] + materiales[mat]["b"] * smin) * f

        if mat == material:
            ax.plot(smin, y, linewidth=3, color='blue')

            ax.text(
                smin[-1], y[-1],
                mat,
                fontsize=11,
                color='blue',
                weight='bold'
            )
        else:
            ax.plot(smin, y, alpha=0.25, color='gray')

            ax.text(
                smin[-1], y[-1],
                mat,
                fontsize=8,
                color='gray',
                alpha=0.5
            )

    # línea 45°
    ax.plot(smin, smin, 'k--')

    # punto
    ax.scatter(smin_user, smax_user, color="red", s=100)

    # ejes desde origen
    ax.set_xlim(0,150)
    ax.set_ylim(0,150)

    ax.set_xlabel("Smin (ksi)")
    ax.set_ylabel("Smax (ksi)")
    ax.set_title("Diagrama de Goodman")
    ax.grid()

    st.pyplot(fig)

    # ======================
    # RESULTADOS
    # ======================
    st.markdown("---")
    st.subheader("Resultados y Conclusión")

    sadm_user = goodman(smin_user, uts_a, b, f)
    FS = sadm_user / smax_user if smax_user > 0 else 0

    col_r1, col_r2, col_r3 = st.columns(3)

    col_r1.metric("Factor total", round(f,3))
    col_r2.metric("Sadm", round(sadm_user,2))
    col_r3.metric("FS", round(FS,2))

    if FS >= 1:
        st.success("✅ CONDICIÓN SEGURA")
    else:
        st.error("❌ CONDICIÓN CRÍTICA")
