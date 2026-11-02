"""Reconstruye el cuerpo del informe sobre una copia, conservando portada y estilos."""
import copy
import re
import shutil
import sys
import zipfile
from pathlib import Path

from lxml import etree as E

ORIGEN, DESTINO = Path(sys.argv[1]), Path(sys.argv[2])
WNS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
MNS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
W = "{%s}" % WNS
M = "{%s}" % MNS
XML = "{http://www.w3.org/XML/1998/namespace}space"

CONTENIDO = [
("h1", "Introducción"),
("p", "La calidad de las respuestas de un modelo de lenguaje depende de cómo se formulan las instrucciones y de los parámetros de generación. Este proyecto estudia cómo elegir una configuración de prompt que aumente la precisión del modelo sin evaluar todas las combinaciones, porque cada evaluación consume tiempo de GPU."),
("p", "Una configuración combina cinco ranuras de instrucciones (rol, estrategia, formato, estilo y cierre) con una temperatura de generación. El resultado de este trabajo es una configuración obtenida mediante una búsqueda documentada, registrada en entrega.json. Se reporta como la mejor configuración encontrada, no como un óptimo global demostrado."),
("h1", "Planteamiento del problema"),
("p", "El problema se separa en dos partes, porque su dificultad tiene naturaleza distinta:"),
("b", "**Parte 1, configuración óptima con oráculo exacto:** se supone que el cumplimiento de cada restricción puede calcularse sin error. La dificultad es combinatoria, y es la parte cuya NP-dureza se demuestra."),
("b", "**Parte 2, búsqueda con consultas limitadas o ruidosas:** la precisión se estima con un presupuesto de consultas a un modelo real. La dificultad es el costo de evaluación y de muestreo. La demostración de la Parte 1 no se traslada a esta parte."),
("h1", "Variante seleccionada: espacio extendido con temperatura"),
("p", "Se selecciona la variante de la sección 4.5 del enunciado, que incorpora la temperatura como decisión adicional con tres niveles. Las variables de decisión son:"),
("b", "**Rol:** perfil que asume el modelo."),
("b", "**Estrategia:** enfoque para resolver la solicitud."),
("b", "**Formato:** estructura de la respuesta."),
("b", "**Estilo:** uso de caracteres, puntuación y mayúsculas."),
("b", "**Cierre:** instrucción ubicada después de la solicitud."),
("b", "**Temperatura:** parámetro de generación, con niveles 0.0, 0.3 y 0.7."),
("p", "El catálogo del proyecto ofrece 8 opciones por ranura. Las categorías y los valores corresponden a la guía de primera entrega y a la interfaz del oráculo del curso, que prevalecen sobre las categorías Verificación y Recordatorio del enunciado inicial."),
("h1", "Formalización del problema"),
("h2", "Tamaño de la entrada"),
("p", "El tamaño no se reduce a una sola variable. Intervienen:"),
("b", "$d$: número de ranuras de decisión."),
("b", "$k_{i}$: número de opciones de la ranura $i$."),
("b", "$|T|$: número de niveles de temperatura."),
("b", "$|C|$: número de configuraciones candidatas."),
("b", "$n$: número de instancias disponibles para la búsqueda."),
("b", "$B$: presupuesto máximo de consultas."),
("p", "El espacio de búsqueda es:"),
("eq", "|C|=|T|∏_{i=1}^{d}k_{i}"),
("p", "En el proyecto, $d=5$, $k_{i}=8$ y $|T|=3$, por lo que:"),
("eq", "|C|=3·8^{5}=98304"),
("p", "Además, $n=100$ instancias de búsqueda, y existen 87 instancias de validación que no se usan para elegir. Sin temperatura, el espacio tiene 32 768 configuraciones."),
("h2", "Parte 1: oráculo exacto"),
("p", "**Entrada:** las $d$ ranuras con sus opciones, los niveles de $T$, un conjunto de instancias $I$ con $|I|=n$, y para cada instancia un conjunto de restricciones verificables en tiempo polinomial."),
("p", "Una configuración es una tupla $c=(r,e,f,s,l,t)$, con una opción por ranura y un nivel de temperatura. Para cada instancia $i$ se define $a(c,i)=1$ si la respuesta con $c$ cumple todas las restricciones de $i$, y $a(c,i)=0$ en caso contrario. Esta evaluación es todo-o-nada. La precisión es:"),
("eq", "A(c)=(1/n)∑_{i∈I}a(c,i)"),
("p", "**Salida:** una configuración $c^{*}∈C$."),
("p", "**Objetivo:** maximizar $A(c)$ sobre $C$."),
("p", "**Representación:** la entrada describe las ranuras y las restricciones de forma compacta. El conjunto $C$ no se lista explícitamente, porque su tamaño es exponencial en $d$."),
("h2", "Parte 2: consultas limitadas o ruidosas"),
("p", "**Entrada:** las configuraciones $C$, las instancias $I$, un presupuesto $B$ y un oráculo que, para una configuración y una instancia, genera una respuesta y la verifica. Una consulta equivale a una generación: un par (configuración, instancia) evaluado por el modelo. Un par ya guardado en caché no cuesta de nuevo."),
("p", "**Salida:** una asignación de $m_{j}$ consultas por configuración $c_{j}$, una configuración ganadora $c^{*}$, su precisión estimada y el registro de la búsqueda."),
("p", "**Objetivo y restricción:** maximizar la precisión esperada $Acc(c^{*})$ sobre datos de prueba no observados, con presupuesto global:"),
("eq", "∑_{j=1}^{|C|}m_{j}≤B"),
("p", "La restricción es global: limita la suma de todas las consultas, no las de cada configuración."),
("h2", "Supuestos y alcance"),
("b", "El oráculo del curso no limita las consultas, por lo que $B$ lo fija el equipo según el tiempo de GPU disponible."),
("b", "Las instancias de búsqueda y validación provienen del mismo conjunto de datos del curso."),
("b", "Los experimentos de corrección y de costo sin GPU usan instancias sintéticas generadas con semilla fija."),
("b", "La evaluación final se hace con datos privados, que incluyen familias de restricciones que no aparecen en los datos visibles."),
("h1", "Prueba de NP-dureza por reducción desde 3-SAT"),
("p", "La demostración se refiere a la Parte 1. Se reduce desde 3-SAT, como indica la guía de primera entrega para el Grupo 1."),
("h2", "Problema de origen: 3-SAT"),
("p", "**Entrada:** variables booleanas $x_{1},…,x_{v}$ y una fórmula $φ=C_{1}∧…∧C_{q}$, donde cada cláusula es una disyunción de tres literales."),
("p", "**Pregunta:** ¿existe una asignación que haga verdadera a $φ$?"),
("p", "3-SAT es NP-completo (Cook, 1971; Karp, 1972)."),
("h2", "Problema de destino: CONFIGURACIÓN GENERALIZADA"),
("p", "Con $d$ fijo el problema no es NP-difícil, como se explica más adelante. Por eso se estudia la versión generalizada, en la que $d$ forma parte de la entrada."),
("p", "**Entrada:** un entero $d$, conjuntos finitos de opciones $A_{1},…,A_{d}$, niveles $T$, $n$ instancias con restricciones verificables en tiempo polinomial, y un umbral $θ∈[0,1]$."),
("p", "**Pregunta:** ¿existe una configuración $c∈A_{1}×…×A_{d}×T$ tal que $A(c)≥θ$?"),
("h2", "Construcción de la reducción"),
("p", "Dada una instancia de 3-SAT con $v$ variables y $q$ cláusulas, se construye:"),
("b", "$d=v$ ranuras, una por variable."),
("b", "$A_{j}={0,1}$ para cada ranura $j$. La opción elegida representa el valor de $x_{j}$."),
("b", "$T$ con los tres niveles del proyecto. Las restricciones ignoran la temperatura, así que no altera el resultado."),
("b", "$n=q$ instancias. La instancia $i$ tiene una restricción: se cumple si y solo si la tupla elegida hace verdadero al menos un literal de $C_{i}$."),
("b", "$θ=1$."),
("p", "De este modo, $A(c)$ es la fracción de cláusulas satisfechas por la asignación que representa $c$."),
("h2", "Corrección de la reducción"),
("p", "**Si φ es satisfacible, existe la configuración.** Sea $σ$ una asignación que satisface $φ$. Se toma la configuración con $c_{j}=σ(x_{j})$ para cada $j$ y cualquier temperatura. Cada cláusula tiene un literal verdadero, de modo que cada instancia cumple su restricción. Entonces $a(c,i)=1$ para toda $i$, y $A(c)=1≥θ$."),
("p", "**Si existe la configuración, φ es satisfacible.** Sea $c$ tal que $A(c)≥1$. Como $A(c)$ es un promedio de valores en ${0,1}$, se tiene $a(c,i)=1$ para toda $i$. Se define $σ(x_{j})=c_{j}$. Cada restricción cumplida significa que $σ$ hace verdadero un literal de esa cláusula, por lo que $σ$ satisface $φ$."),
("p", "Por lo tanto, $φ$ es satisfacible si y solo si la instancia construida tiene respuesta afirmativa."),
("h2", "Tiempo de la transformación"),
("p", "Se crean $v$ ranuras de dos opciones y $q$ restricciones de tres literales, en tiempo $O(v+q)$. La construcción no enumera $C$, que tendría $3·2^{v}$ configuraciones. La reducción es polinomial."),
("h2", "Conclusión"),
("p", "La versión de decisión es NP-difícil. También pertenece a NP: una configuración es un certificado de tamaño polinomial y $A(c)$ se calcula en tiempo polinomial con el oráculo exacto. Por tanto, es NP-completa. La versión de optimización es NP-difícil: si se pudiera hallar el máximo de $A$ en tiempo polinomial, bastaría compararlo con $θ$ para decidir."),
("h2", "Ejemplo de la transformación"),
("p", "Sea $φ=(x_{1}∨¬x_{2}∨x_{3})∧(¬x_{1}∨x_{2}∨x_{3})∧(¬x_{1}∨¬x_{2}∨¬x_{3})$. La construcción produce 3 ranuras binarias, 3 instancias y $θ=1$."),
("b", "La asignación $(1,1,0)$ satisface $C_{1}$ por $x_{1}$, $C_{2}$ por $x_{2}$ y $C_{3}$ por $¬x_{3}$. La configuración correspondiente obtiene $A(c)=3/3=1$, y alcanza el umbral."),
("b", "La asignación $(1,1,1)$ deja falsa a $C_{3}$. Su configuración obtiene $A(c)=2/3<1$, y no alcanza el umbral."),
("h2", "Alcance de la demostración"),
("b", "**Ranuras fijas:** con $d=5$, $k_{i}=8$ y $|T|=3$, el espacio es una constante. Una enumeración exhaustiva con oráculo exacto es polinomial en $n$. La NP-dureza describe el crecimiento con $d$, no el caso concreto de seis decisiones."),
("b", "**Modelo real:** la prueba no afirma nada sobre la dificultad de un modelo de lenguaje con respuestas ruidosas. Esa parte se analiza por costo de muestreo."),
("h1", "Algoritmo exacto: función de eficiencia"),
("h2", "Backtracking con poda por cota superior"),
("p", "El algoritmo recorre el árbol de decisiones: cada nivel fija una ranura. Antes de bajar a un nodo interno calcula una cota superior de la precisión alcanzable y corta la rama si la cota no supera la mejor solución hallada. La implementación está en src/busqueda.py, en la función backtracking."),
("p", "La cota mide la configuración parcial, sin las ranuras no decididas. Es admisible cuando agregar instrucciones nunca aumenta la precisión. Esta propiedad se cumple en el oráculo sintético, y por eso allí el algoritmo es exacto. Con el modelo real es solo un supuesto."),
("h2", "Deducción de T en el peor caso"),
("p", "La operación básica es una generación. Se toman $k$ opciones por ranura. Sea $T(h)$ el costo de explorar un nodo al que le faltan $h$ ranuras por decidir, sin ninguna poda."),
("p", "Si $h=1$, los $k$ hijos son hojas y cada hoja se evalúa en $n$ instancias:"),
("eq", "T(1)=kn"),
("p", "Si $h≥2$, se calcula la cota de cada uno de los $k$ hijos, con costo $n$, y luego se explora cada hijo:"),
("eq", "T(h)=kT(h-1)+kn"),
("p", "Al expandir la recurrencia:"),
("eq", "T(h)=kn+k^{2}n+…+k^{h}n=n∑_{j=1}^{h}k^{j}"),
("p", "Por la suma geométrica, para todo el árbol ($h=d$) y $k≥2$:"),
("eq", "T(d,k,n)=nk(k^{d}-1)/(k-1)=Θ(nk^{d})=Θ(|C|n)"),
("p", "Esta forma coincide con la cota $O(|C|n)$ del enunciado. El costo es lineal en $|C|$, pero exponencial en $d$, porque $|C|=k^{d}$. El ordenamiento de los hijos agrega comparaciones, pero no generaciones."),
("p", "Sin temperatura, con $k=8$, $d=5$ y $n=100$:"),
("eq", "T=100(8+64+512+4096+32768)=3744800"),
("p", "La prueba test_peor_caso_de_backtracking_coincide_con_t_del_informe confirma, con una cota que no poda, que el código gasta exactamente $n∑k^{j}$ generaciones. Con poda, el costo real depende de la instancia, y se reporta como nodos, hojas y podas."),
("h1", "Costo de evaluación y de muestreo"),
("h2", "Successive Halving con tope"),
("p", "En cada ronda se evalúan $|C_{r}|=|C|/2^{r}$ configuraciones y se conserva la mitad mejor. Sin tope, con $n_{r}=n_{0}2^{r}$ y $|C|=2^{R}$:"),
("eq", "T=∑_{r=0}^{R-1}(|C|/2^{r})n_{0}2^{r}=|C|n_{0}R"),
("p", "Esa fórmula exige $n_{R-1}=n_{0}2^{R-1}$ instancias. Con $n_{0}=2$ y solo 100 instancias, el límite se supera desde la ronda 6, que pediría 128. Por eso el costo no es realmente independiente de $n$, y se usa $n_{r}=min(n_{0}2^{r},n)$."),
("p", "Sea $r^{*}$ la primera ronda con tope. Si $r^{*}<R$:"),
("eq", "T=|C|n_{0}r^{*}+n|C|(2^{1-r^{*}}-2^{1-R})"),
("p", "Como $2^{r^{*}}≥n/n_{0}$, el segundo término es a lo sumo $2|C|n_{0}$. Entonces:"),
("eq", "T=O(|C|n_{0}min(log|C|,log(n/n_{0})))"),
("p", "La prueba test_costo_con_tope_coincide_con_la_formula_del_informe compara esta fórmula con el costo calculado por el código. Además, el enunciado propone $|C|=3840$, para el cual $log_{2}|C|$ no es entero; la cifra de 91 444 consultas es una aproximación."),
("p", "Medir todo el espacio no cabe en $B$, así que el algoritmo parte de una muestra aleatoria con el mayor tamaño que el presupuesto permite. Karnin, Koren y Somekh (2013) dan una garantía de identificación para recompensas estocásticas. Aquí no se aplica directamente, porque se trabaja con una muestra de candidatos y un conjunto finito de instancias."),
("h2", "Ascenso por coordenadas"),
("p", "Cada pasada evalúa las opciones de una ranura con las demás fijas. Con $I$ pasadas:"),
("eq", "T=O(I·n∑_{i=1}^{d}k_{i})"),
("p", "Sin caché, una pasada cuesta $40·100=4000$ generaciones, frente a más de 3 millones de la enumeración. La heurística no tiene una razón de aproximación demostrada: si dos opciones solo mejoran juntas, ningún cambio individual sube la precisión y la búsqueda se detiene en un óptimo local. El riesgo crece cuando las ranuras interactúan."),
("h2", "Ruido de muestreo"),
("p", "La precisión medida con $n$ instancias es un promedio de valores 0 o 1. Si se tratan como muestras independientes, la desigualdad de Hoeffding da, para una configuración fija y confianza $1-δ$, un error de a lo sumo:"),
("eq", "ε=√(ln(2/δ)/(2n))"),
("p", "Con $n=100$ y $δ=0.05$, $ε≈0.136$. Si se quiere la misma garantía a la vez para las 98 304 configuraciones, $ε≈0.275$. Son márgenes conservadores y amplios frente a un techo de precisión cercano a 24%. Por eso una diferencia pequeña en la búsqueda no prueba que una configuración sea mejor, y la precisión de la ganadora tiende a ser optimista. La validación se hace con instancias separadas."),
("h1", "Proceso de optimización"),
("p", "La búsqueda se documenta en notebooks/01_busqueda.ipynb, sobre el modelo qwen17b. La elección solo usa las 100 instancias de búsqueda."),
("b", "**Presupuesto (sección 4):** se mide la velocidad y se fija $B$, con un máximo de 15 000 generaciones por método."),
("b", "**Ascenso por coordenadas (sección 5):** parte de una configuración aleatoria con semilla fija, hace hasta 3 pasadas y se detiene si una pasada no mejora."),
("b", "**Uso de trazas (sección 6):** una opción se retira de las pasadas siguientes si la mejor de su ranura supera 10% y la opción queda al menos 3 puntos por debajo. Se registra qué familias de restricciones falló de más."),
("b", "**Temperatura (sección 7):** se prueban los tres niveles sobre la mejor configuración, con tres semillas si la temperatura es mayor que 0. Solo se cambia ante una mejora estricta."),
("b", "**Comparación (secciones 8 a 10):** Successive Halving y backtracking reciben el mismo $B$. El backtracking se limita a las dos mejores opciones por ranura."),
("b", "**Validación (sección 11):** se invoca oraculo.validar sobre la configuración elegida, sin volver a elegir."),
("h1", "Resultados y razonamiento"),
("p", "La búsqueda se ejecutó en Google Colab con una GPU T4. La velocidad medida fue de 0,50 generaciones por segundo, así que con 3 horas de GPU el presupuesto quedó en $B=1803$ generaciones por método. Con ese $B$, cada método podía medir unas 18 configuraciones completas sobre las 100 instancias. Una sola pasada del ascenso por coordenadas cuesta 4000, así que ese método y el backtracking agotaron $B$ antes de terminar."),
("tbl", [["Método", "Precisión en búsqueda", "Generaciones", "Configuración"],
         ["Ascenso por coordenadas", "8%", "1800", "rol 5, estrategia 1, formato 2, estilo 3, cierre 7, temperatura 0.0"],
         ["Successive Halving", "16%", "968", "rol 7, estrategia 0, formato 0, estilo 2, cierre 1, temperatura 0.7"],
         ["Backtracking en subespacio", "8%", "1800", "rol 0, estrategia 2, formato 0, estilo 3, cierre 0, temperatura 0.0"]]),
("p", "Gana Successive Halving, con 16% sobre las 100 instancias de búsqueda, y su configuración es la de entrega.json. Fue el único método que terminó sin agotar $B$. Partió de 128 configuraciones aleatorias con $n_{0}=2$ y duplicó las instancias en cada ronda hasta dejar dos finalistas, medidas con las 100. También fue el único que exploró las tres temperaturas desde el inicio. La figura 1 muestra la mejor precisión de cada método según las generaciones gastadas."),
("img", ("comparacion_informe.png", 1030, 682)),
("cap", "Figura 1. Mejor precisión entre las configuraciones completas medidas con las 100 instancias de búsqueda, según las generaciones gastadas. El salto del ascenso a 11% corresponde a formato 0, que se midió pero no se adoptó porque B se agotó antes de cerrar la ranura. Generada con resultados/graficar_comparacion.py."),
("h2", "Configuración final y validación"),
("p", "La configuración entregada es rol 7, estrategia 0, formato 0, estilo 2, cierre 1 y temperatura 0.7, para el grupo G01 y la semana 6. En validación obtuvo 11,5%, es decir, 10 de 87 instancias, 4,5 puntos menos que en búsqueda. La caída es esperable: la ganadora se eligió por ser la más alta entre muchas medidas ruidosas, y con $n=100$ el margen de Hoeffding es de unos 13,6 puntos. Por eso ninguna diferencia entre los métodos de esta corrida es estadísticamente significativa."),
("p", "En validación, las restricciones que más fallaron fueron last_word:last_word_sent y punctuation:punctuation_dot, con 6 instancias cada una, y keywords:no_adjacent_consecutive, copy:repeat_phrase y combination:repeat_prompt, con 5. Dos de ellas, last_word:last_word_sent y copy:repeat_phrase, también estaban entre las que más fallaban en búsqueda. En ambos conjuntos dominan las restricciones de poner palabras en posiciones fijas y de repetir texto exacto."),
("p", "La temperatura 0.7 de la ganadora se midió con una sola semilla. En la sección 7, sobre la configuración del ascenso por coordenadas, subir la temperatura bajó el promedio de tres semillas: 8% con 0.0, 6,3% con 0.3 y 6% con 0.7. Parte del 16% puede deberse al azar del muestreo, y la precisión en la evaluación privada puede variar entre ejecuciones."),
("h2", "Descartes por trazas"),
("p", "No hubo descartes. La regla exige que la mejor opción de la ranura supere el piso de 10%, y en las ranuras que se alcanzaron a completar, rol y estrategia, la mejor llegó a 8% y 6%. Con precisiones tan bajas, una opción y otra difieren en una o dos instancias por familia, y esa diferencia no permite atribuir el fallo a la opción."),
("p", "Las trazas sí muestran que las mismas familias fallan en todas las configuraciones. En promedio, sobre 45 configuraciones medidas con las 100 instancias, fallan copy:copy (6 de 100), last_word:last_word_sent (5,9), new:copy_span_idx (5), copy:repeat_phrase (3,9), keywords:start_end (3,8) y keywords:keyword_specific_position (3,7). Son restricciones de copiar texto exacto o de poner palabras en posiciones fijas. Que fallen igual con cualquier prompt indica que dependen más de la capacidad del modelo de 1.7B parámetros que de las instrucciones."),
("h2", "Lo que mostró cada método"),
("b", "**Ascenso por coordenadas:** agotó $B$ a mitad de la primera pasada, en la ranura de formato. Ahí midió formato 0 con 11%, por encima del 8% de la configuración actual, pero el código solo adopta un cambio al terminar de medir toda la ranura, y el presupuesto se acabó antes. Por eso reporta 8%. Para la siguiente entrega se corregirá: al agotarse $B$, el método debe quedarse con la mejor configuración que alcanzó a medir."),
("b", "**Backtracking:** visitó 16 nodos, llegó a 6 hojas y podó una rama antes de agotar $B$. Los prompts parciales obtuvieron más que los completos: solo con el rol 0 se obtuvo 15%, y solo con el rol 5, 14%, mientras que ninguna hoja superó 8%. Por eso la cota fue muy holgada y podó poco. Esto también sugiere que, con este modelo, agregar instrucciones tiende a bajar la precisión."),
("b", "**Successive Halving:** fue el más eficiente, con 968 generaciones, el 54% de $B$, porque descartó la mayoría de candidatos con 2 o 4 instancias. El costo es que esas primeras rondas son muy ruidosas: con 2 instancias, una configuración sigue o sale por una sola respuesta."),
("h1", "Validación y reproducibilidad"),
("p", "La función oraculo.validar mide la configuración elegida sobre la partición de validación, con muestra fija, e informa las restricciones que más fallaron. Comprueba si la configuración se sostiene en instancias nuevas de las mismas familias. No equivale a la evaluación final, que usa datos privados a los que el equipo no tiene acceso."),
("p", "Los archivos están en la rama solucion-base del repositorio samyquito/SYY-Adag1-Oraculo:"),
("b", "entrega.json, en la raíz."),
("b", "notebooks/01_busqueda.ipynb y notebooks/02_evaluacion.ipynb."),
("b", "src/busqueda.py, src/oraculo_sintetico.py y tests/."),
("b", "docs/manual_tecnico.md."),
("b", "resultados/: registros de cada método, caché del oráculo, resumen.json y comparacion.png."),
("h1", "Limitaciones"),
("b", "La configuración reportada es la mejor encontrada, no un óptimo global demostrado."),
("b", "El presupuesto real fue de solo 1803 generaciones por método, porque el modelo genera unas 0,5 respuestas por segundo en una T4. El ascenso por coordenadas no completó ni una pasada y el backtracking no terminó su subespacio."),
("b", "La configuración elegida usa temperatura 0.7 y su precisión se midió con una sola semilla."),
("b", "El backtracking con el modelo real depende de un supuesto de monotonía y de un subespacio reducido, así que no certifica optimalidad."),
("b", "Cada traza informa solo la primera restricción incumplida."),
("b", "La guía no indica con qué modelo se califica; se asumió qwen17b, el modelo por defecto del curso."),
("b", "Los datos privados incluyen familias de restricciones nuevas, por lo que la precisión final puede diferir."),
("h1", "Referencias"),
("b", "Cook, S. A. (1971). The complexity of theorem-proving procedures. Proceedings of the Third Annual ACM Symposium on Theory of Computing."),
("b", "Hoeffding, W. (1963). Probability inequalities for sums of bounded random variables. Journal of the American Statistical Association, 58(301)."),
("b", "Karnin, Z., Koren, T. y Somekh, O. (2013). Almost optimal exploration in multi-armed bandits. Proceedings of the 30th International Conference on Machine Learning."),
("b", "Karp, R. M. (1972). Reducibility among combinatorial problems. En Complexity of Computer Computations. Plenum Press."),
]


