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

st.markdown('<div class="titulo">Selector de varillas 🛠️</div>', unsafe_allow_html=True)
st.markdown('<div class="cursiva">Según Criterio de Goodman + Corrosión-Fatiga</div>', unsafe_allow_html=True)
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
    return 1 if ppm < 6000 else 1 - (0.00007 * (ppm**0.8))

# ======================
# FUNCIONES
# ======================
def FS_material(mat,f):
    if f==1: return 1
    if mat=="DA78": return f*0.90
    elif mat=="HS97": return f*0.92
    elif mat=="CS propietario": return f*0.92
    elif mat=="HS propietario": return f*0.75
    elif mat=="D New": return f*0.90
    elif mat=="DSK75": return f if f < 0.75 else 1
    elif mat=="HA96": return f*0.85

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
    smin_user = st.slider("Smin (ksi)",0,100,30)
    smax_user = st.slider("Smax (ksi)",0,100,50)

# ======================
# FACTOR BASE
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

        sadm = goodman(smin_user, materiales[mat]["uts_a"], materiales[mat]["b"], fs)
        margen = sadm - smax_user

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

    ax.scatter(smin_user, smax_user,
               color="red", s=90,
               label="Punto crítico de sarta")

    if smax_user > sadm_user:
        ax.text(
            0.5, 0.15,
            "Seleccione otro tipo de varilla\n"
            "o utilice revestimiento + tratamiento químico",
            transform=ax.transAxes,
            fontsize=10,
            color="red",
            ha="center",
            bbox=dict(facecolor='white', alpha=0.85)
        )

    ax.set_xlim(0,100)
    ax.set_ylim(0,100)
    ax.set_xlabel("Smin (ksi)")
    ax.set_ylabel("Smax (ksi)")
    ax.set_title("Diagrama de Goodman Corrosión-Fatiga", fontstyle='italic')

    ax.legend()
    st.pyplot(fig)

# ======================
# RESTO FUERA (CORREGIDO)
# ======================
df = pd.DataFrame(ranking)
df = df.sort_values(by="Margen", ascending=False).reset_index(drop=True)

if abs(f_base - 1.0) < 1e-6:
    if "HS97" in df["Material"].values:
        fila = df[df["Material"]=="HS97"]
        df = df[df["Material"]!="HS97"]
        df = pd.concat([fila,df]).reset_index(drop=True)

df["%Goodman"] = ((smax_user - smin_user) / (df["Sadm"] - smin_user)) * 100

st.markdown('<div class="subtitulo">Ranking de Varillas Seleccionadas</div>', unsafe_allow_html=True)

col_tabla, _ = st.columns([3,7])

with col_tabla:
    st.dataframe(df.drop(columns=["FS"]), use_container_width=True)

# ======================
# RESULTADOS
# ======================
goodman_pct = ((smax_user - smin_user)/(sadm_user - smin_user))*100

st.markdown('<div class="subtitulo">Resultados</div>', unsafe_allow_html=True)

col1,col2,col3,col4=st.columns(4)

col1.metric("FS",f"{fs_sel:.1f}")
col2.metric("Factor base",f"{f_base:.1f}")
col3.metric("Sadm",f"{sadm_user:.1f}")
col4.metric("%Goodman",f"{goodman_pct:.1f}")

# ======================
# RECOMENDACION (ARREGLADA)
# ======================
st.markdown('<div class="subtitulo">Recomendación</div>', unsafe_allow_html=True)

col_rec, _ = st.columns([4,6])

with col_rec:
    validos = df[df["Margen"] >= 0]

    if len(validos) > 0:

        top = validos.head(3)

        for i, row in top.iterrows():
            st.markdown(f"""
            <div style="
                background-color:#D8E5DF;
                padding:6px 12px;
                margin-bottom:6px;
                border-radius:6px;
                color:#0B6E4F;
                font-weight:500;
            ">
                {top.index.get_loc(i)+1}. {row['Material']}
            </div>
            """, unsafe_allow_html=True)

    else:
        st.error("Requiere tratamiento químico y/o varillas revestidas")

# ======================
# FOOTER
# ======================
st.markdown("---")
st.markdown('<div class="cursiva">Modelo basado en Criterio de Goodman y corrosión-fatiga</div>', unsafe_allow_html=True)
st.markdown('<div class="cursiva">Desarrollado por Fcam. SP-Brazil May-26</div>', unsafe_allow_html=True)
