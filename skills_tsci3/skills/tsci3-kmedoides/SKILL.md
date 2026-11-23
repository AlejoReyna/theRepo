---
name: tsci3-kmedoides
description: K-medoides en TSCI3 con los dos criterios rotulados (T6) - el del ejercicio de clase (OD/DOLLY LIVES.xlsx Sheet2 - una iteración de k-means y medoide = registro más cercano a cada centroide actualizado, con DM0, DM1, pertenencia y costo) y PAM (BUILD + SWAP, cluster::pam) - con silueta por registro, más PAM y CLARA del curso en R (OD/TSCI3 P6.R). Deja Excel con fórmulas, programa en Python, script R y verificación. Úsala cuando pidan "k-medoides", "k-medoids", "medoides", "PAM", "CLARA" o silueta de grupos (TSCI3 AF3 K medoids).
---

# K-medoides (criterio de clase + PAM/CLARA)

Lee antes `../tsci3-comun/references/reglas-academicas.md` y `../tsci3-comun/references/verificacion.md`. Comparte normalización y la iteración de k-means con `tsci3-kmeans`.
`T=/Users/alexis/theCode/newSkills/TSCI3`; `SC=$T/skills_tsci3/skills/tsci3-kmedoides/scripts`.

## Criterio de rúbrica
AF3 K medoids (10): 35/50/15/15 (`OD/AD26 TSCI3 AF3.png`).

## Método (con cita)
- **Clase** (`OD/DOLLY LIVES.xlsx` Sheet2): y = m·x + b; una iteración de k-means con C0 = mín y C1 = máx; C' = (Σx·pertenencia + C)/(n + 1) (AG2:AR3); distancia de cada registro a C0' y C1' (AF8:AG56); medoide = registro de distancia mínima (AF57, AG57 → M0, M1 en AG4:AR5). El archivo deja vacías DM0, DM1 y la nueva pertenencia: aquí se calculan, con el costo ΣDMIN.
- **PAM** (`OD/TSCI3 P6.R` usa `pam`; `EJ26-1` p.1–2): BUILD + SWAP sobre los mismos datos normalizados (hasta 2000 registros en Python; más → CLARA en R).
- **Silueta** s(i) = (b(i) − a(i))/máx{a(i), b(i)} (`AD24` Novianti p.3, ec. 3), para ambos criterios.
- **R (P6.R):** `scale`; PAM y CLARA (`samples = 50, pamLike = TRUE`) con silueta, WSS y gap; k final = silueta.
- T6: se entregan los dos criterios rotulados; no se mezclan.

## Ejecutar
1. `I=$T/incisos/<id>`; datos y `parametros.json` como en `tsci3-kmeans`.
2. `cp $SC/resolver_kmedoides.py $I/codigo/resolver.py && (cd $I && python3 codigo/resolver.py > salida_python.txt)`.
3. Oráculo: `python3 $T/kit_tsci3/kit.py kmedoides-oraculo $I/datos/x.csv $I/traza.json` (✅).
4. R: `$SC/script_kmedoides.R` → `$I/codigo/script.R`; `Rscript codigo/script.R > salida_R.txt 2>&1`; `python3 $SC/comparar_r.py $I` (✅).
5. Excel: `$T/.venv/bin/python $SC/excel_kmedoides.py $I` y `recalcular_excel.py` (todas «sí»).

## Verificación
1. Oráculo: recalcula el criterio de clase y la silueta con su propia matriz de distancias; para PAM comprueba el costo y que ningún intercambio medoide ↔ registro lo mejora.
2. R: medoides de clase y de PAM, grupos y silueta de `cluster::silhouette` por registro.
3. Caso de referencia: AF57, AG57 y M0/M1 tecleados de DOLLY Sheet2 (modo réplica T1, `test_kmeans.py`).
4. Mutante: tomar el registro más lejano (MAX en lugar de MIN) cambia M0/M1 y falla la prueba.

## Casos de referencia comprobados
- **DOLLY Sheet2** (49 × 12): réplica con T1 = AF57 0.355669, AG57 0.857441 y los vectores tecleados M0, M1 (a 1e−12). Sin el error, los medoides son los mismos registros (42 y 8; distancias 0.385066 y 0.827621); asignación 46/3, costo 42.672814, silueta media 0.2538. PAM: registros 42 y 23, costo 40.490272, 28/21, silueta media 0.0860. Oráculo 8/8; R = Python (medoides, grupos, silueta); Excel 36/36. R (P6.R, scale): PAM y CLARA con k = 2 por silueta, medoides 11 y 23 (26/23).