def ele(tag, parent=None, **attrs):
    e = E.Element(tag) if parent is None else E.SubElement(parent, tag)
    for k, v in attrs.items():
        e.set(W + k, str(v))
    return e


def corrida(p, texto, negrita=False, resaltar=False):
    r = ele(W + "r", p)
    if negrita or resaltar:
        pr = ele(W + "rPr", r)
        if negrita:
            ele(W + "b", pr, val="1")
            ele(W + "bCs", pr, val="1")
        if resaltar:
            ele(W + "highlight", pr, val="yellow")
    t = ele(W + "t", r)
    t.text = texto
    t.set(XML, "preserve")


def m_run(padre, texto):
    if not texto:
        return
    r = E.SubElement(padre, M + "r")
    t = E.SubElement(r, M + "t")
    t.text = texto
    t.set(XML, "preserve")


def grupo(s, i):
    assert s[i] == "{", s
    prof, j = 0, i
    while True:
        prof += {"{": 1, "}": -1}.get(s[j], 0)
        if prof == 0:
            return s[i + 1 : j], j + 1
        j += 1


def contenedor(padre, nombre, texto):
    e = E.SubElement(padre, M + nombre)
    llenar(e, texto)


def llenar(padre, s):
    """Interpreta `_{}` y `^{}`. La base es el símbolo anterior, o `∑`/`∏` como n-ario."""
    i, buf = 0, ""
    while i < len(s):
        if s[i] in "_^":
            base, buf = buf[-1:], buf[:-1]
            m_run(padre, buf)
            buf = ""
            sub = sup = None
            while i < len(s) and s[i] in "_^":
                marca = s[i]
                texto, i = grupo(s, i + 1)
                if marca == "_":
                    sub = texto
                else:
                    sup = texto
            if base in "∑∏":
                nary = E.SubElement(padre, M + "nary")
                pr = E.SubElement(nary, M + "naryPr")
                E.SubElement(pr, M + "chr").set(M + "val", base)
                E.SubElement(pr, M + "limLoc").set(M + "val", "undOvr")
                if sup is None:
                    E.SubElement(pr, M + "supHide").set(M + "val", "1")
                contenedor(nary, "sub", sub or "")
                contenedor(nary, "sup", sup or "")
                resto = E.SubElement(nary, M + "e")
                llenar(resto, s[i:])
                return
            nombre = "sSubSup" if sub is not None and sup is not None else ("sSub" if sub is not None else "sSup")
            n = E.SubElement(padre, M + nombre)
            contenedor(n, "e", base)
            if sub is not None:
                contenedor(n, "sub", sub)
            if sup is not None:
                contenedor(n, "sup", sup)
        else:
            buf += s[i]
            i += 1
    m_run(padre, buf)


