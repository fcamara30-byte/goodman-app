import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

st.title("⚙️ Cálculo de Solicitaciones SRP")

st.markdown("---")

# =========================================================
# INPUTS
# =========================================================
st.subheader("📥 Inputs")

c1,c2,c3,c4 = st.columns(4)

L_m = c1.number_input("Longitud (m)",500,5000,1800)
G   = c2.slider("SG",0.6,1.2,0.95)
D   = c3.selectbox("Bomba (in)",[1.5,1.75,2,2.25,2.5])
N   = c4.slider("SPM",1,20,6)

S = st.slider("Carrera (in)",0,300,168)

st.markdown("---")

# =========================================================
# MATERIALES
# =========================================================
materiales={
    "DA78":{"uts_a":30,"b":0.5625},
    "HS97":{"uts_a":50,"b":0.375},
    "CS":{"uts_a":44.64,"b":0.375},
    "HS":{"uts_a":55.36,"b":0.375},
    "DSK75":{"uts_a":42.86,"b":0.375},
    "HA96":{"uts_a":50,"b":0.375},
    "D New":{"uts_a":42.86,"b":0.375}
}

st.subheader("🛠 Material por tramo")

c1,c2,c3=st.columns(3)

rod_sel={
    "1":c1.selectbox('1"',materiales.keys()),
    "7/8":c2.selectbox('7/8"',materiales.keys()),
    "3/4":c3.selectbox('3/4"',materiales.keys())
}

# =========================================================
# AMBIENTE
# =========================================================
CO2={"Nada":1,"Medio":0.9,"Alto":0.8}
H2S={"Nada":1,"Medio":0.8,"Alto":0.75}
BSR={"0":1,"1":1,"2":0.95,"3":0.9,"4":0.82,"5":0.74}

st.subheader("🌡 Ambiente")

c1,c2,c3,c4=st.columns(4)

co2=c1.selectbox("CO₂",CO2)
h2s=c2.selectbox("H₂S",H2S)
bsr=c3.selectbox("BSR",BSR)
cl =c4.number_input("Cl (ppm)",0,200000,0)

def f_cl(ppm):
    return 1 if ppm<9000 else 1-(0.000019*(ppm**0.8))

f_base=CO2[co2]*H2S[h2s]*BSR[bsr]*f_cl(cl)

def FS_material(mat,f):
    if f==1: return 1
    if mat=="HS97": return f
    if mat=="DA78": return f*0.95
    if mat=="DSK75": return f if f<0.83 else 1
    if mat=="HA96": return f*0.93
    if mat=="D New": return f*0.94
    return f*0.9

# =========================================================
# VARILLAS
# =========================================================
st.subheader("🔩 Varillas")

c1,c2,c3=st.columns(3)

n1=c1.number_input('1"',10,300,75)
n78=c2.number_input('7/8"',10,300,80)
n34=c3.number_input('3/4"',10,300,80)

L1,L78,L34=n1*25,n78*25,n34*25
total=L1+L78+L34

# =========================================================
# CONTROL LONGITUD
# =========================================================
st.subheader("📏 Control de longitud")

long_m=total*0.3048
dif=long_m-L_m

st.dataframe(pd.DataFrame({
    "Pozo (m)":[int(L_m)],
    "Sarta (m)":[int(long_m)],
    "Δ (m)":[int(dif)]
}),use_container_width=True)

# =========================================================
# MODELO BASE
# =========================================================
areas={"1":0.786,"7/8":0.601,"3/4":0.442}
peso={"1":2.9,"7/8":2.22,"3/4":1.63}

L_ft=L_m*3.28084

Wr=L_ft*2.3*(1-0.128*G)
Ap=np.pi*D**2/4
Fh=0.433*G*L_ft*Ap
Fd=min((S*N)/2600,0.15)

# =========================================================
# CARGAS
# =========================================================
PPRL=Wr+Fh+1.45*Fd*Wr

# ✅ MPRL v8 + -10%
E=30_000_000
Aeq=0.58
L_in=L_ft*12

kr=(Aeq*E)/L_in

dx=0.52*S*(Fd**0.78)
prop_L=(L_ft/6000)**0.22
prop_F=(Fh/Wr)**0.08

dF=kr*dx*prop_L*(1+0.35*prop_F)

limite=Wr*(0.45+0.20*Fd)
dF=min(dF,limite)

MPRL=0.90*(Wr-dF)   # ✅ factor -10%

# =========================================================
# DISPLAY CARGAS
# =========================================================
st.subheader("📊 Cargas")

c1,c2=st.columns(2)
c1.metric("PPRL (lb)",f"{int(PPRL):,}")
c2.metric("MPRL (lb)",f"{int(MPRL):,}")

# =========================================================
# RESULTADOS
# =========================================================
st.subheader("📋 Resultados por tramo")

pct={"1":L1/total,"7/8":L78/total,"3/4":L34/total}

W1=pct["1"]*L_ft*peso["1"]
W78=pct["7/8"]*L_ft*peso["7/8"]
W_up={"1":0,"7/8":W1,"3/4":W1+W78}

rows=[]

for d in pct:

    Pmax=PPRL-W_up[d]
    Pmin=max(MPRL-0.5*W_up[d],0)

    Smax=Pmax/areas[d]/1000
    Smin=Pmin/areas[d]/1000

    mat=rod_sel[d]
    fs=FS_material(mat,f_base)

    utsa=materiales[mat]["uts_a"]
    b=materiales[mat]["b"]

    Sadm=utsa*fs+b*Smin
    G=(Smax-Smin)/(Sadm-Smin)*100

    rows.append([d,mat,round(fs,2),int(Pmax),int(Pmin),round(Smax,1),round(Smin,1),int(G)])

df=pd.DataFrame(rows,columns=["Tramo","Material","FS","Max (lb)","Min (lb)","Smax","Smin","Goodman"])

st.dataframe(df,use_container_width=True)

# =========================================================
# GOODMAN
# =========================================================
st.subheader("📈 Diagrama de Goodman")

x_max=min([(materiales[rod_sel[d]]["uts_a"]*FS_material(rod_sel[d],f_base))/(1-materiales[rod_sel[d]]["b"]) for d in pct])
x=np.linspace(0,x_max,200)

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

for r in df.values:
    ax.scatter(r[6],r[5])

ax.plot(x,x)

# FS crítico
fs_crit=df.iloc[df["Goodman"].idxmax()]["FS"]

ax.text(0.02,0.95,f"Factor de Servicio: {fs_crit}",
        transform=ax.transAxes)

st.pyplot(fig)

# =========================================================
# DISCLAIMER
# =========================================================
st.markdown("---")
st.caption("Resultados orientativos según API RP11L + modelo calibrado contra QRod.")
