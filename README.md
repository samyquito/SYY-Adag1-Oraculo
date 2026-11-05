# Proyecto Oráculo (ADAG1)

Análisis y Diseño de Algoritmos · 2026-B · Grupo 1

Búsqueda de la mejor configuración de prompt para un LLM: se elige un índice
de rol, estrategia, formato, estilo y cierre, más la temperatura, buscando
maximizar la precisión con un presupuesto limitado de consultas al modelo.

> **Estado:** primera entrega. Búsqueda real completada en Colab (T4, `qwen17b`).

## Resultado

Configuración entregada (`entrega.json`), elegida por Successive Halving:
rol 7, estrategia 0, formato 0, estilo 2, cierre 1, temperatura 0.7.

| Método | Precisión en búsqueda (n = 100) | Generaciones |
| --- | --- | --- |
| Ascenso por coordenadas | 8% | 1800 |
| Successive Halving | **16%** | 968 |
| Backtracking en subespacio | 8% | 1800 |

En validación obtuvo 11,5% (10 de 87). Con `B` = 1803 generaciones por método
el ascenso por coordenadas y el backtracking agotaron el presupuesto antes de terminar; los detalles están en el informe y en `resultados/`.

## Integrantes

- Samuel Fernando Quiroga Tovar
- Yahir Andrés Rangel
- Yonier Vasquez Marin

## Estructura del repositorio

    adag1-oraculo/
    ├── README.md
    ├── requirements.txt
    ├── entrega.json          # mejor configuración encontrada
    ├── notebooks/
    │   ├── 01_busqueda.ipynb     # cómo se obtuvo la configuración
    │   └── 02_evaluacion.ipynb   # carga entrega.json y evalúa
    ├── src/
    │   ├── busqueda.py           # backtracking, halving y coordenadas
    │   └── oraculo_sintetico.py  # oráculo simulado para pruebas
    ├── tests/                # pruebas sin GPU
    ├── resultados/           # registros por método, caché, resumen y gráfica
    └── docs/
        ├── manual_tecnico.docx   # manual técnico (documento formal)
        ├── manual_tecnico.md     # versión web del manual
        └── gen_*.py              # generadores del informe y del manual

## Archivos clave de la entrega

| Archivo | Contenido |
| --- | --- |
| `entrega.json` | Grupo, semana y mejor configuración (índices + temperatura) |
| `notebooks/01_busqueda.ipynb` | Método de búsqueda, configuraciones probadas y su precisión, trazas de fallos y validación con `oraculo.validar` |
| `notebooks/02_evaluacion.ipynb` | Carga `entrega.json` y evalúa sobre los datos de prueba reservados a la profesora |
| [`docs/manual_tecnico.docx`](docs/manual_tecnico.docx) | Manual técnico: entorno, arquitectura, funcionamiento, uso, validación, límites y solución de problemas |
| `docs/manual_tecnico.md` | Versión web del manual técnico |

## Entorno

- Pruebas locales: Python 3.12 (probado con 3.12.5), sin GPU.
- Búsqueda y evaluación: Google Colab con GPU T4.
- Dependencias: ver `requirements.txt`.

## Cómo ejecutar

Pruebas con el oráculo sintético, sin GPU:

    pip install pytest
    python -m pytest

Búsqueda real: abrir `notebooks/01_busqueda.ipynb` en Colab con GPU T4 y seguir sus
secciones. Los resultados quedan en Drive, en `oraculo_g01/`.

Evaluación: abrir `notebooks/02_evaluacion.ipynb` en Colab y usar Ejecutar todo. Lee
`entrega.json` y, si existe, `datos_privados.json`; si no, usa la partición de validación.

## Alcance y limitaciones

La configuración reportada es la mejor encontrada durante la búsqueda, no un
óptimo global demostrado. La evaluación final se hace sobre datos privados a
los que el equipo no tiene acceso.