def en_linea(p, texto):
    """Admite **negrita** y $matemáticas$."""
    for parte in re.split(r"(\*\*.+?\*\*|\$[^$]+\$)", texto):
        if not parte:
            continue
        if parte.startswith("**"):
            for sub in re.split(r"(\$[^$]+\$)", parte[2:-2]):
                if sub.startswith("$"):
                    llenar(E.SubElement(p, M + "oMath"), sub[1:-1])
                elif sub:
                    corrida(p, sub, negrita=True)
        elif parte.startswith("$"):
            llenar(E.SubElement(p, M + "oMath"), parte[1:-1])
        else:
            corrida(p, parte)


def espaciado(ppr, **kw):
    ele(W + "spacing", ppr, line=276, lineRule="auto", **kw)


marcador = [100]


def titulo(nivel, texto):
    p = ele(W + "p")
    ppr = ele(W + "pPr", p)
    ele(W + "pStyle", ppr, val=f"Heading{nivel}")
    ele(W + "keepNext", ppr, val="1")
    ele(W + "keepLines", ppr, val="1")
    if nivel == 1:
        espaciado(ppr, after=80)
    nombre = f"_sec{marcador[0]}"
    ele(W + "bookmarkStart", p, id=marcador[0], name=nombre)
    ele(W + "bookmarkEnd", p, id=marcador[0])
    marcador[0] += 1
    corrida(p, texto, negrita=nivel == 2)
    return p, nombre


