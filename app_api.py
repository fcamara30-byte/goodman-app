import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

st.title("Cálculo de Solicitaciones en Sistemas SRP")

# ======================
# ESTILO VISUAL
# ======================
st.markdown("""
<style>
div[data-testid="stMetric"] {
    text-align: center;
    padding: 8px;
}
div[data-testid="stMetricValue"] {
    font-size: 28px;
    font-weight: bold;
    text-align: center;
}
div[data-testid="stMetricLabel"] {
    text-align: center;
    font-size: 14px;
}
</style>
""", unsafe_allow_html=True)

# ======================
# INPUTS
# ======================
c1,c2=st.columns(2)

with c1:
    L_m = st.number_input("Profundidad pozo (m)",500,5000,1800)
    G = st.slider("Gravedad específica",0.6,1.2,0.95)

with c2:
    D = st.selectbox("Bomba (in)",[1.5,1.75,2,2.25,2.5])
    S = st.slider("Carrera (in)",50,200,168)
    N = st.slider("SPM",1,20,6)

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
st.markdown("### Material por tramo")

c1,c2,c3=st.columns(3)
rod_sel={
    "1":c1.selectbox('1"',materiales.keys()),
    "7/8":c2.selectbox('7/8"',materiales.keys()),
    "3/4":c3.selectbox('3/4"',materiales.keys())
}

# ======================
# CORROSION
# ======================
st.markdown("### Ambiente")

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

f_base = CO2[co2]*H2S[h2s]*BSR[bsr]*factor_cloruros(cl)

st.write("Factor de servicio:", round(f_base,3))

def FS_material(mat,f):
    if f==1: return 1
    if mat=="HS97": return f
    if mat=="DA78": return f*0.95
    if mat=="DSK75": return f if f<0.83 else 1
    if mat=="HA96": return f*0.93
    if mat=="D New": return f*0.94
    return f*0.9

def goodman_corr(smin,uts,b,fs):
    return (uts + b*smin)*fs

# ======================
# VARILLAS
# ======================
st.markdown("### Varillas")

c1,c2=st.columns([1,2])

with c1:
    n1=st.number_input('1"',10,300,75)
    n78=st.number_input('7/8"',10,300,80)
    n34=st.number_input('3/4"',10,300,80)

L1=n1*25
L78=n78*25
L34=n34*25

total=L1+L78+L34

# ======================
# CONTROL DE LONGITUD
# ======================
long_m=total*0.3048
dif=long_m-L_m

with c2:
    st.markdown("### Control de longitud de sarta")

    c1,c2,c3=st.columns(3)

    c1.metric("Profundidad (m)",f"{L_m:.1f}")
    c2.metric("Sarta (m)",f"{long_m:.1f}")
    c3.metric("Diferencia (m)",f"{dif:.1f}")

    if abs(dif)<10:
        st.success("✅ Ajuste correcto")
    elif dif<0:
        st.warning("⚠️ Sarta corta")
    else:
        st.error("❌ Sarta larga")

# ======================
# PROPIEDADES
# ======================
areas={"1":0.786,"7/8":0.601,"3/4":0.442}
peso={"1":2.90,"7/8":2.22,"3/4":1.63}

# ======================
# MODELO CALIBRADO
# ======================
L_ft=L_m*3.28084
Ap=np.pi*D**2/4

W_total=L_ft*2.3
Wr=W_total*(1-0.128*G)

Fh=0.433*G*L_ft*Ap

Fd_base=(S*N)/2000
Fd_base=min(0.20,Fd_base)

Fdyn_up=1.8*Fd_base*Wr
Fdyn_down=0.7*Fd_base*Wr

PPRL=Wr + Fh + Fdyn_up
MPRL=Wr - Fdyn_down
MPRL=max(MPRL,0.55*Wr)

# ======================
# CARGAS
# ======================
st.markdown("### Cargas en cabeza de pozo")

c1,c2=st.columns(2)
c1.metric("PPRL (lb)",f"{int(PPRL):,}")
c2.metric("MPRL (lb)",f"{int(MPRL):,}")

# ======================
# CALCULO
# ======================
pct={"1":L1/total,"7/8":L78/total,"3/4":L34/total}

res={}
fallo=False

for d in pct:

    Smax=PPRL/areas[d]/1000
    Smin=MPRL/areas[d]/1000

    mat=rod_sel[d]
    uts=materiales[mat]["uts_a"]
    b=materiales[mat]["b"]
    fs=FS_material(mat,f_base)

    Sadm=goodman_corr(Smin,uts,b,fs)

    if Smax>Sadm:
        fallo=True

    Gval=((Smax-Smin)/(Sadm-Smin))*100

    res[d]=[mat,round(Smin,1),round(Smax,1),round(Sadm,1),int(Gval)]

# ======================
# RESULTADOS
# ======================
st.markdown("### Resultados")

df=pd.DataFrame(res,index=["Material","Smin","Smax","Sadm","Goodman (%)"]).T

# formato seguro (sin romper streamlit)
df_display=df.copy()
df_display["Goodman (%)"]=df_display["Goodman (%)"].apply(
    lambda x: f"<b><span style='color:blue'>{x}</span></b>"
)

st.write(df_display.to_html(escape=False), unsafe_allow_html=True)

# ======================
# RECOMENDACION
# ======================
st.markdown("### Recomendación")

if fallo:
    st.error("Varillas revestidas + tratamiento químico")

# ======================
# GOODMAN
# ======================
st.markdown("### Diagrama de Goodman")

x=np.linspace(0,150,200)
fig,ax=plt.subplots()

for d in res:
    mat=res[d][0]
    uts=materiales[mat]["uts_a"]
    b=materiales[mat]["b"]
    fs=FS_material(mat,f_base)

    y=goodman_corr(x,uts,b,fs)
    ax.plot(x,y,label=f"{d}-{mat}")

    color="green" if res[d][2]<=res[d][3] else "red"
    ax.scatter(res[d][1],res[d][2],color=color,s=70)

ax.plot(x,x,'k--',label="Límite")
ax.set_xlabel("Smin (ksi)")
ax.set_ylabel("Smax (ksi)")
ax.grid(alpha=0.3)
ax.legend()

st.pyplot(fig)

# ======================
# DISCLAIMER
# ======================
st.markdown("---")
st.caption("Las conclusiones y resultados son orientativas basadas en las formulas de API RP11L mas la experiencia de uso de varillas en fluidos corrosivos.")
