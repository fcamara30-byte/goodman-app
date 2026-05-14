import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

st.title("Cálculo de Solicitaciones en Sistemas SRP")

# ======================
# ESTILO (COMPACTO PERO USABLE)
# ======================
st.markdown("""
<style>

div[data-baseweb="select"] {
    max-width: 140px;
}

input {
    max-width: 80px !important;
}

table {
    width:100%;
    text-align:center;
    font-size:13px;
}

</style>
""", unsafe_allow_html=True)

# ======================
# INPUTS
# ======================
c1,c2,c3,c4 = st.columns(4)

L_m = c1.number_input("Longitud pozo (m)",500,5000,1800)
G   = c2.slider("Gravedad específica",0.6,1.2,0.95)
D   = c3.selectbox("Bomba (in)",[1.5,1.75,2,2.25,2.5])
N   = c4.slider("SPM",1,20,6)

S = st.slider("Carrera (in)",50,200,168)

# ======================
# MATERIALES
# ======================
materiales={
    "DA78":{"uts_a":30,"b":0.5625},
    "HS97":{"uts_a":50,"b":0.375},
    "CS propietario":{"uts_a":44.64,"b":0.375},
    "HS propietario":{"uts_a":55.36,"b":0.375},
    "DSK75":{"uts_a":42.86,"b":0.375},
    "HA96":{"uts_a":50,"b":0.375},
    "D New":{"uts_a":42.86,"b":0.375}
}

# ======================
# MATERIAL POR TRAMO
# ======================
st.subheader("Material por tramo")

c1,c2,c3 = st.columns(3)
rod_sel={
    "1":c1.selectbox('1"',materiales.keys()),
    "7/8":c2.selectbox('7/8"',materiales.keys()),
    "3/4":c3.selectbox('3/4"',materiales.keys())
}

# ======================
# CORROSIÓN
# ======================
st.subheader("Ambiente")

CO2={"Nada":1,"Bajo":1,"Medio":0.9,"Alto":0.8}
H2S={"Nada":1,"Bajo":0.95,"Medio":0.8,"Alto":0.75}
BSR={"0":1,"1":1,"2":0.95,"3":0.9,"4":0.82,"5":0.74}

c1,c2,c3,c4 = st.columns(4)

co2=c1.selectbox("CO2",CO2.keys())
h2s=c2.selectbox("H2S",H2S.keys())
bsr=c3.selectbox("BSR",BSR.keys())
cl=c4.number_input("Cloruros (ppm)",0,200000,0)

def factor_cloruros(ppm):
    return 1 if ppm<9000 else 1-(0.000019*(ppm**0.8))

f_base=CO2[co2]*H2S[h2s]*BSR[bsr]*factor_cloruros(cl)

# ======================
# FUNCIONES
# ======================
def FS_material(mat,f):
    if f==1: return 1
    if mat=="HS97": return f
    if mat=="DA78": return f*0.95
    if mat=="DSK75": return f if f<0.83 else 1
    if mat=="HA96": return f*0.93
    if mat=="D New": return f*0.94
    return f*0.9

def goodman(smin,uts,b,fs):
    return (uts + b*smin)*fs

# ======================
# VARILLAS
# ======================
st.subheader("Varillas")

c1,c2,c3 = st.columns(3)

n1  = c1.number_input('1"',10,300,75)
n78 = c2.number_input('7/8"',10,300,80)
n34 = c3.number_input('3/4"',10,300,80)

L1=n1*25
L78=n78*25
L34=n34*25
total=L1+L78+L34

# ======================
# CONTROL LONGITUD
# ======================
st.subheader("Control de longitud")

long_m=total*0.3048
dif=long_m-L_m

st.write(pd.DataFrame({
    "Longitud pozo (m)":[int(L_m)],
    "Longitud sarta (m)":[int(long_m)],
    "Δ longitud (m)":[int(dif)]
}))

# ======================
# MODELO
# ======================
areas={"1":0.786,"7/8":0.601,"3/4":0.442}
peso={"1":2.9,"7/8":2.22,"3/4":1.63}

L_ft=L_m*3.28084
Wr=L_ft*2.3*(1-0.128*G)
Ap=np.pi*D**2/4
Fh=0.433*G*L_ft*Ap

Fd=min((S*N)/2600,0.15)

Fdyn_up=1.45*Fd*Wr
Fdyn_down=0.75*Fd*Wr

PPRL=Wr+Fh+Fdyn_up
MPRL=max(Wr-Fdyn_down,0.6*Wr)

# ======================
# CARGAS
# ======================
st.subheader("Cargas")

st.write(pd.DataFrame({
    "PPRL (lb)":[int(PPRL)],
    "MPRL (lb)":[int(MPRL)]
}))

# ======================
# RESULTADOS POR TRAMO
# ======================
pct={"1":L1/total,"7/8":L78/total,"3/4":L34/total}

W1=pct["1"]*L_ft*peso["1"]
W78=pct["7/8"]*L_ft*peso["7/8"]

W_up={"1":0,"7/8":W1,"3/4":W1+W78}

res={}

for d in pct:

    Pmax=PPRL-W_up[d]
    Pmin=max(MPRL-0.5*W_up[d],0)

    Smax=Pmax/areas[d]/1000
    Smin=Pmin/areas[d]/1000

    mat=rod_sel[d]
    fs=FS_material(mat,f_base)

    Sadm=goodman(Smin,materiales[mat]["uts_a"],materiales[mat]["b"],fs)

    g=int((Smax-Smin)/(Sadm-Smin)*100)

    res[d]=[mat,Smin,Smax,Sadm,g]

df=pd.DataFrame(res,index=["Material","Smin","Smax","Sadm","Goodman (%)"]).T
st.dataframe(df)

# ======================
# RANKING
# ======================
st.subheader("Ranking")

ranking=[]

for d in pct:
    Smin=res[d][1]
    Smax=res[d][2]

    for mat in materiales:
        fs=FS_material(mat,f_base)
        Sadm=goodman(Smin,materiales[mat]["uts_a"],materiales[mat]["b"],fs)
        ranking.append([mat,Sadm-Smax])

df_rank=pd.DataFrame(ranking,columns=["Material","Margen"])
df_rank=df_rank.groupby("Material").mean().reset_index()

if f_base==1:
    df_rank["Orden"]=df_rank["Material"].apply(lambda x:0 if x=="HS97" else 1)
    df_rank=df_rank.sort_values(["Orden","Margen"],ascending=[True,False])
else:
    df_rank=df_rank.sort_values(by="Margen",ascending=False)

st.dataframe(df_rank.drop(columns="Orden",errors="ignore"))

# ======================
# GOODMAN CORRECTO
# ======================
st.subheader("Diagrama de Goodman")

x=np.linspace(0,150,200)
fig,ax=plt.subplots()

for d in res:

    mat=res[d][0]
    smin=res[d][1]
    smax=res[d][2]

    fs=FS_material(mat,f_base)
    uts=materiales[mat]["uts_a"]
    b=materiales[mat]["b"]

    y=goodman(x,uts,b,fs)

    ax.plot(x,y,label=f"{d}-{mat}")
    ax.scatter(smin,smax,label=f"Punto {d}",s=70)

ax.set_xlabel("Smin (ksi)")
ax.set_ylabel("Smax (ksi)")
ax.legend()

st.pyplot(fig)

# ======================
# DISCLAIMER
# ======================
st.markdown("---")
st.caption("Resultados orientativos basados en API RP11L y experiencia en varillas en fluidos corrosivos.")
