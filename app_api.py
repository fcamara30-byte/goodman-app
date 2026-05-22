import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

st.set_page_config(layout="wide")

# ======================
# INPUTS
# ======================
c1,c2,c3,c4 = st.columns(4)

L_m = c1.number_input("Longitud pozo (m)",500,5000,1800)
G   = c2.slider("Gravedad específica",0.6,1.2,0.95)
D   = c3.selectbox("Bomba (in)",[1.5,1.75,2,2.25,2.5,2.75,3.25])

with c4:
    N = st.slider("SPM", 1, 10, 6)

c_slider, col_box = st.columns([2,3])

with c_slider:
    S = st.slider("Carrera (in)", 0, 300, 168)

# ======================
# VARILLAS
# ======================
total_varillas = int((L_m / 0.3048) / 25)

n1_def = total_varillas // 3
n78_def = total_varillas // 3
n34_def = total_varillas - n1_def - n78_def

col1, col2, col3 = st.columns(3)

with col1:
    n1 = st.number_input('1"', 10, 300, n1_def)

with col2:
    n78 = st.number_input('7/8"', 10, 300, n78_def)

with col3:
    n34 = st.number_input('3/4"', 10, 300, n34_def)

L1,L78,L34=n1*25,n78*25,n34*25
L_total_ft = L1+L78+L34

# ======================
# FUNCIONES
# ======================
E = 30_000_000

areas={"1":0.786,"7/8":0.601,"3/4":0.442}
peso={"1":3.1,"7/8":2.5,"3/4":1.7}

def calc_kr(L1, L78, L34):
    term = (L1/areas["1"]) + (L78/areas["7/8"]) + (L34/areas["3/4"])
    return E / (term * 12)

def calc_No(L_total_ft):
    return (16300 * 1.1) / (4 * L_total_ft) * 60

def interp_2d(x, y, x_vals, y_vals, z):

    x = np.clip(x, x_vals[0], x_vals[-1])
    y = np.clip(y, y_vals[0], y_vals[-1])

    i = np.searchsorted(x_vals, x) - 1
    j = np.searchsorted(y_vals, y) - 1

    i = np.clip(i, 0, len(x_vals)-2)
    j = np.clip(j, 0, len(y_vals)-2)

    x1,x2 = x_vals[i],x_vals[i+1]
    y1,y2 = y_vals[j],y_vals[j+1]

    Q11=z[i][j]
    Q12=z[i][j+1]
    Q21=z[i+1][j]
    Q22=z[i+1][j+1]

    return (
        Q11*(x2-x)*(y2-y)+
        Q21*(x-x1)*(y2-y)+
        Q12*(x2-x)*(y-y1)+
        Q22*(x-x1)*(y-y1)
    )/((x2-x1)*(y2-y1))

# ======================
# CURVAS API (RECONSTRUIDAS)
# ======================

Fo_vals = np.array([0.1,0.2,0.4,0.5])
N_vals  = np.array([0.1,0.2,0.3,0.4,0.5,0.6])

F1_table = np.array([
    [0.25,0.32,0.40,0.50,0.65,0.85],
    [0.25,0.33,0.42,0.50,0.66,0.90],
    [0.45,0.52,0.60,0.70,0.85,1.05],
    [0.555,0.63,0.69,0.80,0.90,1.10]
])

F2_table = np.array([
    [0.03,0.09,0.17,0.26,0.34,0.40],
    [0.04,0.10,0.18,0.26,0.35,0.42],
    [0.05,0.12,0.20,0.27,0.36,0.44],
    [0.06,0.13,0.22,0.30,0.38,0.47]
])

# ======================
# MODELO
# ======================

Wr_air = L1*peso["1"] + L78*peso["7/8"] + L34*peso["3/4"]
Wr = Wr_air*(1-0.128*G)

Ap = np.pi * D**2 / 4
Fo = 0.433 * G * L_total_ft * Ap

kr = calc_kr(L1,L78,L34) * 1.6   # ✅ CORRECCIÓN CRÍTICA

Skr = kr * S

Fo_Skr = Fo / Skr

No = calc_No(L_total_ft)
N_ratio = N / No

F1_Skr = interp_2d(Fo_Skr,N_ratio,Fo_vals,N_vals,F1_table)
F2_Skr = interp_2d(Fo_Skr,N_ratio,Fo_vals,N_vals,F2_table)

PPRL = Wr + F1_Skr * Skr
MPRL = Wr - F2_Skr * Skr

# ======================
# OUTPUT
# ======================

st.write("Fo/Skr:", round(Fo_Skr,3))
st.write("N/No:", round(N_ratio,3))
st.write("F1:", round(F1_Skr,3))
st.write("F2:", round(F2_Skr,3))

col1,col2 = st.columns(2)

with col1:
    st.metric("PPRL", int(PPRL))

with col2:
    st.metric("MPRL", int(MPRL))
