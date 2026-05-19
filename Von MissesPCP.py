
import streamlit as stimport stream
import pandas as pd
import numpy as np
import matplotlib.pyplot as p

st.set_page_config(layout="wide")

st.title("PCP + Sarta – Modelo Ingeniería")

colL, colR = st.columns([2,2])

# =========================
# INPUTS
# =========================
with colL:

    c1,c2 = st.columns(2)

    with c1:
        profundidad = st.number_input("Profundidad (m)",600,step=100)
        rpm = st.number_input("RPM",350)
        prod = st.number_input("Producción",150.0)
        pres_linea = st.number_input("Presión línea",14.1)
        nivel = st.number_input("Nivel dinámico",570)
        densidad = st.number_input("Densidad",840.0)
        eficiencia = st.number_input("Eficiencia",0.6)

    with c2:
        viscosidad = st.number_input("Viscosidad",300)
        solidos = st.number_input("Sólidos",5.0)
        rod = st.selectbox("Varilla",["7/8","1","1 1/8"])
        material = st.selectbox("Material",
            ["DA 78","HS97","Alpha CS","Alpha HS","D New","DSK75","HA96"]
        )

# =========================
# DATA
# =========================
RODS={"7/8":{"d":0.875,"peso":2.22},
      "1":{"d":1.0,"peso":2.67},
      "1 1/8":{"d":1.125,"peso":3.37}}

YIELD={"DA 78":85,"HS97":115,"Alpha CS":110,
       "Alpha HS":135,"D New":85,"DSK75":85,"HA96":115}

d=RODS[rod]["d"]*0.0254
A=math.pi*d**2/4
J=math.pi*d**4/32
r=d/2
peso=RODS[rod]["peso"]*47.88

# =========================
# HIDRÁULICA
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

    text=st.text_area("Perfil: MD Inc Az")

    if text:
        data=[]
        for r in text.split("\n"):
            v=r.split()
            if len(v)>=3:
                data.append([float(v[0]),float(v[1]),float(v[2])])

        df_raw=pd.DataFrame(data,columns=["md","inc","az"])

        if len(df_raw)>1:

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
                dls.append(np.degrees(np.arccos(np.clip(cosdl,-1,1)))*100/(dmd*3.28))

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

            df["X"]=X;df["Y"]=Y;df["Z"]=Z

            # =====================
            # ✅ CARGA LATERAL CORRECTA
            # =====================
            carga=[];centr=[]
            mu=0.15
            R_eff=0.05

            for i in range(1,len(df)):

                dz=df["md"][i]-df["md"][i-1]

                N=peso*np.sin(inc[i])
                N=N*(1+df["DLS"][i]/15)
                N=N/3   # distribución

                carga.append(N)

                # centralizadores
                if N<10: c=0
                elif N<40: c=2
                elif N<55: c=3
                else: c="Black Mamba"

                centr.append(c)

                T_fric += mu*N*R_eff*dz

            df=df.iloc[1:]
            df["Carga"]=np.round(carga,1)
            df["Centralizadores"]=centr

# =========================
# RESULTADOS
# =========================
T_total=T_hid+T_fric

F=peso*profundidad
sigma=(F/A)/6894757
tau=((T_total*1.35582*r)/J)/6894757
von=math.sqrt(sigma**2+3*tau**2)

YS=YIELD[material]
uso=von/YS*100
fs=YS/von

# =========================
# GRAFICO
# =========================
with colR:

    st.metric("Torque Total [lb-ft]",f"{T_total:.1f}")

    if len(df)>1:
        fig=plt.figure(figsize=(5,8))
        ax=fig.add_subplot(111,projection='3d')

        for i in range(len(df)-1):

            c=df["Carga"].iloc[i]

            if c<10:color="green"
            elif c<40:color="yellow"
            elif c<55:color="orange"
            else:color="red"

            ax.plot(
                [df["X"].iloc[i],df["X"].iloc[i+1]],
                [df["Y"].iloc[i],df["Y"].iloc[i+1]],
                [df["Z"].iloc[i],df["Z"].iloc[i+1]],
                color=color
            )

        ax.set_box_aspect([1,1,2])
        ax.tick_params(labelsize=6)
        st.pyplot(fig)

        st.dataframe(df[["md","DLS","Carga","Centralizadores"]])

# =========================
# MECÁNICA
# =========================
st.markdown("---")

c1,c2,c3=st.columns(3)
c1.metric("Axial (ksi)",f"{sigma:.2f}")
c2.metric("Torsión (ksi)",f"{tau:.2f}")
c3.metric("Von Mises (ksi)",f"{von:.2f}")

c4,c5=st.columns(2)
c4.metric("Uso (%)",f"{uso:.1f}")
c5.metric("FS",f"{fs:.2f}")

