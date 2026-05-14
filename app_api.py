import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

st.title("Diseño API RP 11L + Goodman (DA78)")

# ======================
# INPUTS
# ======================
c1, c2 = st.columns(2)

with c1:
    L_m = st.number_input("Profundidad (m)", 500, 5000, 2000)
    H_m = st.number_input("Nivel dinámico (m)", 100, 4000, 1500)
    G = st.slider("Gravedad específica", 0.6, 1.2, 1.0)

with c2:
    D = st.selectbox("Diámetro bomba (in)", [1.5,1.75,2,2.25,2.5,2.75,3.5])
    S = st.slider("Carrera (in)", 50, 200, 100)
    N = st.slider("SPM", 1, 20, 10)

# ======================
# DISTRIBUCION SEGUN DIAMETRO (CORREGIDA)
# ======================
tabla_api = {

    1.5: {"diam": ["7/8","3/4"], "pct": [0.40,0.60]},
    1.75: {"diam": ["1","7/8","3/4"], "pct": [0.20,0.35,0.45]},
    2.0: {"diam": ["1","7/8","3/4"], "pct": [0.25,0.40,0.35]},
    2.25: {"diam": ["1","7/8","3/4"], "pct": [0.30,0.40,0.30]},
    2.5: {"diam": ["1","7/8","3/4"], "pct": [0.35,0.40,0.25]},
    2.75: {"diam": ["1","7/8","3/4"], "pct": [0.40,0.35,0.25]},
    3.5: {"diam": ["1","7/8"], "pct": [0.60,0.40]}


# ======================
# PROPIEDADES VARILLAS
# ======================
areas = {"3/4":0.442
