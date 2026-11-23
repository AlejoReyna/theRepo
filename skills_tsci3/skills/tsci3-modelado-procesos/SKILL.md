---
name: tsci3-modelado-procesos
description: A partir de un registro de eventos (REGEVEN u otro con Case id, Timestamp, Activity, Resource, Cost) obtiene trazas, variantes, relación directamente-seguido, footprint α y dependencias del Heuristics Miner; deriva con evidencia el árbol de proceso y la red de Petri (red WF etiquetada), da su denominación verificada (WF, segura, sólida, libre elección) y el ajuste por token replay, y dibuja el BPMN con carriles por recurso. Deja Excel con fórmulas vivas, programa en Python, figuras, PNML y BPMN 2.0. Úsala cuando pidan "red de Petri", "denominación", "BPMN", "árbol de proceso", "registro de eventos", "REGEVEN" (TSCI3 AF2; medio curso problema 1). YAWL, EPC y red causal: sin método en las fuentes (estado P).
---

# Modelado de procesos desde un registro de eventos

Lee antes `../tsci3-comun/references/reglas-academicas.md` (R3: asignación por matrícula) y `../tsci3-comun/references/verificacion.md`.

`T=/Users/alexis/theCode/newSkills/TSCI3`; `SC=$T/skills_tsci3/skills/tsci3-modelado-procesos/scripts`.

## Cuándo aplica / cuándo no
- Aplica: red de Petri y su denominación, BPMN, árbol de proceso a partir de un registro de eventos.
- **Estado P (no resolver sin fuente):** YAWL, EPC/EDPC y red causal. Ninguna fuente del curso muestra su método ni un ejemplo aceptado (`PLAN_TSCI3.md` §7 B2). Si el enunciado los asigna, avisa al usuario antes de dibujarlos.
- Disco, separación en Disco, diagramas de clase o de transición y bupaR: sin fuente (B2).

## Asignación por matrícula (R3)
El medio curso (`EX-MC`, problema 1): registro = último dígito; dígito 0–2 → YAWL, 3–5 → BPMN, 6–9 → EDPC; impar → árbol de proceso, par → red causal. Matrícula 1851265 → **Registro 05, BPMN, árbol de proceso**. Abre el desarrollo con la tabla «Regla | Condición | Aplicación» (`RESP` p.2). Si el enunciado nuevo trae otras reglas, usa las del enunciado.

## Método (respuesta aceptada sin observación, `RESP` p.2–6; `MC/P1_REGEVEN_Procesos/Problema_1.py`)
1. Letra por actividad, en el orden en que aparece en la hoja (para el Registro 05 coincide con la respuesta).
2. Trazas: eventos de cada caso ordenados por timestamp «dd-mm-aaaa:hh.mm» (T17); variantes y registro simplificado L.
3. |x>y|, footprint α (→, ←, ‖, #), dependencia x⇒y = (|x>y| − |y>x|)/(|x>y| + |y>x| + 1) con umbral 0.5 y bucle de longitud 2 x⇒₂y = (|x>>y| + |y>>x|)/(|x>>y| + |y>>x| + 1).
4. Árbol por bloques, cada decisión con su evidencia (el programa la imprime): repetición de una actividad → etiqueta x′; XOR por componentes desconectadas; secuencia por alcanzabilidad; bloque que solo ocurre en parte de los casos → ×(τ, bloque); paralelo si las actividades se siguen en ambos sentidos; bloque opcional que termina repitiendo una actividad → ⟲(τ, →(…, x)) (retrabajo). **Si ninguna regla explica el registro, el programa se detiene**: decide con el usuario.
5. Red WF etiquetada N = (P, T, F, A, l), M₀ = [ini], M_f = [fin]: silenciosas para sincronizar el AND y para omitir opcionales; la división AND se fusiona con la transición visible anterior.
6. Denominación verificada con el grafo de alcanzabilidad: red WF, segura, sólida, libre elección; máquina de estados y grafo marcado. Ajuste ½(1 − m/c) + ½(1 − r/p).
7. BPMN: compuertas + (AND) y ✕ (XOR, «¿Requiere …?»), retrabajo dibujado hacia atrás, carriles = recursos que comparten actividades (matriz actividad × recurso).

## Ejecutar
1. `I=$T/incisos/<id>`; `mkdir -p $I/datos $I/codigo`; copia el registro a `$I/datos/` y `cp $SC/resolver_procesos.py $I/codigo/resolver.py`.
2. `python3 $I/codigo/resolver.py --registro 05 > $I/salida_python.txt` → `traza.json`, `red.dot`, `arbol.dot`, `red.pnml`.
3. Oráculo: `python3 $T/kit_tsci3/kit.py procesos-oraculo $I/datos/REGEVEN.xlsx $I/traza.json` (✅ obligatorio).
4. BPMN: `python3 $SC/bpmn_procesos.py $I` → `bpmn.bpmn` (Camunda Modeler / demo.bpmn.io) y `bpmn.svg`.
5. Figuras: `dot -Tpng -Gdpi=150 red.dot -o red.png` (igual `arbol.dot`); `soffice --headless --convert-to png bpmn.svg`.
6. Excel: `$T/.venv/bin/python $SC/excel_procesos.py $I` y `$T/.venv/bin/python $T/skills_tsci3/skills/tsci3-comun/scripts/recalcular_excel.py $I/Demostración.xlsx` (todas «sí»).

## Procedimiento a mostrar
Asignación por matrícula → registro (eventos, casos, actividades con letra, recursos, costo) → trazas y variantes (L) → matriz |x>y|, footprint y dependencias → tabla «Evidencia en el registro → Conclusión para el modelo» → red N = (P, T, F, A, l) con la tabla de qué representa cada lugar y la figura → denominación con la tabla de propiedades y su justificación → diagrama asignado (BPMN) y sus elementos → árbol de proceso con su correspondencia con la red → tiempo y costo.

## Verificación (contrato)
1. Oráculo: trazas, variantes, |x>y|, dependencias; alcanzabilidad, segura, sólida, WF, libre elección por otro camino; cada traza aceptada por la red; lenguaje de la red = lenguaje del árbol.
2. Sin R en este método: la segunda comparación es el Excel (Control) contra la traza.
3. Caso de referencia: Registro 05 (abajo).
4. Mutante: quitar la silenciosa que omite g → 4 comprobaciones del oráculo fallan.

## Casos de referencia comprobados
- **Registro 05** (MC problema 1, aceptado +20): 91 eventos, 10 casos, 10 actividades, 13 recursos, 6 variantes; |c>>d| = 2, dep₂ = 0.667; árbol →(a, ∧(b, c), ⟲(τ, →(d, c)), e, f, ×(τ, g), h, i, j), 8 trazas con una vuelta; |P| = 13, |T| = 13 (2 silenciosas), |F| = 28; 13 marcas y 15 arcos; WF, segura, sólida, libre elección; fitness 1.000 con p = c = 128; 6 carriles; duración media 10.05 días, costo medio 721. Coincide con `MC/P1_REGEVEN_Procesos/reporte_P1.txt` y `RESP` p.2–6. Oráculo ✅ 14/14; Excel 67/67.
- **Registros 00–04 y 06–09**: mismo proceso con otras letras (06 no tiene «orientación brindada»); los nueve dan red WF sólida con fitness 1.000 y pasan el oráculo.
