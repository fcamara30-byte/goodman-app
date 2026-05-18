import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

st.set_page_config(layout="wide")

# ======================
# CONTADOR
# ======================
archivo_contador = "visitas.txt"

if os.path.exists(archivo_contador):
    with open(archivo_contador, "r") as f:
        try:
            visitas = int(f.read())
        except:
            visitas = 0
else:
    visitas = 0

visitas += 1

with open(archivo_contador, "w") as f:
    f.write(str(visitas))

st.markdown(f"""
<div style="font-size:13px; color:gray;">
Visitas totais: <b>{visitas}</b>
</div>
""", unsafe_allow_html=True)

# ======================
# TITULO
# ======================
col_title, col_img = st.columns([5,1])

with col_title:
    st.title("Cálculo de Solicitações SRP Corrosão-Fadiga")

with col_img:
    st.markdown("<div style='font-size:60px; text-align:center;'>⚙️</div>", unsafe_allow_html=True)

# ======================
# INPUTS
# ======================
c1,c2,c3,c4=st.columns(4)

L_m=c1.number_input("Comprimento do poço (m)",500,5000,1800)
G=c2.slider("Gravidade específica",0.6,1.2,0.95)
D=c3.selectbox("Bomba (in)",[1.5,1.75,2,2.25,2.5])
N=c4.slider("SPM",1,20,6)

c_slider,_=st.columns([2,3])

with c_slider:
    S=st.slider("Curso (in)",0,300,168)

# ======================
# MATERIALES
# ======================
materiales={
    "DA78":{"uts_a":30,"b":0.5625},
    "HS97":{"uts_a":50,"b":0.375},
    "CS":{"uts_a":44.64,"b":0.375},
    "HS":{"uts_a":55.36,"b":0.375},
    "DSK75":{"uts_a":42.86,"b":0.375},
    "HA96":{"uts_a":50,"b":0.375},
    "D New":{"uts_a":42.86,"b":0.375}
}

st.subheader("Material por trecho")

col1,col2,col3,_=st.columns([1,1,1,2])

sel1=col1.selectbox('1"',materiales.keys())
sel78=col2.selectbox('7/8"',materiales.keys())
sel34=col3.selectbox('3/4"',materiales.keys())

rod_sel={"1":sel1,"7/8":sel78,"3/4":sel34}

# ======================
# FACTOR
# ======================
CO2={"Nada":1,"Bajo":0.98,"Medio":0.9,"Alto":0.8}
H2S={"Nada":1,"Bajo":0.93,"Medio":0.8,"Alto":0.75}
BSR={"0":1,"1":1,"2":0.95,"3":0.9,"4":0.82,"5":0.74}

col1,col2,col3,col4,_=st.columns([1,1,1,1,2])

co2=col1.selectbox("CO₂",CO2)
h2s=col2.selectbox("H₂S",H2S)
bsr=col3.selectbox("BSR",BSR)
cl=col4.number_input("Cloretos (ppm)",0,250000,0)

def f_cl(ppm):
    return 1 if ppm<6000 else 1-(0.00007*(ppm**0.8))

f_base=CO2[co2]*H2S[h2s]*BSR[bsr]*f_cl(cl)

def FS_material(mat,f):
    return f

# ======================
# CALCULO RESULTADOS
# ======================
pct={"1":0.33,"7/8":0.33,"3/4":0.34}

rows=[]

for d in pct:
    Smin=20+np.random.rand()*10
    Smax=40+np.random.rand()*10

    mat=rod_sel[d]

    Sadm=materiales[mat]["uts_a"]*f_base

    Gval=(Smax-Smin)/(Sadm-Smin)*100

    rows.append({
        "Tramo":d,
        "Material":mat,
        "Smax (ksi)":round(Smax,1),
        "Smin (ksi)":round(Smin,1),
        "Goodman (%)":int(Gval)
    })

df=pd.DataFrame(rows)

# ======================
# TABLAS
# ======================
col_tabla, col_der = st.columns([2,1])

with col_tabla:
    st.subheader("Ranking de hastes")
    df_sorted=df.sort_values(by="Goodman (%)")
    st.dataframe(df_sorted)

with col_der:
    st.subheader("Resultados")
    st.metric("Max Goodman",f"{df['Goodman (%)'].max()} %")
    st.metric("Min Goodman",f"{df['Goodman (%)'].min()} %")

# ======================
# GOODMAN
# ======================
st.subheader("Diagrama de Goodman")

x=np.linspace(0,100,200)

fig,ax=plt.subplots()

curvas=[]

for d in pct:
    mat=rod_sel[d]
    y=materiales[mat]["uts_a"]*f_base + materiales[mat]["b"]*x
    curvas.append(y)
    ax.plot(x,y)

y_safe=np.minimum.reduce(curvas)

