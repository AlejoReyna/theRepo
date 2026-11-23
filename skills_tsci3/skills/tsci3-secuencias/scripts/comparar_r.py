#!/usr/bin/env python3
"""Comparación 2 del contrato para patrones secuenciales: patrones_python.csv contra patrones_R.csv (cspade).

Uso: python3 comparar_r.py INCISO. Compara cada patrón (lista de conjuntos) y su soporte.
"""
import csv
import os
import re
import sys


def leer(ruta):
    out = {}
    for f in csv.DictReader(open(ruta, newline="", encoding="utf-8")):
        elems = re.findall(r"\{([^}]*)\}", f["sequence"])
        out[tuple(frozenset(x.strip() for x in e.split(",")) for e in elems)] = float(f["support"])
    return out


def main():
    I = sys.argv[1]
    py, r = leer(os.path.join(I, "patrones_python.csv")), leer(os.path.join(I, "patrones_R.csv"))
    difs = [k for k in set(py) & set(r) if abs(py[k] - r[k]) > 1e-9]
    solo_py, solo_r = set(py) - set(r), set(r) - set(py)
    for k in list(solo_py)[:3]:
        print("❌ solo en Python:", [sorted(e) for e in k])
    for k in list(solo_r)[:3]:
        print("❌ solo en R:", [sorted(e) for e in k])
    ok = not difs and not solo_py and not solo_r
    print("%s Secuencias: Python %d patrones, R %d; %d con el mismo soporte" % (
        "✅" if ok else "❌", len(py), len(r), len(set(py) & set(r)) - len(difs)))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
