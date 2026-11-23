#!/usr/bin/env python3
"""Verificación de Breusch-Pagan (estado VL: las láminas no dan la fórmula del estadístico).

Comprueba con los resultados de R: grados de libertad = número de predictores (p.8), valor p =
P(χ² con esos gl > BP) y decisión = «p < α». Como contraste adicional, fuera de las fuentes, recalcula
el estadístico studentizado de Koenker (el que usa bptest por omisión): BP = n·R² de la regresión de
e² sobre los mismos predictores.
Uso: python3 verificar_bp.py INCISO
"""
import csv
import json
import os
import sys

sys.path.insert(0, "/Users/alexis/theCode/newSkills/TSCI3/kit_tsci3")
from tsci3 import estadistica as st, regresion as rg  # noqa: E402

I = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
modelos = {"old: waiting ~ eruptions": ("old.csv", "waiting", ["eruptions"]),
           "BR: precio ~ m2_construcción + recamaras + condición": ("BR.csv", "precio", ["m2_construcción", "recamaras", "condición"])}
par_path = os.path.join(I, "datos", "parametros.json")
if os.path.exists(par_path):
    par = json.load(open(par_path, encoding="utf-8"))
    for m in par.get("modelos", [par] if "archivo" in par else []):
        modelos[m.get("nombre", "%s: %s ~ %s" % (m["archivo"], m["y"], " + ".join(m["predictores"])))] = (m["archivo"], m["y"], m["predictores"])


def _resolver_modelo(nombre):
    if nombre in modelos:
        return modelos[nombre]
    _, formula = nombre.split(":", 1) if ":" in nombre else ("", nombre)
    y_s, preds_s = formula.split("~", 1)
    y_col = y_s.strip()
    preds_col = [p.strip() for p in preds_s.split("+")]
    csvs = [f for f in sorted(os.listdir(os.path.join(I, "datos"))) if f.endswith(".csv")]
    return csvs[0], y_col, preds_col


ok_total, traza = True, {}
for f in csv.DictReader(open(os.path.join(I, "bp_R.csv"), encoding="utf-8")):
    archivo, y, preds = _resolver_modelo(f["modelo"])
    filas = rg.leer(os.path.join(I, "datos", archivo))
    X, _, _ = rg.disenar(filas, preds)
    yy = [rg._num(r[y]) for r in filas]
    _, yh, _ = rg.mco(X, yy)
    e2 = [(a - b) ** 2 for a, b in zip(yy, yh)]
    _, h2, rss2 = rg.mco(X, e2)
    m = sum(e2) / len(e2)
    tss2 = sum((v - m) ** 2 for v in e2)
    bp = float(len(e2) * (1 - rss2 / tss2))
    gl, p, bpr = int(f["gl"]), float(f["p"]), float(f["BP"])
    checks = [(gl == len(preds) == int(f["predictores"]), "gl = número de predictores = %d" % gl),
              (abs(st.p_chi2(bpr, gl) - p) <= 1e-9 * max(p, 1e-300) or abs(st.p_chi2(bpr, gl) - p) < 1e-15, "p = P(χ²(%d) > %.6g) = %.6g" % (gl, bpr, p)),
              ((p < 0.05) == f["decision"].startswith("se rechaza"), "decisión «%s» coherente con p < 0.05" % f["decision"]),
              (abs(bp - bpr) <= 1e-8 * max(1, bpr), "contraste fuera de las fuentes: BP de Koenker = n·R²(e² ~ X) = %.10g" % bp)]
    print("Modelo %s" % f["modelo"])
    for ok, msg in checks:
        ok_total &= ok
        print("  %s %s" % ("✅" if ok else "❌", msg))
    traza[f["modelo"]] = {"BP": bpr, "gl": gl, "p": p, "decision": f["decision"], "BP_python": bp}
json.dump(traza, open(os.path.join(I, "traza.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
sys.exit(0 if ok_total else 1)
