"""Genera el manual técnico en Word con la misma portada del informe.

Uso:
    python docs/gen_manual.py <informe_original.docx> <destino.docx> <carpeta_resultados>

Toma del informe original la portada, el logo, los estilos y la numeración, pasa los
títulos a negro y gris oscuro, agrega un pie de página y escribe el contenido del manual.
El archivo original no se modifica.
"""
import re
import sys
import zipfile
from pathlib import Path

from lxml import etree as E

sys.path.insert(0, str(Path(__file__).parent))
from docx_comun import *  # noqa: E402,F401,F403
from docx_comun import IMAGENES  # noqa: E402

ORIGEN, DESTINO, RESULTADOS = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
RNS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
RELNS = "http://schemas.openxmlformats.org/package/2006/relationships"
ANCHO = 9029  # ancho útil de la página en twips: 11909 - 2 × 1440

TITULO = "Proyecto Oráculo: Manual técnico"
SUBTITULO = "Solución base · Primera entrega · Rama solucion-base"
PIE = "Proyecto Oráculo · Manual técnico de la solución base"
NEGRO, GRIS_OSCURO, GRIS, GRIS_CLARO = "1F1F1F", "404040", "7F7F7F", "BFBFBF"
ENCABEZADO_TABLA = "D9D9D9"


