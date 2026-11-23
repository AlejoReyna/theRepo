#!/usr/bin/env python3
"""Demostración.xlsx de la matriz de confusión (OD/AM R.pdf p.49-50).

  origen csv   — hoja Clases (real, pred) y la tabla 2×2 con COUNTIFS; márgenes y métricas en fórmula.
  origen tabla — la tabla del artículo; márgenes y métricas en fórmula; contraste con lo reportado.
  reconstruir  — una fila por tabla compatible, con CA y precisión/recall/F1 ponderados en fórmula.
Control: Excel contra el oráculo. Uso: .venv/bin/python excel_matriz.py INCISO_DIR
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


def tabla(ws, tr, par, fuente_celdas):
    """Escribe la tabla 2×2 (real en filas, p.49) en B4:C5 y las métricas; devuelve {métrica: celda}."""
    pos = par.get("positiva", "positivo")
    ws["A1"] = "Matriz de confusión: clase real en las filas, predicha en las columnas (OD/AM R.pdf p.49)"
    ws["A1"].font = TITULO
    enc(ws, 3, ("", "pred %s" % pos, "pred no %s" % pos, "total"))
    ws["A4"], ws["A5"], ws["A6"] = "real %s" % pos, "real no %s" % pos, "total"
    for (r, c), v in fuente_celdas.items():
        ws.cell(r, c, v).font = AZUL if not isinstance(v, str) else NEGRO_N
    ws["D4"], ws["D5"] = "=B4+C4", "=B5+C5"               # p, n
    ws["B6"], ws["C6"], ws["D6"] = "=B4+B5", "=C4+C5", "=SUM(B4:C5)"   # p', n', N
    for c in ("A4", "A5", "A6"):
        ws[c].font = NEGRO_N
    ws["F3"], ws["G3"] = "Márgenes", ""
    for i, (et, f) in enumerate((("p", "=D4"), ("n", "=D5"), ("p′", "=B6"), ("n′", "=C6"), ("N", "=D6")), 4):
        ws.cell(i, 6, et).font = NEGRO_N
        ws.cell(i, 7, f)
    enc(ws, 10, ("Métrica", "Fórmula", "Valor"))
    met = [("Accuracy", "Σdiagonal / N (p.50)", "=(B4+C5)/D6"),
           ("Precision", "TP / (TP + FP) (AD25-03 p.3)", "=IF(B6=0,NA(),B4/B6)"),
           ("Recall", "TP / (TP + FN) (AD25-03 p.3)", "=IF(D4=0,NA(),B4/D4)"),
           ("Specificity", "TN / (TN + FP)", "=IF(D5=0,NA(),C5/D5)"),
           ("NPV", "TN / (TN + FN)", "=IF(C6=0,NA(),C5/C6)"),
           ("F1", "2·P·R / (P + R)", "=2*C12*C13/(C12+C13)"),
           ("Kappa", "(Acc − pe) / (1 − pe)", "=(C11-(D4*B6+D5*C6)/D6^2)/(1-(D4*B6+D5*C6)/D6^2)")]
    celdas = {}
    for i, (k, d, f) in enumerate(met, 11):
        ws.cell(i, 1, k).font = NEGRO_N
        ws.cell(i, 2, d)
        ws.cell(i, 3, f).font = NEGRO_N
        celdas[k] = "Matriz!C%d" % i
    ws.cell(19, 1, "T24: OD/AM R.pdf p.50 pasa table(real, pred) a caret, que lee las filas como predicción: "
                   "su Sensitivity es esta Precision y su Pos Pred Value es este Recall. La exactitud no cambia.")
    ws.column_dimensions["A"].width = 20
    ws.column_dimensions["B"].width = 30
    return celdas


def main():
    I = sys.argv[1]
    tr = json.load(open(os.path.join(I, "traza.json"), encoding="utf-8"))
    par = json.load(open(os.path.join(I, "datos", "parametros.json"), encoding="utf-8"))
    wb = Workbook()
    ws = wb.active
    ws.title = "Matriz"
    control = []
    if par["origen"] == "csv":
        cl = list(csv.DictReader(open(os.path.join(I, "datos", "clases.csv"), encoding="utf-8")))
        wcl = wb.create_sheet("Clases")
        enc(wcl, 1, ("fila", "real", "pred"))
        for i, r in enumerate(cl, 2):
            wcl.cell(i, 1, int(r["fila"])).font = AZUL
            wcl.cell(i, 2, r["real"]).font = AZUL
            wcl.cell(i, 3, r["pred"]).font = AZUL
        u = len(cl) + 1
        pos = par["positiva"]
        R, P = "Clases!$B$2:$B$%d" % u, "Clases!$C$2:$C$%d" % u
        f = {(4, 2): '=COUNTIFS(%s,"%s",%s,"%s")' % (R, pos, P, pos), (4, 3): '=COUNTIFS(%s,"%s",%s,"<>%s")' % (R, pos, P, pos),
             (5, 2): '=COUNTIFS(%s,"<>%s",%s,"%s")' % (R, pos, P, pos), (5, 3): '=COUNTIFS(%s,"<>%s",%s,"<>%s")' % (R, pos, P, pos)}
        celdas = tabla(ws, tr, par, f)
        for k in ("TP", "FN", "FP", "TN"):
            control.append((k, "Matriz!" + {"TP": "B4", "FN": "C4", "FP": "B5", "TN": "C5"}[k], tr[k]))
    elif par["origen"] == "tabla":
        celdas = tabla(ws, tr, par, {(4, 2): tr["TP"], (4, 3): tr["FN"], (5, 2): tr["FP"], (5, 3): tr["TN"]})
        ws["E10"], ws["F10"] = "Reportado", "¿Igual al truncar/redondear?"
        for c in ("E10", "F10"):
            ws[c].font, ws[c].fill = NEGRO_N, ENC
        for i, k in enumerate(("Accuracy", "Precision", "Recall", "Specificity", "NPV", "F1", "Kappa"), 11):
            if k in par.get("reportado", {}):
                v = par["reportado"][k]
                d = len(repr(v).split(".")[1]) if "." in repr(v) else 0
                ws.cell(i, 5, v).font = AZUL
                ws.cell(i, 6, '=IF(OR(ROUND(C%d,%d)=E%d,ROUNDDOWN(C%d,%d)=E%d),"sí","no")' % (i, d, i, i, d, i))
        ws["A21"] = "Inconsistencias del artículo (T4):"
        ws["A21"].font = NEGRO_N
        for i, x in enumerate(tr.get("inconsistencias", []), 22):
            ws.cell(i, 1, "• " + x)
        if par.get("N_declarado"):
            ws["F9"], ws["G9"] = "N declarado", par["N_declarado"]
            ws["G9"].font = AZUL
            ws["H9"] = '=IF(G9=D6,"coincide","≠ N de la tabla")'
    if par["origen"] in ("csv", "tabla"):
        for k in ("Accuracy", "Precision", "Recall", "Specificity", "NPV", "F1", "Kappa"):
            if tr["metricas"].get(k) is not None:
                control.append((k, celdas[k], tr["metricas"][k]))
    else:
        ws["A1"] = "Tablas 2×2 compatibles con el reporte de %s (promedio ponderado por la clase real)" % par["problema"][:40]
        ws["A1"].font = TITULO
        enc(ws, 3, ("TP", "FN", "FP", "TN", "N", "CA", "Prec. pond.", "Recall pond.", "F1 pond.", "¿Redondea a lo reportado?", "p′"))
        rep = par["reportado"]
        dec = par.get("decimales", 3)
        for i, s in enumerate(tr["tablas_compatibles"], 4):
            for j, k in enumerate(("TP", "FN", "FP", "TN"), 1):
                ws.cell(i, j, s[k]).font = AZUL
            ws.cell(i, 5, "=SUM(A%d:D%d)" % (i, i))
            ws.cell(i, 6, "=(A%d+D%d)/E%d" % (i, i, i))
            p, n, pp, nn = "(A%d+B%d)" % (i, i), "(C%d+D%d)" % (i, i), "(A%d+C%d)" % (i, i), "(B%d+D%d)" % (i, i)
            ws.cell(i, 7, "=(%s*A%d/%s+%s*D%d/%s)/E%d" % (p, i, pp, n, i, nn, i))
            ws.cell(i, 8, "=(%s*A%d/%s+%s*D%d/%s)/E%d" % (p, i, p, n, i, n, i))
            f1p = "2*(A{i}/{pp})*(A{i}/{p})/((A{i}/{pp})+(A{i}/{p}))".format(i=i, p=p, pp=pp)
            f1n = "2*(D{i}/{nn})*(D{i}/{n})/((D{i}/{nn})+(D{i}/{n}))".format(i=i, n=n, nn=nn)
            ws.cell(i, 9, "=(%s*%s+%s*%s)/E%d" % (p, f1p, n, f1n, i))
            ws.cell(i, 10, '=IF(AND(ROUND(F{i},{d})={ca},ROUND(G{i},{d})={pr},ROUND(H{i},{d})={re},ROUND(I{i},{d})={f1}),"sí","NO")'.format(
                i=i, d=dec, ca=rep["CA"], pr=rep["Precision"], re=rep["Recall"], f1=rep["F1"]))
            ws.cell(i, 11, "=%s" % pp)
            control.append(("Tabla %d redondea" % (i - 3), "IF(Matriz!J%d=\"sí\",1,0)" % i, 1))
        k = 5 + len(tr["tablas_compatibles"])
        ws.cell(k, 1, "Con los %s predichos positivos de p.11, la única tabla es la de p′ = %s." % (
            par.get("predichos_positivos"), par.get("predichos_positivos"))).font = NEGRO_N
    wc = wb.create_sheet("Control")
    enc(wc, 3, ("Concepto", "Excel", "Python/R", "Diferencia", "¿Coincide?"))
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
