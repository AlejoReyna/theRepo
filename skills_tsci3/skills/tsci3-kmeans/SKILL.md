---
name: tsci3-kmeans
description: K-means con la convención del ejercicio de clase de TSCI3 (OD/mochila_.xlsx, DOLLY LIVES.xlsx) - normalización y = m·x + b, centroides iniciales mínimo y máximo, distancia euclidiana, pertenencia por DMIN, actualización C' = (Σx·pertenencia + C)/(n + 1), una hoja por iteración hasta que la pertenencia no cambia - más la selección de k y el kmeans del curso en R (OD/TSCI3 P6.R - scale, silueta, WSS, gap, nstart 25). Deja Excel con fórmulas vivas, programa en Python, script R y verificación. Úsala cuando pidan "k-means", "kmeans", "agrupar", "clusters", "centroides" o "número de grupos" (TSCI3 AF3 K means clustering).
---

# K-means (ejercicio de clase + R del curso)

Lee antes `../tsci3-comun/references/reglas-academicas.md` (R2: todas las iteraciones) y `../tsci3-comun/references/verificacion.md`.
`T=/Users/alexis/theCode/newSkills/TSCI3`; `SC=$T/skills_tsci3/skills/tsci3-kmeans/scripts`.

## Criterio de rúbrica
AF3 K means clustering (10): Ejercicio de clase 35 (Excel) / Programa 50 (`resolver.py`) / Ejercicio en R 15 (`salida_R.txt`) / Script R 15 (`OD/AD26 TSCI3 AF3.png`; T2).

## Método (con cita)
1. y = m·x + b, m = 1/(máx − mín), b = −m·mín (`OD/mochila_.xlsx` B4:D5).
2. C0 = vector mínimo y C1 = vector máximo normalizados (B6:G7 → (0, …, 0) y (1, …, 1)). k = 2 como en los Excel; con otro k no hay convención de clase: usa solo R.
3. DC0, DC1 euclidianas; DMIN = MIN; pertenencia IF(DMIN = DC0, 1, 0) e IF(DMIN = DC1, 1, 0) (un empate cuenta en ambos) (H10:L10).
4. C' = (SUMPRODUCT(x, pertenencia) + C)/(n + 1) (J6:L7; DOLLY AG2:AR3). Es la regla del profesor (T7): cuenta el centroide anterior como un punto más. `kmeans` de R usa la media.
5. Se repite hasta que ninguna pertenencia cambia; una hoja por iteración (R2).
6. R (`OD/TSCI3 P6.R`): `scale`, `fviz_nbclust` silueta y WSS (codo = máx |x + y − 1|), `clusGap` (Tibs2001SEmax), k final = silueta, `kmeans(nstart = 25)`, `fviz_cluster`, `write.csv`. Semilla declarada (T15); con más de 3000 filas la selección de k usa una muestra (T21).

## Ejecutar
1. `I=$T/incisos/<id>`; datos en `$I/datos/`; `$I/datos/parametros.json`: `{"problema": "…", "archivo": "x.csv", "columnas": [...] (opcional), "actualizacion": "clase"}`.
2. `cp $SC/resolver_kmeans.py $I/codigo/resolver.py && (cd $I && python3 codigo/resolver.py > salida_python.txt)`.
3. Oráculo: `python3 $T/kit_tsci3/kit.py kmeans-oraculo $I/datos/x.csv $I/traza.json` (✅).
4. R: copia `$SC/script_kmeans.R` a `$I/codigo/script.R` (ARCHIVO y COLUMNAS arriba) y `Rscript codigo/script.R > salida_R.txt 2>&1`; `python3 $SC/comparar_r.py $I` (✅).
5. Excel: `$T/.venv/bin/python $SC/excel_kmeans.py $I` y `recalcular_excel.py` (todas «sí»). Con más de 200 000 filas × iteraciones, solo la iteración 1 lleva fórmulas (como el Excel del profesor) y las demás van como valores.

## Verificación
1. Oráculo: otra normalización ((x − mín)/(máx − mín)), asignación por distancias al cuadrado; cada iteración.
2. R: parte 1 del script repite las iteraciones de clase → `comparar_r.py`.
3. Caso de referencia: cifras en caché del profesor (`kit_tsci3/pruebas/test_kmeans.py`).
4. Mutantes: quitar «+ C», quitar la raíz o usar b = +m·mín cambian J6:L8.

## Casos de referencia comprobados
- **mochila_.csv** (100 000 registros; = `OD/mochila_.xlsx`): iteración 1 = caché J6:L8 exacto (C0' = 0.365126, 0.364188, 0.363374; C1' = 0.633363, 0.636243, 0.637025; ΣDMIN = 74 495.033286; 50 044 y 49 956). Converge en 40 iteraciones (49 988 y 50 012). Oráculo ✅; R = Python en 40 iteraciones; Excel 15/15. R (P6.R): WSS 4, silueta 7, gap 1 → kmeans k = 7.
- **DOLLY Sheet1** (49 × 12): el oráculo en modo réplica del error T1 reproduce AC57 = 78.7431, 46/3 y AG2:AR3 a 1e−12. Sin el error: iteración 1 con 46/3 y ΣDMIN = 79.843030; converge en 11 iteraciones (29/20). Oráculo ✅; R = Python; Excel 321/321. R: WSS 4, silueta 2, gap 1 → k = 2 (28 y 21).
