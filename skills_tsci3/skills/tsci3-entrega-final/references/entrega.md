# entrega.json y bloque.json

## entrega.json

```json
{
 "alumno": {"nombre": "Alexis Alberto Reyna Sánchez", "matricula": "1851265"},
 "color": "Amarillo", "hora": "N4", "tarea": "AF3",
 "formato_nombre": "{matricula}_{color}_{hora}_{tarea}",
 "fecha": "13 de noviembre de 2026",
 "problemas": [{"n": 1, "inciso": "/Users/alexis/theCode/newSkills/TSCI3/incisos/KM-dolly"}],
 "teoria": {"titulo": "Examen Ordinario", "preguntas": [{"pregunta": "…", "respuesta": ["párrafo"], "vinetas": ["…"]}]}
}
```

- `color`, `hora` y `tarea` son obligatorios. El grupo es Amarillo, N4. La regla de `OD/AD26 TSCI3 CO PC.pdf` p.4 es «Nombre: Matrícula + Color,Hora,#Tarea» y no fija separadores. Por omisión se usa `_` (1851265_Amarillo_N4_AF3). Si el profesor usa otro formato, se cambia `formato_nombre`.
- `tarea`: el número de la actividad o del examen, por ejemplo AF3, AF4, MC u ORD.
- `problemas[].argumentos` (opcional): argumentos para `codigo/resolver.py` al reproducir. En AF4 no hay un «Programa» calificado y el programa en Python es el verificador de la skill (`verificar_*.py INCISO`). Se copia como `codigo/resolver.py` y se usa `"argumentos": ["."]`, porque se ejecuta desde la copia del inciso.
- `teoria` es opcional. Las AF no la llevan. Si no viene, no se generan `Parte_teórica.pdf` ni `Por si acaso/`.
- Materia y docente son fijos (T12). Se pueden cambiar con `materia` y `docente`.

## bloque.json (lo escribe la sesión de cada elemento; contrato de `tsci3-comun/references/verificacion.md` §3)

| Campo | Qué es | Dónde sale en el PDF |
|---|---|---|
| `metodo` | nombre de la carpeta `P<n>_<metodo>` | — |
| `titulo`, `enunciado` («Se pide …»), `personal` (opcional) | títulos y párrafos de la p.1 | p.1 |
| `asignacion` (opcional) | tabla de R3 «Regla del enunciado \| Condición \| Aplicación» | p.1, antes de los datos |
| `datos` | filas de 4 columnas: Dato \| Valor \| Dato \| Valor (la primera es el encabezado) | p.1 |
| `cajas` | 5 × {titulo, texto, cita}: la cita es el número de `fuentes` | imagen «Procedimiento de resolución» |
| `fuentes` | lista de citas «archivo, página o celdas» | «Fuentes del curso» [1], [2], … |
| `convencion` (opcional) | párrafo «Convención del desarrollo» | p.1 |
| `pasos` | [{titulo «Paso N …», texto (párrafos separados por línea en blanco), formulas, tablas (lista de filas o {titulo, filas, nota}), notas}] | una página por paso; las tablas siguen en la página siguiente con su encabezado |
| `codigo` | {"python": [{"archivo", "funciones": [...]} o {"archivo", "lineas": [a, b]}], "r": [{"archivo", "lineas": [a, b]}]} | «Código Funciones que hicieron los cálculos» |
| `codigo_texto` (opcional) | párrafo bajo el título del código | — |
| `comprobacion`, `comprobacion_titulo`, `respuesta` | contraste con el oráculo y con R; respuesta final | última página |
| `numeros_clave` | [{"texto": "35.5099", "traza": "resumen.suma_dmin"}] | se comprueban contra la traza y el PDF |
| `anexos` (opcional) | figuras u otros archivos del inciso que se copian a la carpeta del problema | — |

Toda cifra de `bloque.json` sale de `traza.json` o de `salida_R.txt`. `pruebas/bloques_prueba.py` muestra cómo armarlo con código, sin teclear números. El desarrollo no menciona el kit, sellos ni ✅/❌ (regla de Endgame).
