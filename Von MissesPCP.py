
import streamlit as st
import streamlit.components.v1 as components
import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os   # ✅ ESTE FALTABA
from io import BytesIO

# CONTADOR DE VISITAS# =========================
# =========================

def contador_visitas():
    archivo = "visitas.txt"

    if not os.path.exists(archivo):
        with open(archivo, "w") as f:
            f.write("0")

    with open(archivo, "r+") as f:
        try:
            count = int(f.read())
        except:
            count = 0

        count += 1
        f.seek(0)
        f.write(str(count))
        f.truncate()

    return count


from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

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

st.title("PCP-QUICK-CALCULATION 🌎")

visitas = contador_visitas()

st.markdown(f"""
<div style='text-align:right; font-size:13px; color:gray; margin-top:-10px;'>
Visitas: {visitas}
</div>
""", unsafe_allow_html=True)








components.html("""
<div style="text-align:right;">
    <button onclick="parent.window.print()" style="
        padding:5px 10px;
        font-size:12px;
        background-color:#1f3b5c;
        color:white;
        border:none;
        border-radius:4px;
        cursor:pointer;
    ">
    🖨️ Print
    </button>
</div>
""", height=40)


colL, colR = st.columns([1,3])

# =========================
# INPUTS
# =========================
with colL:

    c1,c2 = st.columns(2)

    with c1:
        nombre_pozo = st.text_input("Nombre Pozo")
        profundidad = st.number_input("Profundidad Bba (m)",600,step=100)
        rpm = st.number_input("RPM (rev/min)",60,step=10)
        prod = st.number_input("Producción (m³/d)",5.0)
        pres_linea = st.number_input("Presión línea (kg/cm²)", value=1.0,    step=2.0
)
  
        


        
        nivel = st.number_input("Nivel dinámico (m)",
          min_value=0.0, max_value=float(profundidad),  # ✅ no puede superar profundidad
            value=float(profundidad),      # ✅ default = profundidad
               step=50.0
)

        densidad = st.number_input("Densidad (kg/m³)",800.0,step=100.0)
        eficiencia = st.number_input("Eficiencia (-)",0.83)

    with c2:
        viscosidad = st.number_input("Viscosidad (cP)",1,step=40)
        
    # ✅ SUMERGENCIA (ACA)
        sumergencia = st.number_input("Sumergencia (m)", value=50.0,step=10.0)
        
        tbg = st.selectbox("Tubing (in)", ["4", "3 1/2", "2 7/8"])

        liner = st.selectbox("Tubing liner", ["Sin liner", "Con liner"], key="liner")

        # ✅ diccionario (esto NO es input, es dato)
        D_TBG = {
         "4": 0.089,
         "3 1/2": 0.076,
         "2 7/8": 0.062
}

       



      
     
        # ✅ rugosidad absoluta (m)
        RUGOSIDAD = {
          "Sin liner": 0.00015,   # acero viejo / oxidado
           "Con liner": 0.00001    # polímero / muy liso
}
           
        MU_ROD = {
           "Con liner": 0.08,
           "Sin liner": 0.9    
}


     
        
        solidos = st.number_input("Sólidos (%)",1.0,step=1.0)
        rod = st.selectbox("Varilla",["7/8","1","1 1/8"])
        fric_bomba = st.number_input("Fricción Bomba (lb·ft)", value=20.0, step=5.0)
        material = st.selectbox("Material",
            ["DA 78","HS97","Alpha CS","Alpha HS","D New","DSX75","HA96"]
        )

RODS={"7/8":{"d":0.875,"peso":2.22},"1":{"d":1.0,"peso":2.67},"1 1/8":{"d":1.125,"peso":3.37}}
YIELD={"DA 78":100,"HS97":115,"Alpha CS":110,"Alpha HS":135,"D New":95,"DSX75":110,"HA96":115}

# =========================
# CALCULO BASE
# =========================
# =========================
# HIDRÁULICA TUBING
# =========================

# caudal
Q = prod / 86400  # m3/s

# diámetro interno tubing
D_TBG = {
    "4": 0.089,
    "3 1/2": 0.076,
    "2 7/8": 0.062
}

D_tbg = D_TBG[tbg]

# área
A_tbg = math.pi * (D_tbg**2) / 4

# velocidad
v = Q / A_tbg

# viscosidad
mu = viscosidad / 1000

# Reynolds
Re = (1000 * v * D_tbg) / mu
Re = max(Re, 1)

# rugosidad
e = RUGOSIDAD[liner]

# fricción (Swamee-Jain)
f = 0.25 / (math.log10((e/(3.7*D_tbg)) + (5.74/(Re**0.9)))**2)

