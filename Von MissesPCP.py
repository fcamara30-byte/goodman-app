import streamlit as st
import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

st.markdown("""
<style>
div[data-testid="stNumberInput"] {width: 140px;}
</style>
""", unsafe_allow_html=True)
st.markdown("""
<style>
.metric-box {
    padding: 15px;
    border-radius: 10px;
    background-color: #f5f5f5;
    text-align: center;
    margin-bottom: 10px;
}

.metric-title {
    font-size: 14px;
    color: #666;
}

.metric-value {
    font-size: 32px;
    font-weight: bold;
    color: #1f3b5c;
}

.metric-red {
    color: #ff1a1a;
}
</style>
""", unsafe_allow_html=True)

st.title("FCAM-PCP-CALCULATION")

colL, colR = st.columns([1,3])

# =========================
# INPUTS
# =========================
with colL:

    c1,c2 = st.columns(2)

    with c1:
        profundidad = st.number_input("Profundidad (m)",600,step=100)
        rpm = st.number_input("RPM (rev/min)",350)
        prod = st.number_input("Producción (m³/d)",150.0)
        pres_linea = st.number_input("Presión línea (kg/cm²)",14.1)
        nivel = st.number_input("Nivel dinámico (m)",570,step=50)
        densidad = st.number_input("Densidad (kg/m³)",840.0)
        eficiencia = st.number_input("Eficiencia (-)",0.6)

    with c2:
        viscosidad = st.number_input("Viscosidad (cP)",300,step=40)
        solidos = st.number_input("Sólidos (%)",5.0)
        rod = st.selectbox("Varilla",["7/8","1","1 1/8"])
        material = st.selectbox("Material",
            ["DA 78","HS97","Alpha CS","Alpha HS","D New","DSK75","HA96"]
        )

RODS={"7/8":{"d":0.875,"peso":2.22},"1":{"d":1.0,"peso":2.67},"1 1/8":{"d":1.125,"peso":3.37}}
YIELD={"DA 78":85,"HS97":115,"Alpha CS":110,"Alpha HS":135,"D New":85,"DSK75":85,"HA96":115}

# =========================
# CALCULO BASE
# =========================
pres_nivel=(nivel*densidad)/10000
pres_total=pres_linea+pres_nivel

pot_h=prod*pres_total*0.0014
pot_c=pot_h/eficiencia

torque=(5252*pot_c)/rpm
torque*= (1+viscosidad/1000)*(1+solidos/100)

d=RODS[rod]["d"]*0.0254
A=math.pi*d**2/4
J=math.pi*d**4/32
r=d/2

peso=RODS[rod]["peso"]*47.88

# =========================
# ✅ ÁREA EFECTIVA (manual)
# =========================
D_rotor = d * 1.2  # simplificación válida
d_rod = d

Ae = math.pi/4 * (D_rotor**2 - d_rod**2)

# =========================
# ✅ CARGA AXIAL REAL
# =========================
dp_pa = pres_total * 98066  # kg/cm2 → Pa

L = Ae * dp_pa  # carga hidráulica (N)

Wr = peso * profundidad  # peso sarta

F = Wr + L  # carga total real


sigma=(F/A)/6894757
tau=((torque*1.35582*r)/J)/6894757
von=math.sqrt(sigma**2+3*tau**2)

YS=YIELD[material]
uso=von/YS*100
fs=YS/von

# =========================
# TRAYECTORIA
# =========================
st.markdown("---")
modo=st.selectbox("Modo de pozo",["Vertical","Desviado"])

df=pd.DataFrame()
torque_final=torque

# =========================
# ✅ FRICCIÓN REAL (manual)
# =========================
# factor típico basado en tablas (simplificado)
factor = 0.00008 + (0.0000005 * prod)

T_fric = factor * profundidad * viscosidad

torque_final = torque + T_fric


