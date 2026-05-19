import streamlit as st
import numpy as np
import math
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("PCP + Sarta – Modelo Ingeniería")

colL, colR = st.columns([2,2])

# =========================
# INPUTS
# =========================
with colL:

    profundidad = st.number_input("Profundidad [m]", 0, 3000, 1000, 100)

    rpm = st.number_input("RPM", 50, 500, 350)

    prod = st.number_input("Producción [m3/d]", value=150)

    pres_linea = st.number_input("Presión línea [kg/cm²]", value=14)

    nivel = st.number_input("Nivel dinámico [m]", value=500)

    sumergencia = st.number_input("Sumergencia [m]", value=200)

    densidad = st.number_input("Densidad [kg/m3]", 600, 1200, 850, 50)

    eficiencia = st.number_input("Eficiencia [-]", value=0.6)

    viscosidad = st.number_input("Viscosidad [cP]", 0, 2000, 300, 50)

    solidos = st.number_input("Sólidos [%]", value=5)

with colR:

    tubing_sel = st.selectbox("Tubing", ["2 7/8","3 1/2","4"])

    rod = st.selectbox("Varilla", ["7/8","1","1 1/8"])

    material = st.selectbox("Material", [
        "DA 78","HS97","Alpha CS","Alpha HS","D New","DSK75","HA96"
    ])

# =========================
# DATA
# =========================
TBG_ID = {"2 7/8":62,"3 1/2":76,"4":89}

RODS = {
 "7/8":{"d":0.875,"peso":2.22},
 "1":{"d":1.0,"peso":2.67},
 "1 1/8":{"d":1.125,"peso":3.37}
}

YIELD = {
 "DA 78":85,"HS97":115,"Alpha CS":110,
 "Alpha HS":135,"D New":85,"DSK75":85,"HA96":115
}

tubing = TBG_ID[tubing_sel]

d = RODS[rod]["d"] * 0.0254
A = math.pi * d**2 / 4
r = d / 2
J = math.pi * d**4 / 32

peso = RODS[rod]["peso"] * 47.88

# flotabilidad
rho_steel = 7850
peso_eff = peso * (1 - densidad / rho_steel)

# =========================
# HIDRAULICA
# =========================
pres_total = pres_linea + ((nivel + sumergencia) * densidad) / 10000

pot_h = prod * pres_total * 0.0014
pot_c = pot_h / eficiencia

T_hid = (5252 * pot_c) / rpm
T_hid *= (1 + viscosidad/1000)*(1 + solidos/100)
T_hid *= (62/tubing)**0.5

# =========================
# TRAYECTORIA
# =========================
modo = st.selectbox("Modo de pozo", ["Vertical","Desviado"])

T_fric = 0

if modo == "Desviado":

    st.subheader("Pegar perfil: MD – Inclinación – Azimuth")

    text = st.text_area("Ejemplo:\n100 5 120\n200 10 130", height=120)

    if text:

        data=[]
        for row in text.split("\n"):
            vals=row.strip().split()
            if len(vals)>=3:
                try:
                    data.append([float(vals[0]),float(vals[1]),float(vals[2])])
                except:
                    pass

        df = pd.DataFrame(data, columns=["md","inc","az"])

        if len(df)>1:

            # =====================
            # DLS
            # =====================
            dls=[0]

            for i in range(1,len(df)):

                dmd = df["md"][i] - df["md"][i-1]

                inc1=np.radians(df["inc"][i-1])
                inc2=np.radians(df["inc"][i])
                az1=np.radians(df["az"][i-1])
                az2=np.radians(df["az"][i])

                if dmd>0:
                    cos_dl = (np.sin(inc1)*np.sin(inc2)*np.cos(az2-az1) +
                              np.cos(inc1)*np.cos(inc2))
                    cos_dl = np.clip(cos_dl,-1,1)

                    dl=np.degrees(np.arccos(cos_dl))
                    dls.append(dl*(100/(dmd*3.28084)))
                else:
                    dls.append(0)

            df["DLS"]=dls

            # =====================
            # TRAYECTORIA 3D
            # =====================
            X=[0]; Y=[0]; Z=[0]

            for i in range(1,len(df)):

                dmd=df["md"][i]-df["md"][i-1]

                inc1=np.radians(df["inc"][i-1])
                inc2=np.radians(df["inc"][i])
                az1=np.radians(df["az"][i-1])
                az2=np.radians(df["az"][i])

                dX=dmd/2*(np.sin(inc1)*np.cos(az1)+np.sin(inc2)*np.cos(az2))
                dY=dmd/2*(np.sin(inc1)*np.sin(az1)+np.sin(inc2)*np.sin(az2))
                dZ=dmd/2*(np.cos(inc1)+np.cos(inc2))

                X.append(X[-1]+dX)
                Y.append(Y[-1]+dY)
                Z.append(Z[-1]-dZ)

            df["X"]=X
            df["Y"]=Y
            df["Z"]=Z

            # =====================
            # CONTACTO
            # =====================
            mu=0.1
            R_eff=tubing/2000

            carga=[]
            centr=[]

            for i in range(1,len(df)):

                dz=df["md"][i]-df["md"][i-1]
                inc_rad=np.radians(df["inc"][i])

                N = peso_eff*np.sin(inc_rad)
                N = N*(1 + df["DLS"][i]/20)

                carga.append(N)

                if N <= 10:
                    c=0
                elif N <= 40:
                    c=2
                elif N <= 55:
                    c=3
                else:
                    c="Black Mamba"

                centr.append(c)

                dT=mu*N*R_eff*dz
                T_fric+=dT

            df=df.iloc[1:]
            df["Carga (lb)"]=carga
            df["Centralizadores"]=centr

            st.markdown("### Tabla de centralizadores")
            st.dataframe(df)

            # =====================
            # DIAGNOSTICO GLOBAL
            # =====================
            max_carga=max(carga)
            avg_carga=sum(carga)/len(carga)

            st.markdown("## Diagnóstico del String")

            st.write(f"Carga máxima: {max_carga:.1f} lb")
            st.write(f"Carga promedio: {avg_carga:.1f} lb")

            # =====================
            # 3D
            # =====================
            with colR:

                elev=st.slider("Elevación",0,90,25)
                azim=st.slider("Azimut",0,360,45)

                fig=plt.figure(figsize=(5,8))
                ax=fig.add_subplot(111,projection='3d')

                ax.plot(df["X"],df["Y"],df["Z"],color="black")
                ax.scatter(df["X"],df["Y"],df["Z"],c="blue",s=20)

                ax.view_init(elev=elev,azim=azim)
                ax.set_box_aspect([1,1,2])

                st.pyplot(fig)

# =========================
# ESFUERZOS
# =========================
T_total=T_hid+T_fric
potencia=T_total*rpm/5252

F = peso_eff*profundidad

sigma=(F/A)/6894757
tau=((T_total*1.35582*r)/J)/6894757
von=math.sqrt(sigma**2+3*tau**2)

YS=YIELD[material]
uso=(von/YS)*100

st.markdown("---")

c1,c2,c3=st.columns(3)
c1.metric("Axial [ksi]", f"{sigma:.2f}")
c2.metric("Torsión [ksi]", f"{tau:.2f}")
c3.metric("Von Mises [ksi]", f"{von:.2f}")

c4,c5=st.columns(2)
c4.metric("Torque [lb-ft]", f"{T_total:.1f}")
c5.metric("Potencia [HP]", f"{potencia:.1f}")

st.metric("Uso [%]", f"{uso:.1f}")
