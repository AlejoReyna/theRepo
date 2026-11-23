#!/usr/bin/env python3
"""Demostración.xlsx de Lasso y Ridge (OD/AM R.pdf p.29-32).

Hojas:
  Coeficientes — β de Lasso, Ridge literal (T3) y Ridge alpha = 0 en λ.min; ceros contados con
                 fórmula; la fila 1 de los datos sustituida a mano (β0 + Σ βj·xj) para cada modelo.
  Predicciones — y y ŷ de R para las n filas; MSE = SUMXMY2(y, ŷ)/n (p.30 y p.32).
  Control      — Excel contra Python/R.
Uso: .venv/bin/python excel_regularizacion.py INCISO_DIR
"""
import csv
import json
import os
import sys

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

AZUL, VERDE, NEGRO_N, TITULO = Font(color="1F4E9E"), Font(color="1E7B34"), Font(bold=True), Font(bold=True, size=13)
ENC = PatternFill("solid", fgColor="DDE4EE")
MODS = (("lasso", "Lasso (alpha = 1, p.30)"), ("ridge_literal", "Ridge literal alpha <- 1.0 (T3)"), ("ridge_alpha0", "Ridge alpha = 0 (p.31, se entrega)"))


def enc(ws, fila, textos, col=1):
    for j, e in enumerate(textos, col):
        c = ws.cell(fila, j, e)
        c.font, c.fill = NEGRO_N, ENC


def main():
    I = sys.argv[1]
    tr = json.load(open(os.path.join(I, "traza.json"), encoding="utf-8"))
    par = json.load(open(os.path.join(I, "datos", "parametros.json"), encoding="utf-8"))
    datos_raw = list(csv.DictReader(open(os.path.join(I, "datos", par["archivo"]), newline="", encoding="utf-8-sig")))
    datos = [r for r in datos_raw if all(v is not None and str(v).strip() not in ("", "NA") for v in r.values())]
    pr = list(csv.DictReader(open(os.path.join(I, "predicciones_R.csv"), encoding="utf-8")))
    cols, x0_vals = [], {}
    for c in [c for c in datos[0] if c != par["y"]]:
        try:
            for r in datos:
                float(r[c])
            cols.append(c)
            x0_vals[c] = float(datos[0][c])
        except ValueError:
            for nv in sorted({r[c] for r in datos})[1:]:
                nm = "%s%s" % (c, nv)
                cols.append(nm)
                x0_vals[nm] = 1.0 if datos[0][c] == nv else 0.0
    wb = Workbook()
    ws = wb.active
    ws.title = "Coeficientes"
    ws["A1"] = "Lasso y Ridge con glmnet (OD/AM R.pdf p.29-32): coeficientes en λ.min (cv.glmnet, semilla %s)" % par.get("semilla")
    ws["A1"].font = TITULO
    enc(ws, 3, ["Término"] + [m[1] for m in MODS] + ["x de la fila 1"])
    terminos = ["(Intercept)"] + cols
    for i, t in enumerate(terminos, 4):
        ws.cell(i, 1, t).font = AZUL
        for j, (m, _) in enumerate(MODS, 2):
            ws.cell(i, j, tr["modelos"][m]["coef_R"][t]).font = AZUL
        ws.cell(i, 5, 1 if t == "(Intercept)" else x0_vals[t]).font = AZUL
    u = 3 + len(terminos)
    f = u + 2
    filas = [("λ.min", [tr["modelos"][m]["lambda_min"] for m, _ in MODS]),
             ("Coeficientes en cero (sin intercepto)", ['=COUNTIF(%s5:%s%d,0)' % (c, c, u) for c in "BCD"]),
             ("ŷ fila 1 = β0 + Σ βj·xj (a mano)", ["=SUMPRODUCT(%s4:%s%d,$E$4:$E$%d)" % (c, c, u, u) for c in "BCD"])]
    for k, (et, vals) in enumerate(filas):
        ws.cell(f + k, 1, et).font = NEGRO_N
        for j, v in enumerate(vals, 2):
            ws.cell(f + k, j, v).font = AZUL if not isinstance(v, str) else NEGRO_N
    ws.cell(f + 4, 1, "p.29: Lasso puede llevar coeficientes exactamente a cero. p.31: Ridge solo los encoge. "
                      "T3: p.32 escribe alpha <- 1.0, que en glmnet es Lasso (columna C = columna B); se entrega alpha = 0.")
    ws.column_dimensions["A"].width = 38
    for c in "BCDE":
        ws.column_dimensions[c].width = 26

    wp = wb.create_sheet("Predicciones")
    wp["A1"] = "MSE = mean((y − ŷ)²) sobre los datos de ajuste (p.30, p.32)"
    wp["A1"].font = TITULO
    enc(wp, 3, ["y"] + [m[1] for m in MODS])
    for i, r in enumerate(pr, 4):
        wp.cell(i, 1, float(r["y"])).font = AZUL
        for j, (m, _) in enumerate(MODS, 2):
            wp.cell(i, j, float(r[m])).font = AZUL
    v = 3 + len(pr)
    wp.cell(2, 6, "MSE").font = NEGRO_N
    for j, c in enumerate("BCD", 7):
        wp.cell(2, j, "=SUMXMY2($A$4:$A$%d,%s4:%s%d)/COUNT($A$4:$A$%d)" % (v, c, c, v, v)).font = NEGRO_N

    wc = wb.create_sheet("Control")
    enc(wc, 3, ("Concepto", "Excel", "Python/R", "Diferencia", "¿Coincide?"))
    control = []
    for j, (m, et) in enumerate(MODS):
        c = "BCD"[j]
        ent = tr["modelos"][m]
        control += [("MSE %s" % m, "Predicciones!%s2" % "GHI"[j], ent["MSE"]),
                    ("Ceros %s" % m, "Coeficientes!%s%d" % (c, f + 1), len(ent["ceros_R"])),
                    ("ŷ fila 1 %s" % m, "Coeficientes!%s%d" % (c, f + 2), float(pr[0][m]))]
    for i, (c_, ref, val) in enumerate(control, 4):
        wc.cell(i, 1, c_)
        wc.cell(i, 2, "=" + ref).font = VERDE
        wc.cell(i, 3, val).font = AZUL
        wc.cell(i, 4, "=B%d-C%d" % (i, i))
        wc.cell(i, 5, '=IF(ABS(D%d)<=1E-6*MAX(1,ABS(C%d)),"sí","NO")' % (i, i)).font = NEGRO_N
    wc.column_dimensions["A"].width = 28
    wb.save(os.path.join(I, "Demostración.xlsx"))
    print("Excel: %d comprobaciones" % len(control))


if __name__ == "__main__":
    main()
