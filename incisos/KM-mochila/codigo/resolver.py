#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K-MEANS CON LA CONVENCION DEL EJERCICIO DE CLASE (mochila_.xlsx, DOLLY LIVES.xlsx)
==================================================================================
  1. Normalizacion de cada variable: y = m*x + b, m = 1/(max - min), b = -m*min
     (OD/mochila_.xlsx B4:D5; DOLLY LIVES.xlsx B4:M5).
  2. Centroides iniciales: C0 = vector minimo y C1 = vector maximo normalizados
     (mochila E6:G7; DOLLY O2:Z3) -> C0 = (0, ..., 0), C1 = (1, ..., 1).
  3. Distancia euclidiana de cada registro a cada centroide (DC0, DC1), DMIN = min,
     pertenencia C0 = 1 si DMIN = DC0 y C1 = 1 si DMIN = DC1 (un empate cuenta en ambos).
  4. Actualizacion del Excel (T7): C' = (sum(x * pertenencia) + C) / (n + 1)
     (mochila J6:L7; DOLLY AG2:AR3). Con --actualizacion media: C' = promedio de sus miembros.
  5. Se repite hasta que la pertenencia no cambia (una hoja de Excel por iteracion).

Uso   python3 codigo/resolver.py                      (lee datos/parametros.json)
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


def leer(ruta, columnas):
    with open(ruta, newline="", encoding="utf-8-sig") as fh:
        filas = list(csv.DictReader(fh))
    cols = columnas or list(filas[0].keys())
    datos, omitidas = [], []
    for i, f in enumerate(filas, 1):
        try:
            datos.append([float(str(f[c]).replace(",", "")) for c in cols])
        except (ValueError, TypeError):
            omitidas.append(i)
    return cols, datos, omitidas


def normalizar(datos):
    n_var = len(datos[0])
    par = []
    for j in range(n_var):
        col = [x[j] for x in datos]
        lo, hi = min(col), max(col)
        if hi == lo:
            raise SystemExit("La variable %d es constante (max = min): m = 1/(max - min) no existe." % (j + 1))
        m = 1 / (hi - lo)
        par.append((lo, hi, m, -m * lo))
    return [[par[j][2] * x[j] + par[j][3] for j in range(n_var)] for x in datos], par


def iterar(z, c0, c1, actualizacion):
    d0 = [math.sqrt(sum((a - b) ** 2 for a, b in zip(c0, x))) for x in z]
    d1 = [math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, x))) for x in z]
    dmin = [min(a, b) for a, b in zip(d0, d1)]
    p0 = [1 if m == a else 0 for m, a in zip(dmin, d0)]
    p1 = [1 if m == b else 0 for m, b in zip(dmin, d1)]
    n0, n1 = sum(p0), sum(p1)

    def nuevo(c, p, n):
        if actualizacion == "media":
            return [sum(x[j] * w for x, w in zip(z, p)) / n if n else c[j] for j in range(len(c))]
        return [(sum(x[j] * w for x, w in zip(z, p)) + c[j]) / (n + 1) for j in range(len(c))]
    return d0, d1, dmin, p0, p1, n0, n1, nuevo(c0, p0, n0), nuevo(c1, p1, n1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--parametros", default=os.path.join(BASE, "datos", "parametros.json"))
    ap.add_argument("--salida", default=BASE)
    a = ap.parse_args()
    par = json.load(open(a.parametros, encoding="utf-8"))
    ruta = os.path.join(os.path.dirname(a.parametros), par["archivo"])
    cols, datos, omitidas = leer(ruta, par.get("columnas"))
    actualizacion = par.get("actualizacion", "clase")
    max_iter = par.get("max_iter", 100)
    z, norm = normalizar(datos)
    nv = len(cols)
    c0 = [min(x[j] for x in z) for j in range(nv)]
    c1 = [max(x[j] for x in z) for j in range(nv)]
    iters, anterior = [], None
    print("K-MEANS (convencion del ejercicio de clase) — %s: %d registros, %d variables" % (par["archivo"], len(z), nv))
    if omitidas:
        print("Filas omitidas por valores no numericos o vacios: %d (primeras: %s)" % (len(omitidas), omitidas[:10]))
    print("Normalizacion y = m*x + b:")
    for c, (lo, hi, m, b) in zip(cols, norm):
        print("  %-22s min=%-12g max=%-12g m=%.6f b=%.6f" % (c, lo, hi, m, b))
    for t in range(1, max_iter + 1):
        d0, d1, dmin, p0, p1, n0, n1, nc0, nc1 = iterar(z, c0, c1, actualizacion)
        pert = [0 if x and not y else 1 if y and not x else 2 for x, y in zip(p0, p1)]   # 2 = empate
        cambios = None if anterior is None else sum(1 for u, v in zip(pert, anterior) if u != v)
        it = OrderedDict([("iteracion", t), ("C0", c0), ("C1", c1), ("n0", n0), ("n1", n1),
                          ("empates", sum(1 for x in pert if x == 2)), ("suma_dmin", sum(dmin)),
                          ("C0_nuevo", nc0), ("C1_nuevo", nc1), ("cambios", cambios)])
        if len(z) <= 5000:
            it["DC0"], it["DC1"], it["pertenencia"] = d0, d1, pert
        iters.append(it)
        print("Iteracion %d: |C0| = %d, |C1| = %d, empates = %d, suma DMIN = %.6f, cambios = %s" % (
            t, n0, n1, it["empates"], it["suma_dmin"], "—" if cambios is None else cambios))
        if anterior is not None and cambios == 0:
            break
        anterior = pert
        c0, c1 = nc0, nc1
    final = iters[-1]
    traza = OrderedDict([
        ("problema", par.get("problema", "")), ("archivo", par["archivo"]), ("n", len(z)), ("columnas", cols),
        ("filas_omitidas", omitidas), ("actualizacion", actualizacion),
        ("normalizacion", OrderedDict((c, OrderedDict(zip(("min", "max", "m", "b"), v))) for c, v in zip(cols, norm))),
        ("iteraciones", iters),
        ("resumen", OrderedDict([("iteraciones", len(iters)), ("convergio", final["cambios"] == 0),
                                 ("n0", final["n0"]), ("n1", final["n1"]), ("suma_dmin", final["suma_dmin"]),
                                 ("C0", final["C0"]), ("C1", final["C1"])])),
    ])
    print("Centroides finales (normalizados):")
    print("  C0 = (%s)" % ", ".join("%.6f" % x for x in final["C0"]))
    print("  C1 = (%s)" % ", ".join("%.6f" % x for x in final["C1"]))
    print("  en unidades originales: C0 = (%s); C1 = (%s)" % (
        ", ".join("%.4g" % ((x - b) / m) for x, (_, _, m, b) in zip(final["C0"], norm)),
        ", ".join("%.4g" % ((x - b) / m) for x, (_, _, m, b) in zip(final["C1"], norm))))
    with open(os.path.join(a.salida, "traza.json"), "w", encoding="utf-8") as fh:
        json.dump(traza, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("traza.json escrita")


if __name__ == "__main__":
    main()
