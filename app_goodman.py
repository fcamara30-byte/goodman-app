import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# ======================
# CONFIG
# ======================
st.set_page_config(layout="wide")

# ======================
# HEADER COMPACTO
# ======================
col_title, col_brand = st.columns([5,2])

with col_title:
    st.markdown("### Goodman – Fatiga y Corrosión")

with col_brand:
    st.markdown("#### *Powered by Apex*")

# ======================
# DATOS
# ======================
materiales = {
    "DA78": {"uts_a": 30.0, "b": 0.5625},
    "HS97": {"uts_a": 50.0, "b": 0.375},
    "CS propietario": {"uts_a": 44.64, "b": 0.375},
    "HS propietario": {"uts_a": 55.36, "b": 0.375},
    "D New": {"uts_a": 42.86, "b": 0.357},
}

CO2 = {"Nada":1.0,"Bajo":1.0,"Medio":0.9,"Alto":0.8}
H2S = {"Nada":1.0,"Bajo":0.95,"Medio":0.8,"Alto":0.75}

# BSR con 0 primero ✅
BSR = {
