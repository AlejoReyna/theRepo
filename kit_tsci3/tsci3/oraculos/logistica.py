"""Oráculo de regresión logística binaria y multinomial (OD/AM R.pdf p.37-41), independiente de R.

Binaria: máxima verosimilitud por Newton-Raphson (= IRLS de glm) hasta |Δβ| relativo < 1e−14;
p = 1/(1 + e^(−η)) (sigmoide, p.37). Var(β) = (XᵀWX)⁻¹ con W = p(1 − p).
VIF (p.39) como car::vif con términos de un grado de libertad: R = correlación de Var(β) sin el
intercepto; VIF_j = R_jj · (R⁻¹)_jj.
Anova (car, tipo II, razón de verosimilitudes): LR_j = D(modelo sin x_j) − D(modelo completo), χ²(1).
Multinomial (p.41, nnet::multinom): categoría base = primer nivel; Newton sobre los (K−1)(p+1)
parámetros con la matriz de información completa, hasta el máximo de la log-verosimilitud.
cut(right = FALSE) y quantile tipo 7 (el de R por omisión).
"""
import math


def resolver(A, b):
    n = len(A)
    M = [list(A[i]) + [b[i]] for i in range(n)]
    for c in range(n):
        piv = max(range(c, n), key=lambda r: abs(M[r][c]))
        M[c], M[piv] = M[piv], M[c]
        for r in range(n):
            if r != c and M[r][c] != 0:
                f = M[r][c] / M[c][c]
                M[r] = [a - f * bb for a, bb in zip(M[r], M[c])]
    return [M[i][n] / M[i][i] for i in range(n)]


def inversa(A):
    n = len(A)
    cols = [resolver(A, [1.0 if i == j else 0.0 for i in range(n)]) for j in range(n)]
    return [[cols[j][i] for j in range(n)] for i in range(n)]


def sigmoide(eta):
    return 1 / (1 + math.exp(-eta)) if eta >= 0 else math.exp(eta) / (1 + math.exp(eta))


def binaria(X, y, tol=1e-14, max_iter=100):
    """X con columna de unos. Devuelve β, Var(β), devianza, iteraciones."""
    k = len(X[0])
    b = [0.0] * k
    for it in range(1, max_iter + 1):
        p = [sigmoide(sum(bj * xj for bj, xj in zip(b, x))) for x in X]
        g = [sum((yy - pp) * x[j] for x, yy, pp in zip(X, y, p)) for j in range(k)]
        H = [[sum(pp * (1 - pp) * x[i] * x[j] for x, pp in zip(X, p)) for j in range(k)] for i in range(k)]
        d = resolver(H, g)
        b = [bj + dj for bj, dj in zip(b, d)]
        if max(abs(dj) / max(1.0, abs(bj)) for dj, bj in zip(d, b)) < tol:
            break
    p = [sigmoide(sum(bj * xj for bj, xj in zip(b, x))) for x in X]
    H = [[sum(pp * (1 - pp) * x[i] * x[j] for x, pp in zip(X, p)) for j in range(k)] for i in range(k)]
    dev = -2 * sum(yy * math.log(pp) + (1 - yy) * math.log(1 - pp) for yy, pp in zip(y, p))
    return b, inversa(H), dev, it


def vif(V):
    """V = Var(β) con intercepto en la posición 0."""
    S = [row[1:] for row in V[1:]]
    m = len(S)
    R = [[S[i][j] / math.sqrt(S[i][i] * S[j][j]) for j in range(m)] for i in range(m)]
    Ri = inversa(R)
    return [R[j][j] * Ri[j][j] for j in range(m)]


def multinomial(X, y, clases, tol=1e-13, max_iter=200):
    """y = índices de clase (0 = base). Devuelve B [(K−1) × k], log-verosimilitud, iteraciones."""
    K, k = len(clases), len(X[0])
    q = (K - 1) * k
    B = [0.0] * q

    def probs(x):
        etas = [0.0] + [sum(B[c * k + j] * x[j] for j in range(k)) for c in range(K - 1)]
        mx = max(etas)
        e = [math.exp(v - mx) for v in etas]
        s = sum(e)
        return [v / s for v in e]

    for it in range(1, max_iter + 1):
        g = [0.0] * q
        H = [[0.0] * q for _ in range(q)]
        for x, yy in zip(X, y):
            pr = probs(x)
            for c in range(K - 1):
                r = (1.0 if yy == c + 1 else 0.0) - pr[c + 1]
                for j in range(k):
                    g[c * k + j] += r * x[j]
                for d in range(K - 1):
                    w = pr[c + 1] * ((1.0 if c == d else 0.0) - pr[d + 1])
                    for i in range(k):
                        for j in range(k):
                            H[c * k + i][d * k + j] += w * x[i] * x[j]
        dB = resolver(H, g)
        B = [a + b for a, b in zip(B, dB)]
        if max(abs(a) / max(1.0, abs(b)) for a, b in zip(dB, B)) < tol:
            break
    ll = sum(math.log(probs(x)[yy]) for x, yy in zip(X, y))
    return [B[c * k:(c + 1) * k] for c in range(K - 1)], ll, it, probs


def cuantil7(v, p):
    s = sorted(v)
    h = (len(s) - 1) * p
    lo = math.floor(h)
    return s[lo] + (h - lo) * (s[min(lo + 1, len(s) - 1)] - s[lo])


def cortar(v, cortes, etiquetas):
    """cut(breaks = c(-Inf, c1, c2, Inf), right = FALSE): intervalos [a, b)."""
    out = []
    for x in v:
        i = sum(1 for c in cortes if x >= c)
        out.append(etiquetas[i])
    return out
