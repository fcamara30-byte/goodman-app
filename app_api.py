import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

st.title("Diseño automático de varillas API + Goodman DA78")

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
# PROPIEDADES
# ======================
areas = {"3/4":0.442, "7/8":0.601, "1":0.786}
peso = {"3/4":1.63, "7/8":2.22, "1":2.90}

# ======================
# GOODMAN
# ======================
UTS = 30
b = 0.5625
FS = 1

def goodman(smin):
    return (UTS + b * smin) * FS

# ======================
# CARGAS
# ======================
L_ft = L_m * 3.28084
H_ft = H_m * 3.28084

A_pump = np.pi * D**2 / 4
Fo = 0.433 * G * H_ft * A_pump

# peso aproximado
W = L_ft * 2.0
Wri = W * (1 - 0.128 * G)

Fi = Fo * (1.1 + 0.01 * N)
F2 = Fo * 0.6

PPRL = Wri + Fi
MPRL = Wri - F2

# ======================
# FUNCION % GOODMAN
# ======================
def calcular_goodman_pct(A):

    Smax = PPRL / A / 1000
    Smin = MPRL / A / 1000

    Sadm = goodman(Smin)

    if Sadm != Smin:
        pct = ((Smax - Smin)/(Sadm - Smin))*100
    else:
        pct = 0

    return Smin, Smax, Sadm, pct

# ======================
# OPTIMIZACION
# ======================
def optimizar():

    mejor = None
    error_min = 999

    for p1 in np.arange(0.2,0.65,0.05):
        for p2 in np.arange(0.2,0.55,0.05):

            p3 = 1 - p1 - p2

            if p3 < 0.1 or p3 > 0.6:
                continue

            pcts = [p1,p2,p3]
            diams = ["1","7/8","3/4"]

            valores = []

            for d in diams:
                _,_,_,g = calcular_goodman_pct(areas[d])
                valores.append(g)

            error = max(valores)-min(valores)

            if error < error_min:
                error_min = error
                mejor = pcts

    return mejor, error_min

# ======================
# DISTRIBUCION BASE
# ======================
tabla_base = {
    1.5: [0.0,0.4,0.6],
    1.75:[0.2,0.35,0.45],
    2.0: [0.25,0.40,0.35],
    2.25:[0.30,0.40,0.30],
    2.5: [0.35,0.40,0.25],
    2.75:[0.40,0.35,0.25],
    3.5: [0.6,0.4,0.0]
}

# ======================
# ACTIVAR OPTIMIZACION
# ======================
usar_auto = st.checkbox("Optimizar automáticamente")

if usar_auto:
    pct_opt, error = optimizar()
    pct = pct_opt
else:
    pct = tabla_base[D]

# ======================
# RESULTADOS
# ======================
st.subheader("Distribución de varillas")

diams = ["1","7/8","3/4"]

resultados = []

for d,p in zip(diams,pct):

    if p <= 0:
        continue

    L_tramo = L_ft * p
    n = int(L_tramo / 25)

    Smin,Smax,Sadm,g = calcular_goodman_pct(areas[d])

    resultados.append((d,Smin,Smax))

    col1,col2,col3,col4,col5 = st.columns(5)

    col1.metric(f'{d}" %', f"{p*100:.0f} %")
    col2.metric("Smin", f"{Smin:.1f} ksi")
    col3.metric("Smax", f"{Smax:.1f} ksi")
    col4.metric("Sadm", f"{Sadm:.1f} ksi")
    col5.metric("% Goodman", f"{g:.1f} %")

    if Smax <= Sadm:
        st.success(f'{d}" OK')
    else:
        st.error(f'{d}" FALLA')

# ======================
# BALANCE
# ======================
st.subheader("Balance del diseño")

g_vals = []

for d,p in zip(diams,pct):
    if p > 0:
        _,_,_,g = calcular_goodman_pct(areas[d])
        g_vals.append(g)

delta = max(g_vals) - min(g_vals)

if delta < 10:
    st.success(f"✔ Excelente balance Δ={delta:.1f}%")
elif delta < 20:
    st.warning(f"⚠ Aceptable Δ={delta:.1f}%")
else:
    st.error(f"❌ Desbalanceado Δ={delta:.1f}%")

# ======================
# GRAFICO
# ======================
st.subheader("Diagrama Goodman")

x = np.linspace(0,150,200)
y = goodman(x)

fig,ax = plt.subplots()

ax.plot(x,y,label="DA78",linewidth=3)
ax.plot(x,x,'k--')

for r in resultados:
    ax.scatter(r[1],r[2])
    ax.text(r[1],r[2],r[0])

ax.set_xlabel("Smin (ksi)")
ax.set_ylabel("Smax (ksi)")
ax.grid()
ax.legend()

st.pyplot(fig)

# ======================
# CARGAS
# ======================
st.subheader("Cargas")

c1,c2 = st.columns(2)
c1.metric("PPRL", f"{PPRL:,.0f} lb")
c2.metric("MPRL", f"{MPRL:,.0f} lb")

