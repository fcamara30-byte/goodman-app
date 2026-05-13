import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

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
BSR = {"0":1.0,"1":1.0,"2":0.95,"3":0.9,"4":0.82,"5":0.74,"6":0.65}

# ✅ NUEVO: CLORUROS (ajustar según tu Excel real)
CLORUROS = {
    "0 ppm": 1.0,
    "Bajo": 1.0,
    "Medio": 0.9,
    "Alto": 0.8
}

# ======================
# FUNCIÓN
# ======================

def goodman(smin, uts_a, b, f):
    return (uts_a + b*smin) * f

# ======================
# LAYOUT
# ======================

col1, col2 = st.columns([1,2])

# ======================
# CONTROLES (IZQUIERDA)
# ======================

with col1:
    st.header("Inputs")

    material = st.selectbox("Material", list(materiales.keys()))
    co2 = st.selectbox("CO₂", list(CO2.keys()))
    h2s = st.selectbox("H₂S", list(H2S.keys()))
    bsr = st.selectbox("BSR", list(BSR.keys()))
    cl = st.selectbox("Cloruros", list(CLORUROS.keys()))

    smin_user = st.slider("Smin", 0, 150, 30)
    smax_user = st.slider("Smax", 0, 150, 50)

# ======================
# CÁLCULO
# ======================

f = CO2[co2] * H2S[h2s] * BSR[bsr] * CLORUROS[cl]

uts_a = materiales[material]["uts_a"]
b = materiales[material]["b"]

smin = np.linspace(0,150,200)

# ======================
# GRÁFICO (DERECHA)
# ======================

with col2:
    st.header("Diagrama de Goodman")

    fig, ax = plt.subplots(figsize=(6,6))

    # todas las curvas
    for mat in materiales:
        y = (materiales[mat]["uts_a"] + materiales[mat]["b"] * smin) * f
        ax.plot(smin, y, alpha=0.3)

    # curva seleccionada
    y_sel = goodman(smin, uts_a, b, f)
    ax.plot(smin, y_sel, linewidth=3, label=material)

    # línea 45°
    ax.plot(smin, smin, 'k--', label="45°")

    # punto
    ax.scatter(smin_user, smax_user, color="red", s=100)

    ax.set_xlabel("Smin")
    ax.set_ylabel("Smax")
    ax.grid()
    ax.legend()

    st.pyplot(fig)

# ======================
# RESULTADOS
# ======================

st.subheader("Resultados")

sadm_user = goodman(smin_user, uts_a, b, f)
FS = sadm_user / smax_user if smax_user > 0 else 0

st.write("Factor total:", round(f,3))
st.write("Sadm:", round(sadm_user,2))
st.write("FS:", round(FS,2))

if FS >= 1:
    st.success("✅ Seguro")
else:
    st.error("❌ Crítico")
