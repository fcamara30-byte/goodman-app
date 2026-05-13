import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

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
# MATERIALES (actualizado)
# ======================
materiales = {
    "DA78": {"uts_a": 30.0, "b": 0.5625},
    "HS97": {"uts_a": 50.0, "b": 0.375},
    "CS propietario": {"uts_a": 44.64, "b": 0.375},
    "HS propietario": {"uts_a": 55.36, "b": 0.375},
    "D New": {"uts_a": 42.86, "b": 0.375},
    "DSK75": {"uts_a": 42.86, "b": 0.375},
    "HA96": {"uts_a": 50.0, "b": 0.375}
}

# ======================
# FACTORES
# ======================
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

def factor_cloruros(ppm):
    if ppm < 9000:
        return 1.0
    else:
        return 1 - (0.000019 * (ppm ** 0.8))

# ======================
# FS MATERIAL
# ======================
def FS_material(mat, f):

    if f == 1:
        return 1

    if mat == "DA78":
        return f * 0.95
    elif mat == "HS97":
        return f
    elif mat == "CS propietario":
        return f * 0.96
    elif mat == "HS propietario":
        return f * 0.83
    elif mat == "D New":
        return f * 0.94
    elif mat == "DSK75":
        return f if f < 0.83 else 1
    elif mat == "HA96":
        return f * 0.93

# ======================
# GOODMAN
# ======================
def goodman(smin, uts_a, b, fs):
    return (uts_a + b*smin) * fs

# ======================
# LAYOUT
# ======================
col1, col2 = st.columns([1,2])

# ======================
# INPUTS
# ======================
with col1:

    st.markdown("#### Inputs")

    r1c1, r1c2 = st.columns(2)
    material = r1c1.selectbox("Material", list(materiales.keys()))
    co2 = r1c2.selectbox("CO₂", list(CO2.keys()))

    r2c1, r2c2 = st.columns(2)
    h2s = r2c1.selectbox("H₂S", list(H2S.keys()))
    bsr = r2c2.selectbox("BSR (caldos positivos)", list(BSR.keys()))

    cl_ppm = st.number_input("Cloruros (ppm)", 0, 200000, 0)

    smin_user = st.slider("Smin (ksi)", 0, 150, 30)
    smax_user = st.slider("Smax (ksi)", 0, 150, 50)

# ======================
# CALCULOS
# ======================
f_base = CO2[co2] * H2S[h2s] * BSR[bsr] * factor_cloruros(cl_ppm)
smin = np.linspace(0,150,200)

# ======================
# GRAFICO
# ======================
with col2:

    fig, ax = plt.subplots(figsize=(7,3.8))

    materiales_validos = []

    for mat in materiales:

        fs_mat = FS_material(mat, f_base)

        y = goodman(
            smin,
            materiales[mat]["uts_a"],
            materiales[mat]["b"],
            fs_mat
        )

        # Evaluación operativa
        sadm_user = goodman(
            smin_user,
            materiales[mat]["uts_a"],
            materiales[mat]["b"],
            fs_mat
        )

        if smax_user <= sadm_user:
            materiales_validos.append(mat)

        # Graficado
        if mat == material:
            ax.plot(smin, y, linewidth=3, color='blue')
            ax.text(smin[-1], y[-1], mat,
                    fontsize=9, color='blue', weight='bold')
        else:
            ax.plot(smin, y, color='gray', alpha=0.2)

    ax.plot(smin, smin, 'k--')
    ax.scatter(smin_user, smax_user, color="red", s=60)

    ax.set_xlim(0,150)
    ax.set_ylim(0,150)

    ax.set_xlabel("Smin (ksi)")
    ax.set_ylabel("Smax (ksi)")

    ax.grid()
    plt.tight_layout()

    st.pyplot(fig)

    # ======================
    # RESULTADOS FORMATO CUADRO
    # ======================
    fs_sel = FS_material(material, f_base)
    sadm_user = goodman(
        smin_user,
        materiales[material]["uts_a"],
        materiales[material]["b"],
        fs_sel
    )

    if sadm_user != smin_user:
        goodman_pct = ((smax_user - smin_user)/(sadm_user - smin_user))*100
    else:
        goodman_pct = 0

    st.markdown("###### Resultados")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("FS", f"{fs_sel:.3f}")
    c2.metric("Factor Base", f"{f_base:.3f}")
    c3.metric("Sadm (ksi)", f"{sadm_user:.1f}")
    c4.metric("%Goodman", f"{goodman_pct:.1f}")

    # ======================
    # RECOMENDACION INTELIGENTE
    # ======================
    st.markdown("###### Recomendación")

    if smax_user > sadm_user:

        if len(materiales_validos) > 0:
            st.warning("Recomendado usar: " + ", ".join(materiales_validos))
        else:
            st.error("Uso de varillas revestidas y/o productos químicos para corrosión")

