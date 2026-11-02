import json
import math
from collections import Counter

import pytest

from src.busqueda import (
    RANURAS,
    Consultor,
    Medida,
    PresupuestoAgotado,
    ascenso_coordenadas,
    backtracking,
    costo_successive_halving,
    cota_parcial,
    descartar_con_trazas,
    enumerar,
    max_candidatos,
    mejores_opciones,
    muestrear_configs,
    successive_halving,
    tamano_espacio,
    validar_entrega,
)
from src.oraculo_sintetico import OraculoSintetico


def caso(k=4, n=40, semilla=3, **kw):
    return OraculoSintetico({r: k for r in RANURAS}, n, semilla=semilla, **kw)


def consultor(o, presupuesto=None):
    return Consultor(lambda c, l, s: o.evaluar(c, l, s), o.instancias, presupuesto)


def peor_inicio(o):
    return {r: (o.optimo[r] + 1) % len(o.opciones[r]) for r in RANURAS} | {"temperatura": 0.0}


def test_el_optimo_sintetico_coincide_con_la_fuerza_bruta():
    o = caso(k=3)
    mejor = max(enumerar(o.opciones), key=lambda c: o.evaluar(c).precision)
    assert o.evaluar(mejor).precision == 1.0
    assert all(mejor[r] == o.optimo[r] for r in RANURAS)


def test_consultor_no_cobra_dos_veces_y_cobra_solo_lo_nuevo():
    o = caso()
    c = consultor(o)
    config = peor_inicio(o)
    c.medir(config, 10)
    c.medir(config, 10)
    assert c.generaciones == 10
    c.medir(config, 25)
    assert c.generaciones == 25
    assert [fila["nuevas"] for fila in c.registro] == [10, 0, 15]


def test_consultor_rechaza_exceder_el_presupuesto_sin_cobrar():
    o = caso()
    c = consultor(o, presupuesto=15)
    c.medir(peor_inicio(o), 10)
    with pytest.raises(PresupuestoAgotado):
        c.medir({**peor_inicio(o), "rol": o.optimo["rol"]}, 10)
    assert c.generaciones == 10
    assert len(c.registro) == 1


def test_consultor_guarda_registro_json(tmp_path):
    o = caso()
    c = consultor(o)
    c.medir(peor_inicio(o), 5)
    ruta = tmp_path / "registro.json"
    c.guardar(ruta)
    assert json.loads(ruta.read_text(encoding="utf-8"))[0]["n"] == 5


def test_ascenso_recupera_el_optimo_cuando_las_ranuras_son_independientes():
    o = caso()
    r = ascenso_coordenadas(consultor(o), o.opciones, peor_inicio(o))
    assert r.precision == 1.0
    assert all(r.mejor[x] == o.optimo[x] for x in RANURAS)
    assert not r.agotado


def test_ascenso_primera_pasada_cuesta_a_lo_sumo_suma_de_k_por_n():
    o = caso(k=4, n=20)
    c = consultor(o)
    ascenso_coordenadas(c, o.opciones, peor_inicio(o), max_pasadas=1)
    assert c.generaciones <= (1 + 5 * 4) * 20


def test_ascenso_se_detiene_al_agotar_el_presupuesto():
    o = caso()
    B = 130
    c = consultor(o, B)
    r = ascenso_coordenadas(c, o.opciones, peor_inicio(o))
    assert r.agotado
    assert c.generaciones <= B
    assert r.mejor is not None


def test_descartar_con_trazas_usa_el_exceso_de_familias_y_protege_actual():
    medidas = {
        0: Medida(0.20, 100, Counter({"a": 10})),
        1: Medida(0.10, 100, Counter({"a": 10, "b": 7})),
        2: Medida(0.19, 100, Counter({"a": 11})),
        3: Medida(0.05, 100, Counter({"a": 12})),
    }
    assert descartar_con_trazas(medidas, actual=3, margen=0.05) == {1: {"b": 7}}


def test_filtro_retira_opciones_de_las_pasadas_siguientes():
    o = caso()
    r = ascenso_coordenadas(
        consultor(o), o.opciones, peor_inicio(o),
        filtro=lambda ranura, m, actual: descartar_con_trazas(m, actual, 0.01),
    )
    assert r.precision == 1.0
    assert r.detalle["descartes"]


@pytest.mark.parametrize("k", [3, 5, 8, 15])
def test_costo_sh_coincide_con_la_formula_cerrada(k):
    assert costo_successive_halving(2**k, 2) == 2**k * 2 * k


def test_tope_de_instancias_en_sh():
    assert costo_successive_halving(2**15, 2, n_max=100) < 2**15 * 2 * 15
    o = caso(k=4, n=16)
    c = consultor(o)
    candidatos = muestrear_configs(o.opciones, 256, semilla=1)
    r = successive_halving(c, candidatos, n0=2)
    assert all(ronda["n_r"] <= 16 for ronda in r.detalle["rondas"])
    assert max(fila["n"] for fila in c.registro) <= 16


def test_sh_gasta_lo_previsto_con_reutilizacion():
    o = caso(k=4, n=100)
    c = consultor(o)
    candidatos = muestrear_configs(o.opciones, 64, semilla=1)
    successive_halving(c, candidatos, n0=2, n_max=100)
    assert c.generaciones <= costo_successive_halving(64, 2, 100, reutiliza=True) + 100
    assert c.generaciones >= costo_successive_halving(64, 2, 100, reutiliza=True) - 100


def test_max_candidatos_cabe_en_el_presupuesto():
    B = 3000
    tamano = max_candidatos(B, 2, 100)
    assert costo_successive_halving(tamano, 2, 100, reutiliza=True) <= B
    assert costo_successive_halving(tamano * 2, 2, 100, reutiliza=True) > B


