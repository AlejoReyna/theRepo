# Índice de fuentes

Prefijos de las citas (las copias con hash están en `$T/fuentes/`, `T=/Users/alexis/theCode/newSkills/TSCI3`):

| Prefijo | Copia en el proyecto | Original |
|---|---|---|
| `OD/` | `$T/fuentes/OD/` | `~/Downloads/OneDrive_1_11-12-2026/` |
| `DL/` | `$T/fuentes/DL/` | `~/Downloads/` (`gastank.csv`, `export.csv`, `REGEVEN.xlsx`, enunciado del MC) |
| `EX-MC` | `$T/fuentes/DL/AD26 TSCI3 MC (Práctica).pdf` | enunciado del medio curso |
| `MC/` | `$T/fuentes/MC/` | `~/Downloads/1851265_MC_TSCI3/` (respuesta calificada) |
| `RESP` | `$T/fuentes/MC/Respuestas_MC_TSCI3_1851265.pdf` | |
| `EJ25/`, `AD25/`, `EJ26/`, `AD24/` | `$T/fuentes/<carpeta>/` | carpetas «PIA» de `~/Downloads/` (artículos, no PIAs resueltos) |
| `EJ26-14`, `AD25-11`, `EJ25-6` | `EJ26 TSCI3 14.pdf`, `tsci3ad25 11.pdf`, `tsci3 6.pdf` | |
| `EG/` | `/Users/alexis/theCode/newSkills/Endgame/` | |
| `EF/` | `$T/plantilla_entrega/` | `EG/entrega_final/2026-10-15/` |

«p.» = página del visor del PDF; «l.» = línea del archivo. Comprueba cualquier cita con `$T/herramientas/comprobar_citas.py`.


## 1. Endgame (TSO). No es TSCI3.

Periodo: plan de TSO AD25 (`fuentes.md`), entrega del 15/10/2026 y archivo del 22/10/2026 (`EG/README.md`).

| Ruta | Contenido | Citas que usa el plan |
|---|---|---|
| `EG/README.md`, `EG/AGENTS.md`, `EG/CLAUDE.md` | Propósito, capas y reglas. No se modifica la entrega original. | §1.1; §5 (copias, no originales) |
| `EG/skills_tso/LEEME.md`, `MATRIZ_SKILLS.md` | Las 34 skills; la matriz algoritmo → fuente → skill → verificación → estado. | §1.2 |
| `EG/skills_tso/INFORME_VALIDACION.md` | Línea base 176/176, batería 144/144, mutantes 13/13, selección de skills 39/40. | §1.1; §6 paso 24 |
| `EG/skills_tso/PENDIENTES.md` | Discrepancias por confirmar. | §1.2 |
| `EG/skills_tso/skills/tso-resolver-examen/SKILL.md` | Flujo coordinador §0–9. Usa `verificar_docx.py --numeros` (§8). | §1.2; §5; §6 paso 22 |
| `EG/skills_tso/skills/tso-johnson/SKILL.md`, `tso-comun/SKILL.md` | Estructura de una skill por método y de la base común. | §1.2 |
| `EG/skills_tso/skills/tso-comun/references/presentacion.md`, `reglas-academicas.md`, `fuentes.md` | Forma del desarrollo; código como capturas; método nombrado; índice con páginas. | §1.2 |
| `EG/kit_tso/GUIA_DESARROLLO.md`, `MATRIZ_TRAZABILIDAD.md` | Retroalimentación 45/100 del profesor; trazabilidad. | §1.2 |
| `EG/herramientas/reproducir_entrega.py`, `EG/preparar_examen.py` | Recálculo de trazas; sesión por examen sin sobrescribir. | §5; §6 |
| `EG/plantillas/artifact-template-examen-optimizacion/` (`SKILL.md`, `references/formato.md`, `assets/preview.png`, `reference-page-2.png`, `reference-page-3.png`) | Plantilla de Pages del examen de TSO. Su portada dice «Docente: Dr. Raymundo Said Zamora Pequeño». | §5 (confirma al docente) |
| `EG/Material_de_estudio/TSO PIA.png` | Rúbrica del PIA de TSO: REV 1 LEC, REV 2, REV 3, REV 4 INT, PREC TEC, MAN TEC, MAN USU, TEMPO, INST, PROG. | §7 B3 |
| `EG/Examenes_regularización/mochila_.csv` | 100 000 registros (ID, Peso, Volumen, Beneficio). Son los mismos datos de `OD/mochila_.xlsx` (ID 1 = 2.7, 7.43, 29). | §3.3 |

