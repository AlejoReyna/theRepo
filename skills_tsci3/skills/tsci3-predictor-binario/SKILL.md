---
name: tsci3-predictor-binario
description: Regresión lineal simple con un predictor binario (variable ficticia 0/1) en TSCI3 (OD/AM R.pdf p.10-12) - b0 = media del grupo 0, b1 = diferencia de medias con las fórmulas de mínimos cuadrados, t con varianzas iguales (t.test var.equal = TRUE) y cambio de referencia con factor() - con Excel, script R y verificación. Úsala cuando pidan "predictor binario", "variable ficticia", "dummy", lm(mpg ~ am) o comparar dos grupos con regresión (TSCI3 AF4 Regresión lineal simple con predictor binario).
---

# Regresión con predictor binario

`T=/Users/alexis/theCode/newSkills/TSCI3`; `SC=$T/skills_tsci3/skills/tsci3-predictor-binario/scripts`. Usa la recta de `tsci3-minimos-cuadrados`.

## Criterio de rúbrica
AF4 Regresión lineal simple con predictor binario (7): Ejercicio de clase 50 / Script R 50.

## Método (con cita)
- Yᵢ = β0 + β1Xᵢ + εᵢ con Xᵢ ficticia 0/1 (`OD/AM R.pdf` p.10). Con las fórmulas de p.4 sobre x ∈ {0, 1}: β0 = media del grupo 0, β1 = diferencia de medias.
- R: `lm(mpg ~ am, data = mtcars)`, `summary`, `t.test(mpg ~ am, var.equal = TRUE)` (p.11); `factor(automatic)` cambia la referencia y el signo de β1 (p.12). `t.test` resta los grupos en el otro orden: misma |t| y mismo p.

## Ejecutar
1. `I=$T/incisos/<id>`; CSV con X en 0/1 (codifica antes si no lo está); `parametros.json`: `{"archivo", "x", "y"}`.
2. `cp $SC/resolver_binario.py $I/codigo/resolver.py && (cd $I && python3 codigo/resolver.py)`.
3. R: `$SC/script_binario.R` → `$I/codigo/script.R`; `Rscript codigo/script.R > salida_R.txt 2>&1`; `python3 $T/skills_tsci3/skills/tsci3-comun/scripts/comparar_traza_r.py $I binario_R.csv` (✅).
4. Excel: `$T/.venv/bin/python $SC/excel_binario.py $I` y `recalcular_excel.py`.

## Verificación
1. Exactitud: el programa comprueba en fracciones que β0 = media0 y β1 = media1 − media0.
2. R: β0, β1, SE, t, p, R² y los coeficientes con `factor(automatic)` = Python (8/8); |t| y p de `t.test` iguales.
3. Caso: `mtcars` (p.11).
4. Mutante: invertir la codificación 0/1 cambia el signo de β1 y β0 = media1 (lo muestra la versión con factor).

## Casos de referencia comprobados
- **mtcars**: n0 = 19 (media 17.147368), n1 = 13 (media 24.392308); β0 = 17.147368, β1 = 7.244939; t = 4.1061 con 30 gl, p = 0.000285; R² = 0.3598; con `factor(automatic)`: 24.392308 y −7.244939. R = Python 8/8; Excel 7/7.
