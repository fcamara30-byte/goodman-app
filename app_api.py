import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

st.set_page_config(layout="wide")

# ======================
# CONTADOR DE VISITAS
# ======================
archivo_contador = "visitas.txt"

if os.path.exists(archivo_contador):
    with open(archivo_contador, "r") as f:
        try:
            visitas = int(f.read())
        except:
            visitas = 0
else:
    visitas = 0

visitas += 1

with open(archivo_contador, "w") as f:
    f.write(str(visitas))

# ✅ MOSTRAR ARRIBA (FORMA SEGURA)
st.markdown(f"""
<div style="font-size:13px; color:gray;">
Visitas totales: <b>{visitas}</b>
</div>
""", unsafe_allow_html=True)

# ======================
# TITULO
# ======================


col_title, col_img = st.columns([5,1])

with col_title:
    st.title("Cálculo de Solicitaciones SRP Corrosión-Fatiga 🌎")







# ======================
# INPUTS
# ======================
c1,c2,c3,c4 = st.columns(4)

L_m = c1.number_input("Longitud pozo (m)",500,5000,1800)
G   = c2.slider("Gravedad específica",0.6,1.2,0.95)
D   = c3.selectbox("Bomba (in)",[1.5,1.75,2,2.25,2.5,2.75,3.25])
N   = c4.slider("SPM",1,20,6)


c_slider, _ = st.columns([2, 3])  # controla el ancho

with c_slider:
    S = st.slider("Carrera (in)", 0, 300, 168)
    # ======================
# PRODUCCIÓN (ARRIBA)
# ======================

c_prod, _ = st.columns([1, 3])

Q_bpd = 0.1166 * S * N * (D**2)
Q_m3 = Q_bpd * 0.159 * 0.9

with c_prod:
    st.markdown(f"""
    <div style="
        border:2px solid black;
        border-radius:10px;
        padding:12px;
        text-align:center;
    ">
        <div style="font-size:14px;">
            Producción
        </div>
        <div style="font-size:28px; font-weight:bold;">
            {Q_m3:,.1f}
        </div>
        <div style="font-size:13px;">
            m³/día
        </div>
    </div>
    """, unsafe_allow_html=True)

# ======================
# PRODUCCIÓN (ARRIBA)
# ======================

c_prod, _ = st.columns([1, 3])

# ======================
# MATERIALES
# ======================
materiales={
    "DA78":{"uts_a":42.86,"b":0.375},
    "HS97":{"uts_a":50,"b":0.375},
    "CS propietario":{"uts_a":44.64,"b":0.375},
    "HS propietario":{"uts_a":55.36,"b":0.375},
    "DSX75":{"uts_a":42.86,"b":0.375},
    "HA96":{"uts_a":50,"b":0.375},
    "D New":{"uts_a":42.86,"b":0.375}
}

st.subheader("Material por tramo")


col1, col2, col3, _ = st.columns([1,1,1,2])  # mismo criterio que antes

with col1:
    sel1 = st.selectbox('1"', materiales.keys())

with col2:
    sel78 = st.selectbox('7/8"', materiales.keys())

with col3:
    sel34 = st.selectbox('3/4"', materiales.keys())

rod_sel = {
    "1": sel1,
    "7/8": sel78,
    "3/4": sel34
}



# ======================
# AMBIENTE
# ======================
CO2={"Nada":1,"Bajo (0-20) psi":0.98,"Medio (21-100) psi":0.9,"Alto >100 psi":0.8}
H2S={"Nada":1,"Bajo (0-0.99) psi":0.93,"Medio (1-2) psi":0.8,"Alto >2 psi":0.75}
BSR={"0":1,"1":1,"2":0.95,"3":0.9,"4":0.82,"5":0.74,"6":0.65}


col1, col2, col3, col4, _ = st.columns([1,1,1,1,2])  # ← mismo criterio compacto

with col1:
    co2 = st.selectbox("PPCO₂", CO2)

with col2:
    h2s = st.selectbox("PPH₂S", H2S)

with col3:
    bsr = st.selectbox("BSR", BSR)

with col4:
    cl = st.number_input("Cloruros (ppm)", 0, 250000, 0, step=1000)


def f_cl(ppm):
    return 1 if ppm<6000 else (-2e-16)*(ppm**3) + (7e-11)*(ppm**2) - (9e-6)*ppm + 1.0704

f_base=CO2[co2]*H2S[h2s]*BSR[bsr]*f_cl(cl)

def FS_material(mat,f):
    if f==1: return 1
    if mat=="DA78": return f*0.90
    elif mat=="HS97": return f*0.92
    elif mat=="CS propietario": return f*0.92
    elif mat=="HS propietario": return f*0.75
    elif mat=="D New": return f*0.90
    elif mat=="DSX75": return f if f < 0.73 else 1
    elif mat=="HA96": return f*0.85
    return f*0.9

# ======================
# VARILLAS
# ======================
st.subheader("Cant. Varillas")

c1,c2,c3=st.columns(3)