## 2. Plantilla de entrega `EF/` (TSO, 15/10/2026). No es TSCI3: es el formato.

| Ruta | Contenido | Citas |
|---|---|---|
| `EF/1851265_TSOER2.zip` | 23 archivos bajo `1851265_Entrega_final/`: `Parte_práctica/P1_Barrido`, `P2_BFSA`, `P3_ACO`, `P4_Mochila`; `Parte_teórica.pdf`; `Por si acaso/Teoría_pero_en_word.docx`. | §5 (árbol) |
| `…/P4_Mochila/Procedimientos.pdf` (12 p., carta horizontal de 792 × 612 pt) | p.1: encabezado, enunciado, tabla y cajas del procedimiento. p.5: «Paso 1 Selección de datos y modelo». p.11: «Código Funciones que hicieron los cálculos». p.12: «Comprobación exacta del beneficio máximo». | §5 (secciones) |
| `…/P1_Barrido/Procedimientos.pdf` (21 p.), `…/P2_BFSA/BFSA P2.pdf` (1 p.) | Mismo encabezado. Pasos 1.1–5.3. «Fuentes del curso». | §5 |
| `…/P4_Mochila/codigo/resolver.py`, `datos/parametros.json`, `traza.json` | Programa que lee los datos y escribe la traza. | §5 |
| `…/Demostración.xlsx` (P1, P2, P3, P4) | Hojas en el orden Resultado, Datos, una hoja por paso, Control. P4: Resultado, Datos, Constructivo, Control. | §5 |
| `…/Parte_teórica.pdf` (4 p., vertical) | Bloque derecho con nombre, «Matrícula: 1851265» y «Fecha: 15 de octubre de 2026»; título «Examen Extraordinario»; preguntas numeradas. | §5 |
| `…/Por si acaso/Teoría_pero_en_word.docx` | Mismo contenido, con los estilos Normal, Title, Heading 1 y List Bullet. | §5 |
| `EF/editables/P1_Barrido.docx`, `P2_BFSA.docx`, `P3_ACO.docx`, `P4_Mochila.docx` | Fuentes en Word de Procedimientos. Línea 5: «Docente: Dr. Raymundo Said Zamora Pequeño». Incluyen los logotipos. | §5 (base que se clona) |

## 3. `OD/` (AD26 = agosto a diciembre de 2026). Es TSCI3.

