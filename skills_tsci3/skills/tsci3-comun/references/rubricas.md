# Rúbricas y mapa de temas

Prefijos: ver `fuentes.md`. Cada tarea AF vale 10 % de la final; medio curso, ordinario y PIA, 20 % cada uno (`OD/AD26 TSCI3 CO PC.pdf` p.3).

## Columnas de cada actividad

- **AF1 Tratamiento de datos** (`OD/AD26 TSCI3 AF1.png`): 1.1 (5: Contenido 70, Referencias 30); Proceso Minería (10: Fases 50, Corrección 30, Referencias 20); Obj WB, Obj Datagov, Obj datos gob (15 c/u: Coherencia 40, Congruencia 40, Referencias 20); Metro y Border Crossing (15 c/u) y Set R (10): Objetivo 30, Subset + Resultado 50, Referencias 20.
- **AF2 Modelado de procesos** (`OD/AD26 TSCI3 AF2.png`): Disco 15 (Nivel de detalle 35, Análisis 50, Referencias 15); Separación Disco 16 (Separación 50, Análisis 35, Referencias 15); Diagrama clase 7 (25/32/43); Diagrama transición 8, Petri 8, Red Causal 8 y P Tree 8 (Diagrama 60, Definición 40); YAWL, BPMN y EPC 5 c/u (Diagrama 100); Bupa R 15 (Métricas 45, Diagrama 35, Referencias 20).
- **AF3 Técnicas de minería** (`OD/AD26 TSCI3 AF3.png`): Árboles 20 (25/25/25/25); K means 10, K medoids 10, A priori 20, Secuencias 20, Episodios 20, con Ejercicio de clase 35 / Programa 50 / Ejercicio en R 15 / Script R 15 (suman 115: T2).
- **AF4 Regresión y clasificadores** (`OD/AD26 TSCI3 AF4.png`): 14 elementos, cada uno Ejercicio de clase 50 / Script R 50.

## Mapa tema → fuente → skill

