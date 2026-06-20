import streamlit as st

import streamlit.components.v1 as components
import math# =====================
import threading
import time
import requests


def eficiencia_volumetrica(dp_bar, visc_cp, rpm):

    f_dp = 1 / (1 + dp_bar / 60)
    f_visc = 1 - np.exp(-visc_cp / 30)
    f_rpm = np.exp(-rpm / 250)

    # base
    eta = 0.60 + 0.30 * f_visc + 0.20 * f_rpm + 0.15 * f_dp

   
    if eta > 0.85:
        eta = 0.85 + (eta - 0.85) * 2.5   

    return max(0.86, min(0.92, eta))





from bombas import bombas
# ✅ FONDO GLOBAL (poner primero de todos los estilos)
st.markdown("""
<style>
html, body, .stApp {
    background: #e6eef8 !important;
}
</style>
""", unsafe_allow_html=True)


import pandas as pd




import numpy as np
import matplotlib.pyplot as plt
import os   # ✅ ESTE FALTABA
from io import BytesIO
df = pd.DataFrame()
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
def keep_alive():
    while True:
        try:
            requests.get("https://pcpsucke.streamlit.app/")
            print("Self ping OK")
        except:
            print("Self ping failed")
        time.sleep(240)  # cada 4 minutos

threading.Thread(target=keep_alive, daemon=True).start()

st.markdown("""
<style>
.block-container {
    padding-top: 0rem !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
div[data-testid="stNumberInput"] {width: 130px;}
</style>
""", unsafe_allow_html=True)


st.markdown("""
<style>
[data-testid="stDataFrame"] td {
    font-size: 11px !important;
}

[data-testid="stDataFrame"] th {
    font-size: 12px !important;
}
</style>
""", unsafe_allow_html=True)



st.markdown("""
<style>
.metric-box {
    padding: 2px 4px;                 /* 👈 más chica (~15%) */
    border-radius: 6px;
    background-color: #cfe3ff;        /* 👈 dorado claro */
    text-align: center;
    margin-bottom: 1px;               /* 👈 más juntas vertical */
    margin-left: 2px;
    margin-right: 2px;                /* 👈 más juntas horizontal */
    border: 1px solid #e5cc70;
}

.metric-title {
    font-size: 11px;                  /* 👈 un poco más chico */
    color: #5a5a5a;
}

.metric-value {
    font-size: 20px;                  /* 👈 compacto */
    font-weight: bold;
    color: #1f3b5c;
}


.metric-red {
    color: #ff1a1a;
}
</style>
""", unsafe_allow_html=True)


st.markdown("""
<style>
.titulo {
    margin-top: -60px;
    margin-bottom: 0px;
}
.subtitulo {
    margin: 0;
}
.version {
    margin: -120;
}
</style>

<h1 class="titulo" style="
    font-family: 'Segoe UI';
    font-weight: 650;
    font-size: 45px;
    color: #1f3b5c;
">
10-Rod 🌎
</h1>

<p class="subtitulo" style="color:#6c7a89; font-size:18px;">
PCP Design 
</p>

<p class="version" style="color:#999; font-size:16px;">
Versión Beta
</p>
""", unsafe_allow_html=True)



