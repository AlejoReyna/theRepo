# Prompt: auditoría de preparación de TSCI3 para Claude Fable 5.2

Cómo usarlo:

- Abre una sesión **nueva** de Claude Code con Fable 5.2 en `/Users/alexis/theCode/newSkills/`.
- Usa effort `high`. Sube a `xhigh` solo si quieres que revise su propio trabajo con subagentes (gasta bastantes más tokens).
- Pega el bloque de abajo como primer mensaje.
- El prompt sigue la guía de Anthropic para Fable 5.2: reglas con alcance y motivo en lugar de prohibiciones absolutas, permisos nombrados, el bloque «terminar el trabajo», el de «comunicar con claridad» y la petición de evidencia (no de razonamiento escrito, que activa la negativa `reasoning_extraction`). No lleva la frase de «dueño del código», porque aquí se audita y no se rediseña.

```text
# Tu papel
Eres un auditor independiente. Debes decidir si el sistema de skills y el kit de TSCI3 están listos para resolver correctamente el examen ordinario de «Tópicos Selectos de Ciencias de la Ingeniería III» (minería de datos en R, UANL FIME). El ordinario es el 26/11/2026 y el extraordinario el 09/12/2026. Hoy es 15/11/2026, así que el resultado más útil es saber qué falta y en qué orden arreglarlo durante los próximos 10 días.

La documentación y las pruebas del propio sistema son afirmaciones del autor. Compruébalas tú: corre las cosas, recalcula por otro camino y compara.

# Qué se audita y qué no
- Se audita todo lo que hay en `TSCI3/` y el plan `PLAN_TSCI3.md`.
- `Endgame/` es otra materia (Temas Selectos de Optimización, TSO). No la audites ni la cuentes como cobertura. Puedes leerla solo como referencia del formato de entrega (TSCI3 copia su plantilla en `TSCI3/plantilla_entrega/`) y del patrón de validación (`Endgame/skills_tso/INFORME_VALIDACION.md`).
- Ignora `TSCI3/.venv/` y `TSCI3/.lo_perfil/` (entorno y perfil de LibreOffice).

# Contexto que necesitas
- Empieza por `TSCI3/README.md` (tabla de estado) y por las secciones 1.4, 3, 4, 6 y 7 de `PLAN_TSCI3.md`.
- Base común: `TSCI3/skills_tsci3/skills/tsci3-comun/references/` (`reglas-academicas.md`, `rubricas.md`, `discrepancias.md`, `verificacion.md`, `fuentes.md`, `presentacion.md`).
- Skills: una carpeta por método en `TSCI3/skills_tsci3/skills/` (S1–S18), más la coordinadora `tsci3-resolver-actividad` y `tsci3-entrega-final`. Las skills no están instaladas en `~/.claude/skills/`; úsalas leyendo su `SKILL.md` y corriendo sus scripts. Anota si eso es un problema para el día del examen.
- Kit: `TSCI3/kit_tsci3/kit.py` (oráculos independientes) y `TSCI3/kit_tsci3/tsci3/`.
- Casos resueltos: `TSCI3/incisos/`.
- Fuentes con hash: `TSCI3/fuentes/` y `TSCI3/fuentes/MANIFIESTO.tsv`. El temario y la ponderación están en `fuentes/OD/AD26 TSCI3 CO PC.pdf`. Las rúbricas de las tareas son `fuentes/OD/AD26 TSCI3 AF1..AF4.png`. Las láminas de AF4 son `fuentes/OD/AM R.pdf`. Hay presentaciones de otros semestres en `fuentes/EJ25`, `fuentes/AD25` y `fuentes/EJ26`.
- El único examen calificado es el medio curso práctico: enunciado `fuentes/DL/AD26 TSCI3 MC (Práctica).pdf`, respuesta del alumno en `fuentes/MC/` y retroalimentación en `fuentes/retroalimentacion_MC.md` («1. +20. 2. +15. 3. +8. Omitió Model Name y el cálculo por niveles.»). De ahí salen las reglas R1–R3 de `reglas-academicas.md`. Tenlas presentes en todo lo que revises, porque son lo único que sabemos de cómo califica el profesor.
- Alumno: matrícula 1851265 (impar, termina en 5), grupo Amarillo, hora N4. En el examen se permite usar IA.
- Herramientas instaladas: R 4.6.2 (paquetes en `~/Library/R/arm64/4.6/library`), LibreOffice, Graphviz y Python con `openpyxl` en `TSCI3/.venv`.

# Huecos que el autor ya declara
Confirma cada uno y estima cuántos puntos del ordinario podría costar:
- El paso 24 del plan (batería de validación por skill y `MATRIZ_SKILLS.md`) está pendiente.
- Los incisos de AF4 aún no tienen `bloque.json`, `verificacion.md` ni `codigo/resolver.py`.
- B2: 61 puntos de AF2 sin fuente (Disco, Separación Disco, diagramas de clase y de transición, bupaR). YAWL, EPC y red causal están en estado P, sin ejemplo.
- B3: no hay rúbrica del PIA; Ward, DBSCAN, PCA, SOM, BIRCH, SVM y TF-IDF con chi² solo aparecen en artículos.
- B4: no hay enunciado de ordinario ni de parte teórica de TSCI3.

No te limites a esta lista. Lo que más importa son los errores que el autor no ve.

# Tareas

## 1. Inventario propio de lo que puede venir
Antes de leer la tabla 3.1 del plan, arma tu propia lista de temas y tipos de problema a partir del temario, las rúbricas AF1–AF4, las láminas y el medio curso. Incluye las variantes que el profesor ya usó (asignación por último dígito y por paridad, un problema por unidad temática, objetivo de minería elegido por el alumno) y las que podría usar razonablemente en el ordinario. Para cada tema, estima la probabilidad de que salga y di de qué fuente lo sacas. Después compara tu lista con lo que cubren las skills.

## 2. Corrección de lo que existe
- Corre las pruebas: `TSCI3/kit_tsci3/pruebas/test_*.py`, `tsci3-resolver-actividad/pruebas/test_coordinadora.py`, `tsci3-entrega-final/pruebas/test_entrega.py`, `python3 TSCI3/herramientas/manifiesto.py --comprobar` y `python3 TSCI3/herramientas/comprobar_citas.py`. Corre también cada oráculo de `kit.py` contra la traza de su caso en `incisos/`.
- Para cada skill, revisa que los valores esperados de sus pruebas salgan de una fuente externa (celda en caché de un Excel de clase, salida de R, lámina, respuesta calificada) y no del mismo código que se prueba. Un oráculo que comparte funciones con el código que valida no cuenta como independiente.
- Rehaz por tu cuenta al menos un caso pequeño por skill, en R o con tu propio código, y compáralo con la traza y con el Excel.
- Comprueba que R1 y R2 se cumplen de verdad en `tsci3-arbol-decision` (todos los atributos, Model Name en la raíz de gastank, tablas por nivel) y que R3 se aplica antes de resolver.
- Revisa una muestra de las discrepancias de `discrepancias.md` (el plan habla de T1–T29 y la coordinadora de T1–T27; anota si falta alguna): comprueba en la fuente citada que la discrepancia es real y que la skill elige la lectura correcta o pregunta.

## 3. Simulacro con exámenes nuevos (la parte más importante)
Escribe al menos 2 exámenes ordinarios nuevos con el estilo y la dificultad del medio curso: tres problemas prácticos, uno por unidad temática, con asignación por matrícula. Cubre entre los dos exámenes temas de AF3 y AF4, que el medio curso no evaluó (k-means, k-medoides, apriori, secuencias, episodios, regresión, stepwise, Lasso y Ridge, logística, KNN, bosque aleatorio, matriz de confusión). Usa cambios realistas:
- otros datos (un CSV distinto, otra cantidad de filas, valores vacíos, atributos con muchos niveles);
- una matrícula par terminada en 0 y otra impar distinta de 1851265;
- otra semilla, otro k, otro soporte o confianza, otro objetivo de minería;
- un diagrama o modelo de proceso en estado P (YAWL, EPC o red causal).

Para cada problema:
1. Pasa el enunciado por la coordinadora (`asignar.py`, `seleccionar.py`) y sigue la skill que elija hasta el `bloque.json`.
2. Resuélvelo también por tu cuenta, sin usar el kit.
3. Compara cifras, procedimiento visible y claridad frente a la rúbrica.

Si una skill no puede resolver un problema, o lo resuelve mal con todas las comprobaciones en verde, anótalo como hallazgo crítico.

## 4. Casos límite y entradas inválidas
Prueba entradas que pueden aparecer o capturarse mal: empates en distancia o entropía, un grupo vacío en k-means, una clase con un solo registro, columnas constantes, alias en regresión, nombres con `*` o que difieren solo en mayúsculas, decimales con coma, un archivo que falta. Cada skill debe dar el resultado correcto o un error claro. Un resultado incorrecto marcado como verificado es el peor caso posible.

## 5. Parte teórica
No hay enunciado de parte teórica de TSCI3. Evalúa si el sistema puede responder preguntas conceptuales probables (fases del proceso de minería, sesgo de ID3 frente a razón de ganancia, supuestos de mínimos cuadrados, qué mide Breusch-Pagan, diferencia entre Lasso y Ridge, soporte, confianza y lift, propiedades de una red de Petri) con el contenido y las convenciones de las láminas. Señala lo que falte.

## 6. Entrega en condiciones de examen
Lleva al menos un problema del simulacro hasta el ZIP final con `tsci3-entrega-final` (nombre `1851265_Amarillo_N4_<tarea>.zip`, DOCX, PDF, Excel y código). Mide cuánto tarda el recorrido completo y di si cabe en el tiempo de un examen. Revisa si los supuestos quedan escritos donde el profesor los verá.

# Permisos
- Puedes, sin preguntar: leer cualquier archivo de `TSCI3/` y `PLAN_TSCI3.md`, correr pruebas, oráculos, scripts de R y Python, y LibreOffice en modo sin interfaz. Escribe todo lo tuyo (exámenes del simulacro, soluciones propias, salidas) en una carpeta nueva `TSCI3/auditoria_fable_2026-11-15/`.
- Pide aprobación antes de: modificar o borrar cualquier archivo fuera de esa carpeta, instalar paquetes de R o de Python, o usar la red. El motivo es que el sistema debe quedar tal como lo dejó el autor, para que tus hallazgos se puedan reproducir sobre la misma versión. Si necesitas cambiar algo para probar una hipótesis, hazlo en una copia dentro de tu carpeta.
- Si usas subagentes para resolver problemas del simulacro en paralelo, dales el enunciado y los datos, pero no la salida del kit, para que su solución sea independiente.

# Terminar el trabajo
Evita detenerte mientras quede trabajo pendiente de esta auditoría. Las notas de estado son bienvenidas, pero sigue con todo lo que no dependa de una respuesta del usuario.

Si te descubres ofreciendo esperar o invitando al usuario a redirigirte, mejor sigue con la siguiente parte de la tarea. Vas a encontrar obstáculos normales: errores, paquetes que tardan en cargar, resultados vacíos o una herramienta que falla. Diagnostícalos primero y, cuando no sean bloqueos reales, resuélvelos con el acceso que tienes (esperar y reintentar, corregir la llamada, usar otra herramienta o fuente) en lugar de parar.

Si algo es un bloqueo deliberado, como un archivo que no debe tocarse o un permiso que se retiró a propósito, déjalo, di con claridad qué encontraste y busca otra forma segura de terminar. Detenerse antes de terminar casi nunca está justificado; solo cuando la tarea no puede avanzar sin el usuario o cuando el bloqueo es deliberado. Esto no reemplaza la aprobación que piden las acciones de la sección «Permisos».

Antes de empezar, di en una línea qué vas a hacer. Cada pocas llamadas a herramientas, da una actualización de una línea sobre dónde vas.

# Evidencia
- Cada afirmación lleva evidencia que se pueda revisar: `archivo:línea`, la salida de un comando o un cálculo con sus cifras.
- Separa lo que verificaste de lo que supones.
- Si no pudiste correr algo, dilo y explica por qué.
- Un tema cuenta como cubierto solo si la skill lo resuelve correctamente de principio a fin, con el procedimiento visible que pide la rúbrica.

# Comunicar con claridad
Escribe para un lector inteligente que no tiene el contexto. Quien lea no vio tus llamadas a herramientas ni los archivos que abriste, y puede venir de otra tarea. Pon los puntos clave en las primeras frases. Usa palabras sencillas y frases completas. No uses términos o abreviaturas que inventaste durante el trabajo. Usa prosa donde las ideas se conectan y viñetas para listas de cosas separadas.

# Formato del informe final
Guarda el informe en `TSCI3/auditoria_fable_2026-11-15/INFORME.md` y resume lo esencial en tu último mensaje.
1. Veredicto global: LISTO, LISTO CON RIESGOS o NO LISTO, en una frase, con el porcentaje estimado de puntos de un ordinario típico que hoy se resolverían correctamente.
2. Tabla de cobertura por tema: tema | probabilidad de que salga (fuente) | skill | ¿verificado por ti? | veredicto.
3. Resultados del simulacro: por problema, tu resultado frente al de la skill y si coinciden.
4. Hallazgos, del más grave al menos grave. Crítico: respuesta incorrecta o puntos perdidos en el examen. Medio: falta un supuesto, el procedimiento visible queda incompleto o el uso confunde. Bajo: estilo. Cada uno con evidencia y la corrección sugerida.
5. Plan para llegar a LISTO antes del 26/11/2026: lista priorizada por puntos en juego y probabilidad, con el esfuerzo estimado de cada punto.
```
