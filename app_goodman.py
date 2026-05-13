import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

materiales = {
    "DA78": {"uts_a": 30.0, "b": 0.5625},
    "HS97": {"uts_a": 50.0, "b": 0.375},
    "Alpha CS": {"uts_a": 44.64, "b": 0.375},
    "Alpha HS": {"uts_a": 55.36, "b": 0.375},
    "D New": {"uts_a": 42.86, "b": 0.357},
}

CO2 = {"Nada":1.0,"Bajo":1.0,"Medio":0.9,"Alto":0.8}
H2S = {"Nada":1.0,"Bajo":0.95,"Medio":0.8,"Alto":0.75}
BSR = {"0":1.0,"1":1.0,"2":0.95,"3":0.9,"4":0.82,"5":0.74,"6":0.65}

def goodman(smin, uts_a, b, f):
    return (uts_a + b*smin)*f

st.title("Goodman Tool")

material = st.selectbox("Material", list(materiales.keys()))
co2 = st.selectbox("CO2", list(CO2.keys()))
h2s = st.selectbox("H2S", list(H2S.keys()))
bsr = st.selectbox("BSR", list(BSR.keys()))

smin_user = st.slider("Smin",0,150,30)
smax_user = st.slider("Smax",0,150,50)

f = CO2[co2]*H2S[h2s]*BSR[bsr]

uts_a = materiales[material]["uts_a"]
b = materiales[material]["b"]

smin = np.linspace(0,150,200)

fig, ax = plt.subplots()

