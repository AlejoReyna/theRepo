#!/usr/bin/env python3
"""Arma Demostración.xlsx de episodios (OD/EPISODES.R) con fórmulas vivas.

Hojas: Resultado, Datos (eventos ordenados por CASE_ID y MOMENT, con «primer evento del caso»),
Pares (todos los pares i < j del mismo caso con Δ = MOMENT_j − MOMENT_i, ¿0 < Δ ≤ wsize?,
primera vez del episodio en el caso y en el distrito), Soporte (casos con el episodio por SUMIFS
y soporte = casos / N), Distritos (casos por distrito y soporte por distrito), Control.

Uso: .venv/bin/python excel_episodios.py INCISO_DIR
"""
import csv
import json
import os
import sys

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from resolver_episodios import leer  # noqa: E402

AZUL, NEGRO, VERDE = Font(color="1F4E9E"), Font(color="000000"), Font(color="1E7B34")
NEGRO_N, VERDE_N, TITULO = Font(bold=True), Font(color="1E7B34", bold=True), Font(bold=True, size=13)
ENC = PatternFill("solid", fgColor="DDE4EE")


def enc(ws, fila, nombres):
    for j, x in enumerate(nombres, 1):
        c = ws.cell(fila, j, x)
        c.font, c.fill = NEGRO_N, ENC


