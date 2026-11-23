"""Oráculo independiente de Apriori (no importa el resolver).

Otro camino: cuenta cada subconjunto de cada transacción (enumeración directa, sin unir
itemsets por niveles), arma todas las reglas con consecuente de un ítem y las compara con la
traza (número de reglas, soporte, confianza y lift). Recuenta también las reglas pedidas.
"""
import csv
import json
from itertools import combinations


def transacciones(ruta, columnas, na):
    filas = list(csv.DictReader(open(ruta, newline="", encoding="utf-8-sig")))
    cols = columnas or list(filas[0].keys())
    return [frozenset("%s=%s" % (c, f[c]) for c in cols if f[c] not in na) for f in filas]


def contar(trans, maxlen=10):
    cuenta = {}
    for t in trans:
        items = sorted(t)
        for k in range(1, min(len(items), maxlen) + 1):
            for s in combinations(items, k):
                fs = frozenset(s)
                cuenta[fs] = cuenta.get(fs, 0) + 1
    return cuenta


def verificar(ruta_csv, ruta_traza, na=("", "NA")):
    tr = json.load(open(ruta_traza, encoding="utf-8"))
    trans = transacciones(ruta_csv, tr["columnas"], set(na))
    n = len(trans)
    res = []

    def chk(ok, msg):
        res.append((bool(ok), msg))
    cuenta = contar(trans)
    frec = {s: c for s, c in cuenta.items() if c / n >= tr["soporte_min"]}
    reglas = {}
    for s, c in frec.items():
        for y in s:
            x = s - {y}
            cx = frec[x] if x else n
            if c / cx >= tr["confianza_min"]:
                reglas[(x, y)] = (c / n, c / cx, c * n / (cx * frec[frozenset([y])]))
    por_nivel = {}
    for s in frec:
        por_nivel[len(s)] = por_nivel.get(len(s), 0) + 1
    chk([por_nivel.get(k, 0) for k in range(1, len(tr["niveles"]) + 1)] == [nv["itemsets"] for nv in tr["niveles"]],
        "itemsets frecuentes por nivel: %s" % [por_nivel[k] for k in sorted(por_nivel)])
    tr_r = {(frozenset(r["lhs"]), r["rhs"]): (r["soporte"], r["confianza"], r["lift"]) for r in tr["reglas"]}
    iguales = set(tr_r) == set(reglas) and all(max(abs(a - b) for a, b in zip(tr_r[k], reglas[k])) < 1e-12 for k in reglas)
    chk(iguales, "reglas: oráculo %d, traza %d; soporte, confianza y lift iguales" % (len(reglas), len(tr_r)))
    malos = []
    for p in tr.get("reglas_pedidas", []):
        x, y = frozenset(p["lhs"]), p["rhs"]
        cx = sum(1 for t in trans if x <= t)
        cy = sum(1 for t in trans if y in t)
        cxy = sum(1 for t in trans if x <= t and y in t)
        if (cx, cy, cxy) != (p["NX"], p["NY"], p["NXY"]):
            malos.append("%s => %s" % (sorted(x), y))
    if tr.get("reglas_pedidas"):
        chk(not malos, "reglas pedidas: NX, NY y NX∧Y recontados" + (" (difieren %s)" % malos if malos else ""))
    return res