def parrafo(texto):
    p = ele(W + "p")
    espaciado(ele(W + "pPr", p), before=120, after=120)
    en_linea(p, texto)
    return p


def vineta(texto, num_id):
    p = ele(W + "p")
    ppr = ele(W + "pPr", p)
    num = ele(W + "numPr", ppr)
    ele(W + "ilvl", num, val=0)
    ele(W + "numId", num, val=num_id)
    espaciado(ppr, before=60, after=60)
    ele(W + "ind", ppr, left=720, hanging=360)
    en_linea(p, texto)
    return p


def ecuacion(texto):
    p = ele(W + "p")
    ppr = ele(W + "pPr", p)
    espaciado(ppr, before=120, after=120)
    ele(W + "jc", ppr, val="center")
    llenar(E.SubElement(p, M + "oMath"), texto)
    return p


def pendiente(texto):
    p = ele(W + "p")
    espaciado(ele(W + "pPr", p), before=120, after=120)
    corrida(p, texto, negrita=True, resaltar=True)
    return p


IMAGENES = []


def imagen(nombre, ancho_px, alto_px):
    rid = f"rIdImg{len(IMAGENES) + 1}"
    IMAGENES.append((rid, nombre))
    cx = 5486400
    cy = cx * alto_px // ancho_px
    n = 100 + len(IMAGENES)
    p = ele(W + "p")
    ppr = ele(W + "pPr", p)
    espaciado(ppr, before=120, after=60)
    ele(W + "jc", ppr, val="center")
    r = ele(W + "r", p)
    r.append(E.fromstring(
        '<w:drawing xmlns:w="%s" '
        'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
        'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="%d" cy="%d"/>'
        '<wp:effectExtent l="0" t="0" r="0" b="0"/><wp:docPr id="%d" name="%s"/>'
        '<wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr>'
        '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        '<pic:pic><pic:nvPicPr><pic:cNvPr id="%d" name="%s"/><pic:cNvPicPr/></pic:nvPicPr>'
        '<pic:blipFill><a:blip r:embed="%s"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
        '<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="%d" cy="%d"/></a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic>'
        '</a:graphicData></a:graphic></wp:inline></w:drawing>'
        % (WNS, cx, cy, n, nombre, n, nombre, rid, cx, cy)))
    return p


