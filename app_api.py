import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("Cálculo de Solicitaciones en Sistemas SRP")

# ======================
# ESTILO COMPACTO
# ======================
st.markdown("""
<style>
div[data-baseweb="input"] {max-width:90px;}
div[data-baseweb="select"] {max-width:140px;}
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

csl1,csl2,csl3 = st.columns([1,2,1])
with csl2:
    S = st.slider("Carrera (in)",0,300,168)

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
# MATERIAL
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

co2=c1.selectbox("CO₂",CO2.keys())
h2s=c2.selectbox("H₂S",H2S.keys())
bsr=c3.selectbox("BSR (Caldos +)",BSR.keys())
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

n1=c1.number_input('1"',10,300,75)
n78=c2.number_input('7/8"',10,300,80)
n34=c3.number_input('3/4"',10,300,80)

L1=n1*25
L78=n78*25
L34=n34*25
total=L1+L78+L34

# ======================
# CONTROL LONGITUD
# ======================
long_m=total*0.3048
dif=long_m-L_m

st.subheader("Control de longitud")

df_long=pd.DataFrame({
    "Longitud pozo (m)":[int(L_m)],
    "Longitud sarta (m)":[int(long_m)],
    "Δ longitud (m)":[int(dif)]
})

st.dataframe(df_long,use_container_width=True)

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

PPRL=Wr+Fh+1.45*Fd*Wr
MPRL=max(Wr-0.75*Fd*Wr,0.6*Wr)

# ======================
# CARGAS
# ======================
st.subheader("Cargas")

st.dataframe(pd.DataFrame({
    "PPRL (lb)":[int(PPRL)],
    "MPRL (lb)":[int(MPRL)]
}),use_container_width=True)

# ======================
# RESULTADOS API
# ======================
st.subheader("Resultados por tramo")

pct={"1":L1/total,"7/8":L78/total,"3/4":L34/total}

W1=pct["1"]*L_ft*peso["1"]
W78=pct["7/8"]*L_ft*peso["7/8"]

W_up={"1":0,"7/8":W1,"3/4":W1+W78}

rows=[]

g_values=[]

for d in pct:

    Pmax=PPRL-W_up[d]
    Pmin=max(MPRL-0.5*W_up[d],0)

    Smax_psi=Pmax/areas[d]
    Smin_psi=Pmin/areas[d]

    Smax=Smax_psi/1000
    Smin=Smin_psi/1000

    mat=rod_sel[d]
    fs=FS_material(mat,f_base)

    Sadm=goodman(Smin,materiales[mat]["uts_a"],materiales[mat]["b"],fs)

    G=(Smax-Smin)/(Sadm-Smin)*100
    g_values.append(G)

    rows.append({
        "Rod Type":mat,
        "Rod Diam (in)":d,
        "Max Load (lb)":int(Pmax),
        "Min Load (lb)":int(Pmin),
        "Max Stress (psi)":f"{Smax_psi:.0f}",
        "Min Stress (psi)":f"{Smin_psi:.0f}",
        "Goodman (%)":int(G)
    })

st.dataframe(pd.DataFrame(rows),use_container_width=True)

# ======================
# RANKING
# ======================
st.subheader("Ranking")

ranking=[]

for r in rows:

    Smin=float(r["Min Stress (psi)"])/1000
    Smax=float(r["Max Stress (psi)"])/1000

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

df_rank["Margen"]=df_rank["Margen"].map(lambda x:f"{x:.1f}")

st.dataframe(df_rank.drop(columns="Orden",errors="ignore"),use_container_width=True)

# ======================
# GOODMAN PRO
# ======================
st.subheader("Diagrama de Goodman")

x=np.linspace(0,150,200)
fig,ax=plt.subplots()

max_G=max(g_values)
crit_idx=g_values.index(max_G)
crit_row=rows[crit_idx]

for r in rows:

    mat=r["Rod Type"]
    fs=FS_material(mat,f_base)
    uts=materiales[mat]["uts_a"]
    b=materiales[mat]["b"]

    y=(uts + b*x)*fs
    ax.plot(x,y,label=mat)

# zona segura
y_safe=min([(materiales[r["Rod Type"]]["uts_a"] + materiales[r["Rod Type"]]["b"]*x)*FS_material(r["Rod Type"],f_base) for r in rows])
ax.fill_between(x,0,y_safe,alpha=0.1,color="green")

# puntos
for r in rows:
    smin=float(r["Min Stress (psi)"])/1000
    smax=float(r["Max Stress (psi)"])/1000
    ax.scatter(smin,smax,s=60)

# punto crítico
smin=float(crit_row["Min Stress (psi)"])/1000
smax=float(crit_row["Max Stress (psi)"])/1000
ax.scatter(smin,smax,color="red",s=140,edgecolor="black",label="Crítico")

# línea 45°
ax.plot(x,x,color="black")

ax.set_xlim(0)
ax.set_ylim(0)
ax.set_xlabel("Smin (ksi)")
ax.set_ylabel("Smax (ksi)")

ax.text(0.05,0.95,f"FS: {f_base:.2f}",transform=ax.transAxes)

ax.legend(fontsize=8)

st.pyplot(fig)

# ======================
# DISCLAIMER
# ======================
st.markdown("---")
st.caption("Las conclusiones y resultados son orientativas basadas en API RP11L y experiencia en fluidos corrosivos.")
