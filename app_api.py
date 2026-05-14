import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("Diseño SRP + Goodman + Cartas dinamométricas (calibrado QRod)")

# ======================
# INPUTS
# ======================
c1,c2 = st.columns(2)

with c1:
    L_m = st.number_input("Profundidad (m)",500,5000,1800)
    H_m = st.number_input("Nivel dinámico (m)",100,4000,1500)
    G = st.slider("Gravedad específica",0.6,1.2,0.95)

with c2:
    D = st.selectbox("Diámetro bomba (in)",[1.5,1.75,2,2.25,2.5,2.75,3.5])
    N = st.slider("SPM",1,20,8)
    S = st.slider("Carrera vástago superficie (in)",50,200,100)

# ======================
# PROPIEDADES
# ======================
areas = {"1":0.786,"7/8":0.601,"3/4":0.442}
peso  = {"1":2.90,"7/8":2.22,"3/4":1.63}

UTS = 30
b = 0.5625

def goodman(smin):
    return UTS + b*smin

# ======================
# CONVERSIONES
# ======================
L_ft = L_m * 3.28084
H_ft = H_m * 3.28084

# ======================
# CARGA FLUIDO
# ======================
A_pump = np.pi * D**2 / 4
Fo = 0.433 * G * H_ft * A_pump

# ======================
# PESO VARILLAS
# ======================
W = L_ft * 2.3
Wri = W * (1 - 0.128 * G)

# ======================
# RIGIDEZ (aprox)
# ======================
kr = 200 + 400*(1/(L_ft/5000 + 1))

# ======================
# FACTOR ELASTICO
# ======================
FoSkr = Fo / (kr * S)

# ======================
# DINAMICA (CALIBRADA)
# ======================
Fi = Fo * (2.2 - 1.6 * FoSkr)
F2 = Fo * (0.4 + 0.5 * FoSkr)

PPRL = Wri + Fi
MPRL = Wri - F2

# ======================
# STRETCH Y CARRERA BOMBA
# ======================
Stretch = PPRL / kr
Overtravel = Fi / kr

Sp = S - Stretch - Overtravel
Sp = max(Sp, 0)

# ======================
# OUTPUT CARGAS
# ======================
st.subheader("Cargas")

cA,cB,cC,cD = st.columns(4)
cA.metric("PPRL",f"{PPRL:,.0f} lb")
cB.metric("MPRL",f"{MPRL:,.0f} lb")
cC.metric("Fo",f"{Fo:,.0f} lb")
cD.metric("Fo/Skr",f"{FoSkr:.3f}")

# ======================
# CARRERAS
# ======================
st.subheader("Carreras")

c1,c2,c3 = st.columns(3)
c1.metric("Stroke superficie",f"{S:.1f} in")
c2.metric("Stroke bomba",f"{Sp:.1f} in")
c3.metric("Stretch total",f"{Stretch:.1f} in")

# ======================
# DISTRIBUCION
# ======================
pct = {"1":0.35,"7/8":0.40,"3/4":0.25}

# ======================
# EVALUACION VARILLAS
# ======================
def evaluar(pct):

    L1 = pct["1"]*L_ft
    L78 = pct["7/8"]*L_ft
    L34 = pct["3/4"]*L_ft

    W1 = L1*peso["1"]
    W78 = L78*peso["7/8"]
    W34 = L34*peso["3/4"]

    Pmax = {
        "1": PPRL,
        "7/8": PPRL - W1,
        "3/4": PPRL - (W1 + W78)
    }

    Pmin = {
        "1": MPRL,
        "7/8": MPRL + 0.2*W34,
        "3/4": MPRL + 0.4*W34
    }

    res = {}

    for d in pct:
        Smax = Pmax[d]/areas[d]/1000
        Smin = Pmin[d]/areas[d]/1000

        Sadm = goodman(Smin)
        g = ((Smax - Smin)/(Sadm - Smin))*100

        res[d] = {"Smin":Smin,"Smax":Smax,"g":g}

    return res

res = evaluar(pct)

# ======================
# RESULTADOS
# ======================
st.subheader("Resultados por tramo")

for d in res:
    c1,c2,c3 = st.columns(3)
    c1.write(f'{d}" Smin: {res[d]["Smin"]:.1f} ksi')
    c2.write(f'{d}" Smax: {res[d]["Smax"]:.1f} ksi')
    c3.write(f'Goodman: {res[d]["g"]:.1f}%')

# ======================
# GOODMAN
# ======================
st.subheader("Diagrama Goodman")

x = np.linspace(0,150,200)

fig_g, ax_g = plt.subplots()
ax_g.plot(x,goodman(x))
ax_g.plot(x,x,'--')

for d in res:
    ax_g.scatter(res[d]["Smin"],res[d]["Smax"],s=20)

ax_g.grid()
st.pyplot(fig_g)

# ======================
# CARTAS DINAMOMETRICAS
# ======================
st.subheader("Cartas dinamométricas")

theta = np.linspace(0,2*np.pi,200)

# superficie
x_sup = S/2*(1-np.cos(theta))
P_sup = MPRL + (PPRL - MPRL)*(1-np.cos(theta))/2
P_sup += 0.12*(PPRL-MPRL)*np.sin(theta)

# fondo
Sp_eff = max(Sp,1)
x_pump = (Sp_eff/S)*x_sup
P_pump = P_sup*(Sp_eff/S)*0.9

# ======================
# GRAFICOS
# ======================
col1,col2 = st.columns(2)

with col1:
    fig1, ax1 = plt.subplots()
    ax1.plot(x_sup,P_sup)
    ax1.set_title("Carta superficie",fontsize=10)
    ax1.set_xlabel("Posición (in)")
    ax1.set_ylabel("Carga (lb)")
    ax1.grid()
    st.pyplot(fig1)

with col2:
    fig2, ax2 = plt.subplots()
    ax2.plot(x_pump,P_pump)
    ax2.set_title("Carta fondo",fontsize=10)
    ax2.set_xlabel("Posición bomba (in)")
    ax2.set_ylabel("Carga (lb)")
    ax2.grid()
    st.pyplot(fig2)




