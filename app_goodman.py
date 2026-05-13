import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import datetime

st.set_page_config(layout="wide")

# ======================
# ESTILO APEX
# ======================
st.markdown("""
<style>
.titulo-apex {font-size:22px; font-weight:600; color:#0B3C8C;}
.marca-apex {font-size:20px; font-weight:800; color:#0052CC; text-align:right;}
.subtitulo {font-size:16px; font-weight:600; color:#1F4E79; margin-top:10px;}
.box {background:#F4F6F8; padding:10px; border-radius:8px;}
</style>
""", unsafe_allow_html=True)

# ======================
# HEADER
# ======================
c1, c2 = st.columns([6,2])
c1.markdown('<div class="titulo-apex">Goodman – Fatiga y Corrosión</div>', unsafe_allow_html=True)
c2.markdown('<div class="marca-apex">APEX</div>', unsafe_allow_html=True)

# ======================
# MATERIALES
# ======================
materiales = {
    "DA78":{"uts_a":30,"b":0.5625},
    "HS97":{"uts_a":50,"b":0.375},
    "CS propietario":{"uts_a":44.64,"b":0.375},
    "HS propietario":{"uts_a":55.36,"b":0.375},
    "D New":{"uts_a":42.86,"b":0.375},
    "DSK75":{"uts_a":42.86,"b":0.375},
    "HA96":{"uts_a":50,"b":0.375}
}

CO2={"Nada":1,"Bajo":1,"Medio":0.9,"Alto":0.8}
H2S={"Nada":1,"Bajo":0.95,"Medio":0.8,"Alto":0.75}
BSR={"0":1,"1":1,"2":0.95,"3":0.9,"4":0.82,"5":0.74,"6":0.65}

# ======================
# FUNCIONES
# ======================
def factor_cloruros(ppm):
    return 1 if ppm < 9000 else 1 - (0.000019 * (ppm ** 0.8))

def FS_material(mat, f):
    if f == 1:
        return 1

    if mat=="DA78": return f*0.95
    elif mat=="HS97": return f
    elif mat=="CS propietario": return f*0.96
    elif mat=="HS propietario": return f*0.80
    elif mat=="D New": return f*0.94
    elif mat=="DSK75": return f if f<0.83 else 1
    elif mat=="HA96": return f*0.93

def goodman(smin, uts, b, fs):
    return (uts + b * smin) * fs

# ======================
# LAYOUT
# ======================
l, r = st.columns([1,2])

# ======================
# INPUTS
# ======================
with l:
    st.markdown('<div class="subtitulo">Inputs</div>', unsafe_allow_html=True)

    a,b = l.columns(2)
    material = a.selectbox("Material", list(materiales.keys()))
    co2 = b.selectbox("CO₂", list(CO2.keys()))

    c,d = l.columns(2)
    h2s = c.selectbox("H₂S", list(H2S.keys()))
    bsr = d.selectbox("BSR (caldos positivos)", list(BSR.keys()))

    cl_ppm = st.number_input("Cloruros (ppm)", 0, 200000, 0)

    smin_user = st.slider("Smin (ksi)", 0, 150, 30)
    smax_user = st.slider("Smax (ksi)", 0, 150, 50)

# ======================
# CALCULO
# ======================
f_base = CO2[co2]*H2S[h2s]*BSR[bsr]*factor_cloruros(cl_ppm)
smin = np.linspace(0,150,200)

