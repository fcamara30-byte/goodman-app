with col2:

    fig, ax = plt.subplots(figsize=(7,6))

    # TODAS las curvas
    for mat in materiales:

        y = (materiales[mat]["uts_a"] + materiales[mat]["b"] * smin) * f

        # destacar seleccionado
        if mat == material:
            ax.plot(smin, y, linewidth=3, label=mat, color='blue')

            # etiqueta fuerte
            ax.text(
                smin[-1], y[-1],
                mat,
                fontsize=11,
                color='blue',
                weight='bold'
            )
        else:
            ax.plot(smin, y, alpha=0.25, color='gray')

            # etiqueta tenue (no molesta)
            ax.text(
                smin[-1], y[-1],
                mat,
                fontsize=8,
                color='gray',
                alpha=0.5
            )

    # línea 45°
    ax.plot(smin, smin, 'k--', label='45°')

    # punto operativo
    ax.scatter(smin_user, smax_user, color="red", s=100)

    # ejes desde origen
    ax.set_xlim(0,150)
    ax.set_ylim(0,150)

    ax.set_xlabel("Smin (ksi)")
    ax.set_ylabel("Smax (ksi)")
    ax.set_title("Diagrama de Goodman")

    ax.grid()

    st.pyplot(fig)

    # RESULTADOS
    st.markdown("---")
    st.subheader("Resultados")

    sadm_user = goodman(smin_user, uts_a, b, f)
    FS = sadm_user / smax_user if smax_user > 0 else 0

    col_r1, col_r2, col_r3 = st.columns(3)

    col_r1.metric("Factor total", round(f,3))
    col_r2.metric("Sadm", round(sadm_user,2))
    col_r3.metric("FS", round(FS,2))

    if FS >= 1:
        st.success("CONDICIÓN SEGURA ✅")
    else:
        st.error("CONDICIÓN CRÍTICA ❌")
