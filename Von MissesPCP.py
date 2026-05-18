import streamlit as st
import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

# =========================
# UI COMPACTA
# =========================
st.markdown("""
<style>
div[data-testid="stNumberInput"] {width: 140px;}
</style>
""", unsafe_allow_html=True)

st.title("PCP + Sarta (Ingeniería Completa)")

# =========================
# LAYOUT
# =========================
colL, colR = st.columns([2,2])

# =========================
# INPUTS
# =========================
with colL:

    c1,c2 = st.columns(2)

    with c1:
        profundidad = st.number_input("Profundidad (m)",600,step=100)
        rpm = st.number_input("RPM (rev/min)",350)
        prod = st.number_input("Producción (m³/d)",150.0)
        pres_linea = st.number_input("Presión línea (kg/cm²)",14.1)
        nivel = st.number_input("Nivel dinámico (m)",570,step=50)
        densidad = st.number_input("Densidad (kg/m³)",840.0)
        eficiencia = st.number_input("Eficiencia (-)",0.6)

    with c2:
        viscosidad = st.number_input("Viscosidad (cP)",300,step=40)
        solidos = st.number_input("Sólidos (%)",5.0)
        rod = st.selectbox("Varilla",["7/8","1","1 1/8"])
        material = st.selectbox("Material",
            ["DA 78","HS97","Alpha CS","Alpha HS","D New","DSK75","HA96"]
        )

# =========================
# DATA
# =========================
RODS={"7/8":{"d":0.875,"peso":2.22},"1":{"d":1.0,"peso":2.67},"1 1/8":{"d":1.125,"peso":3.37}}

YIELD={"DA 78":85,"HS97":115,"Alpha CS":110,"Alpha HS":135,"D New":85,"DSK75":85,"HA96":115}

# =========================
# CALCULO BASE
# =========================
pres_nivel=(nivel*densidad)/10000
pres_total=pres_linea+pres_nivel

pot_h=prod*pres_total*0.0014
pot_c=pot_h/eficiencia

torque=(5252*pot_c)/rpm
torque*= (1+viscosidad/1000)*(1+solidos/100)

d=RODS[rod]["d"]*0.0254
A=math.pi*d**2/4
J=math.pi*d**4/32
r=d/2

peso=RODS[rod]["peso"]*47.88
F=peso*profundidad+densidad*9.81*profundidad*A

sigma=(F/A)/6894757
tau=((torque*1.35582*r)/J)/6894757

von=math.sqrt(sigma**2+3*tau**2)

YS=YIELD[material]
uso=von/YS*100
fs=YS/von

# =========================
# TRAYECTORIA
# =========================
st.markdown("---")
modo=st.selectbox("Modo de pozo",["Vertical","Desviado"])

df=pd.DataFrame()
torque_final=torque

if modo=="Desviado":

    st.subheader("Pegar datos de Profundidad, Inclinación y Azimuth")

    text=st.text_area("Formato: md inc az",height=120)

    if text:
        data=[]
        for row in text.strip().split("\n"):
            vals=row.replace(",",".").split()
            if len(vals)>=3:
                try:data.append([float(vals[0]),float(vals[1]),float(vals[2])])
                except:pass

        df=pd.DataFrame(data,columns=["md","inc","az"])

    if len(df)>1:

        inc=np.radians(df["inc"])
        az=np.radians(df["az"])

        # DLS
        dls=[0]
        for i in range(1,len(df)):
            dmd=(df["md"][i]-df["md"][i-1])*3.28084
            cosdl=(np.sin(inc[i-1])*np.sin(inc[i])*np.cos(az[i]-az[i-1])
                   +np.cos(inc[i-1])*np.cos(inc[i]))
            cosdl=np.clip(cosdl,-1,1)
            dls.append(np.degrees(np.arccos(cosdl))*100/dmd)

        df["DLS"]=dls

        # coordenadas más juntas
        scale=0.2
        df["X"]=np.cumsum(np.sin(inc)*np.cos(az))*scale
        df["Y"]=np.cumsum(np.sin(inc)*np.sin(az))*scale
        df["Z"]=-df["md"]*scale

        # contacto
        carga=RODS[rod]["peso"]*np.sin(inc)*df["md"]*0.05

        colores=[]
        rec=[]
        for c in carga:
            if c<30:colores.append("green");rec.append("Bajo")
            elif c<60:colores.append("yellow");rec.append("1 centralizador")
            elif c<100:colores.append("orange");rec.append("3 centralizadores")
            else:colores.append("red");rec.append("Black Mamba")

        df["Carga"]=carga
        df["Recomendación"]=rec

        torque_final=torque*(1+np.mean(np.sin(inc))*0.4)

# =========================
# RESULTADOS + GRAFICO
# =========================
with colR:

    st.subheader("Torque Final")
    st.metric("Torque (lb-ft)",f"{torque_final:.1f}")

    elev=st.slider("Vista elevación",0,90,25)
    azim=st.slider("Vista azimut",0,360,45)

    if len(df)>1:

        fig=plt.figure(figsize=(5,8))
        ax=fig.add_subplot(111,projection='3d')

        ax.scatter(df["X"],df["Y"],df["Z"],c=colores,s=25)

        ax.view_init(elev=elev,azim=azim)
        ax.tick_params(labelsize=7)
        ax.set_box_aspect([1,1,2])

        st.pyplot(fig)

        st.markdown("### Referencia de contacto")
        st.write("🟢 Bajo | 🟡 1 centralizador | 🟠 3 centralizadores | 🔴 Black Mamba")

        st.markdown("### Recomendación de intervención")
        st.dataframe(df[["md","DLS","Recomendación"]])

# =========================
# RESULTADOS MECANICOS
# =========================
st.markdown("---")
c1,c2,c3=st.columns(3)
c1.metric("Axial (ksi)",f"{sigma:.2f}")
c2.metric("Torsión (ksi)",f"{tau:.2f}")
c3.metric("Von Mises (ksi)",f"{von:.2f}")

c4,c5=st.columns(2)
c4.metric("Uso (%)",f"{uso:.1f}")
c5.metric("FS (-)",f"{fs:.2f}")

