"""Mínimos cuadrados ordinarios exactos (fracciones) para verificar salidas de lm en R.

β = (XᵀX)⁻¹Xᵀy resolviendo las ecuaciones normales por Gauss-Jordan con Fraction.
`disenar` arma la matriz de diseño como R: intercepto, columnas numéricas y, para factores,
una ficticia por nivel salvo el primero (niveles ordenados como en R: numérico si todos lo son).
"""
import csv
from fractions import Fraction


def leer(ruta):
    return list(csv.DictReader(open(ruta, newline="", encoding="utf-8-sig")))


def _num(v):
    return Fraction(v.strip())


def _niveles(vals):
    try:
        return sorted(set(vals), key=lambda v: float(v))
    except ValueError:
        return sorted(set(vals))


def _es_num(vals):
    try:
        for v in vals:
            Fraction(str(v).strip())
        return True
    except (ValueError, ZeroDivisionError):
        return False


def disenar(filas, predictores, factores=(), niveles=None):
    nombres = ["(Intercept)"]
    columnas = []
    niveles = dict(niveles or {})
    fact_set = set(factores)
    for p in predictores:
        vals = [f[p] for f in filas]
        if p in fact_set or not _es_num(vals):
            lv = niveles.setdefault(p, _niveles(vals))
            for nv in lv[1:]:
                nombres.append("%s%s" % (p, nv))
                columnas.append([Fraction(1) if str(f[p]) == str(nv) else Fraction(0) for f in filas])
        else:
            nombres.append(p)
            columnas.append([_num(str(f[p])) for f in filas])
    X = [[Fraction(1)] + [c[i] for c in columnas] for i in range(len(filas))]
    return X, nombres, niveles


def resolver(A, b):
    n = len(A)
    M = [list(A[i]) + [b[i]] for i in range(n)]
    for c in range(n):
        piv = next(r for r in range(c, n) if M[r][c] != 0)
        M[c], M[piv] = M[piv], M[c]
        p = M[c][c]
        M[c] = [v / p for v in M[c]]
        for r in range(n):
            if r != c and M[r][c] != 0:
                f = M[r][c]
                M[r] = [a - f * bb for a, bb in zip(M[r], M[c])]
    return [M[i][n] for i in range(n)]


def _rango_completo(A):
    M = [list(r) for r in A]
    n = len(M)
    for c in range(n):
        piv = next((r for r in range(c, n) if M[r][c] != 0), None)
        if piv is None:
            return False
        M[c], M[piv] = M[piv], M[c]
        for r in range(c + 1, n):
            if M[r][c] != 0:
                f = M[r][c] / M[c][c]
                M[r] = [a - f * bb for a, bb in zip(M[r], M[c])]
    return True


def mco(X, y):
    """Como lm: una columna que no aumenta el rango queda como alias (coeficiente None = NA)."""
    k = len(X[0])
    XtX = [[sum(row[i] * row[j] for row in X) for j in range(k)] for i in range(k)]
    Xty = [sum(row[i] * yy for row, yy in zip(X, y)) for i in range(k)]
    usadas = []
    for j in range(k):
        prueba = usadas + [j]
        if _rango_completo([[XtX[a][b] for b in prueba] for a in prueba]):
            usadas = prueba
    sub = resolver([[XtX[a][b] for b in usadas] for a in usadas], [Xty[a] for a in usadas])
    beta = [None] * k
    for j, v in zip(usadas, sub):
        beta[j] = v
    yhat = [sum(b * x for b, x in zip(beta, row) if b is not None) for row in X]
    rss = sum((a - h) ** 2 for a, h in zip(y, yhat))
    return beta, yhat, rss


def aic_lm(n, rss, k):
    """extractAIC de R para lm: n·ln(RSS/n) + 2k."""
    import math
    return n * math.log(float(rss) / n) + 2 * k
