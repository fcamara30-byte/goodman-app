class PCPModel:

    def __init__(
        self,
        rpm,
        desplazamiento_m3_d_rpm,
        presion_linea_kgcm2,
        nivel_m,
        densidad_kg_m3,
        eficiencia=0.6
    ):
        self.rpm = rpm
        self.despl = desplazamiento_m3_d_rpm
        self.presion_linea = presion_linea_kgcm2
        self.nivel = nivel_m
        self.densidad = densidad_kg_m3
        self.eficiencia = eficiencia
        self.k = 5252  # constante torque

    # =========================
    # PRODUCCION
    # =========================
    def produccion(self):
        return self.despl * self.rpm  # m3/d

    # =========================
    # PRESIONES
    # =========================
    def presion_nivel(self):
        return (self.nivel * self.densidad) / 10000  # kg/cm2

    def presion_total(self):
        return self.presion_linea + self.presion_nivel()

    # =========================
    # POTENCIAS
    # =========================
    def potencia_hidraulica(self):
        return self.produccion() * self.presion_total() * 0.0014

    def potencia_consumida(self):
        return self.potencia_hidraulica() / self.eficiencia

    # =========================
    # TORQUE
    # =========================
    def torque_lbft(self):
        return (self.k * self.potencia_consumida()) / self.rpm

    def torque_nm(self):
        return self.torque_lbft() * 1.35582

    # =========================
    # REPORTE
    # =========================
    def resumen(self):
        print("\n===== MODELO PCP =====")

        print(f"RPM: {self.rpm}")
        print(f"Producción: {self.produccion():.2f} m3/d")

        print("\n--- PRESIONES ---")
        print(f"Presión de línea: {self.presion_linea:.2f} kg/cm2")
        print(f"Presión de nivel: {self.presion_nivel():.2f} kg/cm2")
        print(f"Presión total: {self.presion_total():.2f} kg/cm2")

        print("\n--- POTENCIAS ---")
        print(f"Potencia hidráulica: {self.potencia_hidraulica():.2f} HP")
        print(f"Potencia consumida: {self.potencia_consumida():.2f} HP")

        print("\n--- TORQUE ---")
        print(f"Torque: {self.torque_lbft():.2f} lb-ft")
        print(f"Torque: {self.torque_nm():.2f} Nm")


# ===================================
# EJEMPLO (basado en tu planilla)
# ===================================
if __name__ == "__main__":

    modelo = PCPModel(
        rpm=350,
        desplazamiento_m3_d_rpm=0.43,  # ajustar según bomba
        presion_linea_kgcm2=200,
        nivel_m=600,
        densidad_kg_m3=950,  # equivalente ~16 API
        eficiencia=0.6
    )

    modelo.resumen()

