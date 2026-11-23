---
name: tsci3-matriz-confusion
description: Matriz de confusión en TSCI3 (OD/AM R.pdf p.49-50; AD25-11 p.9; AD25-03 p.3, p.11) - tabla 2×2 con la clase real en las filas y la predicha en las columnas, márgenes p, n, p′, n′, N, exactitud = Σdiagonal/N, precisión, recall, especificidad, F1 y kappa, caret::confusionMatrix y byClass, con la discrepancia T24 (p.50 pasa la tabla a caret al revés y Sensitivity sale como precisión), revisión de consistencia de tablas publicadas (T4) y reconstrucción de tablas a partir de métricas reportadas - con Excel y script R. Úsala cuando pidan "matriz de confusión", "accuracy/exactitud", "precisión", "recall", "sensibilidad", "confusionMatrix" o evaluar un clasificador; la usan también S14, S16 y S17 (TSCI3 AF4 Matriz de confusión).
---

# Matriz de confusión

`T=/Users/alexis/theCode/newSkills/TSCI3`; `SC=$T/skills_tsci3/skills/tsci3-matriz-confusion/scripts`.

## Criterio de rúbrica
AF4 Matriz de confusión (6): Ejercicio de clase 50 / Script R 50.

## Método (con cita)
- p.49: tp, fn, fp, tn; la clase real va en las filas.
- p.50: `confusionMatrix(table(real, Prediccion))`, `cm$table`, `cm$byClass` y `accuracy = sum(diag(cm$table)) / sum(cm$table)`.
- Precisión = TP/(TP + FP) y recall = TP/(TP + FN), según AD25-03 p.3 y AD25-11 p.9.
- **T24:** caret lee las filas como predicción, así que la llamada literal de p.50 intercambia Sensitivity (recall) con Pos Pred Value (precisión). El script imprime la salida literal y entrega `confusionMatrix(t(tabla))`. La entrega debe decirlo.
- **T4:** AD25-03 p.3 pone la predicción en las filas, al revés que p.49. AD25-11 p.9 no cuadra; ver el caso abajo.
- La clase positiva se declara: en el KNN de p.48 es «alto», que también es el primer nivel en orden alfabético, el que caret toma por omisión.

## Ejecutar
1. `I=$T/incisos/<id>`. `parametros.json` según el origen:
   - `csv`: `datos/clases.csv` (real, pred) y `positiva`;
   - `tabla`: TP, FN, FP, TN, `N_declarado`, `reportado` y `tabla_publicada`;
   - `reconstruir`: N, métricas reportadas, decimales y `predichos_positivos`.
   Hay un ejemplo de cada uno en `$T/incisos/CM-knn-br`, `CM-ad25-11` y `CM-ad25-03`.
2. R (no aplica a `reconstruir`): copia `$SC/script_matriz.R` a `$I/codigo/script.R` y ajusta ORIGEN, POSITIVA y TABLA. Con ORIGEN = `knn_p48` reproduce p.48 tal cual y escribe `clases.csv`. Corre `cd $I && Rscript codigo/script.R > salida_R.txt 2>&1`.
3. Verificación: `python3 $SC/verificar_matriz.py $I`. Debe dar ✅ en todo y escribe `traza.json`.
4. Excel: `$T/.venv/bin/python $SC/excel_matriz.py $I` y luego `recalcular_excel.py`.

## Verificación
1. El oráculo cuenta la tabla y calcula las métricas con fracciones exactas. Los márgenes deben cumplir p + n = p′ + n′ = N.
2. Debe dar lo mismo que caret con la orientación correcta. Además se comprueba T24: la salida literal de p.50 da Sensitivity = precisión y PPV = recall.
3. Artículos: se revisa N contra el N declarado, la tabla publicada contra la tabla de las fórmulas y si cada cifra reportada es un redondeo o un truncamiento del valor exacto.
4. Mutante: leer como p.49 una tabla con la predicción en las filas (AD25-03 p.3) cambia el recall. Si FN = FP, el mutante no aplica y se reporta así.
5. Excel: en el caso csv, la tabla sale de COUNTIFS sobre las clases. Márgenes y métricas van en fórmula.

## Casos de referencia comprobados
- **KNN de p.48** (BR, semilla 42, k = 3, 250 de prueba): TP 83, FN 43, FP 43, TN 81. Exactitud 0.656, kappa 0.3120; precisión = recall = 0.6587. Como FN = FP, T24 no cambia las cifras aquí. Verificación 4/4; Excel 11/11.
- **AD25-11 p.9** (T4): las fórmulas usan TP 45, FN 12, FP 0, TN 26, que suman N = 83.
  - Hallazgos: el artículo declara 87 datos de prueba y la tabla publicada pone TP = 55 y suma 93.
  - Exactitud exacta 0.855422, reportada como 85 % (truncada). Recall 0.789474, reportado como 78.94 % (truncado).
  - Con la llamada literal de p.50, caret daría Sensitivity 1.
  - Verificación 6/6; Excel 7/7.
- **AD25-03 p.11:** CA = precisión = recall = F1 = 0.917 con N = 60 es compatible con 14 tablas. Si las 27 predicciones «superior» son de los mismos datos, la tabla es única: TP 25, FN 3, FP 2, TN 30 (hipótesis declarada). El recall ponderado siempre es igual a CA. Verificación 3/3; Excel 14/14.
