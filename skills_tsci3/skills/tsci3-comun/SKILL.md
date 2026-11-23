---
name: tsci3-comun
description: Referencias y utilidades compartidas por las skills tsci3-* del curso Tópicos Selectos de Ciencias de la Ingeniería III (UANL, FIME; minería de datos en R). Contiene las reglas académicas sacadas de la calificación del medio curso, las rúbricas AF1–AF4, el contrato de verificación, el índice de fuentes con páginas, las discrepancias T1–T27 y las reglas de presentación. Cárgala cuando otra skill tsci3-* la cite; por sí sola no resuelve ejercicios.
---

# Base común de las skills TSCI3

No resuelve un método: concentra lo que comparten las skills `tsci3-*`.

Raíz del proyecto: `T=/Users/alexis/theCode/newSkills/TSCI3`. Python del proyecto: `$T/.venv/bin/python` (trae `openpyxl`, `python-docx` y `pymupdf`). Kit: `$T/kit_tsci3/kit.py`.

## Referencias (lee solo la que necesites)

| Archivo | Cuándo leerlo |
|---|---|
| [references/reglas-academicas.md](references/reglas-academicas.md) | **Siempre**, antes de resolver: R1–R3 de la calificación del medio curso y la asignación por matrícula. |
| [references/verificacion.md](references/verificacion.md) | Antes de dar por buena una solución: contrato de archivos y las cuatro comparaciones. |
| [references/presentacion.md](references/presentacion.md) | Al armar el Excel, el código y el texto del desarrollo. |
| [references/rubricas.md](references/rubricas.md) | Para saber qué columnas califica cada elemento (AF1–AF4) y cuánto pesa. |
| [references/fuentes.md](references/fuentes.md) | Para citar archivo y página. |
| [references/discrepancias.md](references/discrepancias.md) | Cuando un dato, un Excel del profesor o una lámina no coincida con otro (T1–T27). |

## Herramientas del proyecto

- `$T/herramientas/comprobar_citas.py DOC.md`: cada ruta citada existe y cada «p.N» / «l.N» está en rango.
- `$T/herramientas/manifiesto.py --comprobar`: las copias de `fuentes/` no cambiaron (SHA-256).
- `$T/kit_tsci3/kit.py -h`: comandos del kit.

Desde otra skill, estas referencias están en `../tsci3-comun/references/`.
