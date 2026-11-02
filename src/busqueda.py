"""Algoritmos de búsqueda del Proyecto Oráculo (ADAG1, Grupo 1).

Este módulo no depende de torch ni del modelo: todos los algoritmos consultan una
función `evaluar(config, instancias, semilla)` que devuelve un objeto con
`precision` y `trazas`. En Colab esa función es el oráculo real; en las pruebas es
`src.oraculo_sintetico.OraculoSintetico`.

Unidad de costo: una *generación*, es decir, un par (configuración, instancia)
nuevo. Volver a medir un par ya pagado no cuesta, igual que en el caché del oráculo.
"""

import itertools
import json
import math
import random
from collections import Counter
from dataclasses import dataclass, field

RANURAS = ("rol", "estrategia", "formato", "estilo", "cierre")
TEMPERATURAS = (0.0, 0.3, 0.7)


class PresupuestoAgotado(Exception):
    """La siguiente medición superaría el presupuesto `B`."""


@dataclass
class Medida:
    """Resultado de medir una configuración sobre `n` instancias."""

    precision: float
    n: int
    fallos: Counter = field(default_factory=Counter)


@dataclass
class ResultadoBusqueda:
    """Salida común de los tres algoritmos."""

    metodo: str
    mejor: dict
    precision: float
    generaciones: int
    agotado: bool
    detalle: dict = field(default_factory=dict)


def _clave(config):
    return tuple(sorted(config.items()))


class Consultor:
    """Mide configuraciones, cobra el presupuesto y deja el registro.

    Siempre mide un prefijo de `instancias`: ampliar de `n` a `n'` instancias
    solo cuesta las `n' - n` nuevas.
    """

    def __init__(self, evaluar, instancias, presupuesto=None, semilla=1):
        self._evaluar = evaluar
        self.instancias = list(instancias)
        self.presupuesto = presupuesto
        self.semilla = semilla
        self.generaciones = 0
        self.registro = []
        self._pagadas = {}

    def costo(self, config, n=None):
        """Generaciones nuevas que costaría medir `config` sobre `n` instancias."""
        n = self._tamano(n)
        return max(0, n - self._pagadas.get(_clave(config), 0))

    def _tamano(self, n):
        return len(self.instancias) if n is None else min(n, len(self.instancias))

    def medir(self, config, n=None):
        """Devuelve la `Medida` de `config`, o lanza `PresupuestoAgotado`."""
        n = self._tamano(n)
        nuevas = self.costo(config, n)
        if self.presupuesto is not None and self.generaciones + nuevas > self.presupuesto:
            raise PresupuestoAgotado(
                f"faltan {nuevas} generaciones y quedan "
                f"{self.presupuesto - self.generaciones}"
            )
        r = self._evaluar(config, self.instancias[:n], self.semilla)
        clave = _clave(config)
        self._pagadas[clave] = max(self._pagadas.get(clave, 0), n)
        self.generaciones += nuevas
        fallos = Counter(t["violo"] for t in r.trazas)
        self.registro.append(
            {
                "orden": len(self.registro) + 1,
                "config": dict(config),
                "n": n,
                "precision": r.precision,
                "nuevas": nuevas,
                "acumuladas": self.generaciones,
                "fallos": dict(fallos),
            }
        )
        return Medida(r.precision, n, fallos)

    def guardar(self, ruta):
        """Escribe el registro en JSON para citarlo desde el informe."""
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(self.registro, f, indent=1, ensure_ascii=False)


def descartar_con_trazas(medidas, actual, margen):
    """Elige qué opciones de una ranura salen de las pasadas siguientes.

    Se descarta una opción si su precisión queda al menos `margen` por debajo de
    la mejor. Devuelve `{opcion: familias}`, donde `familias` son las restricciones
    que esa opción hizo fallar más veces que la mejor: es la evidencia de las trazas.
    Nunca descarta la opción actual ni la mejor.
    """
    mejor = max(medidas, key=lambda o: medidas[o].precision)
    referencia = medidas[mejor]
    descartadas = {}
    for opcion, medida in medidas.items():
        if opcion in (mejor, actual):
            continue
        if medida.precision <= referencia.precision - margen:
            exceso = medida.fallos - referencia.fallos
            descartadas[opcion] = dict(exceso.most_common())
    return descartadas


