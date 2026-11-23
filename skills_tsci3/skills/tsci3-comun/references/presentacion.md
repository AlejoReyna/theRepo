# Presentación

## 1. Excel del ejercicio de clase (`Demostración.xlsx`)

- **Orden de hojas** (plantilla `EF/1851265_TSOER2.zip`, `Demostración.xlsx` de P1–P4): Resultado, Datos, una hoja por paso o nivel, Control.
- **Fórmulas vivas.** Cada resultado es una fórmula que apunta a sus celdas de origen; al hacer clic se ve la operación. Los conteos salen de COUNTIFS o SUMPRODUCT sobre la hoja Datos, no de números tecleados. Así lo entregó el medio curso (`MC/LEEME.txt`), sin observación.
- **Colores** (`MC/LEEME.txt`; hoja Resumen de `MC/P3_gastank_Arbol/Problema_3.xlsx`, A16:A19): azul = dato de entrada o resultado copiado de otro programa; negro = fórmula de la hoja; verde = fórmula que trae datos de otra hoja.
- **Control:** compara las cifras clave del Excel con `traza.json` (columna «Traza», columna «Excel», columna «¿Coincide?» con fórmula).
- Si el profesor tiene un Excel de clase del método, se copia su convención de filas y columnas (por ejemplo `OD/mochila_.xlsx` para k-means). La skill lo dice.
- `openpyxl` escribe fórmulas, pero no calcula sus valores. Para que el Excel abra con valores en caché, se recalcula con LibreOffice (`soffice --headless --convert-to xlsx`) y la hoja Control se lee de vuelta.

## 2. Desarrollo (lo que va al PDF)

1. Asignación por matrícula, si el enunciado la usa (`reglas-academicas.md` R3).
2. Datos y preparación: qué se leyó, cuántas filas, qué se recodificó y por qué (con su T).
3. Fórmulas del método con su cita, y una sustitución completa a mano.
4. Cada paso o nivel completo, con su tabla (R2).
5. Resultado del método pedido; las objeciones de la literatura, después y como comentario (R1).
6. Comparación con R, si se pide.
7. Comprobación: oráculo, R y caso de referencia.

## 3. Código

- `resolver.py` en Python estándar, con encabezado: problema, datos, método con cita, cómo ejecutar. Las secciones del cálculo llevan el nombre del paso del desarrollo.
- `script.R` con la estructura del script del curso, si existe; si no, comentado por paso. Se ejecuta con `Rscript` y su salida completa va a `salida_R.txt`.
- En la entrega, el código va en la sección «Código Funciones que hicieron los cálculos» (plantilla), con bloques «Código Python» y «Código R».
