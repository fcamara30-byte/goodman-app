import math

# =========================
# DATA VARILLAS
# =========================
RODS = {
    "7/8": {"d_in": 0.875, "peso_lbft": 2.22},
    "1": {"d_in": 1.0, "peso_lbft": 2.67},
    "1 1/8": {"d_in": 1.125, "peso_lbft": 3.37}
}

def in_to_m(x): return x * 0.0254
def lbft_to_nm(x): return x * 1.35582


# =========================
# FACTOR FLUIDO
# =========================
def factor_fluido(viscosidad_cp, solidos_pct):
    """
    Modelo empírico simple (ajustable):
    """

    # viscosidad
    if viscosidad_cp < 100:
        f_visc = 1.0
    elif viscosidad_cp < 300:
        f_visc = 1.15
    elif viscosidad_cp < 800:
        f_visc = 1.35
    else:
        f_visc = 1.6

    # sólidos
    f_sol = 1 + (solidos_pct / 100) * 0.8

    return f_visc * f_sol


# =========================
# CALCULO COMPLETO
# =========================
def modelo_pcp_avanzado(
    diametro,
    profundidad,
    torque_superficie_lbft,
    densidad,
    viscosidad_cp,
    solidos_pct
):

    rod = RODS[diametro]

    d = in_to_m(rod["d_in"])
    r = d / 2

    A = math.pi * d**2 / 4
    J = math.pi * d**4 / 32

    # ------------------------
    # FLUIDO
    # ------------------------
    f_fluido = factor_fluido(viscosidad_cp, solidos_pct)

    torque_real_lbft = torque_superficie_lbft * f_fluido
    torque_nm = lbft_to_nm(torque_real_lbft)

    # ------------------------
    # CARGAS
    # ------------------------
    peso_lineal = rod["peso_lbft"] * 14.5939 / 0.3048
    peso_total = peso_lineal * profundidad

    g = 9.81
    carga_fluido = densidad * g * profundidad * A

    F_total = peso_total + carga_fluido

    # ------------------------
    # ESFUERZOS
    # ------------------------
    sigma = F_total / A / 1e6
    tau = (torque_nm * r) / J / 1e6

    von_mises = math.sqrt(sigma**2 + 3 * tau**2)

    return {
        "Factor fluido": f_fluido,
        "Torque corregido (lb-ft)": torque_real_lbft,
        "Esfuerzo axial (MPa)": sigma,
        "Esfuerzo torsional (MPa)": tau,
        "Von Mises (MPa)": von_mises
    }


# =========================
# EJEMPLO REAL
# =========================
if __name__ == "__main__":

    res = modelo_pcp_avanzado(
        diametro="1",
        profundidad=600,
        torque_superficie_lbft=325.1,
        densidad=840,
        viscosidad_cp=500,
        solidos_pct=5
    )

    print("\n===== MODELO PCP AVANZADO =====\n")

    for k, v in res.items():
        print(f"{k}: {v:.2f}")
``
