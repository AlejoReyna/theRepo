"""Oráculo de KNN (OD/AM R.pdf p.43-48, p.51-53), independiente de R.

Distancia euclidiana sin normalizar (p.48; T5). Regla de class::knn y caret::knn3 (use.all = TRUE):
entran al voto todos los puntos con distancia² ≤ d_k²·(1 + 1e−4), donde d_k es la k-ésima menor.
Medido el 13/11/2026 (class 7.3, caret 7.0.1): con k = 2 un punto a distancia² 1.00006 frente a 1
entra al voto y uno a 1.0004 no; en BR, pliegue Fold07, k = 3, la fila 494 empata 64.01581 con
64.01630 y knn3 da prob 0.5/0.5. Con k = 1, class::knn usa otra rutina y solo empata distancias
exactas; en este caso no cambia ninguna predicción.
gana la clase con más votos; si dos clases empatan en votos, R elige al azar (T15) y el oráculo
lo marca como empate.
"""
import math


def distancias(x, train):
    return [math.sqrt(sum((a - b) ** 2 for a, b in zip(x, t))) for t in train]


def vecinos(x, train, k):
    d = distancias(x, train)
    orden = sorted(range(len(train)), key=lambda i: d[i])
    dk2 = d[orden[k - 1]] ** 2
    return [i for i in orden if d[i] ** 2 <= dk2 * (1 + 1e-4)], d


def votar(x, train, cl, k):
    """Devuelve (clase ganadora o None si hay empate de votos, votos {clase: n}, índices de vecinos)."""
    idx, d = vecinos(x, train, k)
    votos = {}
    for i in idx:
        votos[cl[i]] = votos.get(cl[i], 0) + 1
    m = max(votos.values())
    ganadoras = sorted(c for c, v in votos.items() if v == m)
    return (ganadoras[0] if len(ganadoras) == 1 else None), votos, idx, ganadoras


def wcss(X, grupos):
    """Σ‖x − μ_g‖² con μ_g la media de cada grupo (p.46)."""
    tot = 0.0
    for g in set(grupos):
        miembros = [x for x, gg in zip(X, grupos) if gg == g]
        mu = [sum(c) / len(miembros) for c in zip(*miembros)]
        tot += sum(sum((a - b) ** 2 for a, b in zip(x, mu)) for x in miembros)
    return tot
