#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RECTA DE MINIMOS CUADRADOS (OD/AM R.pdf p.3-6)
==============================================
  m = (N*sum(xy) - sum(x)*sum(y)) / (N*sum(x^2) - (sum(x))^2);   b = (sum(y) - m*sum(x)) / N   (p.4)
  residuo e = y - y_hat;  RSS = sum(e^2);  MSE = RSS / n   (p.5)
  Ademas, para contrastar con summary(lm) (p.6): errores estandar, t, valor p, R^2 y F.
Las sumas se hacen con fracciones exactas a partir del texto del CSV.

Uso   python3 codigo/resolver.py        (lee datos/parametros.json: archivo, x, y)
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
    """Valor p de dos colas de la t de Student (beta incompleta por fraccion continua)."""
    x = gl / (gl + t * t)
    a, b = gl / 2, 0.5
    lbt = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1 - x)

    def cf(a, b, x):
        c, d = 1.0, 1 - (a + b) * x / (a + 1)
        d = 1 / d
        h = d
        for m in range(1, 500):
            for aa in (m * (b - m) * x / ((a - 1 + 2 * m) * (a + 2 * m)), -(a + m) * (a + b + m) * x / ((a + 2 * m) * (a + 1 + 2 * m))):
                d = 1 / (1 + aa * d)
                c = 1 + aa / c
                h *= d * c
            if abs(d * c - 1) < 3e-16:
                break
        return h
    if x < (a + 1) / (a + b + 2):
        return math.exp(lbt) * cf(a, b, x) / a
    return 1 - math.exp(lbt) * cf(b, a, 1 - x) / b


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--parametros", default=os.path.join(BASE, "datos", "parametros.json"))
    ap.add_argument("--salida", default=BASE)
    a = ap.parse_args()
    par = json.load(open(a.parametros, encoding="utf-8"))
    filas = list(csv.DictReader(open(os.path.join(os.path.dirname(a.parametros), par["archivo"]), newline="", encoding="utf-8-sig")))
    xs = [Fraction(f[par["x"]].strip()) for f in filas]
    ys = [Fraction(f[par["y"]].strip()) for f in filas]
    N = len(xs)
    sx, sy = sum(xs), sum(ys)
    sxy, sx2 = sum(x * y for x, y in zip(xs, ys)), sum(x * x for x in xs)
    m = (N * sxy - sx * sy) / (N * sx2 - sx * sx)
    b = (sy - m * sx) / N
    yhat = [m * x + b for x in xs]
    e = [y - h for y, h in zip(ys, yhat)]
    rss = sum(r * r for r in e)
    mse = rss / N
    ybar, xbar = sy / N, sx / N
    tss = sum((y - ybar) ** 2 for y in ys)
    sxx = sum((x - xbar) ** 2 for x in xs)
    r2 = 1 - rss / tss
    s2 = rss / (N - 2)
    se_m = math.sqrt(float(s2 / sxx))
    se_b = math.sqrt(float(s2 * (Fraction(1, N) + xbar * xbar / sxx)))
    t_m, t_b = float(m) / se_m, float(b) / se_b
    traza = OrderedDict([
        ("problema", par.get("problema", "")), ("archivo", par["archivo"]), ("x", par["x"]), ("y", par["y"]), ("N", N),
        ("sumas", OrderedDict([("x", float(sx)), ("y", float(sy)), ("xy", float(sxy)), ("x2", float(sx2))])),
        ("m", float(m)), ("b", float(b)), ("m_fraccion", "%d/%d" % (m.numerator, m.denominator)),
        ("RSS", float(rss)), ("MSE", float(mse)), ("R2", float(r2)), ("R2_ajustado", float(1 - (1 - r2) * (N - 1) / (N - 2))),
        ("sigma", math.sqrt(float(s2))), ("SE_m", se_m), ("SE_b", se_b), ("t_m", t_m), ("t_b", t_b),
        ("p_m", p_t(t_m, N - 2)), ("p_b", p_t(t_b, N - 2)), ("F", t_m * t_m), ("gl", N - 2),
        ("residuos_primeros", [float(r) for r in e[:10]]),
    ])
    print("MINIMOS CUADRADOS — %s: %s ~ %s, N = %d" % (par["archivo"], par["y"], par["x"], N))
    print("  sum x = %s, sum y = %s, sum xy = %s, sum x^2 = %s" % tuple(float(v) for v in (sx, sy, sxy, sx2)))
    print("  m = (N sum xy - sum x sum y)/(N sum x^2 - (sum x)^2) = %.10f" % float(m))
    print("  b = (sum y - m sum x)/N = %.10f" % float(b))
    print("  y_hat = %.6f + %.6f x" % (float(b), float(m)))
    print("  RSS = %.6f   MSE = RSS/n = %.6f   R^2 = %.6f" % (float(rss), float(mse), float(r2)))
    print("  summary(lm): SE(b0) = %.6f, SE(b1) = %.6f, t(b1) = %.4f, p = %.3g, F = %.3f con 1 y %d gl" % (
        se_b, se_m, t_m, traza["p_m"], t_m * t_m, N - 2))
    json.dump(traza, open(os.path.join(a.salida, "traza.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("traza.json escrita")


if __name__ == "__main__":
    main()
