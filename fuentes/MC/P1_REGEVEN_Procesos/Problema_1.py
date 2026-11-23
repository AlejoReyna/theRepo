#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROBLEMA 1 (U.T.2) - Modelado y analisis de procesos con REGEVEN.xlsx
=====================================================================
Matricula 1851265 -> ultimo digito 5:
  * se usa la hoja "Registro 05"
  * digito 3, 4 o 5  -> ademas de la red de Petri, diagrama BPMN
  * matricula impar  -> arbol de proceso

Que hace el programa
  1. Lee el registro de eventos (solo biblioteca estandar, sin openpyxl).
  2. Arma las trazas por caso (ordenadas por timestamp) y sus variantes.
  3. Calcula la relacion "directamente seguido por" (DFG), el footprint
     (relaciones del algoritmo alfa) y las medidas de dependencia del
     Heuristics Miner, incluida la de bucles de longitud 2.
  4. Construye la red de Petri descubierta y la VERIFICA:
       - es red WF (lugar fuente unico, lugar sumidero unico, conexa)
       - grafo de alcanzabilidad -> segura (1-acotada) y solida (sound)
       - de libre eleccion (free-choice)
       - reproduccion (replay) de las 10 trazas -> ajuste (fitness)
  5. Construye el arbol de proceso y comprueba que genera todas las trazas.
  6. Exporta los modelos: DOT/SVG/PNG, PNML (WoPeD/ProM) y BPMN 2.0 XML
     (Camunda Modeler / bpmn.io), ademas de reporte_P1.txt.

Uso
    python3 Problema_1.py                      # usa REGEVEN.xlsx junto al script
    python3 Problema_1.py /ruta/REGEVEN.xlsx   # otra ruta
    python3 Problema_1.py --registro 03        # otro registro (para comparar)

