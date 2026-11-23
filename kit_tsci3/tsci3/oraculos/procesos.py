"""Oráculo independiente del modelado de procesos (no importa el resolver de la skill).

Recalcula desde el registro (lector XLSX del kit): trazas ordenadas por timestamp,
variantes, |x>y|, dependencias del Heuristics Miner y de bucles de longitud 2.
Revisa la red de la traza por otro camino:
  * grafo de alcanzabilidad propio -> segura, sólida (opción de completar, terminación
    propia, sin transiciones muertas), red WF, libre elección;
  * aceptación de cada traza del registro por la red (búsqueda sobre marcas con
    transiciones silenciosas, sin heurísticas de token replay);
  * lenguaje de la red hasta la longitud máxima del lenguaje del árbol (una vuelta por
    bucle) = lenguaje del árbol que reporta la traza.
"""
import collections
import datetime as dt
import json

from .. import datos

TOL = 1e-6


def _registro(ruta, hoja, letras):
    filas = datos.tabla_xlsx(ruta, hoja)
    casos = collections.OrderedDict()
    for f in filas:
        ts = dt.datetime.strptime(str(f["Timestamp"]).strip(), "%d-%m-%Y:%H.%M")
        casos.setdefault(f["Case id"], []).append((ts, f["Event id"], letras[f["Activity"]]))
    return filas, {str(k): "".join(x[2] for x in sorted(v)) for k, v in casos.items()}


def _red(tr):
    r = tr["red"]
    T = {t: [r["l"][t] if r["l"][t] != "τ" else None, [], []] for t in r["T"]}
    for a, b in r["F"]:
        if a in T:
            T[a][2].append(b)
        else:
            T[b][1].append(a)
    return r["P"], T


def _fire(m, ent, sal):
    c = collections.Counter(dict(m))
    for p in ent:
        c[p] -= 1
    for p in sal:
        c[p] += 1
    return frozenset((p, k) for p, k in c.items() if k)


def _ok(m, ent):
    d = dict(m)
    return all(d.get(p, 0) >= n for p, n in collections.Counter(ent).items())


def _alcanzables(T):
    m0 = frozenset({("ini", 1)})
    vistos, cola, arcos = {m0}, collections.deque([m0]), []
    while cola and len(vistos) < 20000:
        m = cola.popleft()
        for t, (_, ent, sal) in T.items():
            if _ok(m, ent):
                m2 = _fire(m, ent, sal)
                arcos.append((m, t, m2))
                if m2 not in vistos:
                    vistos.add(m2)
                    cola.append(m2)
    return vistos, arcos


def _cierre(T, marcas):
    """Marcas alcanzables solo con transiciones silenciosas."""
    res, pila = set(marcas), list(marcas)
    while pila:
        m = pila.pop()
        for t, (et, ent, sal) in T.items():
            if et is None and _ok(m, ent):
                m2 = _fire(m, ent, sal)
                if m2 not in res:
                    res.add(m2)
                    pila.append(m2)
    return res


def _acepta(T, traza):
    actual = _cierre(T, {frozenset({("ini", 1)})})
    for ev in traza:
        sig = set()
        for m in actual:
            for t, (et, ent, sal) in T.items():
                if et == ev and _ok(m, ent):
                    sig.add(_fire(m, ent, sal))
        actual = _cierre(T, sig)
        if not actual:
            return False
    return frozenset({("fin", 1)}) in actual


def _lenguaje(T, maxlen):
    final = frozenset({("fin", 1)})
    res = set()
    frontera = {(m, "") for m in _cierre(T, {frozenset({("ini", 1)})})}
    vistos = set(frontera)
    while frontera:
        nueva = set()
        for m, w in frontera:
            if m == final:
                res.add(w)
            if len(w) >= maxlen:
                continue
            for t, (et, ent, sal) in T.items():
                if et is not None and _ok(m, ent):
                    for m2 in _cierre(T, {_fire(m, ent, sal)}):
                        s = (m2, w + et)
                        if s not in vistos:
                            vistos.add(s)
                            nueva.add(s)
        frontera = nueva
    return res


