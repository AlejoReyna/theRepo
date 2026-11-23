#!/usr/bin/env python3
"""Demostración.xlsx de Breusch-Pagan: hipótesis (OD/AM R.pdf p.8), ŷ y e² con TREND, BP = n·R² de la
regresión auxiliar de e² sobre X (LINEST, contraste de Koenker), p = CHISQ.DIST.RT(BP, gl), decisión.
Uso: .venv/bin/python excel_bp.py INCISO_DIR
"""
import csv
import json
import os
import sys

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter as L

AZUL, VERDE, NEGRO_N, TITULO = Font(color="1F4E9E"), Font(color="1E7B34"), Font(bold=True), Font(bold=True, size=13)
ENC = PatternFill("solid", fgColor="DDE4EE")
MODELOS = [("old: waiting ~ eruptions", "old.csv", "waiting", ["eruptions"]),
           ("BR: precio ~ m2_construcción + recamaras + condición", "BR.csv", "precio", ["m2_construcción", "recamaras", "condición"])]


def _modelos_inciso(I, tr):
    mapa = {m[0]: m for m in MODELOS}
    par_path = os.path.join(I, "datos", "parametros.json")
    if os.path.exists(par_path):
        par = json.load(open(par_path, encoding="utf-8"))
        for m in par.get("modelos", [par] if "archivo" in par else []):
            nm = m.get("nombre", "%s: %s ~ %s" % (m["archivo"], m["y"], " + ".join(m["predictores"])))
            mapa[nm] = (nm, m["archivo"], m["y"], m["predictores"])
    out = []
    csvs = [f for f in sorted(os.listdir(os.path.join(I, "datos"))) if f.endswith(".csv")]
    for nombre in tr:
        if nombre in mapa and os.path.exists(os.path.join(I, "datos", mapa[nombre][1])):
            out.append(mapa[nombre])
        else:
            _, formula = nombre.split(":", 1) if ":" in nombre else ("", nombre)
            y_s, preds_s = formula.split("~", 1)
            out.append((nombre, csvs[0], y_s.strip(), [p.strip() for p in preds_s.split("+")]))
    return out


def main():
    I = sys.argv[1]
    tr = json.load(open(os.path.join(I, "traza.json"), encoding="utf-8"))
    wb = Workbook()
    wb.active.title = "Resumen"
    rs = wb["Resumen"]
    rs["A1"] = "Prueba de Breusch-Pagan (OD/AM R.pdf p.7-9)"
    rs["A1"].font = TITULO
    rs["A3"] = "H0: homocedasticidad (varianza constante de los residuos). HA: heterocedasticidad. Se rechaza H0 si p < α."
    rs["A4"], rs["B4"] = "α", 0.05
    for j, e in enumerate(("Modelo", "BP (Excel)", "gl", "p (Excel)", "Decisión", "BP (R bptest)", "p (R)"), 1):
        c = rs.cell(6, j, e)
        c.font, c.fill = NEGRO_N, ENC
    control = []
    for m_i, (nombre, archivo, y, preds) in enumerate(_modelos_inciso(I, tr), 1):
        filas = list(csv.DictReader(open(os.path.join(I, "datos", archivo), newline="", encoding="utf-8-sig")))
        ws = wb.create_sheet("Modelo%d" % m_i)
        ws["A1"] = nombre
        ws["A1"].font = TITULO
        k = len(preds)
        for j, e in enumerate(preds + [y, "ŷ", "e²"], 1):
            c = ws.cell(3, j, e)
            c.font, c.fill = NEGRO_N, ENC
        n = len(filas)
        u = 3 + n
        X = "$A$4:$%s$%d" % (L(k), u)
        Y = "$%s$4:$%s$%d" % (L(k + 1), L(k + 1), u)
        for i, r in enumerate(filas, 4):
            for j, p in enumerate(preds + [y], 1):
                ws.cell(i, j, float(r[p])).font = AZUL
            ws.cell(i, k + 2, "=TREND(%s,%s,%s%d:%s%d)" % (Y, X, "A", i, L(k), i))
            ws.cell(i, k + 3, "=(%s%d-%s%d)^2" % (L(k + 1), i, L(k + 2), i))
        E = "$%s$4:$%s$%d" % (L(k + 3), L(k + 3), u)
        fila = 6 + m_i
        rs.cell(fila, 1, nombre).font = AZUL
        rs.cell(fila, 2, "=%d*INDEX(LINEST(Modelo%d!%s,Modelo%d!%s,TRUE,TRUE),3,1)" % (n, m_i, E, m_i, X)).font = VERDE
        rs.cell(fila, 3, k).font = AZUL
        rs.cell(fila, 4, "=_xlfn.CHISQ.DIST.RT(B%d,C%d)" % (fila, fila))
        rs.cell(fila, 5, '=IF(D%d<$B$4,"se rechaza H0: heterocedasticidad","no se rechaza H0: homocedasticidad")' % fila).font = NEGRO_N
        rs.cell(fila, 6, tr[nombre]["BP"]).font = AZUL
        rs.cell(fila, 7, tr[nombre]["p"]).font = AZUL
        control += [("BP %s" % nombre[:30], "Resumen!B%d" % fila, tr[nombre]["BP"]), ("p %s" % nombre[:30], "Resumen!D%d" % fila, tr[nombre]["p"])]
    rs.column_dimensions["A"].width = 52
    rs.column_dimensions["E"].width = 40
    rs["A10"] = "BP de Excel = n·R² de e² sobre X (forma studentizada de Koenker, la que usa bptest por omisión; contraste fuera de las láminas)."
    wc = wb.create_sheet("Control")
    for j, e in enumerate(("Concepto", "Excel", "R", "Diferencia", "¿Coincide?"), 1):
        c = wc.cell(3, j, e)
        c.font, c.fill = NEGRO_N, ENC
    for i, (c_, ref, v) in enumerate(control, 4):
        wc.cell(i, 1, c_)
        wc.cell(i, 2, "=" + ref).font = VERDE
        wc.cell(i, 3, v).font = AZUL
        wc.cell(i, 4, "=B%d-C%d" % (i, i))
        wc.cell(i, 5, '=IF(ABS(D%d)<=1E-6*MAX(ABS(C%d),1E-30),"sí","NO")' % (i, i)).font = NEGRO_N
    wb.save(os.path.join(I, "Demostración.xlsx"))
    print("Excel: %d comprobaciones" % len(control))


if __name__ == "__main__":
    main()
