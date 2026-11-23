#!/usr/bin/env python3
"""Comparación 2 del contrato para Apriori: reglas de Python contra association_rules.csv de arules.

Uso: python3 comparar_r.py INCISO. Compara regla por regla (antecedente como conjunto,
consecuente) soporte, confianza, cobertura, lift y conteo. Solo biblioteca estándar.
"""
import csv
import os
import re
import sys


def leer(ruta):
    out = {}
    for f in csv.DictReader(open(ruta, newline="", encoding="utf-8")):
        m = re.fullmatch(r"\{(.*)\} => \{(.*)\}", f["rules"])
        lhs = frozenset(x for x in re.split(r",(?=[^,=]+=)", m.group(1)) if x)
        out[(lhs, m.group(2))] = tuple(float(f[k]) for k in ("support", "confidence", "coverage", "lift", "count"))
    return out


def main():
    I = sys.argv[1]
    py, r = leer(os.path.join(I, "reglas_python.csv")), leer(os.path.join(I, "association_rules.csv"))
    solo_py, solo_r = set(py) - set(r), set(r) - set(py)
    difs = [k for k in set(py) & set(r) if any(abs(a - b) > 1e-9 for a, b in zip(py[k], r[k]))]
    for k in list(solo_py)[:3]:
        print("❌ solo en Python:", sorted(k[0]), "=>", k[1])
    for k in list(solo_r)[:3]:
        print("❌ solo en R:", sorted(k[0]), "=>", k[1])
    for k in difs[:3]:
        print("❌ métricas distintas:", sorted(k[0]), "=>", k[1], py[k], r[k])
    ok = not solo_py and not solo_r and not difs
    print("%s Apriori: Python %d reglas, R %d; %d iguales en soporte, confianza, cobertura, lift y conteo" % (
        "✅" if ok else "❌", len(py), len(r), len(set(py) & set(r)) - len(difs)))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
