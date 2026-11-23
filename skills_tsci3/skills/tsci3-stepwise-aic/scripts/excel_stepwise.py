#!/usr/bin/env python3
"""Demostración.xlsx de regresión stepwise con AIC (OD/AM R.pdf p.20-24).

Hojas:
  Pasos   — por cada paso, la tabla de candidatos («<none>», «− x», «+ x») con k y RSS (del oráculo
            exacto) y AIC = n·LN(RSS/n) + 2k en fórmula; el mínimo y la decisión también en fórmula.
  Final   — datos del modelo final en columnas contiguas; LINEST da coeficientes y RSS (contraste
            independiente del oráculo); ln L y AIC = 2k − 2 ln L de p.21 en fórmula.
  Control — Excel contra Python/R.
Uso: .venv/bin/python excel_stepwise.py INCISO_DIR
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
ELEG = PatternFill("solid", fgColor="E2F0D9")


def enc(ws, fila, textos, col=1):
    for j, e in enumerate(textos, col):
        c = ws.cell(fila, j, e)
        c.font, c.fill = NEGRO_N, ENC


def main():
    I = sys.argv[1]
    tr = json.load(open(os.path.join(I, "traza.json"), encoding="utf-8"))
    par = json.load(open(os.path.join(I, "datos", "parametros.json"), encoding="utf-8"))
    datos = list(csv.DictReader(open(os.path.join(I, "datos", par["archivo"]), newline="", encoding="utf-8-sig")))
    pr = list(csv.DictReader(open(os.path.join(I, "pasos_R.csv"), encoding="utf-8")))
    rr = next(csv.DictReader(open(os.path.join(I, "resumen_R.csv"), encoding="utf-8")))
    n = tr["n"]
    wb = Workbook()
    ws = wb.active
    ws.title = "Pasos"
    ws["A1"] = "Stepwise %s con AIC (OD/AM R.pdf p.20-24): AIC = n·ln(RSS/n) + 2k, menor es mejor (p.22)" % tr["direccion"]
    ws["A1"].font = TITULO
    ws["A2"] = "n ="
    ws["B2"] = n
    ws["B2"].font = AZUL
    ws["C2"] = "RSS exacto del oráculo (fracciones); k = coeficientes sin alias. Regla Df = 0: un alias se quita primero (MASS::stepAIC)."
    fila = 4
    aic_celdas = []                       # celda del AIC de cada modelo aceptado
    pasos = tr["pasos"]
    for s, cands in enumerate(tr["candidatos_por_paso"]):
        k0 = n - pasos[s]["gl_resid"]
        ws.cell(fila, 1, "Paso %d: modelo actual con %d coeficientes" % (s + 1, k0)).font = NEGRO_N
        fila += 1
        enc(ws, fila, ("Cambio", "Df", "k", "RSS", "AIC", "¿Mínimo?"))
        fila += 1
        ini = fila
        for c in cands:
            ws.cell(fila, 1, c["cambio"]).font = AZUL
            ws.cell(fila, 2, c["Df"] if c["Df"] is not None else "").font = AZUL
            ws.cell(fila, 3, k0 + (c["Df"] or 0) * (-1 if c["cambio"].startswith("- ") else 1)).font = AZUL
            ws.cell(fila, 4, c["RSS"]).font = AZUL
            ws.cell(fila, 5, "=$B$2*LN(D%d/$B$2)+2*C%d" % (fila, fila))
            fila += 1
        fin = fila - 1
        for r in range(ini, fin + 1):
            ws.cell(r, 6, '=IF(AND(B%d<>0,E%d=MIN(E%d:E%d)),"◀","")' % (r, r, ini, fin))
        siguiente = pasos[s + 1]["cambio"] if s + 1 < len(pasos) else "<none>"
        regla = "Df = 0 (alias): se quita primero" if s + 1 < len(pasos) and any(
            c["cambio"] == siguiente and c["Df"] == 0 for c in cands) else "mínimo AIC"
        ws.cell(fila, 1, "Decisión").font = NEGRO_N
        ws.cell(fila, 2, siguiente if siguiente != "<none>" else "<none>: ningún cambio baja el AIC → fin").font = NEGRO_N
        ws.cell(fila, 4, regla)
        for r in range(ini, fin + 1):
            if ws.cell(r, 1).value == siguiente:
                for j in range(1, 7):
                    ws.cell(r, j).fill = ELEG
        aic_celdas.append("Pasos!E%d" % ini)
        fila += 2
    ws.column_dimensions["A"].width = 26
    ws.column_dimensions["D"].width = 22
    ws.column_dimensions["E"].width = 16

    # ---- Final: LINEST sobre las columnas del modelo final
    wf = wb.create_sheet("Final")
    final_terms = tr["modelo_final"]
    wf["A1"] = "Modelo final: %s ~ %s" % (par["y"], " + ".join(final_terms))
    wf["A1"].font = TITULO
    sys.path.insert(0, "/Users/alexis/theCode/newSkills/TSCI3/kit_tsci3")
    from tsci3 import regresion as rg
    X_fin, nombres, _ = rg.disenar(datos, final_terms)
    final = nombres[1:]
    enc(wf, 3, final + [par["y"]])
    for i, (r, xrow) in enumerate(zip(datos, X_fin), 4):
        for j, v in enumerate(xrow[1:], 1):
            wf.cell(i, j, float(v))
        wf.cell(i, len(final) + 1, float(r[par["y"]]))
    u = 3 + n
    m = len(final)
    xs = "Final!$A$4:$%s$%d" % (L(m), u)
    ys = "Final!$%s$4:$%s$%d" % (L(m + 1), L(m + 1), u)
    c0 = m + 3
    enc(wf, 3, ("Término", "β (LINEST)", "β (R)"), c0)
    for i, t in enumerate(nombres):
        wf.cell(4 + i, c0, t).font = AZUL
        col = m + 1 if i == 0 else m + 1 - i              # LINEST: βm … β1, β0
        wf.cell(4 + i, c0 + 1, "=INDEX(LINEST(%s,%s,TRUE,TRUE),1,%d)" % (ys, xs, col)).font = VERDE
        wf.cell(4 + i, c0 + 2, tr["coeficientes"][t]).font = AZUL
    r0 = 4 + len(nombres) + 1
    filas_f = [("n", "=COUNT(%s)" % ys), ("RSS (LINEST)", "=INDEX(LINEST(%s,%s,TRUE,TRUE),5,2)" % (ys, xs)),
               ("k (coeficientes + σ²)", m + 2),
               ("ln L = −n/2·(ln 2π + ln(RSS/n) + 1)", "=-{n}/2*(LN(2*PI())+LN({rss}/{n})+1)"),
               ("AIC = 2k − 2 ln L (p.21)", "=2*{k}-2*{lnL}"),
               ("extractAIC = n·ln(RSS/n) + 2(k − 1)", "={n}*LN({rss}/{n})+2*({k}-1)"),
               ("Diferencia = n(ln 2π + 1) + 2", "={aic}-{ext}")]
    ref = {}
    for i, (et, fo) in enumerate(filas_f):
        rr_ = r0 + i
        wf.cell(rr_, c0, et).font = NEGRO_N
        clave = ["n", "rss", "k", "lnL", "aic", "ext", "dif"][i]
        if isinstance(fo, str):
            fo = fo.format(**{a: ref.get(a, "") for a in ("n", "rss", "k", "lnL", "aic", "ext")})
        wf.cell(rr_, c0 + 1, fo).font = AZUL if isinstance(fo, int) else NEGRO_N
        ref[clave] = "%s%d" % (L(c0 + 1), rr_)
    cB = L(c0 + 1)

    # ---- Control
    wc = wb.create_sheet("Control")
    enc(wc, 3, ("Concepto", "Excel", "Python/R", "Diferencia", "¿Coincide?"))
    control = [("AIC paso %d (%s)" % (s + 1, pasos[s]["cambio"] or "inicial"), aic_celdas[s], float(pr[s]["AIC"])) for s in range(len(pasos))]
    control += [("β %s" % t, "Final!%s%d" % (cB, 4 + i), tr["coeficientes"][t]) for i, t in enumerate(nombres)]
    control += [("RSS final", "Final!" + ref["rss"], tr["pasos"][-1]["RSS"]), ("ln L", "Final!" + ref["lnL"], float(rr["logLik"])),
                ("AIC p.21 = AIC() de R", "Final!" + ref["aic"], float(rr["AIC_logLik"])),
                ("extractAIC", "Final!" + ref["ext"], float(rr["extractAIC"]))]
    for i, (c_, refc, val) in enumerate(control, 4):
        wc.cell(i, 1, c_)
        wc.cell(i, 2, "=" + refc).font = VERDE
        wc.cell(i, 3, val).font = AZUL
        wc.cell(i, 4, "=B%d-C%d" % (i, i))
        wc.cell(i, 5, '=IF(ABS(D%d)<=1E-6*MAX(1,ABS(C%d)),"sí","NO")' % (i, i)).font = NEGRO_N
    wc.column_dimensions["A"].width = 30
    wb.save(os.path.join(I, "Demostración.xlsx"))
    print("Excel: %d comprobaciones" % len(control))


if __name__ == "__main__":
    main()
