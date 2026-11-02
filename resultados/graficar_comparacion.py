"""Gráfica del informe: mejor precisión de configuraciones completas según el gasto.

Uso: python resultados/graficar_comparacion.py
Solo cuenta configuraciones con las 5 ranuras medidas con las 100 instancias, porque
el backtracking también registra prompts parciales (sus cotas) y Successive Halving
mide la mayoría de candidatos con menos instancias.
"""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

DIR = Path(__file__).parent
RANURAS = ("rol", "estrategia", "formato", "estilo", "cierre")
N = 100

fig, ax = plt.subplots(figsize=(8, 4.8))
for nombre, archivo, color in [
    ("Ascenso por coordenadas", "registro_coordenadas.json", "#1f77b4"),
    ("Backtracking", "registro_backtracking.json", "#ff7f0e"),
    ("Successive Halving", "registro_halving.json", "#2ca02c"),
]:
    registro = json.load(open(DIR / archivo, encoding="utf-8"))
    total = registro[-1]["acumuladas"]
    x, y, mejor = [], [], None
    for fila in registro:
        if fila["n"] == N and all(r in fila["config"] for r in RANURAS):
            mejor = fila["precision"] if mejor is None else max(mejor, fila["precision"])
            x.append(fila["acumuladas"])
            y.append(mejor)
    x.append(total)
    y.append(mejor)
    ax.step(x, [v * 100 for v in y], where="post", label=nombre, color=color, linewidth=2)
    ax.plot(x[0], y[0] * 100, "o", color=color)

ax.axvline(1803, color="gray", linestyle="--", linewidth=1)
ax.text(1795, 1, "B = 1803", rotation=90, ha="right", va="bottom", color="gray")
ax.set_xlabel("generaciones acumuladas del método")
ax.set_ylabel("mejor precisión medida (%)")
ax.set_title("Configuraciones completas medidas con las 100 instancias de búsqueda")
ax.set_xlim(0, 1900)
ax.set_ylim(0, 18)
ax.grid(alpha=0.3)
ax.legend(loc="upper left")
fig.savefig(DIR / "comparacion_informe.png", dpi=150, bbox_inches="tight")
print("guardado", DIR / "comparacion_informe.png")
