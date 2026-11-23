# TSCI3 — Sistema Agéntico de Tópicos Selectos de Ciencias de la Ingeniería III

Lee `README.md`. Define `T` como la ruta absoluta de esta carpeta (`/Users/alexis/theCode/newSkills/TSCI3`); no dependas de rutas relativas fuera de este repositorio.

- **Kit y oráculos independientes:** `$T/kit_tsci3/kit.py` y `$T/kit_tsci3/tsci3/`. Solo usa la biblioteca estándar de Python 3.
- **Entorno Python para Excel y documentos (`.xlsx`, `.docx`, `.pdf`):** `PY=$T/.venv/bin/python` (`openpyxl`, `python-docx`, `pymupdf`), más LibreOffice (`soffice --headless`), Graphviz (`dot`) y `Rscript` (R 4.6.2).
- **Skills prioritarias:** `SK=$T/skills_tsci3/skills` (enlazadas también en `$T/.agents/skills/` y `$T/.claude/skills/` para autodescubrimiento).
- **Coordinación:** `$SK/tsci3-resolver-actividad/SKILL.md` (`asignar.py` y `seleccionar.py`).
- **Empaquetado final:** `$SK/tsci3-entrega-final/SKILL.md` (`construir_entrega.py`).
- **Base común obligatoria:** `$SK/tsci3-comun/references/` (`reglas-academicas.md`, `verificacion.md`, `rubricas.md`, `discrepancias.md`, `presentacion.md`, `fuentes.md`).
- **Fuentes inmutables:** `$T/fuentes/` (con hash SHA-256 en `$T/fuentes/MANIFIESTO.tsv`; comprueba con `python3 $T/herramientas/manifiesto.py --comprobar`). No modifiques ningún archivo dentro de `fuentes/` ni de `plantilla_entrega/`.
- **Casos de referencia resueltos:** `$T/incisos/` (26 casos verificados de clase y medio curso). Conserva `$T/incisos/` como referencia y línea base; cuando resuelvas una actividad o examen nuevo, trabaja dentro de `$T/actividades/<nombre>/incisos/`.

## Datos fijos del alumno y nomenclatura de entrega

- **Alumno:** Alexis Alberto Reyna Sánchez
- **Matrícula:** `1851265` (impar, termina en `5`)
- **Grupo / Color:** `Amarillo`
- **Hora:** `N4`
- **Materia:** `Tópicos Selectos de Ciencias de la Ingeniería III` (`EX-MC`; `OD/AD26 TSCI3 CO PC.pdf` p.1; `T12`)
- **Docente:** `Dr. Raymundo Said Zamora Pequeño` (`EF/editables/P4_Mochila.docx` l.5; `T12`)
- **Nombre obligatorio del ZIP (`OD/AD26 TSCI3 CO PC.pdf` p.4):** `1851265_Amarillo_N4_<Tarea>.zip` (p. ej. `1851265_Amarillo_N4_AF1.zip`, `1851265_Amarillo_N4_AF3.zip`, `1851265_Amarillo_N4_ORD.zip`).

## Reglas académicas innegociables (`reglas-academicas.md`)

1. **R1 (Todos los atributos):** El método nombrado se aplica a **todos** los atributos del dataset (`Tipo ~ .`). Ningún atributo se excluye por «sesgo de ID3» o «alta cardinalidad» (omitir `Model Name` costó puntos en el medio curso: `fuentes/retroalimentacion_MC.md`). La objeción teórica va como comentario *después* del resultado. Única excepción: una columna clave con un valor distinto en *cada* fila (como `OBJECTID`): calcula su medida, deténte y pregunta al usuario.
2. **R2 (Todos los niveles o iteraciones):** Se calcula y se muestra cada nivel (árboles, Apriori) o iteración (k-means, k-medoides) completo, con una hoja de Excel por nivel/iteración y fórmulas vivas (`COUNTIFS`, `SUMPRODUCT`, `LINEST`, `MMULT/MINVERSE`).
3. **R3 (Asignación por matrícula antes de resolver):** Si el enunciado asigna registro, diagrama, $k$, soporte o semilla por matrícula, abre el desarrollo con la tabla `Regla del enunciado | Condición | Aplicación`.

## Flujo para resolver una actividad (AF1–AF4) o un examen nuevo

1. **Preparar la sesión:**
   ```bash
   python3 preparar_actividad.py --actividad AF3 --nombre AF3
   # O con archivos nuevos de enunciado/datos:
   python3 preparar_actividad.py /ruta/al/enunciado.pdf /ruta/a/datos.csv --nombre Ordinario
   ```
2. **Coordinar (`tsci3-resolver-actividad`):**
   - Lee el `PROMPT.md` generado en `A=$T/actividades/<nombre>/`.
   - Ejecuta `python3 $SK/tsci3-resolver-actividad/scripts/asignar.py 1851265` (si aplica `R3`) y `python3 $SK/tsci3-resolver-actividad/scripts/seleccionar.py "<texto del elemento>"`.
   - Genera un prompt autocontenido por elemento en `$A/prompts/<id>.md` e `$A/prompts/indice.md`.
3. **Ejecutar cada inciso (`$A/incisos/<id>/`):**
   - Puedes delegar los incisos en paralelo a subagentes (cada subagente escribe únicamente en `$A/incisos/<id>/`).
   - Cada inciso debe dejar los archivos del contrato (`verificacion.md` §1): `traza.json`, `Demostración.xlsx` (recalculado con `$PY $SK/tsci3-comun/scripts/recalcular_excel.py` y 0 «NO» en la hoja `Control`), `codigo/resolver.py`, `codigo/script.R` y `salida_R.txt` (salvo métodos sin R como `S18`), `bloque.json` y `verificacion.md` con `Estado: aprobado` y `comprobar_citas.py` en 0 errores.
4. **Construir la entrega final (`tsci3-entrega-final`):**
   - Escribe `$A/entrega.json` uniendo los problemas en orden (y `teoria` si aplica).
   - Ejecuta `$PY $SK/tsci3-entrega-final/scripts/construir_entrega.py $A/entrega.json $A/entrega`.
   - Verifica visualmente las páginas renderizadas del PDF antes de dar por terminada la entrega.
