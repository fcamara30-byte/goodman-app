import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

st.title("Diseño de Varillas API RP 11L + Goodman DA78")

# ======================
# INPUTS
# ======================
c1, c2 = st.columns(2)

with c1:
    L_m = st.number_input("Profundidad (m)", 500, 5000, 2000)
    H_m = st.number_input("Nivel dinámico (m)", 100, 4000, 1500)
    G = st.slider("Gravedad específica", 0.6, 1.2, 1.0)

with c2:
    D = st.selectbox("Diámetro de bomba (in)", [1.5,1.75,2,2.25,2.5,2.75,3.5])
    S = st.slider("Carrera (in)", 50, 200, 100)
    N = st.slider("SPM", 1, 20, 10)

# ======================
# TAPERS API REALES (simplificados desde tabla)
# ======================
tabla_api = {

    "76": {"diam": ["7/8", "3/4"], "pct": [0.7, 0.3]},
    
    "84": {"diam": ["1","7/8","3/4"], "pct": [0.30,0.40,0.30]},
    
    "85": {"diam": ["1","7/8","3/4"], "pct": [0.34,0.37,0.29]},
    
    "86": {"diam": ["1","7/8","3/4"], "pct": [0.40,0.35,0.25]},
    
    "96": {"diam": ["1","7/8"], "pct": [0.6,0.4]},
    
    "97": {"diam": ["1","7/8","3/4"], "pct": [0.45,0.35,0.20]}
}

rod_no = st.selectbox("Taper API (Rod Number)", list(tabla_api.keys()))

# ======================
# PROPIEDADES VARILLAS (API)
# ======================
areas = {"3/4":0.442, "7/8":0.601, "1":0.786}
peso = {"3/4":1.63, "7/8":2.22, "1":2.90}

# ======================
# STRING
# ======================
L_ft = L_m * 3.28084
data = tabla_api[rod_no]

varilla_largo = 25
string = []

for d, pct in zip(data["diam"], data["pct"]):

    L_seg = L_ft * pct
    n = int(L_seg / varilla_largo)

    string.append({
        "diam": d,
        "L": L_seg,
        "n": n
    })

# ======================
# PESO
# ======================
W = sum(s["L"] * peso[s["diam"]] for s in string)
Wri = W * (1 - 0.128 * G)

# ======================
# CARGA FLUIDO
# ======================
H_ft = H_m * 3.28084
A_pump = np.pi * D**2 / 4

Fo = 0.433 * G * H_ft * A_pump

# dinámica (provisional)
Fi = Fo * (1.1 + 0.01 * N)
F2 = Fo * 0.6

PPRL = Wri + Fi
MPRL = Wri - F2

# ======================
# GOODMAN DA78
# ======================
uts = 30
b = 0.5625

def goodman(smin):
    return uts + b * smin

# ======================
# RESULTADOS
# ======================
st.subheader("Distribución de varillas")

for s in string:
    st.write(f"{s['diam']}\" → {s['n']} varillas")

# ======================
# CALCULO POR TRAMO
# ======================
st.subheader("Solicitaciones y chequeo Goodman")

resultados = []

for s in string:

    A = areas[s["diam"]]

    Smax = PPRL / A / 1000
    Smin = MPRL / A / 1000

    Sadm = goodman(Smin)
    margen = Sadm - Smax

    resultados.append({
        "diam": s["diam"],
        "Smin": Smin,
        "Smax": Smax,
        "Sadm": Sadm
    })

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(f'{s["diam"]}" Smin', f"{Smin:.1f}")
    col2.metric(f'{s["diam"]}" Smax', f"{Smax:.1f}")
    col3.metric("Sadm", f"{Sadm:.1f}")

    if margen >= 0:
        col4.success("OK")
    else:
        col4.error("FALLA")

# ======================
# GRAFICO GOODMAN
# ======================
st.subheader("Diagrama Goodman DA78")

smin = np.linspace(0,150,200)
sadm = goodman(smin)

fig, ax = plt.subplots(figsize=(6,4))

ax.plot(smin, sadm, linewidth=3, label="DA78")
ax.plot(smin, smin, 'k--')

for r in resultados:
    ax.scatter(r["Smin"], r["Smax"], s=80, label=f'{r["diam"]}"')


