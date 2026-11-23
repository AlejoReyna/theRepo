---
name: tsci3-breusch-pagan
description: Prueba de Breusch-Pagan de heterocedasticidad en TSCI3 (OD/AM R.pdf p.7-9) - H0 homocedasticidad, HA heterocedasticidad, estadístico χ² con tantos gl como predictores, rechazo si p < 0.05 - con bptest (lmtest) en R, Excel con la regresión auxiliar n·R² y CHISQ.DIST.RT, y verificación. Úsala cuando pidan "Breusch-Pagan", "bptest", "heterocedasticidad" u "homocedasticidad" de un modelo lm (TSCI3 AF4 Prueba de Breusch-Pagan).
---

# Prueba de Breusch-Pagan

`T=/Users/alexis/theCode/newSkills/TSCI3`; `SC=$T/skills_tsci3/skills/tsci3-breusch-pagan/scripts`. Toma el modelo de `tsci3-minimos-cuadrados` o `tsci3-regresion-multiple`.

## Criterio de rúbrica
AF4 Prueba de Breusch-Pagan (6): Ejercicio de clase 50 / Script R 50.

## Método (con cita) — estado VL
- H0: homocedasticidad; HA: heterocedasticidad; χ² con p gl (p = número de predictores); se rechaza H0 si p < α = 0.05 (`OD/AM R.pdf` p.8).
- R: `bptest(modelo)` (p.9); `bptest` es de `lmtest`, que la lámina no carga: el script lo carga.
- Las láminas no dan la fórmula del estadístico. Como contraste adicional (fuera de las fuentes), Python y el Excel recalculan la forma studentizada de Koenker, la que usa `bptest` por omisión: BP = n·R² de la regresión de e² sobre los mismos predictores.

## Ejecutar
1. `I=$T/incisos/<id>`; datos en `$I/datos/`; edita los modelos en `$SC/script_bp.R` (copia a `$I/codigo/script.R`), `verificar_bp.py` y `excel_bp.py` (lista MODELOS).
2. `Rscript codigo/script.R > salida_R.txt 2>&1` → `bp_R.csv`.
3. `python3 $SC/verificar_bp.py $I` (✅) y `$T/.venv/bin/python $SC/excel_bp.py $I` + `recalcular_excel.py`.

## Verificación
gl = número de predictores; p = P(χ²(gl) > BP) con `kit_tsci3/tsci3/estadistica.py`; decisión coherente con p < α; BP de Koenker recalculado (Python exacto y Excel con LINEST) = R.

## Casos de referencia comprobados
- **old.csv**, waiting ~ eruptions: BP = 0.004119, 1 gl, p = 0.9488 → no se rechaza H0 (homocedasticidad).
- **BR (2).csv**, precio ~ m2_construcción + recamaras + condición: BP = 106.42, 3 gl, p = 6.47e−23 → se rechaza H0 (heterocedasticidad). Verificación 8/8; Excel 4/4.
