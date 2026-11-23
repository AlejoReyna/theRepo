#!/usr/bin/env python3
"""Comparación 2 del contrato para episodios: los tres CSV de Python contra los de EPISODES.R.

Uso: python3 comparar_r.py INCISO. Compara fila por fila y en el mismo orden (el cálculo es
determinista): detalle de pares, soporte global y soporte por distrito.
"""
import csv
import os
import sys


def leer(ruta):
    return [tuple(f) for f in csv.reader(open(ruta, newline="", encoding="utf-8"))]


def norm(fila):
    out = []
    for x in fila:
        try:
            v = float(x)
            out.append(round(v, 12))
        except ValueError:
            out.append(x)
    return tuple(out)


def main():
    I = sys.argv[1]
    malos = 0
    for nombre in ("episodios_detalle", "episodios_globales", "episodios_por_distrito"):
        py = [norm(f) for f in leer(os.path.join(I, nombre + "_python.csv"))[1:]]
        r = [norm(f) for f in leer(os.path.join(I, nombre + ".csv"))[1:]]
        if nombre == "episodios_detalle":                         # R agrega district al agrupar por caso
            r = [f[:8] for f in r]
        igual = py == r
        malos += 0 if igual else 1
        if not igual:
            dif = next((i for i, (a, b) in enumerate(zip(py, r)) if a != b), min(len(py), len(r)))
            print("   primera diferencia en la fila %d: Python %s | R %s" % (dif + 2, py[dif] if dif < len(py) else None, r[dif] if dif < len(r) else None))
        print("%s %s: Python %d filas, R %d, %s" % ("✅" if igual else "❌", nombre, len(py), len(r), "iguales y en el mismo orden" if igual else "distintas"))
    return 1 if malos else 0


if __name__ == "__main__":
    sys.exit(main())
