# ✅ MOSTRAR ARRIBA (FORMA SEGURA)
st.markdown(f"""
&lt;div style="font-size:13px; color:gray;"&gt;
Visitas totais: &lt;b&gt;{visitas}&lt;/b&gt;
&lt;/div&gt;
""", unsafe_allow_html=True)

# ======================
# TITULO
# ======================

with col_title:
    st.title("Cálculo de Solicitações SRP Corrosão-Fadiga")

with col_img:
    st.markdown(
        "&lt;div style='font-size:60px; text-align:center;'&gt;⚙️&lt;/div&gt;",
        unsafe_allow_html=True
    )

# ======================
# INPUTS
# ======================
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
st.subheader("Qtd. hastes")

# ======================
# CONTROL LONGITUD
# ======================
st.subheader("Controle de comprimento")

df_ctrl = pd.DataFrame({
    "Poço (m)":[int(L_m)],
    "Coluna (m)":[int(long_m)],
    "Δ (m)":[int(dif)]
})

# ✅ ALERTA
if abs(dif) > 20:
    st.markdown("""
    &lt;style&gt;
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
    &lt;/style&gt;

    &lt;div class="alerta"&gt;⚠ Verificar comprimento da coluna&lt;/div&gt;
    """, unsafe_allow_html=True)

# ======================
# DISPLAY
# ======================
st.subheader("Cargas")

def carga_estilo(titulo, valor):
    st.markdown(f"""
    &lt;div style="text-align:center;"&gt;
        &lt;div style="font-size:14px;"&gt;
            {titulo}
        &lt;/div&gt;
        &lt;div style="font-size:28px; font-weight:700; color:#003399;"&gt;
            {valor}
        &lt;/div&gt;
    &lt;/div&gt;
    """, unsafe_allow_html=True)

# ======================
# RESULTADOS
# ======================
st.subheader("Resultados por trecho")

rows.append({
    "Tramo":d,
    "Material":mat,
    "FS":round(fs,2),
    "Carga Máx (lb)":int(Pmax),
    "Carga Mín (lb)":int(Pmin),
    "Smax (ksi)":round(Smax,1),
    "Smin (ksi)":round(Smin,1),
    "Goodman (%)":int(Gval),
    "Color":colors[i]
})

.format({
    "Carga Máx (lb)": "{:,.0f}",
    "Carga Mín (lb)": "{:,.0f}",
    "Smax (ksi)": "{:.1f}",
    "Smin (ksi)": "{:.1f}",
    "Goodman (%)": "{:.0f}"
})

# ======================
# GOODMAN
# ======================
st.subheader("Diagrama de Goodman")

ax.set_xlabel("Smin (ksi)")
ax.set_ylabel("Smax (ksi)")
ax.set_title("Solicitações penalizadas por corrosão")

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
st.caption("Desenvolvido por Fcam &amp; Eng.Pro. SP-Brazil May-26")
 

