import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("Calculo de Solicitaciones (Versión Beta)")

# ======================
# INPUTS
# ======================
c1,c2=st.columns(2)

with c1:
    L_m=st.number_input("Profundidad (m)",500,5000,1800)
    G=st.slider("Gravedad específica",0.6,1.2,0.95)

with c2:
    D=st.selectbox("Bomba (in)",[1.5,1.75,2,2.25,2.5])
    S=st.slider("Carrera (in)",50,200,168)
    N=st.slider("SPM",1,20,6)

# ======================
# MATERIALES
# ======================
materiales={
    "DA78":{"uts_a":30,"b":0.5625},
    "HS97":{"uts_a":50,"b":0.375},
    "CS propietario":{"uts_a":44.64,"b":0.375},
    "HS propietario":{"uts_a":55.36,"b":0.375},
    "D New":{"uts_a":42.86,"b":0.375},
    "DSK75":{"uts_a":42.86,"b":0.375},
    "HA96":{"uts_a":50,"b":0.375}
}

# ======================
# CORROSION
# ======================

