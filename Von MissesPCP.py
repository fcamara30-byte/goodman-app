import streamlit as st
import numpy as np
import math
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("PCP + Sarta – Modelo Ingeniería")

colL, colR = st.columns([2,2])

# INPUTS
with colL:
    profundidad = st.number_input("Profundidad [m]", 0, 3000, 0, 100)
    rpm = st.number_input("RPM", 0, 500, 0)
    prod = st.number_input("Producción [m3/d]", 0)

    pres_linea = st.number_input("Presión línea [kg/cm²]", 0)
    nivel = st.number_input("Nivel dinámico [m]", 0)
    sumergencia = st.number_input("Sumergencia [m]", 0)

    densidad = st.number_input("Densidad [kg/m3]", 500, 1500, 500, 50)
    eficiencia = st.number_input("Eficiencia", value=0.6)

    viscosidad = st.number_input("Viscosidad [cP]", 0, 2000, 0, 50)
    solidos = st.number_input("Sólidos [%]", 0)

with colR:
    tubing_sel = st.selectbox("Tubing", ["2 7/8","3 1/2","4"])
    rod = st.selectbox("Varilla", ["7/8","1","1 1/8"])
    material = st.selectbox("Material", [
        "DA 78","HS97","Alpha CS","Alpha HS","D New","DSK75","HA96"
    ])

# DATA
TBG_ID={"2 7/8":62,"3 1/2":76,"4":89}
RODS={"7/8":{"d":0.875,"peso":2.22},"1":{"d":1.0,"peso":2.67},"1 1/8":{"d":1.125,"peso":3.37}}
YIELD={"DA 78":85,"HS97":115,"Alpha CS":110,"Alpha HS":135,"D New":85,"DSK75":85,"HA96":115}

tubing=TBG_ID[tubing_sel]
d=RODS[rod]["d"]*0.0254
A=math.pi*d**2/4
r=d/2
J=math.pi*d**4/32
peso=RODS[rod]["peso"]*47.88

rho_steel=7850
peso_eff=peso*(1-densidad/rho_steel)

# HIDRÁULICA
pres_total=pres_linea+((nivel+sumergencia)*densidad)/10000
pot_h=prod*pres_total*0.0014
pot_c=pot_h/eficiencia if eficiencia!=0 else 0

T_hid=(5252*pot_c)/rpm if rpm!=0 else 0
T_hid*=(1+viscosidad/1000)*(1+solidos/100)
T_hid*=(62/tubing)**0.5

# TRAYECTORIA
modo=st.selectbox("Modo de pozo",["Vertical","Desviado"])

T_fric=0
df_final=None

if modo=="Desviado":

    st.subheader("Pegar perfil (MD - Inc - Az)")
    text=st.text_area("Ejemplo:\n100 5 120\n200 10 130")

    if text:

        data=[]
        for row in text.split("\n"):
            v=row.strip().split()

            try:
                if len(v)==3:
                    data.append([float(v[0]),float(v[1]),float(v[2])])

                elif len(v)==2:
                    # caso tipo 80733 67 → separa
                    if len(v[0])>3:
                        md=float(v[0][:-2])
                        inc=float(v[0][-2:])
                    else:
                        md=float(v[0])
                        inc=float(v[1])

                    az=float(v[1])
                    data.append([md,inc,az])
            except:
                pass

        if len(data)>1:

            df=pd.DataFrame(data,columns=["md","inc","az"])

            # interpolación
            step=7.62
            md_new=np.arange(df["md"].min(),df["md"].max(),step)

            df=pd.DataFrame({
                "md":md_new,
                "inc":np.interp(md_new,df["md"],df["inc"]),
                "az":np.interp(md_new,df["md"],df["az"])
            })

            # DLS
            dls=[0]
            for i in range(1,len(df)):
                dmd=df["md"][i]-df["md"][i-1]
                inc1=np.radians(df["inc"][i-1])
                inc2=np.radians(df["inc"][i])
                az1=np.radians(df["az"][i-1])
                az2=np.radians(df["az"][i])

                cos_dl=(np.sin(inc1)*np.sin(inc2)*np.cos(az2-az1)+np.cos(inc1)*np.cos(inc2))
                dl=np.degrees(np.arccos(np.clip(cos_dl,-1,1)))
                dls.append(dl*(100/(dmd*3.28084)))

            df["DLS"]=np.round(dls,1)

            # 3D trayectoria
            X=[0];Y=[0];Z=[0]

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

            df["X"]=X; df["Y"]=Y; df["Z"]=Z

            # contacto
            mu=0.1
            R_eff=tubing/2000

            carga=[]; centr=[]

            for i in range(1,len(df)):

                dz=df["md"][i]-df["md"][i-1]
                inc_rad=np.radians(df["inc"][i])

                N=peso_eff*np.sin(inc_rad)
                N=N*(1+df["DLS"][i]/20)

                carga.append(N)

                if N<=10: c=0
                elif N<=40: c=2
                elif N<=55: c=3
                else: c="Black Mamba"

                centr.append(c)
                T_fric+=mu*N*R_eff*dz

            df=df.iloc[1:]
            df["Carga (lb)"]=np.round(carga,1)
            df["Centralizadores"]=centr

            df_final=df

# =========================
# OUTPUT SIEMPRE VISIBLE
# =========================
T_total=T_hid+T_fric
potencia=T_total*rpm/5252 if rpm!=0 else 0

F=peso_eff*profundidad
sigma=(F/A)/6894757 if A!=0 else 0
tau=((T_total*1.35582*r)/J)/6894757 if J!=0 else 0
von=math.sqrt(sigma**2+3*tau**2)

YS=YIELD[material]
uso=(von/YS)*100 if YS!=0 else 0
FS=YS/von if von!=0 else 0

st.markdown("---")
c1,c2,c3,c4,c5,c6=st.columns(6)

c1.metric("Axial [ksi]",f"{sigma:.1f}")
c2.metric("Torsión [ksi]",f"{tau:.1f}")
c3.metric("Von Mises [ksi]",f"{von:.1f}")
c4.metric("% Fluencia",f"{uso:.1f}")
c5.metric("FS",f"{FS:.2f}")
c6.metric("Torque [lb-ft]",f"{T_total:.0f}")

st.metric("Potencia [HP]",f"{potencia:.0f}")

# =========================
# TABLA + 3D + SUGERENCIA
# =========================
if df_final is not None:

    st.markdown("### Distribución por varilla")
    st.dataframe(df_final[["md","inc","DLS","Carga (lb)","Centralizadores"]])

    # recomendación
    max_carga=df_final["Carga (lb)"].max()

    if max_carga<=10:
        reco="Sin centralizadores"
    elif max_carga<=40:
        reco="2 centralizadores"
    elif max_carga<=55:
        reco="3 centralizadores"
    else:
        reco="Black Mamba"

    st.success(f"Recomendación: {reco}")

    # 3D
    with colR:

        elev=st.slider("Elevación",0,90,25)
        azim=st.slider("Azimut",0,360,45)

        fig=plt.figure(figsize=(5,7))
        ax=fig.add_subplot(111,projection='3d')

        ax.plot(df_final["X"],df_final["Y"],df_final["Z"],color="black")
        ax.scatter(df_final["X"],df_final["Y"],df_final["Z"],c="blue",s=8)

        ax.view_init(elev=elev,azim=azim)
        ax.set_box_aspect([1,1,2])

        st.pyplot(fig)
