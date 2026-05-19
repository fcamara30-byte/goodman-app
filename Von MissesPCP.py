import streamlit as st
importimport mathimport numpy as np
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("PCP + Sarta – Modelo Ingeniería (Corregido)")

colL, colR = st.columns([2,2])

# =========================
# INPUTS
# =========================
with colL:

    profundidad = st.number_input("Profundidad [m]", min_value=0, max_value=3000, value=1000, step=100)

    rpm = st.number_input("RPM", min_value=50, max_value=500, value=350)
    prod = st.number_input("Producción [m3/d]", value=150.0)

    pres_linea = st.number_input("Presión línea [kg/cm²]", value=14.1)

    nivel = st.number_input("Nivel dinámico [m]", value=500)
    sumergencia = st.number_input("Sumergencia (columna sobre bomba) [m]", value=200)

    densidad = st.number_input("Densidad [kg/m3]", value=850.0)
    eficiencia = st.number_input("Eficiencia [-]", value=0.6)

    viscosidad = st.number_input("Viscosidad [cP]", value=300.0)
    solidos = st.number_input("Sólidos [%]", value=5.0)

with colR:
    tubing_sel = st.selectbox("Tubing", ["2 7/8","3 1/2","4"])
    rod = st.selectbox("Varilla", ["7/8","1","1 1/8"])

# =========================
# DATA
# =========================
TBG_ID={"2 7/8":62,"3 1/2":76,"4":89}
RODS={"7/8":{"d":0.875,"peso":2.22},
      "1":{"d":1.0,"peso":2.67},
      "1 1/8":{"d":1.125,"peso":3.37}}

tubing=TBG_ID[tubing_sel]

d = RODS[rod]["d"]*0.0254
A = math.pi*d**2/4
r = d/2
J = math.pi*d**4/32

peso = RODS[rod]["peso"]*47.88

# flotabilidad
rho_steel = 7850
peso_eff = peso*(1 - densidad/rho_steel)

# =========================
# HIDRAULICA
# =========================
pres_total = pres_linea + ((nivel + sumergencia)*densidad)/10000

pot_h = prod * pres_total * 0.0014
pot_c = pot_h / eficiencia

T_hid = (5252 * pot_c) / rpm
T_hid *= (1 + viscosidad/1000)*(1 + solidos/100)
T_hid *= (62/tubing)**0.5

# =========================
# TRAYECTORIA
# =========================
modo = st.selectbox("Modo de pozo",["Vertical","Desviado"])

T_fric = 0

if modo == "Desviado":

    st.subheader("Pegar perfil: Profundidad (MD) – Inclinación – Azimuth")

    text = st.text_area("Ejemplo:\n100 5 120\n200 10 130",height=120)

    if text:

        data=[]
        for row in text.split("\n"):
            vals=row.split()
            if len(vals)>=3:
                data.append([float(vals[0]),float(vals[1]),float(vals[2])])

        df=pd.DataFrame(data,columns=["md","inc","az"])

        if len(df)>1:

            inc=np.radians(df["inc"])

            # =====================
            # DLS
            # =====================
            dls=[0]
            for i in range(1,len(df)):
                dmd=df["md"][i]-df["md"][i-1]
                if dmd>0:
                    dls.append(abs(df["inc"][i]-df["inc"][i-1])/dmd)
                else:
                    dls.append(0)

            df["DLS"]=dls

            # =====================
            # TRAYECTORIA 3D
            # =====================
            df["X"]=np.cumsum(np.sin(inc)*np.cos(np.radians(df["az"])))
            df["Y"]=np.cumsum(np.sin(inc)*np.sin(np.radians(df["az"])))
            df["Z"]=-df["md"]

            # =====================
            # CARGA LATERAL CORRECTA
            # =====================
            mu=0.1
            R_eff=tubing/2000

            carga=[]
            centr=[]

            for i in range(1,len(df)):

                dz=df["md"][i]-df["md"][i-1]
                inc_rad=np.radians(df["inc"][i])

                # ✅ FISICA CORRECTA
                N = peso_eff * np.sin(inc_rad)

                # ajuste leve DLS (SUAVE)
                N = N * (1 + df["DLS"][i]/20)

                carga.append(N)

                # ✅ TU LOGICA
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
            df["Carga lateral (lb)"]=carga
            df["Centralizadores"]=centr

            st.markdown("### Recomendación de Centralizadores")
            st.dataframe(df[["md","inc","DLS","Carga lateral (lb)","Centralizadores"]])

            # =====================
            # GRAFICO 3D
            # =====================
            with colR:

                elev=st.slider("Elevación",0,90,25)
                azim=st.slider("Azimut",0,360,45)

                fig=plt.figure(figsize=(6,8))
                ax=fig.add_subplot(111,projection='3d')

                ax.plot(df["X"],df["Y"],df["Z"],color="black")
                ax.scatter(df["X"],df["Y"],df["Z"],c="blue",s=20)

                ax.view_init(elev=elev, azim=azim)
                ax.set_box_aspect([1,1,2])

                st.pyplot(fig)

# =========================
# RESULTADOS MECANICOS
# =========================
T_total=T_hid+T_fric
potencia=T_total*rpm/5252

F = peso_eff * profundidad

sigma = (F/A)/6894757
tau = ((T_total*1.35582*r)/J)/6894757
von = math.sqrt(sigma**2 + 3*tau**2)

st.markdown("---")

c1,c2,c3=st.columns(3)
c1.metric("Axial [ksi]",f"{sigma:.2f}")
c2.metric("Torsión [ksi]",f"{tau:.2f}")
c3.metric("Von Mises [ksi]",f"{von:.2f}")

c4,c5=st.columns(2)
c4.metric("Torque [lb-ft]",f"{T_total:.1f}")
c5.metric("Potencia [HP]",f"{potencia:.1f}")



