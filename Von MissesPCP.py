import streamlit as st
import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

st.set_page_config(layout="wide")

st.markdown("""
<styleNumberInput"] {width: 140px;}<style>
</style>
""", unsafe_allow_html=True)
st.markdown("""
<style>
.metric-box {
    padding: 15px;
    border-radius: 10px;
    background-color: #f5f5f5;
    text-align: center;
    margin-bottom: 10px;
}

.metric-title {
    font-size: 14px;
    color: #666;
}

.metric-value {
    font-size: 32px;
    font-weight: bold;
    color: #1f3b5c;
}

.metric-red {
    color: #ff1a1a;
}
</style>
""", unsafe_allow_html=True)

st.title("FCAM-PCP-CALCULATION")

colL, colR = st.columns([1,3])

# =========================
# INPUTS
# =========================
with colL:

    c1,c2 = st.columns(2)

    with c1:
        profundidad = st.number_input("Profundidad (m)",600,step=100)
        rpm = st.number_input("RPM (rev/min)",350)
        prod = st.number_input("Producción (m³/d)",150.0)
        pres_linea = st.number_input("Presión línea (kg/cm²)", value=14.0, step=2.0)

        nivel = st.number_input("Nivel dinámico (m)",
          min_value=0.0, max_value=float(profundidad),
            value=float(profundidad),
               step=50.0
)

        densidad = st.number_input("Densidad (kg/m³)",840.0)
        eficiencia = st.number_input("Eficiencia (-)",0.85)

    with c2:
        viscosidad = st.number_input("Viscosidad (cP)",300,step=40)
        sumergencia = st.number_input("Sumergencia (m)", value=50.0,step=10.0)
        tbg = st.selectbox("Tubing (in)", ["4", "3 1/2", "2 7/8"])
        liner = st.selectbox("Tubing liner", ["Sin liner", "Con liner"], key="liner")

        RUGOSIDAD = {
          "Sin liner": 0.00015,
           "Con liner": 0.00001
}

        MU_ROD = {
           "Con liner": 0.08,
           "Sin liner": 0.9    
}

        solidos = st.number_input("Sólidos (%)",5.0)
        rod = st.selectbox("Varilla",["7/8","1","1 1/8"])
        material = st.selectbox("Material",
            ["DA 78","HS97","Alpha CS","Alpha HS","D New","DSK75","HA96"]
        )

RODS={"7/8":{"d":0.875,"peso":2.22},"1":{"d":1.0,"peso":2.67},"1 1/8":{"d":1.125,"peso":3.37}}
YIELD={"DA 78":85,"HS97":115,"Alpha CS":110,"Alpha HS":135,"D New":85,"DSK75":85,"HA96":115}

# =========================
# CALCULO BASE
# =========================

Q = prod / 86400

D_TBG = {"4": 0.089,"3 1/2": 0.076,"2 7/8": 0.062}
D_tbg = D_TBG[tbg]

A_tbg = math.pi * (D_tbg**2) / 4
v = Q / A_tbg
mu = viscosidad / 1000

Re = (1000 * v * D_tbg) / mu
Re = max(Re, 1)

e = RUGOSIDAD[liner]

f = 0.25 / (math.log10((e/(3.7*D_tbg)) + (5.74/(Re**0.9)))**2)

dp_fric = f * (profundidad / D_tbg) * (0.5 * 1000 * v**2)
dp_fric = dp_fric / 98066

pres_nivel = (nivel * densidad) / 10000
pres_entrada = (sumergencia * densidad) / 10000

pres_total = pres_linea + pres_nivel + dp_fric - pres_entrada

pot_h=prod*pres_total*0.0014
pot_c=pot_h/eficiencia

torque=(5252*pot_c)/rpm
torque*= (1+viscosidad/1000)*(1+solidos/100)

d=RODS[rod]["d"]*0.0254
A=math.pi*d**2/4
J=math.pi*d**4/32
r=d/2

peso=RODS[rod]["peso"]*47.88

D_rotor = d * 1.2
Ae = math.pi/4 * (D_rotor**2 - d**2)

dp_pa = pres_total * 98066
L = Ae * dp_pa
Wr = peso * profundidad
F = Wr + L

sigma=(F/A)/6894757

YS=YIELD[material]

# =========================
# TRAYECTORIA
# =========================
st.markdown("---")
modo=st.selectbox("Modo de pozo",["Vertical","Desviado"])

df=pd.DataFrame()
torque_final=torque

if modo=="Desviado":

    text=st.text_area("Perfil: MD Inc Az")

    if text:
        data=[]
        for row in text.strip().split("\n"):
            vals=row.replace(",",".").split()
            try:
                if len(vals)==3:
                    data.append([float(vals[0]),float(vals[1]),float(vals[2])])
            except:
                pass

        df=pd.DataFrame(data,columns=["md","inc","az"])

    if len(df)>1:

        step=7.62
        md_new=np.arange(df["md"].min(),df["md"].max()+step,step)

        df=pd.DataFrame({
            "md":md_new,
            "inc":np.interp(md_new,df["md"],df["inc"]),
            "az":np.interp(md_new,df["md"],df["az"])
        })

        dls=[0]
        for i in range(1,len(df)):
            dmd=(df["md"][i]-df["md"][i-1])*3.28084
            cosdl=(np.cos(np.radians(df["inc"][i]-df["inc"][i-1])))
            dls.append(np.degrees(np.arccos(cosdl))*100/dmd)

        df["DLS"]=np.round(dls,1)

        colores=[];rec=[]
        for dls_val in df["DLS"]:
            if dls_val<=1: colores.append("green");rec.append("sin centralizadores")
            elif dls_val<=3: colores.append("yellow");rec.append("2 centralizadores")
            elif dls_val<=6: colores.append("orange");rec.append("3 centralizadores")
            else: colores.append("red");rec.append("Black Mamba")

        df["Recomendación"]=rec

        # ✅ BLOQUE CORREGIDO
        if len(df)>1:
            mu_rod = MU_ROD[liner]
            radio = d / 2

            df_calc = df.copy()
            df_calc["dMD"] = df_calc["md"].diff().fillna(0)
            df_calc["dW"] = peso * df_calc["dMD"]
            df_calc["W_acum"] = df_calc["dW"].iloc[::-1].cumsum().iloc[::-1]

            factor_contacto = 0.2 + 0.05 * (df_calc["DLS"] / 3)
            df_calc["N"] = df_calc["W_acum"] * factor_contacto

            df_calc["dT"] = mu_rod * df_calc["N"] * radio
            T_fric = df_calc["dT"].sum() / 1000

            torque_final = torque + T_fric
        else:
            torque_final = torque

# ✅ tensiones finales (SIEMPRE con torque_final)
tau = ((torque_final*1.35582*r)/J)/6894757
von = math.sqrt(sigma**2 + 3*tau**2)
uso = von / YS * 100

# =========================
# MÉTRICAS
# =========================

st.markdown("---")
c1,c2,c3=st.columns(3)

with c1:
    st.metric("Axial", f"{sigma:.2f}")
with c2:
    st.metric("Torsión", f"{tau:.2f}")
with c3:
    st.metric("Von Mises", f"{von:.2f}")

c4,c5=st.columns(2)
with c4:
    st.metric("Rod Load", f"{uso:.1f}")
with c5:
    st.metric("Torque", f"{torque_final:.1f}")



