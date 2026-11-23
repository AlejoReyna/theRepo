#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K-MEDOIDES: CRITERIO DEL EJERCICIO DE CLASE (DOLLY LIVES.xlsx, Sheet2) Y PAM
============================================================================
Criterio de clase (OD/DOLLY LIVES.xlsx Sheet2):
  1. Normalizacion y = m*x + b y una iteracion de k-means con C0 = minimo y C1 = maximo:
     C' = (sum(x * pertenencia) + C) / (n + 1)  (AG2:AR3, T7).
  2. Distancia de cada registro a C0' y C1' (AF8:AG56); el medoide es el registro mas
     cercano a cada centroide (AF57, AG57 -> M0 y M1 en AG4:AR5).
  3. Columnas que el archivo deja vacias: DM0 y DM1 (distancia a cada medoide), DMIN,
     nueva pertenencia y costo = sum(DMIN).
Criterio PAM (OD/TSCI3 P6.R usa cluster::pam): BUILD + SWAP exactos sobre los mismos
datos normalizados (hasta 2000 registros; con mas, CLARA en R).
Ambos: silueta s(i) = (b(i) - a(i)) / max{a(i), b(i)} (Novianti et al., ec. 3).

Uso   python3 codigo/resolver.py         (lee datos/parametros.json)
Solo biblioteca estandar.
"""
import argparse
import csv
import json
import math
import os
from collections import OrderedDict

AQUI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(AQUI)
LIMITE_PAM = 2000


def leer(ruta, columnas):
    with open(ruta, newline="", encoding="utf-8-sig") as fh:
        filas = list(csv.DictReader(fh))
    cols = columnas or list(filas[0].keys())
    datos = []
    for f in filas:
        try:
            datos.append([float(str(f[c]).replace(",", "")) for c in cols])
        except (ValueError, TypeError):
            pass
    return cols, datos


def dist(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def asignar(z, medoides):
    d = [[dist(x, z[m]) for m in medoides] for x in z]
    dmin = [min(r) for r in d]
    pert = [[1 if v == mn else 0 for v in r] for r, mn in zip(d, dmin)]
    return d, dmin, pert


def silueta(z, grupo):
    """grupo[i] = indice del grupo (el primero si hay empate). s = 0 si el grupo tiene un solo miembro."""
    k = max(grupo) + 1
    s = []
    for i, x in enumerate(z):
        sumas, cuenta = [0.0] * k, [0] * k
        for j, y in enumerate(z):
            if i != j:
                sumas[grupo[j]] += dist(x, y)
                cuenta[grupo[j]] += 1
        g = grupo[i]
        if cuenta[g] == 0:
            s.append(0.0)
            continue
        a = sumas[g] / cuenta[g]
        b = min(sumas[h] / cuenta[h] for h in range(k) if h != g and cuenta[h])
        s.append((b - a) / max(a, b) if max(a, b) > 0 else 0.0)
    return s


def pam(z, k):
    n = len(z)
    D = [[dist(z[i], z[j]) for j in range(n)] for i in range(n)]
    costo = lambda M: sum(min(D[i][m] for m in M) for i in range(n))
    M = [min(range(n), key=lambda j: (sum(D[i][j] for i in range(n)), j))]          # BUILD
    while len(M) < k:
        mejor = min((j for j in range(n) if j not in M),
                    key=lambda j: (costo(M + [j]), j))
        M.append(mejor)
    c = costo(M)
    while True:                                                                       # SWAP
        mejor = (c, None, None)
        for a in range(len(M)):
            for h in range(n):
                if h in M:
                    continue
                prueba = M[:a] + [h] + M[a + 1:]
                cp = costo(prueba)
                if cp < mejor[0] - 1e-12:
                    mejor = (cp, a, h)
        if mejor[1] is None:
            break
        M[mejor[1]] = mejor[2]
        c = mejor[0]
    return M, c


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--parametros", default=os.path.join(BASE, "datos", "parametros.json"))
    ap.add_argument("--salida", default=BASE)
    a = ap.parse_args()
    par = json.load(open(a.parametros, encoding="utf-8"))
    cols, datos = leer(os.path.join(os.path.dirname(a.parametros), par["archivo"]), par.get("columnas"))
    nv, n = len(cols), len(datos)
    lo = [min(x[j] for x in datos) for j in range(nv)]
    hi = [max(x[j] for x in datos) for j in range(nv)]
    m = [1 / (h - l) for l, h in zip(lo, hi)]
    b = [-mm * l for mm, l in zip(m, lo)]
    z = [[m[j] * x[j] + b[j] for j in range(nv)] for x in datos]
    c0, c1 = [min(x[j] for x in z) for j in range(nv)], [max(x[j] for x in z) for j in range(nv)]
    d0 = [dist(c0, x) for x in z]
    d1 = [dist(c1, x) for x in z]
    p0 = [1 if min(u, v) == u else 0 for u, v in zip(d0, d1)]
    p1 = [1 if min(u, v) == v else 0 for u, v in zip(d0, d1)]
    n0, n1 = sum(p0), sum(p1)
    c0n = [(sum(x[j] * w for x, w in zip(z, p0)) + c0[j]) / (n0 + 1) for j in range(nv)]
    c1n = [(sum(x[j] * w for x, w in zip(z, p1)) + c1[j]) / (n1 + 1) for j in range(nv)]
    e0 = [dist(c0n, x) for x in z]
    e1 = [dist(c1n, x) for x in z]
    i0 = min(range(n), key=lambda i: (e0[i], i))
    i1 = min(range(n), key=lambda i: (e1[i], i))
    if i1 == i0:                                         # mismo registro para ambos: el siguiente mas cercano a C1'
        i1 = min((i for i in range(n) if i != i0), key=lambda i: (e1[i], i))
    dm, dmin, pert = asignar(z, [i0, i1])
    grupo = [0 if r[0] else 1 for r in pert]
    sil = silueta(z, grupo)
    clase = OrderedDict([
        ("C0_nuevo", c0n), ("C1_nuevo", c1n), ("n0_kmeans", n0), ("n1_kmeans", n1),
        ("min_dist_C0", e0[i0]), ("min_dist_C1", e1[i1]),
        ("M0_registro", i0 + 1), ("M1_registro", i1 + 1), ("M0", z[i0]), ("M1", z[i1]),
        ("n0", sum(r[0] for r in pert)), ("n1", sum(r[1] for r in pert)),
        ("empates", sum(1 for r in pert if r[0] and r[1])), ("costo", sum(dmin)),
        ("silueta_media", sum(sil) / n), ("silueta", sil), ("grupo", grupo), ("DM0", [r[0] for r in dm]), ("DM1", [r[1] for r in dm]),
    ])
    print("K-MEDOIDES — %s: %d registros, %d variables" % (par["archivo"], n, nv))
    print("Criterio de clase (medoide = registro mas cercano a C'): M0 = registro %d (dist %.6f), M1 = registro %d (dist %.6f)" % (
        i0 + 1, e0[i0], i1 + 1, e1[i1]))
    print("  pertenencia a medoides: |M0| = %d, |M1| = %d, empates = %d, costo = %.6f, silueta media = %.4f" % (
        clase["n0"], clase["n1"], clase["empates"], clase["costo"], clase["silueta_media"]))
    traza = OrderedDict([("problema", par.get("problema", "")), ("archivo", par["archivo"]), ("n", n), ("columnas", cols),
                         ("normalizacion", OrderedDict((c, OrderedDict([("min", l), ("max", h), ("m", mm), ("b", bb)]))
                                                       for c, l, h, mm, bb in zip(cols, lo, hi, m, b))),
                         ("clase", clase)])
    if n <= LIMITE_PAM:
        M, costo = pam(z, 2)
        dmp, dminp, pertp = asignar(z, M)
        gp = [min(range(2), key=lambda k: (r[k], k)) for r in dmp]
        silp = silueta(z, gp)
        traza["pam"] = OrderedDict([("medoides_registro", [i + 1 for i in M]), ("medoides", [z[i] for i in M]),
                                    ("costo", costo), ("tamanos", [gp.count(0), gp.count(1)]),
                                    ("silueta_media", sum(silp) / n), ("silueta", silp), ("grupo", gp)])
        print("Criterio PAM (BUILD + SWAP): medoides = registros %s, costo = %.6f, tamanos = %s, silueta media = %.4f" % (
            [i + 1 for i in M], costo, traza["pam"]["tamanos"], traza["pam"]["silueta_media"]))
    else:
        print("PAM exacto omitido (%d > %d registros): usar CLARA en R" % (n, LIMITE_PAM))
    with open(os.path.join(a.salida, "traza.json"), "w", encoding="utf-8") as fh:
        json.dump(traza, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("traza.json escrita")


if __name__ == "__main__":
    main()
