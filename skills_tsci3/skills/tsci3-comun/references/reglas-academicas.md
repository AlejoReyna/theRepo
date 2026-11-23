# Reglas académicas

Salen de calificaciones reales, no de preferencias. Si un caso no está cubierto, aplica la regla general y declara la duda en `verificacion.md`.

## Regla general (Endgame, confirmada en TSCI3)

Se califica el **procedimiento visible del método que se pide**. En TSO, la Regularización 1 obtuvo 45/100 y un problema recibió 0 con «No muestra el ordenamiento requerido para el método constructivo» (`EG/kit_tso/GUIA_DESARROLLO.md` §1). En TSCI3 el medio curso lo confirmó (R1, R2).

## Calificación del medio curso AD26 (`fuentes/retroalimentacion_MC.md`)

«1. +20. 2. +15. 3. +8. Omitió Model Name y el cálculo por niveles.» El enunciado (`EX-MC`) no publica el máximo por problema: «sin observación» no significa puntaje completo.

| Problema | Puntos | Observación | Lo que se conserva |
|---|---|---|---|
| 1, REGEVEN (U.T.2) | +20 | ninguna | Estructura de `tsci3-modelado-procesos` (`RESP` p.2–6) |
| 2, export (U.T.1) | +15 | ninguna | Estructura de tratamiento con objetivo de `tsci3-subset-r` (`RESP` p.7–11) |
| 3, gastank (U.T.3) | +8 | «Omitió Model Name y el cálculo por niveles» | R1 y R2 |

### R1. El método nombrado se aplica a todos los atributos del dataset

- Ningún atributo se excluye porque «no conviene» (casi identificador, sesgo de ID3, poca relación). Se calcula con él.
- La objeción de la literatura va como **comentario después del resultado**, nunca como exclusión.
- Los modelos de R usan la misma lista de atributos que el cálculo a mano (`Tipo ~ .`).
- Única excepción: un atributo con un valor distinto en **cada** fila (una clave de registro como OBJECTID). Calcula su medida, deténte y pregunta al usuario antes de usarlo o quitarlo.
- Caso que lo originó: `MC/P3_gastank_Arbol/Problema_3.R` l.234 y l.253 usan `Tipo ~ Ventilacion + Combustible`; la hoja `Modelo` calculó E(Model Name) = 0.0227, la menor, y aun así lo excluyó.

### R2. Los métodos iterativos se muestran por niveles (o iteraciones) completos

- Árboles: en cada nivel, cada nodo impuro lleva la tabla por valor de **cada** atributo candidato (n, conteo por clase, H, peso, aporte), E(A) y ganancia, hasta que el nodo sea puro, la ganancia sea 0 o no queden atributos. Una hoja de Excel por nivel.
- Lo mismo vale, por analogía, para k-means y k-medoides (una hoja por iteración) y Apriori (un nivel por tamaño de itemset). Ningún nivel se resume con «y así sucesivamente».

### R3. La asignación por matrícula se resuelve antes que el problema

- El medio curso asignó registro, diagrama y modelo por el último dígito y la paridad (`EX-MC`, problema 1).
- Se abre el desarrollo con la tabla «Regla del enunciado | Condición | Aplicación» (`RESP` p.2) y se aplica tal cual. Matrícula del alumno: 1851265 (termina en 5, impar).

## Otras reglas de trabajo

- **El método sale de las fuentes.** Cada fórmula y cada decisión lleva cita (archivo y página). Si la fuente no da el método, la skill lo declara (estado VL o P) y no inventa.
- **Una sola respuesta.** Si hay dos lecturas posibles de un enunciado o de una lámina (ver `discrepancias.md`), se resuelve con la que dice el enunciado; la otra va en `verificacion.md`, no en la entrega.
- **Semillas.** Todo lo aleatorio lleva semilla declarada (T15).
- **Nada se presenta como óptimo** salvo que el enunciado lo pida y un exacto lo confirme.
