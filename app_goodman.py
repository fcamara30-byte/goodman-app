import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os

st.set_page_config(layout="wide")

# ======================
# CONTADOR DE VISITAS
# ======================
def contador_visitas():
    archivo = "visitas.txt"

    if not os.path.exists(archivo):
        with open(archivo, "w") as f:
            f.write("0")

    with open(archivo, "r+") as f:
        try:
            count = int(f.read())
        except:
            count = 0

        count += 1
        f.seek(0)
        f.write(str(count))
        f.truncate()

    return count

visitas = contador_visitas()

# ======================
# ESTILO
# ======================
st.markdown("""
<style>
.titulo {font-size:30px; font-weight:700; color:#0B3C8C;}
.subtitulo {font-size:17px; font-weight:600; color:#1F4E79;}
.cursiva {font-style: italic; color:#444;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="titulo">Selector de varillas 🛠️</div>', unsafe_allow_html=True)
st.markdown('<div class="cursiva">Según Criterio Goodman + Corrosión-Fatiga</div>', unsafe_allow_html=True)
st.caption(f"Visitas totales: {visitas}")

# ======================
# DATOS
# ======================
materiales = {
    "DA78":{"uts_a":30,"b":0.5625},
    "HS97":{"uts_a":50,"b":0.375},
    "CS propietario":{"uts_a":44.64,"b":0.375},
    "HS propietario":{"uts_a":55.36,"b":0.375},
    "D New":{"uts_a":42.86,"b":0.375},
    "DSK75":{"uts_a":42.86,"b":0.375},
    "HA96":{"uts_a":50,"b":0.375}
}

BSR = {"0":1,"1":1,"2":0.95,"3":0.9,"4":0.82,"5":0.74,"6":0.65}

# ======================
# FACTORES
# ======================
def factor_co2(sel):
    return {
        "Nada (0 psi)":1.0,
        "Bajo (0–20 psi)":0.98,
        "Medio (21–100 psi)":0.90,
        "Alto (>100 psi)":0.80
    }[sel]

def factor_h2s(sel):
    return {
        "Nada (0 psi)":1.0,
        "Bajo (0–1 psi)":0.95,
        "Medio (1–2 psi)":0.80,
        "Alto (>2 psi)":0.75
    }[sel]

def factor_cloruros(ppm):
    return 1 if ppm < 9000 else 1 - (0.000019 * (ppm**0.8))

# ======================
# FUNCIONES
# ======================
def FS_material(mat,f):
    if f==1: return 1
    if mat=="DA78": return f*0.95
    elif mat=="HS97": return f
    elif mat=="CS propietario": return f*0.96
    elif mat=="HS propietario": return f*0.80
    elif mat=="D New": return f*0.94
    elif mat=="DSK75": return f if f < 0.83 else 1
    elif mat=="HA96": return f*0.93

def goodman(x,uts,b,fs):
    return (uts + b*x) * fs

# ======================
# INPUTS
# ======================
l, r = st.columns([1,2])

with l:
    material = st.selectbox("Material", list(materiales.keys()))
    co2 = st.selectbox("PPCO₂", list(factor_co2("").keys()) if False else [
        "Nada (0 psi)", "Bajo (0–20 psi)",
        "Medio (21–100 psi)", "Alto (>100 psi)"
    ])
    h2s = st.selectbox("PPH₂S", [
        "Nada (0 psi)", "Bajo (0–1 psi)",
        "Medio (1–2 psi)", "Alto (>2 psi)"
    ])
    bsr = st.selectbox("BSR", list(BSR.keys()))
    cl_ppm = st.number_input("Cloruros (ppm)",0,200000,0)

    smin_user = st.slider("Smin (ksi)",0,100,30)
    smax_user = st.slider("Smax (ksi)",0,100,50)

# ======================
# FACTOR BASE
# ======================
f_base = factor_co2(co2)*factor_h2s(h2s)*BSR[bsr]*factor_cloruros(cl_ppm)

# ✅ cálculo correcto del material seleccionado
fs_sel = FS_material(material, f_base)
sadm_user = goodman(
    smin_user,
    materiales[material]["uts_a"],
    materiales[material]["b"],
    fs_sel
)

x = np.linspace(0,100,200)

# ======================
# GRAFICO
# ======================
with r:

    fig, ax = plt.subplots(figsize=(6,4))

    # curva Goodman
    y = goodman(x, materiales[material]["uts_a"], materiales[material]["b"], fs_sel)

    # corte en vértice
    diff = y - x
    idx = np.where(diff <= 0)[0]
    corte = idx[0] if len(idx)>0 else len(x)

    x_clip = x[:corte]
    y_clip = y[:corte]

    # curvas
    ax.plot(x_clip, y_clip, "b", linewidth=3)
    ax.plot(x, x, "k", linewidth=2)

    # zona segura
    ax.fill_between(x_clip, x_clip, y_clip,
                    where=(y_clip >= x_clip),
                    color='green', alpha=0.15)

    # punto crítico
    ax.scatter(smin_user, smax_user,
               color="red",
               s=90,
               label="Punto crítico")

    # ✅ alerta Goodman
    if smax_user > sadm_user:
        ax.text(
            0.5, 0.15,
            "Seleccione otro tipo de varilla\n"
            "o utilice revestimiento + tratamiento químico",
            transform=ax.transAxes,
            fontsize=10,
            color="red",
            ha="center",
            bbox=dict(facecolor='white', alpha=0.85, edgecolor='red')
        )

    # formato gráfico
    ax.set_xlim(0,100)
    ax.set_ylim(0,100)
    ax.set_xlabel("Smin (ksi)")
    ax.set_ylabel("Smax (ksi)")
    ax.set_title("Diagrama de Goodman Corrosión-Fatiga", fontstyle="italic")

    ax.legend()
    ax.grid(alpha=0.3)

    st.pyplot(fig)

# ======================
# RESULTADOS
# ======================
goodman_pct = ((smax_user - smin_user)/(sadm_user - smin_user))*100

st.markdown('<div class="subtitulo">Resultados</div>', unsafe_allow_html=True)

c1,c2,c3,c4 = st.columns(4)
c1.metric("FS", f"{fs_sel:.3f}")
c2.metric("Factor base", f"{f_base:.3f}")
c3.metric("Sadm", f"{sadm_user:.1f}")
c4.metric("%Goodman", f"{goodman_pct:.1f}")

# ======================
# FOOTER
# ======================
st.markdown("---")
st.markdown('<div class="cursiva">Modelo basado en Goodman y corrosión-fatiga</div>', unsafe_allow_html=True)