| # | Tema | Elemento de rúbrica (peso) | Fuente que produce el cálculo | Skill |
|---|---|---|---|---|
| 1 | Subconjuntos y limpieza de datos en R; tratamiento en función de un objetivo de minería | AF1 Metro (15), Border Crossing (15), Set R (10); MC problema 2 | `OD/SUBSET.pdf` p.5–24; `EX-MC` problema 2; `RESP` p.7–11 | S1 |
| 2 | Normalización min-max y z | Dentro de los temas 3, 4 y 20 | `OD/mochila_.xlsx` B4:G7; `OD/DOLLY LIVES.xlsx` B4:M5; `AD25-06` p.2; `OD/TSCI3 P6.R` (`scale`) | S2, S3, S16 |
| 3 | K-means y selección de k | AF3 K means clustering (10) | `OD/mochila_.xlsx`; `OD/DOLLY LIVES.xlsx` Sheet1; `OD/TSCI3 P6.R`; `OD/AM R.pdf` p.46–47 | S2 |
| 4 | K-medoides (PAM, CLARA) | AF3 K medoids (10) | `OD/DOLLY LIVES.xlsx` Sheet2; `OD/TSCI3 P6.R`; `AD24` Novianti p.3 | S3 |
| 5 | Apriori | AF3 A priori (20) | `OD/AP (1).xlsx`; `OD/arules R (2).txt`; `EJ26-24` p.6, p.10 | S4 |
| 6 | Patrones secuenciales | AF3 Secuencias (20) | `OD/SEQMIN.R` | S5 |
| 7 | Episodios | AF3 Episodios (20) | `OD/EPISODES.R` | S6 |
| 8 | Árbol de mínima entropía y comparación con los árboles de R | AF3 Árboles de decisión (20); MC problema 3 | `EJ26-14` p.3; `EJ26-21` p.3; `EX-MC` problema 3; §1.4 R1 y R2 | S7 |
| 9 | Mínimos cuadrados | AF4 (6) | `OD/AM R.pdf` p.3–6 | S8 |
| 10 | Breusch-Pagan | AF4 (6) | `OD/AM R.pdf` p.7–9 | S9 |
| 11 | Predictor binario | AF4 (7) | `OD/AM R.pdf` p.10–12 | S10 |
| 12 | Regresión múltiple | AF4 (10) | `OD/AM R.pdf` p.13–19, p.25–28 | S11 |
| 13 | Predictor no binario | AF4 (6) | `OD/AM R.pdf` p.33–35 | S11 |
| 14 | Stepwise | AF4 (7) | `OD/AM R.pdf` p.20–24 | S12 |
| 15 | Lasso | AF4 (7) | `OD/AM R.pdf` p.29–30 | S13 |
| 16 | Ridge | AF4 (7) | `OD/AM R.pdf` p.31–32 | S13 |
| 17 | Logística binaria | AF4 (6) | `OD/AM R.pdf` p.36–40 | S14 |
| 18 | Logística multinomial | AF4 (6) | `OD/AM R.pdf` p.41 | S14 |
| 19 | Matriz de confusión | AF4 (6) | `OD/AM R.pdf` p.49–50; `AD25-11` p.9 | S15 |
| 20 | KNN | AF4 (10) | `OD/AM R.pdf` p.43–48; `AD25-12` p.2–3 | S16 |
| 21 | Determinación de k para KNN | AF4 (6) | `OD/AM R.pdf` p.45–47, p.51–53 | S16 |
| 22 | Bosques aleatorios | AF4 (10) | `OD/AM R.pdf` p.54–55 | S17 |
| 23 | Red de Petri y su denominación | AF2 Petri (8: Diagrama 60, Definición 40); MC problema 1 | `EX-MC` problema 1; `RESP` p.2–4; `MC/P1_REGEVEN_Procesos/Problema_1.py` | S18 |
| 24 | Diagrama asignado por el último dígito: BPMN (con ejemplo aceptado); YAWL y EPC (sin ejemplo) | AF2 BPMN, YAWL y EPC (5 cada uno: Diagrama 100); MC problema 1 | `EX-MC` problema 1; `RESP` p.5–6 | S18 |
| 25 | Modelo asignado por paridad: árbol de proceso (con ejemplo aceptado); red causal (sin ejemplo) | AF2 P Tree y Red Causal (8 cada uno: Diagrama 60, Definición 40); MC problema 1 | `EX-MC` problema 1; `RESP` p.6 | S18 |

Cobertura:

- AF1: 40 de 100.
- AF2: 21 de 100 con un ejemplo aceptado (Petri, BPMN y P Tree). Otros 18 (YAWL, EPC y Red Causal) entran al mapa porque el examen los califica, pero quedan en estado P porque ninguna fuente muestra su método. Los 61 restantes siguen bloqueados (§7 B2).
- AF3 y AF4: 100 de 100.
- Medio curso: los tres problemas.

Cada tarea vale 10 % de la calificación final (`OD/AD26 TSCI3 CO PC.pdf` p.3), y el medio curso 20 %.

## Sin skill de resolución Calificados o citados sin cálculo demostrable desde las fuentes (no generan skill de resolución)

- **AF1 con respuesta redactada:** 1.1 (Contenido 70, Referencias 30), Proceso Minería (Fases 50, Corrección 30), Obj WB, Obj Datagov y Obj datos gob (Coherencia, Congruencia) (`OD/AD26 TSCI3 AF1.png`).
- **AF2 sin fuente:** Disco (15), Separación Disco (16), Diagrama clase (7), Diagrama transición (8) y Bupa R (15), que suman 61 puntos (§7 B2).
- **Temas que solo aparecen en artículos de PIA**, sin criterio de rúbrica:
  - agrupamiento jerárquico de Ward (`AD24` Žmuk p.1, p.4; `EJ26-25`);
  - DBSCAN (`OD/Anomaly_detection_in_temperature_data_us.pdf` p.3–4; `EJ26-5`);
  - PCA (`EJ26-12`; `AD24` Monteiro);
  - BIRCH (`EJ26-6`);
  - SVM (`AD25-06`);
  - TF-IDF y chi² (`AD25-09`).

  Quedan fuera hasta que exista la rúbrica del PIA (§7 B3).