# pérdida de presión
dp_fric = f * (profundidad / D_tbg) * (0.5 * 1000 * v**2)

# convertir a kg/cm2
dp_fric = dp_fric / 98066

pres_nivel = (nivel * densidad) / 10000
pres_entrada = (sumergencia * densidad) / 10000

pres_total = pres_linea + pres_nivel + dp_fric - pres_entrada


pot_h=prod*pres_total*0.0014
pot_c=pot_h/eficiencia

torque=(5252*pot_c)/rpm
torque*= (1+viscosidad/1000)*(1+solidos/100)*1.07
torque += fric_bomba +20 # ✅ fricción bomba

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

col_modo, _ = st.columns([1,3])

with col_modo:
    modo = st.selectbox("Modo de pozo", ["Vertical","Desviado"])


df=pd.DataFrame()
torque_final=torque


# =========================# ========================= FRICCIÓN REAL CON CURVATURA (MODELO VIGA)
# =========================








def generar_pdf():

    file_path = "reporte_pcp.pdf"
    c = canvas.Canvas(file_path, pagesize=A4)

    width, height = A4

    # =========================
    # CREAR GRAFICO (DENTRO DEL PDF)
    # =========================
    if len(df) > 1:
        fig = plt.figure(figsize=(4,9))
        ax = fig.add_subplot(111, projection='3d')
        ax.tick_params(labelsize=4)
        for i in range(len(df)-1):
            ax.plot(df["X"].iloc[i:i+2],
                    df["Y"].iloc[i:i+2],
                    df["Z"].iloc[i:i+2],
                    color=colores[i], linewidth=2)

        ax.set_box_aspect([1,1,2])
        ax.tick_params(labelsize=6)

        fig.savefig("grafico.png", bbox_inches="tight")
        plt.close(fig)

    # =========================
    # TITULO
    # =========================
    c.setFont("Helvetica-Bold", 16)
    c.drawString(2*cm, height - 2*cm, "REPORTE PCP")

    # =========================
    # INPUTS
    # =========================
    c.setFont("Helvetica", 8)
    y = height - 3*cm

    inputs = [
        f"Prof: {profundidad}",
        f"RPM: {rpm}",
        f"Prod: {prod}",
        f"P Línea: {pres_linea}",
        f"Nivel: {nivel}",
        f"Sumerg: {sumergencia}",
        f"Visc: {viscosidad}",
        f"Sólidos: {solidos}"
    ]

    for txt in inputs:
        c.drawString(2*cm, y, txt)
        y -= 0.4*cm

    # =========================
    # RESULTADOS
    # =========================
    y2 = height - 3*cm

    results = [
        f"Torque: {torque_final:.1f}",
        f"Von Mises: {von:.2f}",
        f"Axial: {sigma:.2f}",
        f"Torsión: {tau:.2f}",
        f"Rod Load: {uso:.1f}"
    ]

    for txt in results:
        c.drawString(11*cm, y2, txt)
        y2 -= 0.4*cm

    # =========================
    # INSERTAR GRAFICO
    # =========================
    try:
        c.drawImage("grafico.png", 9*cm, height-15*cm, width=6*cm)
    except:
        pass

    # =========================
    # TABLA COMPLETA
    # =========================
    y3 = height - 17*cm

    c.setFont("Helvetica-Bold", 9)
    c.drawString(9*cm, y3, "Centralización")

    y3 -= 0.5*cm
    c.setFont("Helvetica", 7)

    if len(df) > 1 and "Recomendación" in df.columns:
        for i in range(len(df)):   # ✅ ahora muestra TODA la tabla

            row = df.iloc[i]
            txt = f"{row['md']:.0f} | {row['DLS']:.1f} | {row['Recomendación']}"
            c.drawString(9*cm, y3, txt)
            y3 -= 0.35*cm

            if y3 < 2*cm:  # evita que se corte
                break

    c.save()

    return file_path


if modo=="Desviado":

    col_text, _ = st.columns([1,3])

    with col_text:
         text = st.text_area("Pegar aquí abajo el perfil: MD-Inc-Az", height=200)

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

            if dls_val <= 1.9:
                colores.append("green")
                rec.append("sin centralizadores")

            elif dls_val <= 3:
                colores.append("yellow")
                rec.append("2 centralizadores ")

            elif dls_val <= 6:
                colores.append("orange")
                rec.append("3 centralizadores ")

            else:
                colores.append("red")
                rec.append("Más de 3 cent o Black Mamba")

        df["Recomendación"]=rec
        df["md"] = df["md"].round(0).astype(int)
