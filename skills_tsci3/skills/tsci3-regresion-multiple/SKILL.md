---
name: tsci3-regresion-multiple
description: Regresión lineal múltiple y con predictor no binario (factores) en TSCI3 (OD/AM R.pdf p.13-19, 25-28, 33-35) - lm con varios predictores, summary, predict con datos nuevos, entrenamiento 80 % / prueba 20 % con MSE, MAE y R², as.factor para predictores categóricos (ficticias = niveles − 1, alias como NA) - con Excel matricial (β = (XᵀX)⁻¹Xᵀy), script R y verificación exacta. Úsala cuando pidan "regresión múltiple", "kitchen sink", "predecir con datos nuevos", "predictor no binario", "variable categórica" o "as.factor" (TSCI3 AF4 Regresión múltiple y Regresión con predictor no binario).
---

# Regresión múltiple y predictor no binario

`T=/Users/alexis/theCode/newSkills/TSCI3`; `SC=$T/skills_tsci3/skills/tsci3-regresion-multiple/scripts`.

## Criterio de rúbrica
AF4 Regresión múltiple (10) y Regresión con predictor no binario (6): Ejercicio de clase 50 / Script R 50.

## Método (con cita)
- Ŷ = β0 + β1X1 + … + βnXn (`OD/AM R.pdf` p.14-15); preparación, selección, división, MSE, MAE y R² (p.17-19, p.25-27).
- R (p.28): `lm(precio ~ tcons + recamaras + condicion)`, `summary`, `predict(model, new_data)` con (130, 3, 4).
- Predictor no binario (p.34-35): `as.factor(condicion)`, `as.factor(recamaras)`; R crea niveles − 1 ficticias; una ficticia colineal queda NA (alias).
- T10: en `OD/BR (2).csv` los nombres son m2_construcción (tcons), condición, m2_terreno (tterreno), baños (numban). T15: la división 80/20 lleva semilla declarada.

## Ejecutar
1. `I=$T/incisos/<id>`; CSV en `$I/datos/`; `parametros.json`: `{"archivo", "y", "predictores", "nuevos", "predictores_factor", "factores"}` (ejemplo: `$T/incisos/RM-br`).
2. R: `$SC/script_multiple.R` → `$I/codigo/script.R` (ajusta nombres de columnas); `Rscript codigo/script.R > salida_R.txt 2>&1`.
3. Verificación: `python3 $SC/verificar_multiple.py $I` (✅; escribe `traza.json`).
4. Excel: `$T/.venv/bin/python $SC/excel_multiple.py $I` y `recalcular_excel.py`.

## Verificación
1. Python (`kit_tsci3/tsci3/regresion.py`): ecuaciones normales con fracciones exactas; alias como `lm`.
2. R = Python: coeficientes, predicción, ŷ de prueba con el mismo entrenamiento, MSE/MAE/R², coeficientes con factores y número de ficticias.
3. Excel: β por MMULT/MINVERSE y por LINEST, predicción sustituida y métricas de prueba = Python.
4. Mutante: olvidar `as.factor` deja un solo coeficiente por variable (la comprobación de ficticias falla).

## Casos de referencia comprobados
- **BR (2).csv** (1000): precio = −35 820.21 + 995.98·m2_construcción − 52 060.63·recamaras + 46 915.93·condición (R² = 0.5095); predicción (130, 3, 4) = 125 139.16; prueba (semilla 1851265): MSE = 5.828e10, MAE = 164 086.50, R² = 0.4726. Con factores: 16 coeficientes, 12 ficticias, `recamaras9` alias (NA). Verificación 5/5; Excel 12/12.
