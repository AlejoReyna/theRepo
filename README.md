# TSCI3 — Minería de Datos (UANL FIME)

Sistema agéntico de skills, oráculos independientes y empaquetado reproducible para **Tópicos Selectos de Ciencias de la Ingeniería III**.

---

## Para humanos

### Requisitos
- **Python 3** con entorno `.venv/` (`openpyxl`, `python-docx`, `pymupdf`)
- **R (`Rscript`)**, **LibreOffice (`soffice`)** y **Graphviz (`dot`)** en el `PATH`
- Ver instalación detallada en [`skills_tsci3/INSTALACION.md`](skills_tsci3/INSTALACION.md)

### Uso rápido
1. **Preparar una sesión** (actividad AF1–AF4, medio curso o archivos nuevos):
   ```bash
   python3 preparar_actividad.py --actividad AF3 --nombre AF3
   # O con enunciado/datos nuevos:
   python3 preparar_actividad.py /ruta/enunciado.pdf /ruta/datos.csv --nombre Ordinario
   ```
2. **Abrir una sesión agéntica** en la carpeta creada (`actividades/<nombre>/`) y pasarle su `PROMPT.md`.
3. **Validar el repositorio completo** (integridad de fuentes, citas, pruebas, oráculos y Excel):
   ```bash
   .venv/bin/python skills_tsci3/validacion/validar_todo.py
   ```
4. **Entrega final:** el empaquetador genera `1851265_Amarillo_N4_<Tarea>.zip` dentro de `actividades/<nombre>/entrega/`.

---

## Para agentes (contexto y navegación)

Lee primero [`AGENTS.md`](AGENTS.md) (o [`CLAUDE.md`](CLAUDE.md)): define rutas canónicas (`T`, `SK`, `PY`), datos del alumno y reglas obligatorias.

### Mapa del repositorio
| Ruta | Qué contiene |
|---|---|
| `AGENTS.md` / `CLAUDE.md` | Reglas operativas, datos del alumno y flujo oficial |
| `skills_tsci3/skills/` | 21 skills (`tsci3-comun`, coordinadora, entrega y S1–S18), enlazadas en `.agents/skills/` y `.claude/skills/` |
| `skills_tsci3/MATRIZ_SKILLS.md` | Cobertura AF1–AF4 y casos de referencia por skill |
| `kit_tsci3/` | Oráculos independientes en biblioteca estándar (`kit.py`, `tsci3/`) |
| `incisos/` | 26 casos de referencia verificados (no sobrescribir al resolver tareas nuevas) |
| `actividades/<nombre>/` | Espacio de trabajo aislado por actividad/examen (`PROMPT.md`, `prompts/`, `incisos/`, `entrega/`) |
| `fuentes/` y `plantilla_entrega/` | **Inmutables.** Material del curso (verificado por SHA-256) y plantilla de entrega |

### Cómo moverse (flujo en 4 pasos)
1. **Coordinar:** usa `tsci3-resolver-actividad` (`asignar.py 1851265` para `R3` y `seleccionar.py "<elemento>"` para mapear cada tema a su skill).
2. **Resolver por inciso:** trabaja en `actividades/<nombre>/incisos/<id>/` siguiendo la skill asignada y las referencias de `tsci3-comun/references/`.
3. **Verificar cada inciso:** deja `traza.json`, `Demostración.xlsx` recalculado (`recalcular_excel.py`, 0 `NO` en `Control`), `codigo/resolver.py`, `codigo/script.R`, `salida_R.txt` (salvo métodos sin R), `bloque.json` y `verificacion.md` (`Estado: aprobado`).
4. **Empaquetar:** arma `actividades/<nombre>/entrega.json` y corre `tsci3-entrega-final/scripts/construir_entrega.py`.

### Reglas críticas
- **R1:** aplica el método a **todos** los atributos del dataset (no excluyas columnas por sesgo o cardinalidad).
- **R2:** muestra **todos** los niveles o iteraciones, con fórmulas vivas en Excel.
- **R3:** aplica primero la asignación por matrícula (`1851265`, impar, termina en `5`) cuando exista.
- **Inmutabilidad:** nunca modifiques `fuentes/` ni `plantilla_entrega/`.