# cálculo automático 33%-33%-33%
total_varillas = int((L_m / 0.3048) / 25)  # convertir m → ft → cantidad sticks

n_default = total_varillas // 3


col1, col2, col3, _ = st.columns([1,1,1,2])  # ← achica inputs

# cálculo automático 33%-33%-33%
total_varillas = int((L_m / 0.3048) / 25)

n1_def = total_varillas // 3
n78_def = total_varillas // 3
n34_def = total_varillas - n1_def - n78_def  # ajusta cierre

with col1:
    n1 = st.number_input('1"', 10, 300, n1_def)

with col2:
    n78 = st.number_input('7/8"', 10, 300, n78_def)

with col3:
    n34 = st.number_input('3/4"', 10, 300, n34_def)


L1,L78,L34=n1*25,n78*25,n34*25
total=L1+L78+L34

# ======================
# CONTROL LONGITUD
# ======================
st.subheader("Control de longitud")

long_m = total * 0.3048
dif = long_m - L_m

# ✅ primero crear dataframe
df_ctrl = pd.DataFrame({
    "Pozo (m)":[int(L_m)],
    "Sarta (m)":[int(long_m)],
    "Δ (m)":[int(dif)]
})

# ✅ después crear columnas
col_tabla, _ = st.columns([3, 7])

# ✅ después mostrar
with col_tabla:
    st.dataframe(df_ctrl, use_container_width=True, hide_index=True)

# ✅ ALERTA
if abs(dif) > 20:
    st.markdown("""
    <style>
    @keyframes blink {
        0% {opacity: 1;}
        50% {opacity: 0;}
        100% {opacity: 1;}
    }
    .alerta {
        color: red;
        font-weight: bold;
        animation: blink 0.6s linear 4;
    }
    </style>

    <div class="alerta">⚠ Chequear longitud de Sarta</div>
    """, unsafe_allow_html=True)

# ======================# =================IONES API RP 11L
# ======================

E = 30_000_000  # psi

def calc_kr(L1, L78, L34):
    A = {"1":0.786, "7/8":0.601, "3/4":0.442}
    term = (L1/(A["1"])) + (L78/(A["7/8"])) + (L34/(A["3/4"]))
    kr = E / (term * 12)  # lb/in
    return kr


def calc_No(L_total_ft):
    a = 16300  # ft/s (API)
    Fc = 1.1   # sarta taper típica
    No = (a * Fc) / (4 * L_total_ft)
    return No * 60  # SPM



def F1_Skr_API(N_ratio, Fo_Skr):
    Fo_Skr = max(0.02, min(Fo_Skr, 0.7))
    N_ratio = max(0.02, min(N_ratio, 0.7))

    term1 = Fo_Skr * (1.1 + 1.2*N_ratio)
    term2 = Fo_Skr * (2.2 * N_ratio**2)

    return term1 + term2



def F2_Skr_API(N_ratio, Fo_Skr):
    Fo_Skr = max(0.01, min(Fo_Skr, 0.7))
    N_ratio = max(0.01, min(N_ratio, 0.7))

    base = Fo_Skr * (0.75 - 1.1*N_ratio + 2.2*N_ratio**2)
    corr = 1 + 0.6 * N_ratio**1.5

    return max(base * corr, 0)








# ======================
# MODELO
# ======================
areas={"1":0.786,"7/8":0.601,"3/4":0.442}
peso={"1":3.1,"7/8":2.5,"3/4":1.7}

Wr_air = L1*peso["1"] + L78*peso["7/8"] + L34*peso["3/4"]
Wr = Wr_air*(1-0.128*G)

L_total_ft = L1+L78+L34

Ap=np.pi*D**2/4
Fh=0.433*G*L_total_ft*Ap


# --- API MODEL ---
kr = calc_kr(L1, L78, L34)
Fo = Fh

Fo_Skr = Fo / (S * kr)

No = calc_No(L_total_ft)
N_ratio = N / No

F1_Skr = F1_Skr_API(N_ratio, Fo_Skr)
F2_Skr = F2_Skr_API(N_ratio, Fo_Skr)

PPRL = Wr + (F1_Skr * S * kr)
MPRL = Wr - (F2_Skr * S * kr)
# --- DEBUG TEMPORAL ---# ---st.write("Fo/Skr:", round(Fo_Skr,3))
st.write("N/No:", round(N_ratio,3))
st.write("F2/Skr:", round(F2_Skr,3))


# ======================
# DISPLAY
# ======================
st.subheader("Cargas")



c1, c2, _ = st.columns([1, 1, 5])  # más juntas

def carga_estilo(titulo, valor):
    st.markdown(f"""
    <div style="text-align:center;">
        <div style="font-size:14px;">
            {titulo}
        </div>
        <div style="font-size:28px; font-weight:700; color:#003399;">
            {valor}
        </div>
    </div>
    """, unsafe_allow_html=True)

with c1:
    carga_estilo("PPRL (lb)", f"{int(PPRL):,}")

with c2:
    carga_estilo("MPRL (lb)", f"{int(MPRL):,}")



