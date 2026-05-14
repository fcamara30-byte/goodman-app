import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

st.title("Cálculo de Solicitaciones en Sistemas SRP")

# ======================
# ESTILO
# ======================
st.markdown("""
<style>

div[data-testid="stMetric"] {text-align:center;}
div[data-testid="stMetricValue"] {font-size:28px;font-weight:bold;}

div[data-baseweb="select"] {
    max-width: 180px;
    margin: auto;
}

label {
    text-align:center;
    display:block;
}

</style>
""", unsafe_allow_html=True)

# ======================
# INPUTS
# ======================
c1,c2 = st.columns(2)

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

c1,c2,c3 = st.columns(3)
rod_sel={
    "1":c1.selectbox('1"',materiales.keys()),
    "7/8":c2.selectbox('7/8"',materiales.keys()),
    "3/4":c3.selectbox('3/4"',materiales.keys())
}

# ======================
# CORROSIÓN COMPLETA
# ======================
st.markdown("### Ambiente")

CO2={"Nada":1,"Bajo":1,"Medio":0.9,"Alto":0.8}
H2S={"Nada":1,"Bajo":0.95,"Medio":0.8,"Alto":0.75}
BSR={"0":1,"1":1,"2":0.95,"3":0.9,"4":0.82,"5":0.74}

c1,c2,c3,c4 = st.columns(4)

co2=c1.selectbox("CO2",CO2.keys())
h2s=c2.selectbox("H2S",H2S.keys())
bsr=c3.selectbox("BSR (caldos positivos)",BSR.keys())
cl=c4.number_input("Cloruros (ppm)",0,200000,0)

def factor_cloruros(ppm):
    return 1 if ppm<9000 else 1-(0.000019*(ppm**0.8))

f_base=CO2[co2]*H2S[h2s]*BSR[bsr]*factor_cloruros(cl)

st.write("Factor de servicio:",round(f_base,3))

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
# MODELO
# ======================
areas={"1":0.786,"7/8":0.601,"3/4":0.442}
peso={"1":2.9,"7/8":2.22,"3/4":1.63}

L_ft=L_m*3.28084

Wr=L_ft*2.3*(1-0.128*G)
Ap=np.pi*D**2/4
Fh=0.433*G*L_ft*Ap

Fd=min((S*N)/2000,0.2)

Fdyn_up=1.8*Fd*Wr
Fdyn_down=0.7*Fd*Wr

PPRL=Wr+Fh+Fdyn_up
MPRL=max(Wr-Fdyn_down,0.55*Wr)

# ======================
# OPTIMIZACIÓN
# ======================
modo=st.radio("Modo",["Manual","Optimización automática"])

if modo=="Optimización automática":
    best=None
    best_score=999

    for p1 in np.linspace(0.2,0.5,5):
        for p2 in np.linspace(0.2,0.5,5):
            p3=1-p1-p2
            if p3<=0: continue

            L1o,L78o,L34o=p1*total,p2*total,p3*total

            W1=L1o/total*L_ft*peso["1"]
            W78=L78o/total*L_ft*peso["7/8"]

            W_up={"1":0,"7/8":W1,"3/4":W1+W78}

            maxg=0

            for d in ["1","7/8","3/4"]:
                Pmax=PPRL-W_up[d]
                Pmin=max(MPRL-0.5*W_up[d],0)

                Smax=Pmax/areas[d]/1000
                Smin=Pmin/areas[d]/1000

                mat=rod_sel[d]
                fs=FS_material(mat,f_base)

                Sadm=goodman_corr(Smin,materiales[mat]["uts_a"],materiales[mat]["b"],fs)

                g=(Smax-Smin)/(Sadm-Smin)*100
                maxg=max(maxg,g)

            if maxg<best_score:
                best_score=maxg
                best=(L1o,L78o,L34o)

    L1,L78,L34=best
    st.success("Sarta optimizada")

# ======================
# RESULTADOS
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

    Sadm=goodman_corr(Smin,materiales[mat]["uts_a"],materiales[mat]["b"],fs)

    g=int((Smax-Smin)/(Sadm-Smin)*100)

    res[d]=[mat,round(Smin,1),round(Smax,1),round(Sadm,1),g]

df=pd.DataFrame(res,index=["Material","Smin","Smax","Sadm","Goodman (%)"]).T

df2=df.copy()
df2["Goodman (%)"]=df2["Goodman (%)"].apply(lambda x:f"<b><span style='color:blue'>{x}</span></b>")

st.write(df2.to_html(escape=False),unsafe_allow_html=True)

# ======================
# RANKING
# ======================
st.markdown("### Ranking de varillas")

ranking=[]

for d in pct:
    Smin=res[d][1]
    Smax=res[d][2]

    for mat in materiales:
        fs=FS_material(mat,f_base)
        Sadm=goodman_corr(Smin,materiales[mat]["uts_a"],materiales[mat]["b"],fs)
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
    fs=FS_material(mat,f_base)

    y=goodman_corr(x,materiales[mat]["uts_a"],materiales[mat]["b"],fs)
    ax.plot(x,y)

    ax.scatter(res[d][1],res[d][2],
               color="green" if res[d][2]<=res[d][3] else "red")

ax.plot(x,x,'k--')
st.pyplot(fig)

# ======================
# DISCLAIMER
# ======================
st.markdown("---")
st.caption("Las conclusiones y resultados son orientativas basadas en las formulas de API RP11L mas la experiencia de uso de varillas en fluidos corrosivos.")
