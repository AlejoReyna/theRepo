---
name: tsci3-regularizacion
description: Regresión Lasso y Ridge en TSCI3 (OD/AM R.pdf p.29-32) - glmnet y cv.glmnet sobre model.matrix(precio ~ .), λ.min, coeficientes en λ.min (Lasso anula algunos, Ridge solo encoge), predicciones y MSE, con la discrepancia T3 (p.32 programa Ridge con alpha <- 1.0, que es Lasso) - con oráculo de descenso por coordenadas independiente de glmnet, Excel y script R. Úsala cuando pidan "Lasso", "Ridge", "regularización", "glmnet", "cv.glmnet" o "lambda.min" (TSCI3 AF4 Regresión Lasso y Regresión Ridge).
---

# Regresión Lasso y Ridge

`T=/Users/alexis/theCode/newSkills/TSCI3`; `SC=$T/skills_tsci3/skills/tsci3-regularizacion/scripts`.

## Criterio de rúbrica
AF4 Regresión Lasso (7) y Regresión Ridge (7): Ejercicio de clase 50 / Script R 50.

## Método (con cita)
- p.29: Lasso añade una penalización al tamaño de los coeficientes y puede llevar algunos exactamente a cero (selección de variables).
- p.30: `x <- model.matrix(precio ~ ., datos)[, -1]`, `glmnet(x, y, alpha = 1)`, `cv.glmnet`, `lambda.min`, `coef(modelo, s = mejor_lambda)`, `predict(newx = x)`, `MSE = mean((y − ŷ)²)`.
- p.31: Ridge «encoge» los coeficientes hacia cero. p.32 repite el código con `alpha <- 1.0`.
- **T3:** en glmnet, alpha = 1 es Lasso (p.30), así que el código literal de p.32 da Lasso. El script calcula las dos lecturas y entrega Ridge con alpha = 0, que es la que cumple p.31. En la entrega se declara la decisión.
- **T15:** `cv.glmnet` reparte los pliegues al azar. Se pone `set.seed(SEMILLA)` antes de cada `cv.glmnet` y se declara la semilla.
- Objetivo de glmnet (y en su escala, x estandarizada con 1/n): F = 1/(2n)·RSS + λ[α‖β‖₁ + (1 − α)/(2 s_y)‖β‖²]. glmnet estandariza y por dentro, y por eso aparece s_y en la parte L2.

## Ejecutar
1. `I=$T/incisos/<id>`; CSV numérico en `$I/datos/`; `parametros.json`: `{"archivo", "y", "semilla"}` (ejemplo: `$T/incisos/REG-br`).
2. R: `$SC/script_regularizacion.R` → `$I/codigo/script.R` (cambia ARCHIVO, SEMILLA y la respuesta si no es precio); `cd $I && Rscript codigo/script.R > salida_R.txt 2>&1`. Exporta `coef_R.csv`, `predicciones_R.csv` y `resumen_R.csv`.
3. Verificación: `python3 $SC/verificar_regularizacion.py $I`. Debe dar ✅ en todo y escribe `traza.json`.
4. Excel: `$T/.venv/bin/python $SC/excel_regularizacion.py $I` y luego `recalcular_excel.py`.

## Verificación
1. Python recalcula ŷ con los coeficientes de R y obtiene el MSE con las predicciones exportadas.
2. El oráculo (`kit_tsci3/tsci3/oraculos/regularizacion.py`) hace descenso por coordenadas hasta 1e−13 con el mismo λ.min. Su F queda ≤ la de glmnet (diferencia relativa < 1e−6) y los valores ajustados son los mismos (< 5e−3·s_y). glmnet se detiene con su propia tolerancia, así que los coeficientes coinciden a unas 3 cifras, no a 9.
3. Lasso anula al menos un coeficiente (p.29) y Ridge con alpha = 0 no anula ninguno (p.31). La lectura literal de p.32 da los mismos coeficientes que Lasso (T3).
4. Mutante: Ridge sin s_y en la penalización da otro modelo, y se detecta.
5. Excel: conteo de ceros, la fila 1 sustituida a mano y MSE = SUMXMY2/n, todo en fórmula.

## Casos de referencia comprobados
- **BR (2).csv** (`precio ~ .`, n = 1000, semilla 1851265):
  - Lasso: λ.min = 2194.68, MSE = 3.29195e10, ceros en m2_terreno, vista y condición.
  - Ridge con alpha = 0: λ.min = 22 991.82, MSE = 3.33195e10, sin ceros.
  - Ridge literal: igual que Lasso (T3).
  - condición = código_condición − 1, así que en Lasso el reparto entre las dos no es único. R anula condición y el oráculo reparte el efecto, pero la suma y los ŷ son los mismos.
  - Verificación 9/9; Excel 9/9.