| Ruta | Contenido | Citas |
|---|---|---|
| `AD26 TSCI3 CO PC.pdf` (9 p.) | p.1: materia «Tópicos selectos de Ciencias de la Ingeniería III», «M.C Said Zamora». p.2: temario (tratamiento de datos; modelado de procesos; técnicas de minería; evaluación) y fechas: medio curso 25/09/2026, ordinario 26/11/2026, extraordinario 09/12/2026. p.3: evaluación (Tareas (4) 40; medio curso 20; ordinario 20; producto integrador 20; los ejercicios de clase van dentro de las actividades). p.4: entrega solo en la carpeta asignada, nombre «Matrícula + Color, Hora, #Tarea», penalización de 10 puntos. p.5: asesorías. p.6–7: bibliografía (van der Aalst 2016; Aggarwal 2015; Bramer 2020; Sumathi y Sivanandam 2006). p.8: enlaces a Disco. p.9: imágenes decorativas. | p.1–4, p.6 |
| `AD26 TSCI3 AF1.png` | Rúbrica AF1, Tratamiento de datos: 1.1 (5), Proceso Minería (10), Obj WB (15), Obj Datagov (15), Obj datos gob (15), Metro (15), Border Crossing (15), Set R (10), con sus criterios. | §3, S1 |
| `AD26 TSCI3 AF2.png` | Rúbrica AF2, Modelado de procesos: Disco 15, Separación Disco 16, Diagrama clase 7, Diagrama transición 8, Petri 8, YAWL 5, BPMN 5, EPC 5, Red Causal 8, P Tree 8, Bupa R 15. | §3.2, §7 B2 |
| `AD26 TSCI3 AF3.png` (pesos leídos en ampliación) | Rúbrica AF3, Técnicas de minería: Árboles 20 (25/25/25/25); K means 10, K medoids 10, A priori 20, Secuencias 20 y Episodios 20, todos con 35/50/15/15. | §3, S2–S7, T2 |
| `AD26 TSCI3 AF4.png` | Rúbrica AF4, Regresión y evaluación de clasificadores: 14 elementos con «Ejercicio de clase 50 / Script R 50». | §3, S8–S17 |
| `AM R.pdf` (55 p., «Análisis Predictivo», M.C. Said Zamora) | p.3–6: mínimos cuadrados (fórmula de p.4 verificada en la imagen), RSS, MSE, `lm`. p.7–9: Breusch-Pagan. p.10–12: predictor binario. p.13–19: regresión múltiple. p.20–24: stepwise y AIC. p.25–27: entrenamiento, 20 % de prueba, MSE/MAE/R², validación cruzada. p.28: `predict`. p.29–32: Lasso y Ridge. p.33–35: predictor no binario. p.36–41: logística y VIF. p.43–48: KNN, WCSS y codo. p.49–50: matriz de confusión (imagen revisada). p.51–53: validación cruzada y determinación de k. p.54–55: bosques aleatorios. | S8–S17 |
| `SUBSET.pdf` (24 p.) | R: lectura (p.1–3), `head` y `tail` (p.4), NA y `complete.cases` (p.5–8, p.10), datasets (p.9), `write.csv` (p.11), Border Crossing (p.12–15), MTA (p.16–17), paquetes (p.18–19), `read_csv` con `na=` (p.20), `clean_names` (p.21), `filter` (p.22), `distinct` (p.23), normalización de valores (p.24). | S1, S7 |
| `arules R (2).txt` | `apriori(supp = 0.01, conf = 0.1)`, `inspect`, `itemFrequencyPlot` relativo, `write.csv`; ejemplo con Groceries. | S4 |
| `SEQMIN.R` + `SEQMIN.csv` (100 líneas en formato SPMF) | `parse_spmf` (−1 cierra evento, −2 cierra secuencia), `read_baskets`, `cspade(support = 0.01, maxsize = 3, maxlen = 4)`. | S5 |
| `EPISODES.R` + `SacramentocrimeJanuary2006mo.csv` (7584 filas) | Episodios A → B por `CASE_ID = G{grid}_B{beat}` con 0 < Δ ≤ `wsize` = 10; soporte = casos con el episodio / casos; global y por distrito. | S6 |
| `TSCI3 P6.R` + `dataclu.csv` (737 filas) | `scale()`. k por silueta, por WSS (codo = máx \|x + y − 1\|) y por gap (`Tibs2001SEmax`) para `kmeans` (`nstart` 25), `pam` y `clara` (`samples` 50, `pamLike`). k final = silueta. `write.csv`. | S2, S3 |
| `mochila_.xlsx` (una hoja, 100 000 registros) | K-means en Excel con Peso, Volumen y Beneficio: m = 1/(máx − mín) y b = −m·mín (B4:D5); C0 y C1 (B6:G7); DC0, DC1, DMIN y pertenencia (H:L); actualización (J6:L7). En caché: m = (0.034483, 0.101010, 0.011111); fila 1 normalizada = (0.058621, 0.740404, 0.211111); C0′ = (0.365126, 0.364188, 0.363374); C1′ = (0.633363, 0.636243, 0.637025); ΣDMIN = 74 495.03; 50 044 y 49 956 registros por grupo. | S2, §6 |
| `DOLLY LIVES.xlsx` | **Sheet1**: k-means de 49 canciones × 12 variables, con la misma convención. En caché: AG2 = 0.341210, AH3 = 0.923077, \|C0\| = 46, \|C1\| = 3, ΣDMIN = 78.7431. AK7:AL9 = «2C 15, 3C 12, 4C 10», sin rótulo. **Sheet2**: k-medoides. Distancias a los centroides actualizados (AF:AG), mínimos AF57 = 0.355669 y AG57 = 0.857441, medoides M0 y M1 tecleados (AG4:AR5). Columnas DM0, DM1, C0 y C1 vacías. | S2, S3, T1, T6, T11 |
| `AP (1).xlsx` | Apriori a mano con 50 registros (HeartDisease, BMI, Smoking, AlcoholDrinking, Stroke): NX, NY y NX∧Y (J4:L11); S = NX∧Y/N, C = NX∧Y/NX, L = NX∧Y·N/(NX·NY) (M4:O11); conteo de reglas (M17:M21); composición «R1 THEN R2» (H24:K25). | S4 |
| `STARAD26.xlsx` (240 filas) | Star type, Star color y Spectral Class, sin enunciado. | S7, T13 |
| `Eelgrass_Beds_2006_Set DTME.xlsx` (166 filas) | OBJECTID, BED_DENSITY (H/M/L), FIELD_06_V, FIELD_02_V. | S7 |
| `old.csv` (272) | eruptions y waiting, las variables de `AM R.pdf` p.6. | S8, S9 |
| `BR (2).csv` (1000) | precio, recamaras, baños, m2_construcción, m2_terreno, pisos, condición, entre otras: las columnas que usa `AM R.pdf` p.40–41, p.48 y p.55. | S9, S11–S17 |
| `DFA.csv` (49) | Datos de Spotify, 11 variables. DOLLY LIVES agrega Key. | S2 |
| `ambx.csv` (29) | Ozone, Solar.R, Wind y Temp, las variables de `SUBSET.pdf` p.5–8. | S1 |
| `apri poko.csv` (50) | Objetos con atributos marcados «Yes». | S4 |
| `MTA_Metro-North_Delay_Verification__Beginning_2012.csv` (141 110), `Border_Crossing_Entry_Data.csv` (394 866) | Datos de `SUBSET.pdf` p.12–17. | S1 |
| `Anomaly_detection_in_temperature_data_us.pdf` (6 p.) | Çelik et al. 2011, DBSCAN (eps y minpts, p.3–4). | §3.2 |

