import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("SRP – Modelo simplificado corregido")

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
    S = st.slider("Carrera superficie (in)",50,200,100)

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
L_ft = L_m*3.28084
H_ft = H_m*3.28084

# ======================
# CARGA FLUIDO
# ======================
A_pump = np.pi * D**2/4
Fo = 0.433 * G * H_ft * A_pump

# ======================
# PESO
# ======================
W = L_ft * 2.3
Wri = W*(1-0.128*G)

# ======================
# DINAMICA (ESTABLE)
# ======================
ratio = Fo / (Fo + 12000)

Fi = Fo*(2.0 - 1.2*ratio)
F2 = Fo*(0.5 + 0.2*ratio)

PPRL = Wri + Fi
MPRL = Wri - F2

# ======================
# OUTPUT
# ======================
st.subheader("Cargas")

c1,c2,c3 = st.columns(3)
c1.metric("PPRL",f"{PPRL:,.0f} lb")
c2.metric("MPRL",f"{MPRL:,.0f} lb")
c3.metric("Fo",f"{Fo:,.0f} lb")

# ======================
# GOODMAN (SIMPLE BIEN)
# ======================
st.subheader("Goodman por diámetro")

for d in ["1","7/8","3/4"]:

    A = areas[d]

    Smax = PPRL/A/1000
    Smin = MPRL/A/1000

    Sadm = goodman(Smin)
    g = ((Smax-Smin)/(Sadm-Smin))*100

    c1,c2,c3 = st.columns(3)
    c1.write(f'{d}" Smin: {Smin:.1f} ksi')
    c2.write(f'{d}" Smax: {Smax:.1f} ksi')
    c3.write(f'Goodman: {g:.1f}%')

# ======================
# GOODMAN GRAFICO
# ======================
st.subheader("Diagrama Goodman")

x = np.linspace(0,150,200)

fig,ax = plt.subplots()
ax.plot(x,goodman(x))
ax.plot(x,x,'--')

for d in ["1","7/8","3/4"]:
    ax.scatter(MPRL/areas[d]/1000, PPRL/areas[d]/1000, s=20)

ax.grid()
st.pyplot(fig)

# ======================
# CARTAS REALISTAS
# ======================
st.subheader("Cartas dinamométricas (corregidas)")

x = np.linspace(0, S, 200)

# 📌 superficie (forma física)
P_up = np.linspace(MPRL, PPRL, 100)
P_down = np.linspace(PPRL*0.9, MPRL*1.05, 100)

x_up = np.linspace(0, S, 100)
x_down = np.linspace(S, 0, 100)

x_surf = np.concatenate([x_up, x_down])
P_surf = np.concatenate([P_up, P_down])

# 📌 fondo (suavizado y menor carga)
P_downhole = P_surf * 0.75

# ======================
# PLOTS
# ======================
col1,col2 = st.columns(2)

with col1:
    fig1, ax1 = plt.subplots()
    ax1.plot(x_surf,P_surf)
    ax1.set_title("Carta superficie")
    ax1.set_xlabel("Stroke (in)")
    ax1.set_ylabel("Carga (lb)")
    ax1.grid()
    st.pyplot(fig1)

with col2:
    fig2, ax2 = plt.subplots()
    ax2.plot(x_surf,P_downhole)
    ax2.set_title("Carta fondo")
    ax2.set_xlabel("Stroke (in)")
    ax2.set_ylabel("Carga (lb)")
    ax2.grid()
    st.pyplot(fig2)



