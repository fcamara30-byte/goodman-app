import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ======================
# CONFIG
# ======================
st.set_page_config(layout="wide")
st.title("Calculo de Solicitaciones (Versión Beta)")

# ======================
# INPUTS
# ======================
c1, c2 = st.columns(2)

with c1:
    L_m = st.number_input("Profundidad (m)", 500, 5000, 1800)
    G = st.slider("Gravedad específica", 0.6, 1.2, 0.95)

with c2:
    D = st.selectbox("Bomba (in)", [1.5,1.75,2,2.25,2.5])
    S = st.slider("Carrera vástago (in)", 50, 200, 168)
    N = st.slider("SPM", 1, 20, 6)

# ======================
# BASE DE VARILLAS
# ======================
rod_db = {
    "D":   {"UTS":115, "b":0.56},
    "KD":  {"UTS":115, "b":0.56},
    "K":   {"UTS":110, "b":0.56},
    "DA78":{"UTS":140, "b":0.50},
    "HS97":{"UTS":160, "b":0.45}
}

areas = {"1":0.786,"7/8":0.601,"3/4":0.442}
peso  = {"1":2.90,"7/8":2.22,"3/4":1.63}

# ======================
# SELECCIÓN ACERO
# ======================
st.subheader("Selección de acero")

col1, col2, col3 = st.columns(3)

rod_type = {
    "1": col1.selectbox('1"', list(rod_db.keys())),
    "7/8": col2.selectbox('7/8"', list(rod_db.keys())),
    "3/4": col3.selectbox('3/4"', list(rod_db.keys()))
}

def goodman(smin, rod):
    return rod_db[rod]["UTS"] + rod_db[rod]["b"] * smin

# ======================
# CONVERSIONES
# ======================
L_ft = L_m * 3.28084

# ======================
# CARGAS
# ======================
A = np.pi * D**2 / 4
Fo = 0.433 * G * L_ft * A

W_total = L_ft * 2.3
Wri = W_total * (1 - 0.128 * G)

ratio = Fo/(Fo+12000)
f_speed = min(N/10,1)
f_stroke = (S/100)**0.8

Fi = Fo*(2.0 - 1.2*ratio)*f_stroke
F2 = Fo*(0.5 + 0.2*ratio)*f_speed*f_stroke

PPRL = Wri + Fi
MPRL = Wri - F2

# ======================
# TABLA EDITABLE
# ======================
st.subheader("Definición de sarta")

df_input = pd.DataFrame({
    "Diámetro":["1","7/8","3/4"],
    "Varillas":[80,80,80]
})

df_edit = st.data_editor(df_input, num_rows="fixed", use_container_width=True)

# ======================
# RECONSTRUIR LONGITUD
# ======================
L1 = df_edit.loc[0,"Varillas"]*25
L78 = df_edit.loc[1,"Varillas"]*25
L34 = df_edit.loc[2,"Varillas"]*25

total = L1 + L78 + L34

pct = {
    "1":L1/total,
    "7/8":L78/total,
    "3/4":L34/total
}

# ======================
# EVALUACIÓN
# ======================
def evaluar(pct):

    L1 = pct["1"]*L_ft
    L78 = pct["7/8"]*L_ft

    W1 = L1*peso["1"]
    W78 = L78*peso["7/8"]

    W_up = {"1":0,"7/8":W1,"3/4":W1+W78}
    beta = {"1":1.0,"7/8":0.7,"3/4":0.4}

    res={}

    for d in pct:

        Pmax = PPRL - W_up[d]
        Pmin = max(MPRL - beta[d]*W_up[d],0)

        Smax = Pmax/areas[d]/1000
        Smin = Pmin/areas[d]/1000

        Sadm = goodman(Smin, rod_type[d])

        G = ((Smax-Smin)/(Sadm-Smin))*100

        res[d]={
            "Pmax":Pmax,
            "Pmin":Pmin,
            "Smax":Smax,
            "Smin":Smin,
            "G":G,
            "L":pct[d]*L_ft,
            "n":int(pct[d]*L_ft/25)
        }

    return res

res = evaluar(pct)

# ======================
# TOTAL VARILLAS
# ======================