def leyenda(texto):
    p = ele(W + "p")
    ppr = ele(W + "pPr", p)
    espaciado(ppr, before=0, after=160)
    ele(W + "jc", ppr, val="center")
    r = ele(W + "r", p)
    pr = ele(W + "rPr", r)
    ele(W + "i", pr, val="1")
    ele(W + "sz", pr, val="18")
    t = ele(W + "t", r)
    t.text = texto
    t.set(XML, "preserve")
    return p


def tabla(filas):
    anchos = [2500, 1600, 1400, 3525]
    tbl = ele(W + "tbl")
    pr = ele(W + "tblPr", tbl)
    ele(W + "tblW", pr, w=sum(anchos), type="dxa")
    bordes = ele(W + "tblBorders", pr)
    for lado in ("top", "left", "bottom", "right", "insideH", "insideV"):
        ele(W + lado, bordes, val="single", sz=8, space=0, color="000000")
    ele(W + "tblLayout", pr, type="fixed")
    grid = ele(W + "tblGrid", tbl)
    for a in anchos:
        ele(W + "gridCol", grid, w=a)
    for f, fila in enumerate(filas):
        tr = ele(W + "tr", tbl)
        for a, celda in zip(anchos, fila):
            tc = ele(W + "tc", tr)
            ele(W + "tcW", ele(W + "tcPr", tc), w=a, type="dxa")
            p = ele(W + "p", tc)
            corrida(p, celda, negrita=f == 0, resaltar=celda == "[pendiente]")
    return tbl


