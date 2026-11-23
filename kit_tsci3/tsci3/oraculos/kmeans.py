"""Oráculo independiente del k-means del ejercicio de clase (no importa el resolver).

Otro camino: asignación comparando distancias al cuadrado, normalización con
(x − mín)/(máx − mín) en lugar de m·x + b, y bucle propio. Compara cada iteración de
traza.json (conteos, empates, ΣDMIN, centroides y cambios).

`replica_excel` reproduce las cifras en caché de los Excel del profesor, con la opción de
repetir el error de DOLLY LIVES.xlsx (T1): el término de una columna usa siempre la fila 8.
"""
import csv
import json
import math

TOL = 1e-9


def _leer(ruta, columnas):
    with open(ruta, newline="", encoding="utf-8-sig") as fh:
        lector = csv.reader(fh)
        enc = next(lector)
        idx = [enc.index(c) for c in columnas] if columnas else list(range(len(enc)))
        datos = []
        for f in lector:
            try:
                datos.append([float(f[i].replace(",", "")) for i in idx])
            except (ValueError, IndexError):
                pass
    return [enc[i] for i in idx], datos


def _norm(datos):
    nv = len(datos[0])
    lo = [min(x[j] for x in datos) for j in range(nv)]
    hi = [max(x[j] for x in datos) for j in range(nv)]
    return [[(x[j] - lo[j]) / (hi[j] - lo[j]) for j in range(nv)] for x in datos], lo, hi


def kmeans_clase(z, c0, c1, max_iter=100, actualizacion="clase", fija=None):
    """fija = (columna, vector): reproduce el error T1 usando ese valor en lugar del de cada fila."""
    salida, anterior = [], None
    for t in range(1, max_iter + 1):
        def d2(c, x):
            return sum((c[j] - (fija[1][j] if fija and j == fija[0] else x[j])) ** 2 for j in range(len(c)))
        a = [d2(c0, x) for x in z]
        b = [d2(c1, x) for x in z]
        p0 = [1 if u <= v else 0 for u, v in zip(a, b)]
        p1 = [1 if v <= u else 0 for u, v in zip(a, b)]
        n0, n1 = sum(p0), sum(p1)
        sdmin = sum(math.sqrt(min(u, v)) for u, v in zip(a, b))
        if actualizacion == "media":
            nc0 = [sum(x[j] for x, w in zip(z, p0) if w) / n0 for j in range(len(c0))]
            nc1 = [sum(x[j] for x, w in zip(z, p1) if w) / n1 for j in range(len(c1))]
        else:
            nc0 = [(sum(x[j] for x, w in zip(z, p0) if w) + c0[j]) / (n0 + 1) for j in range(len(c0))]
            nc1 = [(sum(x[j] for x, w in zip(z, p1) if w) + c1[j]) / (n1 + 1) for j in range(len(c1))]
        pert = [2 if u and v else 0 if u else 1 for u, v in zip(p0, p1)]
        cambios = None if anterior is None else sum(1 for u, v in zip(pert, anterior) if u != v)
        salida.append({"C0": c0, "C1": c1, "n0": n0, "n1": n1, "empates": pert.count(2),
                       "suma_dmin": sdmin, "C0_nuevo": nc0, "C1_nuevo": nc1, "cambios": cambios})
        if cambios == 0:
            break
        anterior, c0, c1 = pert, nc0, nc1
    return salida


def verificar(ruta_csv, ruta_traza):
    tr = json.load(open(ruta_traza, encoding="utf-8"))
    cols, datos = _leer(ruta_csv, tr["columnas"])
    res = []

    def chk(ok, msg):
        res.append((bool(ok), msg))
    chk(len(datos) == tr["n"], "registros: %d" % len(datos))
    z, lo, hi = _norm(datos)
    nm = tr["normalizacion"]
    okn = all(abs(nm[c]["m"] - 1 / (hi[j] - lo[j])) < TOL and abs(nm[c]["b"] + lo[j] / (hi[j] - lo[j])) < TOL
              for j, c in enumerate(cols))
    chk(okn, "normalización m = 1/(máx − mín) y b = −m·mín de %d variables" % len(cols))
    nv = len(cols)
    orac = kmeans_clase(z, [0.0] * nv, [1.0] * nv, len(tr["iteraciones"]) + 1, tr.get("actualizacion", "clase"))
    chk(len(orac) == len(tr["iteraciones"]), "iteraciones hasta que la pertenencia no cambia: oráculo %d, traza %d" % (
        len(orac), len(tr["iteraciones"])))
    malos = []
    for o, t in zip(orac, tr["iteraciones"]):
        k = t["iteracion"]
        if (o["n0"], o["n1"], o["empates"], o["cambios"]) != (t["n0"], t["n1"], t["empates"], t["cambios"]):
            malos.append("it %d conteos" % k)
        if abs(o["suma_dmin"] - t["suma_dmin"]) > 1e-6 * max(1, abs(o["suma_dmin"])):
            malos.append("it %d ΣDMIN" % k)
        for nombre in ("C0", "C1", "C0_nuevo", "C1_nuevo"):
            if any(abs(u - v) > 1e-9 for u, v in zip(o[nombre], t[nombre])):
                malos.append("it %d %s" % (k, nombre))
    chk(not malos, "conteos, empates, ΣDMIN y centroides de cada iteración" + (": %s" % malos[:5] if malos else ""))
    return res


def replica_excel(datos, fija_columna=None, fila_fija=0, actualizacion="clase"):
    """Primera iteración tal como la calcula el Excel del profesor (con el error T1 opcional)."""
    z, _, _ = _norm(datos)
    nv = len(z[0])
    fija = (fija_columna, z[fila_fija]) if fija_columna is not None else None
    return kmeans_clase(z, [0.0] * nv, [1.0] * nv, 1, actualizacion, fija)[0]
