import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

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
    S = st.slider("Carrera (in)", 50, 200, 168)
    N = st.slider("SPM", 1, 20, 6)

# ======================
# MATERIALES REALES
# ======================
rod_db = {
    "D": {"UTS":115,"b":0.56},
    "KD": {"UTS":115,"b":0.56},
    "DSK75": {"UTS":120,"b":0.55},
    "HS Prop": {"UTS":150,"b":0.48}
}

st.subheader("Selección de acero")

col1, col2, col3 = st.columns(3)

rod_type = {
    "1": col1.selectbox('1"', list(rod_db.keys())),
    "7/8": col2.selectbox('7/8"', list(rod_db.keys())),
    "3/4": col3.selectbox('3/4"', list(rod_db.keys()))
}

def goodman(smin, d):
    mat = rod_db[rod_type[d]]
    return mat["UTS"] + mat["b"]*smin

# ======================
# PROPIEDADES
# ======================
areas = {"1":0.786,"7/8":0.601,"3/4":0.442}
peso  = {"1":2.90,"7/8":2.22,"3/4":1.63}

# ======================
# CARGAS
# ======================
L_ft = L_m * 3.28084

A = np.pi*D**2/4
Fo = 0.433*G*L_ft*A