# ======================
# GRAFICO
# ======================
with r:

    fig, ax = plt.subplots(figsize=(7,3.8))
    ranking = []

    for mat in materiales:
        fs = FS_material(mat, f_base)

        y = goodman(smin, materiales[mat]["uts_a"], materiales[mat]["b"], fs)
        sadm = goodman(smin_user, materiales[mat]["uts_a"], materiales[mat]["b"], fs)

        margen = sadm - smax_user

        ranking.append({
            "Material": mat,
            "FS": fs,
            "Sadm": sadm,
            "Margen": margen
        })

        if mat == material:
            ax.plot(smin, y, color='blue', linewidth=3)
        else:
            ax.plot(smin, y, color='gray', alpha=0.2)

    ax.plot(smin, smin, 'k--')
    ax.scatter(smin_user, smax_user, color="red", s=60)

    ax.set_xlim(0,150)
    ax.set_ylim(0,150)

    ax.set_xlabel("Smin (ksi)")
    ax.set_ylabel("Smax (ksi)")
    ax.grid()
    plt.tight_layout()

    st.pyplot(fig)

    df = pd.DataFrame(ranking)

    # ✅ RANKING CORREGIDO
    if f_base == 1:
        orden = ["HS97","HA96","DSK75","CS propietario","HS propietario","D New","DA78"]
        df["orden"] = df["Material"].apply(lambda x: orden.index(x) if x in orden else 999)
        df = df.sort_values("orden")
    else:
        df = df.sort_values(by="Margen", ascending=False)

    df["%Goodman"] = ((smax_user - smin_user)/(df["Sadm"] - smin_user)) * 100

    # ======================
    # RANKING
    # ======================
    st.markdown('<div class="subtitulo">Ranking de Varillas sugeridas (de acuerdo a condición elegida)</div>', unsafe_allow_html=True)

    st.dataframe(
        df.drop(columns=["orden"], errors="ignore").style.format({
            "FS":"{:.3f}",
            "Sadm":"{:.1f}",
            "Margen":"{:.1f}",
            "%Goodman":"{:.1f}"
        }),
        use_container_width=True
    )

    # ======================
    # RESULTADOS
    # ======================
    fs_sel = FS_material(material, f_base)
    sadm_user = goodman(smin_user, materiales[material]["uts_a"], materiales[material]["b"], fs_sel)

    goodman_pct = ((smax_user - smin_user)/(sadm_user - smin_user))*100 if sadm_user != smin_user else 0

    st.markdown('<div class="subtitulo">Resultados</div>', unsafe_allow_html=True)
    st.markdown('<div class="box">', unsafe_allow_html=True)

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("FS", f"{fs_sel:.3f}")
    c2.metric("Factor base", f"{f_base:.3f}")
    c3.metric("Sadm (ksi)", f"{sadm_user:.1f}")
    c4.metric("%Goodman", f"{goodman_pct:.1f}")

    st.markdown('</div>', unsafe_allow_html=True)

    # ======================
    # RECOMENDACION
    # ======================
    mejor = df.iloc[0]

    st.markdown('<div class="subtitulo">Recomendación</div>', unsafe_allow_html=True)

    if mejor["Margen"] >= 0:
        st.success(f"Mejor opción: {mejor['Material']}")
    else:
        st.error("Uso de varillas revestidas y/o productos químicos para corrosión")

    # ======================
    # PDF
    # ======================
    def generar_pdf():
        file="reporte_goodman.pdf"
        c=canvas.Canvas(file,pagesize=letter)

        c.setFont("Helvetica-Bold",14)
        c.drawString(50,750,"Goodman - Fatiga y Corrosion")

        c.drawString(400,750,"APEX")

        fecha=datetime.datetime.now().strftime("%d/%m/%Y")
        c.drawString(50,730,f"Fecha: {fecha}")

        c.drawString(50,700,f"Material: {material}")
        c.drawString(50,685,f"FS: {fs_sel:.3f}")
        c.drawString(50,670,f"Factor base: {f_base:.3f}")
        c.drawString(50,655,f"Sadm: {sadm_user:.1f}")
        c.drawString(50,640,f"%Goodman: {goodman_pct:.1f}")

        y = 600
        for _,row in df.iterrows():
            c.drawString(50,y,f"{row['Material']}  Margen:{row['Margen']:.1f}")
            y -= 15

        c.save()
        return file

    st.markdown('<div class="subtitulo">Exportar</div>', unsafe_allow_html=True)

    if st.button("Generar PDF"):
        file = generar_pdf()
        with open(file, "rb") as f:
            st.download_button("Descargar PDF", f, "reporte_goodman.pdf")
