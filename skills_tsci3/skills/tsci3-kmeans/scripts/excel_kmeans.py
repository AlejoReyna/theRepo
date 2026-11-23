#!/usr/bin/env python3
"""Arma Demostración.xlsx del k-means con la convención de OD/mochila_.xlsx.

Hojas: Resultado, Datos, Normalizacion (mín, máx, m = 1/(máx − mín), b = −m·mín, y = m·x + b),
Iter1..IterK (C0, C1, DC0, DC1, DMIN, pertenencia, C' = (SUMPRODUCT + C)/(n + 1)),
[Iteraciones: resumen con valores del programa si el libro sería demasiado grande], Control.
Las distancias se escriben término por término, como el Excel del profesor
(=((C0_1 - x_1)^2 + ... )^0.5), pero cada término usa su propia fila (sin el error T1).

Uso: .venv/bin/python excel_kmeans.py INCISO_DIR [--max-celdas 200000]
"""
import argparse
import csv
import json
import os

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter as L

AZUL, NEGRO, VERDE = Font(color="1F4E9E"), Font(color="000000"), Font(color="1E7B34")
NEGRO_N, VERDE_N, TITULO = Font(bold=True), Font(color="1E7B34", bold=True), Font(bold=True, size=13)
ENC = PatternFill("solid", fgColor="DDE4EE")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inciso")
    ap.add_argument("--max-celdas", type=int, default=200000)
    a = ap.parse_args()
    I = a.inciso
    tr = json.load(open(os.path.join(I, "traza.json"), encoding="utf-8"))
    par = json.load(open(os.path.join(I, "datos", "parametros.json"), encoding="utf-8"))
    cols = tr["columnas"]
    with open(os.path.join(I, "datos", par["archivo"]), newline="", encoding="utf-8-sig") as fh:
        filas = []
        for f in csv.DictReader(fh):
            try:
                filas.append([float(str(f[c]).replace(",", "")) for c in cols])
            except (ValueError, TypeError):
                pass
    n, nv = len(filas), len(cols)
    N0, N1 = 7, 7 + n - 1                      # filas de datos en Normalizacion
    completas = n * len(tr["iteraciones"]) <= a.max_celdas
    hojas_iter = tr["iteraciones"] if completas else tr["iteraciones"][:1]
    control = []
    wb = Workbook()
    res = wb.active
    res.title = "Resultado"

    ws = wb.create_sheet("Datos")
    ws.cell(1, 1, "ID").font = NEGRO_N
    for j, c in enumerate(cols, 2):
        ws.cell(1, j, c).font = NEGRO_N
    for i, f in enumerate(filas, 2):
        ws.cell(i, 1, i - 1).font = AZUL
        for j, v in enumerate(f, 2):
            ws.cell(i, j, v).font = AZUL

    wn = wb.create_sheet("Normalizacion")
    wn.cell(1, 1, "y = m·x + b;  m = 1/(máx − mín);  b = −m·mín  (OD/mochila_.xlsx B4:D5)").font = TITULO
    for j, c in enumerate(cols, 2):
        wn.cell(2, j, c).font = NEGRO_N
        col = L(j)
        rng = "Datos!%s$2:%s$%d" % (col, col, n + 1)
        wn.cell(3, j, "=MIN(%s)" % rng).font = VERDE
        wn.cell(4, j, "=MAX(%s)" % rng).font = VERDE
        wn.cell(5, j, "=1/(%s4-%s3)" % (col, col)).font = NEGRO
        wn.cell(6, j, "=-%s5*%s3" % (col, col)).font = NEGRO
        nm = tr["normalizacion"][c]
        control.append(("m de %s" % c, "Normalizacion!%s5" % col, nm["m"]))
        control.append(("b de %s" % c, "Normalizacion!%s6" % col, nm["b"]))
        for i in range(n):
            wn.cell(N0 + i, j, "=%s$5*Datos!%s%d+%s$6" % (col, col, i + 2, col)).font = VERDE
    for r, et in zip(range(3, 7), ("mín", "máx", "m", "b")):
        wn.cell(r, 1, et).font = NEGRO_N
    wn.cell(N0 - 1, 1, "ID").font = NEGRO_N
    for i in range(n):
        wn.cell(N0 + i, 1, i + 1).font = AZUL

    previa = None
    for it in hojas_iter:
        k = it["iteracion"]
        ws = wb.create_sheet("Iter%d" % k)
        ws.cell(1, 1, "Iteración %d: distancia euclidiana a C0 y C1, pertenencia y actualización C' = (Σx·pertenencia + C)/(n + 1) (T7)" % k).font = TITULO
        for j, c in enumerate(cols, 2):
            ws.cell(3, j, c).font = NEGRO_N
            col = L(j)
            ncol = "Normalizacion!%s$%d:%s$%d" % (col, N0, col, N1)
            if previa is None:
                ws.cell(4, j, "=MIN(%s)" % ncol).font = VERDE
                ws.cell(5, j, "=MAX(%s)" % ncol).font = VERDE
            else:
                ws.cell(4, j, "=%s!%s7" % (previa, col)).font = VERDE
                ws.cell(5, j, "=%s!%s8" % (previa, col)).font = VERDE
            ws.cell(7, j, "=(SUMPRODUCT(%s,$E$%d:$E$%d)+%s4)/($E$10+1)" % (ncol, 12, 11 + n, col)).font = VERDE
            ws.cell(8, j, "=(SUMPRODUCT(%s,$F$%d:$F$%d)+%s5)/($F$10+1)" % (ncol, 12, 11 + n, col)).font = VERDE
            control.append(("Iter%d C0' %s" % (k, c), "Iter%d!%s7" % (k, col), it["C0_nuevo"][j - 2]))
            control.append(("Iter%d C1' %s" % (k, c), "Iter%d!%s8" % (k, col), it["C1_nuevo"][j - 2]))
        for r, et in ((4, "C0"), (5, "C1"), (7, "C0'"), (8, "C1'")):
            ws.cell(r, 1, et).font = NEGRO_N
        ws.cell(10, 1, "Sumas").font = NEGRO_N
        for j, et in enumerate(("ID", "DC0", "DC1", "DMIN", "C0", "C1"), 1):
            c = ws.cell(11, j, et)
            c.font, c.fill = NEGRO_N, ENC
        for i in range(n):
            r, nr = 12 + i, N0 + i
            ws.cell(r, 1, i + 1).font = AZUL
            for colx, fila_c in ((2, 4), (3, 5)):
                terminos = "+".join("(%s$%d-Normalizacion!%s%d)^2" % (L(j), fila_c, L(j), nr) for j in range(2, nv + 2))
                ws.cell(r, colx, "=(%s)^0.5" % terminos).font = VERDE
            ws.cell(r, 4, "=MIN(B%d:C%d)" % (r, r)).font = NEGRO
            ws.cell(r, 5, "=IF(D%d=B%d,1,0)" % (r, r)).font = NEGRO
            ws.cell(r, 6, "=IF(D%d=C%d,1,0)" % (r, r)).font = NEGRO
        for colx in (4, 5, 6):
            ws.cell(10, colx, "=SUM(%s12:%s%d)" % (L(colx), L(colx), 11 + n)).font = NEGRO_N
        control += [("Iter%d ΣDMIN" % k, "Iter%d!D10" % k, it["suma_dmin"]),
                    ("Iter%d |C0|" % k, "Iter%d!E10" % k, it["n0"]), ("Iter%d |C1|" % k, "Iter%d!F10" % k, it["n1"])]
        ws.freeze_panes = "B12"
        previa = "Iter%d" % k

    if not completas:
        ws = wb.create_sheet("Iteraciones")
        ws.cell(1, 1, "Iteraciones 2 en adelante (valores de resolver.py; el libro con fórmulas tendría %d filas por hoja)" % n).font = TITULO
        enc = ["Iteración", "|C0|", "|C1|", "ΣDMIN", "Cambios"] + ["C0 %s" % c for c in cols] + ["C1 %s" % c for c in cols]
        for j, e in enumerate(enc, 1):
            c = ws.cell(3, j, e)
            c.font, c.fill = NEGRO_N, ENC
        for i, it in enumerate(tr["iteraciones"], 4):
            for j, v in enumerate([it["iteracion"], it["n0"], it["n1"], it["suma_dmin"], it["cambios"]] + it["C0"] + it["C1"], 1):
                ws.cell(i, j, v).font = AZUL

    wc = wb.create_sheet("Control")
    wc.cell(1, 1, "Control: cifras del Excel contra traza.json (resolver.py)").font = TITULO
    for j, e in enumerate(("Concepto", "Excel", "Traza", "Diferencia", "¿Coincide?"), 1):
        c = wc.cell(3, j, e)
        c.font, c.fill = NEGRO_N, ENC
    for i, (concepto, ref, v) in enumerate(control, 4):
        wc.cell(i, 1, concepto)
        wc.cell(i, 2, "=" + ref).font = VERDE
        wc.cell(i, 3, v).font = AZUL
        wc.cell(i, 4, "=B%d-C%d" % (i, i))
        wc.cell(i, 5, '=IF(ABS(D%d)<=1E-6*MAX(1,ABS(C%d)),"sí","NO")' % (i, i)).font = NEGRO_N
    u = len(control) + 3
    wc.cell(u + 2, 1, "Coinciden").font = NEGRO_N
    wc.cell(u + 2, 2, '=COUNTIF(E4:E%d,"sí")&" de "&COUNTA(E4:E%d)' % (u, u)).font = NEGRO_N
    wc.column_dimensions["A"].width = 26

    r = tr["resumen"]
    ult = "Iter%d" % hojas_iter[-1]["iteracion"]
    filas_r = [("Problema", tr.get("problema", ""), AZUL), ("Registros", n, AZUL), ("Variables", ", ".join(cols), AZUL),
               ("Grupos (k)", 2, AZUL), ("Iteraciones hasta que la pertenencia no cambia", r["iteraciones"], AZUL),
               ("|C0| final", ("=%s!E10" % ult) if completas else r["n0"], VERDE_N if completas else AZUL),
               ("|C1| final", ("=%s!F10" % ult) if completas else r["n1"], VERDE_N if completas else AZUL),
               ("ΣDMIN final", ("=%s!D10" % ult) if completas else r["suma_dmin"], VERDE_N if completas else AZUL),
               ("Control", "=Control!B%d" % (u + 2), VERDE_N)]
    res.cell(1, 1, "K-means (convención del ejercicio de clase)").font = TITULO
    for i, (x, y, f) in enumerate(filas_r, 3):
        res.cell(i, 1, x).font = NEGRO_N
        res.cell(i, 2, y).font = f
    rr = len(filas_r) + 4
    res.cell(rr, 1, "Centroides finales").font = NEGRO_N
    for j, c in enumerate(cols, 2):
        res.cell(rr, j, c).font = NEGRO_N
        nm = tr["normalizacion"][c]
        for k, nombre in enumerate(("C0", "C1")):
            res.cell(rr + 1 + k, 1, "%s normalizado" % nombre)
            res.cell(rr + 1 + k, j, r[nombre][j - 2]).font = AZUL
            res.cell(rr + 3 + k, 1, "%s en unidades originales = (y − b)/m" % nombre)
            res.cell(rr + 3 + k, j, "=(%s%d-Normalizacion!%s6)/Normalizacion!%s5" % (L(j), rr + 1 + k, L(j), L(j))).font = VERDE
    res.cell(rr + 6, 1, "Un empate (DMIN = DC0 = DC1) cuenta en ambos grupos, como en el Excel del profesor. "
                        "Colores: azul = dato o resultado del programa; negro = fórmula; verde = fórmula con datos de otra hoja.")
    res.column_dimensions["A"].width = 44
    wb.save(os.path.join(I, "Demostración.xlsx"))
    print("Excel: %s (%d hojas de iteración con fórmulas%s; %d comprobaciones)" % (
        os.path.join(I, "Demostración.xlsx"), len(hojas_iter), "" if completas else ", resto como valores", len(control)))


if __name__ == "__main__":
    main()
