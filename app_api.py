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
    L_m=st.number_input("Profundidad pozo (m)",500,5000,1800)
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
    "DSK75":{"uts_a":42.86,"b":0.375}
}

# ======================
# SELECCIÓN MATERIAL
# ======================
st.subheader("Material por tramo")

c1,c2,c3=st.columns(3)

rod_sel={
    "1":c1.selectbox('1"',materiales.keys()),
    "7/8":c2.selectbox('7/8"',materiales.keys()),
    "3/4":c3.selectbox('3/4"',materiales.keys())
}

# ======================
# CORROSION
# ======================
st.subheader("Ambiente")

CO2={"Nada":1,"Bajo":1,"Medio":0.9,"Alto":0.8}
H2S={"Nada":1,"Bajo":0.95,"Medio":0.8,"Alto":0.75}
BSR={"0":1,"1":1,"2":0.95,"3":0.9,"4":0.82,"5":0.74}

c1,c2,c3,c4=st.columns(4)
co2=c1.selectbox("CO2",CO2.keys())
h2s=c2.selectbox("H2S",H2S.keys())
bsr=c3.selectbox("BSR",BSR.keys())
cl=c4.number_input("Cloruros (ppm)",0,200000,0)

def factor_cloruros(ppm):
    return 1 if ppm<9000 else 1-(0.000019*(ppm**0.8))

f_base=CO2[co2]*H2S[h2s]*BSR[bsr]*factor_cloruros(cl)

st.write(f"Factor de servicio: {round(f_base,3)}")

def FS_material(mat,f):
    if f==1: return 1
    if mat=="HS97": return f
    if mat=="DA78": return f*0.95
    if mat=="DSK75": return f if f<0.83 else 1
    return f*0.9

def goodman_corr(smin,uts,b,fs):
    return (uts+b*smin)*fs

# ======================
# VARILLAS
# ======================
st.subheader("Varillas")

col1,col2=st.columns([1,2])

with col1:
    n1=st.number_input('1"',10,300,75)
    n78=st.number_input('7/8"',10,300,80)
    n34=st.number_input('3/4"',10,300,80)

L1=n1*25
L78=n78*25
L34=n34*25

total_ft=L1+L78+L34
long_m=total_ft*0.3048
dif=long_m-L_m

# ✅ CONTROL PROFUNDIDAD (RESTAURADO)
with col2:

    st.subheader("Control de longitud")

    a,b,c=st.columns(3)
    a.metric("Pozo (m)",round(L_m,1))
    b.metric("Sarta (m)",round(long_m,1))
    c.metric("Dif (m)",round(dif,1))

    if abs(dif)<10:
        st.success("Sarta OK")
    elif dif<0:
        st.warning("Faltan varillas")
    else:
        st.error("Exceso de sarta")

# ======================
# SRP (CARGAS)
# ======================
areas={"1":0.786,"7/8":0.601,"3/4":0.442}
peso={"1":2.90,"7/8":2.22,"3/4":1.63}

L_ft=L_m*3.28084

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

st.subheader("Cargas en vástago")

c1,c2=st.columns(2)
c1.metric("PPRL (lb)",f"{int(PPRL):,}")
c2.metric("MPRL (lb)",f"{int(MPRL):,}")

# ======================
# CALCULO POR TRAMO
# ======================
pct={"1":L1/total_ft,"7/8":L78/total_ft,"3/4":L34/total_ft}

W1=pct["1"]*L_ft*peso["1"]
W78=pct["7/8"]*L_ft*peso["7/8"]
W_up={"1":0,"7/8":W1,"3/4":W1+W78}

res={}
ranking=[]
fallo=False

for d in pct:

    mat=rod_sel[d]
    uts=materiales[mat]["uts_a"]
    b=materiales[mat]["b"]
    fs=FS_material(mat,f_base)

    Pmax=PPRL-W_up[d]
    Pmin=max(MPRL-0.6*W_up[d],0)

    Smax=Pmax/areas[d]/1000
    Smin=Pmin/areas[d]/1000

    Sadm=goodman_corr(Smin,uts,b,fs)

    if Smax>Sadm:
        fallo=True

    G=((Smax-Smin)/(Sadm-Smin))*100

    res[d]=[mat,round(Smin,1),round(Smax,1),round(Sadm,1),int(G)]

    # ranking
    for mat in materiales:
        uts=materiales[mat]["uts_a"]
        fs=FS_material(mat,f_base)
        Sadm=goodman_corr(Smin,uts,materiales[mat]["b"],fs)
        ranking.append([d,mat,Sadm-Smax])

# ======================
# RESULTADOS
# ======================
st.subheader("Resultados")

df=pd.DataFrame(res,index=["Material","Smin (ksi)","Smax (ksi)","Sadm (ksi)","Goodman (%)"]).T
st.dataframe(df, use_container_width=True)

# ======================
# RANKING
# ======================
st.subheader("Ranking de materiales")

df_rank=pd.DataFrame(ranking,columns=["Tramo","Material","Margen"])
df_rank=df_rank.sort_values(by="Margen",ascending=False)

st.dataframe(df_rank, use_container_width=True)

# ======================
# RECOMENDACION
# ======================
st.subheader("Recomendación")

if fallo:
    st.error("Varillas revestidas + tratamiento químico")
else:
    if f_base==1:
        st.success("HS97 lidera (sin corrosión)")
    else:
        mejor=df_rank.iloc[0]
        st.success(f"Material recomendado: {mejor['Material']}")

# ======================
# GOODMAN (FINAL BIEN)
# ======================
st.subheader("Diagrama de Goodman")

x=np.linspace(0,150,200)
fig,ax=plt.subplots()

for d in res:
    mat=res[d][0]
    uts=materiales[mat]["uts_a"]
    b=materiales[mat]["b"]
    fs=FS_material(mat,f_base)

    y=goodman_corr(x,uts,b,fs)
    ax.plot(x,y,label=f"{d}-{mat}")

    Smin=res[d][1]
    Smax=res[d][2]
    Sadm=res[d][3]

    color="green" if Smax<=Sadm else "red"
    ax.scatter(Smin,Smax,color=color,s=70)

ax.plot(x,x,'k--')

ax.set_xlim(0)
ax.set_ylim(0)

ax.set_xlabel("Smin (ksi)")
ax.set_ylabel("Smax (ksi)")

ax.grid()
ax.legend()

st.pyplot(fig)

