import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
import threading
import time
import requests

# ======================
# CONTADOR DE VISITAS
# ======================
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

visitas = contador_visitas()

st.set_page_config(layout="wide")
def keep_alive():
    while True:
        try:
            requests.get("https://selectorvarillas.streamlit.app/")
            print("Self ping OK")
        except:
            print("Self ping failed")
        time.sleep(240)  # cada 4 minutos

threading.Thread(target=keep_alive, daemon=True).start()

# ======================
# ESTILO
# ======================
# ======================
# ESTILO LIMPIO
# ======================
# ======================
# ESTILO FINAL (LIMPIO)
# ======================
st.markdown("""
<style>

/* ===== FONDO GENERAL (CELESTE ELEGANTE) ===== */
html, body, [data-testid="stAppViewContainer"] {
    background-color: #EDF4FB !important;
}

/* ===== CONTENEDOR ===== */
.block-container {
    background-color: transparent;
    padding: 1.5rem 2rem;
}


.titulo-main {
    font-size: 46px;
    font-weight: 700;
    color: #1B3A6F;
    line-height: 1.2;
    margin-bottom: 4px;
}

.titulo-sub {
    font-size: 22px;
    font-weight: 500;
    color: #4A6FA5;
    letter-spacing: 0.3px;
}


/* ===== CURSIVA ===== */
.cursiva {
    font-style: italic;
    color: #555;
}

/* ===== INPUTS ===== */
div[data-baseweb="input"], 
div[data-baseweb="select"] {
    border-radius: 8px;
    max-width: 180px;
}

/* ===== SELECT MÁS COMPACTO ===== */
div[data-baseweb="select"] {
    max-width: 140px;
}

/* ===== TEXTO DENTRO INPUTS (NEGRITA) ===== */
div[data-baseweb="input"] input {
    font-weight: 600;
    color: #1B1F23;
}

/* ===== TEXTO DENTRO SELECT ===== */
div[data-baseweb="select"] span {
    font-weight: 600;
    color: #1B1F23;
}

/* ===== TABLA ===== */
[data-testid="stDataFrame"] {
    background-color: #FFFFFF;
    border-radius: 8px;
}

[data-testid="stDataFrame"] th, 
[data-testid="stDataFrame"] td {
    padding: 3px 6px;
    font-size: 12px;
}

/* ===== METRICS ===== */
[data-testid="stMetric"] {
    background-color: #FFFFFF;
    border-radius: 10px;
    padding: 10px;
    box-shadow: 0px 2px 8px rgba(0,0,0,0.05);
}

</style>
""", unsafe_allow_html=True)

col1, col2 = st.columns([4,1])

with col1:
    st.markdown('<div class="titulo">Sucker Rod Selection 🌎</div>', unsafe_allow_html=True)





st.markdown("""
<div class="titulo-main">10 Rod🌎</div>
<div class="titulo-sub">Corrosion Fatigue Goodman calc</div>
""", unsafe_allow_html=True)



# ======================
# DATOS
# ======================
Grades = {
    "DA78":{"uts_a":42.86,"b":0.375},
    "HS97":{"uts_a":50,"b":0.375},
    "CS propietario":{"uts_a":44.64,"b":0.375},
    "HS propietario":{"uts_a":55.36,"b":0.375},
    "D New":{"uts_a":42.86,"b":0.375},
    "DSX75":{"uts_a":44.64,"b":0.375},
    "HA96":{"uts_a":50,"b":0.375}
}

BSR = {"0":1,"1":1,"2":0.95,"3":0.9,"4":0.82,"5":0.74,"6":0.65}

# ======================
# FACTORES
# ======================
def factor_co2(sel):
    return {
        "Nada (0 psi)":1.0,
        "Low (0–20 psi)":0.98,
        "Medium (21–100 psi)":0.90,
        "High (>100 psi)":0.80
    }[sel]

def factor_h2s(sel):
    return {
        "Nada (0 psi)":1.0,
        "Low (0–1 psi)":0.95,
        "Medium (1–2 psi)":0.80,
        "High (>2 psi)":0.75
    }[sel]

def factor_Clorhides(ppm):
    return 1 if ppm < 6000 else (-2e-16)*(ppm**3) + (7e-11)*(ppm**2) - (9e-6)*ppm + 1.0704

