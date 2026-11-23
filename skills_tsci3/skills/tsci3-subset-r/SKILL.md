---
name: tsci3-subset-r
description: Tratamiento de datos en R con subsettings variados a partir de un objetivo de minería - perfil de columnas (constantes, duplicadas, faltantes, números con coma), plan de pasos en JSON que se ejecuta en Python y se traduce a R con los modismos de SUBSET.pdf (subset, df[, c()], índices negativos, which, %in%, grepl, complete.cases, reshape, cut, sample), bitácora de filas y columnas por paso comparada entre Python y R, vista minable. Úsala cuando pidan filtrar, limpiar, seleccionar columnas, "subset", "subsetting", "tratamiento de datos", "vista minable" o "en función de un objetivo de la minería" (TSCI3 AF1 Metro, Border Crossing, Set R; medio curso problema 2).
---

# Tratamiento de datos con subsettings variados

Lee antes `../tsci3-comun/references/reglas-academicas.md` y `../tsci3-comun/references/verificacion.md`.

`T=/Users/alexis/theCode/newSkills/TSCI3`; `SC=$T/skills_tsci3/skills/tsci3-subset-r/scripts`.

## Cuándo aplica
- AF1 Metro, Border Crossing y Set R: «Objetivo 30 / Subset + Resultado 50 / Referencias 20» (`OD/AD26 TSCI3 AF1.png`).
- Medio curso problema 2 (`EX-MC`): «Analice el registro …, proponga y realice (con subsettings variados) un tratamiento de datos en función de un objetivo de la minería». La respuesta aceptada (+15, sin observación) está en `RESP` p.7–11.
- No aplica: AF1 1.1, Proceso Minería y Obj WB/Datagov/datos gob (respuestas redactadas, sin cálculo).

## Estructura aceptada (`RESP` p.7–11) — síguela
1. **Análisis del registro:** tamaño, qué es cada fila, columnas y su significado; problemas de calidad del perfil (constantes, duplicadas, dispersas, códigos, faltantes y por qué faltan, tipos incorrectos, nombres con espacios, precisión).
2. **Objetivo de minería** (tarea, clase o variable de interés, unidad de análisis) **antes** de filtrar.
3. **Tratamiento:** bitácora con filas y columnas después de cada paso y el subsetting en R de cada uno. Variedad de subsettings: por columnas (índice negativo, `df[, c()]`, patrón), por filas (`subset`, `%in%`, `which`, `grepl`, `is.na`), por calidad, años comunes (`Reduce(intersect, split())`), `reshape`, `complete.cases`, `cut`, `sample` con semilla.
4. **Vista minable:** filas × atributos, sin faltantes, archivo CSV.
5. **Comprobación de que sirve al objetivo** (p. ej. un árbol `rpart` contra la clase mayoritaria).

## Semántica (igual en Python y R)
- Vacío o «NA» → NA (lista `na` del plan, como `na.strings`). Nombres con espacios se recortan (`trimws`).
- `filtrar` = `subset()`: se quedan las filas donde la condición es VERDADERA (NA se va).
- `excluir` = `d[-which(cond), ]`: se van solo las VERDADERAS (NA se queda). El script protege `-integer(0)`, que en R borraría todo.
- `muestra`: en Python solo cuentan los tamaños; el contenido depende del generador de R (T15).

## Ejecutar
1. `I=$T/incisos/<id>`; `mkdir -p $I/datos $I/codigo`; copia o enlaza el CSV en `$I/datos/`; `cp $SC/resolver_tratamiento.py $I/codigo/resolver.py`.
2. Escribe `$I/datos/plan.json` (empieza con `{"tipo": "perfil"}`; ejemplos: `$T/incisos/MC-P2/datos/plan.json`, `SUBSET-border`, `SUBSET-mta`, `SUBSET-ambx`). Pasos: `perfil, quitar_columnas, seleccionar, renombrar, numero, extraer, restar, filtrar (+select, estilo subset|corchetes), excluir, quitar_na, completos, comunes, pivotear, discretizar, muestra, guardar`; `desde` abre una rama desde un paso anterior.
3. `cd $I && python3 codigo/resolver.py --r codigo/script.R > salida_python.txt` → `traza.json`, `bitacora.csv`, `perfil_columnas.csv`, CSV guardados, `codigo/script.R`.
4. `Rscript codigo/script.R > salida_R.txt 2>&1` → `bitacora_R.csv`.
5. `python3 $SC/comparar_bitacoras.py $I [--esperada datos/bitacora_esperada.csv]` (✅ obligatorio).
6. Excel: `$T/.venv/bin/python $SC/excel_subset.py $I` y `$T/.venv/bin/python $T/skills_tsci3/skills/tsci3-comun/scripts/recalcular_excel.py $I/Demostración.xlsx` (todas «sí»).

## Verificación (contrato)
1. Independiente: R ejecuta el mismo plan con su propio motor (`subset`, `which`, `reshape`…) → bitácora R = bitácora Python.
2. Caso de referencia: bitácora de la respuesta aceptada (`RESP` p.7–8).
3. Mutante: cambiar `excluir` por `filtrar` en P5 (o `>` por `>=`) cambia las filas y la comparación falla.

## Casos de referencia comprobados (Python = R paso por paso)
- **export.csv (MC problema 2):** P0 118 580 × 33 → P1 13 col → P2 15 → P3 104 119 × 14 → P4 98 673 → P5 90 650 → P6 3 881 → P7 2 726 → P8 1 818 (años 2011, 2013, 2015, 2017, 2019, 2023) → P9 303 × 9 → P10 303 × 9; P11 1 113 × 5; clase 142 Baja / 113 Media / 48 Alta; P12 212 × 10, P13 91 × 10. Igual a `RESP` p.7–9 (14/14 pasos); R 19/19. Perfil: 6 constantes, YearEnd = YearStart, Data_Value_Alt = Data_Value, Sample_Size con comas, 14 461 Data_Value vacíos (T18).
- **Border Crossing (`OD/SUBSET.pdf` p.12–15):** Texas 41 946; Texas y Trucks 3 783; Arizona con select 22 091 × 2; distinto de Texas 352 920; Texas o Arizona 64 037; 500 ≤ Value ≤ 5000 76 446 (de 394 866).
- **MTA (p.16–17):** Off-Peak 90 157; y Cancelled 1 913; fecha > 2024-01-01, 10 < Minutes Late ≤ 20, Grand Central 374 (de 141 110).
- **ambx (p.5–9):** 29 filas; Ozone sin NA 23; Ozone y Solar.R completos 22; completos 21.
