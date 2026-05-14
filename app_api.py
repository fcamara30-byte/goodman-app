import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("Calculo de Solicitaciones (Versión Beta)")

# ======================
# INPUTS
# ======================
c1,c2=st.columns(2)

with c1:
    L_m=st.number_input("Profundidad objetivo (m)",500,5000,1800)
    G=st.slider("Gravedad específica",0.6,1.2,0.95)

with c2:
    D=st.selectbox("Bomba (in)",[1.5,1.75,2,2.25,2.5])
    S=st.slider("Carrera (in)",50,200,168)
    N=st.slider("SPM",1,20,6)

# ======================
# MATERIALES
# ======================
materiales={
    "DA78":{"uts_a":30,"b":0.5625},
    "HS97":{"uts_a":50,"b":0.375},
    "CS propietario":{"uts_a":44.64,"b":0.375},
    "HS propietario":{"uts_a":55.36,"b":0.375},
    "D New":{"uts_a":42.86,"b":0.375},
    "DSK75":{"uts_a":42.86,"b":0.375},
    "HA96":{"uts_a":50,"b":0.375}
}

# ======================
# CORROSION
# ======================
CO2={"Nada":1,"Bajo":1,"Medio":0.9,"Alto":0.8}
H2S={"Nada":1,"Bajo":0.95,"Medio":0.8,"Alto":0.75}
BSR={"0":1,"1":1,"2":0.95,"3":0.9,"4":0.82,"5":0.74,"6":0.65}

def factor_cloruros(ppm):
    return 1 if ppm<9000 else 1-(0.000019*(ppm**0.8))

def FS_material(mat,f):
    if f==1: return 1
    if mat=="DA78": return f*0.95
    if mat=="HS97": return f
    if mat=="CS propietario": return f*0.96
    if mat=="HS propietario": return f*0.80
    if mat=="D New": return f*0.94
    if mat=="DSK75": return f if f<0.83 else 1
    if mat=="HA96": return f*0.93

def goodman_corr(smin,uts,b,fs):
    return (uts+b*smin)*fs

# ======================
# MATERIAL POR TRAMO
# ======================
st.subheader("Material por tramo")

col1,col2,col3=st.columns(3)

rod_sel={
    "1":col1.selectbox('1"',materiales.keys()),
    "7/8":col2.selectbox('7/8"',materiales.keys()),
    "3/4":col3.selectbox('3/4"',materiales.keys())
}

# ======================
# AMBIENTE
# ======================
st.subheader("Ambiente")

c1,c2,c3,c4=st.columns(4)

co2=c1.selectbox("CO2",CO2.keys())
h2s=c2.selectbox("H2S",H2S.keys())
bsr=c3.selectbox("BSR",BSR.keys())
cl=c4.number_input("Cloruros ppm",0,200000,0)

f_base=CO2[co2]*H2S[h2s]*BSR[bsr]*factor_cloruros(cl)

st.write("Factor de servicio:", round(f_base,3))

# ======================
# VARILLAS COMPACTO
# ======================
st.subheader("Varillas")

df=pd.DataFrame({
    "Diámetro":["1","7/8","3/4"],
    "Varillas":[80,80,80]
})

df=st.data_editor(df,use_container_width=True,height=120).reset_index(drop=True)

L1=float(df.loc[0,"Varillas"])*25
L78=float(df.loc[1,"Varillas"])*25
L34=float(df.loc[2,"Varillas"])*25

total=L1+L78+L34
if total==0: st.stop()

# 🔥 longitud real ahora depende de varillas
L_ft=total

st.write(f"Longitud real del pozo: {round(L_ft*0.3048,1)} m")

# ======================
# PROPIEDADES
# ======================
areas={"1":0.786,"7/8":0.601,"3/4":0.442}
peso={"1":2.90,"7/8":2.22,"3/4":1.63}

# ======================
# API
# ======================
A=np.pi*D**2/4
Fo=0.433*G*L_ft*A

No=1800/np.sqrt(L_ft)
Nr=N/No

Fi=Fo*(1+0.3*Nr)
F2=Fo*(0.3*Nr)

W_total=L_ft*2.3
Wri=W_total*(1-0.128*G)

PPRL=Wri+Fi
MPRL=Wri-F2

# ======================
# DISTRIBUCION
# ======================
pct={"1":L1/total,"7/8":L78/total,"3/4":L34/total}

W1=pct["1"]*L_ft*peso["1"]
W78=pct["7/8"]*L_ft*peso["7/8"]

W_up={"1":0,"7/8":W1,"3/4":W1+W78}

# ======================
# CALCULO
# ======================
res={}

for d in pct:

    mat=rod_sel[d]
    uts=materiales[mat]["uts_a"]
    b=materiales[mat]["b"]

    fs_mat=FS_material(mat,f_base)

    Pmax=PPRL-W_up[d]
    Pmin=max(MPRL-0.6*W_up[d],0)

    Smax=Pmax/areas[d]/1000
    Smin=Pmin/areas[d]/1000

    Sadm=goodman_corr(Smin,uts,b,fs_mat)

    G=((Smax-Smin)/(Sadm-Smin))*100

    res[d]={
        "Material":mat,
        "Smin":Smin,
        "Smax":Smax,
        "Sadm":Sadm,
        "Goodman":G
    }

# ======================
# RESULTADOS
# ======================
st.subheader("Resultados")

df_res=pd.DataFrame(res).T.round(1)

st.dataframe(
    df_res.style
    .set_properties(**{'text-align':'center'})
    .applymap(lambda v:'font-weight:bold' if isinstance(v,(int,float)) else ''),
    use_container_width=True
)

# ======================
# VALIDACION
# ======================
fallo=False
for d in res:
    if res[d]["Smax"]>res[d]["Sadm"]:
        fallo=True

if fallo:
    st.error("⚠️ Fuera de envolvente → recomienda revestimiento + tratamiento químico")

# ======================
# GOODMAN
# ======================
st.subheader("Diagrama de Goodman")

x=np.linspace(0,150,200)
fig,ax=plt.subplots()

for d in res:
    mat=res[d]["Material"]
    uts=materiales[mat]["uts_a"]
    b=materiales[mat]["b"]

    fs=FS_material(mat,f_base)

    y=goodman_corr(x,uts,b,fs)

