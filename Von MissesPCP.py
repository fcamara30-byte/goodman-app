import streamlit as st
import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("PCP + Sarta – Modelo Ingeniería")

colL, colR = st.columns([2,2])

# =========================
# INPUTS
# =========================
with colL:

    profundidad = st.number_input("Profundidad (m)",600,step=100)
    rpm = st.number_input("RPM",350)
    prod = st.number_input("Producción",150.0)

    pres_linea = st.number_input("Presión línea",14.1)
    nivel = st.number_input("Nivel dinámico",570)
    densidad = st.number_input("Densidad",840.0)

    eficiencia = st.number_input("Eficiencia",0.6)
    viscosidad = st.number_input("Viscosidad",300)
    solidos = st.number_input("Sólidos",5.0)

    rod = st.selectbox("Varilla",["7/8","1","1 1/8"])

# =========================
# DATA
# =========================
RODS={"7/8":{"d":0.875,"peso":2.22},
      "1":{"d":1.0,"peso":2.67},
      "1 1/8":{"d":1.125,"peso":3.37}}

d=RODS[rod]["d"]*0.0254
peso=RODS[rod]["peso"]*47.88

# =========================
# TORQUE HIDRAULICO
# =========================
pres_nivel=(nivel*densidad)/10000
pres_total=pres_linea+pres_nivel

pot_h=prod*pres_total*0.0014
pot_c=pot_h/eficiencia

T_hid=(5252*pot_c)/rpm
T_hid*=(1+viscosidad/1000)*(1+solidos/100)

# =========================
# TRAYECTORIA
# =========================
modo=st.selectbox("Modo de pozo",["Vertical","Desviado"])

T_fric=0
df=pd.DataFrame()

if modo=="Desviado":

    text=st.text_area("Perfil (MD Inc Az)")

    if text:

        data=[]

        for row in text.split("\n"):
            v=row.strip().split()

            try:
                if len(v)==3:
                    data.append([float(v[0]),float(v[1]),float(v[2])])

                elif len(v)==2:
                    # ✅ PARSEO ROBUSTO tipo 80733 67
                    val=v[0]
                    if len(val)>3:
                        md=float(val[:-2])
                        inc=float(val[-2:])
                    else:
                        md=float(val)
                        inc=float(v[1])

                    az=float(v[1])
                    data.append([md,inc,az])
            except:
                pass

        df_raw=pd.DataFrame(data,columns=["md","inc","az"])

        if len(df_raw)>1:

            # =====================
            # INTERPOLACION
            # =====================
            step=7.62
            md_new=np.arange(df_raw["md"].min(),
                             df_raw["md"].max()+step,
                             step)

            df=pd.DataFrame({
                "md":md_new,
                "inc":np.interp(md_new,df_raw["md"],df_raw["inc"]),
                "az":np.interp(md_new,df_raw["md"],df_raw["az"])
            })

            inc=np.radians(df["inc"])
            az=np.radians(df["az"])

            # =====================
            # DLS
            # =====================
            dls=[0]
            for i in range(1,len(df)):
                dmd=df["md"][i]-df["md"][i-1]

                inc1=np.radians(df["inc"][i-1])
                inc2=np.radians(df["inc"][i])
                az1=np.radians(df["az"][i-1])
                az2=np.radians(df["az"][i])

                cosdl=(np.sin(inc1)*np.sin(inc2)*np.cos(az2-az1)+
                       np.cos(inc1)*np.cos(inc2))

                dl=np.degrees(np.arccos(np.clip(cosdl,-1,1)))
                dls.append(dl*100/(dmd*3.28))

            df["DLS"]=dls

            # =====================
            # COORDENADAS
            # =====================
            X=[0];Y=[0];Z=[0]

            for i in range(1,len(df)):
                dz=df["md"][i]-df["md"][i-1]

                X.append(X[-1]+np.sin(inc[i])*np.cos(az[i])*dz)
                Y.append(Y[-1]+np.sin(inc[i])*np.sin(az[i])*dz)
                Z.append(Z[-1]-np.cos(inc[i])*dz)

            df["X"]=X; df["Y"]=Y; df["Z"]=Z

            # =====================
            # CONTACTO + TORQUE
            # =====================
            mu=0.25
            R_eff=0.04

            carga=[]

            for i in range(1,len(df)):

                dz=df["md"][i]-df["md"][i-1]

                # ✅ CARGA LOCAL (no crece con profundidad)
                N = peso*np.sin(inc[i])
                N = N*(1 + df["DLS"][i]/10)

                # ✅ DISTRIBUCION REAL
                N = N / 2

                carga.append(N)

                # ✅ TORQUE ACUMULADO (ESTO ES LA CLAVE)
                dT = mu * N * R_eff * dz
                T_fric += dT

            df=df.iloc[1:]
            df["Carga"]=np.round(carga,1)

# =========================
# RESULTADO FINAL
# =========================
T_total = T_hid + T_fric

st.metric("Torque total [lb-ft]", f"{T_total:.1f}")

# =========================
# GRAFICO
# =========================
if len(df)>1:

    fig=plt.figure(figsize=(5,8))
    ax=fig.add_subplot(111,projection='3d')

    ax.plot(df["X"],df["Y"],df["Z"],color="black")

    ax.set_box_aspect([1,1,2])
    st.pyplot(fig)

    st.dataframe(df[["md","DLS","Carga"]])