Graphviz (dot) y rsvg-convert son opcionales: si estan instalados se
generan tambien las imagenes .svg/.png; si no, quedan los .dot/.svg fuente.
"""

import collections
import datetime as dt
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
from xml.sax.saxutils import escape

AQUI = os.path.dirname(os.path.abspath(__file__))

# ----------------------------------------------------------------------------
# Actividades y su abreviatura (convencion de van der Aalst: una letra)
# ----------------------------------------------------------------------------
ACTIVIDADES = [
    ("a", "solicitud recibida"),
    ("b", "identidad validada"),
    ("c", "documentos verificados"),
    ("d", "corrección solicitada"),
    ("e", "cita programada"),
    ("f", "entrevista realizada"),
    ("g", "orientación brindada"),
    ("h", "expediente integrado"),
    ("i", "autorización emitida"),
    ("j", "cierre registrado"),
]
LETRA = {nombre: letra for letra, nombre in ACTIVIDADES}
NOMBRE = {letra: nombre for letra, nombre in ACTIVIDADES}

SALIDA = []  # lineas del reporte


def out(texto=""):
    print(texto)
    SALIDA.append(texto)


# ----------------------------------------------------------------------------
# 1. Lectura del .xlsx con zipfile + xml (sin librerias externas)
# ----------------------------------------------------------------------------
def leer_hoja_xlsx(ruta, nombre_hoja):
    m = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    r = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    with zipfile.ZipFile(ruta) as z:
        libro = ET.fromstring(z.read("xl/workbook.xml"))
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        destino_por_id = {x.get("Id"): x.get("Target") for x in rels}
        hojas = {h.get("name"): destino_por_id[h.get("{%s}id" % r)]
                 for h in libro.find("{%s}sheets" % m)}
        if nombre_hoja not in hojas:
            raise SystemExit("No existe la hoja %r. Hojas: %s" % (nombre_hoja, list(hojas)))
        destino = hojas[nombre_hoja].lstrip("/")
        if not destino.startswith("xl/"):
            destino = "xl/" + destino
        compartidas = []
        if "xl/sharedStrings.xml" in z.namelist():
            sst = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in sst.findall("{%s}si" % m):
                compartidas.append("".join(t.text or "" for t in si.iter("{%s}t" % m)))
        hoja = ET.fromstring(z.read(destino))
    filas = []
    for fila in hoja.iter("{%s}row" % m):
        valores = {}
        for c in fila.findall("{%s}c" % m):
            col = re.match(r"[A-Z]+", c.get("r")).group()
            tipo, v = c.get("t"), c.find("{%s}v" % m)
            if tipo == "s":
                valores[col] = compartidas[int(v.text)]
            elif tipo == "inlineStr":
                valores[col] = "".join(t.text or "" for t in c.iter("{%s}t" % m))
            else:
                valores[col] = None if v is None else v.text
        filas.append(valores)
    return filas


def cargar_registro(ruta, registro):
    filas = leer_hoja_xlsx(ruta, "Registro %s" % registro)
    encabezado = [filas[0][k] for k in sorted(filas[0])]
    eventos = []
    for f in filas[1:]:
        if not f.get("A"):
            continue
        eventos.append({
            "caso": int(float(f["A"])),
            "evento": int(float(f["B"])),
            "ts": dt.datetime.strptime(f["C"], "%d-%m-%Y:%H.%M"),
            "actividad": f["D"].strip(),
            "recurso": f["E"].strip(),
            "costo": float(f["F"]),
        })
    return encabezado, eventos


# ----------------------------------------------------------------------------
# 2. Red de Petri descubierta (red WF etiquetada)
#    Lugares: ini, p1..p11, fin      Transiciones: 11 visibles + 2 silenciosas
# ----------------------------------------------------------------------------
LUGARES = ["ini", "p1", "p2", "p3", "p4", "p5", "p6", "p7", "p8", "p9", "p10", "p11", "fin"]
SIGNIFICADO_LUGAR = {
    "ini": "caso creado (fuente)",
    "p1": "por validar identidad",
    "p2": "por verificar documentos",
    "p3": "identidad validada",
    "p4": "documentos verificados",
    "p5": "expediente en revision (decide: corregir o citar)",
    "p6": "correccion pendiente de re-verificar",
    "p7": "cita programada, por entrevistar",
    "p8": "entrevista hecha (decide: orientar o no)",
    "p9": "listo para integrar expediente",
    "p10": "expediente integrado, por autorizar",
    "p11": "autorizado, por cerrar",
    "fin": "caso terminado (sumidero)",
}
# transicion -> (etiqueta visible o None si es silenciosa, entradas, salidas)
TRANSICIONES = collections.OrderedDict([
    ("a",  ("a", ["ini"], ["p1", "p2"])),       # AND-split
    ("b",  ("b", ["p1"], ["p3"])),
    ("c",  ("c", ["p2"], ["p4"])),
    ("t1", (None, ["p3", "p4"], ["p5"])),       # AND-join silencioso
    ("d",  ("d", ["p5"], ["p6"])),              # XOR: corregir...
    ("c2", ("c", ["p6"], ["p5"])),              # ...y re-verificar (bucle)
    ("e",  ("e", ["p5"], ["p7"])),              # ...o salir del bucle
    ("f",  ("f", ["p7"], ["p8"])),
    ("g",  ("g", ["p8"], ["p9"])),              # XOR: orientar...
    ("t2", (None, ["p8"], ["p9"])),             # ...o saltar (silenciosa)
    ("h",  ("h", ["p9"], ["p10"])),
    ("i",  ("i", ["p10"], ["p11"])),
    ("j",  ("j", ["p11"], ["fin"])),
])
M0 = (("ini", 1),)
MF = (("fin", 1),)


def marca(dic):
    return tuple(sorted((p, n) for p, n in dic.items() if n))


def habilitada(m, t):
    d = dict(m)
    return all(d.get(p, 0) >= 1 for p in TRANSICIONES[t][1])


def disparar(m, t):
    d = dict(m)
    for p in TRANSICIONES[t][1]:
        d[p] -= 1
    for p in TRANSICIONES[t][2]:
        d[p] = d.get(p, 0) + 1
    return marca(d)


def texto_marca(m):
    return "[" + ", ".join(p if n == 1 else "%s^%d" % (p, n) for p, n in m) + "]"


def arcos():
    F = []
    for t, (_, ent, sal) in TRANSICIONES.items():
        F += [(p, t) for p in ent] + [(t, p) for p in sal]
    return F


def grafo_alcanzabilidad():
    estados, aristas, pila = {M0}, [], [M0]
    while pila:
        m = pila.pop()
        for t in TRANSICIONES:
            if habilitada(m, t):
                m2 = disparar(m, t)
                aristas.append((m, t, m2))
                if m2 not in estados:
                    estados.add(m2)
                    pila.append(m2)
    return estados, aristas


def verificar_red():
    res = {}
    F = arcos()
    pre = {n: set() for n in LUGARES + list(TRANSICIONES)}
    post = {n: set() for n in LUGARES + list(TRANSICIONES)}
    for x, y in F:
        post[x].add(y)
        pre[y].add(x)
    fuentes = [p for p in LUGARES if not pre[p]]
    sumideros = [p for p in LUGARES if not post[p]]
    # red cortocircuitada (fin -> t* -> ini) fuertemente conexa
    ady = collections.defaultdict(set)
    for x, y in F:
        ady[x].add(y)
    ady["fin"].add("t*")
    ady["t*"].add("ini")
    nodos = set(LUGARES) | set(TRANSICIONES) | {"t*"}

    def alcanzables(origen, grafo):
        vis, pila = {origen}, [origen]
        while pila:
            for y in grafo[pila.pop()]:
                if y not in vis:
                    vis.add(y)
                    pila.append(y)
        return vis

    inv = collections.defaultdict(set)
    for x, ys in ady.items():
        for y in ys:
            inv[y].add(x)
    fuerte = alcanzables("ini", ady) == nodos and alcanzables("ini", inv) == nodos
    res["wf"] = (fuentes == ["ini"] and sumideros == ["fin"] and fuerte)
    res["fuentes"], res["sumideros"] = fuentes, sumideros

    # libre eleccion: si dos transiciones comparten un lugar de entrada,
    # tienen exactamente el mismo conjunto de lugares de entrada
    fc = True
    for t1 in TRANSICIONES:
        for t2 in TRANSICIONES:
            e1, e2 = set(TRANSICIONES[t1][1]), set(TRANSICIONES[t2][1])
            if e1 & e2 and e1 != e2:
                fc = False
    res["free_choice"] = fc
    res["maquina_estados"] = all(len(pre[t]) == 1 and len(post[t]) == 1 for t in TRANSICIONES)
    res["grafo_marcado"] = all(len(pre[p]) == 1 and len(post[p]) == 1
                               for p in LUGARES if p not in ("ini", "fin"))
    res["pura"] = all(not (pre[t] & post[t]) for t in TRANSICIONES)

    estados, aristas = grafo_alcanzabilidad()
    res["n_estados"], res["n_aristas"] = len(estados), len(aristas)
    res["cota"] = max(n for m in estados for _, n in m)
    res["segura"] = res["cota"] == 1
    inversa = collections.defaultdict(set)
    for m, _, m2 in aristas:
        inversa[m2].add(m)
    llegan_a_fin, pila = {MF}, [MF]
    while pila:
        for m in inversa[pila.pop()]:
            if m not in llegan_a_fin:
                llegan_a_fin.add(m)
                pila.append(m)
    res["opcion_completar"] = estados <= llegan_a_fin
    res["terminacion_propia"] = all(m == MF for m in estados if dict(m).get("fin"))
    res["sin_muertas"] = {t for _, t, _ in aristas} == set(TRANSICIONES)
    res["solida"] = res["opcion_completar"] and res["terminacion_propia"] and res["sin_muertas"]
    res["estados"], res["aristas"] = estados, aristas
    res["F"] = F
    return res


def reproducir(traza):
    """Busca (BFS) una secuencia de disparos que reproduzca la traza,
    permitiendo transiciones silenciosas. Devuelve la secuencia o None."""
    inicio = (M0, 0, ())
    vistos, cola = {(M0, 0)}, collections.deque([inicio])
    while cola:
        m, k, seq = cola.popleft()
        if k == len(traza) and m == MF:
            return seq
        for t, (etq, _, _) in TRANSICIONES.items():
            if not habilitada(m, t):
                continue
            if etq is None:
                sig = (disparar(m, t), k)
            elif k < len(traza) and etq == traza[k]:
                sig = (disparar(m, t), k + 1)
            else:
                continue
            if sig not in vistos:
                vistos.add(sig)
                cola.append((sig[0], sig[1], seq + (t,)))
    return None


def fitness_tokens(secuencia):
    """Token replay (van der Aalst): p producidas, c consumidas, m faltantes,
    r remanentes. Con una secuencia valida m = r = 0."""
    m, p, c = dict(M0), 1, 0
    faltan = 0
    for t in secuencia:
        for lugar in TRANSICIONES[t][1]:
            if m.get(lugar, 0) < 1:
                faltan += 1
                m[lugar] = m.get(lugar, 0) + 1
            m[lugar] -= 1
            c += 1
        for lugar in TRANSICIONES[t][2]:
            m[lugar] = m.get(lugar, 0) + 1
            p += 1
    if m.get("fin", 0) >= 1:
        m["fin"] -= 1
    else:
        faltan += 1
    c += 1
    rem = sum(v for v in m.values() if v > 0)
    return p, c, faltan, rem


# ----------------------------------------------------------------------------
# 3. Arbol de proceso
#    ->( a, ^(b, c), @(tau, ->(d, c)), e, f, x(g, tau), h, i, j )
# ----------------------------------------------------------------------------
TAU = "tau"
ARBOL = ("->", [
    "a",
    ("^", ["b", "c"]),
    ("@", [TAU, ("->", ["d", "c"])]),
    "e",
    "f",
    ("x", ["g", TAU]),
    "h", "i", "j",
])
SIMBOLO = {"->": "→", "^": "∧", "x": "×", "@": "↺"}


def intercalados(u, v):
    if not u:
        return {v}
    if not v:
        return {u}
    return {(u[0],) + w for w in intercalados(u[1:], v)} | \
           {(v[0],) + w for w in intercalados(u, v[1:])}


def lenguaje(nodo, max_rep=2):
    """Lenguaje del arbol con a lo mas max_rep repeticiones de cada bucle."""
    if isinstance(nodo, str):
        return {()} if nodo == TAU else {(nodo,)}
    op, hijos = nodo
    L = [lenguaje(h, max_rep) for h in hijos]
    if op == "->":
        res = {()}
        for Lh in L:
            res = {x + y for x in res for y in Lh}
        return res
    if op == "x":
        return set().union(*L)
    if op == "^":
        res = {()}
        for Lh in L:
            res = {w for x in res for y in Lh for w in intercalados(x, y)}
        return res
    if op == "@":  # do (redo do)*
        hacer, rehacer = L[0], L[1]
        res = set(hacer)
        actual = set(hacer)
        for _ in range(max_rep):
            actual = {x + y + z for x in actual for y in rehacer for z in hacer}
            res |= actual
        return res
    raise ValueError(op)


def arbol_texto(nodo):
    if isinstance(nodo, str):
        return "τ" if nodo == TAU else nodo
    op, hijos = nodo
    return "%s(%s)" % (SIMBOLO[op], ", ".join(arbol_texto(h) for h in hijos))


# ----------------------------------------------------------------------------
# 4. Exportacion de diagramas
# ----------------------------------------------------------------------------
def etiqueta_multilinea(letra):
    nombre = NOMBRE[letra]
    partes = nombre.split(" ", 1)
    return "%s\\n%s" % (letra, "\\n".join(partes))


def dot_red_petri(compacta=False):
    """compacta=True: transiciones solo con su letra (estilo van der Aalst) para el reporte."""
    L = ['digraph RedPetri {',
         '  rankdir=LR; splines=true; nodesep=0.35; ranksep=0.32; pad=0.2;',
         '  node [fontname="Helvetica", fontsize=10]; edge [arrowsize=0.7];',
         '  labelloc="t"; fontname="Helvetica-Bold"; fontsize=14;',
         '  label="Red de Petri (red WF) - Registro 05";']
    for p in LUGARES:
        tok = "&#9679;" if p == "ini" else ""
        per = ' peripheries=2' if p == "fin" else ''
        L.append('  "%s" [shape=circle, width=0.42, fixedsize=true, label="%s", '
                 'xlabel=<<font point-size="9">%s</font>>%s];' % (p, tok, p, per))
    for t, (etq, _, _) in TRANSICIONES.items():
        if etq is None:
            L.append('  "%s" [shape=box, style=filled, fillcolor=black, width=0.14, height=0.55, '
                     'fixedsize=true, label="", xlabel=<<font point-size="9">&#964;%s</font>>];'
                     % (t, t[1:]))
        else:
            nombre = NOMBRE[etq].replace(" ", "<br/>", 1)
            sub = "'" if t == "c2" else ""
            if compacta:
                L.append('  "%s" [shape=box, width=0.5, height=0.5, fixedsize=true, style="filled", '
                         'fillcolor="#EAF2FB", color="#2F5D8A", fontsize=16, label=<<b>%s%s</b>>];'
                         % (t, etq, sub))
            else:
                L.append('  "%s" [shape=box, style="filled", fillcolor="#EAF2FB", color="#2F5D8A", '
                         'label=<<b>%s%s</b><br/><font point-size="9">%s</font>>];' % (t, etq, sub, nombre))
    for x, y in arcos():
        extra = ""
        if (x, y) in (("p6", "c2"), ("c2", "p5"), ("p5", "d"), ("d", "p6")):
            extra = ' [color="#B04A2F"]'
        L.append('  "%s" -> "%s"%s;' % (x, y, extra))
    if compacta:
        leyenda = " &#183; ".join("%s = %s" % (l, n) for l, n in ACTIVIDADES[:5]) + "<br/>" + \
                  " &#183; ".join("%s = %s" % (l, n) for l, n in ACTIVIDADES[5:]) + \
                  "<br/>c' = documentos verificados (re-verificación) &#183; &#964; = transición silenciosa"
        L[4] = ('  labelloc="b"; label=<<b>Red de Petri (red WF) - Registro 05</b><br/>'
                '<font face="Helvetica" point-size="12">%s</font>>;' % leyenda)
    L.append('  { rank=same; "p1"; "p2"; }')
    L.append('  { rank=same; "b"; "c"; }')
    L.append('  { rank=same; "p3"; "p4"; }')
    L.append('}')
    return "\n".join(L)


def dot_arbol():
    L = ['digraph Arbol {',
         '  rankdir=TB; nodesep=0.25; ranksep=0.45; pad=0.2;',
         '  node [fontname="Helvetica", fontsize=11]; edge [arrowhead=none];',
         '  labelloc="t"; fontname="Helvetica-Bold"; fontsize=14;',
         '  label="Árbol de proceso - Registro 05";']
    cont = [0]

    def nuevo():
        cont[0] += 1
        return "n%d" % cont[0]

    def visitar(nodo):
        nid = nuevo()
        if isinstance(nodo, str):
            if nodo == TAU:
                L.append('  %s [shape=box, style="rounded,filled", fillcolor="#EEEEEE", label=<&#964;>];' % nid)
            else:
                nombre = NOMBRE[nodo].replace(" ", "<br/>", 1)
                L.append('  %s [shape=box, style="rounded,filled", fillcolor="#EAF2FB", color="#2F5D8A", '
                         'label=<<b>%s</b><br/><font point-size="9">%s</font>>];' % (nid, nodo, nombre))
            return nid
        op, hijos = nodo
        L.append('  %s [shape=circle, width=0.5, fixedsize=true, style=filled, fillcolor="#FFF4D6", '
                 'fontsize=18, label="%s"];' % (nid, SIMBOLO[op]))
        for h in hijos:
            L.append('  %s -> %s;' % (nid, visitar(h)))
        return nid

    visitar(ARBOL)
    L.append('}')
    return "\n".join(L)


# --- BPMN: un solo layout alimenta el SVG y el XML BPMN 2.0 con DI -----------
CARRILES = [  # (id, nombre, recursos, alto)
    ("L1", "Recepción", "Nora, Luis, Ana", 120),
    ("L2", "Validación de identidad", "Julia, Raúl", 110),
    ("L3", "Revisión documental y agenda", "Elena, Marco, Pilar", 190),
    ("L4", "Entrevista", "Celia, Óscar", 170),
    ("L5", "Integración y cierre", "Marta, Iván", 110),
    ("L6", "Autorización", "Sofía", 110),
]
X_POOL, Y_POOL, BANDA, BANDA_CARRIL = 10, 10, 34, 48
X_CONT = X_POOL + BANDA + BANDA_CARRIL
DX = 14  # desplazamiento horizontal de todos los nodos
ANCHO_POOL = 1745 + DX


def _y_carriles():
    y, res = Y_POOL, {}
    for cid, _, _, alto in CARRILES:
        res[cid] = (y, alto)
        y += alto
    return res


YC = _y_carriles()
FILA = {  # centros verticales de las filas usadas
    "L1": YC["L1"][0] + 60, "L2": YC["L2"][0] + 55,
    "L3a": YC["L3"][0] + 50, "L3": YC["L3"][0] + 140,
    "L4a": YC["L4"][0] + 48, "L4": YC["L4"][0] + 122,
    "L5": YC["L5"][0] + 55, "L6": YC["L6"][0] + 55,
}
# id -> (tipo, nombre, carril, cx, cy)
NODOS_BPMN = collections.OrderedDict([
    ("Inicio", ("start", "Solicitud entrante", "L1", 115, FILA["L1"])),
    ("T_a", ("task", "Solicitud recibida", "L1", 210, FILA["L1"])),
    ("G_and1", ("and", "", "L2", 310, FILA["L2"])),
    ("T_b", ("task", "Identidad validada", "L2", 410, FILA["L2"])),
    ("T_c", ("task", "Documentos verificados", "L3", 410, FILA["L3"])),
    ("G_and2", ("and", "", "L3", 510, FILA["L3"])),
    ("G_xm1", ("xor", "", "L3", 590, FILA["L3"])),
    ("G_xs1", ("xor", "¿Documentación correcta?", "L3", 690, FILA["L3"])),
    ("T_d", ("task", "Corrección solicitada", "L1", 690, FILA["L1"])),
    ("T_c2", ("task", "Documentos verificados (re-verificación)", "L3", 590, FILA["L3a"])),
    ("T_e", ("task", "Cita programada", "L3", 820, FILA["L3"])),
    ("T_f", ("task", "Entrevista realizada", "L4", 950, FILA["L4"])),
    ("G_xs2", ("xor", "¿Requiere orientación?", "L4", 1065, FILA["L4"])),
    ("T_g", ("task", "Orientación brindada", "L4", 1165, FILA["L4a"])),
    ("G_xm2", ("xor", "", "L4", 1265, FILA["L4"])),
    ("T_h", ("task", "Expediente integrado", "L5", 1370, FILA["L5"])),
    ("T_i", ("task", "Autorización emitida", "L6", 1500, FILA["L6"])),
    ("T_j", ("task", "Cierre registrado", "L5", 1630, FILA["L5"])),
    ("Fin", ("end", "Trámite concluido", "L5", 1725, FILA["L5"])),
])
NODOS_BPMN = collections.OrderedDict((k, (t, n, c, cx + DX, cy)) for k, (t, n, c, cx, cy) in NODOS_BPMN.items())
TAM = {"task": (126, 66), "start": (36, 36), "end": (36, 36), "and": (50, 50), "xor": (50, 50)}


def _borde(nid, lado):
    tipo, _, _, cx, cy = NODOS_BPMN[nid]
    w, h = TAM[tipo]
    return {"izq": (cx - w / 2, cy), "der": (cx + w / 2, cy),
            "arr": (cx, cy - h / 2), "aba": (cx, cy + h / 2)}[lado]


def _flujo(fid, src, ls, dst, ld, medio=(), etiqueta=""):
    return (fid, src, dst, [_borde(src, ls)] + list(medio) + [_borde(dst, ld)], etiqueta)


def flujos_bpmn():
    N = NODOS_BPMN
    return [
        _flujo("F1", "Inicio", "der", "T_a", "izq"),
        _flujo("F2", "T_a", "der", "G_and1", "arr", [(N["G_and1"][3], N["T_a"][4])]),
        _flujo("F3", "G_and1", "der", "T_b", "izq"),
        _flujo("F4", "G_and1", "aba", "T_c", "izq", [(N["G_and1"][3], N["T_c"][4])]),
        _flujo("F5", "T_b", "der", "G_and2", "arr", [(N["G_and2"][3], N["T_b"][4])]),
        _flujo("F6", "T_c", "der", "G_and2", "izq"),
        _flujo("F7", "G_and2", "der", "G_xm1", "izq"),
        _flujo("F8", "G_xm1", "der", "G_xs1", "izq"),
        _flujo("F9", "G_xs1", "der", "T_e", "izq", etiqueta="Sí"),
        _flujo("F10", "G_xs1", "arr", "T_d", "aba", etiqueta="No"),
        _flujo("F11", "T_d", "izq", "T_c2", "arr",
               [(N["T_c2"][3], N["T_d"][4])]),
        _flujo("F12", "T_c2", "aba", "G_xm1", "arr"),
        _flujo("F13", "T_e", "der", "T_f", "arr", [(N["T_f"][3], N["T_e"][4])]),
        _flujo("F14", "T_f", "der", "G_xs2", "izq"),
        _flujo("F15", "G_xs2", "arr", "T_g", "izq", [(N["G_xs2"][3], N["T_g"][4])], etiqueta="Sí"),
        _flujo("F16", "G_xs2", "der", "G_xm2", "izq", etiqueta="No"),
        _flujo("F17", "T_g", "der", "G_xm2", "arr", [(N["G_xm2"][3], N["T_g"][4])]),
        _flujo("F18", "G_xm2", "der", "T_h", "arr", [(N["T_h"][3], N["G_xm2"][4])]),
        _flujo("F19", "T_h", "der", "T_i", "arr", [(N["T_i"][3], N["T_h"][4])]),
        _flujo("F20", "T_i", "der", "T_j", "aba", [(N["T_j"][3], N["T_i"][4])]),
        _flujo("F21", "T_j", "der", "Fin", "izq"),
    ]


def _envolver(texto, maximo=16):
    palabras, lineas, actual = texto.split(), [], ""
    for p in palabras:
        if actual and len(actual) + 1 + len(p) > maximo:
            lineas.append(actual)
            actual = p
        else:
            actual = (actual + " " + p).strip()
    lineas.append(actual)
    return lineas


def svg_bpmn():
    alto_pool = sum(c[3] for c in CARRILES)
    W, H = X_POOL + ANCHO_POOL + 10, Y_POOL + alto_pool + 40
    S = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" '
         'font-family="Helvetica, Arial, sans-serif">' % (W, H, W, H),
         '<defs><marker id="flecha" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="9" '
         'markerHeight="9" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#222"/>'
         '</marker></defs>',
         '<rect x="0" y="0" width="%d" height="%d" fill="#FFFFFF"/>' % (W, H)]
    # pool + carriles
    S.append('<rect x="%d" y="%d" width="%d" height="%d" fill="none" stroke="#222" stroke-width="1.5"/>'
             % (X_POOL, Y_POOL, ANCHO_POOL, alto_pool))
    S.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#222" stroke-width="1.5"/>'
             % (X_POOL + BANDA, Y_POOL, X_POOL + BANDA, Y_POOL + alto_pool))
    cxp, cyp = X_POOL + BANDA / 2, Y_POOL + alto_pool / 2
    S.append('<text x="%.1f" y="%.1f" font-size="15" font-weight="bold" text-anchor="middle" '
             'transform="rotate(-90 %.1f %.1f)">Trámite de autorización (Registro 05)</text>'
             % (cxp, cyp + 5, cxp, cyp))
    colores = ["#F7FAFD", "#FFFFFF"]
    for k, (cid, nombre, recursos, alto) in enumerate(CARRILES):
        y, _ = YC[cid]
        S.append('<rect x="%d" y="%d" width="%d" height="%d" fill="%s" stroke="#222" stroke-width="1"/>'
                 % (X_POOL + BANDA, y, ANCHO_POOL - BANDA, alto, colores[k % 2]))
        S.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#222"/>'
                 % (X_CONT, y, X_CONT, y + alto))
        cx, cy = X_POOL + BANDA + BANDA_CARRIL / 2, y + alto / 2
        lineas = _envolver(nombre, int(alto / 8))
        x0 = cx - len(lineas) * 6.5 + 4
        for k, ln in enumerate(lineas):
            S.append('<text x="%.1f" y="%.1f" font-size="11.5" font-weight="bold" text-anchor="middle" '
                     'transform="rotate(-90 %.1f %.1f)">%s</text>' % (x0 + 13 * k, cy, x0 + 13 * k, cy, escape(ln)))
        xr = x0 + 13 * len(lineas) - 1
        S.append('<text x="%.1f" y="%.1f" font-size="9.5" fill="#555" text-anchor="middle" '
                 'transform="rotate(-90 %.1f %.1f)">(%s)</text>' % (xr, cy, xr, cy, escape(recursos)))
    # flujos
    for fid, src, dst, pts, etq in flujos_bpmn():
        d = " ".join("%s%.1f,%.1f" % ("M" if k == 0 else "L", x, y) for k, (x, y) in enumerate(pts))
        S.append('<path d="%s" fill="none" stroke="#222" stroke-width="1.4" marker-end="url(#flecha)"/>' % d)
        if etq:
            x0, y0 = pts[0]
            x1, y1 = pts[1]
            if abs(y1 - y0) > abs(x1 - x0):   # sale vertical
                tx, ty, anc = x0 + 6, y0 - 12 if y1 < y0 else y0 + 16, "start"
            else:
                tx, ty, anc = x0 + 8, y0 - 6, "start"
            S.append('<text x="%.1f" y="%.1f" font-size="13" font-style="italic" font-weight="bold" text-anchor="%s">%s</text>'
                     % (tx, ty, anc, etq))
    # nodos
    for nid, (tipo, nombre, _, cx, cy) in NODOS_BPMN.items():
        w, h = TAM[tipo]
        if tipo == "task":
            S.append('<rect x="%.1f" y="%.1f" width="%d" height="%d" rx="10" ry="10" fill="#EAF2FB" '
                     'stroke="#2F5D8A" stroke-width="1.6"/>' % (cx - w / 2, cy - h / 2, w, h))
            lineas = _envolver(nombre, 14)
            y0 = cy - (len(lineas) - 1) * 8 + 5
            for k, ln in enumerate(lineas):
                S.append('<text x="%.1f" y="%.1f" font-size="14" text-anchor="middle">%s</text>'
                         % (cx, y0 + 16 * k, escape(ln)))
        elif tipo in ("start", "end"):
            ancho = 1.8 if tipo == "start" else 4
            S.append('<circle cx="%.1f" cy="%.1f" r="18" fill="#FFFFFF" stroke="#222" stroke-width="%s"/>'
                     % (cx, cy, ancho))
            for k, ln in enumerate(_envolver(nombre, 10)):
                S.append('<text x="%.1f" y="%.1f" font-size="12" text-anchor="middle">%s</text>'
                         % (cx, cy + 34 + 14 * k, escape(ln)))
        else:
            S.append('<path d="M%.1f,%.1f L%.1f,%.1f L%.1f,%.1f L%.1f,%.1f z" fill="#FFF4D6" '
                     'stroke="#8A6D1F" stroke-width="1.6"/>'
                     % (cx, cy - 25, cx + 25, cy, cx, cy + 25, cx - 25, cy))
            if tipo == "and":
                S.append('<path d="M%.1f,%.1f L%.1f,%.1f M%.1f,%.1f L%.1f,%.1f" stroke="#222" stroke-width="3"/>'
                         % (cx - 10, cy, cx + 10, cy, cx, cy - 10, cx, cy + 10))
            else:
                S.append('<path d="M%.1f,%.1f L%.1f,%.1f M%.1f,%.1f L%.1f,%.1f" stroke="#222" stroke-width="3"/>'
                         % (cx - 8, cy - 8, cx + 8, cy + 8, cx + 8, cy - 8, cx - 8, cy + 8))
            if nombre:
                lineas = _envolver(nombre, 14)
                for k, ln in enumerate(lineas):
                    S.append('<text x="%.1f" y="%.1f" font-size="12.5" text-anchor="middle">%s</text>'
                             % (cx + 2, cy + 42 + 15 * k, escape(ln)))
    S.append('<text x="%d" y="%d" font-size="10" fill="#555">Carriles = roles inferidos del atributo '
             'Resource del registro (minería organizacional). Compuertas: + paralela (AND), '
             'X exclusiva (XOR).</text>' % (X_POOL, Y_POOL + alto_pool + 24))
    S.append('</svg>')
    return "\n".join(S)


def xml_bpmn():
    """BPMN 2.0 con Diagram Interchange: se abre y edita en Camunda Modeler o demo.bpmn.io."""
    alto_pool = sum(c[3] for c in CARRILES)
    flujos = flujos_bpmn()
    entrantes = collections.defaultdict(list)
    salientes = collections.defaultdict(list)
    for fid, s, d, _, _ in flujos:
        salientes[s].append(fid)
        entrantes[d].append(fid)
    etiqueta_xml = {"task": "task", "start": "startEvent", "end": "endEvent",
                    "and": "parallelGateway", "xor": "exclusiveGateway"}
    X = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
         'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" '
         'xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" '
         'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" '
         'id="Definiciones_R05" targetNamespace="http://fime.uanl.mx/tsci3/p1">',
         '  <bpmn:collaboration id="Colaboracion">',
         '    <bpmn:participant id="Pool" name="Trámite de autorización (Registro 05)" processRef="Proceso_R05"/>',
         '  </bpmn:collaboration>',
         '  <bpmn:process id="Proceso_R05" isExecutable="false">',
         '    <bpmn:laneSet id="Carriles">']
    for cid, nombre, recursos, _ in CARRILES:
        X.append('      <bpmn:lane id="%s" name="%s (%s)">' % (cid, escape(nombre), escape(recursos)))
        for nid, (_, _, carril, _, _) in NODOS_BPMN.items():
            if carril == cid:
                X.append('        <bpmn:flowNodeRef>%s</bpmn:flowNodeRef>' % nid)
        X.append('      </bpmn:lane>')
    X.append('    </bpmn:laneSet>')
    for nid, (tipo, nombre, _, _, _) in NODOS_BPMN.items():
        tag = etiqueta_xml[tipo]
        X.append('    <bpmn:%s id="%s" name="%s">' % (tag, nid, escape(nombre)))
        for f in entrantes[nid]:
            X.append('      <bpmn:incoming>%s</bpmn:incoming>' % f)
        for f in salientes[nid]:
            X.append('      <bpmn:outgoing>%s</bpmn:outgoing>' % f)
        X.append('    </bpmn:%s>' % tag)
    for fid, s, d, _, etq in flujos:
        X.append('    <bpmn:sequenceFlow id="%s" name="%s" sourceRef="%s" targetRef="%s"/>'
                 % (fid, escape(etq), s, d))
    X.append('  </bpmn:process>')
    X.append('  <bpmndi:BPMNDiagram id="Diagrama"><bpmndi:BPMNPlane id="Plano" bpmnElement="Colaboracion">')
    X.append('    <bpmndi:BPMNShape id="Pool_di" bpmnElement="Pool" isHorizontal="true">'
             '<dc:Bounds x="%d" y="%d" width="%d" height="%d"/></bpmndi:BPMNShape>'
             % (X_POOL, Y_POOL, ANCHO_POOL, alto_pool))
    for cid, _, _, alto in CARRILES:
        y, _ = YC[cid]
        X.append('    <bpmndi:BPMNShape id="%s_di" bpmnElement="%s" isHorizontal="true">'
                 '<dc:Bounds x="%d" y="%d" width="%d" height="%d"/></bpmndi:BPMNShape>'
                 % (cid, cid, X_POOL + BANDA, y, ANCHO_POOL - BANDA, alto))
    for nid, (tipo, _, _, cx, cy) in NODOS_BPMN.items():
        w, h = TAM[tipo]
        marcador = ' isMarkerVisible="true"' if tipo == "xor" else ""
        X.append('    <bpmndi:BPMNShape id="%s_di" bpmnElement="%s"%s>'
                 '<dc:Bounds x="%.0f" y="%.0f" width="%d" height="%d"/></bpmndi:BPMNShape>'
                 % (nid, nid, marcador, cx - w / 2, cy - h / 2, w, h))
    for fid, _, _, pts, _ in flujos:
        X.append('    <bpmndi:BPMNEdge id="%s_di" bpmnElement="%s">' % (fid, fid))
        for x, y in pts:
            X.append('      <di:waypoint x="%.0f" y="%.0f"/>' % (x, y))
        X.append('    </bpmndi:BPMNEdge>')
    X.append('  </bpmndi:BPMNPlane></bpmndi:BPMNDiagram>')
    X.append('</bpmn:definitions>')
    return "\n".join(X)


def pnml():
    """PNML (formato estandar ISO/IEC 15909-2) para abrir la red en WoPeD / ProM."""
    P = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<pnml><net id="RedWF_R05" type="http://www.pnml.org/version-2009/grammar/ptnet">',
         '<name><text>Red WF - Registro 05</text></name><page id="pagina">']
    for k, p in enumerate(LUGARES):
        ini = '<initialMarking><text>1</text></initialMarking>' if p == "ini" else ""
        P.append('<place id="%s"><name><text>%s</text></name>'
                 '<graphics><position x="%d" y="200"/></graphics>%s</place>' % (p, p, 40 + 80 * k, ini))
    for k, (t, (etq, _, _)) in enumerate(TRANSICIONES.items()):
        nombre = "tau%s" % t[1:] if etq is None else "%s: %s" % (etq, NOMBRE[etq])
        P.append('<transition id="%s"><name><text>%s</text></name>'
                 '<graphics><position x="%d" y="100"/></graphics></transition>'
                 % (t, escape(nombre), 80 + 80 * k))
    for k, (x, y) in enumerate(arcos()):
        P.append('<arc id="arc%d" source="%s" target="%s"/>' % (k + 1, x, y))
    P.append('</page><finalmarkings><marking><place idref="fin"><text>1</text></place>'
             '</marking></finalmarkings></net></pnml>')
    return "\n".join(P)


def renderizar(base):
    """base.dot -> base.svg/base.png  o  base.svg -> base.png"""
    hecho = []
    if os.path.exists(base + ".dot") and shutil.which("dot"):
        subprocess.run(["dot", "-Tsvg", base + ".dot", "-o", base + ".svg"], check=True)
        subprocess.run(["dot", "-Tpng", "-Gdpi=170", base + ".dot", "-o", base + ".png"], check=True)
        hecho = [".svg", ".png"]
    elif os.path.exists(base + ".svg") and shutil.which("rsvg-convert"):
        subprocess.run(["rsvg-convert", "-z", "1.6", "-b", "white", base + ".svg", "-o", base + ".png"],
                       check=True)
        hecho = [".png"]
    return hecho


# ----------------------------------------------------------------------------
# 5. Programa principal
# ----------------------------------------------------------------------------
def main():
    args = sys.argv[1:]
    registro = "05"
    if "--registro" in args:
        k = args.index("--registro")
        registro = args[k + 1].zfill(2)
        del args[k:k + 2]
    ruta = args[0] if args else os.path.join(AQUI, "REGEVEN.xlsx")
    if not os.path.exists(ruta):
        raise SystemExit("No encuentro %s. Uso: python3 Problema_1.py /ruta/REGEVEN.xlsx" % ruta)

    encabezado, eventos = cargar_registro(ruta, registro)
    out("=" * 78)
    out("PROBLEMA 1 - REGEVEN, hoja 'Registro %s'  (matricula 1851265 -> digito 5)" % registro)
    out("=" * 78)
    out("Atributos del registro: %s" % ", ".join(encabezado))
    casos = collections.OrderedDict()
    for ev in sorted(eventos, key=lambda e: (e["caso"], e["ts"], e["evento"])):
        casos.setdefault(ev["caso"], []).append(ev)
    out("Eventos: %d   Casos: %d   Actividades distintas: %d   Recursos distintos: %d"
        % (len(eventos), len(casos), len({e['actividad'] for e in eventos}),
           len({e['recurso'] for e in eventos})))

    desconocidas = {e["actividad"] for e in eventos} - set(LETRA)
    if desconocidas:
        raise SystemExit("Actividades no mapeadas: %s" % desconocidas)

    out("\nCodificacion de actividades:")
    for letra, nombre in ACTIVIDADES:
        n = sum(1 for e in eventos if e["actividad"] == nombre)
        out("  %s = %-24s (%2d eventos)" % (letra, nombre, n))

    trazas = collections.OrderedDict((c, tuple(LETRA[e["actividad"]] for e in evs))
                                     for c, evs in casos.items())
    out("\n--- 1. TRAZAS POR CASO ---")
    for c, t in trazas.items():
        out("  caso %2d: <%s>" % (c, ",".join(t)))

    variantes = collections.Counter(trazas.values())
    out("\n--- 2. VARIANTES (registro simplificado L) ---")
    partes = []
    for v, n in variantes.most_common():
        partes.append("<%s>^%d" % (",".join(v), n))
        casos_v = [str(c) for c, t in trazas.items() if t == v]
        out("  %d x <%s>   casos %s" % (n, ",".join(v), ", ".join(casos_v)))
    out("  L = [ " + ", ".join(partes) + " ]")

    # DFG
    dfg = collections.Counter()
    for t in trazas.values():
        for x, y in zip(t, t[1:]):
            dfg[(x, y)] += 1
    inicios = collections.Counter(t[0] for t in trazas.values())
    finales = collections.Counter(t[-1] for t in trazas.values())
    letras = [l for l, _ in ACTIVIDADES]
    out("\n--- 3. MATRIZ 'DIRECTAMENTE SEGUIDO POR' |x > y| ---")
    out("       " + " ".join("%3s" % y for y in letras))
    for x in letras:
        out("   %s  " % x + " ".join("%3s" % (dfg[(x, y)] or ".") for y in letras))
    out("  Actividades de inicio: %s   de fin: %s" % (dict(inicios), dict(finales)))

    # Footprint
    out("\n--- 4. FOOTPRINT (relaciones del algoritmo alfa) ---")
    out("       " + " ".join("%3s" % y for y in letras))
    for x in letras:
        fila = []
        for y in letras:
            xy, yx = dfg[(x, y)] > 0, dfg[(y, x)] > 0
            fila.append("->" if xy and not yx else "<-" if yx and not xy else "||" if xy and yx else "#")
        out("   %s  " % x + " ".join("%3s" % s for s in fila))
    out("  Nota: c>d y d>c aparecen como 'c||d', pero en realidad es un bucle de longitud 2")
    out("  (patron c,d,c). El alfa clasico no lo detecta; por eso se usan las medidas")
    out("  del Heuristics Miner (y alfa+), que si distinguen el bucle.")

    # Heuristics miner
    ddos = collections.Counter()
    for t in trazas.values():
        for x, y, z in zip(t, t[1:], t[2:]):
            if x == z and x != y:
                ddos[(x, y)] += 1
    out("\n--- 5. HEURISTICS MINER: dependencias a=>b = (|a>b|-|b>a|)/(|a>b|+|b>a|+1) ---")
    for (x, y), n in sorted(dfg.items()):
        dep = (dfg[(x, y)] - dfg[(y, x)]) / (dfg[(x, y)] + dfg[(y, x)] + 1)
        out("  %s => %s : |%s>%s|=%d |%s>%s|=%d  dep=%+.3f" % (x, y, x, y, n, y, x, dfg[(y, x)], dep))
    for (x, y), n in sorted(ddos.items()):
        dep2 = (ddos[(x, y)] + ddos[(y, x)]) / (ddos[(x, y)] + ddos[(y, x)] + 1)
        out("  bucle long. 2: %s=>2%s  |%s>>%s|=%d  dep2=%.3f  -> bucle c-d-c" % (x, y, x, y, n, dep2))
    out("  Lectura (umbral de dependencia 0.5):")
    out("   * |b=>c| = 0.364 < 0.5: b y c ocurren en ambos ordenes sin dependencia causal;")
    out("     ambas dependen de a y preceden a e -> paralelismo AND(b, c).")
    out("   * c=>d y d=>c son bajas (0.286), pero la medida de bucle de longitud 2 (0.667)")
    out("     supera el umbral -> bucle de retrabajo c-d-c. Ademas d solo ocurre cuando b y c")
    out("     ya terminaron -> el bucle va DESPUES de la sincronizacion AND.")
    out("   * f=>g 0.750, g=>h 0.750 y f=>h 0.875 -> g es opcional: XOR(g, tau).")

    # Red de Petri
    out("\n--- 6. RED DE PETRI DESCUBIERTA  N = (P, T, F, A, l),  M0=[ini], Mf=[fin] ---")
    out("  P = {%s}  |P| = %d" % (", ".join(LUGARES), len(LUGARES)))
    out("  T = {%s}  |T| = %d  (11 visibles + 2 silenciosas)"
        % (", ".join(TRANSICIONES), len(TRANSICIONES)))
    F = arcos()
    out("  |F| = %d arcos:" % len(F))
    out("    " + ", ".join("(%s,%s)" % a for a in F))
    out("  l: " + ", ".join("%s->%s" % (t, e if e else "τ")
                            for t, (e, _, _) in TRANSICIONES.items()))
    out("  Significado de los lugares:")
    for p in LUGARES:
        out("    %-4s %s" % (p, SIGNIFICADO_LUGAR[p]))

    v = verificar_red()
    out("\n--- 7. DENOMINACION / PROPIEDADES DE LA RED ---")
    si = lambda b: "SI" if b else "NO"
    out("  Red WF (workflow net): %s  (fuente %s, sumidero %s, conexa al cortocircuitar)"
        % (si(v["wf"]), v["fuentes"], v["sumideros"]))
    out("  Grafo de alcanzabilidad: %d marcas, %d arcos" % (v["n_estados"], v["n_aristas"]))
    out("  Cota maxima de fichas por lugar: %d -> segura (1-acotada): %s" % (v["cota"], si(v["segura"])))
    out("  Solidez (soundness): opcion de completar=%s, terminacion propia=%s, sin transiciones muertas=%s"
        % (si(v["opcion_completar"]), si(v["terminacion_propia"]), si(v["sin_muertas"])))
    out("    -> red WF SOLIDA: %s" % si(v["solida"]))
    out("  Libre eleccion (free-choice): %s" % si(v["free_choice"]))
    out("  Maquina de estados: %s   Grafo marcado: %s   Pura (sin auto-bucles): %s"
        % (si(v["maquina_estados"]), si(v["grafo_marcado"]), si(v["pura"])))
    out("  DENOMINACION: red de Petri etiquetada tipo RED WF (flujo de trabajo), solida,")
    out("  segura y de libre eleccion; no es maquina de estados ni grafo marcado porque")
    out("  combina concurrencia (AND b||c) con eleccion (XOR corregir/citar, orientar/no).")
    out("  Marcas alcanzables:")
    for m in sorted(v["estados"], key=lambda m: (len(m), m)):
        out("    " + texto_marca(m))

    out("\n--- 8. REPRODUCCION (REPLAY) DE LAS TRAZAS EN LA RED ---")
    tot = [0, 0, 0, 0]
    ajustan = 0
    for c, t in trazas.items():
        seq = reproducir(t)
        if seq is None:
            out("  caso %2d: NO reproducible" % c)
            continue
        ajustan += 1
        p, cc, m, r = fitness_tokens(seq)
        tot = [tot[0] + p, tot[1] + cc, tot[2] + m, tot[3] + r]
        out("  caso %2d: disparos %-38s p=%d c=%d m=%d r=%d"
            % (c, " ".join("τ" if TRANSICIONES[x][0] is None else x for x in seq), p, cc, m, r))
    p, cc, m, r = tot
    fit = 0.5 * (1 - m / cc) + 0.5 * (1 - r / p)
    out("  Totales: p=%d c=%d m=%d r=%d  ->  fitness = 1/2(1-m/c)+1/2(1-r/p) = %.3f" % (p, cc, m, r, fit))
    out("  Trazas que ajustan: %d/%d" % (ajustan, len(trazas)))

    out("\n--- 9. ARBOL DE PROCESO ---")
    out("  " + arbol_texto(ARBOL))
    out("  Operadores: → secuencia, ∧ paralelo, × eleccion exclusiva, "
        "↺ bucle (hacer, rehacer), τ silenciosa")
    Lt = lenguaje(ARBOL, max_rep=1)
    out("  Lenguaje con a lo mas 1 correccion: %d trazas" % len(Lt))
    for w in sorted(Lt, key=lambda w: (len(w), w)):
        marca_log = "  <- en el registro (%dx)" % variantes[w] if w in variantes else ""
        out("    <%s>%s" % (",".join(w), marca_log))
    todas = all(t in lenguaje(ARBOL, 2) for t in variantes)
    out("  Todas las variantes del registro pertenecen al lenguaje del arbol: %s" % si(todas))
    out("  Precision: el registro cubre %d de las %d trazas posibles con <=1 correccion."
        % (len(set(variantes) & Lt), len(Lt)))

    out("\n--- 10. DESEMPENO Y RECURSOS (perspectivas de tiempo, costo y organizacion) ---")
    dur, costos = [], []
    for c, evs in casos.items():
        h = (evs[-1]["ts"] - evs[0]["ts"]).total_seconds() / 3600
        dur.append(h)
        costos.append(sum(e["costo"] for e in evs))
        out("  caso %2d: %6.1f h (%4.1f dias)  costo %4.0f" % (c, h, h / 24, costos[-1]))
    out("  Duracion promedio: %.1f h (%.2f dias); costo promedio por caso: %.1f"
        % (sum(dur) / len(dur), sum(dur) / len(dur) / 24, sum(costos) / len(costos)))
    out("  Recursos por actividad:")
    for letra, nombre in ACTIVIDADES:
        rec = collections.Counter(e["recurso"] for e in eventos if e["actividad"] == nombre)
        out("    %s %-24s %s" % (letra, nombre, dict(rec)))

    # exportaciones
    archivos = {
        "red_petri.dot": dot_red_petri(),
        "red_petri_compacta.dot": dot_red_petri(compacta=True),
        "arbol_proceso.dot": dot_arbol(),
        "bpmn.svg": svg_bpmn(),
        "Problema_1.bpmn": xml_bpmn(),
        "Problema_1.pnml": pnml(),
    }
    for nombre, contenido in archivos.items():
        with open(os.path.join(AQUI, nombre), "w", encoding="utf-8") as fh:
            fh.write(contenido + "\n")
    generados = list(archivos)
    for base in ("red_petri", "red_petri_compacta", "arbol_proceso", "bpmn"):
        generados += [base + ext for ext in renderizar(os.path.join(AQUI, base))]
    out("\nArchivos generados en %s:" % AQUI)
    out("  " + ", ".join(sorted(set(generados))))
    with open(os.path.join(AQUI, "reporte_P1.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(SALIDA) + "\n")


if __name__ == "__main__":
    main()