def test_sh_respeta_presupuesto():
    o = caso(k=4, n=100)
    c = consultor(o, 200)
    r = successive_halving(c, muestrear_configs(o.opciones, 128, semilla=1), n0=2)
    assert r.agotado
    assert c.generaciones <= 200


def test_muestreo_reproducible_sin_repetidos_y_con_temperaturas():
    o = caso()
    a = muestrear_configs(o.opciones, 200, semilla=5, temperaturas=(0.0, 0.3, 0.7))
    b = muestrear_configs(o.opciones, 200, semilla=5, temperaturas=(0.0, 0.3, 0.7))
    assert a == b
    assert len({tuple(sorted(c.items())) for c in a}) == 200
    assert {c["temperatura"] for c in a} <= {0.0, 0.3, 0.7}


def test_tamano_del_espacio_real():
    opciones = {r: list(range(8)) for r in RANURAS}
    assert tamano_espacio(opciones) == 32768
    assert tamano_espacio(opciones, temperaturas=(0.0, 0.3, 0.7)) == 98304


@pytest.mark.parametrize("semilla", range(8))
def test_backtracking_encuentra_el_optimo_de_fuerza_bruta(semilla):
    o = caso(k=3, n=30, semilla=semilla, imposibles=0.2)
    c = consultor(o)
    r = backtracking(c, o.opciones, cota_parcial(c))
    exacto = max(o.evaluar(x).precision for x in enumerar(o.opciones))
    assert math.isclose(r.precision, exacto)
    assert not r.agotado


def test_backtracking_poda_frente_al_peor_caso():
    o = caso(k=4, n=40, dano=0.4)
    c = consultor(o)
    r = backtracking(c, o.opciones, cota_parcial(c))
    assert r.detalle["podas"] > 0
    assert r.detalle["hojas"] < tamano_espacio(o.opciones)


def test_backtracking_sin_poda_recorre_todas_las_hojas():
    o = caso(k=3, n=10)
    c = consultor(o)
    r = backtracking(c, o.opciones, cota=lambda parcial: math.inf)
    assert r.detalle["hojas"] == 3**5
    assert r.detalle["podas"] == 0
    assert r.precision == 1.0


@pytest.mark.parametrize("k,n", [(2, 7), (3, 10), (4, 5)])
def test_peor_caso_de_backtracking_coincide_con_t_del_informe(k, n):
    """T = n · Σ_{j=1..d} k^j cuando ninguna cota permite podar."""
    o = caso(k=k, n=n, imposibles=0.5, semilla=2)
    c = consultor(o)
    r = backtracking(c, o.opciones, cota_parcial(c, holgura=1.0))
    assert r.precision < 1.0
    assert r.detalle["podas"] == 0
    assert c.generaciones == n * sum(k**j for j in range(1, len(RANURAS) + 1))


def test_costo_con_tope_coincide_con_la_formula_del_informe():
    """|C|·n0·r* + N·|C|·(2^(1-r*) - 2^(1-R)), con |C| = 2^R."""
    R, n0, N, r_tope = 10, 2, 100, 6
    C = 2**R
    formula = C * n0 * r_tope + N * C * (2 ** (1 - r_tope) - 2 ** (1 - R))
    assert costo_successive_halving(C, n0, N) == formula


def test_mejores_opciones_ordena_por_la_mejor_precision_observada():
    registro = [
        {"config": {"rol": 0, "estilo": 1}, "n": 100, "precision": 0.1},
        {"config": {"rol": 1, "estilo": 1}, "n": 100, "precision": 0.3},
        {"config": {"rol": 2, "estilo": 1}, "n": 100, "precision": 0.2},
        {"config": {"rol": 0, "estilo": 1}, "n": 10, "precision": 0.9},
    ]
    assert mejores_opciones(registro, {"rol": [0, 1, 2]}, ("rol",), 2, 100) == {"rol": [1, 2]}


def test_backtracking_respeta_presupuesto():
    o = caso(k=4, n=40)
    c = consultor(o, 150)
    r = backtracking(c, o.opciones, cota_parcial(c))
    assert r.agotado
    assert c.generaciones <= 150


def test_ruido_es_reproducible_y_depende_de_la_semilla():
    o = caso(ruido=0.2)
    config = peor_inicio(o)
    assert o.evaluar(config, semilla=1).precision == o.evaluar(config, semilla=1).precision
    resultados = {o.evaluar(config, semilla=s).precision for s in range(8)}
    assert len(resultados) > 1


ENTREGA = {
    "grupo": "G01",
    "config": {"rol": 1, "estrategia": 2, "formato": 3, "estilo": 4, "cierre": 5, "temperatura": 0.3},
    "semana": 6,
}


def test_validar_entrega_acepta_el_formato_correcto():
    assert validar_entrega(json.loads(json.dumps(ENTREGA)))


@pytest.mark.parametrize(
    "cambio",
    [
        {"grupo": ""},
        {"semana": "6"},
        {"semana": True},
        {"config": {**ENTREGA["config"], "rol": 8}},
        {"config": {**ENTREGA["config"], "cierre": 1.0}},
        {"config": {**ENTREGA["config"], "temperatura": 0.5}},
        {"config": {k: v for k, v in ENTREGA["config"].items() if k != "estilo"}},
        {"extra": 1},
    ],
)
def test_validar_entrega_rechaza_formatos_invalidos(cambio):
    with pytest.raises(ValueError):
        validar_entrega({**ENTREGA, **cambio})
