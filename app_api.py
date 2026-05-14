import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("SRP Diseño + Goodman (optimizado tipo QRod)")

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
# PROPIEDADES
# ======================
areas = {"1":0.786, "7/8":0.601, "3/4":0.442}
peso  = {"1":2.90, "7/8":2.22, "3/4":1.63}

UTS = 30
b = 0.5625

def goodman(smin):
    return UTS + b*smin

# ======================
# CONVERSIONES
# ======================
L_ft = L_m * 3.28084

# ======================
# FO REAL
# ======================
A_pump = np.pi * D**2 / 4
Fo = 0.433 * G * L_ft * A_pump

# ======================
# PESO
# ======================
W_total = L_ft * 2.3
Wri = W_total * (1 - 0.128 * G)

# ======================
# DINAMICA REALISTA
# ======================
ratio = Fo / (Fo + 12000)

f_speed = min(N/10,1)
f_stroke = S/100

Fi = Fo*(2.0 - 1.2*ratio) * f_stroke
F2 = Fo*(0.5 + 0.2*ratio) * f_speed * f_stroke

PPRL = Wri + Fi
MPRL = Wri - F2

# ======================
# INICIAL TAPER
# ======================
pct = {"1":0.33,"7/8":0.33,"3/4":0.34}

# ======================
# EVALUACION
# ======================
def evaluar(pct):

    L1 = pct["1"]*L_ft
    L78 = pct["7/8"]*L_ft

    W1 = L1*peso["1"]
    W78 = L78*peso["7/8"]

    W_up = {
        "1":0,
        "7/8":W1,
        "3/4":W1+W78
    }

    beta = {
        "1":1.0,
        "7/8":0.7,
        "3/4":0.4
    }

    res={}

    for d in pct:

        Pmax = PPRL - W_up[d]
        Pmin = MPRL - beta[d]*W_up[d]

        Pmin = max(Pmin,0)

        A = areas[d]

        Smax = Pmax/A/1000
        Smin = Pmin/A/1000

        Sadm = goodman(Smin)

        g = ((Smax - Smin)/(Sadm - Smin))*100

        res[d] = {
            "g":g,
            "Smax":Smax,
            "Smin":Smin,
            "Pmax":Pmax,
            "Pmin":Pmin
        }

    return res

# ======================
# OPTIMIZACION TAPER
# ======================
def optimizar(pct, n_iter=80):

    for _ in range(n_iter):

        res = evaluar(pct)

        g_vals = {d:res[d]["g"] for d in res}

        d_max = max(g_vals, key=g_vals.get)
        d_min = min(g_vals, key=g_vals.get)

        step = 0.01

        if pct[d_min] > 0.1:
            pct[d_min] -= step
            pct[d_max] += step

        total = sum(pct.values())
        for d in pct:
            pct[d] /= total

    return pct

pct = optimizar(pct)
res = evaluar(pct)

# ======================
# OUTPUT
# ======================
st.subheader("Cargas vástago")

c1,c2,c3 = st.columns(3)
c1.metric("PPRL",f"{PPRL:,.0f}")
c2.metric("MPRL",f"{MPRL:,.0f}")
c3.metric("Fo",f"{Fo:,.0f}")

# ======================
# RESULTADOS
# ======================
st.subheader("Resultados + taper optimizado")

for d in res:

    c1,c2,c3,c4,c5 = st.columns(5)

    c1.write(f'{d}"')
    c2.write(f"{pct[d]*100:.1f}%")
    c3.write(f"Smax {res[d]['Smax']:.1f}")
    c4.write(f"Smin {res[d]['Smin']:.1f}")
    c5.write(f"G {res[d]['g']:.1f}%")

# ======================
# CHEQUEO
# ======================
st.subheader("Balance Goodman")

gvals = [res[d]["g"] for d in res]

st.write(f"Min: {min(gvals):.1f}%")
st.write(f"Max: {max(gvals):.1f}%")
st.write(f"Δ: {(max(gvals)-min(gvals)):.1f}%")

# ======================
# GOODMAN
# ======================
st.subheader("Diagrama Goodman")

x = np.linspace(0,150,200)
y = goodman(x)

fig, ax = plt.subplots()

ax.plot(x,y,label="Goodman")
ax.plot(x,x,'--')

for d in res:
    ax.scatter(res[d]["Smin"], res[d]["Smax"])
    ax.text(res[d]["Smin"], res[d]["Smax"], d)

ax.set_xlabel("Smin")
ax.set_ylabel("Smax")

ax.grid()
ax.legend()

st.pyplot(fig)

