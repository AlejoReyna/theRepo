#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
REGLAS DE ASOCIACION CON APRIORI (por niveles), COMO arules
===========================================================
  S = N(X y Y)/N;  C = N(X y Y)/N(X);  L = N(X y Y)*N/(N(X)*N(Y))   (OD/AP (1).xlsx M4:O11)
  Dos etapas: itemsets frecuentes por niveles con la propiedad de cierre descendente
  (todo subconjunto de un itemset frecuente es frecuente) y reglas con confianza minima
  (Gao, Wang y Yang 2023, EJ26-24 p.6). Umbrales del curso: soporte 0.01, confianza 0.1
  (OD/arules R (2).txt).
  Igual que arules::apriori: items "columna=valor" (las celdas vacias o NA no son items),
  consecuente de un solo item, longitud maxima 10 y reglas con antecedente vacio {} => {Y}.

Uso   python3 codigo/resolver.py        (lee datos/parametros.json)
Solo biblioteca estandar.
"""
import argparse
import csv
import json
import os
import re
from collections import OrderedDict
from itertools import combinations

AQUI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(AQUI)


def es_numero(v):
    return re.fullmatch(r"\s*[-+]?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?\s*", v) is not None


def leer(ruta, columnas, na):
    with open(ruta, newline="", encoding="utf-8-sig") as fh:
        filas = list(csv.DictReader(fh))
    cols = columnas or list(filas[0].keys())
    numericas = [c for c in cols if all(es_numero(f[c]) for f in filas if f[c] not in na) and any(f[c] not in na for f in filas)]
    if numericas:
        raise SystemExit("Columnas numericas %s: discretizalas o quitalas de 'columnas' (arules las discretizaria solo)." % numericas)
    trans = [frozenset("%s=%s" % (c, f[c]) for c in cols if f[c] not in na) for f in filas]
    return cols, trans


def apriori(trans, minsup, maxlen=10):
    n = len(trans)
    tid = {}
    for i, t in enumerate(trans):
        for it in t:
            tid.setdefault(it, set()).add(i)
    nivel = {frozenset([it]): s for it, s in tid.items() if len(s) / n >= minsup}
    frecuentes = [dict((k, len(v)) for k, v in nivel.items())]
    k = 1
    while nivel and k < maxlen:
        k += 1
        claves = sorted(nivel, key=lambda s: sorted(s))
        cand = {}
        for a, b in combinations(claves, 2):
            u = a | b
            if len(u) != k or u in cand:
                continue
            if all(frozenset(s) in nivel for s in combinations(u, k - 1)):        # cierre descendente
                cand[u] = nivel[a] & nivel[b]
        nivel = {c: s for c, s in cand.items() if len(s) / n >= minsup}
        if nivel:
            frecuentes.append(dict((c, len(s)) for c, s in nivel.items()))
    return frecuentes


def reglas(frecuentes, n, minconf):
    cuenta = {}
    for nv in frecuentes:
        cuenta.update(nv)
    salida = []
    for nv in frecuentes:
        for items, cxy in nv.items():
            for y in items:
                x = items - {y}
                cx = cuenta[x] if x else n
                conf = cxy / cx
                if conf >= minconf:
                    cy = cuenta[frozenset([y])]
                    salida.append(OrderedDict([("lhs", sorted(x)), ("rhs", y), ("NX", cx), ("NY", cy), ("NXY", cxy),
                                               ("soporte", cxy / n), ("confianza", conf), ("cobertura", cx / n),
                                               ("lift", cxy * n / (cx * cy))]))
    return salida


def texto(r):
    return "{%s} => {%s}" % (",".join(r["lhs"]), r["rhs"])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--parametros", default=os.path.join(BASE, "datos", "parametros.json"))
    ap.add_argument("--salida", default=BASE)
    a = ap.parse_args()
    par = json.load(open(a.parametros, encoding="utf-8"))
    na = set(par.get("na", ["", "NA"]))
    cols, trans = leer(os.path.join(os.path.dirname(a.parametros), par["archivo"]), par.get("columnas"), na)
    n = len(trans)
    sup, conf = par.get("soporte", 0.01), par.get("confianza", 0.1)
    frec = apriori(trans, sup, par.get("maxlen", 10))
    rs = reglas(frec, n, conf)
    rs.sort(key=lambda r: (-r["lift"], -r["confianza"], -r["soporte"], texto(r)))
    print("APRIORI — %s: %d transacciones, %d items, soporte >= %g, confianza >= %g" % (
        par["archivo"], n, len(frec[0]) if frec else 0, sup, conf))
    for k, nv in enumerate(frec, 1):
        print("  Nivel %d: %d itemsets frecuentes" % (k, len(nv)))
    print("Reglas: %d (con antecedente vacio: %d)" % (len(rs), sum(1 for r in rs if not r["lhs"])))
    for r in rs[:10]:
        print("  %-70s S=%.4f C=%.4f L=%.4f n=%d" % (texto(r)[:70], r["soporte"], r["confianza"], r["lift"], r["NXY"]))
    pedidas = []
    for p in par.get("reglas_pedidas", []):
        x, y = frozenset(p["si"]), p["entonces"]
        cx = sum(1 for t in trans if x <= t)
        cy = sum(1 for t in trans if y in t)
        cxy = sum(1 for t in trans if x <= t and y in t)
        pedidas.append(OrderedDict([("lhs", sorted(x)), ("rhs", y), ("NX", cx), ("NY", cy), ("NXY", cxy), ("soporte", cxy / n),
                                    ("confianza", cxy / cx if cx else None), ("lift", cxy * n / (cx * cy) if cx and cy else None)]))
        print("  pedida %-60s NX=%d NY=%d NXY=%d S=%.4f C=%s L=%s" % (texto(pedidas[-1]), cx, cy, cxy, cxy / n,
              "%.4f" % (cxy / cx) if cx else "—", "%.4f" % (cxy * n / (cx * cy)) if cx and cy else "—"))
    traza = OrderedDict([("problema", par.get("problema", "")), ("archivo", par["archivo"]), ("n", n), ("columnas", cols),
                         ("soporte_min", sup), ("confianza_min", conf),
                         ("niveles", [OrderedDict([("nivel", k), ("itemsets", len(nv)),
                                                   ("muestra", [[sorted(s), c] for s, c in sorted(nv.items(), key=lambda kv: (-kv[1], sorted(kv[0])))[:200]])])
                                      for k, nv in enumerate(frec, 1)]),
                         ("n_reglas", len(rs)), ("reglas", rs), ("reglas_pedidas", pedidas)])
    with open(os.path.join(a.salida, "traza.json"), "w", encoding="utf-8") as fh:
        json.dump(traza, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    with open(os.path.join(a.salida, "reglas_python.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["rules", "support", "confidence", "coverage", "lift", "count"])
        for r in rs:
            w.writerow([texto(r), r["soporte"], r["confianza"], r["cobertura"], r["lift"], r["NXY"]])
    print("traza.json y reglas_python.csv escritas")


if __name__ == "__main__":
    main()
