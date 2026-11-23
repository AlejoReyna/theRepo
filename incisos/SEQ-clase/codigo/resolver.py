#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PATRONES SECUENCIALES COMO cspade (OD/SEQMIN.R)
===============================================
Entrada en formato SPMF (OD/SEQMIN.csv): una secuencia por linea; -1 cierra un evento y
-2 cierra la secuencia (parse_spmf de SEQMIN.R).
Patron = secuencia de elementos (conjuntos de items) <E1, E2, ..., Ek>. Una secuencia lo
contiene si hay eventos i1 < i2 < ... < ik con Ej contenido en el evento ij.
Soporte = secuencias que contienen el patron / secuencias (misma definicion por caso que
OD/EPISODES.R). Parametros del curso: support = 0.01, maxsize = 3 (items por elemento),
maxlen = 4 (elementos por patron) (cspade en SEQMIN.R).

Uso   python3 codigo/resolver.py        (lee datos/parametros.json)
Solo biblioteca estandar.
"""
import argparse
import csv
import json
import os
from collections import OrderedDict
from itertools import combinations

AQUI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(AQUI)


def leer_spmf(ruta):
    secuencias = []
    for linea in open(ruta, encoding="utf-8-sig"):
        tokens = [int(t) for t in linea.split()]
        if not tokens:
            continue
        seq, evento = [], []
        for t in tokens:
            if t in (-1, -2):
                if evento:
                    seq.append(frozenset(evento))
                    evento = []
                if t == -2:
                    break
            else:
                evento.append(t)
        secuencias.append(seq)
    return secuencias


def subconjuntos(evento, maxsize):
    items = sorted(evento)
    for k in range(1, min(maxsize, len(items)) + 1):
        for c in combinations(items, k):
            yield frozenset(c)


def patrones_de(seq, maxsize, maxlen):
    """Todos los patrones distintos contenidos en una secuencia."""
    vistos = set()
    def extender(prefijo, desde):
        if prefijo:
            vistos.add(tuple(prefijo))
        if len(prefijo) == maxlen:
            return
        for i in range(desde, len(seq)):
            for s in subconjuntos(seq[i], maxsize):
                extender(prefijo + [s], i + 1)
    extender([], 0)
    return vistos


def texto(p):
    return "<%s>" % ",".join("{%s}" % ",".join(str(x) for x in sorted(e)) for e in p)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--parametros", default=os.path.join(BASE, "datos", "parametros.json"))
    ap.add_argument("--salida", default=BASE)
    a = ap.parse_args()
    par = json.load(open(a.parametros, encoding="utf-8"))
    seqs = leer_spmf(os.path.join(os.path.dirname(a.parametros), par["archivo"]))
    sup, maxsize, maxlen = par.get("soporte", 0.01), par.get("maxsize", 3), par.get("maxlen", 4)
    n = len(seqs)
    cuenta = {}
    for s in seqs:
        for p in patrones_de(s, maxsize, maxlen):
            cuenta[p] = cuenta.get(p, 0) + 1
    frec = {p: c for p, c in cuenta.items() if c / n >= sup}
    orden = sorted(frec.items(), key=lambda kv: (-kv[1], len(kv[0]), texto(kv[0])))
    por_long = OrderedDict()
    for p, c in orden:
        k = sum(len(e) for e in p)
        por_long[k] = por_long.get(k, 0) + 1
    print("PATRONES SECUENCIALES — %s: %d secuencias; support >= %g, maxsize %d, maxlen %d" % (par["archivo"], n, sup, maxsize, maxlen))
    print("Patrones frecuentes: %d; por numero de items: %s" % (len(frec), dict(sorted(por_long.items()))))
    for p, c in orden[:15]:
        print("  %-30s %3d secuencias  soporte %.2f" % (texto(p), c, c / n))
    ejemplo = sorted(patrones_de(seqs[0], maxsize, maxlen), key=lambda p: (len(p), texto(p)))
    print("Secuencia 1 = %s contiene %d patrones (descomposicion a mano en el Excel)" % (texto(seqs[0]), len(ejemplo)))
    traza = OrderedDict([("problema", par.get("problema", "")), ("archivo", par["archivo"]), ("n", n),
                         ("soporte_min", sup), ("maxsize", maxsize), ("maxlen", maxlen),
                         ("secuencias", [[sorted(e) for e in s] for s in seqs]),
                         ("n_patrones", len(frec)), ("por_numero_de_items", por_long),
                         ("patrones", [OrderedDict([("patron", [sorted(e) for e in p]), ("texto", texto(p)), ("secuencias", c), ("soporte", c / n)])
                                       for p, c in orden]),
                         ("ejemplo_secuencia_1", [texto(p) for p in ejemplo])])
    json.dump(traza, open(os.path.join(a.salida, "traza.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with open(os.path.join(a.salida, "patrones_python.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["sequence", "support"])
        for p, c in orden:
            w.writerow([texto(p), c / n])
    print("traza.json y patrones_python.csv escritas")


if __name__ == "__main__":
    main()
