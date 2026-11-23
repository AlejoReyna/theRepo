---
name: tsci3-secuencias
description: Patrones secuenciales en TSCI3 con cspade (OD/SEQMIN.R) - lectura SPMF (-1 cierra evento, -2 cierra secuencia), patrones de hasta maxlen elementos con hasta maxsize ítems, soporte = secuencias que contienen el patrón / secuencias - con Excel de conteo y cociente (fórmulas COUNTIF), descomposición a mano de una secuencia, programa en Python, script R y verificación. Úsala cuando pidan "patrones secuenciales", "secuencias", "cspade", "SPADE", "sequence mining" o "SEQMIN" (TSCI3 AF3 Secuencias).
---

# Patrones secuenciales (cspade)

Lee antes `../tsci3-comun/references/reglas-academicas.md` y `../tsci3-comun/references/verificacion.md`.
`T=/Users/alexis/theCode/newSkills/TSCI3`; `SC=$T/skills_tsci3/skills/tsci3-secuencias/scripts`.

## Criterio de rúbrica
AF3 Secuencias (20): 35/50/15/15 (`OD/AD26 TSCI3 AF3.png`).

## Método (con cita)
- `OD/SEQMIN.R`: `parse_spmf` (−1 cierra el evento, −2 la secuencia), eventos agregados, `read_baskets` y `cspade(support = 0.01, maxsize = 3, maxlen = 4)`; `df_freq` ordenado por soporte.
- Un patrón ⟨E1, …, Ek⟩ está en una secuencia si hay eventos i1 < … < ik con Ej ⊆ evento ij. Soporte = secuencias que lo contienen / secuencias, la misma definición por caso que `OD/EPISODES.R`.
- No hay Excel de clase de secuencias en las fuentes (decisión de rutina del plan): se usa el formato de conteo y cociente de `OD/AP (1).xlsx`, una hoja por número de ítems (R2) y la descomposición a mano de la secuencia 1.

## Ejecutar
1. `I=$T/incisos/<id>`; archivo SPMF en `$I/datos/`; `parametros.json`: `{"archivo": "x.csv", "soporte": 0.01, "maxsize": 3, "maxlen": 4}`.
2. `cp $SC/resolver_secuencias.py $I/codigo/resolver.py && (cd $I && python3 codigo/resolver.py > salida_python.txt)`.
3. Oráculo: `python3 $T/kit_tsci3/kit.py secuencias-oraculo $I/datos/x.csv $I/traza.json` (✅).
4. R: `cp $SC/script_secuencias.R $I/codigo/script.R` (ARCHIVO y parámetros arriba; el resto es `SEQMIN.R`); `Rscript codigo/script.R > salida_R.txt 2>&1`; `python3 $SC/comparar_r.py $I` (✅).
5. Excel: `$T/.venv/bin/python $SC/excel_secuencias.py $I` y `recalcular_excel.py` (todas «sí»).

## Verificación
1. Oráculo: crecimiento de patrones (extensiones de secuencia y de ítem) con contención voraz.
2. R: `patrones_R.csv` (cspade) = `patrones_python.csv`, patrón por patrón.
3. Caso: la secuencia 1 ⟨{1},{3},{7},{4}⟩ se descompone a mano en el Excel (15 patrones).
4. Mutante: ignorar el orden de los eventos cambia el conteo de 178 patrones (contar apariciones en vez de secuencias no se detecta con SEQMIN.csv porque ningún ítem se repite en una secuencia).

## Casos de referencia comprobados
- **SEQMIN.csv** (100 secuencias): 258 patrones frecuentes (por número de ítems 7, 31, 80, 97, 40, 3); ⟨{3}⟩ 1.00, ⟨{1}⟩ y ⟨{1},{3}⟩ 0.85, ⟨{6}⟩ 0.70. Oráculo ✅; R (cspade) = Python 258/258; Excel 147/147.
