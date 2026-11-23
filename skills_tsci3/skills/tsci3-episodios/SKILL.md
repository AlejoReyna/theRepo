---
name: tsci3-episodios
description: Episodios A -> B dentro de una ventana de tiempo en TSCI3 (OD/EPISODES.R) - EVENT en mayúsculas, caso = G grid _B beat, pares i < j del mismo caso con 0 < Δ ≤ wsize, soporte = casos con el episodio / casos, global y por distrito - con Excel de pares y soporte (fórmulas), programa en Python que reproduce exactamente los CSV del script, script R y verificación. Úsala cuando pidan "episodios", "ventana de tiempo", "wsize", "A -> B", "secuencias de eventos por caso" o "EPISODES" (TSCI3 AF3 Episodios).
---

# Episodios en una ventana (EPISODES.R)

Lee antes `../tsci3-comun/references/reglas-academicas.md` y `../tsci3-comun/references/verificacion.md`.
`T=/Users/alexis/theCode/newSkills/TSCI3`; `SC=$T/skills_tsci3/skills/tsci3-episodios/scripts`.

## Criterio de rúbrica
AF3 Episodios (20): 35/50/15/15 (`OD/AD26 TSCI3 AF3.png`).

## Método (`OD/EPISODES.R`)
- MOMENT = `cdatetime`; EVENT = `str_to_upper(str_trim(crimedescr))`; CASE_ID = «G» + grid + «_B» + beat; se ordena por CASE_ID y MOMENT.
- Por caso, todos los pares i < j con 0 < Δ ≤ wsize (wsize = 10); episodio = «A -> B».
- Soporte = casos distintos con el episodio / casos (`n_distinct(CASE_ID)`), global y por distrito (cada distrito con sus propios casos).
- T14: `read_csv` recorta los espacios de `beat` («3C        » → «3C»). T23: un `beat` vacío forma el caso «G…_BNA» (como `paste0` en R); en Sacramento son 42 filas.
- El cálculo es determinista: el programa reproduce los tres CSV del script en contenido y orden.

## Ejecutar
1. `I=$T/incisos/<id>`; CSV con `cdatetime, crimedescr, grid, beat, district` en `$I/datos/`; `parametros.json`: `{"archivo": "x.csv", "wsize": 10}`. Con otras columnas, adapta `leer()` y el script R a la vez.
2. `cp $SC/resolver_episodios.py $I/codigo/resolver.py && (cd $I && python3 codigo/resolver.py > salida_python.txt)` → `traza.json` y `episodios_*_python.csv`.
3. Oráculo: `python3 $T/kit_tsci3/kit.py episodios-oraculo $I/datos/x.csv $I/traza.json` (✅).
4. R: `cp $SC/script_episodios.R $I/codigo/script.R` (ARCHIVO y WSIZE arriba); `Rscript codigo/script.R > salida_R.txt 2>&1`; `python3 $SC/comparar_r.py $I` (✅ los tres CSV iguales).
5. Excel: `$T/.venv/bin/python $SC/excel_episodios.py $I` y `recalcular_excel.py` (todas «sí»).

## Verificación
1. Oráculo: ventana deslizante con dos punteros por caso; soporte global y por distrito.
2. R: `episodios_detalle.csv`, `episodios_globales.csv` y `episodios_por_distrito.csv` del script = los de Python, fila por fila.
3. Caso de referencia: Sacramento (abajo).
4. Mutante: aceptar Δ ≥ 0 da 832 pares en lugar de 726 (el oráculo lo comprueba).

## Casos de referencia comprobados
- **SacramentocrimeJanuary2006mo.csv**: 7584 eventos, 606 casos, 726 pares, 393 episodios; el más frecuente es «TOWED/STORED VEHICLE -> TOWED/STORED VEHICLE» (27 casos, soporte 0.0446); 448 filas por distrito. R = Python en los tres CSV; oráculo 5/5; Excel 62/62.