def indice(entradas, fldprop):
    salida = []
    for pos, (nivel, texto, nombre) in enumerate(entradas):
        p = ele(W + "p")
        ppr = ele(W + "pPr", p)
        espaciado(ppr, before=40)
        if nivel == 2:
            ele(W + "ind", ppr, left=360)
        if pos == 0:
            r = ele(W + "r", p)
            ele(W + "fldChar", r, fldCharType="begin", dirty="true")
            r = ele(W + "r", p)
            it = ele(W + "instrText", r)
            it.text = ' TOC \\h \\u \\z \\t "Heading 1,1,Heading 2,2,"'
            it.set(XML, "preserve")
            r = ele(W + "r", p)
            ele(W + "fldChar", r, fldCharType="separate")
        h = ele(W + "hyperlink", p, anchor=nombre)
        corrida(h, texto, negrita=nivel == 1)
        if pos == len(entradas) - 1:
            r = ele(W + "r", p)
            ele(W + "fldChar", r, fldCharType="end")
        salida.append(p)
    return salida


def es_vineta(numbering, num_id):
    r = E.fromstring(numbering)
    abstracto = r.xpath(f"w:num[@w:numId='{num_id}']/w:abstractNumId/@w:val", namespaces={"w": WNS})[0]
    return r.xpath(f"w:abstractNum[@w:abstractNumId='{abstracto}']/w:lvl[@w:ilvl='0']/w:numFmt/@w:val",
                   namespaces={"w": WNS})[0]


