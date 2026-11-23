---
name: tsci3-knn
description: K vecinos más cercanos y determinación de k en TSCI3 (OD/AM R.pdf p.43-48, p.51-53) - class::knn con categoria_precio (alto si precio ≥ mediana), set.seed(42), 75 % de entrenamiento, k = 3, distancia euclidiana sin normalizar (T5), voto por mayoría con empates (T15), matriz de confusión (S15), k por validación cruzada de 10 pliegues con caret::train(method = "knn") sobre k = 1, 3, …, 15, y WCSS con método del codo para k desconocido - con oráculo que recalcula cada predicción y cada pliegue, Excel con distancias, vecinos y voto, y script R. Úsala cuando pidan "KNN", "k vecinos", "vecinos más cercanos", "elegir k", "validación cruzada" o "codo/WCSS" para KNN (TSCI3 AF4 KNN y Determinación de k para KNN).
---

# KNN y determinación de k

`T=/Users/alexis/theCode/newSkills/TSCI3`; `SC=$T/skills_tsci3/skills/tsci3-knn/scripts`.

## Criterio de rúbrica
AF4 KNN (10) y Determinación de k para KNN (6): Ejercicio de clase 50 / Script R 50.

## Método (con cita)
- p.44: un punto nuevo se clasifica por los k puntos más cercanos en el espacio de características. La distancia es la euclidiana (AD25-12 p.2; AD25-03 p.2).
- p.48 (código tal cual): `categoria_precio <- ifelse(precio >= mediana, 'alto', 'bajo')`; columnas recamaras, baños, m2_construcción, m2_terreno, pisos y condición; `set.seed(42)`; `sample(…, 0.75·n)`; `knn(k = 3)`. No normaliza (T5) y m2_terreno domina la distancia; la entrega lo dice.
- p.49-50: la matriz de confusión se hace con **tsci3-matriz-confusion** (T24).
- p.51-53: validación cruzada de 10 pliegues con `train(method = "knn", tuneGrid = k = seq(1, 15, 2))`. El mejor k es el de mayor exactitud media.
- p.45-47: para k desconocido, WCSS = Σ‖x − μ‖² y codo. El script corre kmeans con nstart = 10 y semilla 42, y toma el codo como la máxima segunda diferencia (criterio declarado).
- **T15:** R desempata los votos al azar. Además, con k ≥ 2, class::knn y knn3 meten en el voto a los puntos con distancia² ≤ dₖ²·(1 + 1e−4). Esto se midió y está en el oráculo.

## Ejecutar
1. `I=$T/incisos/<id>`; CSV en `$I/datos/`; `parametros.json`: `{"archivo", "columnas", "k", "k_valores", "punto_excel"}` (ejemplo: `$T/incisos/KNN-br`).
2. R: `$SC/script_knn.R` → `$I/codigo/script.R`; `cd $I && Rscript codigo/script.R > salida_R.txt 2>&1`. Exporta los índices de entrenamiento, las predicciones, las predicciones de cada pliegue y cada k (`savePredictions = "all"`, que no consume números aleatorios), el WCSS y sus grupos, y la gráfica `k_vs_exactitud.pdf`.
3. Verificación: `python3 $SC/verificar_knn.py $I`. Debe dar ✅ en todo y escribe `traza.json`.
4. Excel: `$T/.venv/bin/python $SC/excel_knn.py $I` y luego `recalcular_excel.py`.
5. Matriz de confusión: copia `predicciones_R.csv` (fila, real, pred) a un inciso de **tsci3-matriz-confusion** con origen `csv` (ejemplo: `$T/incisos/CM-knn-br`).

## Verificación
1. `set.seed(42)` no se puede reproducir en Python. Por eso el oráculo (`kit_tsci3/tsci3/oraculos/knn.py`) usa los índices y pliegues que exporta R, y con ellos recalcula distancias, vecinos y voto.
2. Las 250 predicciones de prueba deben ser iguales a R, y los empates de votos se listan. La exactitud debe ser igual a la de caret.
3. En la validación cruzada se revisa cada predicción de cada pliegue para cada k, y la exactitud media debe ser igual a la de caret. El mejor k también.
4. El WCSS se recalcula con los grupos de R.
5. Mutante: con normalización min-max (T5) cambian 84 de 250 predicciones, y se detecta.
6. Excel: SQRT(SUMXMY2) a los 750 puntos de entrenamiento; los vecinos con SMALL/MATCH, el voto con COUNTIF y la revisión del empate en la frontera; el mejor k con MAX/INDEX y el codo con segundas diferencias.

## Casos de referencia comprobados
- **BR (2).csv:** mediana 443 750, con 500 altos; 750 de entrenamiento y 250 de prueba.
  - k = 3: exactitud 0.656 (TP 83, FN 43, FP 43, TN 81), sin empates.
  - Fila 5: vecinos 592, 256 y 668, todos «alto», a 85.50, 148.78 y 168.23.
  - Validación cruzada: k = 1 → 0.6346 … k = 13 → 0.7185 (el mejor), k = 15 → 0.7159. Hay 2 empates de votos en los pliegues; el de Fold07 con k = 3 sale por la tolerancia 1e−4.
  - WCSS: el codo está en k = 2.
  - Verificación 7/7; Excel 11/11.
