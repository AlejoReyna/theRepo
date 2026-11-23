# Prompt por elemento (TSCI3)

Es la estructura de `Endgame/skills_tso/skills/tso-resolver-examen/references/prompt-inciso.md`, con cinco partes en orden, adaptada a TSCI3. La sesión que recibe el prompt no ve el enunciado ni la conversación de la sesión maestra. Todo lo que necesita va en el prompt o en una ruta absoluta.

## Reglas para llenarlo

- Un archivo por elemento: `$A/prompts/<id>.md`, donde `<id>` es por ejemplo `P1`, `P2` o `AF4-KNN`. Las rutas van absolutas y ya resueltas.
- `<enunciado>`: copia literal del problema o del elemento de rúbrica, con el nombre del archivo de datos tal cual.
- `<matricula>`: la tabla «Regla | Condición | Aplicación» que da `scripts/asignar.py`, o la de la regla del enunciado nuevo. Si no aplica, escribe «no aplica».
- `<interpretacion>`:
  - verbo;
  - método nombrado;
  - skill o skills, según `scripts/seleccionar.py`;
  - entregable;
  - reglas R1–R3 que aplican;
  - discrepancias T que toca, con la lectura elegida.
- El prompt describe la tarea, no la resuelve: no lleva números calculados, salvo la cuenta de la matrícula.

## Plantilla

````markdown
# TSCI3 · {id}

## 1. Rol y tarea
Actúa como especialista en Tópicos Selectos de Ciencias de la Ingeniería III (minería de datos en R, UANL FIME). Resuelve {id} con el método que nombra el enunciado y deja en {A}/incisos/{id}/ el Excel, el script R, la traza, la verificación y el bloque para la entrega.

## 2. Datos
<enunciado>
{texto literal}
</enunciado>

<adjuntos>
{ruta absoluta de cada CSV, XLSX o PDF; hoja o página}
</adjuntos>

<matricula>
{tabla de asignar.py o «no aplica»}
</matricula>

<interpretacion>
- Verbo: {obtenga, compare, analice, proponga y realice…} → la respuesta debe mostrar {…}
- Método nombrado: {…}
- Skill(s), en orden: {tsci3-… → tsci3-matriz-confusion si clasifica}
- Entregable: {…}
- Reglas: R1 (todos los atributos) {sí/no}; R2 (niveles o iteraciones completos) {sí/no}; R3 (asignación) {sí/no}
- Discrepancias y lectura elegida: {T… → …; ninguna}
</interpretacion>

<entorno>
- Proyecto: /Users/alexis/theCode/newSkills/TSCI3 (kit en kit_tsci3/, Python con openpyxl en .venv/bin/python, R con los paquetes del curso).
- Skills: /Users/alexis/theCode/newSkills/TSCI3/skills_tsci3/skills
- Escribe solo en {A}/incisos/{id}/.
</entorno>

## 3. Instrucciones
1. Lee {SK}/tsci3-comun/references/reglas-academicas.md y verificacion.md; carga la skill {skill} y sigue su sección «Ejecutar» completa con {A}/incisos/{id} como inciso.
2. Copia los datos a {A}/incisos/{id}/datos/ sin modificarlos y escribe parametros.json con todo lo que fija el enunciado; lo que no fije (semilla, positiva, etc.) va como supuesto declarado.
3. Script R: parte del script de la skill, conserva la estructura del código del curso y comenta cada desviación con su T.
4. Verificación: la de la skill debe dar ✅ en todo; Excel recalculado con recalcular_excel.py sin «NO» ni errores. Anota las cuatro comparaciones en verificacion.md (contrato §2) y pasa comprobar_citas.py.
5. Escribe bloque.json (contrato §3): enunciado «Se pide …», tabla de datos, cinco cajas con cita, fuentes, un paso por nivel o iteración (R2), código (Python y R), comprobación y respuesta; si hubo asignación, la tabla de R3 al inicio.
6. Si aparece una ambigüedad que cambia la respuesta y no está en <interpretacion>, calcula ambas lecturas y pregúntame mostrando el efecto.
7. No modifiques el kit ni las skills.

## 4. Ejemplo
<ejemplo>
{caso de referencia de la skill (incisos/<caso>) solo para la forma; nunca como respuesta}
</ejemplo>

## 5. Lo crítico
- El método nombrado, con su procedimiento visible; ninguna exclusión de atributos (R1); todos los niveles (R2).
- Las cifras del bloque salen de traza.json y salida_R.txt; nada se escribe a mano.
- Al terminar:

<resumen>
elemento: {id}
respuesta: {una línea con el resultado y sus números}
supuestos: {…}
pendientes: {lo no verificado; «ninguno»}
archivos: {rutas}
</resumen>
````
