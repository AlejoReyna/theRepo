#!/usr/bin/env python3
"""Comparación 2 del contrato para k-means: iteraciones de clase de Python contra las de R.

Uso: python3 comparar_r.py INCISO     (lee traza.json y kmeans_clase_R.csv)
Sale con 1 si difieren conteos, empates, cambios, ΣDMIN o centroides. Solo biblioteca estándar.
"""
import csv
import json
import os
import sys


def main():
    I = sys.argv[1]
    tr = json.load(open(os.path.join(I, "traza.json"), encoding="utf-8"))
    with open(os.path.join(I, "kmeans_clase_R.csv"), newline="", encoding="utf-8") as fh:
        rr = list(csv.DictReader(fh))
    malos = []
    if len(rr) != len(tr["iteraciones"]):
        malos.append("iteraciones: Python %d, R %d" % (len(tr["iteraciones"]), len(rr)))
    nv = len(tr["columnas"])
    for t, r in zip(tr["iteraciones"], rr):
        k = t["iteracion"]
        cam = None if r["cambios"] in ("NA", "") else int(r["cambios"])
        if (t["n0"], t["n1"], t["empates"], t["cambios"]) != (int(r["n0"]), int(r["n1"]), int(r["empates"]), cam):
            malos.append("it %d conteos" % k)
        if abs(t["suma_dmin"] - float(r["suma_dmin"])) > 1e-6 * max(1, t["suma_dmin"]):
            malos.append("it %d ΣDMIN %.9f vs %s" % (k, t["suma_dmin"], r["suma_dmin"]))
        for j in range(nv):
            if abs(t["C0"][j] - float(r["C0_%d" % (j + 1)])) > 1e-9 or abs(t["C1"][j] - float(r["C1_%d" % (j + 1)])) > 1e-9:
                malos.append("it %d centroides" % k)
                break
    for m in malos[:10]:
        print("❌", m)
    print("%s k-means de clase: Python contra R en %d iteraciones, %d diferencias" % (
        "✅" if not malos else "❌", min(len(rr), len(tr["iteraciones"])), len(malos)))
    return 1 if malos else 0


if __name__ == "__main__":
    sys.exit(main())
