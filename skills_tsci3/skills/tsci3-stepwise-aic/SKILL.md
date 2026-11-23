---
name: tsci3-stepwise-aic
description: Regresión stepwise con AIC en TSCI3 (OD/AM R.pdf p.20-24) - selección automática de variables hacia adelante, hacia atrás o bidireccional con stepAIC(full_model, direction = "both"), AIC = 2k − 2 ln L (menor es mejor), tabla de pasos con la variable que entra o sale y su AIC, modelo final - con oráculo exacto independiente de R, Excel con los candidatos de cada paso y script R. Úsala cuando pidan "stepwise", "stepAIC", "selección de variables", "forward/backward", "AIC" o "Boston" (TSCI3 AF4 Regresión Stepwise).
---

# Regresión stepwise con AIC

`T=/Users/alexis/theCode/newSkills/TSCI3`; `SC=$T/skills_tsci3/skills/tsci3-stepwise-aic/scripts`.

## Criterio de rúbrica
AF4 Regresión Stepwise (7): Ejercicio de clase 50 / Script R 50.

## Método (con cita)
- p.20: forward (modelo vacío, agrega), backward (modelo completo, quita), bidireccional (agrega y quita en cada paso).
- p.21-22: AIC = 2k − 2 ln L; k parámetros, L verosimilitud máxima; menor es mejor; solo compara modelos entre sí.
- p.23-24: `full_model <- lm(y ~ ., data)`, `stepAIC(full_model, direction = "both", trace = FALSE)`, `summary(step_model)`. T9: `library(MASSExtra)`; `stepAIC` es la de MASS.
- R usa `extractAIC` = n·ln(RSS/n) + 2k. Difiere del AIC de p.21 (que da `AIC()`) en la constante n(ln 2π + 1) + 2, así que el camino es el mismo. La traza muestra los dos.
- Reglas de `MASS::stepAIC` que el oráculo reproduce: (1) un término alias (Df = 0) se quita primero; (2) gana el cambio de menor AIC y, si el mejor es «<none>», se detiene; (3) se detiene si el AIC nuevo ≥ AIC anterior + 1e−7.

## Ejecutar
1. `I=$T/incisos/<id>`; CSV en `$I/datos/` (o `dataset: "Boston"`); `parametros.json`: `{"archivo", "y", "direccion"}` (ejemplos: `$T/incisos/SW-br`, `$T/incisos/SW-boston`).
2. R: `$SC/script_stepwise.R` → `$I/codigo/script.R` (cambia ARCHIVO, DATASET, Y, DIRECCION); `cd $I && Rscript codigo/script.R > salida_R.txt 2>&1`. Exporta `pasos_R.csv`, `final_R.csv`, `vecinos_R.csv` y `resumen_R.csv`.
3. Verificación: `python3 $SC/verificar_stepwise.py $I`. Debe dar ✅ en todo y escribe `traza.json`.
4. Excel: `$T/.venv/bin/python $SC/excel_stepwise.py $I` y luego `recalcular_excel.py`.

## Verificación
1. El oráculo (`kit_tsci3/tsci3/oraculos/stepwise.py`) calcula el RSS de cada candidato con fracciones exactas y trata los alias como `lm`.
2. R = Python: camino (cambio, gl, RSS, AIC), coeficientes finales y la vecindad de `drop1`/`add1`.
3. Óptimo local (p.20-22): ningún cambio de una sola variable baja el AIC del modelo final.
4. El AIC de p.21 (2k − 2 ln L, con k + 1 parámetros porque σ² cuenta) es igual a `AIC()` de R.
5. Mutante: sin la penalización 2k nunca se quita una variable, y el modelo final cambia.
6. Excel: AIC de cada candidato en fórmula, el mínimo marcado; en la hoja Final, LINEST recalcula coeficientes y RSS, y ln L y AIC están en fórmula.

## Casos de referencia comprobados
- **Boston** (p.23, n = 506): quita age (AIC 1589.64 → 1587.65) e indus (→ 1585.76). Final: 11 variables, AIC() = 3023.73, R² = 0.7406. Verificación 6/6; Excel 19/19.
- **BR (2).csv** (p.24, `precio ~ .`, n = 1000): quita condición (= código_condición − 1, alias con Df = 0), m2_terreno, pais_id, agente_id y vista; AIC 24 247.10 → 24 241.92. Final: 12 variables, R² = 0.6950. Verificación 6/6; Excel 23/23.
