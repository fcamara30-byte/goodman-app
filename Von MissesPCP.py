import math


def calcular_pcp(
    rpm,
    desplazamiento,
    presion_linea,
    nivel,
    densidad,
    eficiencia=0.6
):
    """
    rpm: revoluciones por minuto
    desplazamiento: m3/d por RPM
    presion_linea: kg/cm2
    nivel: metros
    densidad: kg/m3
    """

    # --- PRODUCCIÓN ---
    produccion = desplazamiento * rpm

    # --- PRESIONES ---
    presion_nivel = (nivel * densidad) / 10000  # kg/cm2
    presion_total = presion_linea + presion_nivel

    # --- POTENCIAS ---
    potencia_hidraulica = produccion * presion_total * 0.0014
    potencia_consumida = potencia_hidraulica / eficiencia

    # --- TORQUE ---
    k = 5252
    torque_lbft = (k * potencia_consumida) / rpm
    torque_nm = torque_lbft * 1.35582

    return {
        "Produccion (m3/d)": produccion,
        "Presion Nivel (kg/cm2)": presion_nivel,
        "Presion Total (kg/cm2)": presion_total,
        "Potencia Hidraulica (HP)": potencia_hidraulica,
        "Potencia Consumida (HP)": potencia_consumida,
        "Torque (lb-ft)": torque_lbft,
        "Torque (Nm)": torque_nm
    }


# =========================
# EJECUCIÓN INTERACTIVA
# =========================
if __name__ == "__main__":

    print("\n=== CALCULO PCP - TORQUE ===\n")

    rpm = float(input("RPM: "))
    desplazamiento = float(input("Desplazamiento [m3/d/RPM]: "))
    presion_linea = float(input("Presion de linea [kg/cm2]: "))
    nivel = float(input("Nivel dinamico [m]: "))
    densidad = float(input("Densidad fluido [kg/m3]: "))

    resultados = calcular_pcp(
        rpm,
        desplazamiento,
        presion_linea,
        nivel,
        densidad
    )

    print("\n===== RESULTADOS =====\n")

    for k, v in resultados.items():
        print(f"{k}: {v:.2f}")

