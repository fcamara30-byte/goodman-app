import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Image, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import tempfile
import os

st.set_page_config(layout="wide")

# ======================
# ESTILO
# ======================
st.markdown("""
<style>
.titulo {font-size:26px; font-weight:700; color:#0B3C8C;}
.subtitulo {font-size:17px; font-weight:600; color:#1F4E79; margin-top:12px;}
.box {background:#F4F6F8; padding:12px; border-radius:10px;}
.cursiva {font-style: italic; color:#444;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="titulo">Selector de varillas 🛠️</div>', unsafe_allow_html=True)
st.markdown('<div class="cursiva">Criterio basado en Goodman y Corrosión-Fatiga</div>', unsafe_allow_html=True)

# ======================
# MATERIALES
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

BSR={"0":1,"1":1,"2":0.95,"3":0.9,"4":0.82,"5":0.74,"6":0.65}

# ======================
# FACTORES
# ======================
def factor_co2(sel):
    if sel == "Nada (0 psi)": return 1.00
    if sel == "Bajo (0–20 psi)": return 0.98
    if sel == "Medio (21–100 psi)": return 0.90
    if sel == "Alto (>100 psi)": return 0.80

def factor_h2s(sel):
    if sel == "Nada (0 psi)": return 1.00
    if sel == "Bajo (0–1 psi)": return 0.95
    if sel == "Medio (1–2 psi)": return 0.80
    if sel == "Alto (>2 psi)": return 0.75

def factor_cloruros(ppm):
    return 1 if ppm < 9000 else 1-(0.000019*(ppm**0.8))

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

def goodman(smin,uts,b,fs):
    return (uts+b*smin)*fs

# ======================
# LAYOUT
# ======================
l,r = st.columns([1,2])

# ======================
# INPUTS
# ======================
with l:
    st.markdown('<div class="subtitulo">Entradas</div>', unsafe_allow_html=True)

    a,b=l.columns(2)
    material=a.selectbox("Material",list(materiales.keys()))

    ppco2_sel=b.selectbox("PPCO₂ (psi)", [
        "Nada (0 psi)",
        "Bajo (0–20 psi)",
        "Medio (21–100 psi)",
        "Alto (>100 psi)"
    ])

    c,d=l.columns(2)
    pph2s_sel=c.selectbox("PPH₂S (psi)", [
        "Nada (0 psi)",
        "Bajo (0–1 psi)",
        "Medio (1–2 psi)",
        "Alto (>2 psi)"
    ])

    bsr=d.selectbox("BSR", list(BSR.keys()))

    cl_ppm=st.number_input("Cloruros (ppm)",0,200000,0)

    smin_user=st.slider("Smin (ksi)",0,150,30)
    smax_user=st.slider("Smax (ksi)",0,150,50)

# ======================
# FACTOR BASE
# ======================
f_co2 = factor_co2(ppco2_sel)
f_h2s = factor_h2s(pph2s_sel)

f_base = f_co2 * f_h2s * BSR[bsr] * factor_cloruros(cl_ppm)

smin=np.linspace(0,150,200)

# ======================
# GRÁFICO
# ======================
with r:

    fig,ax=plt.subplots(figsize=(7,4))
    ranking=[]

    for mat in materiales:
        fs=FS_material(mat,f_base)

        y=goodman(smin,materiales[mat]["uts_a"],materiales[mat]["b"],fs)
        sadm=goodman(smin_user,materiales[mat]["uts_a"],materiales[mat]["b"],fs)
        margen=sadm-smax_user

        ranking.append({"Material":mat,"FS":fs,"Sadm":sadm,"Margen":margen})

        if mat==material:
            ax.plot(smin,y,color='blue',linewidth=3)
        else:
            ax.plot(smin,y,color='gray',alpha=0.15)

    ax.plot(smin,smin,'k-',linewidth=2)

    ax.scatter(
        smin_user,
        smax_user,
        color="red",
        s=80,
        label="Punto crítico de sarta"
    )

    ax.set_xlim(smin_user*0.7,150)
    ax.set_ylim(smax_user*0.7,150)

    ax.set_xlabel("Smin (ksi)")
    ax.set_ylabel("Smax (ksi)")

    ax.set_title(
        "Diagrama de Goodman Fatiga–Corrosión por Varilla",
        fontstyle='italic'
    )

    ax.grid(alpha=0.3)
    ax.legend()

    plt.tight_layout()
    st.pyplot(fig)

    # ======================
    # RANKING
    # ======================
    df=pd.DataFrame(ranking)
    df=df.sort_values(by="Margen",ascending=False).reset_index(drop=True)

    # ✅ REGLA HS97
    if f_base >= 0.999:   # sin corrosión
        if "HS97" in df["Material"].values:
            fila=df[df["Material"]=="HS97"]
            df=df[df["Material"]!="HS97"]
            df=pd.concat([fila,df]).reset_index(drop=True)

    df["%Goodman"]=((smax_user-smin_user)/(df["Sadm"]-smin_user))*100

    st.markdown('<div class="subtitulo">Ranking de Varillas</div>', unsafe_allow_html=True)

    st.dataframe(df.style.format({
        "FS":"{:.3f}",
        "Sadm":"{:.1f}",
        "Margen":"{:.1f}",
        "%Goodman":"{:.1f}"
    }),use_container_width=True)

    # ======================
    # RESULTADOS
    # ======================
    fs_sel=FS_material(material,f_base)
    sadm_user=goodman(smin_user,materiales[material]["uts_a"],materiales[material]["b"],fs_sel)
    goodman_pct=((smax_user-smin_user)/(sadm_user-smin_user))*100

    st.markdown('<div class="subtitulo">Resultados</div>', unsafe_allow_html=True)
    st.markdown('<div class="box">', unsafe_allow_html=True)

    c1,c2,c3,c4=st.columns(4)
    c1.metric("FS",f"{fs_sel:.3f}")
    c2.metric("Factor",f"{f_base:.3f}")
    c3.metric("Sadm",f"{sadm_user:.1f} ksi")
    c4.metric("Goodman",f"{goodman_pct:.1f}%")

    st.markdown('</div>',unsafe_allow_html=True)

    # ======================
    # RECOMENDACIÓN
    # ======================
    st.markdown('<div class="subtitulo">Recomendación</div>', unsafe_allow_html=True)

    validos = df[df["Margen"] >= 0]

    if len(validos) > 0:
        st.success(f"Material recomendado: {validos.iloc[0]['Material']}")
    else:
        st.error("Aplicar varillas revestidas y/o tratamiento químico")

# ======================
# FOOTER
# ======================
st.markdown("---")
st.markdown(
    '<div class="cursiva">Modelo basado en APIRP11L, corrosión-fatiga y experiencia de campo</div>',
    unsafe_allow_html=True
)
