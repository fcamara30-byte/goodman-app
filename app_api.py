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
    D = st.slider("Diámetro bomba (in)", 1.0, 3.0, 1.5)
    S = st.slider("Carrera (in)", 50, 200, 100)
    N = st.slider("SPM", 1, 20, 10)

# ======================
# TABLA API (EJEMPLO REAL)
# 🔴 ACA TENES QUE COMPLETAR CON LA 4.1
# ======================
tabla_api = {
    "85": {
        "diametros": ["1", "7/8", "3/4"],
        "porcentajes": [0.34, 0.37, 0.29]
    },
    "76": {
        "diametros": ["7/8", "3/4"],
        "porcentajes": [0.70, 0.30]
    }
}

rod_no = st.selectbox("Rod Number (API Table 4.1)", list(tabla_api.keys()))

# ======================
# PROPIEDADES VARILLAS (TABLA 4.3 API)
# ======================
areas = {
    "3/4": 0.442,
    "7/8": 0.601,
    "1": 0.786
}

peso = {
    "3/4": 1.63,
    "7/8": 2.22,
    "1": 2.90
}

# ======================
# CALCULO STRING
# ======================
L_ft = L_m * 3.28084

data = tabla_api[rod_no]

varilla_largo = 25  # ft
string = []

for d, frac in zip(data["diametros"], data["porcentajes"]):

    L_seg = L_ft * frac
    n = int(L_seg / varilla_largo)

    string.append({
        "diam": d,
        "L": L_seg,
        "n": n
    })

# ======================
# PESO TOTAL
# ======================
W = sum(s["L"] * peso[s["diam"]] for s in string)
Wri = W * (1 - 0.128 * G)

# ======================
# CARGA DE FLUIDO
# ======================
H_ft = H_m * 3.28084
A_pump = np.pi * (D**2) / 4

Fo = 0.433 * G * H_ft * A_pump

# ======================
# DINAMICA (aprox inicial)
# ======================
Fi = Fo * (1.1 + 0.01 * N)
F2 = Fo * 0.6

PPRL = Wri + Fi
MPRL = Wri - F2

# ======================
# GOODMAN DA78
# ======================
uts = 30
b = 0.5625
fs = 1

def goodman(smin):
    return (uts + b * smin) * fs

# ======================
# RESULTADOS
# ======================
st.subheader("Distribución real de varillas")

for s in string:
    st.write(f"{s['diam']}\" → {s['n']} varillas")

st.subheader("Evaluación por tramo (Goodman DA78)")

resultados = []

for s in string:

    A = areas[s["diam"]]

    Smax = PPRL / A / 1000
    Smin = MPRL / A / 1000

    Sadm = goodman(Smin)

    resultados.append((s["diam"], Smin, Smax))

    if Smax <= Sadm:
        st.success(f"{s['diam']}\" OK | Smax={Smax:.1f} ksi")
    else:
        st.error(f"{s['diam']}\" FALLA | Smax={Smax:.1f} ksi")

# ======================
# GRAFICO GOODMAN
# ======================
st.subheader("Diagrama de Goodman – DA78")

smin = np.linspace(0,150,200)
sadm_curve = goodman(smin)

fig, ax = plt.subplots(figsize=(6,4))

ax.plot(smin, sadm_curve, linewidth=3, label="DA78")
ax.plot(smin, smin, 'k--')

for r in resultados:
    ax.scatter(r[1], r[2], label=f'{r[0]}"', s=80)

ax.set_xlim(0,150)
ax.set_ylim(0,150)

ax.set_xlabel("Smin (ksi)")
ax.set_ylabel("Smax (ksi)")
ax.grid()
ax.legend()

st.pyplot(fig)

# ======================
# OUTPUT CARGAS
# ======================
st.subheader("Cargas")

c1, c2, c3 = st.columns(3)
c1.metric("PPRL (lb)", f"{PPRL:,.0f}")
c2.metric("MPRL (lb)", f"{MPRL:,.0f}")
c3.metric("Peso varillas (lb)", f"{W:,.0f}")
