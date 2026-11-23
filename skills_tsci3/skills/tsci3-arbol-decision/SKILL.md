---
name: tsci3-arbol-decision
description: Construye el árbol de decisión de mínima entropía (ID3) de un dataset categórico con TODOS sus atributos, calculado y mostrado nivel por nivel (tabla por valor de cada atributo en cada nodo impuro), y lo compara con los árboles de R (rpart y ctree). Deja Excel con una hoja por nivel y fórmulas vivas, programa en Python, script R y verificación con oráculo. Úsala cuando el enunciado pida "árbol de decisión", "mínima entropía", "ID3", "ganancia de información", entropía o Gini de atributos, o comparar con árboles obtenidos en R (TSCI3 AF3 Árboles; medio curso problema 3).
---

# Árbol de decisión de mínima entropía (ID3)

Lee antes `../tsci3-comun/references/reglas-academicas.md` (R1 y R2 salen de **este** método: el medio curso perdió puntos aquí) y `../tsci3-comun/references/verificacion.md`.

`T=/Users/alexis/theCode/newSkills/TSCI3`; `SC=$T/skills_tsci3/skills/tsci3-arbol-decision/scripts`.

## Cuándo aplica / cuándo no
- Aplica: «árbol de decisión», «mínima entropía», «ID3», «ganancia de información», entropía/Gini de atributos categóricos, «compare con los árboles de R».
- No aplica: bosques aleatorios (`tsci3-bosque-aleatorio`), regresión. Con atributos numéricos continuos, ninguna fuente del curso da el método de discretización: pregunta antes de cortar.

## Regla (con cita)
- Info(D) = −Σ pᵢ log2 pᵢ; Info_A(D) = Σ |D_j|/|D|·Info(D_j); Ganancia(A) = Info(D) − Info_A(D) (`EJ26-14` p.3, ecs. 2.1–2.3). Gini y razón de ganancia: ecs. 2.4–2.5 y 2.7–2.8.
- **Mínima entropía:** en cada nodo se divide por el atributo con **menor E(A) = Info_A(D)**, que es el de mayor ganancia (`EJ26-14` p.3; `EJ26-21` p.3). La razón de ganancia se informa como comentario; no decide.
- **R1 (calificado):** se evalúan **todos** los atributos, aunque uno tenga muchos valores (Model Name: 163 valores en 737 filas). Excluirlo costó puntos en el medio curso. Única excepción: un atributo con un valor distinto en cada fila (clave como OBJECTID): calcula su E(A), deténte y pregunta.
- **R2 (calificado):** se calcula y se muestra **cada nivel**: cada nodo impuro con la tabla por valor de cada atributo que queda. El nodo es hoja si es puro, si la mejor ganancia es 0 o si no quedan atributos; la hoja predice la clase mayoritaria (empate: orden alfabético, se declara).
- Empate de E(A) entre atributos: el que aparece primero en el archivo (se declara si ocurre).
- Vacíos de un atributo → categoría «Sin especificar» (T16). Mayúsculas distintas son valores distintos («IQ Floor Model» ≠ «iQ Floor Model»), como en R.

## Ejecutar
1. Inciso: `I=$T/incisos/<id>`; copia el CSV a `$I/datos/` y escribe `$I/datos/parametros.json`:
   `{"problema": "…", "archivo": "gastank.csv", "clase": "Type", "vacio": "Sin especificar", "excluir": []}` (`excluir` siempre vacío, R1).
2. Programa: `cp $SC/resolver_arbol.py $I/codigo/resolver.py` y `python3 $I/codigo/resolver.py > $I/salida_python.txt` → `$I/traza.json`.
3. Oráculo: `python3 $T/kit_tsci3/kit.py arbol-oraculo $I/datos/<archivo> $I/traza.json` (✅ obligatorio: R1, R2, cifras de cada nodo, hojas, resumen).
4. R: `cp $SC/script_arbol.R $I/codigo/script.R` (cambia ARCHIVO, CLASE y VACIO arriba), `Rscript $I/codigo/script.R > $I/salida_R.txt 2>&1`. Deja `id3_R.csv`, `comparacion_R.csv` y `predicciones_R.csv`.
5. Traza contra R y tabla comparativa: `python3 $SC/comparar_r.py $I` (✅ obligatorio) → `comparacion.csv`.
6. Excel: `$T/.venv/bin/python $SC/excel_arbol.py $I --comparacion $I/comparacion.csv`, después recalcula con LibreOffice y comprueba Control: `$T/.venv/bin/python $T/skills_tsci3/skills/tsci3-comun/scripts/recalcular_excel.py $I/Demostración.xlsx` (todas «sí»).

