#!/usr/bin/env python3
"""Arma Demostración.xlsx del modelado de procesos a partir de traza.json y del registro.

Hojas: Resultado, Datos (registro ordenado por caso y fecha, con letra, siguiente, etc.),
Letras, Casos (trazas, duración y costo), Variantes, Relaciones (|x>y|, footprint,
dependencias, bucles de longitud 2), Recursos, Red, Alcanzabilidad, Replay, Control.
Lo que se cuenta en el registro es fórmula viva (COUNTIFS, MINIFS, SUMIF); la red, sus
marcas y el replay vienen del programa (azul) y se contrastan en Control.

Uso: .venv/bin/python excel_procesos.py INCISO_DIR
"""
import datetime as dt
import json
import os
import sys

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter as L

AZUL, NEGRO, VERDE = Font(color="1F4E9E"), Font(color="000000"), Font(color="1E7B34")
NEGRO_N, VERDE_N = Font(bold=True), Font(color="1E7B34", bold=True)
TITULO = Font(bold=True, size=13)
ENC = PatternFill("solid", fgColor="DDE4EE")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def encabezado(ws, fila, nombres, col=1):
    for j, n in enumerate(nombres):
        c = ws.cell(fila, col + j, n)
        c.font, c.fill = NEGRO_N, ENC