# ======================
# RESULTADOS
# ======================
st.subheader("Resultados por tramo")

pct={"1":L1/total,"7/8":L78/total,"3/4":L34/total}

W1=pct["1"]*Wr_air
W78=pct["7/8"]*Wr_air

W_up={"1":0,"7/8":W1,"3/4":W1+W78}

rows=[]
colors=["red","green","orange"]

for i,d in enumerate(pct):

    Pmax=PPRL-W_up[d]
    Pmin=max(MPRL-0.3*W_up[d],0)

    Smax=Pmax/areas[d]/1000
    Smin=Pmin/areas[d]/1000

    mat=rod_sel[d]
    fs=FS_material(mat,f_base)

    utsa=materiales[mat]["uts_a"]
    b=materiales[mat]["b"]

    Sadm=utsa*fs+b*Smin
    Gval=(Smax-Smin)/(Sadm-Smin)*100

    rows.append({
        "Tramo":d,
        "Material":mat,
        "FS":round(fs,2),
        "Max Load (lb)":int(Pmax),
        "Min Load (lb)":int(Pmin),
        "Smax (ksi)":round(Smax,1),
        "Smin (ksi)":round(Smin,1),
        "Goodman (%)":int(Gval),
        "Color":colors[i]
    })


df = pd.DataFrame(rows)



def estilo_tabla(df):
    return (
        df.style
        # ✅ fondo gris suave
        .set_properties(**{
            'background-color': '#F2F2F2',
            'font-size': '15px'   # ← un poco más grande
        })
        # ✅ Material en azul fuerte
        .map(lambda x: 'color:#003399; font-weight:bold;', subset=["Material"])
        # ✅ formato numérico controlado

.format({
    "Max Load (lb)": "{:,.0f}",
    "Min Load (lb)": "{:,.0f}",
    "Smax (ksi)": "{:.1f}",
    "Smin (ksi)": "{:.1f}",
    "Goodman (%)": "{:.0f}"
})

        # ✅ padding compacto pero no exagerado
        .set_table_styles([
            {'selector': 'th', 'props': [('font-size', '14px')]},
            {'selector': 'td', 'props': [('padding', '6px 10px')]}
        ])
    )


col_res, _ = st.columns([8,2])  # ✅ achica ancho tabla

with col_res:
    st.dataframe(
        estilo_tabla(df.drop(columns=["Color"])),
        use_container_width=True
    )



# ======================
# GOODMAN
# ======================
st.subheader("Diagrama de Goodman")

x_max=min([
    materiales[rod_sel[d]]["uts_a"] *
    FS_material(rod_sel[d],f_base) / (1-materiales[rod_sel[d]]["b"])
    for d in pct
])

x=np.linspace(0,x_max,200)

fig,ax=plt.subplots()

curvas=[]
for d in pct:
    mat=rod_sel[d]
    fs=FS_material(mat,f_base)

    y=materiales[mat]["uts_a"]*fs + materiales[mat]["b"]*x
    curvas.append(y)

    ax.plot(x,y)

# ✅ zona segura
y_safe=np.minimum.reduce(curvas)
ax.fill_between(x,x,y_safe,where=(y_safe>=x),alpha=0.2)

# ✅ RECUPERAR PUNTOS Y LEYENDA
labels=set()
for _,r in df.iterrows():
    etiqueta=f'{r["Tramo"]}" - {r["Material"]}'
    if etiqueta not in labels:
        ax.scatter(r["Smin (ksi)"], r["Smax (ksi)"], label=etiqueta)
        labels.add(etiqueta)
    else:
        ax.scatter(r["Smin (ksi)"], r["Smax (ksi)"])

# ✅ línea 45°
ax.plot(x,x)

# ✅ límites
ax.set_xlim(left=0)
ax.set_ylim(bottom=0)

# ✅ etiquetas
ax.set_xlabel("Smin (ksi)")
ax.set_ylabel("Smax (ksi)")

# ✅ título (faltaba)
ax.set_title("Solicitaciones penalizadas por Corrosión")

# ✅ leyenda (faltaba)
ax.legend(title="Tramo")

# ✅ DETECCIÓN DE FALLA
fuera = any(df["Goodman (%)"] > 100)

# ✅ MENSAJE EN EL GRÁFICO
if fuera:
    ax.text(
        0.5, 0.1,
        "Seleccione otro tipo de varilla o utilice revestimiento\n+ Tratamiento químico",
        transform=ax.transAxes,
        fontsize=10,
        color="red",
        ha="center",
        bbox=dict(facecolor='white', alpha=0.8, edgecolor='red')
    )


col_plot, col_blank = st.columns([4, 2])  # más chico y a la izquierda

with col_plot:
    st.pyplot(fig)






st.markdown("---")
st.caption("Basada en cálculos APIRP11L, Estudios de Corrosión-Fatiga y Experiencias de Campo..")
st.caption("Desarrollado por Fcam & Eng.Pro. SP-Brazil May-26")



 