visitas = contador_visitas()










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
""", height=30)


colL, colR = st.columns([1.1,2.3])

# =========================
# INPUTS
# =========================
with colL:

    c1,c2 = st.columns(2)


    

   
    with c1:
        
        nombre_pozo = st.text_input("Well Name")
        profundidad = st.number_input("Pump Seat (m)",100,step=100)                                   
                                 
         # ✅ selección de bomba
        prod = st.number_input("Gross Prod. (m³/d)", value=10.0, step=10.0)
        rpm_manual = st.number_input("RPM oper", value=150, step=10)










        
        Q_real = prod




        
        pres_linea = st.number_input("Tubing Head Pressure (kg/cm²)", value=1.0,    step=2.0
)
  
        




        # gravedad específica del petróleo
        sg_oil = st.number_input(
        "Oil Specific Gravity (-)",
         min_value=0.5,
         max_value=1.1,
         value=0.85,
         step=0.01
)

# corte de agua
        wc = st.number_input(
       "Water Cut (%)",
        min_value=0.0,
        max_value=100.0,
        value=50.0,
        step=5.0
)



       
        eficiencia = st.number_input(
       "Mec Effic. (-)",
        min_value=0.0,
        max_value=1.2,
        value=0.85,
        step=0.03
)


    with c2:
       
        viscosidad = st.number_input(
         "Viscosity (cP)",
           min_value=1,
            value=1,
            step=10
)

        
    # ✅ SUMERGENCIA (ACA)
        sumergencia = st.number_input("Submergence TVD (m)", value=50.0,step=10.0)
        
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



     
        
        solidos = st.number_input("Solid content (%)",1.0,step=1.0)
        rod = st.selectbox("Sucker Rod Diameter",["7/8","1","1 1/8"])
        
        material = st.selectbox("Rod Grade",
            ["DA 78","HS97","CS Proprietary","HS Proprietary","D New","DSX75","HA96"]
        )
        fric_bomba = st.number_input("Pump Friction (lb·ft)", value=20.0, step=5.0)



RODS={"7/8":{"d":0.875,"peso":2.22},"1":{"d":1.0,"peso":2.67},"1 1/8":{"d":1.125,"peso":3.37}}
YIELD={"DA 78":100,"HS97":120,"CS Proprietary":110,"HS Proprietary":135,"D New":95,"DSX75":115,"HA96":120}
# =========================


# =========================
# CALCULO BASE
# =========================
# =========================
# HIDRÁULICA TUBING
# =========================
# =========================
# ✅ DENSIDAD MEZCLA
# =========================

rho_water = 1000  # kg/m3

densidad = (
    (1 - wc/100) * sg_oil * 1000
    + (wc/100) * rho_water
)

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


pres_entrada = (sumergencia * densidad) / 10000

# presión columna tubing (desde bomba a superficie)
pres_columna = (profundidad * densidad) / 10000

# presión intake correcta
pres_total = pres_linea + pres_columna + dp_fric - pres_entrada
# ✅ eficiencia correcta
eta_sugerida = eficiencia_volumetrica(pres_total, viscosidad, rpm_manual)
usar_auto = st.checkbox("Auto η", value=True)

if usar_auto:
    st.session_state["eta_input"] = round(eta_sugerida, 3)

with c1:



    eta_usuario = st.number_input(
    "Volumetric Effic (-)",
    min_value=0.0,
    max_value=1.0,
    step=0.01,
    key="eta_input"
)






if usar_auto:
    eta = eficiencia_volumetrica(pres_total, viscosidad, rpm_manual)
else:
    eta = eta_usuario




# ===============================
# ✅ BUSQUEDA RPM ÓPTIMA (mínimo torque)
# ===============================

rpm_range = np.arange(40, 501, 5)

mejor_rpm = None
mejor_torque = 1e12
mejor_Q100 = None

for r in rpm_range:

    eta_test = eficiencia_volumetrica(pres_total, viscosidad, r)

    Q100_test = prod / (eta_test * (r / 100))
    Q_teorico_test = Q100_test * (r / 100)

    Q_slip_test = Q_teorico_test * (1 - eta_test)
    Q_cap_test = Q_teorico_test - Q_slip_test

    # ✅ ESTA LÍNEA FALTABA
    pot_h_test = Q_cap_test * pres_total * 0.0014

    # ✅ ahora sí funciona
    pot_c_test = pot_h_test / eficiencia

    torque_test = (5252 * pot_c_test) / r
    torque_test *= (1 + viscosidad/1000) * (1 + solidos/100) * 1.07

    if torque_test < mejor_torque:
        mejor_torque = torque_test
        mejor_rpm = r
        mejor_Q100 = Q100_test


# ✅ resultados óptimos
rpm_optima_real = mejor_rpm
Q100_optimo = round(mejor_Q100 / 10) * 10




# ✅ input editable dinámico
rpm = rpm_manual

# ✅ bomba resultante REAL
Q100_req = prod / (eta * (rpm / 100))
Q100_req = round(Q100_req / 10) * 10

# ✅ caudal coherente
Q_teorico = Q_real/eta



# ===============================
# ✅ SLIP REAL (modelo físico)
# ===============================

Q_slip = Q_teorico * (1 - eta)

Q_cap = Q_teorico - Q_slip

pot_h = Q_teorico * pres_total * 0.0014


pot_c = pot_h / eficiencia



rpm_eff = max(rpm, 5)



# diámetro en metros
d = RODS[rod]["d"] * 0.0254

# factor relativo
factor_d = d / 0.0254   # relativo a varilla de 1"

# torque
torque = (5252 * pot_c) / rpm_eff

torque *= (1 + viscosidad/1000) * (1 + solidos/100) * 1.07
# ===============================
# ✅ TORQUE VISCOSO (C-FER)
# ===============================
T_visc = 0.02 * viscosidad * (rpm_eff / 100)

torque += T_visc

# ✅ corregido con diámetro
torque += (fric_bomba + 20) * factor_d



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

rho_steel = 7850  # kg/m3

Wr = peso * profundidad * (1 - densidad / rho_steel)



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


col_modo, _ = st.columns([1,3])


with col_modo:
    modo = st.selectbox("Survey", ["Desviado","Vertical"], key="modo_pozo")

if modo != "Desviado":
    df = pd.DataFrame()

torque_final = torque



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
        CELESTE_FUERTE = "#d2e3f3"
        fig = plt.figure(figsize=(5,6))
        fig.patch.set_facecolor="#d2e3f3"
        ax = fig.add_subplot(111, projection='3d')
        ax.set_facecolor="#d2e3f3"
        
        ax.xaxis.pane.set_facecolor="#d2e3f3"
        ax.yaxis.pane.set_facecolor(CELESTE_FUERTE)
        ax.zaxis.pane.set_facecolor(CELESTE_FUERTE)

        for axis in [ax.xaxis, ax.yaxis, ax.zaxis]:
            for t in axis.get_ticklabels():
                t.set_fontsize(3)

        ax.tick_params(labelsize=2)
        for i in range(len(df)-1):
            ax.plot(df["X"].iloc[i:i+2],
                    df["Y"].iloc[i:i+2],
                    df["Z"].iloc[i:i+2],
                    color=colores[i], linewidth=2)

        ax.set_box_aspect([1,1,4])
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
        f"Von Mises: {von:.1f}",
        f"Axial: {sigma:.0f}",
        f"Torsión: {tau:.1f}",
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

col_text, _ = st.columns([1,3])

with col_text:

    # ✅ PERFIL DEMO (TAB REAL)
    demo_text = """5\t0\t0