if len(df) > 1:

  mu_rod = MU_ROD[liner]
  radio = d / 2

  df_calc = df.copy()

  # ✅ asegurar columnas
  df_calc["dMD"] = df_calc["md"].diff().fillna(0)

  # ✅ calcular peso por tramo
  df_calc["dW"] = peso * df_calc["dMD"]

  # ✅ peso acumulado (desde fondo)
  df_calc["W_acum"] = df_calc["dW"].iloc[::-1].cumsum().iloc[::-1]

  # ✅ curvatura
  df_calc["kappa"] = df_calc["DLS"] * (math.pi/180) / 30.48

  # ✅ fuerza normal

  # ✅ modelo de contacto realista (reemplazo)

  factor_contacto = 0.2 + 0.05 * (df_calc["DLS"] / 3)

  df_calc["N"] = df_calc["W_acum"] * factor_contacto


  # ✅ torque incremental
  df_calc["dT"] = mu_rod * df_calc["N"] * radio

  # ✅ torque total
  T_fric = df_calc["dT"].sum() / 1000

  torque_final = torque + T_fric

  # ✅ AHORA sí tensiones correctas

  tau = ((torque_final*1.35582*r)/J)/6894757
  von = math.sqrt(sigma**2 + 3*tau**2)

  uso = von / YS * 100


else:
    torque_final = torque



# =========================
# RESULTADOS + GRAFICO
# =========================



    # =========================
    # ✅ GRAFICO ARRIBA
    # =========================
# =========================
# ✅ GRAFICO + SLIDERS LADO A LADO
# =========================

with colR:
    colG, colS, colT = st.columns([2.4,0.9,1.7])

    # sliders (derecha)
    with colS:
        elev = st.slider("Vista elevación", 0, 90, 25)
        azim = st.slider("Vista azimut", 0, 360, 45)

    # grafico (izquierda)
    with colG:
        if len(df) > 1:
            fig = plt.figure(figsize=(4,6))
            ax = fig.add_subplot(111, projection='3d')

            for i in range(len(df)-1):
                ax.plot(df["X"].iloc[i:i+2],
                        df["Y"].iloc[i:i+2],
                        df["Z"].iloc[i:i+2],
                        color=colores[i], linewidth=2)

            ax.view_init(elev=elev, azim=azim)
            ax.tick_params(labelsize=6)
            ax.set_box_aspect([1,1,2])

            fig.savefig("grafico.png", bbox_inches="tight")
            st.pyplot(fig)
            
           
            st.markdown("""
            <div style="margin-left:90px">
              🟢 **< 2°/100ft** → Sin centralizadores<br>  
              🟡 **2 – 3°/100ft** → 2 centralizadores<br>  
              🟠 **3 – 6°/100ft** → 3 centralizadores<br>  
              🔴 **> 6°/100ft** → +3 o Black Mamba  
               
            </div>
            """, unsafe_allow_html=True)

            fig.savefig("grafico.png", bbox_inches="tight")

    # tabla derecha
with colT:

    if len(df) > 1:

        st.markdown("### Centralización")

        st.dataframe(
            df[["md","DLS","Recomendación"]]
            .rename(columns={"Recomendación": "Var"}),
            height=600,
            use_container_width=True
        )



            





                # =========================
# ✅ RESUMEN CENTRALIZACIÓN (PANTALLA)
# =========================
if len(df) > 1 and "Recomendación" in df.columns:

    df.columns = df.columns.str.strip()

    st.markdown("### Resumen de Centralización")

    df_centralizados = df[~df["Recomendación"].str.lower().str.contains("bajo|sin")]

    total_tramos = len(df_centralizados)
    st.write(f"**Varillas centralizadas:** {total_tramos}")

    grupos = df_centralizados.groupby("Recomendación")


for tipo, grupo in grupos:

    cantidad = len(grupo)
    md_min = grupo["md"].min()
    md_max = grupo["md"].max()

    st.write(f"{tipo}   |   {cantidad} tramos   |   {md_min:.0f} → {md_max:.0f} m")


               
            


  



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


c4, c5 = st.columns(2)

# 🔴 lógica color rojo si >100
color_class = "metric-red" if uso > 100 else ""

with c4:
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-title">Efect. Road Load (%)</div>
        <div class="metric-value {color_class}">{uso:.1f}</div>
    </div>
    """, unsafe_allow_html=True)

with c5:
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-title">Torque (lb-ft)</div>
        <div class="metric-value">{torque_final:.1f}</div>
    </div>
    """, unsafe_allow_html=True)




# 🔴 lógica color rojo si >100
color_class = "metric-red" if uso > 100 else ""



st.markdown('<div class="cursiva">Desarrollado por Fcam & Eng.Pro. SP-Brazil May-26</div>', unsafe_allow_html=True)


