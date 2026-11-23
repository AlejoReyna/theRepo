#!/usr/bin/env python3
"""Demostración.xlsx de bosque aleatorio (OD/AM R.pdf p.54-55).

Hojas:
  Bootstrap   — árbol 1: las filas de entrenamiento y cuántas veces entran a su muestra (con reemplazo);
                tamaño = SUM = n, filas fuera de la bolsa = COUNTIF(=0), repetidas = COUNTIF(>1).
  Observación — predicción de cada uno de los árboles para una observación de prueba y su promedio
                (= predicción del bosque, p.54).
  Métricas    — y_test, y_pred; RMSE, MAE y R² en fórmula (p.55).
  Importancia — %IncMSE e IncNodePurity (varImpPlot) con su orden.
  Control     — Excel contra Python/R.
Uso: .venv/bin/python excel_bosque.py INCISO_DIR
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
    leer = lambda n: list(csv.DictReader(open(os.path.join(I, n), encoding="utf-8")))  # noqa: E731
    train = [int(r["fila"]) for r in leer("train_index_R.csv")]
    inbag = leer("inbag_R.csv")
    pr = leer("predicciones_R.csv")
    wb = Workbook()
    wbt = wb.active
    wbt.title = "Bootstrap"
    wbt["A1"] = "Árbol 1: muestra con reemplazo del entrenamiento (p.54)"
    wbt["A1"].font = TITULO
    enc(wbt, 3, ("Fila (datos)", "Veces en la muestra del árbol 1"))
    col1 = list(inbag[0].keys())[0]
    for i, (f, r) in enumerate(zip(train, inbag), 4):
        wbt.cell(i, 1, f).font = AZUL
        wbt.cell(i, 2, int(float(r[col1]))).font = AZUL
    u = 3 + len(train)
    for i, (et, fo) in enumerate((("Tamaño de la muestra (= n)", "=SUM(B4:B%d)" % u), ("Filas fuera de la bolsa", "=COUNTIF(B4:B%d,0)" % u),
                                  ("Filas repetidas", '=COUNTIF(B4:B%d,">1")' % u), ("% fuera de la bolsa", "=E4/COUNT(B4:B%d)" % u),
                                  ("(1 − 1/n)^n", "=(1-1/E3)^E3")), 3):
        wbt.cell(i, 4, et).font = NEGRO_N
        wbt.cell(i, 5, fo)
    wbt.column_dimensions["D"].width = 30

    wo = wb.create_sheet("Observación")
    ob = tr["observacion"]
    wo["A1"] = "Observación de prueba (fila %d): la predicción del bosque es el promedio de los árboles (p.54)" % ob["fila"]
    wo["A1"].font = TITULO
    enc(wo, 3, ("Árbol", "Predicción"))
    for i, v in enumerate(ob["arboles"], 4):
        wo.cell(i, 1, i - 3).font = AZUL
        wo.cell(i, 2, v).font = AZUL
    v = 3 + len(ob["arboles"])
    for i, (et, fo) in enumerate((("Promedio de los árboles", "=AVERAGE(B4:B%d)" % v), ("predict(model) de R", ob["y_pred"]),
                                  ("y real", ob["y"]), ("Error", "=E5-E3")), 3):
        wo.cell(i, 4, et).font = NEGRO_N
        wo.cell(i, 5, fo).font = AZUL if not isinstance(fo, str) else NEGRO_N
    wo.column_dimensions["D"].width = 26

    wm = wb.create_sheet("Métricas")
    wm["A1"] = "Desempeño en prueba (p.55)"
    wm["A1"].font = TITULO
    enc(wm, 3, ("Fila", "y_test", "y_pred"))
    for i, r in enumerate(pr, 4):
        wm.cell(i, 1, int(r["fila"])).font = AZUL
        wm.cell(i, 2, float(r["y"])).font = AZUL
        wm.cell(i, 3, float(r["y_pred"])).font = AZUL
    w = 3 + len(pr)
    for i, (et, fo) in enumerate((("RMSE = √mean((y − ŷ)²)", "=SQRT(SUMXMY2(B4:B%d,C4:C%d)/COUNT(B4:B%d))" % (w, w, w)),
                                  ("MAE = mean|y − ŷ|", "=SUMPRODUCT(ABS(B4:B%d-C4:C%d))/COUNT(B4:B%d)" % (w, w, w)),
                                  ("R² = 1 − Σ(y − ŷ)²/Σ(y − ȳ)²", "=1-SUMXMY2(B4:B%d,C4:C%d)/DEVSQ(B4:B%d)" % (w, w, w))), 3):
        wm.cell(i, 5, et).font = NEGRO_N
        wm.cell(i, 6, fo).font = NEGRO_N
    wm.column_dimensions["E"].width = 32

    wi = wb.create_sheet("Importancia")
    wi["A1"] = "Importancia de variables (importance = TRUE; varImpPlot, p.55)"
    wi["A1"].font = TITULO
    enc(wi, 3, ("Variable", "%IncMSE", "Orden", "IncNodePurity", "Orden"))
    vs = tr["variables"]
    for i, vv in enumerate(vs, 4):
        wi.cell(i, 1, vv).font = AZUL
        wi.cell(i, 2, tr["IncMSE"][vv]).font = AZUL
        wi.cell(i, 3, "=RANK(B%d,$B$4:$B$%d)" % (i, 3 + len(vs)))
        wi.cell(i, 4, tr["IncNodePurity"][vv]).font = AZUL
        wi.cell(i, 5, "=RANK(D%d,$D$4:$D$%d)" % (i, 3 + len(vs)))
    wi.column_dimensions["A"].width = 22

    wc = wb.create_sheet("Control")
    enc(wc, 3, ("Concepto", "Excel", "Python/R", "Diferencia", "¿Coincide?"))
    control = [("Tamaño muestra árbol 1", "Bootstrap!E3", tr["n_train"]), ("Promedio de los árboles", "Observación!E3", ob["y_pred"]),
               ("RMSE", "Métricas!F3", tr["RMSE"]), ("MAE", "Métricas!F4", tr["MAE"]), ("R²", "Métricas!F5", tr["R2"])]
    for i, (c_, ref, val) in enumerate(control, 4):
        wc.cell(i, 1, c_)
        wc.cell(i, 2, "=" + ref).font = VERDE
        wc.cell(i, 3, val).font = AZUL
        wc.cell(i, 4, "=B%d-C%d" % (i, i))
        wc.cell(i, 5, '=IF(ABS(D%d)<=1E-9*MAX(1,ABS(C%d)),"sí","NO")' % (i, i)).font = NEGRO_N
    wb.save(os.path.join(I, "Demostración.xlsx"))
    print("Excel: %d comprobaciones" % len(control))


if __name__ == "__main__":
    main()