260\t0\t222
263\t2\t222
272\t3\t215,5
281\t4\t208,5
290\t5\t203,5
299\t6,5\t199
308\t8\t200,5
316\t9,5\t202
325\t10,75\t203
332\t12\t204,5
360\t13,25\t210
379\t13,5\t217,5
399\t13,5\t218
408\t13,5\t215
426\t13,5\t212,5
437\t13,75\t214
446\t14\t217,5
455\t14,25\t217,5
464\t14,75\t217
480\t15,25\t218,5
489\t15,5\t220,5
498\t16\t220,5
516\t16,75\t220
533\t17,5\t221,5
546\t20,5\t223
564\t23\t221
574\t24,5\t219,5
592\t28\t220
628\t36\t221
664\t42\t221,5
681\t45\t220
701\t47,5\t218,5
712\t48\t218
729\t48,5\t219
747\t47,25\t219
765\t46\t219,5
801\t43,75\t221
846\t42,25\t220,5
884\t42\t220
953\t42\t220"""

    # ✅ FUNCIÓN (evita error StreamlitAPIException)
    def cargar_demo():
        st.session_state["perfil_texto"] = demo_text

    # ✅ CSS FINAL
    st.markdown("""
    <style>
    div.stButton > button {
        background-color: #1f4fbf !important;
        color: white !important;
        border-radius: 8px;
        width: 160px;
        height: 40px;
        font-size: 14px;
        font-weight: 600;
        white-space: nowrap;
        display: flex;
        align-items: center;
        justify-content: center;
        border: none;
        margin-top: 25px;
    }

    /* 👇 baja el título (acercarlo al cuadro) */
    .titulo-perfil {
        margin-bottom: -10px;
    }
    </style>
    """, unsafe_allow_html=True)

    # ✅ TÍTULO (más cerca del cuadro)
    st.markdown('<div class="titulo-perfil"><b>⬇️Paste from Xls. Survey : MD-Inc-Az</b></div>', unsafe_allow_html=True)

    # ✅ LAYOUT CUADRO + BOTÓN
    col_box, col_btn = st.columns([4,1])

    # ✅ CUADRO
    with col_box:
        text = st.text_area(
            "",
            height=230,
            key="perfil_texto"
        )

    # ✅ BOTÓN
    with col_btn:
        st.button("Demo", on_click=cargar_demo)




if modo=="Desviado" and text:

    data = []

    for row in text.strip().split("\n"):

        vals = row.replace(",", ".").split()

        try:
            if len(vals) == 3:
                data.append([float(vals[0]), float(vals[1]), float(vals[2])])

            elif len(vals) == 2:

                val = vals[0]

                if len(val) > 3:
                    md = float(val[:-2])
                    inc = float(val[-2:])
                else:
                    md = float(val)
                    inc = float(vals[1])

                az = float(vals[1])
                data.append([md, inc, az])

        except:
            pass

    if len(data) > 0:
        df = pd.DataFrame(data, columns=["md","inc","az"])


    if 'df' in locals() and len(df) > 1:

        step=7.62
        md_new=np.arange(df["md"].min(),df["md"].max()+step,step)

        df=pd.DataFrame({
            "md":md_new,
            "inc":np.interp(md_new,df["md"],df["inc"]),
            "az":np.interp(md_new,df["md"],df["az"])
        })
       
        df = df.sort_values("md").reset_index(drop=True)
        df["md"] = df["md"] - df["md"].iloc[0]

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

        df["DLS"] = np.round(dls, 1)

# ✅ versión elegante (centrada en el tramo)
        df["DLS_plot"] = (df["DLS"] + df["DLS"].shift(1)) / 2

        # =====================
        # COORDENADAS
        # =====================

X = [0]*len(df)
Y = [0]*len(df)
Z = [0]*len(df)


inc = inc if 'inc' in locals() else [0]

for i in range(1, len(inc)):

    dz = df["md"][i] - df["md"][i-1]

    X[i] = X[i-1] + np.sin(inc[i]) * np.cos(az[i]) * dz
    Y[i] = Y[i-1] + np.sin(inc[i]) * np.sin(az[i]) * dz
    Z[i] = Z[i-1] - np.cos(inc[i]) * dz

# ✅ AFUERA DEL LOOP
df["X"] = X
df["Y"] = Y

if len(df) > 0:
    df["Z"] =-df["md"]




        # =====================
        # ✅ RECOMENDACIÓN POR DLS
        # =====================

colores = []
rec = []


for _, row in df.iterrows():
    dls_val = row["DLS"]
    inc_val = row["inc"]

    if dls_val <= 1.9 and inc_val <= 25:
        colores.append("green")
        rec.append("sin cent.")

    elif dls_val <= 3:
        colores.append("yellow")
        rec.append("2 cent.")

    elif dls_val <= 6:
        colores.append("orange")
        rec.append("3 cent.")

    elif inc_val > 30:
        colores.append("orange")
        rec.append("Inc.liner")

    else:
        colores.append("red")
        rec.append("Mamba")


df["Recomendación"] = rec

df["md"] = df["md"].round(0).astype(int) if "md" in df else df.get("md", [])



# =====================================
# MODELO CONTACTO PCP - FISICO FINAL
# =====================================

# ✅ siempre definido (no rompe en vertical)
torque_final = torque
radio_contacto = d / 2
N_crit = None
N_min = None
md_crit = None
md_min = None
md_max = None
t_dias = None

if len(df) > 1 and "inc" in df.columns:

    df_calc = df.copy()

    # ---------------------------------
    # GEOMETRIA
    # ---------------------------------

    spacing = 7.62

    inc_rad = np.deg2rad(df_calc["inc"])
    kappa = np.deg2rad(df_calc["DLS"]) / 30.48

    # ---------------------------------
    # PESO ACUMULADO (TENSION)
    # ---------------------------------

    df_calc["dMD"] = df_calc["md"].diff().fillna(0)
    df_calc["dW"] = peso * df_calc["dMD"]

    df_calc["T_local"] = (
        df_calc["dW"]
        .iloc[::-1]
        .cumsum()
        .iloc[::-1]
    )

    # ---------------------------------
    # CONTACTO (SUMA DIRECTA ✅)
    # ---------------------------------

    W_tramo = peso * spacing

    df_calc["N_grav"] = W_tramo * np.sin(inc_rad)

    df_calc["N_curv"] = (
        df_calc["T_local"]
        * kappa
        * spacing
    )

    # ✅ IMPORTANTE — SUMA (NO VECTORIAL)
    df_calc["N"] = (
        df_calc["N_grav"]
        + df_calc["N_curv"]
    )

    # ---------------------------------
    # CUPLAS
    # ---------------------------------

    df_calc["n_cupla"] = (df_calc["md"] / spacing).astype(int)

    df_calc["es_cupla"] = (
        df_calc["n_cupla"] != df_calc["n_cupla"].shift(1)
    )

    df_calc["N_eff"] = 0.0
    df_calc.loc[df_calc["es_cupla"], "N_eff"] = df_calc["N"]

    # ---------------------------------
    # TORQUE
    # ---------------------------------

    mu_rod = MU_ROD.get(liner, 0.4)

    df_calc["dT"] = (
        mu_rod
        * df_calc["N_eff"]
        * radio_contacto
    )

    T_fric = df_calc["dT"].max()

    torque_final = torque + T_fric

    # ---------------------------------
    # CUPLA CRITICA (FISICA ✅)
    # ---------------------------------

    df_contacto = df_calc[df_calc["N_eff"] > 0]

    if len(df_contacto) > 0:
        idx_crit = df_contacto["N_eff"].idxmax()
        md_crit = df_contacto.loc[idx_crit, "md"]
        N_crit = df_contacto.loc[idx_crit, "N_eff"]
    else:
        md_crit = None
        N_crit = None
    
    if len(df_contacto) > 0:
     N_min = df_contacto["N_eff"].min()
    else:
     N_min = None

    # ---------------------------------
    # ZONA CRITICA (USANDO CONTACTO ✅)
    # ---------------------------------

    if len(df_contacto) > 0:
        umbral = 0.9 * df_contacto["N_eff"].max()
        zona = df_contacto[df_contacto["N_eff"] >= umbral]

        md_min = zona["md"].min()
        md_max = zona["md"].max()
    else:
        md_min = None
        md_max = None

    # ---------------------------------
    # VIDA (ARCHARD CON N REAL ✅)
    # ---------------------------------

    V = (2 * np.pi * rpm / 60) * radio_contacto

    if liner == "Con liner":
        mu_wear = 0.08
    else:
        mu_wear = 0.30

    K = 1.1e-12 * (1 + solidos / 100)
    h_fail = 0.005

    if N_crit is not None and N_crit > 0:
        wear_rate = K * mu_wear * N_crit * V
        t_dias = (h_fail / wear_rate) / 86400
    else:
        t_dias = None

else:
    md_min = None
    md_max = None
    md_crit = None
    N_crit = None
    t_dias = None





  # ✅ AHORA sí tensiones correctas

tau = ((torque_final*1.35582*r)/J)/6894757
von = math.sqrt(sigma**2 + 3*tau**2)

uso = von / YS * 100

st.write(f"N crítica (N): {N_crit:.0f}" if N_crit else "N crítica: N/A")

st.write(
    f"N mínima (N): {N_min:.0f}"
    if N_min is not None else "N mínima: N/A"
)





# =========================
# RESULTADOS + GRAFICO
# =========================
c1, c2, c3, c6 = st.columns(4)

if md_min is not None:
    st.markdown(
        f"<div style='text-align:right;'>👉 Zona crítica: {md_min:.0f} – {md_max:.0f} m</div>",
        unsafe_allow_html=True
    )
else:
    st.markdown(
        "<div style='text-align:right;'>👉 No aplica (pozo vertical)</div>",
        unsafe_allow_html=True
    )





with c1:
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-title">Axial (ksi)</div>
        <div class="metric-value">{sigma:.1f}</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-title">Torsión (ksi)</div>
        <div class="metric-value">{tau:.1f}</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-title">Von Mises (ksi)</div>
        <div class="metric-value">{von:.1f}</div>
    </div>
    """, unsafe_allow_html=True)


