import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

st.set_page_config(layout="centered")

# ======================
# CONTADOR
# ======================
archivo_contador = "visitas.txt"

if os.path.exists(archivo_contador):
    with open(archivo_contador, "r") as f:
        try:
            visitas = int(f.read())
        except:
            visitas = 0
else:
    visitas = 0

visitas += 1

with open(archivo_contador, "w") as f:
    f.write(str(visitas))

# ======================
# ESTILO
# ======================
st.markdown("""
<style>
.block-container {
    max-width: 1050px;
    padding-top: 1rem;
}
</style>
""", unsafe_allow_html=True)

# ======================
# CABECERA
# ======================
c_img, c_title = st.columns([1,5])

with c_img:
    st.image(
        "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3b/Pumpjack.svg/120px-Pumpjack.svg.png",
        width=80
    )

with c_title:
    st.title("Cálculo de Solicitaciones SRP Corrosión-Fatiga")
    st.caption(f"Visitas totales: {visitas}")

# ======================
# INPUTS
# ======================
c1,c2,c3,c4 = st.columns([1,1,1,1])

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
CO2={"Nada":1,"Bajo":0.98,"Medio":0.9,"Alto":0.8}
H2S={"Nada":1,"Bajo":0.93,"Medio":0.8,"Alto":0.75}
BSR={"0":1,"1":1,"2":0.95,"3":0.9,"4":0.82,"5":0.74}

c1,c2,c3,c4 = st.columns(4)

co2=c1.selectbox("CO₂",CO2)
h2s=c2.selectbox("H₂S",H2S)
bsr=c3.selectbox("BSR",BSR)
cl=c4.number_input("Cloruros (ppm)",0,250000,0)

def f_cl(ppm):
    return 1 if ppm<9000 else 1-(0.000019*(ppm**0.8))

f_base=CO2[co2]*H2S[h2s]*BSR[bsr]*f_cl(cl)

def FS_material(mat,f):
    if f==1: return 1
    if mat=="DA78": return f*0.95
    elif mat=="HS97": return f*0.96
    elif mat=="CS": return f*0.96
    elif mat=="HS": return f*0.75
    elif mat=="D New": return f*0.94
    elif mat=="DSK75": return f if f < 0.75 else 1
    elif mat=="HA96": return f*0.85
    return f*0.9

# ======================
# VARILLAS
# ======================
st.subheader("Cant. Varillas")

c1,c2,c3=st.columns(3)

n1=c1.number_input('1"',10,300,75)
n78=c2.number_input('7/8"',10,300,80)
n34=c3.number_input('3/4"',10,300,80)

L1,L78,L34=n1*25,n78*25,n34*25
total=L1+L78+L34

# ======================
# MODELO
# ======================
areas={"1":0.786,"7/8":0.601,"3/4":0.442}
peso={"1":2.9,"7/8":2.22,"3/4":1.63}

Wr_air = L1*peso["1"] + L78*peso["7/8"] + L34*peso["3/4"]
Wr = Wr_air*(1-0.128*G)

L_total_ft = total

Ap=np.pi*D**2/4
Fh=0.433*G*L_total_ft*Ap

Fd = (S * N) / (2600 + S * N)

PPRL=(Wr+Fh+1.45*Fd*Wr)*0.92

dF = 0.52*S*(Fd**0.78)

MPRL=max(Wr-dF,0)*0.97

# ======================
# OUTPUT
# ======================
st.subheader("Cargas")

c1,c2=st.columns(2)
c1.metric("PPRL (lb)",f"{int(PPRL):,}")
c2.metric("MPRL (lb)",f"{int(MPRL):,}")

# ======================
# GOODMAN
# ======================
st.subheader("Diagrama de Goodman")

x=np.linspace(0,100,200)

fig,ax=plt.subplots(figsize=(6,4))

curvas=[]
rows=[]

for d in rod_sel:

    mat=rod_sel[d]
    fs=FS_material(mat,f_base)

    y=materiales[mat]["uts_a"]*fs + materiales[mat]["b"]*x
    curvas.append(y)

    # ⚠️ uso valores originales (NO los altero)
    Smax=50
    Smin=30

    Sadm=materiales[mat]["uts_a"]*fs + materiales[mat]["b"]*Smin
    Gval=(Smax-Smin)/(Sadm-Smin)*100

    rows.append({
        "Tramo":d,
        "Material":mat,
        "Smax (ksi)":Smax,
        "Smin (ksi)":Smin,
        "Goodman (%)":Gval
    })

    ax.plot(x,y)

# zona segura
y_safe=np.minimum.reduce(curvas)
ax.fill_between(x,x,y_safe,where=(y_safe>=x),alpha=0.2)

# línea 45°
ax.plot(x,x)

df=pd.DataFrame(rows)

# puntos con color dinámico
for _,r in df.iterrows():

    color_pto = "green" if r["Goodman (%)"] <= 100 else "red"

    ax.scatter(
        r["Smin (ksi)"],
        r["Smax (ksi)"],
        color=color_pto,
        s=80,
        edgecolors="black",
        label=r["Material"]
    )

# mensaje
if any(df["Goodman (%)"]>100):
    ax.text(
        0.5,0.1,
        "Zona insegura\nRevisar diseño o aplicar mitigación",
        transform=ax.transAxes,
        color="red",
        ha="center"
    )

ax.set_xlabel("Smin (ksi)")
ax.set_ylabel("Smax (ksi)")
ax.set_title("Goodman")
ax.legend()

st.pyplot(fig)

# indicador global
if any(df["Goodman (%)"] > 100):
    st.error("🚫 Falla en al menos un tramo")
else:
    st.success("✅ Condición segura")

# ======================
# TABLA
# ======================
def color_estado(val):
    return "color:red" if val>100 else "color:green"

st.dataframe(
    df.style.applymap(color_estado, subset=["Goodman (%)"]),
    use_container_width=False,
    height=220
)

# ======================
# FOOTER
# ======================
st.markdown("---")
st.caption("Modelo basado en Goodman + experiencia de campo")