## 4. `EJ25/` (enero a junio de 2025). Es TSCI3 (archivos «tsci3 n»).

Son artículos, no PIAs resueltos. Tema común: regresión lineal múltiple.

| Archivo | Contenido | Citas |
|---|---|---|
| 1 | Świecka et al. 2024 (preprint), decisiones de pensión con minería de datos | — |
| 2 | Miljković et al. 2010, predicción de partidos de baloncesto | — |
| 3 | Nie y Yu 2016, consumo eléctrico de oficinas con regresión multivariada | — |
| 4 | Somayasa et al., detección de cambio de modelo en regresión multivariada | — |
| 5 | Kaya, Şahin y Alma, eficiencia de paneles fotovoltaicos con regresión multivariada | p.3 (eliminación hacia atrás) |
| 6 | Amnuaylojaroen, PM2.5 con regresión multivariada | p.3 (R², RMSE, SE) |
| 7 | Rani y Sathyanarayana 2020, rendimiento de cultivos con regresión combinatoria | — |
| 8 | Rajalaxmi et al. 2019, regresión del rendimiento académico | — |

## 5. `AD25/` (agosto a diciembre de 2025). Es TSCI3 (archivos «tsci3ad25 nn»).

Son artículos. Tema común: KNN.

- 01 Sudipa et al. 2024: frutas.
- 02 Wijati et al. 2024: reseñas de aplicaciones.
- 03 Sinkron 2023: clase superior. p.2 distancia euclidiana; p.3 matriz de confusión; p.11 métricas.
- 04 Alkhatib et al. 2013: acciones; p.2 menciona algoritmos genéticos.
- 05 Islam et al. 2018: depresión.
- 06 Anggoro et al. 2020: SVM frente a KNN; p.2, ec. 1: normalización min-max.
- 07 Li, Yu y Lu: KNN para texto.
- 08 Pal 2021: KNN frente a bosque aleatorio; p.6 cita PSO.
- 09 Kirana y Al Faraby 2021: TF-IDF y chi².
- 10 Shouman et al.: KNN con voto y 10 pliegues.
- 11 Suprayogi y Sari 2022: p.9, exactitud, precisión y recall con números.
- 12 Saxena et al. 2014: diabetes; p.2 distancia; p.3 pasos.