with c6:
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-title">Tubing RL (Days)</div>
        <div class="metric-value">
            {"No aplica" if t_dias is None else f"{t_dias:.0f}"}
        </div>
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
st.write(f"ΔP bomba = {pres_total:.1f} bar")
st.markdown("### Pump Requirement")



# ✅ recomendación REAL DE DISEÑO
Q100_sugerido = Q100_optimo
rpm_calc = rpm_optima_real

colA, colB = st.columns(2)

with colA:
    st.markdown("✅ **Recomendado**")
    st.write(f"AP {pres_total:.0f} bar – {Q100_sugerido:.0f} m³/100 rpm")
    st.write(f"RPM óptima: {rpm_calc:.0f}")

with colB:
    st.markdown("📌 **Operando**")
    st.write(f"RPM: {rpm}")
    # ===============================
# ===============================
# ✅ SELECCIÓN DE BOMBAS (REAL)
# ===============================

bombas_validas = []

for nombre, data in bombas.items():

    Q_bomba = data["Q"]
    DP_bomba = data["DP"]

    # ✅ filtro por presión
    if DP_bomba >= pres_total:
        bombas_validas.append((nombre, Q_bomba, DP_bomba))


# ✅ fallback
modo_fallback = False
if len(bombas_validas) == 0:
    modo_fallback = True 
    st.warning("⚠ No pump meets the ΔP requirement")
    bombas_validas = [
        (nombre, data["Q"], data["DP"])
        for nombre, data in bombas.items()
    ]


