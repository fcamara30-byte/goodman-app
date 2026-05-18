# ✅ MOSTRAR ARRIBA
st.markdown("""
<div style="font-size:13px; color:gray;">
Visitas totais: <b>{visitas}</b>
</div>
""", unsafe_allow_html=True)

# ======================
# TITULO
# ======================

col_title, col_img = st.columns([5,1])

with col_title:
    st.title("Cálculo de Solicitações SRP Corrosão-Fadiga")

with col_img:
    st.markdown(
        "<div style='font-size:60px; text-align:center;'>⚙️</div>",
        unsafe_allow_html=True
    )

# ======================
# INPUTS
# ======================
c1,c2,c3,c4 = st.columns(4)

L_m = c1.number_input("Comprimento do poço (m)",500,5000,1800)
G   = c2.slider("Gravidade específica",0.6,1.2,0.95)
D   = c3.selectbox("Bomba (in)",[1.5,1.75,2,2.25,2.5])
N   = c4.slider("SPM",1,20,6)

with c_slider:
    S = st.slider("Curso (in)", 0, 300, 168)

# ======================
# MATERIALES
# ======================
st.subheader("Material por trecho")

# ======================
# AMBIENTE
# ======================
with col1:
    co2 = st.selectbox("CO₂", CO2)

with col2:
    h2s = st.selectbox("H₂S", H2S)

with col3:
    bsr = st.selectbox("BSR", BSR)

with col4:
    cl = st.number_input("Cloretos (ppm)", 0, 250000, 0, step=1000)

# ======================
# VARILLAS
# ======================
st.subheader("Quantidade de hastes")

with col1:
    n1 = st.number_input('1"', 10, 300, n1_def)

with col2:
    n78 = st.number_input('7/8"', 10, 300, n78_def)

with col3:
    n34 = st.number_input('3/4"', 10, 300, n34_def)

# ======================
# CONTROL LONGITUD
# ======================
st.subheader("Controle de comprimento")

df_ctrl = pd.DataFrame({
    "Poço (m)":[int(L_m)],
    "Haste (m)":[int(long_m)],
    "Δ (m)":[int(dif)]
})

# ALERTA
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

<div class="alerta">⚠ Verificar comprimento da haste</div>
""", unsafe_allow_html=True)

# ======================
# DISPLAY
# ======================
st.subheader("Cargas")

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
st.subheader("Resultados por trecho")

# ======================
# GOODMAN
# ======================
st.subheader("Diagrama de Goodman")

ax.set_xlabel("Smin (ksi)")
ax.set_ylabel("Smax (ksi)")
ax.set_title("Solicitações penalizadas por Corrosão")

ax.legend(title="Trecho")

if fora:
    ax.text(
        0.5, 0.1,
        "Selecione outro tipo de haste ou utilize revestimento\n+ tratamento químico",
        transform=ax.transAxes,
        fontsize=10,
        color="red",
        ha="center",
        bbox=dict(facecolor='white', alpha=0.8, edgecolor='red')
    )

# ======================
# FOOTER
# ======================
st.markdown("---")
st.caption("Baseado em cálculos APIRP11L, estudos de corrosão-fadiga e experiências de campo.")
st.caption("Desenvolvido por Fcam & Eng.Pro. SP-Brazil May-26")

