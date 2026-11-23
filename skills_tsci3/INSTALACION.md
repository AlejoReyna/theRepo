# Instalación e invocación de las skills de TSCI3

En `TSCI3` puedes usar directamente las 20 skills locales sin instalarlas fuera del repositorio:
- Ruta canónica: `SK=$T/skills_tsci3/skills` (con `T=/Users/alexis/theCode/newSkills/TSCI3`).
- Autodescubrimiento local en el workspace: están enlazadas en `$T/.agents/skills/tsci3-*` y `$T/.claude/skills/tsci3-*`.

## Contenido (20 skills)

- **Coordinadora:** `tsci3-resolver-actividad` (`scripts/asignar.py`, `scripts/seleccionar.py`, `references/prompt-elemento.md`).
- **Base común:** `tsci3-comun` (`references/reglas-academicas.md`, `verificacion.md`, `rubricas.md`, `discrepancias.md`, `presentacion.md`, `fuentes.md`; `scripts/recalcular_excel.py`, `scripts/comparar_traza_r.py`).
- **Entrega final:** `tsci3-entrega-final` (`scripts/construir_entrega.py`, `docx_tsci3.py`, `cajas.py`, `teoria.py`).
- **17 skills de cálculo y validación con R + 1 de procesos (S1–S18):**
  - `S1` `tsci3-subset-r`
  - `S2` `tsci3-kmeans`
  - `S3` `tsci3-kmedoides`
  - `S4` `tsci3-apriori`
  - `S5` `tsci3-secuencias`
  - `S6` `tsci3-episodios`
  - `S7` `tsci3-arbol-decision`
  - `S8` `tsci3-minimos-cuadrados`
  - `S9` `tsci3-breusch-pagan`
  - `S10` `tsci3-predictor-binario`
  - `S11` `tsci3-regresion-multiple`
  - `S12` `tsci3-stepwise-aic`
  - `S13` `tsci3-regularizacion`
  - `S14` `tsci3-regresion-logistica`
  - `S15` `tsci3-matriz-confusion`
  - `S16` `tsci3-knn`
  - `S17` `tsci3-bosque-aleatorio`
  - `S18` `tsci3-modelado-procesos`

## Instalación personal opcional (fuera del workspace)

Para Claude Code (`~/.claude/skills/`):
```bash
mkdir -p ~/.claude/skills && ln -sfn /Users/alexis/theCode/newSkills/TSCI3/skills_tsci3/skills/tsci3-* ~/.claude/skills/
```

Para Codex (`~/.codex/skills/`):
```bash
mkdir -p ~/.codex/skills && ln -sfn /Users/alexis/theCode/newSkills/TSCI3/skills_tsci3/skills/tsci3-* ~/.codex/skills/
```

## Preparar una sesión de actividad o examen

```bash
cd /Users/alexis/theCode/newSkills/TSCI3
python3 preparar_actividad.py --actividad AF3 --nombre AF3
# O con archivos adicionales conseguidos por el alumno:
python3 preparar_actividad.py /ruta/a/instrucciones_AF1.pdf --actividad AF1 --nombre AF1_entrega
```

Esto crea `actividades/<nombre>/` con `enunciado/`, `datos/`, `prompts/`, `incisos/`, `entrega/`, `AGENTS.md`, `CLAUDE.md`, `PROMPT.md` y `verificacion.md`.

## Validar todo el sistema

```bash
/Users/alexis/theCode/newSkills/TSCI3/.venv/bin/python /Users/alexis/theCode/newSkills/TSCI3/skills_tsci3/validacion/validar_todo.py
```