def ascenso_coordenadas(consultor, opciones, inicial, ranuras=RANURAS, max_pasadas=3,
                        n=None, filtro=None):
    """Ascenso por coordenadas: mejora una ranura a la vez hasta converger.

    Solo cambia de opción ante una mejora estricta. `filtro(ranura, medidas, actual)`
    es opcional y devuelve las opciones a retirar, como `descartar_con_trazas`.
    Costo por pasada, sin caché: `Σ k_i · n` generaciones.
    """
    actual = dict(inicial)
    activas = {r: list(opciones[r]) for r in ranuras}
    pasadas, descartes = [], []
    agotado = False
    mejor_precision = None

    try:
        mejor_precision = consultor.medir(actual, n).precision
        for pasada in range(1, max_pasadas + 1):
            cambios = 0
            for ranura in ranuras:
                medidas = {}
                for opcion in activas[ranura]:
                    medidas[opcion] = consultor.medir({**actual, ranura: opcion}, n)
                ganadora = max(medidas, key=lambda o: medidas[o].precision)
                if medidas[ganadora].precision > mejor_precision:
                    actual[ranura] = ganadora
                    mejor_precision = medidas[ganadora].precision
                    cambios += 1
                if filtro is not None:
                    retiradas = filtro(ranura, medidas, actual[ranura])
                    activas[ranura] = [o for o in activas[ranura] if o not in retiradas]
                    if retiradas:
                        descartes.append(
                            {"pasada": pasada, "ranura": ranura, "opciones": retiradas}
                        )
            pasadas.append({"pasada": pasada, "cambios": cambios, "precision": mejor_precision})
            if cambios == 0:
                break
    except PresupuestoAgotado:
        agotado = True

    return ResultadoBusqueda(
        "ascenso_coordenadas", actual, mejor_precision if mejor_precision is not None else 0.0,
        consultor.generaciones, agotado, {"pasadas": pasadas, "descartes": descartes},
    )


def costo_successive_halving(candidatos, n0, n_max=None, reutiliza=False):
    """Generaciones de Successive Halving.

    Con `reutiliza=False` y `|C| = 2^R` sin tope da `|C|·n0·log2|C|`. Con
    `reutiliza=True` cada ronda paga solo las instancias nuevas, como `Consultor`.
    """
    vivos, r, total, previo = candidatos, 0, 0, 0
    while vivos > 1:
        n_r = n0 * 2**r if n_max is None else min(n0 * 2**r, n_max)
        total += vivos * (n_r - previo if reutiliza else n_r)
        previo = n_r
        vivos = math.ceil(vivos / 2)
        r += 1
    return total


def max_candidatos(presupuesto, n0, n_max):
    """Mayor potencia de 2 de candidatos cuyo costo con reutilización cabe en `B`."""
    candidatos = 2
    while costo_successive_halving(candidatos * 2, n0, n_max, reutiliza=True) <= presupuesto:
        candidatos *= 2
    if costo_successive_halving(candidatos, n0, n_max, reutiliza=True) > presupuesto:
        raise ValueError("el presupuesto no alcanza ni para 2 candidatos")
    return candidatos


def muestrear_configs(opciones, tamano, semilla=0, ranuras=RANURAS, temperaturas=(0.0,)):
    """Toma `tamano` configuraciones distintas del espacio, con semilla fija."""
    ejes = [list(opciones[r]) for r in ranuras] + [list(temperaturas)]
    total = math.prod(len(e) for e in ejes)
    if tamano > total:
        raise ValueError(f"se piden {tamano} configuraciones de {total}")
    configs = []
    for indice in random.Random(semilla).sample(range(total), tamano):
        valores = []
        for eje in reversed(ejes):
            indice, resto = divmod(indice, len(eje))
            valores.append(eje[resto])
        valores.reverse()
        configs.append(dict(zip(ranuras, valores[:-1]), temperatura=valores[-1]))
    return configs


def successive_halving(consultor, candidatos, n0, n_max=None):
    """Divide y vencerás por rondas, con tope `n_r = min(n0·2^r, n_max)`.

    El tope es necesario: sin él, `n_r` supera las instancias disponibles. Los
    empates conservan el orden de la ronda anterior.
    """
    n_max = len(consultor.instancias) if n_max is None else min(n_max, len(consultor.instancias))
    vivos = [dict(c) for c in candidatos]
    rondas = []
    agotado = False
    r = 0
    ultimas = {}

    try:
        while len(vivos) > 1:
            n_r = min(n0 * 2**r, n_max)
            medidas = [(c, consultor.medir(c, n_r)) for c in vivos]
            medidas.sort(key=lambda par: par[1].precision, reverse=True)
            ultimas = {_clave(c): m.precision for c, m in medidas}
            vivos = [c for c, _ in medidas[: math.ceil(len(vivos) / 2)]]
            rondas.append(
                {"ronda": r, "n_r": n_r, "candidatos": len(medidas), "mejor": medidas[0][1].precision}
            )
            r += 1
        precision = consultor.medir(vivos[0], n_max).precision
    except PresupuestoAgotado:
        agotado = True
        precision = ultimas.get(_clave(vivos[0]), 0.0)

    return ResultadoBusqueda(
        "successive_halving", vivos[0], precision, consultor.generaciones, agotado,
        {"rondas": rondas},
    )


