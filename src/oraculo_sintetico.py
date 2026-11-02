"""Oráculo simulado para probar la búsqueda sin GPU.

Modelo: cada opción de una ranura rompe un conjunto de instancias, y una instancia
vale 1 solo si ninguna opción elegida la rompe (todo-o-nada). Una opción por ranura
no rompe nada, de modo que el óptimo se conoce de antemano. Agregar instrucciones
nunca sube la precisión, por lo que la cota de `src.busqueda.cota_parcial` es
admisible aquí.

Nada de este archivo reproduce el catálogo ni la lógica de `oraculo.py`.
"""

import random
import zlib
from dataclasses import dataclass


@dataclass
class ResultadoSintetico:
    precision: float
    trazas: list
    n: int


class OraculoSintetico:
    """Instancia sintética reproducible.

    Parameters
    ----------
    opciones_por_ranura:
        `{ranura: k}` con el número de opciones de cada ranura.
    n_instancias:
        Cantidad de instancias generadas.
    dano:
        Probabilidad de que una opción no óptima rompa una instancia.
    imposibles:
        Fracción de instancias que fallan siempre. Fija el techo de precisión.
    ruido:
        Probabilidad de invertir el resultado de cada par (config, instancia).
        Con `ruido > 0` el oráculo deja de ser exacto; depende de la semilla.
    """

    def __init__(self, opciones_por_ranura, n_instancias, semilla=0, dano=0.3,
                 imposibles=0.0, ruido=0.0):
        rng = random.Random(semilla)
        self.opciones = {r: list(range(k)) for r, k in opciones_por_ranura.items()}
        self.instancias = [{"id": i} for i in range(n_instancias)]
        self.ruido = ruido
        self.semilla = semilla
        self.imposibles = {
            i for i in range(n_instancias) if rng.random() < imposibles
        }
        self.optimo = {r: rng.choice(v) for r, v in self.opciones.items()}
        self.rompe = {}
        for ranura, valores in self.opciones.items():
            for opcion in valores:
                if opcion == self.optimo[ranura]:
                    self.rompe[ranura, opcion] = frozenset()
                else:
                    self.rompe[ranura, opcion] = frozenset(
                        i for i in range(n_instancias) if rng.random() < dano
                    )

    def _pasa(self, config, instancia, semilla):
        iid = instancia["id"]
        violo = None
        if iid in self.imposibles:
            violo = "imposible"
        else:
            for ranura in self.opciones:
                if ranura in config and iid in self.rompe[ranura, config[ranura]]:
                    violo = f"familia:{ranura}"
                    break
        pasa = violo is None
        if self.ruido:
            texto = f"{sorted(config.items())}|{iid}|{semilla}|{self.semilla}"
            if random.Random(zlib.crc32(texto.encode())).random() < self.ruido:
                pasa = not pasa
                violo = None if pasa else "familia:ruido"
        return pasa, violo

    def evaluar(self, config, instancias=None, semilla=1):
        """Misma interfaz que `Oraculo.evaluar`: precisión y trazas de los fallos."""
        instancias = self.instancias if instancias is None else instancias
        aciertos, trazas = 0, []
        for instancia in instancias:
            pasa, violo = self._pasa(config, instancia, semilla)
            if pasa:
                aciertos += 1
            else:
                trazas.append({"id": instancia["id"], "violo": violo, "salida": ""})
        return ResultadoSintetico(aciertos / len(instancias), trazas, len(instancias))
