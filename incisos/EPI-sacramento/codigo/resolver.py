#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EPISODIOS A -> B DENTRO DE UNA VENTANA DE TIEMPO (OD/EPISODES.R)
================================================================
  MOMENT = cdatetime (entero); EVENT = descripcion en mayusculas y sin espacios en los
  extremos; CASE_ID = "G" + grid + "_B" + beat (read_csv recorta espacios: T14).
  Se ordena por CASE_ID y MOMENT (orden estable) y, dentro de cada caso, se forman todos los
  pares i < j con 0 < MOMENT_j - MOMENT_i <= wsize (wsize = 10).
  Soporte de un episodio = casos con el episodio / casos (global y por distrito).

Uso   python3 codigo/resolver.py        (lee datos/parametros.json)
Solo biblioteca estandar.
"""
import argparse
import csv
import json
import os
from collections import OrderedDict, defaultdict

AQUI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(AQUI)


def num(v):
    v = v.strip()
    if v == "" or v.upper() == "NA":
        return None
    x = float(v)
    return int(x) if x.is_integer() else x


def leer(ruta):
    filas = []
    for f in csv.DictReader(open(ruta, newline="", encoding="utf-8-sig")):
        f = {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in f.items()}
        m, ev = num(f["cdatetime"]), f["crimedescr"].upper() if f["crimedescr"] else None
        grid, beat, dist = num(f["grid"]), f["beat"], num(f["district"])
        if m is None or not ev or dist is None:
            continue
        # T23: como paste0() de R, un grid o beat vacio se escribe "NA" y la fila se queda
        caso = "G%s_B%s" % ("NA" if grid is None else grid, beat if beat else "NA")
        filas.append({"MOMENT": int(m), "EVENT": ev, "CASE_ID": caso, "district": dist})
    filas.sort(key=lambda r: (r["CASE_ID"], r["MOMENT"]))      # estable, como arrange()
    return filas


def episodios(filas, wsize):
    por_caso = OrderedDict()
    for r in filas:
        por_caso.setdefault(r["CASE_ID"], []).append(r)
    pares = []
    for caso, evs in por_caso.items():
        for i in range(len(evs)):
            for j in range(i + 1, len(evs)):
                d = evs[j]["MOMENT"] - evs[i]["MOMENT"]
                if 0 < d <= wsize:
                    pares.append(OrderedDict([("CASE_ID", caso), ("district", evs[i]["district"]),
                                              ("start_event", evs[i]["EVENT"]), ("next_event", evs[j]["EVENT"]),
                                              ("ep", "%s -> %s" % (evs[i]["EVENT"], evs[j]["EVENT"])),
                                              ("moment_start", evs[i]["MOMENT"]), ("moment_end", evs[j]["MOMENT"]), ("diff", d)]))
    return pares


def soporte(pares, n_casos):
    casos = defaultdict(set)
    for p in pares:
        casos[p["ep"]].add(p["CASE_ID"])
    tabla = [(ep, len(c), len(c) / n_casos) for ep, c in casos.items()]
    tabla.sort(key=lambda t: t[0])                 # count() ordena por ep
    tabla.sort(key=lambda t: -t[2])                # arrange(desc(support)), estable
    return tabla


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--parametros", default=os.path.join(BASE, "datos", "parametros.json"))
    ap.add_argument("--salida", default=BASE)
    a = ap.parse_args()
    par = json.load(open(a.parametros, encoding="utf-8"))
    wsize = par.get("wsize", 10)
    filas = leer(os.path.join(os.path.dirname(a.parametros), par["archivo"]))
    n_casos = len({r["CASE_ID"] for r in filas})
    pares = episodios(filas, wsize)
    glob = soporte(pares, n_casos)
    distritos = sorted({r["district"] for r in filas})
    por_d = []
    for d in distritos:
        fd = [r for r in filas if r["district"] == d]
        pd = episodios(fd, wsize)
        if pd:
            por_d += [(d, ep, c, s) for ep, c, s in soporte(pd, len({r["CASE_ID"] for r in fd}))]
    print("EPISODIOS — %s: %d eventos, %d casos, wsize = %d" % (par["archivo"], len(filas), n_casos, wsize))
    print("Pares (episodios) dentro de la ventana: %d; episodios distintos: %d" % (len(pares), len(glob)))
    print("Top 15 global:")
    for ep, c, s in glob[:15]:
        print("  %-80s %4d casos  soporte %.4f" % (ep[:80], c, s))
    with open(os.path.join(a.salida, "episodios_detalle_python.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(list(pares[0].keys()) if pares else [])
        for p in pares:
            w.writerow(list(p.values()))
    with open(os.path.join(a.salida, "episodios_globales_python.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["ep", "cases_with_ep", "support"])
        w.writerows(glob)
    with open(os.path.join(a.salida, "episodios_por_distrito_python.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["district", "ep", "cases_with_ep", "support"])
        w.writerows(por_d)
    traza = OrderedDict([("problema", par.get("problema", "")), ("archivo", par["archivo"]), ("wsize", wsize),
                         ("eventos", len(filas)), ("casos", n_casos), ("pares", len(pares)), ("episodios", len(glob)),
                         ("top_global", [OrderedDict([("ep", e), ("casos", c), ("soporte", s)]) for e, c, s in glob[:50]]),
                         ("distritos", OrderedDict((str(d), OrderedDict([("casos", len({r["CASE_ID"] for r in filas if r["district"] == d})),
                                                                          ("episodios", sum(1 for x in por_d if x[0] == d))])) for d in distritos))])
    json.dump(traza, open(os.path.join(a.salida, "traza.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("traza.json y tres CSV escritos")


if __name__ == "__main__":
    main()