# ✅ ORDEN FUERA DEL LOOP ✅

def get_diametro(nombre):
    return int(nombre.split()[1])

bombas_ordenadas = sorted(
    bombas_validas,
    key=lambda x: get_diametro(x[0])
)

# ✅ TOP 5
top5 = bombas_ordenadas[:18]


# ===============================
# ✅ OUTPUT
# ===============================


if modo_fallback:
    st.markdown("### 🔴 ")
else:
    st.markdown("### Suggested Pumps")


html = '<div style="display:grid; grid-template-columns: repeat(3,1fr); gap:6px;">'

for nombre, Q, DP in top5:
    html += f'<div style="font-size:12px; line-height:1.2; padding:2px;">{nombre} | {Q} m³/100rpm | {DP} bar</div>'

html += "</div>"
st.markdown(html, unsafe_allow_html=True)


# =========================
# ✅ GRAFICO + SLIDERS LADO A LADO
# =========================

with colR:
  colG, colS, colT = st.columns([3.8,1.6,3])

    # sliders
with colS:
        elev = st.slider("Vista elevación", 0, 90, 25)
        azim = st.slider("Vista azimut", 0, 360, 45)

    # gráfico
with colG:
    st.markdown("###### Well Survey")

    if len(df) > 1:
        fig = plt.figure(figsize=(4,6))
        ax = fig.add_subplot(111, projection='3d')

        # ✅ PLOTEO
        for i in range(len(df)-1):
            ax.plot(
                df["X"].iloc[i:i+2],
                df["Y"].iloc[i:i+2],
                df["Z"].iloc[i:i+2],
                color=colores[i],
                linewidth=3   # 👈 evita “engrosamiento”
            )

        # ✅ ESCALA ORIGINAL (como tenías)
        X = df["X"].values
        Y = df["Y"].values
        Z = df["Z"].values

        max_range = max(
            max(X) - min(X),
            max(Y) - min(Y),
            max(Z) - min(Z)
        )

        mid_x = (max(X) + min(X)) / 2
        mid_y = (max(Y) + min(Y)) / 2
        mid_z = (max(Z) + min(Z)) / 2

        ax.set_xlim(mid_x - max_range/2, mid_x + max_range/2)
        ax.set_ylim(mid_y - max_range/2, mid_y + max_range/2)
        ax.set_zlim(mid_z - max_range/2, mid_z + max_range/2)

        # ✅ VIEW ESTABLE (ANTI-LOCO)
        elev_safe = max(10, min(elev, 80))
        azim_safe = azim

        for z in [0, 90, 180, 270]:
            if abs(azim_safe - z) < 5:
                azim_safe = z + 10

        ax.view_init(elev=elev_safe, azim=azim_safe)

        # ✅ DISTANCIA → controla “zoom”
        ax.dist = 9

        # ✅ ESTÉTICA ORIGINAL (ligeramente mejorada)
        ax.tick_params(labelsize=6)
        ax.set_box_aspect([1,1,2.2])

        st.pyplot(fig)

        # ✅ LEYENDA
        st.markdown("""
        <div style="margin-left:90px">
          🟢 **< 2°/100ft** → sin cent.<br>  
          🟡 **2 – 3°/100ft** → 2 cent.<br>  
          🟠 **3 – 6°/100ft** → 3 cent.<br>  
          🔴 **> 6°/100ft** → +3 o Mamba  
        </div>
        """, unsafe_allow_html=True)

        fig.savefig("grafico.png", bbox_inches="tight")



    # tabla derecha
