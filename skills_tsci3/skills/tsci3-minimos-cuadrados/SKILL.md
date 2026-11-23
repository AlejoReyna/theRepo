---
name: tsci3-minimos-cuadrados
description: Recta de mínimos cuadrados en TSCI3 (OD/AM R.pdf p.3-6) - m = (NΣxy − ΣxΣy)/(NΣx² − (Σx)²), b = (Σy − mΣx)/N, residuos, RSS y MSE = RSS/n - con Excel de sumas y fórmulas vivas, gráfica, lm/summary/abline en R y verificación exacta en fracciones. Úsala cuando pidan "mínimos cuadrados", "recta de regresión", "regresión lineal simple", "RSS", "MSE" o lm(y ~ x) (TSCI3 AF4 Mínimos cuadrados).
---

# Mínimos cuadrados

Lee antes `../tsci3-comun/references/verificacion.md`. `T=/Users/alexis/theCode/newSkills/TSCI3`; `SC=$T/skills_tsci3/skills/tsci3-minimos-cuadrados/scripts`.

## Criterio de rúbrica
AF4 Mínimos cuadrados (6): Ejercicio de clase 50 (Excel) / Script R 50 (`OD/AD26 TSCI3 AF4.png`).

## Método (con cita)
- m = (NΣxy − ΣxΣy)/(NΣx² − (Σx)²); b = (Σy − mΣx)/N (`OD/AM R.pdf` p.4, leído en la imagen).
- e = y − ŷ; RSS = Σe²; MSE = RSS/n (p.5).
- R: `lm(data$waiting ~ data$eruptions, data = data)`, `summary`, `abline` (p.6).

## Ejecutar
1. `I=$T/incisos/<id>`; CSV en `$I/datos/`; `parametros.json`: `{"archivo": "x.csv", "x": "…", "y": "…"}`.
2. `cp $SC/resolver_minimos.py $I/codigo/resolver.py && (cd $I && python3 codigo/resolver.py > salida_python.txt)` (fracciones exactas).
3. Oráculo: `python3 $T/kit_tsci3/kit.py minimos-oraculo $I/datos/x.csv $I/traza.json` (✅).
4. R: `$SC/script_minimos.R` → `$I/codigo/script.R` (ARCHIVO y columnas); `Rscript codigo/script.R > salida_R.txt 2>&1`; `python3 $T/skills_tsci3/skills/tsci3-comun/scripts/comparar_traza_r.py $I minimos_R.csv` (✅ 12 cifras).
5. Excel: `$T/.venv/bin/python $SC/excel_minimos.py $I` y `recalcular_excel.py`.

## Verificación
1. Oráculo: forma centrada Sxy/Sxx en fracciones (m idéntica como fracción).
2. R: b, m, SE, t, p, R², R² ajustado, F, σ, RSS y MSE = Python a 1e−9.
3. Caso: `OD/old.csv`.
4. Mutante: (Σx)² en lugar de Σx² (el oráculo lo comprueba).

## Casos de referencia comprobados
- **old.csv** (272): Σx = 948.677, Σy = 19 284, Σxy = 71 046.395, Σx² = 3661.818975; m = 10.7296414, b = 33.4743970; RSS = 9443.387, MSE = 34.718335, R² = 0.811461; t(b1) = 34.089, p = 8.13e−100, F = 1162.06 con 1 y 270 gl. R = Python (12/12); oráculo 4/4; Excel 7/7.
