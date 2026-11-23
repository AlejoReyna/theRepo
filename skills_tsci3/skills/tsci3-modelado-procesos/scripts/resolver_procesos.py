#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MODELADO DE PROCESOS A PARTIR DE UN REGISTRO DE EVENTOS (REGEVEN)
=================================================================
Pasos (estructura de la respuesta aceptada del medio curso, RESP p.2-6):
  1. Lee la hoja del registro (Case id, Event id, Timestamp, Activity, Resource, Cost)
     y codifica cada actividad con una letra, en el orden en que aparece en la hoja.
  2. Ordena los eventos de cada caso por su timestamp ("dd-mm-aaaa:hh.mm") -> trazas,
     variantes y registro simplificado L.
  3. Relacion "directamente seguido por" |x>y|, footprint del algoritmo alfa,
     dependencias del Heuristics Miner (|x>y|-|y>x|)/(|x>y|+|y>x|+1) con umbral 0.5 y
     medida de bucles de longitud 2 (|x>>y|+|y>>x|)/(|x>>y|+|y>>x|+1).
  4. Deriva el arbol de proceso con reglas de bloques, cada una con su evidencia:
       - la repeticion de una actividad ya ejecutada se etiqueta aparte (x') ;
       - corte XOR: componentes desconectadas del grafo DFG;
       - corte de secuencia: grupos ordenados por alcanzabilidad;
       - bloques que solo ocurren en parte de los casos -> x(tau, bloque);
       - corte paralelo: actividades que se siguen en ambos sentidos (dependencia < 0.5);
       - un bloque opcional que termina repitiendo una actividad -> bucle de retrabajo
         loop(tau, ->(..., x)).
     Si ninguna regla explica un sublog, el programa se detiene: no inventa.
  5. Traduce el arbol a una red WF etiquetada N = (P, T, F, A, l) con M0 = [ini], Mf = [fin].
  6. Verifica: red WF, segura, solida, libre eleccion, maquina de estados, grafo marcado
     (grafo de alcanzabilidad) y ajuste por token replay 1/2(1-m/c) + 1/2(1-r/p).
  7. Comprueba que el lenguaje del arbol contiene todas las variantes.
  8. Escribe traza.json, red.dot, arbol.dot y red.pnml.

Uso   python3 codigo/resolver.py --registro 05            (hoja "Registro 05")
      python3 codigo/resolver.py --registro 05 --datos otra/ruta/REGEVEN.xlsx
Solo usa la biblioteca estandar de Python 3.
"""
import argparse
import collections
import datetime as dt
import json
import os
import re
import string
import sys
import xml.etree.ElementTree as ET
import zipfile
from xml.sax.saxutils import escape

AQUI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(AQUI)
UMBRAL = 0.5
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"


class SinRegla(Exception):
    """Ningun corte explica el sublog: se detiene en lugar de inventar."""


# ---------------------------------------------------------------------------
# 1. Lectura del registro (.xlsx con zipfile + xml)
# ---------------------------------------------------------------------------
def leer_hoja(ruta, nombre):
    with zipfile.ZipFile(ruta) as z:
        comp = []
        if "xl/sharedStrings.xml" in z.namelist():
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS):
                comp.append("".join(t.text or "" for t in si.iter("{%s}t" % NS["m"])))
        libro = ET.fromstring(z.read("xl/workbook.xml"))
        rels = {r.get("Id"): r.get("Target") for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
        hojas = {h.get("name"): h.get(REL) for h in libro.find("m:sheets", NS)}
        if nombre not in hojas:
            raise SystemExit("No existe la hoja %r. Hojas: %s" % (nombre, sorted(hojas)))
        destino = rels[hojas[nombre]].lstrip("/")
        destino = destino if destino.startswith("xl/") else "xl/" + destino
        raiz = ET.fromstring(z.read(destino))
    filas = collections.defaultdict(dict)
    for c in raiz.iter("{%s}c" % NS["m"]):
        ref = c.get("r")
        col = re.match(r"[A-Z]+", ref).group(0)
        fila = int(ref[len(col):])
        v = c.find("m:v", NS)
        if c.get("t") == "inlineStr":
            val = "".join(x.text or "" for x in c.iter("{%s}t" % NS["m"]))
        elif v is None:
            val = None
        elif c.get("t") == "s":
            val = comp[int(v.text)]
        elif c.get("t") == "str":
            val = v.text
        else:
            x = float(v.text)
            val = int(x) if x.is_integer() else x
        filas[fila][col] = val
    orden = sorted(filas)
    enc = filas[orden[0]]
    cols = sorted(enc, key=lambda c: (len(c), c))
    nombres = [str(enc[c]).strip() for c in cols]
    return [dict(zip(nombres, [filas[f].get(c) for c in cols])) for f in orden[1:] if filas[f]]


def leer_registro(ruta, hoja):
    eventos = leer_hoja(ruta, hoja)
    letras, nombres = collections.OrderedDict(), {}
    for e in eventos:                                   # letra por orden de aparicion en la hoja
        if e["Activity"] not in letras:
            letras[e["Activity"]] = string.ascii_lowercase[len(letras)]
    for act, l in letras.items():
        nombres[l] = act
    casos = collections.OrderedDict()
    for e in eventos:
        ts = dt.datetime.strptime(str(e["Timestamp"]).strip(), "%d-%m-%Y:%H.%M")    # T17
        casos.setdefault(e["Case id"], []).append((ts, e["Event id"], letras[e["Activity"]], e))
    trazas = collections.OrderedDict()
    for caso, evs in casos.items():
        evs.sort(key=lambda x: (x[0], x[1]))
        trazas[caso] = tuple(x[2] for x in evs)
    return eventos, letras, nombres, casos, trazas


# ---------------------------------------------------------------------------
# 3. DFG, footprint, dependencias
# ---------------------------------------------------------------------------
def relaciones(trazas, letras_orden):
    dfg = collections.Counter()
    dos = collections.Counter()
    for t in trazas:
        for x, y in zip(t, t[1:]):
            dfg[(x, y)] += 1
        for x, y, z in zip(t, t[1:], t[2:]):
            if x == z and x != y:
                dos[(x, y)] += 1
    inicio = collections.Counter(t[0] for t in trazas)
    fin = collections.Counter(t[-1] for t in trazas)
    foot = {}
    for x in letras_orden:
        for y in letras_orden:
            xy, yx = dfg[(x, y)] > 0, dfg[(y, x)] > 0
            foot[(x, y)] = "->" if xy and not yx else "<-" if yx and not xy else "||" if xy and yx else "#"
    dep = {}
    for (x, y), n in dfg.items():
        if x != y:
            dep[(x, y)] = (n - dfg[(y, x)]) / (n + dfg[(y, x)] + 1)
    dep2 = {}
    for (x, y), n in dos.items():
        dep2[(x, y)] = (n + dos[(y, x)]) / (n + dos[(y, x)] + 1)
    return dfg, dos, inicio, fin, foot, dep, dep2


# ---------------------------------------------------------------------------
# 4. Descubrimiento del arbol de proceso por bloques (con evidencia)
# ---------------------------------------------------------------------------
# Nodos: ("act", x) | ("tau",) | ("seq", [..]) | ("xor", [..]) | ("and", [..]) | ("loop", hacer, rehacer)
def primar(t):
    """Segunda ejecucion de una actividad -> etiqueta x' (re-ejecucion)."""
    vistos, salida = collections.Counter(), []
    for x in t:
        salida.append(x + "'" * vistos[x])
        vistos[x] += 1
    return tuple(salida)


def _dfg(log):
    g = collections.defaultdict(set)
    for t in log:
        for x, y in zip(t, t[1:]):
            g[x].add(y)
    return g


def _alcanza(g, acts):
    alc = {}
    for a in acts:
        vis, pila = set(), [a]
        while pila:
            x = pila.pop()
            for y in g[x]:
                if y not in vis:
                    vis.add(y)
                    pila.append(y)
        alc[a] = vis
    return alc


def _componentes(nodos, vecinos):
    comp, visto = [], set()
    for n in nodos:
        if n in visto:
            continue
        c, pila = set(), [n]
        while pila:
            x = pila.pop()
            if x in c:
                continue
            c.add(x)
            pila.extend(vecinos(x) - c)
        visto |= c
        comp.append(c)
    return comp


def _proyectar(log, grupo):
    return [tuple(x for x in t if x in grupo) for t in log]


def descubrir(log, evid, nivel=0):
    acts = set(x for t in log for x in t)
    n = len(log)
    vacias = sum(1 for t in log if not t)
    if not acts:
        return ("tau",)
    if vacias:
        resto = [t for t in log if t]
        evid.append("Bloque {%s}: %d de %d casos no lo ejecutan -> opcional x(tau, bloque)." % (
            ", ".join(sorted(acts)), vacias, n))
        return ("xor", [("tau",), descubrir(resto, evid, nivel + 1)])
    if len(acts) == 1:
        a = next(iter(acts))
        if all(t == (a,) for t in log):
            return ("act", a)
        raise SinRegla("la actividad %s se repite dentro de un caso sin otra actividad" % a)
    g = _dfg(log)
    orden = sorted(acts, key=lambda a: (min(t.index(a) for t in log if a in t), a))
    # corte XOR: componentes del grafo no dirigido
    und = collections.defaultdict(set)
    for x in acts:
        for y in g[x]:
            und[x].add(y)
            und[y].add(x)
    comps = _componentes(orden, lambda x: und[x])
    if len(comps) > 1:
        evid.append("Corte XOR: {%s} no tienen relacion directa entre si -> eleccion exclusiva." % "} {".join(
            ", ".join(sorted(c)) for c in comps))
        return ("xor", [descubrir([t for t in log if t and t[0] in c], evid, nivel + 1) for c in comps])
    # corte de secuencia (alcanzabilidad)
    alc = _alcanza(g, acts)
    grupos = []
    for a in orden:
        for gr in grupos:
            b = next(iter(gr))
            mutuo = (b in alc[a]) == (a in alc[b])           # mutuamente alcanzables o no alcanzables
            if mutuo:
                gr.add(a)
                break
        else:
            grupos.append({a})
    # fusionar grupos que no quedaron ordenados de forma consistente
    if len(grupos) > 1:
        # orden topologico: un grupo va antes de los que alcanza (alcanza a mas actividades)
        grupos.sort(key=lambda gr: (-len(set().union(*(alc[a] for a in gr)) - gr), min(orden.index(a) for a in gr)))
        ok = all(all(y in alc[x] or x == y for x in grupos[i] for y in grupos[j]) and
                 not any(x in alc[y] for x in grupos[i] for y in grupos[j])
                 for i in range(len(grupos)) for j in range(i + 1, len(grupos)))
        if ok:
            # bloques consecutivos opcionales que ocurren en los mismos casos -> un solo bloque
            presencia = [frozenset(i for i, t in enumerate(log) if any(x in gr for x in t)) for gr in grupos]
            fusion, pres = [], []
            for gr, p in zip(grupos, presencia):
                if fusion and p == pres[-1] and len(p) < n:
                    fusion[-1] = fusion[-1] | gr
                    evid.append("Las actividades {%s} ocurren exactamente en los mismos %d casos -> un bloque en secuencia." % (
                        ", ".join(sorted(fusion[-1])), len(p)))
                else:
                    fusion.append(set(gr))
                    pres.append(p)
            if len(fusion) > 1:
                evid.append("Corte de secuencia: %s." % " -> ".join("{%s}" % ", ".join(
                    sorted(gr, key=orden.index)) for gr in fusion))
                return ("seq", [descubrir(_proyectar(log, gr), evid, nivel + 1) for gr in fusion])
    # corte paralelo: x||y si se siguen en ambos sentidos
    noparal = collections.defaultdict(set)
    for x in acts:
        for y in acts:
            if x != y and not (y in g[x] and x in g[y]):
                noparal[x].add(y)
    partes = _componentes(orden, lambda x: noparal[x])
    if len(partes) > 1:
        ini = {t[0] for t in log}
        fin = {t[-1] for t in log}
        if all(p & ini and p & fin for p in partes):
            evid.append("Corte paralelo: %s se ejecutan en cualquier orden (cada una sigue a la otra) -> AND." % " y ".join(
                "{%s}" % ", ".join(sorted(p)) for p in partes))
            return ("and", [descubrir(_proyectar(log, p), evid, nivel + 1) for p in partes])
    raise SinRegla("ningun corte explica el sublog con actividades {%s}" % ", ".join(sorted(acts)))


def aplanar(nodo):
    if nodo[0] in ("seq", "xor", "and"):
        hijos = []
        for h in nodo[1]:
            h = aplanar(h)
            if h[0] == nodo[0] and nodo[0] != "xor":
                hijos.extend(h[1])
            else:
                hijos.append(h)
        return (nodo[0], hijos)
    if nodo[0] == "loop":
        return ("loop", aplanar(nodo[1]), aplanar(nodo[2]))
    return nodo


def retrabajo(nodo, evid, dep2):
    """x(tau, ->(..., x')) -> loop(tau, ->(..., x)): bloque opcional que repite una actividad."""
    if nodo[0] == "xor" and len(nodo[1]) == 2 and nodo[1][0] == ("tau",):
        cuerpo = nodo[1][1]
        hojas = cuerpo[1] if cuerpo[0] == "seq" else [cuerpo]
        if hojas and hojas[-1][0] == "act" and hojas[-1][1].endswith("'"):
            base = hojas[-1][1].rstrip("'")
            nuevo = [("act", h[1].rstrip("'")) if h[0] == "act" else h for h in hojas]
            antes = [h[1] for h in hojas[:-1] if h[0] == "act"]
            med = ["dep2(%s,%s) = %.3f" % (base, y, v) for (x, y), v in sorted(dep2.items()) if x == base and y in antes]
            evid.append("Retrabajo: el bloque opcional ->(%s) termina repitiendo %s (ya ejecutada) -> bucle loop(tau, ->(%s)) "
                        "despues de lo anterior%s." % (", ".join(h[1] for h in hojas), base,
                                                       ", ".join(h[1] for h in nuevo),
                                                       "; " + ", ".join(med) + " >= %.1f" % UMBRAL if med else ""))
            return ("loop", ("tau",), ("seq", nuevo) if len(nuevo) > 1 else nuevo[0])
    if nodo[0] in ("seq", "xor", "and"):
        return (nodo[0], [retrabajo(h, evid, dep2) for h in nodo[1]])
    if nodo[0] == "loop":
        return ("loop", retrabajo(nodo[1], evid, dep2), retrabajo(nodo[2], evid, dep2))
    return nodo


def arbol_txt(nodo):
    s = {"seq": "->", "xor": "x", "and": "∧"}
    if nodo[0] == "act":
        return nodo[1]
    if nodo[0] == "tau":
        return "τ"
    if nodo[0] == "loop":
        return "⟲(%s, %s)" % (arbol_txt(nodo[1]), arbol_txt(nodo[2]))
    return "%s(%s)" % (s[nodo[0]], ", ".join(arbol_txt(h) for h in nodo[1]))


def a_json(nodo):
    if nodo[0] == "act":
        return {"tipo": "act", "etiqueta": nodo[1]}
    if nodo[0] == "tau":
        return {"tipo": "tau"}
    if nodo[0] == "loop":
        return {"tipo": "loop", "hijos": [a_json(nodo[1]), a_json(nodo[2])]}
    return {"tipo": nodo[0], "hijos": [a_json(h) for h in nodo[1]]}


def lenguaje(nodo, rep=1):
    """Trazas del arbol con a lo mas `rep` vueltas por bucle."""
    if nodo[0] == "act":
        return {(nodo[1],)}
    if nodo[0] == "tau":
        return {()}
    if nodo[0] == "seq":
        res = {()}
        for h in nodo[1]:
            res = {a + b for a in res for b in lenguaje(h, rep)}
        return res
    if nodo[0] == "xor":
        return set().union(*(lenguaje(h, rep) for h in nodo[1]))
    if nodo[0] == "and":
        res = {()}
        for h in nodo[1]:
            res = {m for a in res for b in lenguaje(h, rep) for m in _intercalar(a, b)}
        return res
    hacer, rehacer = lenguaje(nodo[1], rep), lenguaje(nodo[2], rep)
    res, actual = set(hacer), set(hacer)
    for _ in range(rep):
        actual = {a + r + h for a in actual for r in rehacer for h in hacer}
        res |= actual
    return res


def _intercalar(u, v):
    if not u:
        return {v}
    if not v:
        return {u}
    return {(u[0],) + w for w in _intercalar(u[1:], v)} | {(v[0],) + w for w in _intercalar(u, v[1:])}


# ---------------------------------------------------------------------------
# 5. Arbol -> red WF etiquetada
# ---------------------------------------------------------------------------
class Red:
    def __init__(self):
        self.lugares, self.trans = [], collections.OrderedDict()   # t -> [etiqueta|None, entradas, salidas]
        self._n = {"p": 0, "tau": 0}

    def lugar(self, nombre=None):
        if nombre is None:
            self._n["p"] += 1
            nombre = "p%d" % self._n["p"]
        self.lugares.append(nombre)
        return nombre

    def transicion(self, etiqueta, entradas, salidas):
        if etiqueta is None:
            self._n["tau"] += 1
            t = "τ%d" % self._n["tau"]
        else:
            t = etiqueta
            k = 1
            while t in self.trans:
                k += 1
                t = etiqueta + "′" * (k - 1)
        self.trans[t] = [etiqueta, list(entradas), list(salidas)]
        return t


def traducir(nodo, red, entrada, salida=None):
    """Conecta el nodo entre el lugar `entrada` y un lugar de salida (lo crea si no se da)."""
    tipo = nodo[0]
    if tipo in ("act", "tau"):
        salida = salida or red.lugar()
        red.transicion(nodo[1] if tipo == "act" else None, [entrada], [salida])
        return salida
    if tipo == "seq":
        actual = entrada
        for i, h in enumerate(nodo[1]):
            ultimo = i == len(nodo[1]) - 1
            actual = traducir(h, red, actual, salida if ultimo else None)
        return actual
    if tipo == "xor":
        salida = salida or red.lugar()
        for h in nodo[1]:
            traducir(h, red, entrada, salida)
        return salida
    if tipo == "and":
        ent = [red.lugar() for _ in nodo[1]]
        red.transicion(None, [entrada], ent)                         # division (se fusiona si se puede)
        sal = [traducir(h, red, e) for h, e in zip(nodo[1], ent)]
        salida = salida or red.lugar()
        red.transicion(None, sal, [salida])                          # sincronizacion
        return salida
    if tipo == "loop":
        hacer, rehacer = nodo[1], nodo[2]
        if hacer == ("tau",):                                        # loop(tau, X): el lugar decide
            _traducir_ciclo(rehacer, red, entrada)
            return entrada if salida is None else _puente(red, entrada, salida)
        m = traducir(hacer, red, entrada)
        traducir(rehacer, red, m, entrada)
        return m if salida is None else _puente(red, m, salida)
    raise ValueError(tipo)


def _traducir_ciclo(nodo, red, lugar):
    return traducir(nodo, red, lugar, lugar)


def _puente(red, a, b):
    red.transicion(None, [a], [b])
    return b


def reducir(red):
    """Fusiona una division AND silenciosa con la transicion visible que la precede
    cuando ese lugar intermedio no tiene otro uso (como la transicion a de la respuesta)."""
    cambio = True
    while cambio:
        cambio = False
        for t, (et, ent, sal) in list(red.trans.items()):
            if et is not None or len(ent) != 1 or len(sal) < 2:
                continue
            p = ent[0]
            prod = [u for u, (_, e2, s2) in red.trans.items() if p in s2]
            cons = [u for u, (_, e2, s2) in red.trans.items() if p in e2]
            if len(prod) == 1 and cons == [t] and red.trans[prod[0]][0] is not None and len(red.trans[prod[0]][2]) == 1:
                red.trans[prod[0]][2] = list(sal)
                del red.trans[t]
                red.lugares.remove(p)
                cambio = True
                break
    # renumerar lugares p1..pn y silenciosas tau1..taun en orden de aparicion
    orden = [x for x in red.lugares if x not in ("ini", "fin")]
    ren = {p: "p%d" % (i + 1) for i, p in enumerate(orden)}
    ren.update({"ini": "ini", "fin": "fin"})
    red.lugares = ["ini"] + [ren[p] for p in orden] + ["fin"]
    nuevas, k = collections.OrderedDict(), 0
    for t, (et, ent, sal) in red.trans.items():
        if et is None:
            k += 1
            t = "τ%d" % k
        nuevas[t] = [et, [ren[x] for x in ent], [ren[x] for x in sal]]
    red.trans = nuevas


# ---------------------------------------------------------------------------
# 6. Verificacion de la red
# ---------------------------------------------------------------------------
def disparar(m, ent, sal):
    m = collections.Counter(dict(m))
    for p in ent:
        m[p] -= 1
    for p in sal:
        m[p] += 1
    return tuple(sorted((p, k) for p, k in m.items() if k))


def habilitada(m, ent):
    d = dict(m)
    need = collections.Counter(ent)
    return all(d.get(p, 0) >= k for p, k in need.items())


def alcanzabilidad(red, limite=10000):
    m0 = (("ini", 1),)
    marcas, arcos, pila, cota = {m0}, [], [m0], 1
    while pila:
        m = pila.pop()
        for t, (et, ent, sal) in red.trans.items():
            if habilitada(m, ent):
                m2 = disparar(m, ent, sal)
                arcos.append((m, t, m2))
                cota = max([cota] + [k for _, k in m2])
                if m2 not in marcas:
                    marcas.add(m2)
                    pila.append(m2)
                    if len(marcas) > limite:
                        return marcas, arcos, cota, False
    return marcas, arcos, cota, True


def propiedades(red):
    P, T = red.lugares, red.trans
    entradas_p = collections.defaultdict(list)
    salidas_p = collections.defaultdict(list)
    for t, (et, ent, sal) in T.items():
        for p in ent:
            salidas_p[p].append(t)
        for p in sal:
            entradas_p[p].append(t)
    fuentes = [p for p in P if not entradas_p[p]]
    sumideros = [p for p in P if not salidas_p[p]]
    # conexidad fuerte con t* de fin a ini
    g = collections.defaultdict(set)
    for t, (et, ent, sal) in T.items():
        for p in ent:
            g[p].add(t)
        for p in sal:
            g[t].add(p)
    g["fin"].add("t*")
    g["t*"].add("ini")
    nodos = set(P) | set(T) | {"t*"}
    alc = _alcanza(g, nodos)
    fuerte = all(alc[x] >= nodos - {x} or alc[x] >= nodos for x in nodos)
    marcas, arcos, cota, completo = alcanzabilidad(red)
    final = (("fin", 1),)
    inversa = collections.defaultdict(set)
    for a, t, b in arcos:
        inversa[b].add(a)
    llegan = {final}
    pila = [final]
    while pila:
        x = pila.pop()
        for y in inversa[x]:
            if y not in llegan:
                llegan.add(y)
                pila.append(y)
    opcion = all(m in llegan for m in marcas)
    propia = all(m == final for m in marcas if dict(m).get("fin", 0) > 0)
    disparadas = {t for _, t, _ in arcos}
    muertas = [t for t in T if t not in disparadas]
    libre = all(len(T[t][1]) == 1 for p in P for t in salidas_p[p] if len(salidas_p[p]) > 1)
    maquina = all(len(ent) == 1 and len(sal) == 1 for _, ent, sal in T.values())
    marcado = all(len(entradas_p[p]) == 1 and len(salidas_p[p]) == 1 for p in P if p not in ("ini", "fin"))
    return collections.OrderedDict([
        ("red_wf", fuentes == ["ini"] and sumideros == ["fin"] and fuerte),
        ("fuentes", fuentes), ("sumideros", sumideros), ("fuertemente_conexa_con_t*", fuerte),
        ("marcas", len(marcas)), ("arcos_alcanzabilidad", len(arcos)), ("exploracion_completa", completo),
        ("segura", cota <= 1), ("cota", cota),
        ("opcion_de_completar", opcion), ("terminacion_propia", propia), ("transiciones_muertas", muertas),
        ("solida", opcion and propia and not muertas and completo),
        ("libre_eleccion", libre), ("maquina_de_estados", maquina), ("grafo_marcado", marcado),
        ("lugares_con_eleccion", [p for p in P if len(salidas_p[p]) > 1]),
        ("transiciones_con_division", [t for t, (_, ent, sal) in T.items() if len(sal) > 1]),
        ("transiciones_con_sincronizacion", [t for t, (_, ent, sal) in T.items() if len(ent) > 1]),
    ]), sorted(marcas)


def replay(red, traza, max_silencio=8):
    """Token replay con transiciones silenciosas (busqueda corta para habilitar la siguiente)."""
    m = collections.Counter({"ini": 1})
    p, c, falt = 1, 0, 0
    def silencioso_hasta(m, objetivo):
        inicio = tuple(sorted(m.items()))
        cola = collections.deque([(inicio, [])])
        vistos = {inicio}
        while cola:
            marca, camino = cola.popleft()
            md = collections.Counter(dict(marca))
            if objetivo(md):
                return camino
            if len(camino) >= max_silencio:
                continue
            for t, (et, ent, sal) in red.trans.items():
                if et is None and all(md[x] >= 1 for x in ent):
                    m2 = collections.Counter(md)
                    for x in ent:
                        m2[x] -= 1
                    for x in sal:
                        m2[x] += 1
                    clave = tuple(sorted((k, v) for k, v in m2.items() if v))
                    if clave not in vistos:
                        vistos.add(clave)
                        cola.append((clave, camino + [t]))
        return None
    def fuego(t):
        nonlocal p, c, falt
        et, ent, sal = red.trans[t]
        for x in ent:
            if m[x] < 1:
                falt += 1
                m[x] += 1
            m[x] -= 1
            c += 1
        for x in sal:
            m[x] += 1
            p += 1
    for ev in traza:
        candidatas = [t for t, (et, _, _) in red.trans.items() if et == ev]
        lista = [t for t in candidatas if all(m[x] >= 1 for x in red.trans[t][1])]
        if not lista:
            camino = silencioso_hasta(m, lambda md: any(all(md[x] >= 1 for x in red.trans[t][1]) for t in candidatas))
            if camino is not None:
                for s in camino:
                    fuego(s)
                lista = [t for t in candidatas if all(m[x] >= 1 for x in red.trans[t][1])]
        fuego(lista[0] if lista else candidatas[0])
    camino = silencioso_hasta(m, lambda md: md["fin"] >= 1)
    for s in camino or []:
        fuego(s)
    if m["fin"] < 1:
        falt += 1
        m["fin"] += 1
    m["fin"] -= 1
    c += 1
    rest = sum(v for v in m.values() if v > 0)
    return p, c, falt, rest


# ---------------------------------------------------------------------------
# 8. Exportacion
# ---------------------------------------------------------------------------
def dot_red(red, nombres):
    L = ['digraph red {', '  rankdir=LR; nodesep=0.35; ranksep=0.45;', '  node [fontname="Helvetica"];']
    for p in red.lugares:
        tok = " ●" if p == "ini" else ""
        L.append('  "%s" [shape=circle, width=0.45, fixedsize=true, label="%s", xlabel="%s"];' % (
            p, tok.strip(), p))
    for t, (et, ent, sal) in red.trans.items():
        if et is None:
            L.append('  "%s" [shape=box, style=filled, fillcolor=black, width=0.12, height=0.5, fixedsize=true, label="", xlabel="%s"];' % (t, t))
        else:
            L.append('  "%s" [shape=box, label=<<b>%s</b><br/><font point-size="9">%s</font>>];' % (
                t, t, escape(nombres.get(et, et))))
        for p in ent:
            L.append('  "%s" -> "%s";' % (p, t))
        for p in sal:
            L.append('  "%s" -> "%s";' % (t, p))
    L.append("}")
    return "\n".join(L) + "\n"


def dot_arbol(nodo, nombres):
    L = ['digraph arbol {', '  node [fontname="Helvetica"];']
    cont = [0]
    sim = {"seq": "→", "xor": "×", "and": "∧", "loop": "⟲"}
    def visita(n):
        cont[0] += 1
        nid = "n%d" % cont[0]
        if n[0] == "act":
            L.append('  %s [shape=box, label=<<b>%s</b><br/><font point-size="9">%s</font>>];' % (
                nid, n[1], escape(nombres.get(n[1], n[1]))))
        elif n[0] == "tau":
            L.append('  %s [shape=box, style=filled, fillcolor=black, fontcolor=white, label="τ"];' % nid)
        else:
            L.append('  %s [shape=circle, label="%s"];' % (nid, sim[n[0]]))
            hijos = n[1] if n[0] != "loop" else [n[1], n[2]]
            for h in hijos:
                L.append("  %s -> %s;" % (nid, visita(h)))
        return nid
    visita(nodo)
    L.append("}")
    return "\n".join(L) + "\n"


def pnml(red, nombres):
    L = ['<?xml version="1.0" encoding="UTF-8"?>', '<pnml>',
         '  <net id="red" type="http://www.pnml.org/version-2009/grammar/ptnet">', '    <page id="p">']
    for p in red.lugares:
        L.append('      <place id="%s"><name><text>%s</text></name>%s</place>' % (
            p, p, '<initialMarking><text>1</text></initialMarking>' if p == "ini" else ""))
    for t, (et, ent, sal) in red.trans.items():
        texto = nombres.get(et, et) if et else t
        L.append('      <transition id="%s"><name><text>%s</text></name>%s</transition>' % (
            escape(t), escape(texto), "" if et else '<toolspecific tool="ProM" version="6.4" activity="$invisible$"/>'))
        for p in ent:
            L.append('      <arc id="%s-%s" source="%s" target="%s"/>' % (escape(p), escape(t), escape(p), escape(t)))
        for p in sal:
            L.append('      <arc id="%s-%s" source="%s" target="%s"/>' % (escape(t), escape(p), escape(t), escape(p)))
    L += ['    </page>', '    <finalmarkings><marking><place idref="fin"><text>1</text></place></marking></finalmarkings>',
          '  </net>', '</pnml>']
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--registro", required=True, help='numero de registro, p. ej. 05 -> hoja "Registro 05"')
    ap.add_argument("--datos", default=os.path.join(BASE, "datos", "REGEVEN.xlsx"))
    ap.add_argument("--salida", default=BASE)
    a = ap.parse_args()
    hoja = "Registro %s" % a.registro
    eventos, letras, nombres, casos, trazas = leer_registro(a.datos, hoja)
    orden = list(letras.values())
    lista = list(trazas.values())
    variantes = collections.Counter(lista)
    var_orden = sorted(variantes, key=lambda v: (-variantes[v], min(i for i, t in enumerate(lista) if t == v)))
    dfg, dos, ini, fin, foot, dep, dep2 = relaciones(lista, orden)
    evid = []
    try:
        arbol = descubrir([primar(t) for t in lista], evid)
    except SinRegla as e:
        raise SystemExit("DETENIDO: %s. Las reglas de bloques no explican este registro; "
                         "hay que decidir el modelo a mano con la evidencia de los pasos 3." % e)
    arbol = retrabajo(aplanar(arbol), evid, dep2)
    arbol = aplanar(arbol)
    leng1 = lenguaje(arbol, 1)
    contiene = all(v in lenguaje(arbol, max(1, max(v.count(x) for x in set(v)))) for v in variantes)
    red = Red()
    red.lugares.append("ini")
    traducir(arbol, red, "ini", "fin")
    red.lugares.append("fin")
    reducir(red)
    props, marcas = propiedades(red)
    tot = [0, 0, 0, 0]
    rep_casos = collections.OrderedDict()
    for caso, t in trazas.items():
        r = replay(red, t)
        rep_casos[str(caso)] = r
        tot = [x + y for x, y in zip(tot, r)]
    p, c, mm, rr = tot
    fitness = 0.5 * (1 - mm / c) + 0.5 * (1 - rr / p)
    arcos_F = sum(len(e) + len(s) for _, e, s in red.trans.values())
    denom = []
    if props["red_wf"]:
        denom.append("red WF (flujo de trabajo)")
    if props["solida"]:
        denom.append("sólida")
    if props["segura"]:
        denom.append("segura (1-acotada)")
    if props["libre_eleccion"]:
        denom.append("de libre elección")
    denom = "Red de Petri etiquetada: " + ", ".join(denom) + "; %s máquina de estados y %s grafo marcado." % (
        "es" if props["maquina_de_estados"] else "no es", "es" if props["grafo_marcado"] else "no es")
    # recursos, tiempo y costo
    recursos = collections.defaultdict(collections.Counter)
    for e in eventos:
        recursos[letras[e["Activity"]]][e["Resource"]] += 1
    costos = collections.defaultdict(set)
    for e in eventos:
        costos[letras[e["Activity"]]].add(e["Cost"])
    dur = {str(k): (max(x[0] for x in v) - min(x[0] for x in v)).total_seconds() / 86400 for k, v in casos.items()}
    costo_caso = {str(k): sum(x[3]["Cost"] for x in v) for k, v in casos.items()}
    traza = collections.OrderedDict([
        ("registro", hoja), ("archivo", os.path.basename(a.datos)),
        ("eventos", len(eventos)), ("casos", len(trazas)), ("actividades", len(letras)),
        ("recursos", len({e["Resource"] for e in eventos})),
        ("letras", collections.OrderedDict((l, n) for n, l in letras.items())),
        ("trazas", collections.OrderedDict((str(k), "".join(v)) for k, v in trazas.items())),
        ("variantes", [collections.OrderedDict([("traza", "".join(v)), ("frecuencia", variantes[v]),
                                                ("casos", [str(k) for k, t in trazas.items() if t == v])]) for v in var_orden]),
        ("dfg", collections.OrderedDict(("%s>%s" % k, n) for k, n in sorted(dfg.items()))),
        ("inicio", dict(ini)), ("fin", dict(fin)),
        ("footprint", collections.OrderedDict(("%s,%s" % k, v) for k, v in sorted(foot.items()))),
        ("dependencia", collections.OrderedDict(("%s=>%s" % k, round(v, 6)) for k, v in sorted(dep.items()))),
        ("bucle2", collections.OrderedDict(("%s>>%s" % k, n) for k, n in sorted(dos.items()))),
        ("dependencia_bucle2", collections.OrderedDict(("%s=>2%s" % k, round(v, 6)) for k, v in sorted(dep2.items()))),
        ("evidencia", evid),
        ("arbol", arbol_txt(arbol)),
        ("arbol_json", a_json(arbol)),
        ("lenguaje_una_vuelta", sorted("".join(t) for t in leng1)),
        ("variantes_en_el_lenguaje", contiene),
        ("red", collections.OrderedDict([
            ("P", red.lugares), ("T", list(red.trans)),
            ("F", [[p, t] for t, (_, e, s) in red.trans.items() for p in e] + [[t, p] for t, (_, e, s) in red.trans.items() for p in s]),
            ("l", collections.OrderedDict((t, et if et else "τ") for t, (et, _, _) in red.trans.items())),
            ("visibles", sum(1 for et, _, _ in red.trans.values() if et)),
            ("silenciosas", sum(1 for et, _, _ in red.trans.values() if et is None)),
            ("arcos", arcos_F)])),
        ("propiedades", props),
        ("marcas", ["[" + ", ".join(p if k == 1 else "%s^%d" % (p, k) for p, k in m) + "]" for m in marcas]),
        ("replay", collections.OrderedDict([("por_caso", rep_casos), ("p", p), ("c", c), ("m", mm), ("r", rr),
                                            ("fitness", fitness)])),
        ("denominacion", denom),
        ("recursos_por_actividad", collections.OrderedDict((l, dict(recursos[l])) for l in orden)),
        ("costo_por_actividad", collections.OrderedDict((l, sorted(costos[l])) for l in orden)),
        ("duracion_dias", dur), ("costo_por_caso", costo_caso),
    ])
    # pantalla
    print("MODELADO DE PROCESOS — %s de %s" % (hoja, os.path.basename(a.datos)))
    print("Eventos: %d   Casos: %d   Actividades: %d   Recursos: %d" % (
        len(eventos), len(trazas), len(letras), traza["recursos"]))
    for n, l in letras.items():
        print("  %s = %s" % (l, n))
    print("\nVariantes:")
    for v in traza["variantes"]:
        print("  %d x <%s>  casos %s" % (v["frecuencia"], ",".join(v["traza"]), ", ".join(v["casos"])))
    print("\nDirectamente seguido por |x>y|:")
    print("     " + " ".join("%3s" % y for y in orden))
    for x in orden:
        print("  %s  " % x + " ".join("%3s" % (dfg[(x, y)] or ".") for y in orden))
    print("\nDependencias (umbral %.1f):" % UMBRAL)
    for (x, y), v in sorted(dep.items()):
        print("  %s => %s  %+.3f" % (x, y, v))
    for (x, y), v in sorted(dep2.items()):
        print("  bucle de longitud 2: %s =>2 %s  |%s>>%s| = %d  dep2 = %.3f" % (x, y, x, y, dos[(x, y)], v))
    print("\nEvidencia -> modelo:")
    for e in evid:
        print("  * " + e)
    print("\nArbol de proceso: %s" % traza["arbol"])
    print("Con a lo mas una vuelta por bucle genera %d trazas; contiene las %d variantes: %s" % (
        len(leng1), len(variantes), "SI" if contiene else "NO"))
    print("\nRed: |P| = %d, |T| = %d (%d visibles, %d silenciosas), |F| = %d" % (
        len(red.lugares), len(red.trans), traza["red"]["visibles"], traza["red"]["silenciosas"], arcos_F))
    for t, (et, e, s) in red.trans.items():
        print("  %-4s l=%s  %s -> %s" % (t, et or "τ", "{" + ", ".join(e) + "}", "{" + ", ".join(s) + "}"))
    print("\nGrafo de alcanzabilidad: %d marcas, %d arcos" % (props["marcas"], props["arcos_alcanzabilidad"]))
    for k in ("red_wf", "segura", "solida", "libre_eleccion", "maquina_de_estados", "grafo_marcado"):
        print("  %-20s %s" % (k, "SI" if props[k] else "NO"))
    print("Replay: p=%d c=%d m=%d r=%d -> fitness = 1/2(1-m/c)+1/2(1-r/p) = %.3f" % (p, c, mm, rr, fitness))
    print("\nDenominacion: " + denom)
    os.makedirs(a.salida, exist_ok=True)
    with open(os.path.join(a.salida, "traza.json"), "w", encoding="utf-8") as fh:
        json.dump(traza, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    for nombre, texto in (("red.dot", dot_red(red, nombres)), ("arbol.dot", dot_arbol(arbol, nombres)),
                          ("red.pnml", pnml(red, nombres))):
        with open(os.path.join(a.salida, nombre), "w", encoding="utf-8") as fh:
            fh.write(texto)
    print("\nEscritos: traza.json, red.dot, arbol.dot, red.pnml en %s" % a.salida)


if __name__ == "__main__":
    main()
