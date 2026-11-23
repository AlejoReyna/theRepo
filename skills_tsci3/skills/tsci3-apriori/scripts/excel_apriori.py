#!/usr/bin/env python3
"""Arma Demostración.xlsx de Apriori con el formato de OD/AP (1).xlsx.

Hojas: Resultado, Datos, Nivel1..NivelK (itemsets frecuentes de cada nivel con su conteo por
fórmula), Reglas («IF X THEN Y»: N, NX, NY, NX∧Y, S = NX∧Y/N, C = NX∧Y/NX, L = NX∧Y·N/(NX·NY);
las reglas pedidas y las 20 de mayor lift), Composicion («R1 THEN R2», si se pide), Control.
Los conteos son SUMPRODUCT(1*EXACT(columna, valor)*...) sobre Datos (sin comodines, T20).

Uso: .venv/bin/python excel_apriori.py INCISO_DIR
"""
import csv
import json
import os
import sys

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter as L

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from resolver_apriori import apriori, leer  # noqa: E402

AZUL, NEGRO, VERDE = Font(color="1F4E9E"), Font(color="000000"), Font(color="1E7B34")
NEGRO_N, VERDE_N, TITULO = Font(bold=True), Font(color="1E7B34", bold=True), Font(bold=True, size=13)
ENC = PatternFill("solid", fgColor="DDE4EE")
MAX_NIVEL = 2000


def enc(ws, fila, nombres, col=1):
    for j, x in enumerate(nombres):
        c = ws.cell(fila, col + j, x)
        c.font, c.fill = NEGRO_N, ENC


