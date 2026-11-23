#!/usr/bin/env python3
"""Demostración.xlsx de regresión múltiple (OD/AM R.pdf p.14-15, p.28): matriz de diseño X,
β = (XᵀX)⁻¹Xᵀy con MMULT/MINVERSE (fórmulas matriciales), LINEST como contraste, predicción con
los datos nuevos sustituida a mano y métricas de prueba (MSE, MAE, R²) desde prueba_R.csv.
Uso: .venv/bin/python excel_multiple.py INCISO_DIR
"""
import csv
import json
import os
import sys

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter as L
from openpyxl.worksheet.formula import ArrayFormula

AZUL, VERDE, NEGRO_N, TITULO = Font(color="1F4E9E"), Font(color="1E7B34"), Font(bold=True), Font(bold=True, size=13)
ENC = PatternFill("solid", fgColor="DDE4EE")


def main():
    I = sys.argv[1]
    sys.path.insert(0, "/Users/alexis/theCode/newSkills/TSCI3/kit_tsci3")
    from tsci3 import regresion as rg
    tr = json.load(open(os.path.join(I, "traza.json"), encoding="utf-8"))
    par = json.load(open(os.path.join(I, "datos", "parametros.json"), encoding="utf-8"))
    f = list(csv.DictReader(open(os.path.join(I, "datos", par["archivo"]), newline="", encoding="utf-8-sig")))
    X_full, nombres_full, niv1 = rg.disenar(f, par["predictores"])
    nuevo_full, _, _ = rg.disenar([par["nuevos"]], par["predictores"], niveles=niv1)
    activos = [j for j, nm in enumerate(nombres_full) if tr["coeficientes"].get(nm) is not None]
    nombres = [nombres_full[j] for j in activos]
    preds = nombres[1:]
    nuevo_vals = [float(nuevo_full[0][j]) for j in activos[1:]]
    k, n = len(nombres), len(f)
    wb = Workbook()
    ws = wb.active
    ws.title = "Matriz"
    ws["A1"] = "Ŷ = β0 + β1X1 + … + βnXn (OD/AM R.pdf p.14-15): β = (XᵀX)⁻¹Xᵀy"
    ws["A1"].font = TITULO
    cab = ["1 (intercepto)"] + preds + [par["y"]]
    for j, e in enumerate(cab, 1):
        c = ws.cell(3, j, e)
        c.font, c.fill = NEGRO_N, ENC
    for i, (r, xrow) in enumerate(zip(f, X_full), 4):
        for j, col_idx in enumerate(activos, 1):
            ws.cell(i, j, float(xrow[col_idx])).font = AZUL
        ws.cell(i, k + 1, float(r[par["y"]])).font = AZUL
    u = 3 + n
    Xr, yr = "Matriz!$A$4:$%s$%d" % (L(k), u), "Matriz!$%s$4:$%s$%d" % (L(k + 1), L(k + 1), u)
    wb_ = wb.create_sheet("Coeficientes")
    wb_["A1"] = "β = MMULT(MINVERSE(MMULT(TRANSPOSE(X), X)), MMULT(TRANSPOSE(X), y))"
    wb_["A1"].font = TITULO
    for j, e in enumerate(("Término", "β (matricial)", "LINEST (contraste)", "R (lm)"), 1):
        c = wb_.cell(3, j, e)
        c.font, c.fill = NEGRO_N, ENC
    for i, nm in enumerate(nombres, 4):
        wb_.cell(i, 1, nm).font = AZUL
        wb_.cell(i, 4, tr["coeficientes"][nm]).font = AZUL
    wb_["B4"] = ArrayFormula("B4:B%d" % (3 + k), "=MMULT(MINVERSE(MMULT(TRANSPOSE(%s),%s)),MMULT(TRANSPOSE(%s),%s))" % (Xr, Xr, Xr, yr))
    xs = "Matriz!$B$4:$%s$%d" % (L(k), u)
    for i in range(k):                                  # LINEST devuelve βn..β1, β0
        wb_.cell(4 + i, 3, "=INDEX(LINEST(%s,%s),1,%d)" % (yr, xs, k - i if i else k)).font = VERDE
    pn = 4 + k + 2
    wb_.cell(pn, 1, "Predicción con datos nuevos (p.28), sustituida a mano").font = NEGRO_N
    terminos = ["B4"] + ["B%d*%g" % (4 + j, v) for j, v in enumerate(nuevo_vals, 1)]
    wb_.cell(pn + 1, 1, " + ".join(["β0"] + ["β%d·%g" % (j, v) for j, v in enumerate(nuevo_vals, 1)])).font = AZUL
    wb_.cell(pn + 1, 2, "=" + "+".join(terminos)).font = NEGRO_N
    prueba = list(csv.DictReader(open(os.path.join(I, "prueba_R.csv"), encoding="utf-8")))
    wp = wb.create_sheet("Prueba")
    wp["A1"] = "Conjunto de prueba (20 %): MSE, MAE y R² (OD/AM R.pdf p.25-27)"
    wp["A1"].font = TITULO
    for j, e in enumerate(("fila", "y", "ŷ (R)", "e", "e²", "|e|"), 1):
        c = wp.cell(3, j, e)
        c.font, c.fill = NEGRO_N, ENC
    for i, r in enumerate(prueba, 4):
        wp.cell(i, 1, int(r["fila"])).font = AZUL
        wp.cell(i, 2, float(r["y"])).font = AZUL
        wp.cell(i, 3, float(r["y_pred"])).font = AZUL
        wp.cell(i, 4, "=B%d-C%d" % (i, i))
        wp.cell(i, 5, "=D%d^2" % i)
        wp.cell(i, 6, "=ABS(D%d)" % i)
    v = 3 + len(prueba)
    for r, (et, fo) in enumerate((("MSE", "=AVERAGE(E4:E%d)" % v), ("MAE", "=AVERAGE(F4:F%d)" % v), ("R²", "=1-SUM(E4:E%d)/DEVSQ(B4:B%d)" % (v, v))), 2):
        wp.cell(r, 8, et).font = NEGRO_N
        wp.cell(r, 9, fo).font = NEGRO_N
    wc = wb.create_sheet("Control")
    for j, e in enumerate(("Concepto", "Excel", "Python/R", "Diferencia", "¿Coincide?"), 1):
        c = wc.cell(3, j, e)
        c.font, c.fill = NEGRO_N, ENC
    control = [("β %s" % nm, "Coeficientes!B%d" % (4 + i), tr["coeficientes"][nm]) for i, nm in enumerate(nombres)]
    control += [("LINEST %s" % nm, "Coeficientes!C%d" % (4 + i), tr["coeficientes"][nm]) for i, nm in enumerate(nombres)]
    control += [("Predicción", "Coeficientes!B%d" % (pn + 1), tr["prediccion"]), ("MSE", "Prueba!I2", tr["MSE"]), ("MAE", "Prueba!I3", tr["MAE"]), ("R²", "Prueba!I4", tr["R2"])]
    for i, (c_, ref, val) in enumerate(control, 4):
        wc.cell(i, 1, c_)
        wc.cell(i, 2, "=" + ref).font = VERDE
        wc.cell(i, 3, val).font = AZUL
        wc.cell(i, 4, "=B%d-C%d" % (i, i))
        wc.cell(i, 5, '=IF(ABS(D%d)<=1E-6*MAX(1,ABS(C%d)),"sí","NO")' % (i, i)).font = NEGRO_N
    wb.save(os.path.join(I, "Demostración.xlsx"))
    print("Excel: %d comprobaciones" % len(control))


if __name__ == "__main__":
    main()
