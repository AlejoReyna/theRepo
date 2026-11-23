---
name: tsci3-bosque-aleatorio
description: Bosque aleatorio de regresión en TSCI3 (OD/AM R.pdf p.54-55) - randomForest(ntree = 100, importance = TRUE) para precio con set.seed(42) y división 80/20, muestreo con reemplazo, subconjunto aleatorio de variables por nodo (mtry), predicción = promedio de los árboles, RMSE, MAE y R² en prueba, importancia de variables (varImpPlot) - con oráculo que recorre cada árbol con getTree, comprueba hojas e IncNodePurity con la muestra bootstrap, Excel con el bootstrap y el promedio de los árboles, y script R. Úsala cuando pidan "bosque aleatorio", "random forest", "randomForest", "varImpPlot", "importancia de variables" o "ntree" (TSCI3 AF4 Bosques aleatorios).
---

# Bosque aleatorio

`T=/Users/alexis/theCode/newSkills/TSCI3`; `SC=$T/skills_tsci3/skills/tsci3-bosque-aleatorio/scripts`.

## Criterio de rúbrica
AF4 Bosques aleatorios (10): Ejercicio de clase 50 / Script R 50.

## Método (con cita)
- p.54: muestras aleatorias con reemplazo, un árbol por muestra y un subconjunto aleatorio de variables en cada nodo. En regresión, la predicción es el promedio de los árboles.
- p.55 (código tal cual):
  - `X <- df[, !(colnames(df) %in% 'precio')]`, `set.seed(42)`, `sample(nrow(df), 0.8·n)`;
  - `randomForest(x = X_train, y = y_train, ntree = 100, importance = TRUE)`;
  - RMSE, MAE y R² en prueba, y `varImpPlot(model)`.
- Agregados para verificar: `keep.inbag = TRUE`, `predict.all = TRUE` y `getTree`. Ninguno consume números aleatorios, así que el resultado no cambia (el script lo comprueba con `identical`).
- mtry = ⌊p/3⌋ es el valor por omisión en regresión. Con las 17 columnas de BR da 5.
- **T15:** la semilla 42 fija la división y el bosque.
- **T26:** `read.csv` de R lee algunos decimales de 17 cifras a 1 ulp del redondeo correcto. En BR son 245 valores. El oráculo usa los doubles de R (`X_R.csv`, escrito con `%.17g`).
- **T27:** cuando un nodo tiene todas sus y iguales, randomForest igual registra una división con un corte sin sentido (por ejemplo, año_construcción ≤ 0). La rama vacía queda con una predicción sobrante. Ningún dato real llega ahí, pero conviene mencionarlo si se explica un árbol con `getTree`.

## Ejecutar
1. `I=$T/incisos/<id>`; CSV en `$I/datos/`; `parametros.json`: `{"archivo", "y", "ntree", "observacion_excel"}` (ejemplo: `$T/incisos/RF-br`).
2. R: copia `$SC/script_bosque.R` a `$I/codigo/script.R` y corre `cd $I && Rscript codigo/script.R > salida_R.txt 2>&1`. Exporta índices, predicciones con las de cada árbol, inbag, `arboles_R.csv` (getTree), importancia, `X_R.csv` y `varImpPlot.pdf`.
3. Verificación: `python3 $SC/verificar_bosque.py $I`. Debe dar ✅ en todo y escribe `traza.json`.
4. Excel: `$T/.venv/bin/python $SC/excel_bosque.py $I` y luego `recalcular_excel.py`.

## Verificación
1. División 80/20 sin filas en común. Cada árbol tiene una muestra con reemplazo de tamaño n, con cerca de 36.8 % de filas fuera de la bolsa. mtry = ⌊p/3⌋.
2. El oráculo (`kit_tsci3/tsci3/oraculos/bosque.py`) recorre los 100 árboles para cada observación de prueba (x ≤ corte → izquierda) y debe llegar a la hoja que predice R. La predicción del bosque debe ser el promedio de los árboles.
3. Cada hoja debe predecir el promedio de y de su muestra bootstrap, con repeticiones; la excepción son las ramas vacías de T27. IncNodePurity se recalcula como Σ ΔRSS / ntree.
4. RMSE, MAE y R² se recalculan con y_test y y_pred. Con la misma semilla, R debe dar lo mismo.
5. Mutante: usar la mediana de los árboles en lugar del promedio cambia el RMSE, y se detecta.
6. Excel: tamaño, filas fuera de la bolsa y repetidas del árbol 1; AVERAGE de los 100 árboles; RMSE, MAE y R² en fórmula; orden de importancia con RANK.

## Casos de referencia comprobados
- **BR (2).csv** (`precio ~` las otras 17 columnas; 800 de entrenamiento y 200 de prueba):
  - RMSE = 153 636.66, MAE = 89 096.29 y R² = 0.7534; mtry = 5; 36.9 % fuera de la bolsa.
  - %IncMSE más alto: latitud (24.8), m2_construcción (14.2) y código_postal (8.6).
  - IncNodePurity más alta: m2_construcción, baños y latitud.
  - Los 20 000 recorridos coinciden con R; 26 916 hojas, 18 de ellas ramas vacías (T27).
  - Verificación 10/10; Excel 5/5.
