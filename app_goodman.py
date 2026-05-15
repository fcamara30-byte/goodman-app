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
# ESTILO LIMPIO
# ======================
st.markdown("""
<style>
.titulo {font-size:22px; font-weight:600; color:#0B3C8C;}
.subtitulo {font-size:16px; font-weight:600; color:#1F4E79; margin-top:10px;}
.box {background:#F4F6F8; padding:10px; border-radius:8px;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="titulo">Selector de varillas de acuerdo a criterio Goodman y Corrosión-Fatiga</div>', unsafe_allow_html=True)

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

def factor_cloruros(ppm):
    return 1 if ppm < 9000 else 1-(0.000019*(ppm**0.8))

# ======================
# CLASIFICACIÓN POR PSI
# ======================
def clasificar_co2(pp):
    if pp == 0:
        return "Nada", 1.00
    elif pp <= 20:
        return "Bajo", 0.98
    elif pp <= 100:
        return "Medio", 0.90
    else:
        return "Alto", 0.80

def clasificar_h2s(pp):
    if pp == 0:
        return "Nada", 1.00
    elif pp <= 1:
        return "Bajo", 0.95
    elif pp <= 2:
        return "Medio", 0.80
    else:
        return "Alto", 0.75

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
    st.markdown('<div class="subtitulo">Inputs</div>', unsafe_allow_html=True)

    a,b=l.columns(2)
    material=a.selectbox("Material",list(materiales.keys()))
    ppco2=b.number_input("PPCO₂ (psi)",0.0,2000.0,0.0)

    c,d=l.columns(2)
    pph2s=c.number_input("PPH₂S (psi)",0.0,50.0,0.0)
    bsr=d.selectbox("BSR (caldos positivos)",list(BSR.keys()))

    cl_ppm=st.number_input("Cloruros (ppm)",0,200000,0)

    smin_user=st.slider("Smin (ksi)",0,150,30)
    smax_user=st.slider("Smax (ksi)",0,150,50)

# ======================
# FACTORES
# ======================
nivel_co2, f_co2 = clasificar_co2(ppco2)
nivel_h2s, f_h2s = clasificar_h2s(pph2s)

f_base = f_co2 * f_h2s * BSR[bsr] * factor_cloruros(cl_ppm)

smin=np.linspace(0,150,200)

# ======================
# GRAFICO + DATOS
# ======================
with r:

    fig,ax=plt.subplots(figsize=(7,3.8))
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
            ax.plot(smin,y,color='gray',alpha=0.2)

    ax.plot(smin,smin,'k--')
    ax.scatter(smin_user,smax_user,color="red",s=60)
    ax.set_xlim(0,150)
    ax.set_ylim(0,150)
    ax.set_xlabel("Smin (ksi)")
    ax.set_ylabel("Smax (ksi)")
    ax.grid()
    plt.tight_layout()
    st.pyplot(fig)

    df=pd.DataFrame(ranking)

    df=df.sort_values(by="Margen",ascending=False).reset_index(drop=True)

    df["%Goodman"]=((smax_user-smin_user)/(df["Sadm"]-smin_user))*100

    st.markdown('<div class="subtitulo">Ranking de Varillas sugeridas</div>', unsafe_allow_html=True)

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
    goodman_pct=((smax_user-smin_user)/(sadm_user-smin_user))*100 if sadm_user!=smin_user else 0

    st.markdown('<div class="subtitulo">Resultados</div>', unsafe_allow_html=True)
    st.markdown('<div class="box">', unsafe_allow_html=True)

    c1,c2,c3,c4=st.columns(4)
    c1.metric("FS",f"{fs_sel:.3f}")
    c2.metric("Factor base",f"{f_base:.3f}")
    c3.metric("Sadm (ksi)",f"{sadm_user:.1f}")
    c4.metric("%Goodman",f"{goodman_pct:.1f}")

    st.markdown('</div>',unsafe_allow_html=True)

    # ======================
    # RECOMENDACION
    # ======================
    st.markdown('<div class="subtitulo">Recomendación</div>', unsafe_allow_html=True)

    validos = df[df["Margen"] >= 0]

    if len(validos) > 0:
        mejor = validos.iloc[0]["Material"]