# ======================
# FUNCIONES
# ======================

def ppm_to_psi_CO2(ppm, sal_ppm=50000):
    MW = 44.01
    C = (ppm / 1000) / MW  # mol/L

    kH = 0.02  # mol/L·atm a 60°C

    sal = sal_ppm / 10000
    kH *= np.exp(0.02 * sal)

    P_atm = C / kH
    return P_atm * 14.7


def ppm_to_psi_H2S(ppm, sal_ppm=50000):
    MW = 34.08
    C = (ppm / 1000) / MW

    kH = 0.08  # más soluble que CO2

    sal = sal_ppm / 10000
    kH *= np.exp(0.015 * sal)

    P_atm = C / kH
    return P_atm * 14.7
def FS_Grade(mat,f):
    if f==1: return 1
    if mat=="DA78": return f*0.90
    elif mat=="HS97": return f*0.91
    elif mat=="CS propietario": return f*0.93
    elif mat=="HS propietario": return f*0.75
    elif mat=="D New": return f*0.90
    elif mat=="DSX75": return f if f < 0.77 else 1
    elif mat=="HA96": return f*0.8

def goodman(x,uts,b,fs):
    return (uts + b*x) * fs

# ======================
# INPUTS
# ======================
l,r = st.columns([1,2])

with l:
    Grade = st.selectbox("Grade", list(Grades.keys()))
    co2_ppm = st.number_input("CO2 (ppm)", value=500.0, step=100.0)
    h2s_ppm = st.number_input("H2S (ppm)", value=50.0, step=10.0)
    salinidad = st.number_input("Salinity (ppm)", value=50000.0, step=5000.0)
    
    bsr = st.selectbox("BSR-caldos+", list(BSR.keys()))
    cl_ppm = st.number_input("Clorhides (ppm)",0,200000,0, step=1000)
# ===== GuidesS =====
col_g1, col_g2 = st.columns(2)

# ✅ CO2
with col_g1:
    with st.expander("📘 Guides CO2"):
        st.dataframe(pd.DataFrame({
            "CO2 (ppm)":  [50,100,200,300,500,700,1000,1500,2000,3000,5000,8000,10000,12000],
            "P_CO2 (psi)": [0.5,1,2,3,5,7,10,15,20,30,50,80,100,120]
             }), 
            width=300,
            use_container_width=False)

        st.caption("Regla rápida: ~75 ppm ≈ 1 psi de CO₂")


# ✅ H2S
with col_g2:
    with st.expander("📗 Guides H2S"):
        st.dataframe(pd.DataFrame({
            "H2S (ppm)": [1,5,10,20,50,100,200,500],
            "P_H2S (psi)": [0.01,0.05,0.1,0.2,0.5,1,2,5]
             }),
             width=300,
             use_container_width=False)

        st.caption("H₂S es mucho más soluble → menor presión para mismo ppm")


st.subheader("Load/Diameter Selection")

col_d, col_max, col_min = st.columns([0.3, 0.3, 0.3])

with col_d:
    diam = st.selectbox("Diámetro (in)", ["1", "7/8", "3/4"])

with col_max:
    Pmax_input = float(st.text_input("Max Load (lb)", value="10000"))

with col_min:
    Pmin_input = float(st.text_input("Min Load (lb)", value="2000"))



# áreas
areas = {
    "1": 0.786,
    "7/8": 0.601,
    "3/4": 0.442
}

A = areas[diam]

# ✅ calcular tensiones
Smax = Pmax_input / A / 1000
Smin = Pmin_input / A / 1000

# ======================
# BASE
# ======================
Pco2 = ppm_to_psi_CO2(co2_ppm, salinidad)
Ph2s = ppm_to_psi_H2S(h2s_ppm, salinidad)

def co2_factor_from_psi(p):
    if p < 20:
        return 0.98
    elif p < 100:
        return 0.90
    else:
        return 0.80

def h2s_factor_from_psi(p):
    if p < 1:
        return 0.95
    elif p < 2:
        return 0.80
    else:
        return 0.75

