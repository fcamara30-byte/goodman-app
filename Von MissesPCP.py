import streamlit as st
import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

# =========================
# UI COMPACTA REAL
# =========================
st.markdown("""
<style>
/* reduce ancho inputs */
div[data-testid="stNumberInput"] {
    width: 140px;
}
/* reduce ancho columnas tabla */
[data-testid="stDataFrameContainer"] div {
    font-size: 12px;
}
</style>
""", unsafe_allow_html=True)

st.title("PCP + Sarta (Von Mises - Ingeniería)")

# =========================
# INPUTS
# =========================
col1, col2 = st.columns(2)

with col1:
    profundidad = st.number_input("Prof (m)", 600, step=100)
    rpm = st.number_input("RPM", 350)
    prod = st.number_input("Prod (m3/d)", 150.0)
    pres_linea = st.number_input("P línea", 14.1)
    nivel = st.number_input("Nivel", 570, step=50)
    densidad = st.number_input("Densidad", 840.0)
    eficiencia = st.number_input("Eficiencia", 0.6)

with col2:
    viscosidad = st.number_input("Visc (cP)", 300, step=40)
    solidos = st.number_input("% sólidos", 5.0)
    rod = st.selectbox("Varilla", ["7/8", "1", "1 1/8"])
    material = st.selectbox("Material",
        ["DA 78","HS97","Alpha CS","Alpha HS","D New","DSK75","HA96"]
    )

# =========================
# DATA
# =========================
RODS = {
    "7/8": {"d":0.875,"peso":2.22},
    "1": {"d":1.0,"peso":2.67},
    "1 1/8": {"d":1.125,"peso":3.37}
}

YIELD = {
    "DA 78":85,"HS97":115,"Alpha CS":110,
    "Alpha HS":135,"D New":85,"DSK75":85,"HA96":115
}

# =========================
# CALCULO BASE
# =========================
pres_nivel = (nivel*densidad)/10000
pres_total = pres_linea + pres_nivel

pot_h = prod * pres_total * 0.0014
pot_c = pot_h / eficiencia

torque = (5252 * pot_c) / rpm

f_fluido = (1+viscosidad/1000)*(1+solidos/100)
torque *= f_fluido

# varilla
d = RODS[rod]["d"]*0.0254
r = d/2

A = math.pi*d**2/4
J = math.pi*d**4/32

peso = RODS[rod]["peso"]*47.88
F = peso*profundidad + densidad*9.81*profundidad*A

sigma = (F/A)/6894757
tau = ((torque*1.35582*r)/J)/6894757

von = math.sqrt(sigma**2 + 3*tau**2)

YS = YIELD[material]
uso = von/YS*100
fs = YS/von

# =========================
# RESULTADOS
# =========================
st.markdown("---")

c1,c2,c3 = st.columns(3)
c1.metric("Torque", f"{torque:.1f}")
c2.metric("Axial (ksi)", f"{sigma:.2f}")
c3.metric("Torsión (ksi)", f"{tau:.2f}")

c4,c5,c6 = st.columns(3)
c4.metric("Von Mises", f"{von:.2f}")
c5.metric("% uso", f"{uso:.1f}")
c6.metric("FS", f"{fs:.2f}")

# =========================
# MODO POZO
# =========================
st.markdown("---")
modo = st.selectbox("Trayectoria", ["Vertical","Desviado"])

if modo == "Desviado":

    st.subheader("Pegar trayectoria (md inc az)")

    text = st.text_area(
        "Copiar desde Excel",
        height=150,
        placeholder="5 0 0\n165 2.25 192\n199 2.75 187"
    )

    df = pd.DataFrame(columns=["md","inc","az"])

    if text:
        rows = text.strip().split("\n")
        data = []

        for riga in rows:
            vals = riga.replace(",",".").split()
            if len(vals)>=3:
                try:
                    data.append([float(vals[0]),float(vals[1]),float(vals[2])])
                except:
                    pass

        df = pd.DataFrame(data, columns=["md","inc","az"])

    if len(df)>1:

        # -------------------------
        # DLS
        # -------------------------
        dls=[0]

        for i in range(1,len(df)):
            inc1,inc2=np.radians(df["inc"][i-1]),np.radians(df["inc"][i])
            az1,az2=np.radians(df["az"][i-1]),np.radians(df["az"][i])

            dmd=(df["md"][i]-df["md"][i-1])*3.28084

            cosdl = np.sin(inc1)*np.sin(inc2)*np.cos(az2-az1)+np.cos(inc1)*np.cos(inc2)
            cosdl = np.clip(cosdl,-1,1)

            dl = np.degrees(np.arccos(cosdl))*100/dmd
            dls.append(dl)

        df["DLS"]=dls

        # -------------------------
        # POSICION 3D
        # -------------------------
        inc_rad=np.radians(df["inc"])
        az_rad=np.radians(df["az"])

        df["X"]=np.cumsum(np.sin(inc_rad)*np.cos(az_rad))
        df["Y"]=np.cumsum(np.sin(inc_rad)*np.sin(az_rad))
        df["Z"]=-df["md"]

        # -------------------------
        # CONTACTO
        # -------------------------
        carga = RODS[rod]["peso"]*np.sin(inc_rad)*df["md"]*0.05

        col=[]
        rec=[]

        for c in carga:
            if c<30: col.append("green"); rec.append("Bajo")
            elif c<60: col.append("yellow"); rec.append("1 cen")
            elif c<100: col.append("orange"); rec.append("3 cen")
            else: col.append("red"); rec.append("Black M")

        df["Carga"]=carga
        df["Rec"]=rec

        # torque corregido
        t_dev = torque*(1+np.mean(np.sin(inc_rad))*0.4)

        st.write("Torque desviado:", round(t_dev,1),"lb-ft")

        # -------------------------
        # GRAFICO 3D
        # -------------------------
        fig = plt.figure()
        ax = fig.add_subplot(111,projection='3d')

        ax.scatter(df["X"],df["Y"],df["Z"],c=col,s=30)

        ax.set_title("Trayectoria 3D")
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_zlabel("TVD")

        st.pyplot(fig)

        # tabla compacta
        st.dataframe(df[["md","inc","az","DLS","Carga","Rec"]],
                     use_container_width=True)