def cota_parcial(consultor, n=None, holgura=0.0):
    """Cota superior: mide el prompt sin las ranuras aún no decididas.

    Solo es admisible si agregar una instrucción nunca aumenta la precisión. En el
    oráculo sintético eso se cumple; con un modelo real es un supuesto, y por eso el
    backtracking real no certifica optimalidad global. `holgura` relaja la cota.
    """
    def cota(parcial):
        return min(1.0, consultor.medir(parcial, n).precision + holgura)

    return cota


def backtracking(consultor, opciones, cota, base=None, ranuras=RANURAS, n=None):
    """Backtracking con poda por cota superior sobre el árbol de ranuras.

    Corta una rama si su cota no supera la mejor precisión hallada. Peor caso: visita
    todas las hojas, `O(|C|·n)` generaciones, además del costo de las cotas. Los hijos
    se exploran de mayor a menor cota. Es exacto si la cota es admisible y no se
    agota el presupuesto.
    """
    base = dict(base or {"temperatura": 0.0})
    estado = {"mejor": None, "precision": -1.0, "nodos": 0, "hojas": 0, "podas": 0}

    def explorar(parcial, profundidad):
        estado["nodos"] += 1
        if profundidad == len(ranuras):
            estado["hojas"] += 1
            precision = consultor.medir(parcial, n).precision
            if precision > estado["precision"]:
                estado["mejor"], estado["precision"] = dict(parcial), precision
            return
        ranura = ranuras[profundidad]
        hijos = [{**parcial, ranura: o} for o in opciones[ranura]]
        if profundidad + 1 < len(ranuras):
            hijos = sorted(((cota(h), i, h) for i, h in enumerate(hijos)), reverse=True,
                           key=lambda t: (t[0], -t[1]))
        else:
            hijos = [(math.inf, i, h) for i, h in enumerate(hijos)]
        for valor, _, hijo in hijos:
            if valor <= estado["precision"]:
                estado["podas"] += 1
                continue
            explorar(hijo, profundidad + 1)

    agotado = False
    try:
        explorar(base, 0)
    except PresupuestoAgotado:
        agotado = True

    detalle = {k: estado[k] for k in ("nodos", "hojas", "podas")}
    return ResultadoBusqueda(
        "backtracking", estado["mejor"], max(estado["precision"], 0.0),
        consultor.generaciones, agotado, detalle,
    )


def mejores_opciones(registro, opciones, ranuras, tope, n):
    """Conserva las `tope` opciones con mejor precisión observada sobre `n` instancias.

    Sirve para acotar el backtracking real: su resultado es exacto, a lo sumo, dentro
    de este subespacio reducido.
    """
    mejores = {}
    for ranura in ranuras:
        vistas = {o: -1.0 for o in opciones[ranura]}
        for fila in registro:
            valor = fila["config"].get(ranura)
            if fila["n"] == n and valor in vistas:
                vistas[valor] = max(vistas[valor], fila["precision"])
        mejores[ranura] = sorted(vistas, key=lambda o: vistas[o], reverse=True)[:tope]
    return mejores


def tamano_espacio(opciones, ranuras=RANURAS, temperaturas=(0.0,)):
    """`|C| = Π k_i · |T|`."""
    return math.prod(len(opciones[r]) for r in ranuras) * len(temperaturas)


def enumerar(opciones, ranuras=RANURAS, temperaturas=(0.0,)):
    """Recorre el espacio completo. Solo es viable en instancias pequeñas."""
    for combo in itertools.product(*(opciones[r] for r in ranuras), temperaturas):
        yield dict(zip(ranuras, combo[:-1]), temperatura=combo[-1])


def validar_entrega(entrega, opciones_por_ranura=8, temperaturas=TEMPERATURAS):
    """Comprueba el formato de `entrega.json`. Lanza `ValueError` si no cumple."""
    if set(entrega) != {"grupo", "config", "semana"}:
        raise ValueError("entrega.json debe traer exactamente grupo, config y semana")
    if not isinstance(entrega["grupo"], str) or not entrega["grupo"]:
        raise ValueError("grupo debe ser un texto no vacío")
    if type(entrega["semana"]) is not int or entrega["semana"] < 0:
        raise ValueError("semana debe ser un entero no negativo")
    config = entrega["config"]
    if set(config) != set(RANURAS) | {"temperatura"}:
        raise ValueError("config debe traer las 5 ranuras y la temperatura")
    for ranura in RANURAS:
        valor = config[ranura]
        if type(valor) is not int or not 0 <= valor < opciones_por_ranura:
            raise ValueError(f"índice inválido en {ranura}: {valor!r}")
    if config["temperatura"] not in temperaturas:
        raise ValueError(f"temperatura inválida: {config['temperatura']!r}")
    return True