def main():
    I = sys.argv[1]
    tr = json.load(open(os.path.join(I, "traza.json"), encoding="utf-8"))
    par = json.load(open(os.path.join(I, "datos", "parametros.json"), encoding="utf-8"))
    filas = leer(os.path.join(I, "datos", par["archivo"]))
    w = tr["wsize"]
    n = len(filas)
    pares = list(csv.DictReader(open(os.path.join(I, "episodios_detalle_python.csv"), encoding="utf-8")))
    glob = list(csv.DictReader(open(os.path.join(I, "episodios_globales_python.csv"), encoding="utf-8")))
    dist = list(csv.DictReader(open(os.path.join(I, "episodios_por_distrito_python.csv"), encoding="utf-8")))
    control = []
    wb = Workbook()
    res = wb.active
    res.title = "Resultado"

    wd = wb.create_sheet("Datos")
    enc(wd, 1, ["CASE_ID", "MOMENT", "EVENT", "district", "Primer evento del caso", "Primer evento del caso en el distrito"])
    for i, r in enumerate(filas, 2):
        for j, k in enumerate(("CASE_ID", "MOMENT", "EVENT", "district"), 1):
            wd.cell(i, j, r[k]).font = AZUL
        wd.cell(i, 5, "=IF(A%d<>A%d,1,0)" % (i, i - 1))
        wd.cell(i, 6, "=IF(COUNTIFS(A$2:A%d,A%d,D$2:D%d,D%d)=1,1,0)" % (i, i, i, i))
    wd.column_dimensions["A"].width = 14
    wd.column_dimensions["C"].width = 40
    N = "SUM(Datos!$E$2:$E$%d)" % (n + 1)

    wp = wb.create_sheet("Pares")
    wp.cell(1, 1, "Pares i < j del mismo caso; se queda si 0 < Δ ≤ %d (wsize)" % w).font = TITULO
    wp.cell(2, 1, "wsize").font = NEGRO_N
    wp.cell(2, 2, w).font = AZUL
    enc(wp, 4, ["CASE_ID", "district", "start_event", "next_event", "ep", "moment_start", "moment_end", "Δ",
                "¿0 < Δ ≤ wsize?", "1.ª vez del ep en el caso", "1.ª vez del ep en el caso y distrito"])
    for i, p in enumerate(pares, 5):
        for j, k in enumerate(("CASE_ID", "district", "start_event", "next_event", "ep", "moment_start", "moment_end"), 1):
            v = p[k]
            wp.cell(i, j, int(v) if k in ("moment_start", "moment_end", "district") else v).font = AZUL
        wp.cell(i, 8, "=G%d-F%d" % (i, i))
        wp.cell(i, 9, '=IF(AND(H%d>0,H%d<=$B$2),"sí","no")' % (i, i))
        wp.cell(i, 10, "=IF(COUNTIFS(A$5:A%d,A%d,E$5:E%d,E%d)=1,1,0)" % (i, i, i, i))
        wp.cell(i, 11, "=IF(COUNTIFS(A$5:A%d,A%d,E$5:E%d,E%d,B$5:B%d,B%d)=1,1,0)" % (i, i, i, i, i, i))
    u = 4 + len(pares)
    wp.cell(u + 2, 1, "Pares en la ventana").font = NEGRO_N
    wp.cell(u + 2, 2, '=COUNTIF(I5:I%d,"sí")' % u).font = NEGRO_N
    control.append(("Pares en la ventana", "Pares!B%d" % (u + 2), tr["pares"]))
    rp = "Pares!$%s$5:$%s$%d"

    ws = wb.create_sheet("Soporte")
    ws.cell(1, 1, "Soporte global = casos con el episodio / casos").font = TITULO
    ws.cell(2, 1, "Casos (N)").font = NEGRO_N
    ws.cell(2, 2, "=" + N).font = VERDE_N
    control.append(("Casos", "Soporte!B2", tr["casos"]))
    enc(ws, 4, ["Episodio", "Casos con el episodio", "Soporte"])
    for i, g in enumerate(glob, 5):
        ws.cell(i, 1, g["ep"]).font = AZUL
        ws.cell(i, 2, "=SUMIFS(%s,%s,A%d)" % (rp % ("J", "J", u), rp % ("E", "E", u), i)).font = VERDE
        ws.cell(i, 3, "=B%d/$B$2" % i)
        if i < 35:
            control.append(("Soporte %s" % g["ep"][:40], "Soporte!C%d" % i, float(g["support"])))
    ws.column_dimensions["A"].width = 80

    wdi = wb.create_sheet("Distritos")
    wdi.cell(1, 1, "Soporte por distrito = casos del distrito con el episodio / casos del distrito").font = TITULO
    enc(wdi, 3, ["district", "Episodio", "Casos con el episodio", "Casos del distrito", "Soporte"])
    for i, d in enumerate(dist, 4):
        wdi.cell(i, 1, int(d["district"])).font = AZUL
        wdi.cell(i, 2, d["ep"]).font = AZUL
        wdi.cell(i, 3, "=SUMIFS(%s,%s,B%d,%s,A%d)" % (rp % ("K", "K", u), rp % ("E", "E", u), i, rp % ("B", "B", u), i)).font = VERDE
        wdi.cell(i, 4, "=SUMIFS(Datos!$F$2:$F$%d,Datos!$D$2:$D$%d,A%d)" % (n + 1, n + 1, i)).font = VERDE
        wdi.cell(i, 5, "=C%d/D%d" % (i, i))
        if i < 34:
            control.append(("Distrito %s %s" % (d["district"], d["ep"][:30]), "Distritos!E%d" % i, float(d["support"])))
    wdi.column_dimensions["B"].width = 80

    wc = wb.create_sheet("Control")
    wc.cell(1, 1, "Control: cifras del Excel contra resolver.py").font = TITULO
    enc(wc, 3, ["Concepto", "Excel", "Programa", "Diferencia", "¿Coincide?"])
    for i, (concepto, ref, v) in enumerate(control, 4):
        wc.cell(i, 1, concepto)
        wc.cell(i, 2, "=" + ref).font = VERDE
        wc.cell(i, 3, v).font = AZUL
        wc.cell(i, 4, "=B%d-C%d" % (i, i))
        wc.cell(i, 5, '=IF(ABS(D%d)<=1E-9,"sí","NO")' % i).font = NEGRO_N
    uc = len(control) + 3
    wc.cell(uc + 2, 1, "Coinciden").font = NEGRO_N
    wc.cell(uc + 2, 2, '=COUNTIF(E4:E%d,"sí")&" de "&COUNTA(E4:E%d)' % (uc, uc)).font = NEGRO_N
    wc.column_dimensions["A"].width = 50

    res.cell(1, 1, "Episodios A -> B en una ventana de %d (EPISODES.R)" % w).font = TITULO
    for i, (x, y) in enumerate([("Problema", tr["problema"]), ("Eventos", n), ("Casos (G grid _B beat)", "=Soporte!B2"),
                                ("Pares en la ventana", "=Pares!B%d" % (u + 2)), ("Episodios distintos", len(glob)),
                                ("Episodio más frecuente", "=Soporte!A5&\" (soporte \"&TEXT(Soporte!C5,\"0.0000\")&\")\""),
                                ("Control", "=Control!B%d" % (uc + 2))], 3):
        res.cell(i, 1, x).font = NEGRO_N
        res.cell(i, 2, y).font = VERDE_N if isinstance(y, str) and y.startswith("=") else AZUL
    res.cell(11, 1, "T14: read_csv recorta espacios en beat. T23: un beat vacío forma el caso «G…_BNA», como paste0() en R.")
    res.column_dimensions["A"].width = 30
    wb.save(os.path.join(I, "Demostración.xlsx"))
    print("Excel: %s (%d comprobaciones)" % (os.path.join(I, "Demostración.xlsx"), len(control)))


if __name__ == "__main__":
    main()