def verificar(ruta_xlsx, ruta_traza):
    with open(ruta_traza, encoding="utf-8") as fh:
        tr = json.load(fh)
    res = []

    def chk(ok, msg):
        res.append((bool(ok), msg))

    letras = {n: l for l, n in tr["letras"].items()}
    filas, trazas = _registro(ruta_xlsx, tr["registro"], letras)
    chk(len(filas) == tr["eventos"] and len(trazas) == tr["casos"],
        "registro: %d eventos y %d casos" % (len(filas), len(trazas)))
    chk(trazas == tr["trazas"], "trazas por caso (orden por timestamp) iguales")
    var = collections.Counter(trazas.values())
    chk({v["traza"]: v["frecuencia"] for v in tr["variantes"]} == dict(var),
        "%d variantes con sus frecuencias" % len(var))
    dfg = collections.Counter()
    dos = collections.Counter()
    for t in trazas.values():
        for i in range(len(t) - 1):
            dfg[t[i] + ">" + t[i + 1]] += 1
        for i in range(len(t) - 2):
            if t[i] == t[i + 2] and t[i] != t[i + 1]:
                dos[t[i] + ">>" + t[i + 1]] += 1
    chk(dict(dfg) == tr["dfg"], "|x>y|: %d pares iguales" % len(dfg))
    malos = []
    for k, n in dfg.items():
        x, y = k.split(">")
        if x == y:
            continue
        inv = dfg.get(y + ">" + x, 0)
        v = (n - inv) / (n + inv + 1)
        if abs(v - tr["dependencia"].get(x + "=>" + y, 99)) > TOL:
            malos.append(k)
    for k, n in dos.items():
        x, y = k.split(">>")
        inv = dos.get(y + ">>" + x, 0)
        if abs((n + inv) / (n + inv + 1) - tr["dependencia_bucle2"].get(x + "=>2" + y, 99)) > TOL:
            malos.append(k)
    chk(not malos and dict(dos) == tr["bucle2"], "dependencias y bucles de longitud 2" + (": difieren %s" % malos if malos else ""))

    P, T = _red(tr)
    acts = set("".join(trazas.values()))
    chk(acts <= {et for et, _, _ in T.values() if et}, "todas las actividades del registro están en la red")
    marcas, arcos = _alcanzables(T)
    final = frozenset({("fin", 1)})
    cota = max(k for m in marcas for _, k in m)
    inv = collections.defaultdict(set)
    for a, _, b in arcos:
        inv[b].add(a)
    llegan, pila = {final}, [final]
    while pila:
        x = pila.pop()
        for y in inv[x] - llegan:
            llegan.add(y)
            pila.append(y)
    solida = (all(m in llegan for m in marcas) and all(m == final for m in marcas if dict(m).get("fin"))
              and {t for _, t, _ in arcos} == set(T))
    pr = tr["propiedades"]
    chk(len(marcas) == pr["marcas"] and len(arcos) == pr["arcos_alcanzabilidad"],
        "grafo de alcanzabilidad: %d marcas y %d arcos" % (len(marcas), len(arcos)))
    chk((cota <= 1) == pr["segura"], "segura: %s" % (cota <= 1))
    chk(solida == pr["solida"], "sólida: %s" % solida)
    sal = collections.defaultdict(list)
    ent_p = collections.defaultdict(list)
    for t, (_, e, s) in T.items():
        for p in e:
            sal[p].append(t)
        for p in s:
            ent_p[p].append(t)
    wf = [p for p in P if not ent_p[p]] == ["ini"] and [p for p in P if not sal[p]] == ["fin"]
    chk(wf == pr["red_wf"], "red WF: %s" % wf)
    libre = all(T[t][1] == [p] for p in P if len(sal[p]) > 1 for t in sal[p])
    chk(libre == pr["libre_eleccion"], "libre elección: %s" % libre)
    acept = {c: _acepta(T, t) for c, t in trazas.items()}
    todas = all(acept.values())
    chk(todas == (abs(tr["replay"]["fitness"] - 1) < 1e-12),
        "aceptación de las %d trazas por la red: %s; fitness de la traza %.3f" % (
            len(acept), "todas" if todas else [c for c, v in acept.items() if not v], tr["replay"]["fitness"]))
    leng_arbol = set(tr["lenguaje_una_vuelta"])
    maxlen = max(len(w) for w in leng_arbol)
    leng_red = _lenguaje(T, maxlen)
    chk(leng_red == leng_arbol, "lenguaje de la red (longitud <= %d) = lenguaje del árbol: %d trazas" % (maxlen, len(leng_red))
        if leng_red == leng_arbol else "lenguajes distintos: solo red %s; solo árbol %s" % (
            sorted(leng_red - leng_arbol)[:3], sorted(leng_arbol - leng_red)[:3]))
    chk(set(var) <= leng_red or all(acept.values()), "las variantes están en el lenguaje del modelo")
    return res