## 6. `EJ26/` (enero a junio de 2026). Es TSCI3 (archivos «EJ26 TSCI3 n»).

Son artículos de aplicaciones de minería de datos.

- 1 Ng y Han: CLARANS, PAM y CLARA; p.1–2.
- 2 Babbar y Babbar 2017: calidad de ríos.
- 3 Karimipour et al. 2005: SIG y calidad del agua.
- 4 Hafeez et al. 2011: demanda de riego.
- 5 Majumdar et al.: agricultura (PAM, DBSCAN, regresión).
- 6 Zhang et al. 1997: BIRCH.
- 7 Kusiak y Verma: turbinas eólicas.
- 8 Shah y Kusiak 2007: genes y algoritmos genéticos; p.1–2.
- 9 Carvalho y Freitas 2004: árbol de decisión y algoritmo genético; p.2, p.4.
- 10 Rugeles Díaz et al. 2025: fraude con tarjetas.
- 11 Destriani et al.: incendios con CLARA.
- 12 Tang et al. 2013: PCA y CLARA; p.2.
- 13 Artículo sin título extraíble: minería educativa.
- **14 Karaolis et al. 2010: árboles de decisión; p.3, ecs. 2.1–2.10.**
- 15 Križanić: agrupamiento y árbol.
- 16 Bifet et al.: árbol rápido.
- 17 Banu 2016: tiroides con árbol.
- 18 Pachet et al.: música.
- 19 Jurnal Ekonomi dan Pembangunan 2021: macroeconomía.
- 20 Gharehchopogh y Mohammadi 2012: árbol en salud.
- **21 Al-Radaideh et al. 2006: árboles con estudiantes; p.3.**
- 22 Araujo et al.: recomendación en juegos MOBA; p.4 descenso de gradiente estocástico.
- 23 Siqueira et al.: jugadores de WoW.
- **24 Gao, Wang y Yang 2023: reglas de asociación y k-means; p.6 y p.10, Tabla 3.**
- 25 Hossain: ventas de videojuegos con agrupamiento.

## 7. `AD24/` (agosto a diciembre de 2024)

Se consideran de TSCI3 porque el pedido lo dice. Los nombres de archivo no lo marcan. Tema común: agrupamiento.

- Žmuk 2015 (CREBBS): Ward y distancia euclidiana al cuadrado; p.1, p.4.
- Heinz et al. 2020: desigualdades de salud.
- Ulkhaq y Adyatama 2021: reporte mundial de felicidad.
- Rosmahadi y Hamdan 2022: nutrición con k-means.
- **Novianti et al. 2020: k-medoides; p.3, VIF (ec. 2) y silueta (ec. 3).**
- **Privandhani y Sulastri 2022: canciones de Spotify con k-means y k-medoides en RStudio; p.3, silueta con 3 grupos.**
- Quiñones Huatangari et al. 2023: hábitos de alimentación.
- *Human Development Clustering in Indonesia* (JATM 2023).
- Atsa’am et al. 2021: cereales.
- Duman et al. 2022: rasgos de Spotify.
- Monteiro et al. 2019: Better Life Index.
- Cho 2014: bienestar infantil.

