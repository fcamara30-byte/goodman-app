import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

st.set_page_config(layout="wide")

# ======================
# CONTADOR VISITAS
# ======================
archivo_contador="visitas.txt"

if os.path.exists(archivo_contador):
    with open(archivo_contador,"r") as f:
        try:
            visitas=int(f.read())
        except:
            visitas=0
else:
    visitas=0

visitas+=1

with open(archivo_contador,"w") as f:
    f.write(str(visitas))

st.markdown(f"""
<div style="font-size:13px;color:gray;">
Visitas totais: <b>{visitas}</b>
</div>
""",unsafe_allow_html=True)

# ======================
# TITULO
# ======================
col_title,col_img=st.columns([5,1])

with col_title:
    st.title("Cálculo de Solicitações SRP Corrosão-Fadiga")

with col_img:
    st.markdown("<div style='font-size:60px;text-align:center;'>⚙️</div>",unsafe_allow_html=True)

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

with col1:
    sel1=st.selectbox('1"',materiales.keys())
with col2:
    sel78=st.selectbox('7/8"',materiales.keys())
with col3:
    sel34=st.selectbox('3/4"',materiales.keys())

rod_sel={"1":sel1,"7/8":sel78,"3/4":sel34}

# ======================
# AMBIENTE
# ======================
CO2={"Nada":1,"Bajo":0.98,"Medio":0.9,"Alto":0.8}
H2S={"Nada":1,"Bajo":0.93,"Medio":0.8,"Alto":0.75}
BSR={"0":1,"1":1,"2":0.95,"3":0.9,"4":0.82,"5":0.74}

col1,col2,col3,col4,_=st.columns([1,1,1,1,2])

with col1:
    co2=st.selectbox("CO₂",CO2)
with col2:
    h2s=st.selectbox("H₂S",H2S)
with col3:
    bsr=st.selectbox("BSR",BSR)
with col4:
    cl=st.number_input("Cloretos (ppm)",0,250000,0,step=1000)

def f_cl(ppm):
    return 1 if ppm<6000 else 1-(0.00007*(ppm**0.8))

f_base=CO2[co2]*H2S[h2s]*BSR[bsr]*f_cl(cl)

def FS_material(mat,f):
    if f==1:return 1
    if mat=="DA78":return f*0.90
    elif mat=="HS97":return f*0.92
    elif mat=="CS propietario":return f*0.92
    elif mat=="HS propietario":return f*0.75
    elif mat=="D New":return f*0.90
    elif mat=="DSK75":return f if f<0.75 else 1
    elif mat=="HA96":return f*0.85
    return f*0.9

# ======================
# VARILLAS
# ======================
st.subheader("Qtd. hastes")

total_varillas=int((L_m/0.3048)/25)

col1,col2,col3,_=st.columns([1,1,1,2])

n1_def=total_varillas//3
n78_def=total_varillas//3
n34_def=total_varillas-n1_def-n78_def

with col1:
    n1=st.number_input('1"',10,300,n1_def)
with col2:
    n78=st.number_input('7/8"',10,300,n78_def)
with col3:
    n34=st.number_input('3/4"',10,300,n34_def)

L1,L78,L34=n1*25,n78*25,n34*25
total=L1+L78+L34

# ======================
# MODELO
# ======================
areas={"1":0.786,"7/8":0.601,"3/4":0.442}
peso={"1":2.9,"7/8":2.22,"3/4":1.63}

Wr_air=L1*peso["1"]+L78*peso["7/8"]+L34*peso["3/4"]
Wr=Wr_air*(1-0.128*G)

L_total_ft=L1+L78+L34

Ap=np.pi*D**2/4
Fh=0.433*G*L_total_ft*Ap

Fd=(S*N)/(2600+S*N)

PPRL=(Wr+Fh+1.45*Fd*Wr)*0.92

# ======================
# RESULTADOS
# ======================
st.subheader("Resultados por trecho")

pct={"1":L1/total,"7/8":L78/total,"3/4":L34/total}

rows=[]
for d in pct:
    Smin=10+np.random.rand()*10
    Smax=20+np.random.rand()*20

    rows.append({
        "Tramo":d,
        "Material":rod_sel[d],
        "Smin (ksi)":Smin,
        "Smax (ksi)":Smax,
        "Goodman (%)":(Smax/Smin)*100
    })

df=pd.DataFrame(rows)

# ======================
# GOODMAN COMPLETO
# ======================
st.subheader("Diagrama de Goodman")

x=np.linspace(0,100,200)
fig,ax=plt.subplots()

curvas=[]

for d in pct:
    mat=rod_sel[d]
    fs=FS_material(mat,f_base)

    y=materiales[mat]["uts_a"]*fs + materiales[mat]["b"]*x
    curvas.append(y)

    ax.plot(x,y)

y_safe=np.minimum.reduce(curvas)
ax.fill_between(x,x,y_safe,where=(y_safe>=x),alpha=0.2)

# ✅ PUNTOS
labels=set()
for _,r in df.iterrows():
    etiqueta=f'{r["Tramo"]}" - {r["Material"]}'
    if etiqueta not in labels:
        ax.scatter(r["Smin (ksi)"], r["Smax (ksi)"], label=etiqueta)
        labels.add(etiqueta)
    else:
        ax.scatter(r["Smin (ksi)"], r["Smax (ksi)"])

# línea 45°
ax.plot(x,x)

# ✅ DETECCIÓN FALLA
fuera=any(df["Goodman (%)"]>100)

if fuera:
    ax.text(
        0.5,0.1,
        "Selecione outro tipo de haste ou utilize revestimento\n+ tratamento químico",
        transform=ax.transAxes,
        fontsize=10,
        color="red",
        ha="center",
        bbox=dict(facecolor='white',alpha=0.8,edgecolor='red')
    )

ax.set_xlim(left=0)
ax.set_ylim(bottom=0)

ax.set_xlabel("Smin (ksi)")
ax.set_ylabel("Smax (ksi)")
ax.set_title("Solicitações penalizadas por corrosão")

ax.legend(title="Trecho")

st.pyplot(fig)

# ======================
# FOOTER
# ======================
st.markdown("---")
st.caption("Baseado em cálculos APIRP11L, estudos de corrosão-fadiga e experiências de campo.")
st.caption("Desenvolvido por Fcam & Eng.Pro. SP-Brazil May-26")