def main():
    I = sys.argv[1]
    tr = json.load(open(os.path.join(I, "traza.json"), encoding="utf-8"))
    from resolver_procesos import leer_registro            # misma lectura del programa
    ruta = os.path.join(I, "datos", tr["archivo"])
    eventos, letras, nombres, casos, trazas = leer_registro(ruta, tr["registro"])
    filas = [ev[3] for caso in casos.values() for ev in caso]          # ya ordenados por caso y fecha
    N = len(filas) + 1
    orden = list(tr["letras"])
    control = []
    wb = Workbook()
    res = wb.active
    res.title = "Resultado"

    # ---------------- Datos
    ws = wb.create_sheet("Datos")
    cols = ["Case id", "Event id", "Timestamp", "Activity", "Resource", "Cost"]
    encabezado(ws, 1, cols + ["Letra", "Fecha", "¿En orden?", "Siguiente", "Siguiente 2", "Traza acumulada", "Inicio", "Fin"])
    for i, f in enumerate(filas, 2):
        for j, c in enumerate(cols, 1):
            ws.cell(i, j, f[c]).font = AZUL
        ws.cell(i, 7, "=VLOOKUP(D%d,Letras!$A$2:$B$%d,2,0)" % (i, len(orden) + 1)).font = VERDE
        ws.cell(i, 8, "=DATE(MID(C{r},7,4),MID(C{r},4,2),LEFT(C{r},2))+TIME(MID(C{r},12,2),MID(C{r},15,2),0)".format(r=i)).font = NEGRO
        ws.cell(i, 8).number_format = "dd/mm/yyyy hh:mm"
        ws.cell(i, 9, '=IF(A{r}<>A{p},"inicio",IF(H{r}>=H{p},"sí","NO"))'.format(r=i, p=i - 1)).font = NEGRO
        ws.cell(i, 10, '=IF(A{r}=A{s},G{s},"")'.format(r=i, s=i + 1)).font = NEGRO
        ws.cell(i, 11, '=IF(AND(A{r}=A{s},A{r}=A{t}),G{t},"")'.format(r=i, s=i + 1, t=i + 2)).font = NEGRO
        ws.cell(i, 12, '=IF(A{r}=A{p},L{p}&","&G{r},G{r})'.format(r=i, p=i - 1)).font = NEGRO
        ws.cell(i, 13, "=IF(A%d<>A%d,1,0)" % (i, i - 1)).font = NEGRO
        ws.cell(i, 14, "=IF(A%d<>A%d,1,0)" % (i, i + 1)).font = NEGRO
    ws.freeze_panes = "A2"
    for j, w in enumerate([8, 11, 17, 24, 10, 7, 7, 17, 11, 10, 11, 26, 7, 6], 1):
        ws.column_dimensions[L(j)].width = w
    R = lambda c: "Datos!$%s$2:$%s$%d" % (c, c, N)

    # ---------------- Letras
    ws = wb.create_sheet("Letras")
    encabezado(ws, 1, ["Actividad", "Letra", "Eventos", "Costo"])
    for i, l in enumerate(orden, 2):
        ws.cell(i, 1, tr["letras"][l]).font = AZUL
        ws.cell(i, 2, l).font = AZUL
        ws.cell(i, 3, "=COUNTIF(%s,A%d)" % (R("D"), i)).font = VERDE
        ws.cell(i, 4, "=SUMIF(%s,A%d,%s)/C%d" % (R("D"), i, R("F"), i)).font = VERDE
    ws.cell(len(orden) + 3, 1, "Letra por orden de aparición en la hoja (convención de van der Aalst: una letra por actividad).")
    ws.column_dimensions["A"].width = 28

    # ---------------- Casos
    ws = wb.create_sheet("Casos")
    encabezado(ws, 1, ["Caso", "Traza", "Inicio", "Fin", "Duración (días)", "Costo", "Eventos"])
    for i, caso in enumerate(casos, 2):
        ws.cell(i, 1, caso).font = AZUL
        ws.cell(i, 2, "=INDEX(%s,MATCH(A%d,%s,0)+COUNTIF(%s,A%d)-1)" % (R("L"), i, R("A"), R("A"), i)).font = VERDE
        ws.cell(i, 3, "=_xlfn.MINIFS(%s,%s,A%d)" % (R("H"), R("A"), i)).font = VERDE
        ws.cell(i, 4, "=_xlfn.MAXIFS(%s,%s,A%d)" % (R("H"), R("A"), i)).font = VERDE
        ws.cell(i, 5, "=D%d-C%d" % (i, i)).font = NEGRO
        ws.cell(i, 6, "=SUMIF(%s,A%d,%s)" % (R("A"), i, R("F"))).font = VERDE
        ws.cell(i, 7, "=COUNTIF(%s,A%d)" % (R("A"), i)).font = VERDE
        for c in (3, 4):
            ws.cell(i, c).number_format = "dd/mm/yyyy hh:mm"
        ws.cell(i, 5).number_format = "0.00"
        control.append(("Duración caso %s" % caso, "Casos!E%d" % i, tr["duracion_dias"][str(caso)]))
        control.append(("Costo caso %s" % caso, "Casos!F%d" % i, tr["costo_por_caso"][str(caso)]))
    u = len(casos) + 1
    ws.cell(u + 2, 4, "Promedio").font = NEGRO_N
    ws.cell(u + 2, 5, "=AVERAGE(E2:E%d)" % u).font = NEGRO_N
    ws.cell(u + 2, 5).number_format = "0.00"
    ws.cell(u + 2, 6, "=AVERAGE(F2:F%d)" % u).font = NEGRO_N
    ws.column_dimensions["B"].width = 26
    for c in "CD":
        ws.column_dimensions[c].width = 17
    casos_rng = "Casos!$B$2:$B$%d" % u

    # ---------------- Variantes
    ws = wb.create_sheet("Variantes")
    encabezado(ws, 1, ["Variante", "Frecuencia", "Casos (del programa)"])
    for i, v in enumerate(tr["variantes"], 2):
        ws.cell(i, 1, ",".join(v["traza"])).font = AZUL
        ws.cell(i, 2, "=COUNTIF(%s,A%d)" % (casos_rng, i)).font = VERDE
        ws.cell(i, 3, ", ".join(v["casos"])).font = AZUL
        control.append(("Frecuencia <%s>" % ",".join(v["traza"]), "Variantes!B%d" % i, v["frecuencia"]))
    k = len(tr["variantes"]) + 1
    ws.cell(k + 1, 1, "Total de casos").font = NEGRO_N
    ws.cell(k + 1, 2, "=SUM(B2:B%d)" % k).font = NEGRO_N
    ws.column_dimensions["A"].width = 32
    ws.column_dimensions["C"].width = 22

    # ---------------- Relaciones
    ws = wb.create_sheet("Relaciones")
    n = len(orden)
    pos = {}

    def matriz(fila0, titulo):
        ws.cell(fila0, 1, titulo).font = TITULO
        for j, y in enumerate(orden):
            c = ws.cell(fila0 + 1, 2 + j, y)
            c.font, c.fill = NEGRO_N, ENC
        for i, x in enumerate(orden):
            c = ws.cell(fila0 + 2 + i, 1, x)
            c.font, c.fill = NEGRO_N, ENC
        return lambda i, j: "%s%d" % (L(2 + j), fila0 + 2 + i)
    d = matriz(1, "|x>y|: veces que y sigue directamente a x (fila x, columna y)")
    for i, x in enumerate(orden):
        for j, y in enumerate(orden):
            ws[d(i, j)] = "=COUNTIFS(%s,$A%d,%s,%s$2)" % (R("G"), 3 + i, R("J"), L(2 + j))
            ws[d(i, j)].font = VERDE
            if tr["dfg"].get("%s>%s" % (x, y)):
                control.append(("|%s>%s|" % (x, y), "Relaciones!" + d(i, j), tr["dfg"]["%s>%s" % (x, y)]))
    f0 = n + 4
    ws.cell(f0 - 1, 1, "Inicio / fin").font = NEGRO_N
    ws.cell(f0 - 1, 2, "=" + "&\"  \"&".join('"%s:"&COUNTIFS(%s,"%s",%s,1)' % (x, R("G"), x, R("M")) for x in orden if x in tr["inicio"]) or '""').font = VERDE
    fp = matriz(f0 + 1, "Footprint del algoritmo α: → causalidad, ← inversa, || paralelo, # sin relación")
    for i in range(n):
        for j in range(n):
            xy, yx = d(i, j), d(j, i)
            ws[fp(i, j)] = '=IF(AND({a}>0,{b}>0),"||",IF({a}>0,"→",IF({b}>0,"←","#")))'.format(a=xy, b=yx)
    f1 = f0 + n + 4
    dp = matriz(f1, "Dependencia del Heuristics Miner x⇒y = (|x>y| − |y>x|)/(|x>y| + |y>x| + 1); umbral 0.5")
    for i, x in enumerate(orden):
        for j, y in enumerate(orden):
            xy, yx = d(i, j), d(j, i)
            ws[dp(i, j)] = '=IF(OR({a}+{b}=0,"{x}"="{y}"),"",({a}-{b})/({a}+{b}+1))'.format(a=xy, b=yx, x=x, y=y)
            ws[dp(i, j)].number_format = "0.000"
            clave = "%s=>%s" % (x, y)
            if clave in tr["dependencia"]:
                control.append(("%s⇒%s" % (x, y), "Relaciones!" + dp(i, j), tr["dependencia"][clave]))
    f2 = f1 + n + 3
    b2 = matriz(f2, "|x>>y|: patrón x, y, x (bucle de longitud 2)")
    for i, x in enumerate(orden):
        for j, y in enumerate(orden):
            ws[b2(i, j)] = '=IF($A{r}={c}${h},0,COUNTIFS({G},$A{r},{J},{c}${h},{K},$A{r}))'.format(
                r=f2 + 2 + i, c=L(2 + j), h=f2 + 1, G=R("G"), J=R("J"), K=R("K"))
            ws[b2(i, j)].font = VERDE
            if tr["bucle2"].get("%s>>%s" % (x, y)):
                control.append(("|%s>>%s|" % (x, y), "Relaciones!" + b2(i, j), tr["bucle2"]["%s>>%s" % (x, y)]))
    f3 = f2 + n + 3
    d2 = matriz(f3, "Dependencia de bucle de longitud 2: x⇒2y = (|x>>y| + |y>>x|)/(|x>>y| + |y>>x| + 1)")
    for i, x in enumerate(orden):
        for j, y in enumerate(orden):
            a, b = b2(i, j), b2(j, i)
            ws[d2(i, j)] = '=IF({a}=0,"",({a}+{b})/({a}+{b}+1))'.format(a=a, b=b)
            ws[d2(i, j)].number_format = "0.000"
            clave = "%s=>2%s" % (x, y)
            if clave in tr["dependencia_bucle2"]:
                control.append(("%s⇒2%s" % (x, y), "Relaciones!" + d2(i, j), tr["dependencia_bucle2"][clave]))
    ws.column_dimensions["A"].width = 8

    # ---------------- Recursos
    ws = wb.create_sheet("Recursos")
    personas = sorted({f["Resource"] for f in filas})
    encabezado(ws, 1, ["Actividad \\ Recurso"] + personas)
    for i, l in enumerate(orden, 2):
        ws.cell(i, 1, l).font = AZUL
        for j, p in enumerate(personas, 2):
            ws.cell(i, j, "=COUNTIFS(%s,$A%d,%s,%s$1)" % (R("G"), i, R("E"), L(j))).font = VERDE
    ws.cell(len(orden) + 3, 1, "Los carriles del BPMN agrupan actividades que comparten algún recurso.")

    # ---------------- Red
    ws = wb.create_sheet("Red")
    red = tr["red"]
    ws.cell(1, 1, "Red WF etiquetada N = (P, T, F, A, l), M0 = [ini], Mf = [fin]").font = TITULO
    encabezado(ws, 3, ["Transición", "Etiqueta l(t)", "Entradas", "Salidas"])
    ent = {t: [a for a, b in red["F"] if b == t] for t in red["T"]}
    sal = {t: [b for a, b in red["F"] if a == t] for t in red["T"]}
    for i, t in enumerate(red["T"], 4):
        for j, v in enumerate([t, red["l"][t], ", ".join(ent[t]), ", ".join(sal[t])], 1):
            ws.cell(i, j, v).font = AZUL
    r = len(red["T"]) + 5
    for etq, f, val in (("|P| lugares", "=%d" % len(red["P"]), len(red["P"])),
                        ("|T| transiciones", "=COUNTA(A4:A%d)" % (r - 2), len(red["T"])),
                        ("silenciosas", '=COUNTIF(B4:B%d,"τ")' % (r - 2), red["silenciosas"]),
                        ("|F| arcos", '=SUMPRODUCT(LEN(C4:D%d)-LEN(SUBSTITUTE(C4:D%d,",",""))+(LEN(C4:D%d)>0))' % (r - 2, r - 2, r - 2), red["arcos"])):
        ws.cell(r, 1, etq).font = NEGRO_N
        ws.cell(r, 2, f).font = NEGRO_N
        control.append((etq, "Red!B%d" % r, val))
        r += 1
    ws.cell(r + 1, 1, "Denominación").font = NEGRO_N
    ws.cell(r + 1, 2, tr["denominacion"]).font = AZUL
    r += 3
    encabezado(ws, r, ["Propiedad", "¿Cumple?"])
    for i, k in enumerate(("red_wf", "segura", "solida", "libre_eleccion", "maquina_de_estados", "grafo_marcado"), r + 1):
        ws.cell(i, 1, k.replace("_", " ")).font = NEGRO
        ws.cell(i, 2, "Sí" if tr["propiedades"][k] else "No").font = AZUL
    for c, w in zip("ABCD", (16, 40, 18, 18)):
        ws.column_dimensions[c].width = w

    # ---------------- Alcanzabilidad
    ws = wb.create_sheet("Alcanzabilidad")
    encabezado(ws, 1, ["#", "Marca alcanzable"])
    for i, m in enumerate(tr["marcas"], 2):
        ws.cell(i, 1, i - 1).font = AZUL
        ws.cell(i, 2, m).font = AZUL
    ws.cell(len(tr["marcas"]) + 3, 1, "Marcas").font = NEGRO_N
    ws.cell(len(tr["marcas"]) + 3, 2, "=COUNTA(B2:B%d)" % (len(tr["marcas"]) + 1)).font = NEGRO_N
    control.append(("Marcas alcanzables", "Alcanzabilidad!B%d" % (len(tr["marcas"]) + 3), tr["propiedades"]["marcas"]))
    ws.column_dimensions["B"].width = 40

    # ---------------- Replay
    ws = wb.create_sheet("Replay")
    encabezado(ws, 1, ["Caso", "Traza", "p producidas", "c consumidas", "m faltantes", "r restantes"])
    for i, (caso, v) in enumerate(tr["replay"]["por_caso"].items(), 2):
        ws.cell(i, 1, caso).font = AZUL
        ws.cell(i, 2, tr["trazas"][caso]).font = AZUL
        for j, x in enumerate(v, 3):
            ws.cell(i, j, x).font = AZUL
    u = len(tr["replay"]["por_caso"]) + 1
    ws.cell(u + 1, 1, "Total").font = NEGRO_N
    for j in range(3, 7):
        ws.cell(u + 1, j, "=SUM(%s2:%s%d)" % (L(j), L(j), u)).font = NEGRO_N
    ws.cell(u + 3, 1, "Ajuste = ½(1 − m/c) + ½(1 − r/p)").font = NEGRO_N
    ws.cell(u + 3, 3, "=0.5*(1-E{t}/D{t})+0.5*(1-F{t}/C{t})".format(t=u + 1)).font = NEGRO_N
    control.append(("Ajuste (fitness)", "Replay!C%d" % (u + 3), tr["replay"]["fitness"]))
    control.append(("p producidas", "Replay!C%d" % (u + 1), tr["replay"]["p"]))

    # ---------------- Control
    ws = wb.create_sheet("Control")
    ws.cell(1, 1, "Control: cifras del Excel contra traza.json (resolver.py)").font = TITULO
    encabezado(ws, 3, ["Concepto", "Excel", "Traza", "Diferencia", "¿Coincide?"])
    control = [("Eventos", "COUNTA(%s)" % R("A"), tr["eventos"]), ("Casos", "COUNTA(Casos!A2:A%d)" % (len(casos) + 1), tr["casos"])] + control
    for i, (concepto, ref, val) in enumerate(control, 4):
        ws.cell(i, 1, concepto).font = NEGRO
        ws.cell(i, 2, "=" + ref).font = VERDE
        ws.cell(i, 3, val).font = AZUL
        ws.cell(i, 4, "=B%d-C%d" % (i, i)).font = NEGRO
        ws.cell(i, 5, '=IF(ABS(D%d)<=1E-6,"sí","NO")' % i).font = NEGRO_N
    fin = len(control) + 3
    ws.cell(fin + 2, 1, "Comprobaciones").font = NEGRO_N
    ws.cell(fin + 2, 2, "=COUNTA(E4:E%d)" % fin).font = NEGRO_N
    ws.cell(fin + 3, 1, "Coinciden").font = NEGRO_N
    ws.cell(fin + 3, 2, '=COUNTIF(E4:E%d,"sí")' % fin).font = NEGRO_N
    ws.column_dimensions["A"].width = 30

    # ---------------- Resultado
    filas_r = [("Registro", tr["registro"], AZUL), ("Eventos", "=COUNTA(%s)" % R("A"), VERDE_N),
               ("Casos", "=COUNTA(Casos!A2:A%d)" % (len(casos) + 1), VERDE_N),
               ("Actividades", "=COUNTA(Letras!A2:A%d)" % (len(orden) + 1), VERDE_N),
               ("Variantes", "=COUNTA(Variantes!A2:A%d)" % (len(tr["variantes"]) + 1), VERDE_N),
               ("Árbol de proceso", tr["arbol"], AZUL),
               ("Red", "|P| = %d, |T| = %d (%d silenciosas), |F| = %d" % (len(red["P"]), len(red["T"]), red["silenciosas"], red["arcos"]), AZUL),
               ("Denominación", tr["denominacion"], AZUL),
               ("Ajuste (fitness)", "=Control!B%d" % (4 + [c[0] for c in control].index("Ajuste (fitness)")), VERDE_N),
               ("Duración promedio (días)", "=ROUND(Casos!E%d,2)" % (len(casos) + 3), VERDE_N),
               ("Costo promedio por caso", "=Casos!F%d" % (len(casos) + 3), VERDE_N),
               ("Control: cifras que coinciden", '=Control!B%d&" de "&Control!B%d' % (fin + 3, fin + 2), VERDE_N)]
    res.cell(1, 1, "Modelado de procesos: %s" % tr["registro"]).font = TITULO
    for i, (a, b, fnt) in enumerate(filas_r, 3):
        res.cell(i, 1, a).font = NEGRO_N
        res.cell(i, 2, b).font = fnt
    res.cell(len(filas_r) + 4, 1, "Colores: azul = dato tecleado o resultado del programa; negro = fórmula de la hoja; verde = fórmula que trae datos de otra hoja.")
    res.column_dimensions["A"].width = 30
    res.column_dimensions["B"].width = 90
    salida = os.path.join(I, "Demostración.xlsx")
    wb.save(salida)
    print("Excel: %s (%d comprobaciones en Control)" % (salida, len(control)))


if __name__ == "__main__":
    main()
