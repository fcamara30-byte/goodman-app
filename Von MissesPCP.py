import tkinter as tk
from tkinter import ttk
import math

# -------------------------
# DATA VARILLAS
# -------------------------
RODS = {
    "7/8": {"d": 0.875, "peso": 2.22},
    "1": {"d": 1.0, "peso": 2.67},
    "1 1/8": {"d": 1.125, "peso": 3.37}
}

def calcular():

    try:
        rpm = float(entry_rpm.get())
        prod = float(entry_prod.get())
        pres_linea = float(entry_presion.get())
        nivel = float(entry_nivel.get())
        densidad = float(entry_densidad.get())
        visc = float(entry_visc.get())
        solidos = float(entry_solidos.get())
        profundidad = float(entry_prof.get())
        rod = combo_rod.get()

        # -------------------------
        # PCP
        # -------------------------
        pres_nivel = (nivel * densidad)/10000
        pres_total = pres_linea + pres_nivel

        pot_h = prod * pres_total * 0.0014
        pot_c = pot_h / 0.6

        torque = (5252 * pot_c) / rpm

        # -------------------------
        # FACTOR FLUIDO
        # -------------------------
        f_visc = 1 + (visc / 1000)
        f_sol = 1 + (solidos / 100)
        f_total = f_visc * f_sol

        torque_corr = torque * f_total

        # -------------------------
        # VARILLA
        # -------------------------
        d = RODS[rod]["d"] * 0.0254
        r = d/2

        A = math.pi * d**2 / 4
        J = math.pi * d**4 / 32

        peso = RODS[rod]["peso"] * 47.88  # N/m
        peso_total = peso * profundidad

        carga_fluido = densidad * 9.81 * profundidad * A
        F = peso_total + carga_fluido

        sigma = F/A/1e6
        tau = (torque_corr*1.35582*r)/J/1e6

        von = math.sqrt(sigma**2 + 3*tau**2)

        # -------------------------
        # OUTPUT
        # -------------------------
        out_torque.config(text=f"{torque:.1f} lb-ft")
        out_von.config(text=f"{von:.1f} MPa")
        out_tau.config(text=f"{tau:.1f} MPa")
        out_sigma.config(text=f"{sigma:.1f} MPa")

    except:
        out_torque.config(text="Error")


# -------------------------
# UI
# -------------------------
root = tk.Tk()
root.title("PCP Calculator PRO")

# Inputs
labels = [
    ("RPM", "350"),
    ("Producción m3/d", "150"),
    ("Presión línea kg/cm2", "14"),
    ("Nivel m", "570"),
    ("Densidad kg/m3", "840"),
    ("Viscosidad cP", "300"),
    ("% Sólidos", "5"),
    ("Profundidad m", "600")
]

entries = []

for i, (text, val) in enumerate(labels):
    tk.Label(root, text=text).grid(row=i, column=0)
    e = tk.Entry(root)
    e.insert(0, val)
    e.grid(row=i, column=1)
    entries.append(e)

(entry_rpm, entry_prod, entry_presion, entry_nivel,
 entry_densidad, entry_visc, entry_solidos, entry_prof) = entries

# Varillas
tk.Label(root, text="Varilla").grid(row=8, column=0)
combo_rod = ttk.Combobox(root, values=list(RODS.keys()))
combo_rod.set("1")
combo_rod.grid(row=8, column=1)

# Botón
tk.Button(root, text="CALCULAR", command=calcular, bg="green").grid(row=9, columnspan=2)

# Outputs
tk.Label(root, text="Torque").grid(row=10, column=0)
out_torque = tk.Label(root, text="-")
out_torque.grid(row=10, column=1)

tk.Label(root, text="Von Mises").grid(row=11, column=0)
out_von = tk.Label(root, text="-")
out_von.grid(row=11, column=1)

tk.Label(root, text="Torsión").grid(row=12, column=0)
out_tau = tk.Label(root, text="-")
out_tau.grid(row=12, column=1)

tk.Label(root, text="Axial").grid(row=13, column=0)
out_sigma = tk.Label(root, text="-")
out_sigma.grid(row=13, column=1)

root.mainloop()
