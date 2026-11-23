"""Normalización, distancias y entropía.

- Min-max del Excel de clase: y = m·x + b, m = 1/(máx − mín), b = −m·mín
  (`OD/mochila_.xlsx` B4:D5).
- z como `scale()` de R: (x − media)/sd con sd de n − 1 (`OD/TSCI3 P6.R`).
"""
import math
from fractions import Fraction


def minmax_parametros(valores):
    lo, hi = min(valores), max(valores)
    if hi == lo:
        raise ValueError("columna constante: máx = mín, m no está definida")
    m = 1 / (hi - lo)
    return m, -m * lo


def minmax(valores):
    m, b = minmax_parametros(valores)
    return [m * x + b for x in valores], m, b


def zscore(valores):
    n = len(valores)
    if n < 2:
        raise ValueError("scale() necesita al menos 2 valores")
    media = sum(valores) / n
    sd = math.sqrt(sum((x - media) ** 2 for x in valores) / (n - 1))
    if sd == 0:
        raise ValueError("columna constante: sd = 0")
    return [(x - media) / sd for x in valores], media, sd


def euclidiana(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def entropia(conteos):
    """H = −Σ p·log2 p sobre conteos enteros (los ceros no aportan)."""
    n = sum(conteos)
    if n == 0:
        return 0.0
    return -sum((c / n) * math.log2(c / n) for c in conteos if c)


def fraccion(x):
    """Fraction exacta desde int, str o float (vía su representación decimal)."""
    if isinstance(x, Fraction):
        return x
    if isinstance(x, float):
        return Fraction(repr(x))
    return Fraction(x)
