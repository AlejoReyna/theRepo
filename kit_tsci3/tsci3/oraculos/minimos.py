"""Oráculo de mínimos cuadrados: otro camino (forma centrada m = Sxy/Sxx, b = ȳ − m·x̄, en fracciones)."""
import csv
import json
from fractions import Fraction


def verificar(ruta_csv, ruta_traza):
    tr = json.load(open(ruta_traza, encoding="utf-8"))
    f = list(csv.DictReader(open(ruta_csv, newline="", encoding="utf-8-sig")))
    x = [Fraction(r[tr["x"]].strip()) for r in f]
    y = [Fraction(r[tr["y"]].strip()) for r in f]
    n = len(x)
    xb, yb = sum(x) / n, sum(y) / n
    sxy = sum((a - xb) * (b - yb) for a, b in zip(x, y))
    sxx = sum((a - xb) ** 2 for a in x)
    m = sxy / sxx
    b = yb - m * xb
    rss = sum((c - (m * a + b)) ** 2 for a, c in zip(x, y))
    res = [(n == tr["N"], "N = %d" % n),
           ("%d/%d" % (m.numerator, m.denominator) == tr["m_fraccion"], "m exacta = Sxy/Sxx (fracción idéntica)"),
           (abs(float(b) - tr["b"]) < 1e-12 and abs(float(rss) - tr["RSS"]) < 1e-9 * float(rss) and abs(float(rss) / n - tr["MSE"]) < 1e-9,
            "b, RSS y MSE = RSS/n")]
    sx, sy = sum(x), sum(y)
    mut = (n * sum(a * c for a, c in zip(x, y)) - sx * sy) / (n * sx * sx - sx * sx)
    res.append((abs(float(mut) - tr["m"]) > 1e-6, "mutante (Σx)² en lugar de Σx²: m = %.6g (se detecta)" % float(mut)))
    return res