def main():
    I = sys.argv[1]
    tr = json.load(open(os.path.join(I, "traza.json"), encoding="utf-8"))
    par = json.load(open(os.path.join(I, "datos", "parametros.json"), encoding="utf-8"))
    na = set(par.get("na", ["", "NA"]))
    ruta = os.path.join(I, "datos", par["archivo"])
    cols, trans = leer(ruta, par.get("columnas"), na)
    filas = list(csv.DictReader(open(ruta, newline="", encoding="utf-8-sig")))
    n = len(filas)
    col_de = {c: L(j + 1) for j, c in enumerate(cols)}
    rango = lambda c: "Datos!$%s$2:$%s$%d" % (col_de[c], col_de[c], n + 1)

    def cuenta(items):
        if not items:
            return "=$B$2" if False else "=Reglas!$B$2"
        partes = ["1"]
        for it in items:
            c, v = it.split("=", 1)
            partes.append("EXACT(%s,%s)" % (rango(c), '"' + v.replace('"', '""') + '"'))
        return "=SUMPRODUCT(%s)" % "*".join(partes)

    control = []
    wb = Workbook()
    res = wb.active
    res.title = "Resultado"
    ws = wb.create_sheet("Datos")
    enc(ws, 1, cols)
    for i, f in enumerate(filas, 2):
        for j, c in enumerate(cols, 1):
            v = f[c]
            ws.cell(i, j, "NA" if v in na else v).font = AZUL

    wr = wb.create_sheet("Reglas")
    wr.cell(1, 1, "IF X THEN Y").font = TITULO
    wr.cell(2, 1, "N").font = NEGRO_N
    wr.cell(2, 2, "=ROWS(%s)" % rango(cols[0])).font = VERDE_N
    enc(wr, 4, ["Regla", "Origen", "NX", "NY", "NX^Y", "S = NX^Y/N", "C = NX^Y/NX", "L = NX^Y·N/(NX·NY)"])
    lista = [(p, "pedida") for p in tr.get("reglas_pedidas", [])]
    vistas = {(tuple(p["lhs"]), p["rhs"]) for p, _ in lista}
    for r in tr["reglas"]:
        if len(lista) >= len(tr.get("reglas_pedidas", [])) + 20:
            break
        if (tuple(r["lhs"]), r["rhs"]) not in vistas:
            lista.append((r, "mayor lift"))
    for i, (r, origen) in enumerate(lista, 5):
        wr.cell(i, 1, "IF(%s) THEN(%s)" % (" AND ".join(r["lhs"]) or "∅", r["rhs"])).font = AZUL
        wr.cell(i, 2, origen).font = AZUL
        wr.cell(i, 3, cuenta(r["lhs"])).font = VERDE
        wr.cell(i, 4, cuenta([r["rhs"]])).font = VERDE
        wr.cell(i, 5, cuenta(r["lhs"] + [r["rhs"]])).font = VERDE
        wr.cell(i, 6, "=E%d/$B$2" % i)
        wr.cell(i, 7, '=IF(C%d=0,"—",E%d/C%d)' % (i, i, i))
        wr.cell(i, 8, '=IF(C%d*D%d=0,"—",(E%d*$B$2)/(C%d*D%d))' % (i, i, i, i, i))
        control += [("NX^Y %s" % wr.cell(i, 1).value[:40], "Reglas!E%d" % i, r["NXY"]),
                    ("S %s" % wr.cell(i, 1).value[:40], "Reglas!F%d" % i, r["soporte"])]
        if r.get("lift") is not None:
            control.append(("L %s" % wr.cell(i, 1).value[:40], "Reglas!H%d" % i, r["lift"]))
    wr.column_dimensions["A"].width = 70

    comp = par.get("composicion", [])
    if comp:
        wcp = wb.create_sheet("Composicion")
        wcp.cell(1, 1, "R1 THEN R2: dos reglas con el mismo antecedente → IF X THEN (Y1 AND Y2) (OD/AP (1).xlsx H24:K25)").font = TITULO
        enc(wcp, 3, ["Regla compuesta", "NX", "NY1^Y2", "NX^Y1^Y2", "S", "C", "L"])
        for i, cpar in enumerate(comp, 4):
            x, ys = cpar["si"], cpar["entonces"]
            wcp.cell(i, 1, "IF(%s) THEN(%s)" % (" AND ".join(x), " AND ".join(ys))).font = AZUL
            wcp.cell(i, 2, cuenta(x)).font = VERDE
            wcp.cell(i, 3, cuenta(ys)).font = VERDE
            wcp.cell(i, 4, cuenta(x + ys)).font = VERDE
            wcp.cell(i, 5, "=D%d/Reglas!$B$2" % i)
            wcp.cell(i, 6, '=IF(B%d=0,"—",D%d/B%d)' % (i, i, i))
            wcp.cell(i, 7, '=IF(B%d*C%d=0,"—",D%d*Reglas!$B$2/(B%d*C%d))' % (i, i, i, i, i))
        wcp.column_dimensions["A"].width = 70

    frec = apriori(trans, tr["soporte_min"], par.get("maxlen", 10))
    for k, nv in enumerate(frec, 1):
        wn = wb.create_sheet("Nivel%d" % k)
        wn.cell(1, 1, "Nivel %d: itemsets de %d ítems con soporte >= %g (cierre descendente: sus subconjuntos ya eran frecuentes)" % (
            k, k, tr["soporte_min"])).font = TITULO
        enc(wn, 3, ["Itemset", "Conteo", "Soporte", "¿Frecuente?"])
        items = sorted(nv.items(), key=lambda kv: (-kv[1], sorted(kv[0])))
        for i, (s, c) in enumerate(items[:MAX_NIVEL], 4):
            wn.cell(i, 1, "{%s}" % ", ".join(sorted(s))).font = AZUL
            wn.cell(i, 2, cuenta(sorted(s))).font = VERDE
            wn.cell(i, 3, "=B%d/Reglas!$B$2" % i)
            wn.cell(i, 4, '=IF(C%d>=%s,"sí","no")' % (i, tr["soporte_min"]))
        u = 3 + min(len(items), MAX_NIVEL)
        wn.cell(u + 2, 1, "Itemsets frecuentes del nivel").font = NEGRO_N
        wn.cell(u + 2, 2, '=COUNTIF(D4:D%d,"sí")' % u).font = NEGRO_N
        if len(items) > MAX_NIVEL:
            wn.cell(u + 3, 1, "Se muestran %d de %d (los demás están en traza.json)" % (MAX_NIVEL, len(items)))
        else:
            control.append(("Itemsets frecuentes nivel %d" % k, "Nivel%d!B%d" % (k, u + 2), tr["niveles"][k - 1]["itemsets"]))
        wn.column_dimensions["A"].width = 80

    wc = wb.create_sheet("Control")
    wc.cell(1, 1, "Control: cifras del Excel contra traza.json (resolver.py)").font = TITULO
    enc(wc, 3, ["Concepto", "Excel", "Traza", "Diferencia", "¿Coincide?"])
    for i, (concepto, ref, v) in enumerate(control, 4):
        wc.cell(i, 1, concepto)
        wc.cell(i, 2, "=" + ref).font = VERDE
        wc.cell(i, 3, v).font = AZUL
        wc.cell(i, 4, "=B%d-C%d" % (i, i))
        wc.cell(i, 5, '=IF(ABS(D%d)<=1E-9,"sí","NO")' % i).font = NEGRO_N
    uc = len(control) + 3
    wc.cell(uc + 2, 1, "Coinciden").font = NEGRO_N
    wc.cell(uc + 2, 2, '=COUNTIF(E4:E%d,"sí")&" de "&COUNTA(E4:E%d)' % (uc, uc)).font = NEGRO_N
    wc.column_dimensions["A"].width = 50

    res.cell(1, 1, "Reglas de asociación (Apriori)").font = TITULO
    filas_r = [("Problema", tr.get("problema", "")), ("Transacciones (N)", "=Reglas!B2"), ("Columnas", ", ".join(cols)),
               ("Soporte mínimo", tr["soporte_min"]), ("Confianza mínima", tr["confianza_min"]),
               ("Itemsets frecuentes por nivel", ", ".join(str(nv["itemsets"]) for nv in tr["niveles"])),
               ("Reglas que cumplen", tr["n_reglas"]), ("Control", "=Control!B%d" % (uc + 2))]
    for i, (x, y) in enumerate(filas_r, 3):
        res.cell(i, 1, x).font = NEGRO_N
        res.cell(i, 2, y).font = VERDE_N if isinstance(y, str) and y.startswith("=") else AZUL
    res.cell(len(filas_r) + 4, 1, "S = NX^Y/N; C = NX^Y/NX; L = NX^Y·N/(NX·NY) (OD/AP (1).xlsx M4:O11). Celdas vacías y «NA» no son ítems (T22).")
    res.column_dimensions["A"].width = 34
    wb.save(os.path.join(I, "Demostración.xlsx"))
    print("Excel: %s (%d comprobaciones)" % (os.path.join(I, "Demostración.xlsx"), len(control)))


if __name__ == "__main__":
    main()
