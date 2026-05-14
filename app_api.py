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
div[data-testid="stMetric"] {text-align: center;}
div[data-testid="stMetricValue"] {font-size: 28px; font-weight: bold;}
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
# CORROSIÓN
# ======================
CO2={"Nada":1,"Medio":0.9,"Alto":0.8}
H2S={"Nada":1,"Medio":0.8,"Alto":0.75}

co2=st.selectbox("CO2",CO2.keys())
h2s=st.selectbox("H2S",H2S.keys())

f_base=CO2[co2]*H2S[h2s]

def FS_material(mat,f):
    return f if f<1 else 1

def goodman(smin,uts,b,fs):
    return (uts + b*smin)*fs

# ======================
# VARILLAS
# ======================
st.markdown("### Varillas")

n1=st.number_input('1"',10,300,75)
n78=st.number_input('7/8"',10,300,80)
n34=st.number_input('3/4"',10,300,80)

L1=n1*25
L78=n78*25
L34=n34*25

total=L1+L78+L34

# ======================
# CONTROL LONGITUD
# ======================
long_m=total*0.3048
dif=long_m-L_m

c1,c2,c3=st.columns(3)
c1.metric("Pozo",round(L_m,1))
c2.metric("Sarta",round(long_m,1))
c3.metric("Dif",round(dif,1))

# ======================
# PROPIEDADES
# ======================
areas={"1":0.786,"7/8":0.601,"3/4":0.442}
peso={"1":2.9,"7/8":2.22,"3/4":1.63}

L_ft=L_m*3.28084

W_total=L_ft*2.3
Wr=W_total*(1-0.128*G)

Ap=np.pi*D**2/4
Fh=0.433*G*L_ft*Ap

Fd=(S*N)/2000
Fd=min(Fd,0.2)

Fdyn_up=1.8*Fd*Wr
Fdyn_down=0.7*Fd*Wr

PPRL=Wr+Fh+Fdyn_up
MPRL=Wr-Fdyn_down
MPRL=max(MPRL,0.55*Wr)

# ======================
# OPTIMIZACION
# ======================
modo=st.radio("Modo",["Manual","Optimización automática"])

if modo=="Optimización automática":

    best=None
    best_g=999

    for p1 in np.linspace(0.2,0.5,5):
        for p2 in np.linspace(0.2,0.5,5):
            p3=1-p1-p2
            if p3<=0: continue

            L1o=p1*total
            L78o=p2*total
            L34o=p3*total

            W1=L1o/total*L_ft*peso["1"]
            W78=L78o/total*L_ft*peso["7/8"]

            W_up={"1":0,"7/8":W1,"3/4":W1+W78}

            maxg=0

            for d in ["1","7/8","3/4"]:
                area=areas[d]

                Pmax=PPRL-W_up[d]
                Pmin=max(MPRL-0.5*W_up[d],0)

                Smax=Pmax/area/1000
                Smin=Pmin/area/1000

                mat=rod_sel[d]
                uts=materiales[mat]["uts_a"]
                b=materiales[mat]["b"]

                Sadm=goodman(Smin,uts,b,f_base)

                g=(Smax-Smin)/(Sadm-Smin)*100
                maxg=max(maxg,g)

            if maxg<best_g:
                best_g=maxg
                best=(L1o,L78o,L34o)

    L1,L78,L34=best
    st.success("Sarta optimizada")

# ======================
# RESULTADOS
# ======================
st.markdown("### Resultados")

pct={"1":L1/total,"7/8":L78/total,"3/4":L34/total}

W1=pct["1"]*L_ft*peso["1"]
W78=pct["7/8"]*L_ft*peso["7/8"]

W_up={"1":0,"7/8":W1,"3/4":W1+W78}

res={}
fallo=False

for d in pct:

    Pmax=PPRL-W_up[d]
    Pmin=max(MPRL-0.5*W_up[d],0)

    Smax=Pmax/areas[d]/1000
    Smin=Pmin/areas[d]/1000

    mat=rod_sel[d]
    uts=materiales[mat]["uts_a"]
    b=materiales[mat]["b"]

    Sadm=goodman(Smin,uts,b,f_base)

    if Smax>Sadm:
        fallo=True

    g=int((Smax-Smin)/(Sadm-Smin)*100)

    res[d]=[mat,round(Smin,1),round(Smax,1),round(Sadm,1),g]

df=pd.DataFrame(res,index=["Material","Smin","Smax","Sadm","Goodman (%)"]).T

# GOODMAN EN AZUL
df2=df.copy()
df2["Goodman (%)"]=df2["Goodman (%)"].apply(lambda x:f"<b><span style='color:blue'>{x}</span></b>")

st.write(df2.to_html(escape=False),unsafe_allow_html=True)

# ======================
# CARGAS
# ======================
st.markdown("### Cargas")

c1,c2=st.columns(2)
c1.metric("PPRL",int(PPRL))
c2.metric("MPRL",int(MPRL))

# ======================
# GOODMAN
# ======================
st.markdown("### Diagrama Goodman")

x=np.linspace(0,150,200)
fig,ax=plt.subplots()

for d in res:
    mat=res[d][0]
    uts=materiales[mat]["uts_a"]
    b=materiales[mat]["b"]

    y=goodman(x,uts,b,f_base)
    ax.plot(x,y)

    ax.scatter(res[d][1],res[d][2],
               color="green" if res[d][2]<=res[d][3] else "red")

ax.plot(x,x,'k--')

st.pyplot(fig)

# ======================
# RECOMENDACIÓN
# ======================
if fallo:
    st.error("Varillas revestidas + tratamiento químico")

# ======================
# DISCLAIMER
# ======================
st.markdown("---")
st.caption("Las conclusiones y resultados son orientativas basadas en las formulas de API RP11L mas la experiencia de uso de varillas en fluidos corrosivos.")
