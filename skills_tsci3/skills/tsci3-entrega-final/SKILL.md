---
name: tsci3-entrega-final
description: Arma la entrega de TSCI3 (actividad AF o examen) con el formato de la entrega de Endgame (EF/1851265_TSOER2.zip): carpeta Parte_práctica/P<n>_<Método> con Procedimientos.pdf (carta horizontal, encabezado UANL/FIME con logotipos, tabla de datos, cinco cajas del procedimiento, fuentes, un paso por página, código Python y R, comprobación), Demostración.xlsx, código, datos y traza; Parte_teórica.pdf opcional; ZIP con el nombre «Matrícula + Color, Hora, #Tarea» (1851265_Amarillo_N4_<tarea>). No recalcula nada: exige los archivos del contrato, reproduce la traza con resolver.py y coteja las cifras clave del PDF con la traza. Úsala solo cuando cada elemento ya está resuelto y verificado (después de tsci3-resolver-actividad).
---

# Entrega final de TSCI3

`T=/Users/alexis/theCode/newSkills/TSCI3`; `SC=$T/skills_tsci3/skills/tsci3-entrega-final/scripts`; Python: `$T/.venv/bin/python`.

## Antes de empezar
Cada problema debe tener en `incisos/<id>/` los archivos del contrato (`tsci3-comun/references/verificacion.md`):
- `traza.json` y `Demostración.xlsx` recalculado;
- `codigo/resolver.py`, `codigo/script.R` y `salida_R.txt`;
- `bloque.json`;
- `verificacion.md` con la línea `Estado: aprobado`.

Si falta alguno, el programa se detiene con el código 2 y los lista. En ese caso hay que terminar el elemento en su sesión. Esta skill no completa nada.

## Ejecutar
1. Escribe `entrega.json` con el esquema de [references/entrega.md](references/entrega.md):
   - grupo Amarillo, hora N4 y la `tarea` (AF3, AF4, MC, ORD…);
   - los problemas en el orden del enunciado;
   - la `teoria`, si el examen la tiene.
2. `$T/.venv/bin/python $SC/construir_entrega.py entrega.json <carpeta de salida>`. Hace esto:
   - corre `codigo/resolver.py` en una copia temporal y exige una traza idéntica;
   - revisa que la hoja Control del Excel no tenga «NO»;
   - arma `Procedimientos.docx` sobre una copia de `EF/editables/P4_Mochila.docx`, clonando el encabezado con los logotipos, la tabla de datos y los títulos;
   - lo convierte a PDF con LibreOffice y comprueba cada `numeros_clave` contra la traza y contra el texto del PDF;
   - si hay `teoria`, arma `Parte_teórica.pdf` y su `.docx` a partir de la copia en `assets/teoria_base.docx`;
   - comprime `<nombre>.zip`.
3. Mira las páginas renderizadas (p.1, un paso, el código y la comprobación) antes de entregar.

Códigos de salida:
- 0: ZIP listo;
- 2: faltan archivos, color, hora o tarea;
- 3: una comprobación falló. No se comprime y no se corrige a mano: se vuelve a la sesión del elemento.

## Qué no hace
No recalcula, no elige método, no limpia datos y no redacta teoría que no venga en `entrega.json`. Tampoco modifica la plantilla original (EG/AGENTS.md).

## Diferencias declaradas con la plantilla
- La carpeta raíz se llama como el ZIP (por ejemplo, 1851265_Amarillo_N4_AF3), no `1851265_Entrega_final`, porque la regla de p.4 nombra la entrega completa.
- Cada problema lleva además `codigo/script.R` y `salida_R.txt`, porque las rúbricas de TSCI3 califican el script R.
- `Demostración.xlsx` es el del inciso tal cual, con las hojas de su skill y la hoja Control. No se reordena.
- Las cinco cajas se dibujan con Graphviz con las mismas proporciones; la plantilla las trae como imagen.

## Prueba
`$T/.venv/bin/python $T/skills_tsci3/skills/tsci3-entrega-final/pruebas/test_entrega.py`. Antes hay que correr `pruebas/bloques_prueba.py`, que escribe `bloque.json` y `verificacion.md` de KM-dolly y AP-clase a partir de sus trazas y de los oráculos.

Resultado: 11/11.
- **Caso completo:** el árbol coincide con el de la plantilla salvo los nombres. Procedimientos sale en carta horizontal (27 y 9 páginas) con el encabezado, los logotipos y las cajas; la teoría sale vertical. Las dos trazas se reproducen.
- **Casos que deben fallar:** sin color da 2; un inciso incompleto (RM-br) da 2 con la lista de faltantes; una cifra clave alterada da 3 y una traza alterada da 3.
