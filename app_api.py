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
# DISTRIBUCIÓN CORRECTA (según bomba)
# ======================
tabla_api = {
    1.5: {"diam": ["7/8","3/4"], "pct": [0.40,0.60]},
    1.75: {"diam": ["1","7/8","3/4"], "pct": [0.20,0.35,0.45]},
    2.0: {"diam": ["1","7/8","3/4"], "pct": [0.25,0.40,0.35]},
    2.25: {"diam": ["1","7/8","3/4"], "pct": [0.30,0.40,0.30]},
    2.5: {"diam": ["1","7/8","3/4"], "pct": [0.35,0.40,0.25]},
    2.75: {"diam": ["1","7/8","3/4"], "pct": [0.40,0.35,0.25]},
    3.5: {"diam": ["1","7/8"], "pct": [0.60,0.40]}
}

# ======================
# PROPIEDADES VARILLAS
# ======================
areas = {"3/4":0.442, "7/8":0.601, "1":0.786}
peso = {"3/4":1.63, "7/8":2.22, "1":2.90}

# ======================
# STRING
# ======================
L_ft = L_m * 3.28084
data = tabla_api[D]

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
# PESO Y CARGA
# ======================
W = sum(s["L"] * peso[s["diam"]] for s in string)
Wri = W * (1 - 0.128 * G)

H_ft = H_m * 3.28084
A_pump = np.pi * D**2 / 4

Fo = 0.433 * G * H_ft * A_pump

# dinámica simple (aproximada)
Fi = Fo * (1.1 + 0.01 * N)
F2 = Fo * 0.6

PPRL = Wri + Fi
MPRL = Wri - F2

# ======================
# GOODMAN CORRECTO
# ======================
UTS = 30
b = 0.5625
FS = 1

def goodman(smin):
    return (UTS + b * smin) * FS

# ======================
# RESULTADOS
# ======================
st.subheader("Distribución de varillas")

for s in string:
    st.write(f'{s["diam"]}" → {s["n"]} varillas')

# ======================
# CALCULO POR TRAMO
# ======================
st.subheader("Solicitaciones y % Goodman")

resultados = []

for s in string:

    A = areas[s["diam"]]

    Smax = PPRL / A / 1000
    Smin = MPRL / A / 1000

    Sadm = goodman(Smin)

    # % Goodman correcto
    if Sadm != Smin:
        goodman_pct = ((Smax - Smin)/(Sadm - Smin))*100
    else:
        goodman_pct = 0

    margen = Sadm - Smax

    resultados.append({
        "diam": s["diam"],
        "Smin": Smin,
        "Smax": Smax
    })

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(f'{s["diam"]}" Smin', f"{Smin:.1f} ksi")
    col2.metric(f'{s["diam"]}" Smax', f"{Smax:.1f} ksi")
    col3.metric("Sadm", f"{Sadm:.1f} ksi")
    col4.metric("% Goodman", f"{goodman_pct:.1f} %")

    if margen >= 0:
        st.success(f'{s["diam"]}" OK')
    else:
        st.error(f'{s["diam"]}" FALLA')

# ======================
# GRAFICO GOODMAN
# ======================
st.subheader("Diagrama Goodman DA78")

smin_vals = np.linspace(0,150,200)
sadm_vals = goodman(smin_vals)

fig, ax = plt.subplots(figsize=(7,4))

ax.plot(smin_vals, sadm_vals, label="DA78", linewidth=3)
ax.plot(smin_vals, smin_vals, 'k--')

for r in resultados:
    ax.scatter(r["Smin"], r["Smax"], s=80)
    ax.text(r["Smin"], r["Smax"], r["diam"])

ax.set_xlabel("Smin (ksi)")
ax.set_ylabel("Smax (ksi)")
ax.set_xlim(0,150)
ax.set_ylim(0,150)
ax.grid()
ax.legend()

plt.tight_layout()

st.pyplot(fig)

# ======================
# CARGAS
# ======================
st.subheader("Cargas")

c1, c2, c3 = st.columns(3)
c1.metric("PPRL", f"{PPRL:,.0f} lb")
c2.metric("MPRL", f"{MPRL:,.0f} lb")
c3.metric("Peso total", f"{W:,.0f} lb")
