---
name: tsci3-apriori
description: Reglas de asociación con Apriori en TSCI3 - soporte S = NX∧Y/N, confianza C = NX∧Y/NX y lift L = NX∧Y·N/(NX·NY) con el formato del ejercicio de clase (OD/AP (1).xlsx), itemsets frecuentes por niveles con cierre descendente, reglas con los umbrales del curso (soporte 0.01, confianza 0.1) igual que arules, composición «R1 THEN R2», y el script del curso con arules. Deja Excel con fórmulas, programa en Python, script R y verificación. Úsala cuando pidan "reglas de asociación", "Apriori", "soporte", "confianza", "lift", "IF X THEN Y" o "canasta" (TSCI3 AF3 A priori).
---

# Apriori (ejercicio de clase + arules)

Lee antes `../tsci3-comun/references/reglas-academicas.md` y `../tsci3-comun/references/verificacion.md`.
`T=/Users/alexis/theCode/newSkills/TSCI3`; `SC=$T/skills_tsci3/skills/tsci3-apriori/scripts`.

## Criterio de rúbrica
AF3 A priori (20): 35/50/15/15 (`OD/AD26 TSCI3 AF3.png`).

## Método (con cita)
- S = NX∧Y/N, C = NX∧Y/NX, L = NX∧Y·N/(NX·NY) (`OD/AP (1).xlsx` M4:O11); la tabla «IF X THEN Y» con N, NX, NY, NX∧Y (I2:O11) y la composición «R1 THEN R2» = IF X THEN (Y1 AND Y2) (H24:K25).
- Dos etapas: itemsets frecuentes por niveles con cierre descendente y reglas con confianza mínima (`EJ26-24` p.6). Una hoja por nivel (R2).
- Umbrales del curso: soporte 0.01, confianza 0.1 (`OD/arules R (2).txt`). Ejemplo de la literatura: 0.1, 0.5 y lift 1 (`EJ26-24` p.10). Usa los del enunciado si los da.
- Igual que `arules::apriori`: ítems «columna=valor», consecuente de un ítem, `maxlen` 10, reglas {} ⇒ {Y} incluidas. Las columnas numéricas se discretizan o se quitan antes (el programa se detiene si encuentra una).
- T22: las celdas vacías y «NA» no son ítems (`na.strings = c("", "NA")`). Con el script del curso tal cual, `apri poko.csv` se queda sin memoria. T8: los multiplicadores de M17:M21 no tienen explicación y no se usan.

## Ejecutar
1. `I=$T/incisos/<id>`; `$I/datos/parametros.json`: `{"archivo": "x.csv", "columnas": [...], "soporte": 0.01, "confianza": 0.1, "reglas_pedidas": [{"si": ["A=x"], "entonces": "B=y"}], "composicion": [{"si": [...], "entonces": [..., ...]}]}`.
2. `cp $SC/resolver_apriori.py $I/codigo/resolver.py && (cd $I && python3 codigo/resolver.py > salida_python.txt)` → `traza.json`, `reglas_python.csv`.
3. Oráculo: `python3 $T/kit_tsci3/kit.py apriori-oraculo $I/datos/x.csv $I/traza.json` (✅).
4. R: `$SC/script_apriori.R` → `$I/codigo/script.R` (ARCHIVO, COLUMNAS, umbrales); `Rscript codigo/script.R > salida_R.txt 2>&1`; `python3 $SC/comparar_r.py $I` (✅ regla por regla).
5. Excel: `$T/.venv/bin/python $SC/excel_apriori.py $I` y `recalcular_excel.py` (todas «sí»).

## Verificación
1. Oráculo: cuenta cada subconjunto de cada transacción (sin unir por niveles) y rearma todas las reglas.
2. R: `association_rules.csv` de arules = `reglas_python.csv` en soporte, confianza, cobertura, lift y conteo.
3. Caso de referencia: J4:O11 de `OD/AP (1).xlsx` (`kit_tsci3/pruebas/test_apriori.py`).
4. Mutante: NX·NY en el numerador del lift no reproduce O4 (en la misma prueba).

## Casos de referencia comprobados
- **AP (1).xlsx** (50 registros; HeartDisease, Smoking, AlcoholDrinking, Stroke): las 8 reglas de I4:I11 con NX/NY/NX∧Y = 44/25/24, 44/25/20, 25/44/24, 25/6/1, 6/25/1, 6/25/5, 25/44/20, 25/6/5 y S, C, L de M:O. Niveles 8, 22, 24, 9; 136 reglas (6 con antecedente vacío). Oráculo ✅; R = Python 136/136; Excel 88/88.
- **apri poko.csv** (50 objetos, 88 ítems): niveles 88, 488, 1081, 1328, 1027, 521, 172, 34, 3; 18 686 reglas (16 con antecedente vacío). Oráculo ✅; R = Python 18 686/18 686; Excel 69/69.
