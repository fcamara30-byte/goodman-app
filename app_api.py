import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

st.markdown(
    f"""
    <div style="position:fixed;
                top:5px;
                left:10px;
                font-size:12px;
                color:gray;
                z-index:1000;">
        Visitas: {visitas}
    </div>
    """,
    unsafe_allow_html=True
)

import os

archivo_contador = "visitas.txt"

if os.path.exists(archivo_contador):
    with open(archivo_contador, "r") as f:
        visitas = int(f.read())
else:
    visitas = 0

visitas += 1

with open(archivo_contador, "w") as f:
    f.write(str(visitas))

.markdown(
    f"""
    <div style="position:fixed;
                top:5px;
                left:10px;
                font-size:12px;
                color:gray;
                z-index:1000;">
        Visitas: {visitas}
    </div>
    """,
    unsafe_allow_html=True
)

st.title("Cálculo de Solicitaciones SRP Corrosión-Fatiga")

# ======================
# INPUTS
# ======================
c1,c2,c3,c4 = st.columns(4)

L_m = c1.number_input("Longitud pozo (m)",500,5000,1800)
G   = c2.slider("Gravedad específica",0.6,1.2,0.95)
D   = c3.selectbox("Bomba (in)",[1.5,1.75,2,2.25,2.5])
N   = c4.slider("SPM",1,20,6)

S = st.slider("Carrera (in)",0,300,168)

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

st.subheader("Material por tramo")

c1,c2,c3 = st.columns(3)
rod_sel={
    "1":c1.selectbox('1"',materiales.keys()),
    "7/8":c2.selectbox('7/8"',materiales.keys()),
    "3/4":c3.selectbox('3/4"',materiales.keys())
}

# ======================
# AMBIENTE
# ======================
CO2={"Nada":1,"Medio":0.9,"Alto":0.8}
H2S={"Nada":1,"Medio":0.8,"Alto":0.75}
BSR={"0":1,"1":1,"2":0.95,"3":0.9,"4":0.82,"5":0.74}

c1,c2,c3,c4 = st.columns(4)

co2=c1.selectbox("CO₂",CO2)
h2s=c2.selectbox("H₂S",H2S)
bsr=c3.selectbox("BSR",BSR)
cl=c4.number_input("Cloruros (ppm)",0,200000,0)

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

# ======================
# CANT. VARILLAS
# ======================
st.subheader("Cant. Varillas")

c1,c2,c3=st.columns(3)

n1=c1.number_input('1"',10,300,75)
n78=c2.number_input('7/8"',10,300,80)
n34=c3.number_input('3/4"',10,300,80)

L1,L78,L34=n1*25,n78*25,n34*25
total=L1+L78+L34

# ======================
# CONTROL LONGITUD
# ======================
st.subheader("Control de longitud")

long_m=total*0.3048
dif=long_m-L_m

st.dataframe(pd.DataFrame({
    "Pozo (m)":[int(L_m)],
    "Sarta (m)":[int(long_m)],
    "Δ (m)":[int(dif)]
}),use_container_width=True)

# ======================
# MODELO
# ======================
areas={"1":0.786,"7/8":0.601,"3/4":0.442}
peso={"1":2.9,"7/8":2.22,"3/4":1.63}

# peso real
Wr_air = L1*peso["1"] + L78*peso["7/8"] + L34*peso["3/4"]
Wr = Wr_air*(1-0.128*G)

L_total_ft = L1+L78+L34

Ap=np.pi*D**2/4
Fh=0.433*G*L_total_ft*Ap

# ✅ NUEVO Fd (RESPONDE A SPM)
Fd = (S * N) / (2600 + S * N)

# ======================
# PPRL
# ======================
PPRL=(Wr+Fh+1.45*Fd*Wr)*0.92

# ======================
# MPRL
# ======================
E=30_000_000
Aeq=0.58

kr=(Aeq*E)/(L_total_ft*12)

dx=0.52*S*(Fd**0.78)

prop_L=(L_total_ft/6000)**0.22
prop_F=(Fh/Wr)**0.08

# ✅ CLAVE: efecto dinámico fuerte
dF = kr*dx*prop_L*(1+0.35*prop_F)*(1 + 2.5*Fd)

limite=Wr*(0.45+0.20*Fd)
dF=min(dF,limite)

MPRL_base=max(Wr-dF,0)

# factores finales
MPRL = MPRL_base * 0.97

# ======================
# DISPLAY
# ======================
st.subheader("Cargas")

c1,c2=st.columns(2)
c1.metric("PPRL (lb)",f"{int(PPRL):,}")
c2.metric("MPRL (lb)",f"{int(MPRL):,}")

# ======================
# RESULTADOS
# ======================
st.subheader("Resultados por tramo")

pct={"1":L1/total,"7/8":L78/total,"3/4":L34/total}

W1=pct["1"]*Wr_air
W78=pct["7/8"]*Wr_air

W_up={"1":0,"7/8":W1,"3/4":W1+W78}

rows=[]
colors=["red","green","orange"]

for i,d in enumerate(pct):

    Pmax=PPRL-W_up[d]
    Pmin=max(MPRL-0.3*W_up[d],0)

    Smax=Pmax/areas[d]/1000
    Smin=Pmin/areas[d]/1000

    mat=rod_sel[d]
    fs=FS_material(mat,f_base)

    utsa=materiales[mat]["uts_a"]
    b=materiales[mat]["b"]

    Sadm=utsa*fs+b*Smin
    Gval=(Smax-Smin)/(Sadm-Smin)*100

    rows.append({
        "Tramo":d,
        "Material":mat,
        "FS":round(fs,2),
        "Max Load (lb)":int(Pmax),
        "Min Load (lb)":int(Pmin),
        "Smax (ksi)":round(Smax,1),
        "Smin (ksi)":round(Smin,1),
        "Goodman (%)":int(Gval),
        "Color":colors[i]
    })

df=pd.DataFrame(rows)
st.dataframe(df.drop(columns=["Color"]),use_container_width=True)

# ======================
# GOODMAN
# ======================
st.subheader("Diagrama de Goodman")

x_max=min([
    materiales[rod_sel[d]]["uts_a"] *
    FS_material(rod_sel[d],f_base) / (1-materiales[rod_sel[d]]["b"])
    for d in pct
])

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

labels=set()
for _,r in df.iterrows():
    etiqueta=f'{r["Tramo"]}" - {r["Material"]}'
    if etiqueta not in labels:
        ax.scatter(r["Smin (ksi)"],r["Smax (ksi)"],label=etiqueta)
        labels.add(etiqueta)
    else:
        ax.scatter(r["Smin (ksi)"],r["Smax (ksi)"])

ax.plot(x,x)

ax.set_xlim(left=0)
ax.set_ylim(bottom=0)

ax.set_xlabel("Smin (ksi)")
ax.set_ylabel("Smax (ksi)")

ax.legend(title="Tramo")

st.pyplot(fig)

# ======================
# FOOTER
# ======================
st.markdown("---")
st.caption("Modelo SRP sólo referencial")