## 8. Medio curso AD26 (25/09/2026) y respuesta calificada. Es TSCI3.

| Ruta | Contenido | Citas |
|---|---|---|
| `EX-MC` (1 p.) | «Tipo de evaluación: Medio curso»; «Unidad de aprendizaje: Tópicos Selectos de Ciencias de la Ingeniería III»; Academia de Desarrollo de Tecnologías de la Información. **Problema 1 (U.T.2):** REGEVEN, registro del último dígito; red de Petri «y su denominación»; YAWL si termina en 0, 1 o 2, BPMN en 3, 4 o 5, EDPC en 6 a 9; árbol de proceso si es impar, red causal si es par. **Problema 2:** «Analice el registro que export, proponga y realice (con subsettings variados) un tratamiento de datos en función de un objetivo de la minería». **Problema 3:** «Obtenga el árbol de decisión de mínima entropía para el dataset gastank, compare el resultado con ambos árboles obtenidos mediante R». No trae puntos por problema. | §1.4; S1; S7; S18; T12 |
| `DL/REGEVEN.xlsx` | Hojas «Registro 00» a «Registro 09» con Case id, Event id, Timestamp (texto «05-05-2011:11.10»), Activity, Resource y Cost. Es idéntico a la copia de `MC/`. | S18; T17 |
| `DL/export.csv` | 118 580 filas y 33 columnas (Nutrition, Physical Activity, and Obesity del BRFSS). Data_Value vacío en 14 461 filas (13 214 con «-» y 1 247 con «~», recontadas). Encabezado «High_Confidence_Limit » con espacio final; Sample_Size con comas («1,367»). | S1; T18 |
| `DL/gastank.csv` | 737 filas: Model Name (163 valores), Type (la clase: 412 GS, 210 GT, 68 EHP, 47 GSI), Fuel Type (4 valores) y Vent Type (3 valores más 151 vacíos). Es idéntico a la copia de `MC/`. | S7; T16 |
| `MC/LEEME.txt` | Asignación de la matrícula 1851265 (termina en 5 e impar → Registro 05, BPMN, árbol de proceso); contenido de cada carpeta; cómo ejecutar; paquetes de R `partykit` y `rpart.plot`. | S18; §6 paso 0 |
| `RESP` (16 p.) y su `.docx` | Respuesta calificada. p.1: portada con «Tópicos Selectos de Ciencias de la Ingeniería III». p.2: tabla de asignación por matrícula. p.2–6: problema 1. p.7–11: problema 2. p.12–16: problema 3 y anexo de archivos. | §1.4 |
| `MC/P1_REGEVEN_Procesos/` | `Problema_1.py` (978 líneas, solo Python estándar): trazas, variantes, DFG, footprint, dependencia heurística, red escrita a mano en `TRANSICIONES` (l.132–170), grafo de alcanzabilidad, verificación, replay, árbol de proceso y exportación a DOT, PNML y BPMN 2.0. `reporte_P1.txt`: 91 eventos, 10 casos, 10 actividades, 13 recursos (l.5); \|F\| = 28 (l.98); 13 marcas y 15 arcos (l.118); red WF sólida (l.121); fitness 1.000 con p = c = 128 (l.153). | S18 |
| `MC/P2_export_Tratamiento/` | Según `MC/LEEME.txt`: `Problema_2.R` (R base y `rpart`), `Problema_2.xlsx` y `salidas/`. Vista minable de 303 × 10 y bitácora P0–P13 en `RESP` p.7–8. | S1 |
| `MC/P3_gastank_Arbol/` | `Problema_3.R` (ID3 programado; `rpart` con Gini y con información; `ctree`). `Problema_3.xlsx`, con las hojas Resumen, Raiz, Modelo, Nivel2, Arbol_ID3, Comparacion y Datos (COUNTIFS y SUMPRODUCT con LOG base 2). `reporte_P3.txt`: 12 hojas y 86.70 % (l.73–74); `rpart` y `ctree` 84.67 % (l.130, l.173). | S7; §1.4 |