def tbl(filas, *proporciones):
    """Tabla con anchos proporcionales al ancho útil."""
    total = sum(proporciones)
    anchos = [ANCHO * p // total for p in proporciones]
    anchos[-1] += ANCHO - sum(anchos)
    return ("tbl", (filas, anchos))


CONTENIDO = [
# 1 ---------------------------------------------------------------------------
("h1", "1. Introducción"),
("p", "Este manual describe la solución base del Proyecto Oráculo, desarrollada por el Grupo 1 (ADAG1) para la primera entrega de Análisis y Diseño de Algoritmos. Explica cómo está construido el código, cómo se instala y ejecuta, qué formato tienen sus entradas y salidas, y cuáles son sus límites conocidos. Está escrito para que otra persona pueda reproducir la búsqueda y la evaluación sin ayuda de los autores."),
("h2", "1.1 Alcance"),
("p", "La solución busca una configuración de prompt que maximice la precisión de un modelo de lenguaje sobre instrucciones con restricciones verificables. Una configuración elige un índice para cada una de las cinco ranuras (rol, estrategia, formato, estilo y cierre) y una temperatura. El repositorio incluye tres algoritmos de búsqueda, un oráculo simulado para probarlos sin GPU, dos notebooks y los resultados de la corrida real."),
("p", "Es una solución base: cubre lo exigido para la primera entrega y no se presenta como terminada. La sección 7 indica qué falta."),
("h2", "1.2 Identificación de la versión"),
tbl([["Campo", "Valor"],
     ["Proyecto", "Proyecto Oráculo · ADAG1 · Grupo 1 (`G01`)"],
     ["Integrantes", "Yahir Andres Rangel Dueñas, Yonier Vásquez Marin y Samuel Quiroga"],
     ["Repositorio", "github.com/samyquito/SYY-Adag1-Oraculo"],
     ["Rama entregada", "`solucion-base`"],
     ["Semana de la entrega", "6, contada desde el 27 de septiembre de 2026"],
     ["Documentos relacionados", "Informe de la primera entrega, `README.md` y `docs/manual_tecnico.md`, la versión web de este manual"]],
    3, 7),
# 2 ---------------------------------------------------------------------------
("h1", "2. Entorno"),
("h2", "2.1 Entornos de ejecución"),
tbl([["Tarea", "Entorno", "Requisitos"],
     ["Pruebas automáticas", "PC local. Probado con Python 3.12.5 en Windows 11", "`pytest` 8 o superior. No requiere GPU ni el modelo."],
     ["Búsqueda (`01_busqueda.ipynb`)", "Google Colab con GPU T4", "Cuenta de Google con Drive. Con los parámetros entregados, unas 3 a 4 horas de GPU."],
     ["Reproducción de la búsqueda", "Google Colab con CPU", "El caché de una corrida completa en Drive. No consume cuota de GPU."],
     ["Evaluación (`02_evaluacion.ipynb`)", "Google Colab con GPU T4", "Ninguno adicional: el notebook instala y descarga todo."]],
    3, 3, 4),
("h2", "2.2 Dependencias"),
("p", "Están en `requirements.txt`. En Colab los notebooks las instalan solos; para las pruebas locales solo hace falta `pytest`."),
tbl([["Paquete", "Uso"],
     ["`pytest` ≥ 8", "Pruebas automáticas locales"],
     ["`torch`, `transformers`, `accelerate`", "Carga del modelo y generación de respuestas"],
     ["`bitsandbytes` ≥ 0.46.1", "Modelos cuantizados en 4 bits; lo exige el notebook del curso"],
     ["`nltk`, `spacy`, `emoji`, `langdetect`, `immutabledict`", "Verificadores de restricciones de open-instruct"],
     ["`matplotlib`, `tqdm`", "Gráficas y barras de progreso"]],
    4, 6),
("h2", "2.3 Archivos externos"),
("p", "El código del equipo no copia el oráculo del curso. Los notebooks descargan en cada ejecución:"),
("b", "`oraculo.py`, `ayudas.py` y `datos_visibles.json`, del repositorio del curso `JuManoel/ADA-2026-2-GP01`."),
("b", "Los verificadores de restricciones de `allenai/open-instruct`."),
("b", "El modelo `Qwen/Qwen3-1.7B`, desde Hugging Face, sin necesidad de cuenta."),
# 3 ---------------------------------------------------------------------------
("h1", "3. Arquitectura"),
("h2", "3.1 Estructura del repositorio"),
("code", """
SYY-Adag1-Oraculo/
├── README.md
├── requirements.txt
├── pytest.ini
├── entrega.json               configuración entregada
├── src/
│   ├── busqueda.py            algoritmos y control del presupuesto
│   └── oraculo_sintetico.py   oráculo simulado con óptimo conocido
├── tests/
│   └── test_busqueda.py       pruebas sin GPU
├── notebooks/
│   ├── 01_busqueda.ipynb      búsqueda ejecutada, con salidas
│   └── 02_evaluacion.ipynb    evaluación de entrega.json
├── resultados/                registros y caché de la corrida real
└── docs/
    ├── manual_tecnico.md      versión web de este manual
    ├── manual_tecnico.docx    este documento
    └── gen_*.py               generadores del informe y del manual
"""),
("h2", "3.2 Responsabilidad de cada módulo"),
tbl([["Archivo", "Responsabilidad"],
     ["`src/busqueda.py`", "Los tres algoritmos, el control del presupuesto (`Consultor`), el filtro por trazas, las fórmulas de costo y la validación de `entrega.json`. No importa `torch` ni el modelo."],
     ["`src/oraculo_sintetico.py`", "Oráculo simulado: cada opción no óptima invalida un conjunto fijo de instancias, así que el óptimo se conoce de antemano. Admite ruido para simular consultas ruidosas."],
     ["`tests/test_busqueda.py`", "Comprueba los algoritmos contra el oráculo sintético y contra las fórmulas de costo del informe."],
     ["`notebooks/01_busqueda.ipynb`", "Ejecuta la búsqueda con el modelo real, analiza las trazas, valida y genera `entrega.json`."],
     ["`notebooks/02_evaluacion.ipynb`", "Carga `entrega.json` y la evalúa sobre los datos privados de la profesora, o sobre la partición de validación si no existen."],
     ["`resultados/`", "Copia de la carpeta de Drive de la corrida real: registros por método, caché, `resumen.json`, gráficas y `graficar_comparacion.py`."],
     ["`docs/`", "Este manual y los scripts que generan el informe y el manual."]],
    3, 7),
("h2", "3.3 Desacoplamiento del oráculo"),
("p", "Los algoritmos no llaman al modelo directamente. Reciben una función `evaluar(config, instancias, semilla)` que devuelve un objeto con `precision` y `trazas`. En Colab esa función es `Oraculo.evaluar`, del curso; en las pruebas es `OraculoSintetico.evaluar`. Así, el mismo código se prueba en segundos en un PC y se ejecuta sin cambios con el modelo real."),
# 4 ---------------------------------------------------------------------------
("h1", "4. Funcionamiento"),
("h2", "4.1 Flujo de la búsqueda"),
("p", "El notebook `01_busqueda.ipynb` tiene 12 secciones. Las secciones 1 a 3, 11 y 12 siguen al notebook del curso. Las secciones 4 a 10 reemplazan la búsqueda aleatoria de ejemplo, que es el punto 4 del notebook del curso."),
tbl([["Sección", "Qué hace", "Produce"],
     ["1 · Instalación", "Instala dependencias, descarga los archivos del curso y clona la rama `solucion-base`.", "—"],
     ["2 · Parámetros", "Define el presupuesto, las semillas y los umbrales.", "—"],
     ["3 · Modelo, datos y oráculo", "Carga el modelo, o solo el tokenizador si no hay GPU; divide los datos y abre el caché en Drive.", "`cache_oraculo.json`"],
     ["4 · Velocidad y presupuesto", "Mide generaciones por segundo y fija `B`.", "`velocidad.json`"],
     ["5 · Ascenso por coordenadas", "Mejora una ranura a la vez y aplica el filtro por trazas.", "`registro_coordenadas.json`"],
     ["6 · Análisis de fallos", "Resume los descartes y las familias de restricciones que más fallan.", "—"],
     ["7 · Temperatura", "Prueba 0.0, 0.3 y 0.7 sobre la mejor configuración.", "`registro_temperatura.json`"],
     ["8 · Successive Halving", "Conserva la mitad mejor de los candidatos en cada ronda.", "`registro_halving.json`"],
     ["9 · Backtracking", "Recorre un subespacio con poda por cota.", "`registro_backtracking.json`"],
     ["10 · Comparación", "Elige el método con mayor precisión en búsqueda y grafica.", "`comparacion.png`"],
     ["11 · Validación", "Llama a `oraculo.validar` sobre la configuración elegida.", "—"],
     ["12 · Entrega", "Genera, valida y descarga `entrega.json`.", "`entrega.json`, `resumen.json`"]],
    25, 45, 30),
("p", "La elección usa solo las 100 instancias de búsqueda. La validación se mide al final y no cambia la elección."),
("h2", "4.2 Parámetros"),
tbl([["Parámetro", "Valor", "Significado"],
     ["`HORAS_MAX`", "3.0", "Horas de GPU para los tres métodos juntos."],
     ["`B_MAXIMO`", "15 000", "Tope de generaciones por método."],
     ["`B`", "1803 en la corrida real", "Presupuesto por método: el menor entre `B_MAXIMO` y lo que alcanza a generarse en `HORAS_MAX / 3` horas."],
     ["`N0`", "2", "Instancias de la primera ronda de Successive Halving."],
     ["`MAX_PASADAS`", "3", "Pasadas máximas del ascenso por coordenadas."],
     ["`MARGEN`", "0.03", "Distancia mínima a la mejor opción para descartar por trazas."],
     ["`PISO`", "0.10", "Precisión mínima de la mejor opción para que el filtro por trazas actúe."],
     ["`TOPE_BACKTRACKING`", "2", "Opciones por ranura en el subespacio del backtracking."],
     ["`HOLGURA_COTA`", "0.02", "Margen que se suma a la cota parcial del backtracking."],
     ["`SEMILLA`", "0", "Muestreo de la configuración inicial y de los candidatos."],
     ["`SEMILLAS_TEMPERATURA`", "(1, 2, 3)", "Semillas que se promedian para temperaturas mayores que 0."]],
    3, 2, 5),
("h2", "4.3 Algoritmos"),
("p", "**Ascenso por coordenadas** (`ascenso_coordenadas`). Parte de una configuración aleatoria con semilla fija. En cada pasada recorre las ranuras y, para cada una, mide sus opciones activas con las demás ranuras fijas. Solo cambia de opción ante una mejora estricta. Se detiene si una pasada no produce cambios, al llegar a `MAX_PASADAS` o al agotar `B`. Con $d$ ranuras de $k_{i}$ opciones, $n$ instancias e $I$ pasadas, el costo sin caché es:"),
("eq", "T=O(I·n∑_{i=1}^{d}k_{i})"),
("p", "Una pasada completa cuesta $100·40=4000$ generaciones."),
("p", "**Filtro por trazas** (`descartar_con_trazas`). Al terminar una ranura, si su mejor opción supera `PISO`, se retiran de las pasadas siguientes las opciones que quedaron al menos `MARGEN` por debajo de ella. Para cada opción retirada se registran las familias de restricciones que falló más veces que la mejor. Nunca se retira la opción actual ni la mejor."),
("p", "**Successive Halving** (`successive_halving`). Toma una muestra aleatoria de candidatos, que incluye las tres temperaturas, con el mayor tamaño potencia de 2 que cabe en `B` (`max_candidatos`). En la ronda $r$ mide a los candidatos vivos con $n_{r}=min(n_{0}2^{r},n)$ instancias y conserva la mitad mejor. El `Consultor` solo cobra las instancias nuevas de cada ronda. Se detiene cuando queda un candidato, que se mide con las $n$ instancias. Su costo es:"),
("eq", "T=O(|C|n_{0}min(log|C|,log(n/n_{0})))"),
("p", "**Backtracking con poda** (`backtracking`). Recorre el árbol de ranuras visitando primero los hijos con mayor cota, y poda una rama si su cota no supera la mejor hoja encontrada. La cota (`cota_parcial`) mide el prompt sin las ranuras aún no decididas y le suma `HOLGURA_COTA`. Con el modelo real se aplica al subespacio de las `TOPE_BACKTRACKING` mejores opciones por ranura según el registro del ascenso (`mejores_opciones`). En el peor caso visita todas las hojas:"),
("eq", "T_{peor}=n∑_{j=1}^{d}k^{j}"),
("p", "Es exacto con el oráculo sintético. Con el modelo real no certifica el óptimo, porque no está demostrado que la cota sea admisible."),
("h2", "4.4 Estructuras de datos"),
tbl([["Estructura", "Contenido"],
     ["Configuración", "Diccionario con `rol`, `estrategia`, `formato`, `estilo` y `cierre`, enteros de 0 a 7, y `temperatura`, que vale 0.0, 0.3 o 0.7."],
     ["`Consultor`", "Mide configuraciones sobre prefijos de las instancias y cobra solo los pares (configuración, instancia) nuevos. Guarda un registro con orden, configuración, número de instancias, precisión, generaciones nuevas y acumuladas, y fallos por familia."],
     ["`Medida`", "Precisión, número de instancias y conteo de fallos por familia."],
     ["`ResultadoBusqueda`", "Método, mejor configuración, precisión, generaciones gastadas, indicador de presupuesto agotado y detalle propio de cada método."],
     ["`PresupuestoAgotado`", "Excepción que lanza el `Consultor` antes de exceder `B`. Cada algoritmo la captura y devuelve lo mejor que tenía."]],
    3, 7),
("h2", "4.5 Presupuesto y caché"),
("p", "La unidad de costo es la generación: un par (configuración, instancia) que el modelo responde por primera vez. Cada método tiene su propio `Consultor`, que lleva la cuenta y lanza `PresupuestoAgotado` antes de pasarse de `B`. Así los tres métodos compiten con el mismo presupuesto."),
("p", "Además, el oráculo del curso guarda cada respuesta en `cache_oraculo.json`, con la clave modelo, configuración, instancia y semilla. El notebook deja ese archivo en Google Drive: si Colab se desconecta, al volver a ejecutar, las respuestas ya generadas se leen del caché y no se repiten. Esto también permite reproducir la búsqueda completa sin GPU, como se explica en la sección 5.3."),
# 5 ---------------------------------------------------------------------------
("h1", "5. Uso"),
("h2", "5.1 Pruebas locales"),
("p", "Desde la raíz del repositorio:"),
("code", """
pip install pytest
python -m pytest
"""),
("p", "Resultado esperado: 45 pruebas aprobadas en menos de un segundo, sin GPU. Son 26 funciones de prueba; algunas se ejecutan con varios parámetros."),
("h2", "5.2 Búsqueda con GPU en Colab"),
("n", "Abrir el notebook desde la rama entregada: `colab.research.google.com/github/samyquito/SYY-Adag1-Oraculo/blob/solucion-base/notebooks/01_busqueda.ipynb`."),
("n", "Usar **Archivo ▸ Guardar una copia en Drive**, para conservar las salidas."),
("n", "Elegir **Entorno de ejecución ▸ Cambiar tipo de entorno de ejecución ▸ T4 GPU**."),
("n", "Ejecutar la sección 1. Al terminar, usar **Entorno de ejecución ▸ Reiniciar sesión**."),
("n", "Situarse en la sección 2, ajustar `HORAS_MAX` si hace falta y usar **Entorno de ejecución ▸ Ejecutar celda y siguientes**."),
("n", "Aceptar el acceso a Google Drive. Los resultados quedan en `MyDrive/oraculo_g01/`."),
("nota", "**Nota:** la pestaña debe quedar abierta y el equipo sin suspenderse. Si Colab se desconecta, repetir los pasos 3 a 5: lo ya generado sale del caché."),
("h2", "5.3 Reproducción sin GPU"),
("p", "Si `cache_oraculo.json` y `velocidad.json` de una corrida completa están en `MyDrive/oraculo_g01/`, el notebook puede ejecutarse con el entorno de CPU. La sección 3 detecta que no hay GPU, carga solo el tokenizador e imprime `sin GPU: se reproduce desde el caché`. Todas las respuestas salen del caché, así que el resultado es idéntico al de la corrida original. Si una consulta no estuviera en el caché, la ejecución se detiene con un mensaje que pide cambiar a GPU."),
("p", "Así se generó la versión con salidas que está en el repositorio. El caché de la corrida real tiene 5255 respuestas y cubre todas las consultas del notebook."),
("h2", "5.4 Evaluación de la entrega"),
("n", "Abrir `notebooks/02_evaluacion.ipynb` en Colab con GPU T4."),
("n", "Si se tienen los datos privados, subir `datos_privados.json` junto al notebook."),
("n", "Usar **Entorno de ejecución ▸ Ejecutar todo**. La primera vez, el entorno se reinicia solo al terminar la instalación; al reconectar, usar **Ejecutar todo** otra vez."),
("p", "El notebook clona la rama `solucion-base`, carga `entrega.json`, comprueba su formato con `validar_entrega` y evalúa la configuración. Si no existe `datos_privados.json`, usa la partición de validación. No hay que editar código, rutas ni parámetros."),
("h2", "5.5 Formato de entrega.json"),
("code", """
{
 "grupo": "G01",
 "config": {
  "rol": 7,
  "estrategia": 0,
  "formato": 0,
  "estilo": 2,
  "cierre": 1,
  "temperatura": 0.7
 },
 "semana": 6
}
"""),
("p", "Cada índice es un entero de 0 a 7, y la temperatura es 0.0, 0.3 o 0.7. La función `validar_entrega` rechaza claves faltantes o sobrantes, índices fuera de rango y temperaturas no permitidas."),
("h2", "5.6 Formato de los datos de prueba"),
("p", "Se asume el formato de `datos_visibles.json`: una lista de objetos con `id`, `prompt`, `ids`, `kwargs` y `restriccion`. Si los datos privados usan familias de restricciones nuevas, el oráculo puede necesitar verificadores adicionales mediante `Oraculo(registros=...)`."),
("h2", "5.7 Interpretación de la salida"),
("p", "`precision` es la fracción de instancias que cumplen todas sus restricciones: la calificación es todo o nada por instancia. Cada traza trae `violo`, la primera restricción incumplida, y `salida`, el texto generado. Este es un extracto real de la sección 11:"),
("code", """
validación: 11.5%  (87 inst)
    6  last_word:last_word_sent
    6  punctuation:punctuation_dot
    5  keywords:no_adjacent_consecutive
    5  copy:repeat_phrase
    5  combination:repeat_prompt
Resultado(precision=11.5%, fallos=77/87)
"""),
("p", "La configuración acertó 10 de 87 instancias. Las líneas intermedias son las restricciones que más fallaron, con el número de instancias en que cada una fue la primera incumplida."),
# 6 ---------------------------------------------------------------------------
("h1", "6. Resultados de referencia"),
("p", "La corrida real se hizo en Colab con una GPU T4 y el modelo `qwen17b`. La velocidad medida fue de 0,50 generaciones por segundo, lo que dio $B=1803$ generaciones por método."),
tbl([["Método", "Precisión en búsqueda", "Generaciones", "Configuración"],
     ["Ascenso por coordenadas", "8%", "1800", "rol 5, estrategia 1, formato 2, estilo 3, cierre 7, temperatura 0.0"],
     ["Successive Halving", "16%", "968", "rol 7, estrategia 0, formato 0, estilo 2, cierre 1, temperatura 0.7"],
     ["Backtracking en subespacio", "8%", "1800", "rol 0, estrategia 2, formato 0, estilo 3, cierre 0, temperatura 0.0"]],
    26, 16, 15, 43),
("p", "La configuración de Successive Halving es la de `entrega.json`, y en validación obtuvo 11,5%. La figura 1 muestra la mejor precisión de las configuraciones completas según el gasto de cada método. Se genera con `resultados/graficar_comparacion.py`."),
("img", "comparacion_informe.png"),
("cap", "Figura 1. Mejor precisión entre las configuraciones completas medidas con las 100 instancias de búsqueda, según las generaciones gastadas por cada método."),
("p", "Estos valores sirven para comprobar una reproducción: con el mismo caché, el notebook debe imprimir exactamente las mismas cifras."),
# 7 ---------------------------------------------------------------------------
("h1", "7. Validación y límites"),
("h2", "7.1 Pruebas disponibles"),
tbl([["Grupo", "Qué verifica"],
     ["Corrección", "El oráculo sintético tiene el óptimo que declara; el ascenso lo recupera cuando las ranuras son independientes; el backtracking coincide con la fuerza bruta en varias semillas."],
     ["Costo", "Las fórmulas del informe coinciden con lo que gasta el código: una pasada del ascenso, Successive Halving con y sin tope de instancias, y el peor caso del backtracking. También se comprueba que la poda ahorra frente al peor caso."],
     ["Presupuesto", "El `Consultor` no cobra dos veces el mismo par y rechaza exceder `B` sin cobrar; los tres métodos se detienen al agotar el presupuesto."],
     ["Trazas", "`descartar_con_trazas` usa el exceso de fallos por familia y protege la opción actual; el filtro retira opciones de las pasadas siguientes; `mejores_opciones` ordena por la mejor precisión observada."],
     ["Reproducibilidad", "El muestreo con semilla no repite configuraciones, el ruido del oráculo sintético depende solo de la semilla, el tamaño del espacio es 98 304 y el registro se guarda en JSON."],
     ["Formato", "`validar_entrega` acepta el formato correcto y rechaza los inválidos."]],
    2, 8),
("h2", "7.2 Supuestos"),
("b", "El modelo de calificación es `qwen17b`, el predeterminado del curso, porque la guía no lo indica."),
("b", "El grupo es `G01`, y la semana se cuenta desde el 27 de septiembre de 2026 a las 23:04, con la primera semana igual a 1."),
("b", "El presupuesto `B` lo fija el equipo, porque el oráculo no limita las consultas."),
("b", "Los datos privados tienen el mismo formato que `datos_visibles.json`."),
("h2", "7.3 Errores conocidos"),
("b", "`ascenso_coordenadas` descarta las medidas de la ranura en curso cuando se agota `B`. En la corrida real midió formato 0 con 11%, pero reportó 8%."),
("b", "La configuración entregada usa temperatura 0.7, y su precisión en búsqueda se midió con una sola semilla."),
("b", "Con el modelo real, los prompts parciales obtuvieron más precisión que los completos: 15% frente a 8%. Por eso la cota del backtracking es holgada y poda poco."),
("h2", "7.4 Componentes no desarrollados"),
("b", "Adoptar la mejor configuración medida cuando el ascenso agota el presupuesto."),
("b", "Una corrida en la que el filtro por trazas descarte opciones. En la corrida real no hubo descartes, porque ninguna ranura completa superó `PISO`."),
("b", "Verificadores para las familias de restricciones nuevas de los datos privados."),
("b", "Repetir la medición de la configuración final con varias semillas."),
# 8 ---------------------------------------------------------------------------
("h1", "8. Solución de problemas"),
tbl([["Síntoma", "Causa", "Solución"],
     ["«No se puede conectar con el backend de GPU»", "Se agotó la cuota gratuita de GPU de la cuenta.", "Esperar de 12 a 24 horas; usar otra cuenta, con `cache_oraculo.json` y `velocidad.json` en su `MyDrive/oraculo_g01/`; o reproducir con CPU si el caché está completo."],
     ["`RuntimeError: No hay GPU` en la sección 3", "Se abrió una copia antigua del notebook, sin el modo sin GPU.", "Abrir de nuevo el enlace de la rama `solucion-base` y guardar una copia nueva."],
     ["`caché: 0 respuestas recuperadas`", "Los archivos no están en `MyDrive/oraculo_g01/` de la cuenta que ejecuta.", "Subirlos a esa carpeta exacta, en «Mi unidad» y no en «Compartidos conmigo»."],
     ["`JSONDecodeError` al abrir el caché", "Colab se cortó mientras escribía `cache_oraculo.json`.", "Restaurar la copia de `resultados/cache_oraculo.json` del repositorio."],
     ["Colab pide reiniciar tras instalar", "Es el comportamiento normal de la sección 1.", "Reiniciar la sesión y seguir desde la sección 2."],
     ["El índice de este documento aparece vacío", "Word no ha actualizado los campos.", "Clic derecho sobre el índice ▸ **Actualizar campos** ▸ **Actualizar toda la tabla**."]],
    3, 3, 4),
]


# --------------------------------------------------------------------------------
def leer(ruta):
    with zipfile.ZipFile(ruta) as z:
        return {i.filename: z.read(i.filename) for i in z.infolist()}, [i.filename for i in z.infolist()]


def lista_decimal(numbering):
    """Agrega una lista numerada nueva que reinicia en 1, basada en la decimal del documento."""
    raiz = E.fromstring(numbering[0])
    ns = {"w": WNS}
    abstracto = numbering[1]
    ids = [int(x) for x in raiz.xpath("w:num/@w:numId", namespaces=ns)]
    nuevo = max(ids) + 1
    num = E.SubElement(raiz, W + "num")
    num.set(W + "numId", str(nuevo))
    E.SubElement(num, W + "abstractNumId").set(W + "val", abstracto)
    sobre = E.SubElement(num, W + "lvlOverride")
    sobre.set(W + "ilvl", "0")
    E.SubElement(sobre, W + "startOverride").set(W + "val", "1")
    numbering[0] = E.tostring(raiz, xml_declaration=True, encoding="UTF-8", standalone=True)
    return nuevo


def abstracto_de(numbering, formato):
    raiz = E.fromstring(numbering)
    ns = {"w": WNS}
    for num in raiz.xpath("w:num", namespaces=ns):
        abstracto = num.xpath("w:abstractNumId/@w:val", namespaces=ns)[0]
        fmt = raiz.xpath(f"w:abstractNum[@w:abstractNumId='{abstracto}']/w:lvl[@w:ilvl='0']/w:numFmt/@w:val",
                         namespaces=ns)
        izquierda = raiz.xpath(f"w:abstractNum[@w:abstractNumId='{abstracto}']/w:lvl[@w:ilvl='0']/w:pPr/w:ind/@w:left",
                               namespaces=ns)
        if fmt == [formato] and izquierda == ["720"]:
            return num.get(W + "numId"), abstracto
    raise ValueError(f"no hay lista {formato}")


def pie_de_pagina():
    texto = (
        '<w:ftr xmlns:w="%s"><w:p><w:pPr>'
        '<w:pBdr><w:top w:val="single" w:sz="4" w:space="6" w:color="%s"/></w:pBdr>'
        '<w:tabs><w:tab w:val="right" w:pos="%d"/></w:tabs>'
        '<w:spacing w:before="0" w:after="0"/></w:pPr>'
        '<w:r><w:rPr><w:color w:val="%s"/><w:sz w:val="16"/></w:rPr><w:t xml:space="preserve">%s</w:t></w:r>'
        '<w:r><w:rPr><w:color w:val="%s"/><w:sz w:val="16"/></w:rPr><w:tab/><w:t xml:space="preserve">Página </w:t></w:r>'
        '%s<w:r><w:rPr><w:color w:val="%s"/><w:sz w:val="16"/></w:rPr><w:t xml:space="preserve"> de </w:t></w:r>%s'
        '</w:p></w:ftr>'
    ) % (WNS, GRIS_CLARO, ANCHO, GRIS, PIE, GRIS, campo("PAGE"), GRIS, campo("NUMPAGES"))
    return texto.encode("utf-8")


def campo(nombre):
    """Campo complejo: a diferencia de fldSimple, Word conserva el formato del resultado."""
    rpr = '<w:rPr><w:color w:val="%s"/><w:sz w:val="16"/></w:rPr>' % GRIS
    return (
        f'<w:r>{rpr}<w:fldChar w:fldCharType="begin"/></w:r>'
        f'<w:r>{rpr}<w:instrText xml:space="preserve"> {nombre} \\* MERGEFORMAT</w:instrText></w:r>'
        f'<w:r>{rpr}<w:fldChar w:fldCharType="separate"/></w:r>'
        f'<w:r>{rpr}<w:t>1</w:t></w:r>'
        f'<w:r>{rpr}<w:fldChar w:fldCharType="end"/></w:r>'
    )


def estilos_neutros(styles):
    """Títulos en negro y gris oscuro: sin el morado del informe ni azules."""
    s = styles.decode("utf-8")
    s = re.sub(r'w:color w:val="a64d79"', f'w:color w:val="{NEGRO}"', s, flags=re.I)
    s = re.sub(
        r'(<w:style w:type="paragraph" w:styleId="Heading2">.*?<w:rPr>.*?)(<w:sz )',
        lambda m: m.group(1) + f'<w:color w:val="{GRIS_OSCURO}"/>' + m.group(2), s, count=1, flags=re.S,
    )
    return s.encode("utf-8")


def actualizar_campos(settings):
    ajustes = E.fromstring(settings)
    if ajustes.find(W + "updateFields") is None:
        nodo = E.Element(W + "updateFields")
        nodo.set(W + "val", "true")
        siguientes = {"hdrShapeDefaults", "footnotePr", "endnotePr", "compat", "docVars", "rsids",
                      "mathPr", "attachedSchema", "themeFontLang", "clrSchemeMapping",
                      "doNotIncludeSubdocsInStats", "doNotAutoCompressPictures", "forceUpgrade", "captions",
                      "readModeInkLockDown", "smartTagType", "schemaLibrary", "shapeDefaults",
                      "doNotEmbedSmartTags", "decimalSymbol", "listSeparator"}
        for hijo in ajustes:
            if E.QName(hijo).localname in siguientes:
                hijo.addprevious(nodo)
                break
        else:
            ajustes.append(nodo)
    return E.tostring(ajustes, xml_declaration=True, encoding="UTF-8", standalone=True)


def texto_de(p):
    return "".join(p.itertext()).strip()


def poner_texto(p, texto, color, tamano, negrita):
    """Reemplaza las corridas de un párrafo de portada por una sola."""
    for hijo in list(p):
        if E.QName(hijo).localname in ("r", "proofErr", "bookmarkStart", "bookmarkEnd"):
            p.remove(hijo)
    r = ele(W + "r", p)
    pr = ele(W + "rPr", r)
    if negrita:
        ele(W + "b", pr, val="1")
        ele(W + "bCs", pr, val="1")
    ele(W + "color", pr, val=color)
    ele(W + "sz", pr, val=tamano)
    ele(W + "szCs", pr, val=tamano)
    t = ele(W + "t", r)
    t.text = texto
    t.set(XML, "preserve")


def main():
    partes, orden = leer(ORIGEN)

    raiz = E.fromstring(partes["word/document.xml"])
    cuerpo = raiz.find(W + "body")
    hijos = list(cuerpo)
    assert texto_de(hijos[0]).startswith("Proyecto Oráculo"), "la portada cambió"
    assert texto_de(hijos[6]) == "Yahir Andres Rangel Dueñas"
    assert hijos[30].findall(".//" + W + "drawing"), "el logo debe estar en el párrafo 30"
    assert texto_de(hijos[31]) == "Índice" and hijos[33].tag == W + "sdt"
    assert texto_de(hijos[37]) == "Introducción"
    sect = hijos[-1]
    assert sect.tag == W + "sectPr"

    # Portada: título nuevo en negro y subtítulo en el párrafo vacío que le sigue.
    poner_texto(hijos[0], TITULO, NEGRO, 36, True)
    assert texto_de(hijos[1]) == ""
    poner_texto(hijos[1], SUBTITULO, GRIS, 24, False)

    # Se quitan los párrafos vacíos y el salto que seguían al índice: dejaban una página
    # en blanco. El primer título abre página por sí mismo.
    for h in hijos[34:-1]:
        cuerpo.remove(h)

    # Listas numeradas: cada grupo de pasos reinicia en 1.
    _, abstracto = abstracto_de(partes["word/numbering.xml"], "decimal")
    num_vineta, _ = abstracto_de(partes["word/numbering.xml"], "bullet")
    numbering = [partes["word/numbering.xml"], abstracto]

    nuevos, entradas, previo, num_actual = [], [], None, None
    for tipo, valor in CONTENIDO:
        if tipo in ("h1", "h2"):
            nivel = int(tipo[1])
            p, nombre = titulo(nivel, valor)
            if not entradas:
                p.find(W + "pPr").insert(3, E.Element(W + "pageBreakBefore"))
            entradas.append((nivel, valor, nombre))
            nuevos.append(p)
        elif tipo == "p":
            nuevos.append(parrafo(valor))
        elif tipo == "b":
            nuevos.append(vineta(valor, num_vineta))
        elif tipo == "n":
            if previo != "n":
                num_actual = lista_decimal(numbering)
            nuevos.append(numerado(valor, num_actual))
        elif tipo == "eq":
            nuevos.append(ecuacion(valor))
        elif tipo == "code":
            nuevos.extend(codigo(valor))
        elif tipo == "nota":
            nuevos.append(nota(valor))
        elif tipo == "img":
            from PIL import Image

            with Image.open(RESULTADOS / valor) as im:
                ancho, alto = im.size
            nuevos.append(imagen(valor, ancho, alto))
        elif tipo == "cap":
            nuevos.append(leyenda(valor))
        elif tipo == "tbl":
            filas, anchos = valor
            nuevos.append(tabla(filas, anchos, borde=GRIS_CLARO, fondo_encabezado=ENCABEZADO_TABLA, tamano=19))
        else:
            raise ValueError(tipo)
        previo = tipo
    for e in nuevos:
        sect.addprevious(e)

    contenido_sdt = hijos[33].find(W + "sdtContent")
    for h in list(contenido_sdt):
        contenido_sdt.remove(h)
    for p in indice(entradas, None):
        contenido_sdt.append(p)

    # Pie de página con número, sin mostrarlo en la portada.
    ref = E.Element(W + "footerReference")
    ref.set(W + "type", "default")
    ref.set("{%s}id" % RNS, "rIdPie1")
    sect.insert(0, ref)
    if sect.find(W + "titlePg") is None:
        sect.append(E.Element(W + "titlePg"))

    documento = E.tostring(raiz, xml_declaration=True, encoding="UTF-8", standalone=True).decode("utf-8")
    documento = re.sub(r'w:color w:val="a64d79"', f'w:color w:val="{NEGRO}"', documento, flags=re.I)
    partes["word/document.xml"] = documento.encode("utf-8")
    partes["word/numbering.xml"] = numbering[0]
    partes["word/styles.xml"] = estilos_neutros(partes["word/styles.xml"])
    partes["word/settings.xml"] = actualizar_campos(partes["word/settings.xml"])

    partes["word/footer1.xml"] = pie_de_pagina()
    orden.append("word/footer1.xml")
    rels = E.fromstring(partes["word/_rels/document.xml.rels"])
    E.SubElement(rels, "{%s}Relationship" % RELNS, Id="rIdPie1",
                 Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer",
                 Target="footer1.xml")
    for rid, nombre in IMAGENES:
        E.SubElement(rels, "{%s}Relationship" % RELNS, Id=rid,
                     Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image",
                     Target="media/" + nombre)
        partes["word/media/" + nombre] = (RESULTADOS / nombre).read_bytes()
        orden.append("word/media/" + nombre)
    partes["word/_rels/document.xml.rels"] = E.tostring(rels, xml_declaration=True, encoding="UTF-8",
                                                         standalone=True)
    tipos = partes["[Content_Types].xml"].decode("utf-8")
    tipos = tipos.replace(
        "</Types>",
        '<Override PartName="/word/footer1.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/></Types>',
    )
    partes["[Content_Types].xml"] = tipos.encode("utf-8")

    with zipfile.ZipFile(DESTINO, "w", zipfile.ZIP_DEFLATED) as z:
        for nombre in orden:
            z.writestr(nombre, partes[nombre])
    print("escrito", DESTINO, len(nuevos), "bloques,", len(entradas), "títulos")


if __name__ == "__main__":
    main()