with zipfile.ZipFile(ORIGEN) as z:
    partes = {i.filename: z.read(i.filename) for i in z.infolist()}
    orden = [i.filename for i in z.infolist()]

NUM_ID = 2
assert es_vineta(partes["word/numbering.xml"], NUM_ID) == "bullet"

raiz = E.fromstring(partes["word/document.xml"])
cuerpo = raiz.find(W + "body")
hijos = list(cuerpo)
assert hijos[33].tag == W + "sdt"
assert "".join(hijos[37].itertext()) == "Introducción"
sect = hijos[-1]
assert sect.tag == W + "sectPr"

for h in hijos[37:-1]:
    cuerpo.remove(h)

nuevos, entradas = [], []
for tipo, valor in CONTENIDO:
    if tipo in ("h1", "h2"):
        nivel = int(tipo[1])
        p, nombre = titulo(nivel, valor)
        entradas.append((nivel, valor, nombre))
        nuevos.append(p)
    elif tipo == "p":
        nuevos.append(parrafo(valor))
    elif tipo == "b":
        nuevos.append(vineta(valor, NUM_ID))
    elif tipo == "eq":
        nuevos.append(ecuacion(valor))
    elif tipo == "todo":
        nuevos.append(pendiente(valor))
    elif tipo == "img":
        nuevos.append(imagen(*valor))
    elif tipo == "cap":
        nuevos.append(leyenda(valor))
    elif tipo == "tbl":
        nuevos.append(tabla(valor))
