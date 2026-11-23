---
name: tsci3-resolver-actividad
description: Coordina la resolución de un examen (medio curso, ordinario, extraordinario) o de una actividad AF1–AF4 de Tópicos Selectos de Ciencias de la Ingeniería III (TSCI3, minería de datos en R, UANL FIME). Resuelve primero la asignación por matrícula (R3), lleva cada problema o elemento de rúbrica a su skill tsci3-* con seleccionar.py, escribe un prompt autocontenido por elemento para sesiones separadas y al final reúne los bloques para tsci3-entrega-final. Úsala cuando pidan resolver un examen o una actividad completa de TSCI3; para un solo método conocido basta la skill especializada.
---

# Resolver una actividad o un examen de TSCI3

`T=/Users/alexis/theCode/newSkills/TSCI3`; `SK=$T/skills_tsci3/skills`; `SC=$SK/tsci3-resolver-actividad/scripts`.

Recorrido: **preparar → asignación por matrícula → elemento → skill → un prompt por elemento → (sesiones) → reunir**. Es el patrón de `Endgame/skills_tso/skills/tso-resolver-examen` §1 y §8. La sesión maestra no resuelve, solo reparte el trabajo.

Antes de empezar, lee `$SK/tsci3-comun/references/reglas-academicas.md` (R1–R3) y `verificacion.md` (contrato de archivos).

## 0. Preparar
1. Crea la carpeta de la actividad `A=$T/actividades/<fecha>_<nombre>/` con `prompts/` e `incisos/`. Guarda ahí el enunciado original (PDF, imagen o texto) y los datos que adjunte.
2. Comprueba el entorno: `which Rscript soffice` y `$T/.venv/bin/python -c "import openpyxl"`.
3. Pide en una sola petición lo que falte: la matrícula si el enunciado la usa (la del alumno es 1851265) y los archivos de datos que no estén. Para la entrega, el grupo es Amarillo y la hora N4 (dados por el usuario el 13/11/2026; B1 resuelto).

## 1. Asignación por matrícula (R3), antes que cualquier problema
- Si el enunciado usa la regla del medio curso, corre `python3 $SC/asignar.py <matrícula>`. Da la tabla «Regla del enunciado | Condición | Aplicación» (`RESP` p.2) y avisa si lo asignado está en estado P (YAWL, EDPC, red causal). Ejemplos: 1851265 → Registro 05, BPMN, árbol de proceso; 1851260 → Registro 00, YAWL, red causal.
- Si la regla es otra, aplica la del enunciado y escribe la tabla a mano con la cuenta.
- La tabla va al principio del prompt y del `bloque.json` del problema que la usa.

## 2. Elemento → skill
`python3 $SC/seleccionar.py "<texto literal del problema o del elemento>"` usa la tabla de `$SK/tsci3-comun/references/rubricas.md`. El código de salida indica qué hacer:
- **0**: una o más skills. Si el problema es un clasificador (KNN, bosque, logística) y pide evaluarlo, agrega **tsci3-matriz-confusion** después.
- **2**: tema sin skill de resolución:
  - AF1 con respuesta redactada;
  - AF2 Disco, Separación Disco, diagramas de clase o de transición, bupaR (B2);
  - temas que solo aparecen en artículos de PIA (B3).

  No inventes el método: díselo al usuario y pregúntale cómo seguir.
- **3**: no se reconoce. Revisa el texto contra `rubricas.md` y pregunta.
- El aviso de estado P lo decide la asignación, no el texto. El enunciado del medio curso menciona YAWL y red causal para todos, pero a 1851265 le tocan BPMN y árbol de proceso.

Junta en una sola pregunta al usuario las ambigüedades que cambian la respuesta. Revisa `discrepancias.md` (T1–T27): por ejemplo, la lectura de Ridge (T3), la orientación de caret (T24) o la normalización (T5).

## 3. Un prompt por elemento
Escribe `$A/prompts/<id>.md` con [references/prompt-elemento.md](references/prompt-elemento.md) y el índice `$A/prompts/indice.md`:

| Prompt | Problema / elemento | Verbo | Método | Skill(s) | Matrícula | Estado |
|---|---|---|---|---|---|---|

Dile al usuario que pegue cada prompt en una sesión nueva. Pueden correr en paralelo, porque cada una escribe en su propia carpeta.

## 4. Reunir
Cuando el usuario avise que las sesiones terminaron:
- Comprueba que cada `incisos/<id>/` tenga los archivos del contrato:
  - `traza.json`, `Demostración.xlsx` recalculado, `codigo/script.R`, `salida_R.txt`, `bloque.json` y `verificacion.md`;
  - `codigo/resolver.py` cuando la rúbrica califica un «Programa» (AF3 y los problemas del examen).

  Lo que falte se termina en la sesión de ese elemento.
- Une los `bloque.json` en el orden del enunciado y pásalos a **tsci3-entrega-final**. La entrega no recalcula nada; nombra el ZIP 1851265_Amarillo_N4_<tarea>.

## 5. Qué reportar
- una línea por elemento, con la respuesta y la skill;
- la asignación por matrícula;
- los supuestos y las lecturas elegidas de cada T;
- lo que no se pudo verificar o quedó en estado P;
- dónde están `prompts/`, `incisos/` y `verificacion.md`.

No prometas calificación.

## Prueba
`python3 $SK/tsci3-resolver-actividad/pruebas/test_coordinadora.py` comprueba tres cosas:
- los 25 temas de `rubricas.md`, con los nombres literales de las rúbricas, van a su skill;
- los 9 temas sin skill dan código 2 y los tres problemas de EX-MC van a su skill;
- la asignación con 1851265 y con 1851260 sale como se espera.

Resultado: 46/46. No es a ciegas: las reglas se escribieron conociendo esos nombres.