f_base = (
    co2_factor_from_psi(Pco2) *
    h2s_factor_from_psi(Ph2s) *
    BSR[bsr] *
    factor_Clorhides(cl_ppm)
)

x = np.linspace(0,100,200)

# ======================
# GRAFICO
# ======================
with r:
    fig, ax = plt.subplots(figsize=(6,4))
    ranking=[]

    for mat in Grades:
        fs = FS_Grade(mat,f_base)
        y = goodman(x, Grades[mat]["uts_a"], Grades[mat]["b"], fs)

        sadm = goodman(Smin, Grades[mat]["uts_a"], Grades[mat]["b"], fs)
        margen = sadm - Smax

        ranking.append({"Grade":mat,"FS":fs,"Sadm":sadm,"Margen":margen})

        if mat == Grade:
            y_sel = y
            fs_sel = fs
            sadm_user = sadm

    diff = y_sel - x
    idx = np.where(diff <= 0)[0]
    corte = idx[0] if len(idx)>0 else len(x)

    x_clip = x[:corte]
    y_clip = y_sel[:corte]

    ax.plot(x_clip, y_clip, "b", linewidth=3)
    ax.plot(x, x, "k", linewidth=2)

    ax.fill_between(x_clip, x_clip, y_clip,
                    where=(y_clip>=x_clip),
                    color='green', alpha=0.15)

    ax.scatter(Smin, Smax, color="red", s=90)

    if Smax > sadm_user:
        ax.text(
            0.5,0.15,
            "Anoter SR grade must be selected"
            "or Chemical treat/coating",
            transform=ax.transAxes,
            fontsize=10,
            color="red",
            ha="center",
            bbox=dict(facecolor='white', alpha=0.85)
        )

    # ✅ CAMBIO ÚNICO: eje Y pasa por origen
    ax.spines['left'].set_position(('data', 0))

    ax.set_xlim(0,100)
    ax.set_ylim(0,100)
    ax.set_xlabel("Smin (ksi)")
    ax.set_ylabel("Smax (ksi)")
    ax.set_title("Corrosion Fatigue Goodman Graph")

    st.pyplot(fig)

# ======================
# DATA
# ======================
df = pd.DataFrame(ranking)
df = df.sort_values(by="Margen", ascending=False).reset_index(drop=True)

if abs(f_base - 1.0) < 1e-6:
    if "HS97" in df["Grade"].values:
        fila = df[df["Grade"]=="HS97"]
        df = df[df["Grade"]!="HS97"]
        df = pd.concat([fila, df]).reset_index(drop=True)


df["%Goodman"] = ((Smax - Smin) /
(df["Sadm"] - Smin)) * 100


col_tabla, col_der = st.columns([2.7,1.8])

col_tabla, col_der = st.columns([2.7,1.8])

with col_tabla:
    st.markdown('<div class="subtitulo">Sucker Rod Ranking</div>', unsafe_allow_html=True)

    st.dataframe(
        df.drop(columns=["FS"]).style.format({
            "Sadm":"{:.0f}",
            "Margen":"{:.0f}",
            "%Goodman":"{:.0f}"
        }),
        use_container_width=False,
        height=300
    )



with col_der:
    st.markdown('<div class="subtitulo">Results</div>', unsafe_allow_html=True)

    c1,c2 = st.columns(2)
    c3,c4 = st.columns(2)

    c1.metric("FS", f"{fs_sel:.1f}")
    c2.metric("Factor base", f"{f_base:.1f}")
    c3.metric("Sadm", f"{sadm_user:.1f}")
    c4.metric("%Goodman", f"{((Smax - Smin) / (sadm_user - Smin) * 100):.1f}")

    st.markdown('<div class="subtitulo">Suggestions</div>', unsafe_allow_html=True)

    validos = df[df["Margen"] >= 0]
    for i,row in validos.head(3).iterrows():
        st.markdown(f"{i+1}. {row['Grade']}")

st.markdown("---")
st.markdown('<div class="cursiva">Modelo basado en Criterio de Goodman y corrosión-fatiga</div>', unsafe_allow_html=True)
st.markdown('<div class="cursiva">Desarrollado por Fcam & Eng.Pro-Apolo-Apex. SP-Brazil May-26</div>', unsafe_allow_html=True)