for e in nuevos:
    sect.addprevious(e)

sdt = hijos[33]
contenido_sdt = sdt.find(W + "sdtContent")
for h in list(contenido_sdt):
    contenido_sdt.remove(h)
for p in indice(entradas, None):
    contenido_sdt.append(p)

ajustes = E.fromstring(partes["word/settings.xml"])
if ajustes.find(W + "updateFields") is None:
    nodo = E.Element(W + "updateFields")
    nodo.set(W + "val", "true")
    siguientes = {"hdrShapeDefaults", "footnotePr", "endnotePr", "compat", "docVars", "rsids",
                  "mathPr", "attachedSchema", "themeFontLang", "clrSchemeMapping", "doNotIncludeSubdocsInStats",
                  "doNotAutoCompressPictures", "forceUpgrade", "captions", "readModeInkLockDown",
                  "smartTagType", "schemaLibrary", "shapeDefaults", "doNotEmbedSmartTags",
                  "decimalSymbol", "listSeparator"}
    ubicado = False
    for hijo in ajustes:
        if E.QName(hijo).localname in siguientes:
            hijo.addprevious(nodo)
            ubicado = True
            break
    if not ubicado:
        ajustes.append(nodo)
partes["word/settings.xml"] = E.tostring(ajustes, xml_declaration=True, encoding="UTF-8", standalone=True)
RELNS = "http://schemas.openxmlformats.org/package/2006/relationships"
rels = E.fromstring(partes["word/_rels/document.xml.rels"])
for rid, nombre in IMAGENES:
    E.SubElement(rels, "{%s}Relationship" % RELNS, Id=rid,
                 Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image",
                 Target="media/" + nombre)
    partes["word/media/" + nombre] = (Path(sys.argv[3]) / nombre).read_bytes()
    orden.append("word/media/" + nombre)
partes["word/_rels/document.xml.rels"] = E.tostring(rels, xml_declaration=True, encoding="UTF-8", standalone=True)
partes["word/document.xml"] = E.tostring(raiz, xml_declaration=True, encoding="UTF-8", standalone=True)

with zipfile.ZipFile(DESTINO, "w", zipfile.ZIP_DEFLATED) as z:
    for nombre in orden:
        z.writestr(nombre, partes[nombre])
print("escrito", DESTINO, len(nuevos), "bloques,", len(entradas), "títulos")
