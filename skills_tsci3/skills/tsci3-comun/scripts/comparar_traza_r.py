#!/usr/bin/env python3
"""Comparación 2 del contrato para AF4: cifras de traza.json contra un CSV de una fila que escribe R.

Uso: python3 comparar_traza_r.py INCISO ARCHIVO_R.csv [--tol 1e-9] [--claves a,b,c]
Compara cada columna del CSV de R con la clave del mismo nombre en la traza (tolerancia
relativa). Sale con 1 si algo difiere. Solo biblioteca estándar.
"""
import argparse
import csv
import json
import os
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inciso")
    ap.add_argument("csv_r")
    ap.add_argument("--tol", type=float, default=1e-9)
    ap.add_argument("--claves")
    a = ap.parse_args()
    tr = json.load(open(os.path.join(a.inciso, "traza.json"), encoding="utf-8"))
    fila = next(csv.DictReader(open(os.path.join(a.inciso, a.csv_r), encoding="utf-8")))
    claves = a.claves.split(",") if a.claves else [k for k in fila if k in tr]
    malos = 0
    for k in claves:
        r, p = float(fila[k]), float(tr[k])
        ok = abs(r - p) <= a.tol * max(1.0, abs(r))
        malos += 0 if ok else 1
        print("%s %-14s Python %-22.12g R %-22.12g" % ("✅" if ok else "❌", k, p, r))
    print("%s %d cifras comparadas, %d diferencias (tolerancia relativa %g)" % ("✅" if not malos else "❌", len(claves), malos, a.tol))
    return 1 if malos else 0


if __name__ == "__main__":
    sys.exit(main())
