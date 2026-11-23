"""Oráculo independiente de episodios (no importa el resolver).

Otro camino: agrupa por caso con un diccionario, ordena cada caso por (MOMENT, posición en el
archivo) y avanza una ventana [t + 1, t + wsize] con dos punteros. Recalcula los casos con cada
episodio y el soporte global y por distrito, y los compara con los CSV de resolver.py.
"""
import csv
import json
import os
from collections import defaultdict


def _eventos(ruta, cols=None):
    cols = cols or {}
    c_mom = cols.get("momento", "cdatetime")
    c_ev = cols.get("evento", "crimedescr")
    c_grid = cols.get("grid", "grid")
    c_beat = cols.get("beat", "beat")
    c_caso = cols.get("caso")
    c_dist = cols.get("distrito", "district")
    out = []
    for i, f in enumerate(csv.DictReader(open(ruta, newline="", encoding="utf-8-sig"))):
        f = {k.strip(): v.strip() for k, v in f.items()}
        if not f.get(c_mom) or not f.get(c_ev) or not f.get(c_dist):
            continue
        if c_caso and c_caso in f:
            caso = f[c_caso] or "NA"
        else:
            grid = f.get(c_grid, "") or "NA"
            if grid not in ("NA",):
                g = float(grid)
                grid = str(int(g)) if g.is_integer() else str(g)
            caso = "G%s_B%s" % (grid, f.get(c_beat, "") or "NA")
        out.append((i, int(float(f[c_mom])), f[c_ev].upper(), caso, f[c_dist]))
    return out


def _pares(evs, wsize, minimo=1):
    casos = defaultdict(list)
    for e in evs:
        casos[e[3]].append(e)
    pares = []
    for c, lista in casos.items():
        lista.sort(key=lambda e: (e[1], e[0]))
        for i, e in enumerate(lista):
            for f in lista[i + 1:]:
                d = f[1] - e[1]
                if d > wsize:
                    break
                if d >= minimo:
                    pares.append((c, e[4], "%s -> %s" % (e[2], f[2])))
    return pares, len(casos)


def _soporte(pares, n):
    casos = defaultdict(set)
    for c, _, ep in pares:
        casos[ep].add(c)
    return {ep: (len(s), len(s) / n) for ep, s in casos.items()}


def verificar(ruta_csv, ruta_traza):
    tr = json.load(open(ruta_traza, encoding="utf-8"))
    I = os.path.dirname(os.path.abspath(ruta_traza))
    w = tr["wsize"]
    par_p = os.path.join(I, "datos", "parametros.json")
    cols_cfg = json.load(open(par_p, encoding="utf-8")).get("columnas") if os.path.exists(par_p) else None
    evs = _eventos(ruta_csv, cols_cfg)
    pares, n = _pares(evs, w)
    res = [(len(evs) == tr["eventos"] and n == tr["casos"], "eventos %d y casos %d" % (len(evs), n)),
           (len(pares) == tr["pares"], "pares con 0 < Δ ≤ %d: %d" % (w, len(pares)))]
    glob = _soporte(pares, n)
    py = {f["ep"]: (int(f["cases_with_ep"]), float(f["support"]))
          for f in csv.DictReader(open(os.path.join(I, "episodios_globales_python.csv"), encoding="utf-8"))}
    res.append((set(py) == set(glob) and all(py[k][0] == glob[k][0] and abs(py[k][1] - glob[k][1]) < 1e-12 for k in glob),
                "soporte global de %d episodios" % len(glob)))
    malos = 0
    pyd = defaultdict(dict)
    for f in csv.DictReader(open(os.path.join(I, "episodios_por_distrito_python.csv"), encoding="utf-8")):
        pyd[f["district"]][f["ep"]] = (int(f["cases_with_ep"]), float(f["support"]))
    for d in sorted({e[4] for e in evs}):
        pd, nd = _pares([e for e in evs if e[4] == d], w)
        sd = _soporte(pd, nd)
        if set(sd) != set(pyd.get(d, {})) or any(pyd[d][k][0] != sd[k][0] or abs(pyd[d][k][1] - sd[k][1]) > 1e-12 for k in sd):
            malos += 1
    res.append((malos == 0, "soporte por distrito" + (": difieren %d distritos" % malos if malos else "")))
    mut, _ = _pares(evs, w, minimo=0)
    res.append((len(mut) != len(pares), "mutante Δ ≥ 0: %d pares en lugar de %d (se detecta)" % (len(mut), len(pares))))
    return res
