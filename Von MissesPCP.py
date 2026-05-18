import streamlit as st
import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

# =========================
# CSS UI COMPACTA + ESPACIO
# =========================
st.markdown("""
<style>
div[data-testid="stNumberInput"] {width: 130px;}
div[data-testid="column"] {padding-right: 10px;}
</style>
""", unsafe_allow_html=True)

st.title("PCP + Sarta (Ingeniería)")

# =========================
# LAYOUT PRINCIPAL
# =========================
col_main_left, col_main_right = st.columns([2,2])

# =========================
# INPUTS IZQUIERDA
# =========================
with col_main_left:

    col1, col2 = st.columns([1,1])

    with col1:
        profundidad = st.number_input("Prof",600,step=100)
        rpm = st.number_input("RPM",350)
        prod = st.number_input("Prod",150.0)
        pres_linea = st.number_input("P línea",14.1)
        nivel = st.number_input("Nivel",570,step=50)
        densidad = st.number_input("Densidad",840.0)
        eficiencia = st.number_input("Efic",0.6)

    with col2:
        viscosidad = st.number_input("Visc",300,step=40)
        solidos = st.number_input("%sol",5.0)
        rod = st.selectbox("Rod",["7/8","1","1 1/8"])
        material = st.selectbox("Mat",
            ["DA 78","HS97","Alpha CS","Alpha HS","D New","DSK75","HA96"]
        )

# =========================
# DATA
# =========================
RODS = {
    "7/8":{"d":0.875,"peso":2.22},
    "1":{"d":1.0,"peso":2.67},
    "1 1/8":{"d":1.125,"peso":3.37}
}

YIELD = {
    "DA 78":85,"HS97":115,"Alpha CS":110,
    "Alpha HS":135,"D New":85,"DSK75":85,"HA96":115
}

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
r=d/2
A=math.pi*d**2/4
J=math.pi*d**4/32

peso=RODS[rod]["peso"]*47.88
F=peso*profundidad+densidad*9.81*profundidad*A

sigma=(F/A)/6894757
tau=((torque*1.35582*r)/J)/6894757

von=math.sqrt(sigma**2+3*tau**2)
YS=YIELD[material]

uso=von/YS*100
fs=YS/von

# =========================
# RESULTADOS (IZQUIERDA)
# =========================
with col_main_left:

    st.markdown("---")

    c1,c2,c3=st.columns(3)
    c1.metric("Axial",f"{sigma:.2f}")
    c2.metric("Torsión",f"{tau:.2f}")
    c3.metric("Von Mises",f"{von:.2f}")

    c4,c5=st.columns(2)
    c4.metric("%Uso",f"{uso:.1f}")
    c5.metric("FS",f"{fs:.2f}")

# =========================
# MODO POZO
# =========================
modo = st.selectbox("Trayectoria",["Vertical","Desviado"])

df=pd.DataFrame()

if modo=="Desviado":

    text = st.text_area("Pegar md inc az",height=120)

    if text:
        data=[]
        for riga in text.strip().split("\n"):
            vals=riga.replace(",",".").split()
            if len(vals)>=3:
                try:
                    data.append([float(vals[0]),float(vals[1]),float(vals[2])])
                except:pass

        df=pd.DataFrame(data,columns=["md","inc","az"])

    if len(df)>1:

        inc_rad=np.radians(df["inc"])
        az_rad=np.radians(df["az"])

        # DLS
        dls=[0]
        for i in range(1,len(df)):
            inc1,inc2=inc_rad[i-1],inc_rad[i]
            az1,az2=az_rad[i-1],az_rad[i]

            dmd=(df["md"][i]-df["md"][i-1])*3.28084
            cosdl=np.sin(inc1)*np.sin(inc2)*np.cos(az2-az1)+np.cos(inc1)*np.cos(inc2)
            cosdl=np.clip(cosdl,-1,1)

            dls.append(np.degrees(np.arccos(cosdl))*100/dmd)

        df["DLS"]=dls

        # coordenadas
        df["X"]=np.cumsum(np.sin(inc_rad)*np.cos(az_rad))
        df["Y"]=np.cumsum(np.sin(inc_rad)*np.sin(az_rad))
        df["Z"]=-df["md"]

        # contacto
        carga=RODS[rod]["peso"]*np.sin(inc_rad)*df["md"]*0.05

        col=[]
        for c in carga:
            if c<30:col.append("green")
            elif c<60:col.append("yellow")
            elif c<100:col.append("orange")
            else:col.append("red")

        df["Carga"]=carga

    
# =====================
# TORQUE FINAL SIEMPRE DEFINIDO
# =====================
torque_final = torque  # base (vertical)

if len(df) > 1:
    factor_desvio = 1 + np.mean(np.sin(inc_rad)) * 0.4
    torque_final = torque * factor_desvio


# =========================
# GRAFICO A LA DERECHA
# =========================
with col_main_right:

    st.markdown("### Torque Final")
    st.metric("Torque (lb-ft)",f"{torque_final:.1f}")

    elev=st.slider("Elev",0,90,25)
    azim=st.slider("Azim",0,360,45)

    if len(df)>1:

        fig=plt.figure(figsize=(5,8))
        ax=fig.add_subplot(111,projection='3d')

        ax.scatter(df["X"],df["Y"],df["Z"],c=col,s=30)

        ax.view_init(elev=elev,azim=azim)
        ax.tick_params(labelsize=7)

        ax.set_box_aspect([1,1,2])

        st.pyplot(fig)
