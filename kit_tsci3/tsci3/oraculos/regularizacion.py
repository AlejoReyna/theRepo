"""Oráculo de Lasso y Ridge (OD/AM R.pdf p.29-32), independiente de glmnet.

Problema que resuelve glmnet (familia gaussiana, standardize = TRUE, con intercepto), escrito en
la escala original de y y con x estandarizada (media 0, varianza con 1/n):

    F(β0, β) = 1/(2n)·Σ(y − β0 − Xβ)² + λ·[ α·‖β‖₁ + (1 − α)/(2·s_y)·‖β‖² ]

s_y = desviación estándar de y con 1/n: glmnet estandariza y por dentro y reporta λ en la escala
de y; la parte L1 no cambia con esa escala y la L2 sí. Se minimiza por descenso por coordenadas
hasta que ningún coeficiente cambie más de 1e−13 (en la escala estandarizada).

Con alpha = 1 es Lasso (p.30): el umbral suave lleva coeficientes exactamente a cero (p.29).
Con alpha = 0 es Ridge (p.31): solo encoge. Si dos columnas son colineales, en Lasso los
coeficientes no son únicos pero F y los valores ajustados sí; por eso se comparan F y ŷ.
"""
import math


def preparar(X, y):
    n, p = len(X), len(X[0])
    m = [sum(r[j] for r in X) / n for j in range(p)]
    s = [math.sqrt(sum((r[j] - m[j]) ** 2 for r in X) / n) for j in range(p)]
    Z = [[(r[j] - m[j]) / s[j] if s[j] > 0 else 0.0 for j in range(p)] for r in X]
    ym = sum(y) / n
    sy = math.sqrt(sum((v - ym) ** 2 for v in y) / n)
    return {"n": n, "p": p, "m": m, "s": s, "Z": Z, "y": y, "ym": ym, "sy": sy}


def objetivo(P, b0, b, lam, alpha):
    """F con β en la escala original de x (como devuelve coef de glmnet)."""
    n = P["n"]
    rss = 0.0
    bs = [bj * sj for bj, sj in zip(b, P["s"])]
    # ŷ = β0 + Σ βj xj = (β0 + Σ βj mj) + Σ bs_j z_j
    c = b0 + sum(bj * mj for bj, mj in zip(b, P["m"]))
    for zr, yy in zip(P["Z"], P["y"]):
        e = yy - c - sum(a * z for a, z in zip(bs, zr))
        rss += e * e
    return rss / (2 * n) + lam * (alpha * sum(abs(v) for v in bs) + (1 - alpha) / (2 * P["sy"]) * sum(v * v for v in bs))


def ajustar(P, lam, alpha, tol=1e-13, max_iter=200000):
    n, p, Z, sy = P["n"], P["p"], P["Z"], P["sy"]
    cols = [[r[j] for r in Z] for j in range(p)]
    bs = [0.0] * p
    r = [v - P["ym"] for v in P["y"]]                 # residuo con intercepto = media de y
    den = 1 + lam * (1 - alpha) / sy
    for it in range(max_iter):
        dmax = 0.0
        for j in range(p):
            cj = cols[j]
            z = sum(a * b for a, b in zip(cj, r)) / n + bs[j]
            nuevo = math.copysign(max(abs(z) - lam * alpha, 0.0), z) / den
            d = nuevo - bs[j]
            if d:
                r = [ri - d * a for ri, a in zip(r, cj)]
                bs[j] = nuevo
                dmax = max(dmax, abs(d) / sy)
        if dmax < tol:
            break
    b = [v / s if s > 0 else 0.0 for v, s in zip(bs, P["s"])]
    b0 = P["ym"] - sum(bj * mj for bj, mj in zip(b, P["m"]))
    return b0, b, it + 1


def predecir(X, b0, b):
    return [b0 + sum(bj * xj for bj, xj in zip(b, x)) for x in X]
