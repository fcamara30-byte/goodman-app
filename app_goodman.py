import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

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
# MATERIALES
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
# FS MATERIAL (Excel)
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
def goodman(smin, uts, b, fs):
    return (uts + b * smin) * fs

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

    ranking = []

    for mat in materiales:

        fs_mat = FS_material(mat, f_base)

        y = goodman(
            smin,
            materiales[mat]["uts_a"],
            materiales[mat]["b"],
            fs_mat
        )

        sadm = goodman(
            smin_user,
            materiales[mat]["uts_a"],
            materiales[mat]["b"],
            fs_mat
        )

        margen = sadm - smax_user

        ranking.append({
            "Material": mat,
            "FS": fs_mat,
            "Sadm": sadm,
            "Margen": margen
        })

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
    # RANKING
    # ======================
    df = pd.DataFrame(ranking)

    df = df.sort_values(by="Margen", ascending=False)

    # % Goodman
    df["%Goodman"] = ((smax_user - smin_user) / (df["Sadm"] - smin_user)) * 100

    st.markdown("##### Ranking de Materiales")

    st.dataframe(
        df.style.format({
            "FS": "{:.3f}",
            "Sadm": "{:.1f}",
            "Margen": "{:.1f}",
            "%Goodman": "{:.1f}"
        }),
        use_container_width=True
    )

    # ======================
    # MEJOR OPCION
    # ======================
    mejor = df.iloc[0]

    st.markdown("##### Recomendación")

    if mejor["Margen"] >= 0:
        st.success(f"Mejor opción: {mejor['Material']}")
    else:
        st.error("Uso de varillas revestidas y/o productos químicos para corrosión")
