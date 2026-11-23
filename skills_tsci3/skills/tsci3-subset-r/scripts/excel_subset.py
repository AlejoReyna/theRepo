#!/usr/bin/env python3
"""Demostración.xlsx de tratamiento de datos con subsetting (tsci3-subset-r: AF1 Metro, Border Crossing, Set R; MC-P2).

Hojas:
  Bitácora — cada paso P0..Pn del plan, operación en R, filas y columnas en Python (bitacora.csv) y en R
             (bitacora_R.csv), con diferencias en fórmula.
  Perfil   — perfil de calidad de cada columna (no_na, na, distintos, % vacíos en fórmula =na/(no_na+na)).
  Control  — comprobación con fórmulas de que las filas y columnas de cada paso coinciden entre Python y R.
Uso: .venv/bin/python excel_subset.py INCISO_DIR
"""
import csv
import json
import os
import sys

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

AZUL, VERDE, NEGRO_N, TITULO = Font(color="1F4E9E"), Font(color="1E7B34"), Font(bold=True), Font(bold=True, size=13)
ENC = PatternFill("solid", fgColor="DDE4EE")


def enc(ws, fila, textos, col=1):
    for j, e in enumerate(textos, col):
        c = ws.cell(fila, j, e)
        c.font, c.fill = NEGRO_N, ENC


def main():
    I = sys.argv[1]
    tr = json.load(open(os.path.join(I, "traza.json"), encoding="utf-8"))
    bit_py = list(csv.DictReader(open(os.path.join(I, "bitacora.csv"), encoding="utf-8")))
    bit_r = {r.get("paso", r.get("id")): r for r in csv.DictReader(open(os.path.join(I, "bitacora_R.csv"), encoding="utf-8"))}
    wb = Workbook()
    ws = wb.active
    ws.title = "Bitácora"
    ws["A1"] = "Bitácora de subsettings y tratamiento de datos (%s)" % tr.get("archivo", "")
    ws["A1"].font = TITULO
    ws["A2"] = "Objetivo:"
    ws["A2"].font = NEGRO_N
    ws["B2"] = tr.get("objetivo", tr.get("problema", ""))
    enc(ws, 4, ("Paso", "Operación / Subsetting", "Filas (Python)", "Cols (Python)", "Filas (R)", "Cols (R)", "Δ Filas", "Δ Cols"))
    control = []
    for idx, p in enumerate(bit_py, 5):
        pid = p.get("paso", p.get("id", ""))
        r = bit_r.get(pid, p)
        ws.cell(idx, 1, pid).font = AZUL
        ws.cell(idx, 2, p.get("operacion", p.get("descripcion", ""))).font = AZUL
        ws.cell(idx, 3, int(p["filas"])).font = AZUL
        ws.cell(idx, 4, int(p["columnas"])).font = AZUL
        ws.cell(idx, 5, int(r["filas"])).font = AZUL
        ws.cell(idx, 6, int(r["columnas"])).font = AZUL
        ws.cell(idx, 7, "=C%d-E%d" % (idx, idx))
        ws.cell(idx, 8, "=D%d-F%d" % (idx, idx))
        control.append(("Filas %s" % pid, "Bitácora!E%d" % idx, int(p["filas"])))
        control.append(("Columnas %s" % pid, "Bitácora!F%d" % idx, int(p["columnas"])))
    ws.column_dimensions["B"].width = 52

    perfil_path = os.path.join(I, "perfil_columnas.csv")
    if os.path.exists(perfil_path):
        perf = list(csv.DictReader(open(perfil_path, encoding="utf-8")))
        if perf:
            wp = wb.create_sheet("Perfil")
            wp["A1"] = "Perfil de calidad de columnas antes de limpiar"
            wp["A1"].font = TITULO
            cols_p = list(perf[0].keys())
            enc(wp, 3, cols_p + ["% vacíos (fórmula)"])
            for i, f in enumerate(perf, 4):
                for j, c in enumerate(cols_p, 1):
                    v = f[c]
                    try:
                        v = int(v)
                    except ValueError:
                        try:
                            v = float(v)
                        except ValueError:
                            pass
                    wp.cell(i, j, v).font = AZUL
                if "no_na" in cols_p and "na" in cols_p:
                    c_nona = chr(65 + cols_p.index("no_na"))
                    c_na = chr(65 + cols_p.index("na"))
                    wp.cell(i, len(cols_p) + 1, "=%s%d/(%s%d+%s%d)" % (c_na, i, c_nona, i, c_na, i))
            wp.column_dimensions["A"].width = 28

    wc = wb.create_sheet("Control")
    enc(wc, 3, ("Concepto", "Excel (R)", "Traza (Python)", "Diferencia", "¿Coincide?"))
    for i, (c_, ref, val) in enumerate(control, 4):
        wc.cell(i, 1, c_)
        wc.cell(i, 2, "=" + ref).font = VERDE
        wc.cell(i, 3, val).font = AZUL
        wc.cell(i, 4, "=B%d-C%d" % (i, i))
        wc.cell(i, 5, '=IF(ABS(D%d)<=1E-9,"sí","NO")' % i).font = NEGRO_N
    wc.column_dimensions["A"].width = 24
    wb.save(os.path.join(I, "Demostración.xlsx"))
    print("Excel: %d comprobaciones" % len(control))


if __name__ == "__main__":
    main()
