#!/usr/bin/env python3
"""Demostración.xlsx del predictor binario (OD/AM R.pdf p.4, p.10-12): codificación 0/1, sumas,
m y b con las fórmulas de p.4, medias por grupo (AVERAGEIF), t con varianza combinada y su valor p.
Uso: .venv/bin/python excel_binario.py INCISO_DIR
"""
import csv
import json
import os
import sys

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

AZUL, VERDE, NEGRO_N, TITULO = Font(color="1F4E9E"), Font(color="1E7B34"), Font(bold=True), Font(bold=True, size=13)
ENC = PatternFill("solid", fgColor="DDE4EE")


def main():
    I = sys.argv[1]
    tr = json.load(open(os.path.join(I, "traza.json"), encoding="utf-8"))
    par = json.load(open(os.path.join(I, "datos", "parametros.json"), encoding="utf-8"))
    f = list(csv.DictReader(open(os.path.join(I, "datos", par["archivo"]), newline="", encoding="utf-8-sig")))
    n = len(f)
    wb = Workbook()
    ws = wb.active
    ws.title = "Binario"
    ws["A1"] = "Regresión con predictor binario: %s ~ %s (X = 0 o 1, OD/AM R.pdf p.10)" % (par["y"], par["x"])
    ws["A1"].font = TITULO
    for j, e in enumerate(["X = %s (0/1)" % par["x"], "Y = %s" % par["y"], "XY", "X²", "Ŷ", "e²"], 1):
        c = ws.cell(14, j, e)
        c.font, c.fill = NEGRO_N, ENC
    for i, r in enumerate(f, 15):
        ws.cell(i, 1, int(r[par["x"]])).font = AZUL
        ws.cell(i, 2, float(r[par["y"]])).font = AZUL
        ws.cell(i, 3, "=A%d*B%d" % (i, i))
        ws.cell(i, 4, "=A%d^2" % i)
        ws.cell(i, 5, "=$B$6+$B$5*A%d" % i)
        ws.cell(i, 6, "=(B%d-E%d)^2" % (i, i))
    u = 14 + n
    R = lambda c: "%s15:%s%d" % (c, c, u)
    celdas = [("N", "=COUNT(%s)" % R("A")), ("Σx · Σy · Σxy · Σx²", None),
              ("b1 = (NΣxy − ΣxΣy)/(NΣx² − (Σx)²)", "=(B3*C4-A4*B4)/(B3*D4-A4^2)"), ("b0 = (Σy − b1Σx)/N", "=(B4-B5*A4)/B3"),
              ("Media de Y con X = 0", '=AVERAGEIF(%s,0,%s)' % (R("A"), R("B"))), ("Media de Y con X = 1", '=AVERAGEIF(%s,1,%s)' % (R("A"), R("B"))),
              ("s²p (varianza combinada)", '=(SUMPRODUCT((%s=0)*(%s-B7)^2)+SUMPRODUCT((%s=1)*(%s-B8)^2))/(B3-2)' % (R("A"), R("B"), R("A"), R("B"))),
              ("t = (media1 − media0)/√(s²p(1/n0 + 1/n1))", '=(B8-B7)/SQRT(B9*(1/COUNTIF(%s,0)+1/COUNTIF(%s,1)))' % (R("A"), R("A"))),
              ("valor p (dos colas, N − 2 gl)", "=_xlfn.T.DIST.2T(ABS(B10),B3-2)"),
              ("R² = 1 − RSS/TSS", "=1-SUM(%s)/DEVSQ(%s)" % (R("F"), R("B")))]
    for r, (et, fo) in enumerate(celdas, 3):
        ws.cell(r, 1, et).font = NEGRO_N
        if fo:
            ws.cell(r, 2, fo).font = NEGRO_N
    for j, c in enumerate("ABCD"):
        ws.cell(4, j + 1, "=SUM(%s)" % R(c)).font = NEGRO_N
    ws["E4"] = "← Σx, Σy, Σxy, Σx²"
    ws["D5"] = "b0 = media del grupo 0 y b1 = diferencia de medias"
    ws.column_dimensions["A"].width = 44
    wc = wb.create_sheet("Control")
    for j, e in enumerate(("Concepto", "Excel", "Traza", "Diferencia", "¿Coincide?"), 1):
        c = wc.cell(3, j, e)
        c.font, c.fill = NEGRO_N, ENC
    control = [("b1", "Binario!B5", tr["b1"]), ("b0", "Binario!B6", tr["b0"]), ("media0", "Binario!B7", tr["media0"]), ("media1", "Binario!B8", tr["media1"]),
               ("t", "Binario!B10", tr["t"]), ("p", "Binario!B11", tr["p"]), ("R2", "Binario!B12", tr["R2"])]
    for i, (k, ref, v) in enumerate(control, 4):
        wc.cell(i, 1, k)
        wc.cell(i, 2, "=" + ref).font = VERDE
        wc.cell(i, 3, v).font = AZUL
        wc.cell(i, 4, "=B%d-C%d" % (i, i))
        wc.cell(i, 5, '=IF(ABS(D%d)<=1E-9*MAX(1,ABS(C%d)),"sí","NO")' % (i, i)).font = NEGRO_N
    wb.save(os.path.join(I, "Demostración.xlsx"))
    print("Excel: %d comprobaciones" % len(control))


if __name__ == "__main__":
    main()
