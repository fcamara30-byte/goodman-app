import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os

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

st.set_page_config(layout="wide")

# ======================
# ESTILO
# ======================
st.markdown("""
<style>
.titulo {font-size:43px; font-weight:700; color:#0B3C8C;}
.subtitulo {font-size:17px; font-weight:600; color:#1F4E79;}
.cursiva {font-style: italic; color:#444;}
</style>
""", unsafe_allow_html=True)
st.markdown("""
<style>
[data-testid="stDataFrame"] div {
    font-size: 12px;
}

[data-testid="stDataFrame"] th, 
[data-testid="stDataFrame"] td {
    padding: 4px 6px;
    max-width: 80px;
    white-space: nowrap;
}

[data-testid="stDataFrame"] {
    width: fit-content;
}
</style>
""", unsafe_allow_html=True)

col1, col2 = st.columns([4,1])

with col1:
    st.markdown('<div class="titulo">Selector de varillas 🌎</div>', unsafe_allow_html=True)




st.markdown('<div class="cursiva">Según Criterio de Goodman + Corrosión-Fatiga</div>', unsafe_allow_html=True)
st.caption(f"Visitas totales: {visitas}")

# ======================
# DATOS
# ======================
materiales = {
    "DA78":{"uts_a":42.86,"b":0.375},
    "HS97":{"uts_a":50,"b":0.375},
    "CS propietario":{"uts_a":44.64,"b":0.375},
    "HS propietario":{"uts_a":55.36,"b":0.375},
    "D New":{"uts_a":42.86,"b":0.375},
    "DSX75":{"uts_a":42.86,"b":0.375},
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
    return 1 if ppm < 6000 else (-2e-16)*(ppm**3) + (7e-11)*(ppm**2) - (9e-6)*ppm + 1.0704

# ======================
# FUNCIONES
# ======================
def FS_material(mat,f):
    if f==1: return 1
    if mat=="DA78": return f*0.90
    elif mat=="HS97": return f*0.91
    elif mat=="CS propietario": return f*0.93
    elif mat=="HS propietario": return f*0.75
    elif mat=="D New": return f*0.90
    elif mat=="DSX75": return f if f < 0.73 else 1
    elif mat=="HA96": return f*0.8

def goodman(x,uts,b,fs):
    return (uts + b*x) * fs

# ======================
# INPUTS
# ======================
l,r = st.columns([1,2])

with l:
    material = st.selectbox("Material", list(materiales.keys()))
    co2 = st.selectbox("PPCO₂ (psi)", [
        "Nada (0 psi)", "Bajo (0–20 psi)",
        "Medio (21–100 psi)", "Alto (>100 psi)"
    ])
    h2s = st.selectbox("PPH₂S (psi)", [
        "Nada (0 psi)", "Bajo (0–1 psi)",
        "Medio (1–2 psi)", "Alto (>2 psi)"
    ])
    bsr = st.selectbox("BSR-caldos+", list(BSR.keys()))
    cl_ppm = st.number_input("Cloruros (ppm)",0,200000,0, step=1000)

    st.markdown('<div class="subtitulo">Selector de Solicitaciones Máximas y Mínimas</div>', unsafe_allow_html=True)


st.subheader("Selector de Cargas y Diámetro")

col_d, col_min, col_max = st.columns(3)

with col_d:
    diam = st.selectbox("Diámetro (in)", ["1", "7/8", "3/4"])

with col_min:
    Pmin_input = float(st.text_input("Carga mínima (lb)", value="2000"))

with col_max:
    Pmax_input = float(st.text_input("Carga máxima (lb)", value="10000"))

# áreas
areas = {
    "1": 0.786,
    "7/8": 0.601,
    "3/4": 0.442
}

A = areas[diam]

# ✅ calcular tensiones
Smax = Pmax_input / A / 1000
Smin = Pmin_input / A / 1000

# ======================
# BASE
# ======================
f_base = factor_co2(co2)*factor_h2s(h2s)*BSR[bsr]*factor_cloruros(cl_ppm)
x = np.linspace(0,100,200)

# ======================
# GRAFICO
# ======================
with r:
    fig, ax = plt.subplots(figsize=(6,4))
    ranking=[]

    for mat in materiales:
        fs = FS_material(mat,f_base)
        y = goodman(x, materiales[mat]["uts_a"], materiales[mat]["b"], fs)

        sadm = goodman(Smin, materiales[mat]["uts_a"], materiales[mat]["b"], fs)
        margen = sadm - Smax

        ranking.append({"Material":mat,"FS":fs,"Sadm":sadm,"Margen":margen})

        if mat == material:
            y_sel = y
            fs_sel = fs
            sadm_user = sadm

    diff = y_sel - x
    idx = np.where(diff <= 0)[0]
    corte = idx[0] if len(idx)>0 else len(x)

    x_clip = x[:corte]
    y_clip = y_sel[:corte]

    ax.plot(x_clip, y_clip, "b", linewidth=3)
    ax.plot(x, x, "k", linewidth=2)

    ax.fill_between(x_clip, x_clip, y_clip,
                    where=(y_clip>=x_clip),
                    color='green', alpha=0.15)

    ax.scatter(Smin, Smax, color="red", s=90)

    if Smax > sadm_user:
        ax.text(
            0.5,0.15,
            "Seleccione otro tipo de varilla\n"
            "o utilice revestimiento + tratamiento químico",
            transform=ax.transAxes,
            fontsize=10,
            color="red",
            ha="center",
            bbox=dict(facecolor='white', alpha=0.85)
        )

    # ✅ CAMBIO ÚNICO: eje Y pasa por origen
    ax.spines['left'].set_position(('data', 0))

    ax.set_xlim(0,100)
    ax.set_ylim(0,100)
    ax.set_xlabel("Smin (ksi)")
    ax.set_ylabel("Smax (ksi)")
    ax.set_title("Diagrama de Goodman Corrosión-Fatiga")

    st.pyplot(fig)

# ======================
# DATA
# ======================
df = pd.DataFrame(ranking)
df = df.sort_values(by="Margen", ascending=False).reset_index(drop=True)

if abs(f_base - 1.0) < 1e-6:
    if "HS97" in df["Material"].values:
        fila = df[df["Material"]=="HS97"]
        df = df[df["Material"]!="HS97"]
        df = pd.concat([fila, df]).reset_index(drop=True)


df["%Goodman"] = ((Smax - Smin) /
(df["Sadm"] - Smin)) * 100


col_tabla, col_der = st.columns([2.7,1.8])

with col_tabla:
    st.markdown('<div class="subtitulo">Ranking de Varillas Seleccionadas</div>', unsafe_allow_html=True)
    st.dataframe(df.drop(columns=["FS"]).style.format({
        "Sadm":"{:.0f}",
        "Margen":"{:.0f}",
        "%Goodman":"{:.0f}"
    }), use_container_width=False)

with col_der:
    st.markdown('<div class="subtitulo">Resultados</div>', unsafe_allow_html=True)

    c1,c2 = st.columns(2)
    c3,c4 = st.columns(2)

    c1.metric("FS", f"{fs_sel:.1f}")
    c2.metric("Factor base", f"{f_base:.1f}")
    c3.metric("Sadm", f"{sadm_user:.1f}")
    c4.metric("%Goodman", f"{((Smax - Smin) / (sadm_user - Smin) * 100):.1f}")

    st.markdown('<div class="subtitulo">Recomendación</div>', unsafe_allow_html=True)

    validos = df[df["Margen"] >= 0]
    for i,row in validos.head(3).iterrows():
        st.markdown(f"{i+1}. {row['Material']}")

st.markdown("---")
st.markdown('<div class="cursiva">Modelo basado en Criterio de Goodman y corrosión-fatiga</div>', unsafe_allow_html=True)
st.markdown('<div class="cursiva">Desarrollado por Fcam & Eng.Pro. SP-Brazil May-26</div>', unsafe_allow_html=True)
