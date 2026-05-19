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

    profundidad = st.number_input("Profundidad [m]",2000,step=100)
    rpm = st.number_input("RPM",350)
    prod = st.number_input("Producción [m3/d]",150.0)

    pres_linea = st.number_input("Presión línea [kg/cm2]",14.1)

    nivel = st.number_input("Nivel dinámico [m]",500)
    sumergencia = st.number_input("Sumergencia (columna sobre bomba) [m]",200)

    densidad = st.number_input("Densidad [kg/m3]",850.0)
    eficiencia = st.number_input("Eficiencia",0.6)

    viscosidad = st.number_input("Viscosidad [cP]",300)
    solidos = st.number_input("Sólidos [%]",5.0)

with colR:
    tubing_sel = st.selectbox("Tubing",["2 7/8","3 1/2","4"])
    rod = st.selectbox("Varilla",["7/8","1","1 1/8"])

# =========================
# DATOS
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
# CARGA + DEFLEXION
# =========================
F_peso = peso_eff * profundidad
F_hid = pres_total * A * 1e5
F_total = F_peso + F_hid

E = 2.1e11
elong = F_total / (E*A)

# =========================
# TRAYECTORIA
# =========================
modo = st.selectbox("Modo de pozo",["Vertical","Desviado"])

T_fric = 0

if modo=="Desviado":

    text = st.text_area("Pegar md inc az",height=120)

    if text:

        data=[]
        for row in text.split("\n"):
            vals=row.replace(",",".").split()
            if len(vals)>=3:
                try:
                    data.append([float(vals[0]),float(vals[1]),float(vals[2])])
                except:
                    pass

        df = pd.DataFrame(data,columns=["md","inc","az"])

        if len(df)>1:

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

                if dmd>0:
                    cos_dl=(np.sin(inc1)*np.sin(inc2)*np.cos(az2-az1)
                            +np.cos(inc1)*np.cos(inc2))
                    cos_dl=np.clip(cos_dl,-1,1)

                    dl=np.degrees(np.arccos(cos_dl))
                    dls.append(dl*(100/(dmd*3.28)))
                else:
                    dls.append(0)

            df["DLS"]=dls

            # =====================
            # TRAYECTORIA REAL
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
            # CONTACTO + TORTQUE
            # =====================
            mu=0.1
            R_eff=tubing/2000

            carga_list=[]
            centr_list=[]

            for i in range(1,len(df)):

                dz=df["md"][i]-df["md"][i-1]
                inc_rad=np.radians(df["inc"][i])

                N1=peso_eff*np.sin(inc_rad)
                N2=3*(df["DLS"][i]**1.5)
                N3=elong*2e5

                N=N1+N2+N3

                carga_list.append(N)

                if N < 30:
                    centr=0
                elif N < 60:
                    centr=1
                elif N < 100:
                    centr=3
                elif N < 150:
                    centr=5
                else:
                    centr="Black Mamba"

                centr_list.append(centr)

                dT=mu*N*R_eff*dz
                T_fric+=dT

            df = df.iloc[1:]
            df["Carga"]=carga_list
            df["Centralizadores"]=centr_list

# =========================
# RESULTADOS
# =========================
T_total=T_hid+T_fric
potencia=T_total*rpm/5252

st.markdown("---")
st.metric("Torque Final [lb-ft]",f"{T_total:.1f}")
st.metric("Potencia [HP]",f"{potencia:.1f}")

# =========================
# TABLA CENTRALIZADORES
# =========================
if modo=="Desviado" and len(df)>1:

    st.markdown("### Recomendación de Centralizadores")

    st.dataframe(
        df[["md","DLS","Carga","Centralizadores"]],
        use_container_width=True
    )

# =========================
# 3D
# =========================
with colR:

    if modo=="Desviado" and len(df)>1:

        st.markdown("### Trayectoria 3D")

        elev=st.slider("Elevación",0,90,25)
        azim=st.slider("Azimut",0,360,45)

        colores=[]
        for d in df["DLS"]:
            if d<2:colores.append("green")
            elif d<5:colores.append("yellow")
            else:colores.append("red")

        fig=plt.figure(figsize=(6,8))
        ax=fig.add_subplot(111,projection='3d')

        ax.plot(df["X"],df["Y"],df["Z"],color="black")
        ax.scatter(df["X"],df["Y"],df["Z"],c=colores,s=20)

        ax.set_box_aspect([1,1,2])
        ax.view_init(elev=elev,azim=azim)

        st.pyplot(fig)