if modo=="Desviado":

    text=st.text_area("Perfil: MD Inc Az")

    if text:

        data=[]
        for row in text.strip().split("\n"):

            vals=row.replace(",",".").split()

            try:
                if len(vals)==3:
                    data.append([float(vals[0]),float(vals[1]),float(vals[2])])

                elif len(vals)==2:
                    val=vals[0]
                    if len(val)>3:
                        md=float(val[:-2])
                        inc=float(val[-2:])
                    else:
                        md=float(val)
                        inc=float(vals[1])
                    az=float(vals[1])
                    data.append([md,inc,az])
            except:
                pass

        df=pd.DataFrame(data,columns=["md","inc","az"])

    if len(df)>1:

        step=7.62
        md_new=np.arange(df["md"].min(),df["md"].max()+step,step)

        df=pd.DataFrame({
            "md":md_new,
            "inc":np.interp(md_new,df["md"],df["inc"]),
            "az":np.interp(md_new,df["md"],df["az"])
        })

        inc=np.radians(df["inc"])
        az=np.radians(df["az"])

        # =====================
        # DLS
        # =====================
        dls=[0]
        for i in range(1,len(df)):
            dmd=(df["md"][i]-df["md"][i-1])*3.28084

            cosdl=(np.sin(inc[i-1])*np.sin(inc[i])*np.cos(az[i]-az[i-1])
                   +np.cos(inc[i-1])*np.cos(inc[i]))

            cosdl=np.clip(cosdl,-1,1)
            dls.append(np.degrees(np.arccos(cosdl))*100/dmd)

        df["DLS"]=np.round(dls,1)

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
        # ✅ RECOMENDACIÓN POR DLS
        # =====================
        colores=[]
        rec=[]

        for dls_val in df["DLS"]:

            if dls_val <= 1:
                colores.append("green")
                rec.append("Bajo")

            elif dls_val <= 3:
                colores.append("yellow")
                rec.append("2 centralizadores")

            elif dls_val <= 6:
                colores.append("orange")
                rec.append("3 centralizadores")

            else:
                colores.append("red")
                rec.append("Black Mamba")

        df["Recomendación"]=rec

# =========================
# RESULTADOS + GRAFICO
# =========================
with colR:

    st.subheader("Torque Final")
    st.metric("Torque (lb-ft)",f"{torque_final:.1f}")

    elev=st.slider("Vista elevación",0,90,25)
    azim=st.slider("Vista azimut",0,360,45)

    if len(df)>1:

        fig=plt.figure(figsize=(5,8))
        ax=fig.add_subplot(111,projection='3d')

        for i in range(len(df)-1):
            ax.plot(df["X"].iloc[i:i+2],
                    df["Y"].iloc[i:i+2],
                    df["Z"].iloc[i:i+2],
                    color=colores[i], linewidth=2)

        ax.view_init(elev=elev,azim=azim)
        ax.tick_params(labelsize=6)
        ax.set_box_aspect([1,1,2])

        st.pyplot(fig)

        st.markdown("### Recomendación de intervención")
        st.dataframe(df[["md","DLS","Recomendación"]])

# =========================
# MÉTRICAS
# =========================
st.markdown("---")
# =========================
# MÉTRICAS VISUALES PRO
# =========================
st.markdown("---")

c1,c2,c3=st.columns(3)

with c1:
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-title">Axial (ksi)</div>
        <div class="metric-value">{sigma:.2f}</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-title">Torsión (ksi)</div>
        <div class="metric-value">{tau:.2f}</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-title">Von Mises (ksi)</div>
        <div class="metric-value">{von:.2f}</div>
    </div>
    """, unsafe_allow_html=True)


c4 = st.columns(1)[0]

# 🔴 lógica color rojo si >100
color_class = "metric-red" if uso > 100 else ""

with c4:
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-title">Rod Load (%)</div>
        <div class="metric-value {color_class}">{uso:.1f}</div>
    </div>
    """, unsafe_allow_html=True)


