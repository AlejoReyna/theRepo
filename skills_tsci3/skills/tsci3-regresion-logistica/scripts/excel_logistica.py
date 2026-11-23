#!/usr/bin/env python3
"""Demostración.xlsx de regresión logística (OD/AM R.pdf p.37-41).

Hojas:
  Datos        — precio; mediana, percentiles (PERCENTILE.INC = tipo 7) y conteos (> mediana; [a, b)).
  Binaria      — β de glm; η de los datos nuevos con SUMPRODUCT; p = 1/(1 + EXP(−η)) (sigmoide, p.37);
                 VIF con su lectura (p.39); Anova LR con p = CHIDIST.
  Multinomial  — β de multinom; η por categoría; p_c = e^η_c / (1 + Σ e^η) (base «bajo»); suma = 1.
  Control      — Excel contra Python/R.
Uso: .venv/bin/python excel_logistica.py INCISO_DIR
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
    par = json.load(open(os.path.join(I, "datos", "parametros.json"), encoding="utf-8"))
    datos = list(csv.DictReader(open(os.path.join(I, "datos", par["archivo"]), newline="", encoding="utf-8-sig")))
    preds = par["predictores"]
    nombres = ["(Intercept)"] + preds
    wb = Workbook()
    wd = wb.active
    wd.title = "Datos"
    wd["A1"] = par["y"]
    wd["A1"].font, wd["A1"].fill = NEGRO_N, ENC
    for i, r in enumerate(datos, 2):
        wd.cell(i, 1, float(r[par["y"]])).font = AZUL
    u = len(datos) + 1
    rng = "Datos!$A$2:$A$%d" % u
    filas = [("Mediana (p.40)", "=MEDIAN(%s)" % rng), ("precio_alto = 1 (precio > mediana)", '=COUNTIF(%s,">"&C2)' % rng),
             ("Percentil 0.33 (tipo 7)", "=_xlfn.PERCENTILE.INC(%s,0.33)" % rng), ("Percentil 0.66 (tipo 7)", "=_xlfn.PERCENTILE.INC(%s,0.66)" % rng),
             ("bajo: [−∞, P33)", '=COUNTIF(%s,"<"&C4)' % rng), ("medio: [P33, P66)", '=COUNTIFS(%s,">="&C4,%s,"<"&C5)' % (rng, rng)),
             ("alto: [P66, ∞)", '=COUNTIF(%s,">="&C5)' % rng), ("Total", "=SUM(C6:C8)")]
    for i, (et, f) in enumerate(filas, 2):
        wd.cell(i, 2, et).font = NEGRO_N
        wd.cell(i, 3, f)
    wd["B11"] = "cut(right = FALSE): cada intervalo incluye su límite inferior (p.41)."
    wd.column_dimensions["B"].width = 36

    wb_ = wb.create_sheet("Binaria")
    wb_["A1"] = "Logística binaria (p.40): P(precio_alto = 1) = 1 / (1 + e^(−η)), η = β0 + Σ βj·xj (sigmoide, p.37)"
    wb_["A1"].font = TITULO
    enc(wb_, 3, ("Término", "β (glm)", "x nuevo", "β·x", "VIF (p.39)", "Lectura", "LR χ² (Anova)", "p = CHIDIST(LR, 1)"))
    for i, t in enumerate(nombres, 4):
        wb_.cell(i, 1, t).font = AZUL
        wb_.cell(i, 2, tr["coef_bin"][t]).font = AZUL
        wb_.cell(i, 3, 1 if t == "(Intercept)" else par["nuevos"][t]).font = AZUL
        wb_.cell(i, 4, "=B%d*C%d" % (i, i))
        if t != "(Intercept)":
            wb_.cell(i, 5, tr["VIF"][t]).font = AZUL
            wb_.cell(i, 6, '=IF(E{0}<=1.000001,"sin colinealidad",IF(E{0}<=5,"moderada","preocupante (> 5 o 10)"))'.format(i))
            wb_.cell(i, 7, tr["anova"][t]["LR"]).font = AZUL
            wb_.cell(i, 8, "=CHIDIST(G%d,1)" % i)
    u2 = 3 + len(nombres)
    wb_.cell(u2 + 2, 1, "η").font = NEGRO_N
    wb_.cell(u2 + 2, 2, "=SUM(D4:D%d)" % u2)
    wb_.cell(u2 + 3, 1, "p = 1/(1 + e^(−η))").font = NEGRO_N
    wb_.cell(u2 + 3, 2, "=1/(1+EXP(-B%d))" % (u2 + 2)).font = NEGRO_N
    wb_.column_dimensions["A"].width = 22
    wb_.column_dimensions["F"].width = 22

    wm = wb.create_sheet("Multinomial")
    wm["A1"] = "Logística multinomial (p.41): base «bajo»; p_c = e^(η_c) / (1 + e^(η_medio) + e^(η_alto))"
    wm["A1"].font = TITULO
    enc(wm, 3, ("Término", "x nuevo", "β medio", "β alto"))
    for i, t in enumerate(nombres, 4):
        wm.cell(i, 1, t).font = AZUL
        wm.cell(i, 2, 1 if t == "(Intercept)" else par["nuevos"][t]).font = AZUL
        wm.cell(i, 3, tr["coef_multi"]["medio"][t]).font = AZUL
        wm.cell(i, 4, tr["coef_multi"]["alto"][t]).font = AZUL
    u3 = 3 + len(nombres)
    r = u3 + 2
    wm.cell(r, 1, "η").font = NEGRO_N
    wm.cell(r, 2, 0)
    wm.cell(r, 3, "=SUMPRODUCT(C4:C%d,$B$4:$B$%d)" % (u3, u3))
    wm.cell(r, 4, "=SUMPRODUCT(D4:D%d,$B$4:$B$%d)" % (u3, u3))
    enc(wm, r + 1, ("", "bajo", "medio", "alto", "Σ"))
    wm.cell(r + 2, 1, "Probabilidad").font = NEGRO_N
    den = "(1+EXP(C%d)+EXP(D%d))" % (r, r)
    wm.cell(r + 2, 2, "=1/%s" % den)
    wm.cell(r + 2, 3, "=EXP(C%d)/%s" % (r, den))
    wm.cell(r + 2, 4, "=EXP(D%d)/%s" % (r, den))
    wm.cell(r + 2, 5, "=SUM(B%d:D%d)" % (r + 2, r + 2))
    wm.cell(r + 4, 1, "T25: p.41 toma intercepts <- model_multinom$wts[1:3], que vale (0, 0, 0): son los pesos de la clase base. "
                      "Los interceptos son la fila (Intercept) de esta tabla (coef(model_multinom)[, 1]).")
    wm.column_dimensions["A"].width = 22

    wc = wb.create_sheet("Control")
    enc(wc, 3, ("Concepto", "Excel", "Python/R", "Diferencia", "¿Coincide?"))
    control = [("Mediana", "Datos!C2", tr["mediana"]), ("n precio_alto", "Datos!C3", tr["n_alto"]),
               ("P33", "Datos!C4", tr["p33"]), ("P66", "Datos!C5", tr["p66"])]
    control += [("n %s" % c, "Datos!C%d" % (6 + i), tr["conteos"][c]) for i, c in enumerate(("bajo", "medio", "alto"))]
    control += [("η binaria", "Binaria!B%d" % (u2 + 2), tr["eta_nuevo"]), ("p binaria", "Binaria!B%d" % (u2 + 3), tr["p_nuevo"])]
    control += [("p Anova %s" % t, "Binaria!H%d" % (4 + j), tr["anova"][t]["p"]) for j, t in enumerate(preds, 1)]
    control += [("p %s" % c, "Multinomial!%s%d" % ("BCD"[i], r + 2), tr["probs_nuevo"][c]) for i, c in enumerate(("bajo", "medio", "alto"))]
    control += [("Σ probabilidades", "Multinomial!E%d" % (r + 2), 1.0)]
    for i, (c_, ref, val) in enumerate(control, 4):
        wc.cell(i, 1, c_)
        wc.cell(i, 2, "=" + ref).font = VERDE
        wc.cell(i, 3, val).font = AZUL
        wc.cell(i, 4, "=B%d-C%d" % (i, i))
        wc.cell(i, 5, '=IF(ABS(D%d)<=1E-6*MAX(1E-3,ABS(C%d)),"sí","NO")' % (i, i)).font = NEGRO_N
    wb.save(os.path.join(I, "Demostración.xlsx"))
    print("Excel: %d comprobaciones" % len(control))


if __name__ == "__main__":
    main()