with colT:

    if len(df) > 1:

        st.markdown("###### Guiding Proposal")

        st.dataframe(
            df[["md","DLS","Recomendación"]]
            .rename(columns={"Recomendación": "Var"}),
            height=530,
            use_container_width=True
        )



            





                # =========================
# ✅ RESUMEN CENTRALIZACIÓN (PANTALLA)
# =========================
if len(df) > 1 and "Recomendación" in df.columns:

    df.columns = df.columns.str.strip()

    st.markdown("### Guiding Proposal and Rod Wearing Graph simulation")

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

# =========================
# MÉTRICAS VISUALES PRO
# =========================





# 🔴 lógica color rojo si >100
color_class = "metric-red" if uso > 100 else ""

# ===============================
# ✅ VERSION FINAL LIMPIA (CORRIGE TODO LO QUE==============# ✅ VERSION FINAL LIMPIA (CORRIGE TODO LO QUE ESTÁ MAL)

import plotly.graph_objects as go
import numpy as np

# ✅ MATAR TODOS LOS ESPACIOS SUPERIORES DE STREAMLIT
st.markdown("""
<style>
.block-container {
    padding-top: 0rem;
    padding-bottom: 0rem;
}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

if len(df) > 1:


   
    # ===============================
    # DATA
    # ===============================
    X = df["X"].values
    Y = df["Y"].values
    Z = df["Z"].values
    DLS = df["DLS"].values

    # ===============================
    # ✅ PERFIL CORRECTO (REAL)
    # ===============================
    Xc = X - np.mean(X)
    Yc = Y - np.mean(Y)

    # 👇 esto es lo correcto para survey
    Zc = Z 

    # ===============================
    # BASE LOCAL
    # ===============================
    dx = np.gradient(Xc)
    dy = np.gradient(Yc)
    dz = np.gradient(Zc)

    T = np.vstack([dx, dy, dz]).T
    T = T/(np.linalg.norm(T,axis=1)[:,None]+1e-6)

    N = np.zeros_like(T)
    N[0] = np.array([1,0,0])

    for i in range(1,len(T)):
        v = N[i-1]
        t = T[i]
        v = v - np.dot(v,t)*t
        if np.linalg.norm(v) < 1e-6:
            v = np.cross(t, np.array([0,1,0]))
        N[i] = v/(np.linalg.norm(v)+1e-6)

    B = np.cross(T,N)

    # ===============================
    # DIMENSIONES
    # ===============================
    escala = max(abs(Xc).max(), abs(Yc).max(), abs(Zc).max())

    radio_varilla = escala * 0.002   # 👈 tamaño chico relativo
    radio_tubo   = radio_varilla * 3.5
    # ===============================
    # SEMÁFORO
    # ===============================
    col_map=[]
    for d in DLS:
        if d<=1.9: col_map.append("green")
        elif d<=3: col_map.append("yellow")
        elif d<=6: col_map.append("orange")
        else: col_map.append("red")
    col_map=np.array(col_map)
    crit = col_map=="red"

    # ===============================
    # TUBING
    # ===============================
    tube=[]
    for ang in np.linspace(0,2*np.pi,8):
        Xt = Xc + radio_tubo*(N[:,0]*np.cos(ang)+B[:,0]*np.sin(ang))
        Yt = Yc + radio_tubo*(N[:,1]*np.cos(ang)+B[:,1]*np.sin(ang))
        Zt = Zc + radio_tubo*(N[:,2]*np.cos(ang)+B[:,2]*np.sin(ang))

        tube.append(go.Scatter3d(
            x=Xt,y=Yt,z=Zt,
            mode='lines',
            line=dict(color='blue',width=1),
            showlegend=False
        ))

    # ===============================
    # ANIMACIÓN (NO TOCADA)
    # ===============================


if len(df) > 1:

    frames=[]
    n_frames=140

    for k in range(n_frames):

        theta = k*0.35

        cos_t=np.cos(theta)
        sin_t=np.sin(theta)

        Xr = Xc + radio_varilla*(N[:,0]*cos_t + B[:,0]*sin_t)
        Yr = Yc + radio_varilla*(N[:,1]*cos_t + B[:,1]*sin_t)
        Zr = Zc + radio_varilla*(N[:,2]*cos_t + B[:,2]*sin_t)

        
        puls = 0.3 + 0.7*np.cos(theta*3)
        puls = np.clip(puls, 0.2, 1)


        frames.append(go.Frame(data=tube+[

            go.Scatter3d(
                x=Xr,y=Yr,z=Zr,
                mode='lines',
                line=dict(color='silver',width=10),
                showlegend=False
            ),

            go.Scatter3d(
                x=Xr[~crit],y=Yr[~crit],z=Zr[~crit],
                mode='markers',
                marker=dict(size=4,color=col_map[~crit]),
                showlegend=False
            ),

            go.Scatter3d(
                x=Xr[crit],y=Yr[crit],z=Zr[crit],
                mode='markers',
                marker=dict(size=6 + 4*puls,   # 👈 cambia tamaño dinámico
                color='red',
                opacity=puls
)

            )

        ]))

    # ✅ FIGURA TAMBIÉN ADENTRO
    fig = go.Figure(data=frames[0].data, frames=frames)

  

    fig.update_layout(

        height=900,
        
        paper_bgcolor="#cfe3ff",   # ✅ fondo externo
        plot_bgcolor="#cfe3ff",    # ✅ fondo interno

        uirevision="keep",


        scene=dict(
          aspectmode='cube',

          camera=dict(
          eye=dict(x=1.8, y=2, z=0.2),
          center=dict(x=0, y=0, z=0.1)
    ),

          zaxis=dict(
          title="Profundidad",
          
    ),

),




        margin=dict(l=0, r=0, t=0, b=0),

        updatemenus=[{
            "type":"buttons",
            "x":0.1,
            "y":0.75,
            "buttons":[
                dict(label="Play ▶",
                     method="animate",
                     args=[None, {
                         "frame": {"duration":80},
                         "fromcurrent": True,
                         "mode": "immediate"
                     }]),

                dict(label="Stop⏸",
                     method="animate",
                     args=[[None], {"mode":"immediate"}])
            ]
        }]
    )
    st.markdown("""
<style>
.block-container {
    padding-top: 0rem;
}

div[data-testid="stPlotlyChart"] {
    margin-top: -10px;
}
</style>
""", unsafe_allow_html=True)
    


    fig.write_html("animacion.html")
    
if os.path.exists("animacion.html"):
    with open("animacion.html", "r", encoding="utf-8") as f:
        html_bytes = f.read()

    # ✅ botón descarga
    st.download_button(
        label="⬇ Download Media Graph",
        data=html_bytes,
        file_name="animacion.html",
        mime="text/html"
    )



if len(df) > 1:
    

    st.markdown("""
    <style>
    div[data-testid="stPlotlyChart"] {
    margin-top: -100px;
}
</style>
""", unsafe_allow_html=True)


    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Modo vertical: sin trayectoria 3D")

# ===============================



st.markdown("""
<style>
.footer-text {
    color: #444444;                 /* ✅ gris oscuro */
    font-size: 14px;
    font-family: 'Segoe UI', sans-serif;
    margin-top: -20px;              /* ✅ lo sube */
    margin-left: 10px;
}
</style>

<div class="footer-text">
Desarrollado por Fcam & Eng.Pro-Apolo-Apex. SP-Brazil May-26
</div>
""", unsafe_allow_html=True)
