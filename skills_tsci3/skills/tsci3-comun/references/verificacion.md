# Contrato de verificación (S1–S18)

## 1. Archivos que deja cada skill en `incisos/<id>/`

| Archivo | Qué es | Columna de rúbrica |
|---|---|---|
| `Demostración.xlsx` | Ejercicio de clase con fórmulas vivas; hojas Resultado, Datos, una por paso o nivel, Control (`presentacion.md` §1) | Ejercicio de clase |
| `codigo/resolver.py` | «Programa» en Python estándar (sin numpy); lee `datos/` y escribe `traza.json` | Programa |
| `traza.json` | Todos los números del desarrollo, por paso o nivel | — |
| `codigo/script.R` | «Script R» con la estructura del script del curso | Script R |
| `salida_R.txt` | Salida de `Rscript codigo/script.R` | Ejercicio en R |
| `bloque.json` | Contenido del problema para la entrega (§3) | — |
| `verificacion.md` | Registro de las comparaciones de §2 | — |

`datos/` guarda la entrada tal como se usó (CSV o JSON) y `parametros.json`.

## 2. Las cuatro comparaciones (todas obligatorias)

1. **Oráculo contra traza.** `$T/kit_tsci3/kit.py <comando> --oraculo` recalcula por otro camino (fracciones exactas, conteo directo) y compara con `traza.json`. Diferencia = no se entrega.
2. **Traza contra R.** Las cifras que R también produce se comparan con la tolerancia declarada en la skill (por omisión 1e−6 absoluto). Si R decide distinto (otra raíz, otro k), se explica en `verificacion.md`; no se cambia la traza para que coincida.
3. **Caso de referencia de la fuente.** El caso de la sección «Casos» de la skill reproduce sus cifras.
4. **Mutante.** Un error sembrado (el de la skill) debe hacer fallar la comparación 1 o 3.

Además, antes de dar por buena una solución:

- **R1:** la lista de atributos o columnas de la traza, del Excel y de `script.R` es la misma y no excluye nada sin la pregunta al usuario de `reglas-academicas.md`.
- **R2:** cada nivel o iteración de la traza tiene su hoja en el Excel.
- **R3:** si el enunciado asigna por matrícula, `bloque.json` trae la tabla de asignación.
- `python3 $T/herramientas/comprobar_citas.py verificacion.md` sin errores.

## 3. `bloque.json`

```json
{
  "id": "MC-P3",
  "metodo": "Arbol",                      
  "titulo": "Árbol de decisión de mínima entropía",
  "enunciado": "Se pide …",
  "asignacion": [["Regla", "Condición", "Aplicación"], ["…", "…", "…"]],
  "datos": [["Dato", "Valor", "Dato", "Valor"], ["…", "…", "…", "…"]],
  "cajas": [{"titulo": "…", "texto": "…", "cita": 1}],
  "fuentes": ["EJ26-14 p.3, ecs. 2.1–2.3", "…"],
  "pasos": [{"titulo": "Paso 1 …", "texto": "…", "formulas": ["…"], "tablas": [[["…"]]]}],
  "codigo": {"python": ["codigo/resolver.py"], "r": ["codigo/script.R"]},
  "comprobacion": "…",
  "respuesta": "…"
}
```

`cajas` tiene cinco elementos (plantilla: «Procedimiento de resolución», `EF/1851265_TSOER2.zip`). La skill de entrega copia estos textos y cifras; no recalcula.

## 4. `verificacion.md` del inciso

Para cada comparación: comando, resultado (✅ o la diferencia), y lo que quedó sin verificar. Al final: supuestos, discrepancias T aplicadas y semillas.
