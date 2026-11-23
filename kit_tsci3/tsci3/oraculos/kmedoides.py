"""Oráculo independiente de k-medoides (no importa el resolver).

* Criterio de clase: recalcula C' (una iteración de k-means), el registro más cercano a cada
  centroide, DM0/DM1, pertenencia y costo, y la silueta con una matriz de distancias propia.
* PAM: no vuelve a correr BUILD/SWAP; comprueba que los medoides de la traza son registros,
  que su costo es el reportado y que ningún intercambio medoide ↔ no medoide lo mejora.
* `replica_excel` reproduce AF57/AG57 de DOLLY LIVES.xlsx Sheet2 con el error T1.
"""
import json
import math

from . import kmeans as km

TOL = 1e-9


def _d(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def medoides_clase(z, fija=None):
    it = km.kmeans_clase(z, [0.0] * len(z[0]), [1.0] * len(z[0]), 1, "clase", fija)[0]

    def dist_fija(c, x):
        return math.sqrt(sum((c[j] - (fija[1][j] if fija and j == fija[0] else x[j])) ** 2 for j in range(len(c))))
    e0 = [dist_fija(it["C0_nuevo"], x) for x in z]
    e1 = [dist_fija(it["C1_nuevo"], x) for x in z]
    i0 = min(range(len(z)), key=lambda i: (e0[i], i))
    i1 = min((i for i in range(len(z)) if i != i0), key=lambda i: (e1[i], i)) if min(
        range(len(z)), key=lambda i: (e1[i], i)) == i0 else min(range(len(z)), key=lambda i: (e1[i], i))
    return it, e0[i0], e1[i1], i0, i1


def _silueta(D, grupo):
    n = len(D)
    s = []
    for i in range(n):
        por = {}
        for j in range(n):
            if j != i:
                por.setdefault(grupo[j], []).append(D[i][j])
        if not por.get(grupo[i]):
            s.append(0.0)
            continue
        a = sum(por[grupo[i]]) / len(por[grupo[i]])
        b = min(sum(v) / len(v) for g, v in por.items() if g != grupo[i])
        s.append((b - a) / max(a, b))
    return s


def verificar(ruta_csv, ruta_traza):
    tr = json.load(open(ruta_traza, encoding="utf-8"))
    _, datos = km._leer(ruta_csv, tr["columnas"])
    z, _, _ = km._norm(datos)
    res = []

    def chk(ok, msg):
        res.append((bool(ok), msg))
    it, d0, d1, i0, i1 = medoides_clase(z)
    c = tr["clase"]
    chk(all(abs(u - v) < TOL for u, v in zip(it["C0_nuevo"] + it["C1_nuevo"], c["C0_nuevo"] + c["C1_nuevo"])),
        "C0' y C1' de la iteración de k-means")
    chk((i0 + 1, i1 + 1) == (c["M0_registro"], c["M1_registro"]) and abs(d0 - c["min_dist_C0"]) < TOL and abs(d1 - c["min_dist_C1"]) < TOL,
        "medoides de clase: registros %d y %d (distancias %.6f y %.6f)" % (i0 + 1, i1 + 1, d0, d1))
    chk(all(abs(u - v) < TOL for u, v in zip(z[i0] + z[i1], c["M0"] + c["M1"])), "M0 y M1 son los vectores de esos registros")
    n = len(z)
    D = [[_d(z[i], z[j]) for j in range(n)] for i in range(n)] if n <= 3000 else None
    dm = [(_d(x, z[i0]), _d(x, z[i1])) for x in z]
    costo = sum(min(a, b) for a, b in dm)
    chk(abs(costo - c["costo"]) < 1e-6 and sum(1 for a, b in dm if a <= b) == c["n0"] and sum(1 for a, b in dm if b <= a) == c["n1"],
        "DM0, DM1, pertenencia (%d, %d) y costo %.6f" % (c["n0"], c["n1"], costo))
    if D:
        s = _silueta(D, c["grupo"])
        chk(all(abs(u - v) < 1e-9 for u, v in zip(s, c["silueta"])), "silueta de cada registro (criterio de clase), media %.4f" % (sum(s) / n))
    if "pam" in tr and D:
        p = tr["pam"]
        M = [i - 1 for i in p["medoides_registro"]]
        cst = lambda MM: sum(min(D[i][m] for m in MM) for i in range(n))
        cp = cst(M)
        mejora = min(cst(M[:a] + [h] + M[a + 1:]) for a in range(len(M)) for h in range(n) if h not in M)
        chk(abs(cp - p["costo"]) < 1e-6, "costo PAM de los medoides %s: %.6f" % (p["medoides_registro"], cp))
        chk(mejora >= cp - 1e-12, "ningún intercambio medoide ↔ registro baja el costo (mejor alternativa %.6f)" % mejora)
        s = _silueta(D, p["grupo"])
        chk(all(abs(u - v) < 1e-9 for u, v in zip(s, p["silueta"])), "silueta de cada registro (PAM), media %.4f" % (sum(s) / n))
    return res


def replica_excel(datos, fija_columna=None, fila_fija=0):
    z, _, _ = km._norm(datos)
    fija = (fija_columna, z[fila_fija]) if fija_columna is not None else None
    it, d0, d1, i0, i1 = medoides_clase(z, fija)
    return {"min_dist_C0": d0, "min_dist_C1": d1, "M0": z[i0], "M1": z[i1], "M0_registro": i0 + 1, "M1_registro": i1 + 1}