## Procedimiento a mostrar
1. Datos: registros, clase, atributos (todos), valores distintos, vacíos recodificados.
2. H de la clase con la sustitución completa.
3. **Nivel 1:** tabla por valor de cada atributo (n, conteo por clase, H(Sᵥ), peso, aporte), E(A), ganancia; decisión. Si un atributo tiene muchos valores, la tabla completa va en el Excel y en el texto se muestran los valores impuros y la suma.
4. **Nivel 2, 3, …:** lo mismo para cada nodo impuro (R2).
5. Árbol resultante y reglas SI–ENTONCES; exactitud de re-sustitución.
6. Comentario (después del resultado): sesgo de ID3 y razón de ganancia, si eligen distinto (R1).
7. Comparación con R: raíz, criterio, tipo de corte, hojas, profundidad, clases que predice, exactitud, coincidencia de predicciones.

## Código para la entrega
`codigo/resolver.py` (copia de `resolver_arbol.py`, solo biblioteca estándar) y `codigo/script.R` (copia de `script_arbol.R`: ID3 en R base + rpart + ctree, todos con `Tipo ~ .`). No toques el algoritmo; solo el encabezado y los parámetros.

## Verificación (las cuatro del contrato)
1. Oráculo (`kit.py arbol-oraculo`): otro camino (E por conteos, ganancia cero exacta con enteros, recorrido en profundidad).
2. R: `comparar_r.py` compara E y ganancia de cada candidato de cada nodo contra el ID3 de R (tol 1e-9).
3. Caso de referencia: gastank (abajo).
4. Mutante calificado: `"excluir": ["Model Name"]` reproduce la respuesta del medio curso y el oráculo debe fallar en R1, R2 y hojas.
- T19: un atributo nominal con más de 30 niveles no entra como factor en `rpart` ni en `ctree`; `script.R` usa su código entero (orden alfabético) y escribe la tabla de códigos. **No** se quita el atributo.

## Respuesta
Raíz, árbol (reglas), hojas, profundidad, exactitud; comparación con los árboles de R en una tabla y un párrafo de coincidencias y diferencias.

## Casos de referencia comprobados
- **gastank** (`DL/gastank.csv`, 737 filas; MC problema 3). H = 1.5556. Nivel 1: E(Model Name) = 0.0227, E(Vent Type) = 0.7864, E(Fuel Type) = 1.0850 → Model Name (163 ramas, 3 impuras). Nivel 2: Shield → Vent Type (E 0.4349); Elite XL → Fuel Type (E 0.5572); Conquest → hoja Gas Storage (ganancia 0). Nivel 3: ambas ramas impuras con ganancia 0 → hojas. 165 hojas, profundidad 2, 733/737 = 99.46 %. Oráculo ✅ 6/6; ID3 de R = ID3 de Python en los 11 candidatos (tol 1e−9); Excel 44/44.
- **Comparación con R (gastank, todos los atributos; Model Name como código en R, T19):** ID3 165 hojas, profundidad 2, 99.46 %; `rpart` (Gini y entropía) raíz Vent Type, 11 hojas, profundidad 7, 92.81 %, coincide con ID3 en 93.22 % de las predicciones; `ctree` raíz Vent Type, 10 hojas, profundidad 5, 89.42 %, coincidencia 89.96 %, no predice GSI.
- **Mutante calificado** (sin Model Name): raíz Vent Type, 14 hojas (12 tras la poda trivial de la respuesta del MC, `MC/P3_gastank_Arbol/reporte_P3.txt` l.73). Oráculo ❌ en R1, R2, nodos y hojas.
