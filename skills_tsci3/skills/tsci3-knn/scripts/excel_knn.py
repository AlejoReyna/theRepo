#!/usr/bin/env python3
"""Demostración.xlsx de KNN (OD/AM R.pdf p.43-48, p.51-53).

Hojas:
  Distancias — filas de entrenamiento (índices de R, semilla 42), clase y distancia euclidiana al
               punto de prueba con SQRT(SUMXMY2) (sin normalizar, T5); orden con RANK.
  Voto       — los k vecinos con SMALL/MATCH, sus clases, el conteo por clase y la clase ganadora.
  Elegir k   — exactitud media de la validación cruzada de 10 pliegues por k (p.53) y el mejor k;
               WCSS por k (p.46) con primera y segunda diferencia para el codo (p.47).
  Control    — Excel contra Python/R.
Uso: .venv/bin/python excel_knn.py INCISO_DIR
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
    cols, K = par["columnas"], tr["k"]
    col_y = par.get("y") or ("precio" if "precio" in datos[0] else [c for c in datos[0] if c not in cols][0])
    med = tr["mediana"]
    P = tr["punto"]
    wb = Workbook()
    wd = wb.active
    wd.title = "Distancias"
    wd["A1"] = "KNN (p.48): distancia euclidiana de la fila de prueba %d a cada fila de entrenamiento (sin normalizar, T5)" % P["fila"]
    wd["A1"].font = TITULO
    enc(wd, 3, ["Punto de prueba"] + cols + ["clase real"])
    wd.cell(4, 1, "fila %d" % P["fila"]).font = AZUL
    for j, v in enumerate(P["x"], 2):
        wd.cell(4, j, v).font = AZUL
    wd.cell(4, 2 + len(cols), P["real"]).font = AZUL
    enc(wd, 6, ["fila (datos)"] + cols + [col_y, "clase (≥ mediana)", "distancia", "orden"])
    n = len(tr["train_index"])
    last = chr(ord("A") + len(cols))                       # columna de la última variable
    cP, cC, cD, cR = [chr(ord("A") + len(cols) + i) for i in (1, 2, 3, 4)]
    wd["J2"], wd["K2"] = "Mediana", med
    wd["K2"].font = AZUL
    for r, f in enumerate(tr["train_index"], 7):
        fila = datos[f - 1]
        wd.cell(r, 1, f).font = AZUL
        for j, c in enumerate(cols, 2):
            wd.cell(r, j, float(fila[c])).font = AZUL
        wd.cell(r, len(cols) + 2, float(fila[col_y])).font = AZUL
        wd.cell(r, len(cols) + 3, '=IF(%s%d>=$K$2,"alto","bajo")' % (cP, r))
        wd.cell(r, len(cols) + 4, "=SQRT(SUMXMY2(B%d:%s%d,$B$4:$%s$4))" % (r, last, r, last))
        wd.cell(r, len(cols) + 5, "=RANK(%s%d,$%s$7:$%s$%d,1)" % (cD, r, cD, cD, 6 + n))
    u = 6 + n
    wv = wb.create_sheet("Voto")
    wv["A1"] = "Los k = %d vecinos más cercanos y el voto por mayoría (p.44, p.48)" % K
    wv["A1"].font = TITULO
    enc(wv, 3, ("Vecino", "Distancia", "Fila (datos)", "Clase"))
    D = "Distancias!$%s$7:$%s$%d" % (cD, cD, u)
    for i in range(1, K + 1):
        r = 3 + i
        wv.cell(r, 1, i)
        wv.cell(r, 2, "=SMALL(%s,%d)" % (D, i))
        wv.cell(r, 3, "=INDEX(Distancias!$A$7:$A$%d,MATCH(B%d,%s,0))" % (u, r, D))
        wv.cell(r, 4, "=INDEX(Distancias!$%s$7:$%s$%d,MATCH(B%d,%s,0))" % (cC, cC, u, r, D))
    v = 4 + K
    wv.cell(v + 1, 1, "Votos alto").font = NEGRO_N
    wv.cell(v + 1, 2, '=COUNTIF(D4:D%d,"alto")' % (v - 1))
    wv.cell(v + 2, 1, "Votos bajo").font = NEGRO_N
    wv.cell(v + 2, 2, '=COUNTIF(D4:D%d,"bajo")' % (v - 1))
    wv.cell(v + 3, 1, "Predicción").font = NEGRO_N
    wv.cell(v + 3, 2, '=IF(B%d>B%d,"alto",IF(B%d<B%d,"bajo","empate (R decide al azar, T15)"))' % (v + 1, v + 2, v + 1, v + 2)).font = NEGRO_N
    wv.cell(v + 4, 1, "(k+1)-ésima distancia").font = NEGRO_N
    wv.cell(v + 4, 2, "=SMALL(%s,%d)" % (D, K + 1))
    wv.cell(v + 5, 1, "¿Empate en la frontera?").font = NEGRO_N
    wv.cell(v + 5, 2, '=IF(B%d^2<=B%d^2*(1+1E-4),"sí: entra al voto","no")' % (v + 4, v - 1))
    wv.column_dimensions["A"].width = 24

    wk = wb.create_sheet("Elegir k")
    wk["A1"] = "Determinación de k: validación cruzada de 10 pliegues (p.51-53) y codo del WCSS (p.45-47)"
    wk["A1"].font = TITULO
    enc(wk, 3, ("k", "Exactitud CV", "¿Mejor?"))
    ks = list(tr["cv"].items())
    for i, (k, a) in enumerate(ks, 4):
        wk.cell(i, 1, int(k)).font = AZUL
        wk.cell(i, 2, a).font = AZUL
    e = 3 + len(ks)
    for i in range(4, e + 1):
        wk.cell(i, 3, '=IF(B%d=MAX($B$4:$B$%d),"◀","")' % (i, e))
    wk.cell(e + 2, 1, "Mejor k").font = NEGRO_N
    wk.cell(e + 2, 2, "=INDEX(A4:A%d,MATCH(MAX(B4:B%d),B4:B%d,0))" % (e, e, e)).font = NEGRO_N
    enc(wk, 3, ("k", "WCSS", "Δ1 = W(k−1) − W(k)", "Δ2 = Δ1(k) − Δ1(k+1)"), 6)
    for i, wv_ in enumerate(tr["wcss"], 4):
        k = i - 3
        wk.cell(i, 6, k).font = AZUL
        wk.cell(i, 7, wv_).font = AZUL
        if k > 1:
            wk.cell(i, 8, "=G%d-G%d" % (i - 1, i))
        if 1 < k < len(tr["wcss"]):
            wk.cell(i, 9, "=H%d-H%d" % (i, i + 1))
    f = 3 + len(tr["wcss"])
    wk.cell(f + 2, 6, "Codo (máx. Δ2)").font = NEGRO_N
    wk.cell(f + 2, 7, "=INDEX(F5:F%d,MATCH(MAX(I5:I%d),I5:I%d,0))" % (f - 1, f - 1, f - 1)).font = NEGRO_N
    wk.cell(f + 3, 6, "WCSS de kmeans (nstart = 10, semilla 42) sobre las columnas de p.48 sin normalizar: lo domina m2_terreno.")

    wc = wb.create_sheet("Control")
    enc(wc, 3, ("Concepto", "Excel", "Python/R", "Diferencia", "¿Coincide?"))
    control = [("Distancia vecino %d" % (i + 1), "Voto!B%d" % (4 + i), vv["d"]) for i, vv in enumerate(P["vecinos"][:K])]
    control += [("Fila vecino %d" % (i + 1), "Voto!C%d" % (4 + i), vv["fila"]) for i, vv in enumerate(P["vecinos"][:K])]
    control += [("Votos alto", "Voto!B%d" % (v + 1), P["votos"].get("alto", 0)), ("Votos bajo", "Voto!B%d" % (v + 2), P["votos"].get("bajo", 0)),
                ("Mejor k", "'Elegir k'!B%d" % (e + 2), tr["best_k"]), ("Codo", "'Elegir k'!G%d" % (f + 2), tr["codo"])]
    for i, (c_, ref, val) in enumerate(control, 4):
        wc.cell(i, 1, c_)
        wc.cell(i, 2, "=" + ref).font = VERDE
        wc.cell(i, 3, val).font = AZUL
        wc.cell(i, 4, "=B%d-C%d" % (i, i))
        wc.cell(i, 5, '=IF(ABS(D%d)<=1E-9*MAX(1,ABS(C%d)),"sí","NO")' % (i, i)).font = NEGRO_N
    r = 4 + len(control)
    wc.cell(r, 1, "Predicción del punto")
    wc.cell(r, 2, "=Voto!B%d" % (v + 3)).font = VERDE
    wc.cell(r, 3, P["pred"] or "empate").font = AZUL
    wc.cell(r, 5, '=IF(B%d=C%d,"sí","NO")' % (r, r)).font = NEGRO_N
    wb.save(os.path.join(I, "Demostración.xlsx"))
    print("Excel: %d comprobaciones" % (len(control) + 1))


if __name__ == "__main__":
    main()
