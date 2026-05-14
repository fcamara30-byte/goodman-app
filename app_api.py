import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

st.title("Diseño API RP 11L + Goodman DA78")

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
# TAPERS API
# ======================
tabla_api = {
    "76": {"diam": ["7/8", "3/4"], "pct": [0.7, 0.3]},
    "84": {"diam": ["1","7/8","3/4"], "pct": [0.30,0.40,0.30]},
    "85": {"diam": ["1","7/8","3/4"], "pct": [0.34,0.37,0.29]},
    "86": {"diam": ["1","7/8","3/4"], "pct": [0.40,0.35,0.25]},
    "96": {"diam": ["1","7/8"], "pct": [0.6,0.4]},
    "97": {"diam": ["1","7/8","3/4"], "pct": [0.45,0.35,0.20]}
}

rod_no = st.selectbox("Taper API", list(tabla_api.keys()))

# ======================
# PROPIEDADES
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
# PESO Y CARGA
# ======================
W = sum(s["L"] * peso[s["diam"]] for s in string)
Wri = W * (1 - 0.128 * G)

H_ft = H_m * 3.28084
A_pump = np.pi * D**2 / 4

Fo = 0.433 * G * H_ft * A_pump

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
    return (UTS + b * smin) * FS   # ✅ CORRECTO

# ======================
# RESULTADOS
# ======================
st.subheader("Distribución de varillas")

for s in string:
    st.write(f"{s['diam']}\" → {s['n']} varillas")

# ======================
# CALCULO POR TRAMO
# ======================
st.subheader("Solicitaciones y Goodman")

resultados = []

for s in string:

    A = areas[s["diam"]]

    Smax = PPRL / A / 1000
    Smin = MPRL / A / 1000

    Sadm = goodman(Smin)
    margen = Sadm - Smax

    resultados.append((s["diam"], Smin, Smax))

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(f'{s["diam"]}" Smin', f"{Smin:.1f}")
    c2.metric(f'{s["diam"]}" Smax', f"{Smax:.1f}")
    c3.metric("Sadm", f"{Sadm:.1f}")

    if margen >= 0:
        c4.success("OK")
    else:
        c4.error("FALLA")

# ======================
# GRAFICO GOODMAN
# ======================
st.subheader("Diagrama Goodman DA78")

smin_curve = np.linspace(0,150,200)
sadm_curve = goodman(smin_curve)

fig, ax = plt.subplots(figsize=(7,4))

ax.plot(smin_curve, sadm_curve, label="Goodman DA78", linewidth=3)
ax.plot(smin_curve, smin_curve, 'k--')

for r in resultados:
    ax.scatter(r[1], r[2], s=80, label=f'{r[0]}"')

ax.set_xlim(0,150)
ax.set_ylim(0,150)

ax.set_xlabel("Smin (ksi)")
ax.set_ylabel("Smax (ksi)")
ax.grid()
ax.legend()

plt.tight_layout()

st.pyplot(fig)

# ======================
# CARGAS
# ======================
st.subheader("Cargas")

c1, c2, c3 = st.columns(3)
c1.metric("PPRL (lb)", f"{PPRL:,.0f}")
c2.metric("MPRL (lb)", f"{MPRL:,.0f}")
c3.metric("Peso varillas (lb)", f"{W:,.0f}")
