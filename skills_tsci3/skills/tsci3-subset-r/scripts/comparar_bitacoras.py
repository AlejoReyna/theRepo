#!/usr/bin/env python3
"""Compara la bitácora de Python con la de R (y, si se da, con una bitácora esperada).

Uso: python3 comparar_bitacoras.py INCISO [--esperada esperada.csv]
  INCISO/bitacora.csv     (resolver.py)
  INCISO/bitacora_R.csv   (Rscript codigo/script.R)
  esperada.csv            paso,filas,columnas de una fuente (p. ej. la respuesta aceptada)
Compara filas y columnas por paso. Sale con 1 si algo difiere. Solo biblioteca estándar.
"""
import argparse
import csv
import os
import sys


def leer(ruta):
    with open(ruta, newline="", encoding="utf-8") as fh:
        return {f["paso"]: (int(f["filas"]), int(f["columnas"])) for f in csv.DictReader(fh)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inciso")
    ap.add_argument("--esperada")
    a = ap.parse_args()
    py = leer(os.path.join(a.inciso, "bitacora.csv"))
    malos = 0
    otras = []
    r = os.path.join(a.inciso, "bitacora_R.csv")
    if os.path.exists(r):
        otras.append(("R", leer(r)))
    else:
        print("⚠️  falta bitacora_R.csv: ejecuta Rscript codigo/script.R")
    if a.esperada:
        otras.append(("esperada", leer(a.esperada)))
    for nombre, otra in otras:
        comunes = [p for p in py if p in otra]
        difs = [(p, py[p], otra[p]) for p in comunes if py[p] != otra[p]]
        faltan = [p for p in otra if p not in py] if nombre == "R" else []
        for p, x, y in difs:
            print("❌ %s: Python %d×%d, %s %d×%d" % (p, x[0], x[1], nombre, y[0], y[1]))
        for p in faltan:
            print("❌ %s solo está en %s" % (p, nombre))
        ok = not difs and not faltan and comunes
        malos += 0 if ok else 1
        print("%s Python contra %s: %d pasos comparados, %d diferencias" % ("✅" if ok else "❌", nombre, len(comunes), len(difs)))
    return 1 if malos else 0


if __name__ == "__main__":
    sys.exit(main())
