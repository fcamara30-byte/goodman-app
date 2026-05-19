import streamlit as st
import numpy as np
import math
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("PCP + Sarta – Modelo Ingeniería")

colL, colR = st.columns([2,2])

# =========================
# INPUTS
# =========================
with colL:

    profundidad = st.number_input("Profundidad [m]", 0, 3000, 0, 100)
    rpm = st.number_input("RPM", 0, 500, 0)
    prod = st.number_input("Producción [m3/d]", 0)

    pres_linea = st.number_input("Presión línea [kg/cm²]", 0)
    nivel = st.number_input("Nivel dinámico [m]", 0)
    sumergencia = st.number_input("Sumergencia [m]", 0)

    densidad = st.number_input("Densidad [kg/m3]", 500, 1500, 500, 50)
    eficiencia = st.number_input("Eficiencia", value=0.6)

    viscosidad = st.number_input("Viscosidad [cP]", 0, 2000, 0, 50)
    solidos = st.number_input("Sólidos [%]", 0)

with colR:

    tubing_sel = st.selectbox("Tubing", ["2 7/8","3 1/2","4"])
    rod = st.selectbox("Varilla", ["7/8","1","1 1/8"])
    material = st.selectbox("Material", [
        "DA 78","HS97","Alpha CS","Alpha HS","D New","DSK75","HA96"
    ])

# =========================
# DATA
# =========================
TBG_ID={"2 7/8":62,"3 1/2":76,"4":89}

RODS={
 "7/8":{"d":0.875,"peso":2.22},
 "1":{"d":1.0,"peso":2.67},
 "1 1/8":{"d":1.125,"peso":3.37}
}

YIELD={
 "DA 78":85,"HS97":115,"Alpha CS":110,
 "Alpha HS":135,"D New":85,"DSK75":85,"HA96":115
}

tubing=TBG_ID[tubing_sel]

d=RODS[rod]["d"]*0.0254
A=math.pi*d**2/4
r=d/2
J=math.pi*d**4/32
peso=RODS[rod]["peso"]*47.88

rho_steel=7850
peso_eff=peso*(1-densidad/rho_steel)

# =========================
# HIDRÁULICA
# =========================
pres_total=pres_linea+((nivel+sumergencia)*densidad)/10000
pot_h=prod*pres_total*0.0014
pot_c=pot_h/eficiencia if eficiencia!=0 else 0

T_hid=(5252*pot_c)/rpm if rpm!=0 else 0
T_hid*=(1+viscosidad/1000)*(1+solidos/100)
T_hid*=(62/tubing)**0.5

# =========================
# TRAYECTORIA
# =========================
modo=st.selectbox("Modo de pozo",["Vertical","Desviado"])

T_fric=0

if modo=="Desviado":

    st.subheader("Pegar perfil (MD - Inc - Az)")

    text=st.text_area("Ejemplo:\n100 5 120\n200 10 130")

    if text:

        data=[]
        for row in text.split("\n"):
            v=row.strip().split()
            if len(v)>=3:

