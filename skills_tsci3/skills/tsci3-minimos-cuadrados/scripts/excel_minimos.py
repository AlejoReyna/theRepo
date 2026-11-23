#!/usr/bin/env python3
"""Demostración.xlsx de mínimos cuadrados (OD/AM R.pdf p.4-5): x, y, xy, x², sumas, m, b,
ŷ, residuo, residuo², RSS y MSE con fórmulas; SLOPE/INTERCEPT/RSQ como contraste; gráfica.
Uso: .venv/bin/python excel_minimos.py INCISO_DIR
"""
import csv
import json
import os
import sys

from openpyxl import Workbook
from openpyxl.chart import Reference, ScatterChart, Series
from openpyxl.chart.trendline import Trendline
from openpyxl.styles import Font, PatternFill

AZUL, NEGRO, VERDE = Font(color="1F4E9E"), Font(color="000000"), Font(color="1E7B34")
NEGRO_N, VERDE_N, TITULO = Font(bold=True), Font(color="1E7B34", bold=True), Font(bold=True, size=13)
ENC = PatternFill("solid", fgColor="DDE4EE")


def main():
    I = sys.argv[1]
    tr = json.load(open(os.path.join(I, "traza.json"), encoding="utf-8"))
    par = json.load(open(os.path.join(I, "datos", "parametros.json"), encoding="utf-8"))
    filas = list(csv.DictReader(open(os.path.join(I, "datos", par["archivo"]), newline="", encoding="utf-8-sig")))
    n = len(filas)
    wb = Workbook()
    ws = wb.active
    ws.title = "Minimos"
    ws["A1"] = "Mínimos cuadrados: %s ~ %s (OD/AM R.pdf p.4-5)" % (par["y"], par["x"])
    ws["A1"].font = TITULO
    for j, e in enumerate(["x = %s" % par["x"], "y = %s" % par["y"], "xy", "x²", "ŷ = m·x + b", "e = y − ŷ", "e²"], 1):
        c = ws.cell(10, j, e)
        c.font, c.fill = NEGRO_N, ENC
    for i, f in enumerate(filas, 11):
        ws.cell(i, 1, float(f[par["x"]])).font = AZUL
        ws.cell(i, 2, float(f[par["y"]])).font = AZUL
        ws.cell(i, 3, "=A%d*B%d" % (i, i))
        ws.cell(i, 4, "=A%d^2" % i)
        ws.cell(i, 5, "=$B$5*A%d+$B$6" % i)
        ws.cell(i, 6, "=B%d-E%d" % (i, i))
        ws.cell(i, 7, "=F%d^2" % i)
    u = 10 + n
    filas_r = [("N", "=COUNT(A11:A%d)" % u), ("Σx · Σy · Σxy · Σx²", None),
               ("m = (NΣxy − ΣxΣy)/(NΣx² − (Σx)²)", "=(B3*C4-A4*B4)/(B3*D4-A4^2)"),
               ("b = (Σy − mΣx)/N", "=(B4-B5*A4)/B3"), ("RSS = Σe²", "=SUM(G11:G%d)" % u), ("MSE = RSS/n", "=B7/B3")]
    ws["A3"], ws["B3"] = "N", "=COUNT(A11:A%d)" % u
    for j, col in enumerate("ABCD"):
        ws.cell(4, j + 1, "=SUM(%s11:%s%d)" % (col, col, u)).font = NEGRO_N
    ws["E4"] = "← Σx, Σy, Σxy, Σx²"
    for r, (et, f) in zip((5, 6, 7, 8), filas_r[2:]):
        ws.cell(r, 1, et).font = NEGRO_N
        ws.cell(r, 2, f).font = NEGRO_N
    ws["D5"], ws["E5"] = "SLOPE (contraste)", "=SLOPE(B11:B%d,A11:A%d)" % (u, u)
    ws["D6"], ws["E6"] = "INTERCEPT (contraste)", "=INTERCEPT(B11:B%d,A11:A%d)" % (u, u)
    ws["D7"], ws["E7"] = "R² = RSQ (contraste)", "=RSQ(B11:B%d,A11:A%d)" % (u, u)
    ws.column_dimensions["A"].width = 38
    ch = ScatterChart()
    ch.title, ch.x_axis.title, ch.y_axis.title = "%s ~ %s" % (par["y"], par["x"]), par["x"], par["y"]
    s = Series(Reference(ws, min_col=2, min_row=11, max_row=u), Reference(ws, min_col=1, min_row=11, max_row=u), title="datos")
    s.marker.symbol, s.graphicalProperties.line.noFill = "circle", True
    s.trendline = Trendline(trendlineType="linear", dispEq=True, dispRSqr=True)
    ch.series.append(s)
    ws.add_chart(ch, "I3")
    wc = wb.create_sheet("Control")
    wc["A1"] = "Control: Excel contra traza.json (resolver.py, fracciones exactas)"
    wc["A1"].font = TITULO
    for j, e in enumerate(("Concepto", "Excel", "Traza", "Diferencia", "¿Coincide?"), 1):
        c = wc.cell(3, j, e)
        c.font, c.fill = NEGRO_N, ENC
    control = [("m", "Minimos!B5", tr["m"]), ("b", "Minimos!B6", tr["b"]), ("RSS", "Minimos!B7", tr["RSS"]), ("MSE", "Minimos!B8", tr["MSE"]),
               ("R²", "Minimos!E7", tr["R2"]), ("SLOPE = m", "Minimos!E5", tr["m"]), ("INTERCEPT = b", "Minimos!E6", tr["b"])]
    for i, (k, ref, v) in enumerate(control, 4):
        wc.cell(i, 1, k)
        wc.cell(i, 2, "=" + ref).font = VERDE
        wc.cell(i, 3, v).font = AZUL
        wc.cell(i, 4, "=B%d-C%d" % (i, i))
        wc.cell(i, 5, '=IF(ABS(D%d)<=1E-9*MAX(1,ABS(C%d)),"sí","NO")' % (i, i)).font = NEGRO_N
    wb.save(os.path.join(I, "Demostración.xlsx"))
    print("Excel: %s (%d comprobaciones)" % (os.path.join(I, "Demostración.xlsx"), len(control)))


if __name__ == "__main__":
    main()
