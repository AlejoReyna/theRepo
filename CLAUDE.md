# TSCI3 — Preparación y resolución agéntica de Minería de Datos

Lee `AGENTS.md`: contiene las rutas (`T`, `SK`, `PY`), los datos fijos del alumno (`1851265`, `Amarillo`, `N4`), las reglas académicas (`R1–R3`), las discrepancias (`T1–T29`) y el contrato de verificación vigentes en este proyecto.

- Para preparar una actividad (`AF1`–`AF4`, `MC`) o un examen nuevo sin sobrescribir `incisos/`:
  `python3 preparar_actividad.py --actividad <AF1|AF2|AF3|AF4|MC> --nombre <sesion>` o `python3 preparar_actividad.py /ruta/al/enunciado.pdf --nombre <sesion>`.
- Usa la skill coordinadora `skills_tsci3/skills/tsci3-resolver-actividad/SKILL.md`, las 18 skills de cálculo (`S1–S18`) y `tsci3-entrega-final`.
- Para correr la batería completa de validación del sistema: `/Users/alexis/theCode/newSkills/TSCI3/.venv/bin/python skills_tsci3/validacion/validar_todo.py`.
