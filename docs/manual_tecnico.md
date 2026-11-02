# Manual técnico: solución base del Proyecto Oráculo

ADAG1, Grupo 1, 2026-B. Rama: `solucion-base`.

Integrantes: Yahir Andrés Rangel Dueñas, Yonier Vásquez Marin y Samuel Quiroga.

Esta solución base no está terminada: cubre la búsqueda y la evaluación de la primera entrega. La sección [Validación y límites](#validación-y-límites) indica qué falta.

## Entorno

| Uso | Entorno |
| --- | --- |
| Pruebas sin GPU | Python 3.12 (probado con 3.12.5 en Windows 11), `pytest` |
| Búsqueda y evaluación | Google Colab con GPU T4 |

Las dependencias están en `requirements.txt`. Los notebooks instalan las suyas y descargan `oraculo.py`, `ayudas.py` y `datos_visibles.json` del repositorio del curso, además de los verificadores de `allenai/open-instruct`.

## Arquitectura

| Ruta | Responsabilidad |
| --- | --- |
| `src/busqueda.py` | Algoritmos, control del presupuesto, registro y validación de `entrega.json` |
| `src/oraculo_sintetico.py` | Oráculo simulado con óptimo conocido, para probar sin GPU |
| `tests/test_busqueda.py` | Pruebas de corrección, costo, presupuesto y formato |
| `notebooks/01_busqueda.ipynb` | Búsqueda real, análisis de trazas, validación y generación de `entrega.json` |
| `notebooks/02_evaluacion.ipynb` | Carga `entrega.json` y evalúa la configuración |
| `entrega.json` | Mejor configuración encontrada |
| `resultados/` | Copia de `oraculo_g01` de la corrida real: registros por método, caché, `resumen.json` y `comparacion.png` |

El código no copia `oraculo.py`. Los algoritmos reciben una función `evaluar(config, instancias, semilla)`, que puede ser el oráculo real o el sintético.

## Funcionamiento

### Flujo de `01_busqueda.ipynb`

1. Instala dependencias y descarga los archivos.
2. Carga el modelo, los datos y el oráculo, con caché en Drive.
3. Mide la velocidad y fija el presupuesto `B`.
4. Ejecuta ascenso por coordenadas y descarta opciones con las trazas.
5. Prueba las temperaturas 0.0, 0.3 y 0.7.
6. Ejecuta Successive Halving y backtracking con el mismo `B`.
7. Compara los métodos y elige usando solo las 100 instancias de búsqueda.
8. Llama a `oraculo.validar` y genera `entrega.json`.

### Algoritmos

| Función | Idea | Condición de parada | Costo sin caché |
| --- | --- | --- | --- |
| `ascenso_coordenadas` | Mejora una ranura a la vez | Pasada sin mejora, `max_pasadas` o fin de `B` | `O(I · n · Σ k_i)` |
| `successive_halving` | Duplica instancias y conserva la mitad mejor, con tope `n_r ≤ n` | Queda un candidato o fin de `B` | `O(|C| · n0 · min(log|C|, log(n/n0)))` |
| `backtracking` | Recorre el árbol y poda por cota superior | Árbol recorrido o fin de `B` | `n · Σ_{j=1..d} k^j` en el peor caso |

### Estructuras de datos

- **Configuración:** diccionario con `rol`, `estrategia`, `formato`, `estilo`, `cierre` y `temperatura`.
- **`Consultor`:** mide prefijos de instancias, cobra solo los pares nuevos y conserva el registro. Lanza `PresupuestoAgotado` antes de exceder `B`.
- **`Medida`:** precisión, número de instancias y conteo de fallos por familia.
- **`ResultadoBusqueda`:** mejor configuración, precisión, generaciones, indicador de presupuesto agotado y detalle del método.

## Uso

### Pruebas locales

    pip install pytest
    python -m pytest

Resultado esperado: todas las pruebas pasan, sin GPU.

### Búsqueda en Colab

1. Abrir `notebooks/01_busqueda.ipynb` desde la rama `solucion-base`.
2. Elegir GPU T4.
3. Correr la instalación y reiniciar la sesión.
4. Ajustar `HORAS_MAX` si hace falta y correr las demás secciones. Colab pedirá acceso a Drive.
5. Si Colab se desconecta, volver a correr todo: lo ya generado sale del caché.

Los resultados quedan en `MyDrive/oraculo_g01/`: registros por método, `comparacion.png`, `resumen.json` y `entrega.json`.

### Evaluación

Abrir `notebooks/02_evaluacion.ipynb` con GPU T4 y usar Ejecutar todo. La primera vez el entorno se reinicia solo; al reconectar, usar Ejecutar todo otra vez. Si existe `datos_privados.json`, se evalúa ese archivo. Si no, se usa la partición de validación.

### Formato de `entrega.json`

```json
{
 "grupo": "G01",
 "config": {"rol": 0, "estrategia": 0, "formato": 0, "estilo": 0, "cierre": 0, "temperatura": 0.0},
 "semana": 6
}
```

Los índices del ejemplo son de relleno. Cada índice va de 0 a 7, y la temperatura es 0.0, 0.3 o 0.7.

### Formato de los datos privados (supuesto)

Se asume el formato de `datos_visibles.json`: una lista de objetos con `id`, `prompt`, `ids`, `kwargs` y `restriccion`.

### Significado de la salida

`precision` es la fracción de instancias que cumplen todas sus restricciones. En cada traza, `violo` es solo la primera restricción incumplida, y `salida` es el texto generado.

## Validación y límites

**Pruebas disponibles:** óptimo sintético, costos deducidos en el informe, respeto de `B`, tope de `n_r`, reproducibilidad con semilla y formato de `entrega.json`.

**Supuestos**

- El modelo de calificación es `qwen17b`, porque la guía no lo indica.
- El grupo es `G01`, y la semana se cuenta desde el 27 de septiembre de 2026 a las 23:04, con la primera semana igual a 1.
- `B` lo fija el equipo, porque el oráculo no limita consultas.

**Límites conocidos**

- El resultado es la mejor configuración encontrada, no un óptimo global demostrado.
- Con el modelo real, el backtracking usa un subespacio y una cota sin admisibilidad demostrada.
- El test privado incluye familias nuevas y podría requerir verificadores adicionales en `Oraculo(registros=...)`.
- `B` real fue de 1803 generaciones por método, porque el modelo genera unas 0,5 respuestas por segundo en una T4. El ascenso por coordenadas y el backtracking agotaron `B` antes de terminar.
- `ascenso_coordenadas` descarta las medidas de la ranura en curso cuando se agota `B`. En la corrida midió formato 0 con 11%, pero reportó 8%. Se corregirá para la siguiente entrega.
- La configuración entregada usa temperatura 0.7 y se midió con una sola semilla.

## Resultados de la corrida real

Colab con GPU T4, modelo `qwen17b`, velocidad 0,50 generaciones/s, `B` = 1803 por método.

| Método | Precisión en búsqueda | Generaciones | Configuración |
| --- | --- | --- | --- |
| Ascenso por coordenadas | 8% | 1800 | rol 5, estrategia 1, formato 2, estilo 3, cierre 7, T 0.0 |
| Successive Halving | 16% | 968 | rol 7, estrategia 0, formato 0, estilo 2, cierre 1, T 0.7 |
| Backtracking | 8% | 1800 | rol 0, estrategia 2, formato 0, estilo 3, cierre 0, T 0.0 |

La configuración de Successive Halving es la de `entrega.json`. En validación obtuvo 11,5% (10 de 87). No hubo descartes por trazas porque ninguna ranura completa superó `PISO` = 10%.

**Pendiente:** confirmar el formato de los datos privados.
