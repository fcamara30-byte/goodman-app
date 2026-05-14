import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("Cálculo de Solicitaciones en Sistemas SRP")

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
# MATERIALES POR TRAMO
# ======================
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
st.subheader("Ambiente")

CO2={"Nada":1,"Medio":0.9,"Alto":0.8}
H2S={"Nada":1,"Medio":0.8,"Alto":0.75}
BSR={"0":1,"1":1,"2":0.95,"3":0.9,"4":0.82,"5":0.74}

c1,c2,c3,c4 = st.columns(4)

co2=c1.selectbox("CO₂",CO2.keys())
h2s=c2.selectbox("H₂S",H2S.keys())
bsr=c3.selectbox("BSR (Caldos +)",BSR.keys())
cl=c4.number_input("Cloruros (ppm)",0,200000,0)

def f_cl(ppm):
    return 1 if ppm<9000 else 1-(0.000019*(ppm**0.8))

f_base=CO2[co2]*H2S[h2s]*BSR[bsr]*f_cl(cl)

# ======================
# FS MATERIAL
# ======================
def FS_material(mat,f):
    if f==1: return 1
    if mat=="HS97": return f
    if mat=="DA78": return f*0.95
    if mat=="DSK75": return f if f<0.83 else 1
    if mat=="HA96": return f*0.93
    if mat=="D New": return f*0.94
    return f*0.9

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
st.subheader("Control de longitud")

long_m = total * 0.3048
dif = long_m - L_m

st.dataframe(
    pd.DataFrame({
        "Longitud pozo (m)": [int(L_m)],
        "Longitud sarta (m)": [int(long_m)],
        "Δ longitud (m)": [int(dif)]
    }),
    use_container_width=True
)

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

st.markdown(f"""
### **PPRL (lb): {int(PPRL):,}**  
### **MPRL (lb): {int(MPRL):,}**
""")

# ======================
# RESULTADOS
# ======================
st.subheader("Resultados por tramo")

pct={"1":L1/total,"7/8":L78/total,"3/4":L34/total}

W1=pct["1"]*L_ft*peso["1"]
W78=pct["7/8"]*L_ft*peso["7/8"]

W_up={"1":0,"7/8":W1,"3/4":W1+W78}

rows=[]
gvals=[]

for d in pct:

    Pmax=PPRL-W_up[d]
    Pmin=max(MPRL-0.5*W_up[d],0)

    Smax_psi=Pmax/areas[d]
    Smin_psi=Pmin/areas[d]

    Smax=Smax_psi/1000
    Smin=Smin_psi/1000

    mat=rod_sel[d]
    fs=FS_material(mat,f_base)

    utsa=materiales[mat]["uts_a"]
    b=materiales[mat]["b"]

    Sadm = utsa*fs + b*Smin

    G=(Smax-Smin)/(Sadm-Smin)*100
    gvals.append(G)

    rows.append({
        "Tramo":d,
        "Material":mat,
        "Max Load (lb)":int(Pmax),
        "Min Load (lb)":int(Pmin),
        "Smax (ksi)":round(Smax,1),
        "Smin (ksi)":round(Smin,1),
        "Goodman (%)":int(G)
    })

st.dataframe(pd.DataFrame(rows),use_container_width=True)

# ======================
# RANKING
# ======================
st.subheader("Ranking")

ranking=[]

for r in rows:

    Smin=r["Smin (ksi)"]
    Smax=r["Smax (ksi)"]

    for mat in materiales:

        fs=FS_material(mat,f_base)
        utsa=materiales[mat]["uts_a"]
        b=materiales[mat]["b"]

        Sadm=utsa*fs + b*Smin
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
# GOODMAN PRO (TRIANGULAR)
# ======================
st.subheader("Diagrama de Goodman")

# límite físico
x_max_list = []

for d in pct:
    mat = rod_sel[d]
    fs  = FS_material(mat, f_base)
    utsa = materiales[mat]["uts_a"]
    b    = materiales[mat]["b"]

    if (1 - b) > 0:
        x_max_list.append((utsa * fs) / (1 - b))

x_max = min(x_max_list)
x=np.linspace(0,x_max,200)

fig,ax=plt.subplots()

curvas=[]

for d in pct:

    mat=rod_sel[d]
    fs=FS_material(mat,f_base)

    utsa=materiales[mat]["uts_a"]
    b=materiales[mat]["b"]

    y=utsa*fs + b*x
    curvas.append(y)

    ax.plot(x,y,label=f"{d}-{mat}")

y_safe=np.minimum.reduce(curvas)

ax.fill_between(x,x,y_safe,where=(y_safe>=x),alpha=0.15,color="green")

for r in rows:
    ax.scatter(r["Smin (ksi)"],r["Smax (ksi)"],s=60)

ax.plot(x,x,color="black")

ax.set_xlim(0,x_max)
ax.set_ylim(0,x_max)

ax.set_xlabel("Smin (ksi)")
ax.set_ylabel("Smax (ksi)")
ax.text(0.02,0.95,f"f_base = {f_servicio:.2f}",transform=ax.transAxes)
st.pyplot(fig)

# ======================
# DISCLAIMER
# ======================
st.markdown("---")
st.caption("Resultados orientativos basados en API RP11L y comportamiento de varillas en ambientes corrosivos.")
