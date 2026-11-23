#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
REGRESION LINEAL SIMPLE CON UN PREDICTOR BINARIO (OD/AM R.pdf p.10-12)
=====================================================================
  Y_i = b0 + b1*X_i + e_i con X_i ficticia (0/1) (p.10). Con las formulas de p.4 sobre x en {0, 1}:
  b0 = media de Y en el grupo 0;  b1 = media del grupo 1 - media del grupo 0.
  t de la pendiente = t de Student con varianzas iguales (t.test(var.equal = TRUE), p.11).
  Con factor(automatic) (p.12) la referencia cambia y el signo de b1 se invierte.

Uso   python3 codigo/resolver.py        (parametros.json: archivo, x (0/1), y)
Solo biblioteca estandar.
"""
import argparse
import csv
import json
import math
import os
from collections import OrderedDict
from fractions import Fraction

AQUI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(AQUI)


def p_t(t, gl):
    x = gl / (gl + t * t)
    a, b = gl / 2, 0.5
    lbt = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1 - x)

    def cf(a, b, x):
        c, d = 1.0, 1 / (1 - (a + b) * x / (a + 1))
        h = d
        for m in range(1, 500):
            for aa in (m * (b - m) * x / ((a - 1 + 2 * m) * (a + 2 * m)), -(a + m) * (a + b + m) * x / ((a + 2 * m) * (a + 1 + 2 * m))):
                d = 1 / (1 + aa * d)
                c = 1 + aa / c
                h *= d * c
            if abs(d * c - 1) < 3e-16:
                break
        return h
    return math.exp(lbt) * cf(a, b, x) / a if x < (a + 1) / (a + b + 2) else 1 - math.exp(lbt) * cf(b, a, 1 - x) / b


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--parametros", default=os.path.join(BASE, "datos", "parametros.json"))
    ap.add_argument("--salida", default=BASE)
    a = ap.parse_args()
    par = json.load(open(a.parametros, encoding="utf-8"))
    f = list(csv.DictReader(open(os.path.join(os.path.dirname(a.parametros), par["archivo"]), newline="", encoding="utf-8-sig")))
    x = [Fraction(r[par["x"]]) for r in f]
    y = [Fraction(r[par["y"]]) for r in f]
    if set(x) - {0, 1}:
        raise SystemExit("El predictor %s no es 0/1: codificalo antes (p.10)." % par["x"])
    N = len(x)
    sx, sy, sxy, sx2 = sum(x), sum(y), sum(a * b for a, b in zip(x, y)), sum(a * a for a in x)
    m = (N * sxy - sx * sy) / (N * sx2 - sx * sx)
    b = (sy - m * sx) / N
    g0 = [v for u, v in zip(x, y) if u == 0]
    g1 = [v for u, v in zip(x, y) if u == 1]
    m0, m1 = sum(g0) / len(g0), sum(g1) / len(g1)
    ss = sum((v - m0) ** 2 for v in g0) + sum((v - m1) ** 2 for v in g1)
    sp2 = ss / (N - 2)
    se = math.sqrt(float(sp2 * (Fraction(1, len(g0)) + Fraction(1, len(g1)))))
    t = float(m1 - m0) / se
    rss = sum((v - (m * u + b)) ** 2 for u, v in zip(x, y))
    tss = sum((v - sy / N) ** 2 for v in y)
    traza = OrderedDict([("problema", par.get("problema", "")), ("archivo", par["archivo"]), ("x", par["x"]), ("y", par["y"]), ("N", N),
                         ("n0", len(g0)), ("n1", len(g1)), ("media0", float(m0)), ("media1", float(m1)),
                         ("b0", float(b)), ("b1", float(m)), ("b0_es_media0", b == m0), ("b1_es_diferencia", m == m1 - m0),
                         ("SE_b1", se), ("t", t), ("gl", N - 2), ("p", p_t(t, N - 2)), ("R2", float(1 - rss / tss)),
                         ("b0_factor", float(m1)), ("b1_factor", float(m0 - m1))])
    print("PREDICTOR BINARIO — %s ~ %s (%s), N = %d" % (par["y"], par["x"], par["archivo"], N))
    print("  grupo 0: n = %d, media = %.6f; grupo 1: n = %d, media = %.6f" % (len(g0), float(m0), len(g1), float(m1)))
    print("  formulas de p.4: b0 = %.6f (= media del grupo 0: %s), b1 = %.6f (= diferencia de medias: %s)" % (
        float(b), b == m0, float(m), m == m1 - m0))
    print("  t = %.4f con %d gl, p = %.6g  (lm y t.test(var.equal = TRUE) dan la misma t)" % (t, N - 2, traza["p"]))
    print("  con factor(automatic): intercepto = %.6f, coeficiente = %.6f (cambia el signo)" % (float(m1), float(m0 - m1)))
    json.dump(traza, open(os.path.join(a.salida, "traza.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
