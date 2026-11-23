#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DIAGRAMA BPMN 2.0 A PARTIR DEL ARBOL DE PROCESO DE traza.json
=============================================================
Traduccion del arbol (como el BPMN aceptado del medio curso, RESP p.5-6):
  ->(..)      secuencia de flujos
  ∧(..)       compuerta paralela (+) de division y compuerta paralela de union
  x(τ, X)     compuerta exclusiva (X) «¿Requiere ...?»: Si -> X; No -> se omite; fusion
  ⟲(τ, X)     compuerta exclusiva de fusion + compuerta «¿Requiere ...?»: Si -> X, que
              regresa a la fusion (retrabajo, dibujado hacia atras); No -> continua
  actividad   tarea; si es una repeticion de una actividad ya hecha, lleva «(repetición)»
Carriles: dos actividades van en el mismo carril si comparten algun recurso (matriz
actividad x recurso del registro). Cada carril lleva los nombres de sus recursos.
Salidas: bpmn.bpmn (BPMN 2.0 con diagrama: Camunda Modeler o demo.bpmn.io) y bpmn.svg.

Uso   python3 bpmn_procesos.py CARPETA        (lee CARPETA/traza.json)
Solo biblioteca estandar.
"""
import collections
import json
import os
import sys
from xml.sax.saxutils import escape

TAREA = (136, 66)
COMP = 48
EVENTO = 38
COLX = 168
FILA = 112
BANDA = 70           # banda con el nombre del carril
TITULO = 34          # banda con el titulo del proceso


def carriles(traza):
    rec = traza["recursos_por_actividad"]
    acts = list(rec)
    padre = {a: a for a in acts}

    def raiz(x):
        while padre[x] != x:
            padre[x] = padre[padre[x]]
            x = padre[x]
        return x
    for a in acts:
        for b in acts:
            if a < b and set(rec[a]) & set(rec[b]):
                padre[raiz(a)] = raiz(b)
    grupos = collections.OrderedDict()
    for a in acts:
        grupos.setdefault(raiz(a), []).append(a)
    lista = []
    for i, (_, g) in enumerate(grupos.items()):
        personas = collections.Counter()
        for a in g:
            personas.update(rec[a])
        lista.append({"id": "Carril_%d" % (i + 1), "actividades": g,
                      "nombre": ", ".join(p for p, _ in personas.most_common())})
    de = {a: i for i, c in enumerate(lista) for a in c["actividades"]}
    return lista, de


def mayuscula(s):
    return s[:1].upper() + s[1:]


class Grafo:
    def __init__(self, nombres):
        self.nodos = collections.OrderedDict()     # id -> dict(tipo, nombre, etiqueta)
        self.flujos = []                          # [origen, destino, etiqueta, retorno]
        self.nombres = nombres
        self.k = collections.Counter()
        self.hechas = set()
        self.bucles = []                          # (fusion, decision, [nodos del rehacer])
        self.opcionales = set()                   # nodos de la rama «Sí» de un x(τ, X)

    def nodo(self, tipo, nombre="", etiqueta=None):
        self.k[tipo] += 1
        nid = "%s_%d" % (tipo, self.k[tipo])
        self.nodos[nid] = {"tipo": tipo, "nombre": nombre, "etiqueta": etiqueta}
        return nid

    def flujo(self, a, b, etiqueta="", retorno=False):
        self.flujos.append([a, b, etiqueta, retorno])

    def primera(self, n):
        if n["tipo"] == "act":
            return n["etiqueta"]
        for h in n.get("hijos", []):
            if h["tipo"] != "tau":
                return self.primera(h)
        return None

    def gen(self, n, entrada, etiqueta=""):
        t = n["tipo"]
        if t == "act":
            et = n["etiqueta"]
            nombre = mayuscula(self.nombres.get(et, et))
            if et in self.hechas:
                nombre += " (repetición)"
            self.hechas.add(et)
            x = self.nodo("Tarea", nombre, et)
            self.flujo(entrada, x, etiqueta)
            return x
        if t == "tau":
            return entrada
        if t == "seq":
            actual = entrada
            for i, h in enumerate(n["hijos"]):
                actual = self.gen(h, actual, etiqueta if i == 0 else "")
            return actual
        if t == "and":
            d = self.nodo("Paralela")
            self.flujo(entrada, d, etiqueta)
            salidas = [self.gen(h, d) for h in n["hijos"]]
            u = self.nodo("Paralela")
            for s in salidas:
                self.flujo(s, u)
            return u
        if t == "xor":
            opc = [h for h in n["hijos"] if h["tipo"] != "tau"]
            tau = len(opc) < len(n["hijos"])
            pregunta = ("¿Requiere %s?" % self.nombres.get(self.primera(opc[0]), "")) if tau and len(opc) == 1 else "¿Qué camino?"
            d = self.nodo("Exclusiva", pregunta)
            self.flujo(entrada, d, etiqueta)
            u = self.nodo("Exclusiva")
            for h in opc:
                antes = set(self.nodos)
                self.flujo(self.gen(h, d, "Sí" if tau else ""), u)
                if tau:
                    self.opcionales |= set(self.nodos) - antes
            if tau:
                self.flujo(d, u, "No")
            return u
        if t == "loop":
            hacer, rehacer = n["hijos"]
            f = self.nodo("Exclusiva")
            self.flujo(entrada, f, etiqueta)
            fin_hacer = self.gen(hacer, f)
            d = self.nodo("Exclusiva", "¿Requiere %s?" % self.nombres.get(self.primera(rehacer), ""))
            self.flujo(fin_hacer, d)
            antes = set(self.nodos)
            s = self.gen(rehacer, d, "Sí")
            self.flujo(s, f, "", True)
            self.bucles.append((f, d, [x for x in self.nodos if x not in antes]))
            return d
        raise ValueError(t)


def construir(traza):
    g = Grafo(traza["letras"])
    ini = g.nodo("Inicio", "Inicio del caso")
    ultimo = g.gen(traza["arbol_json"], ini)
    fin = g.nodo("Fin", "Caso terminado")
    g.flujo(ultimo, fin, "No" if g.nodos[ultimo]["nombre"].startswith("¿") else "")
    for f in g.flujos:                       # salidas sin etiqueta de una «¿Requiere ...?» -> "No"
        if g.nodos[f[0]]["nombre"].startswith("¿Requiere") and not f[2]:
            f[2] = "No"
    return g


def acomodar(g, de, n_carriles):
    rehacer = {x for _, _, xs in g.bucles for x in xs}
    ent = collections.defaultdict(list)
    sal = collections.defaultdict(list)
    for a, b, et, r in g.flujos:
        if not r:
            ent[b].append(a)
            sal[a].append(b)
    col = {}

    def c(n):
        if n not in col:
            previos = [p for p in ent[n] if p not in rehacer]
            col[n] = 0 if not previos else 1 + max(c(p) for p in previos)
        return col[n]
    for n in g.nodos:
        if n not in rehacer:
            c(n)
    for f, d, xs in g.bucles:                # el rehacer se dibuja hacia atras sobre fusion..decision
        for i, x in enumerate(xs):
            col[x] = max(col[f], col[d] - i)
    carril = {n: de[v["etiqueta"]] for n, v in g.nodos.items() if v["tipo"] == "Tarea"}
    for _ in range(len(g.nodos)):
        for n, v in g.nodos.items():
            if n in carril:
                continue
            previos = [p for p in ent[n] if p not in rehacer]
            if len(sal[n]) >= 2 and not (len(previos) == 1 and g.nodos[previos[0]]["tipo"] in ("Exclusiva", "Paralela")):
                destino = next((s for s in sal[n] if s in carril), None)       # division: carril de su primera rama
                if destino:
                    carril[n] = carril[destino]
            elif previos and all(p in carril for p in previos):
                carril[n] = carril[previos[-1]]                                 # union o simple: el ultimo previo
            elif v["tipo"] == "Inicio" and sal[n] and sal[n][0] in carril:
                carril[n] = carril[sal[n][0]]
    for n in g.nodos:
        carril.setdefault(n, 0)
    # filas dentro del carril: 0 = flujo principal; la rama opcional va arriba (-1);
    # el retrabajo usa la fila 0 si esta libre y si no sube
    fila, usadas = {}, set()

    def libre(n, filas):
        for r in filas:
            if (carril[n], col[n], r) not in usadas:
                usadas.add((carril[n], col[n], r))
                return r
    for n in g.nodos:
        if n not in rehacer and n not in g.opcionales:
            fila[n] = libre(n, range(0, 50))
    for n in g.nodos:
        if n in g.opcionales:
            fila[n] = libre(n, range(-1, -50, -1))
    for n in g.nodos:
        if n in rehacer:
            fila[n] = libre(n, [0] + list(range(-1, -50, -1)))
    lim = []
    for i in range(n_carriles):
        rs = [fila[n] for n in g.nodos if carril[n] == i] or [0]
        lim.append((min(rs), max(rs)))
    y0, y = [], TITULO
    for lo, hi in lim:
        y0.append(y)
        y += (hi - lo + 1) * FILA
    alto = [hi - lo + 1 for lo, hi in lim]
    pos = {}
    for n, v in g.nodos.items():
        cx = BANDA + 40 + col[n] * COLX + TAREA[0] / 2
        cy = y0[carril[n]] + (fila[n] - lim[carril[n]][0]) * FILA + FILA / 2
        w, h = TAREA if v["tipo"] == "Tarea" else ((COMP, COMP) if v["tipo"] in ("Exclusiva", "Paralela") else (EVENTO, EVENTO))
        pos[n] = (cx - w / 2, cy - h / 2, w, h)
    ancho = BANDA + 80 + (max(col.values()) + 1) * COLX
    return pos, [(y0[i], alto[i] * FILA) for i in range(n_carriles)], ancho, y


def puntos(g, pos, a, b):
    xa, ya, wa, ha = pos[a]
    xb, yb, wb, hb = pos[b]
    ca, cb = (xa + wa / 2, ya + ha / 2), (xb + wb / 2, yb + hb / 2)
    abajo = cb[1] > ca[1]
    if abs(ca[0] - cb[0]) < 1:                                       # misma columna: vertical
        return [(ca[0], ya + ha if abajo else ya), (cb[0], yb if abajo else yb + hb)]
    if abs(ca[1] - cb[1]) < 1:                                       # misma fila: horizontal
        return [(xa + wa, ca[1]), (xb, cb[1])] if cb[0] > ca[0] else [(xa, ca[1]), (xb + wb, cb[1])]
    if cb[0] < ca[0]:                                                # hacia atras: sale por un lado y entra por arriba/abajo
        return [(xa, ca[1]), (cb[0], ca[1]), (cb[0], yb if abajo else yb + hb)]
    if g.nodos[a]["tipo"] in ("Exclusiva", "Paralela"):              # compuerta: vertical y luego horizontal
        return [(ca[0], ya + ha if abajo else ya), (ca[0], cb[1]), (xb, cb[1])]
    return [(xa + wa, ca[1]), (cb[0], ca[1]), (cb[0], yb if abajo else yb + hb)]


def xml(g, pos, lanes, filas, miembros, ancho, alto):
    L = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
         'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" '
         'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" id="Definiciones" targetNamespace="http://bpmn.io/schema/bpmn">',
         '  <bpmn:collaboration id="Colaboracion"><bpmn:participant id="Participante" name="%s" processRef="Proceso"/></bpmn:collaboration>' % escape(g.titulo),
         '  <bpmn:process id="Proceso" isExecutable="false">', '    <bpmn:laneSet id="Carriles">']
    for i, l in enumerate(lanes):
        L.append('      <bpmn:lane id="%s" name="%s">' % (l["id"], escape(l["nombre"])))
        L += ['        <bpmn:flowNodeRef>%s</bpmn:flowNodeRef>' % n for n in g.nodos if miembros[n] == i]
        L.append('      </bpmn:lane>')
    L.append('    </bpmn:laneSet>')
    tipos = {"Inicio": "startEvent", "Fin": "endEvent", "Tarea": "task",
             "Exclusiva": "exclusiveGateway", "Paralela": "parallelGateway"}
    for n, v in g.nodos.items():
        L.append('    <bpmn:%s id="%s" name="%s"/>' % (tipos[v["tipo"]], n, escape(v["nombre"])))
    for i, (a, b, et, r) in enumerate(g.flujos, 1):
        L.append('    <bpmn:sequenceFlow id="Flujo_%d" sourceRef="%s" targetRef="%s"%s/>' % (
            i, a, b, ' name="%s"' % escape(et) if et else ""))
    L += ['  </bpmn:process>', '  <bpmndi:BPMNDiagram id="Diagrama">',
          '    <bpmndi:BPMNPlane id="Plano" bpmnElement="Colaboracion">',
          '      <bpmndi:BPMNShape id="Participante_di" bpmnElement="Participante" isHorizontal="true">'
          '<dc:Bounds x="0" y="%d" width="%d" height="%d"/></bpmndi:BPMNShape>' % (TITULO, ancho, alto - TITULO)]
    for l, (y, h) in zip(lanes, filas):
        L.append('      <bpmndi:BPMNShape id="%s_di" bpmnElement="%s" isHorizontal="true"><dc:Bounds x="30" y="%d" width="%d" height="%d"/></bpmndi:BPMNShape>' % (
            l["id"], l["id"], y, ancho - 30, h))
    for n in g.nodos:
        x, y, w, h = pos[n]
        L.append('      <bpmndi:BPMNShape id="%s_di" bpmnElement="%s"><dc:Bounds x="%d" y="%d" width="%d" height="%d"/></bpmndi:BPMNShape>' % (
            n, n, x, y, w, h))
    for i, (a, b, et, r) in enumerate(g.flujos, 1):
        pts = "".join('<di:waypoint x="%d" y="%d"/>' % p for p in puntos(g, pos, a, b))
        L.append('      <bpmndi:BPMNEdge id="Flujo_%d_di" bpmnElement="Flujo_%d">%s</bpmndi:BPMNEdge>' % (i, i, pts))
    L += ['    </bpmndi:BPMNPlane>', '  </bpmndi:BPMNDiagram>', '</bpmn:definitions>']
    return "\n".join(L) + "\n"


def _texto(x, y, s, tam=12, ancho=16, extra=""):
    palabras, lineas, actual = s.split(), [], ""
    for p in palabras:
        if len(actual) + len(p) + 1 > ancho and actual:
            lineas.append(actual)
            actual = p
        else:
            actual = (actual + " " + p).strip()
    if actual:
        lineas.append(actual)
    y0 = y - (len(lineas) - 1) * (tam + 3) / 2
    return "".join('<text x="%d" y="%d" font-size="%d" text-anchor="middle"%s>%s</text>' % (
        x, y0 + i * (tam + 3) + tam / 3, tam, extra, escape(l)) for i, l in enumerate(lineas))


def svg(g, pos, lanes, filas, ancho, alto):
    S = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" font-family="Helvetica, Arial, sans-serif">' % (ancho + 10, alto + 30),
         '<defs><marker id="f" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
         '<path d="M0,0 L10,5 L0,10 z" fill="#222"/></marker></defs>',
         '<rect x="0" y="0" width="%d" height="%d" fill="white"/>' % (ancho + 10, alto + 30),
         '<text x="10" y="22" font-size="16" font-weight="bold">%s</text>' % escape(g.titulo)]
    for i, (l, (y, h)) in enumerate(zip(lanes, filas)):
        S.append('<rect x="0" y="%d" width="%d" height="%d" fill="%s" stroke="#555"/>' % (y, ancho, h, "#F6F9FC" if i % 2 == 0 else "white"))
        S.append('<rect x="0" y="%d" width="%d" height="%d" fill="#ECECEC" stroke="#555"/>' % (y, BANDA - 10, h))
        S.append(_texto((BANDA - 10) / 2, y + h / 2, l["nombre"], 11, 11))
    for a, b, et, r in g.flujos:
        pts = puntos(g, pos, a, b)
        S.append('<polyline points="%s" fill="none" stroke="#222" stroke-width="1.5" marker-end="url(#f)"/>' % " ".join(
            "%d,%d" % p for p in pts))
        if et:
            (x1, y1), (x2, y2) = pts[0], pts[1]
            dx = 8 if x2 >= x1 else -24
            dy = -6 if abs(y2 - y1) < 1 else (14 if y2 > y1 else -8)
            S.append('<text x="%d" y="%d" font-size="12" font-weight="bold" font-style="italic">%s</text>' % (x1 + dx, y1 + dy, escape(et)))
    for n, v in g.nodos.items():
        x, y, w, h = pos[n]
        cx, cy = x + w / 2, y + h / 2
        if v["tipo"] == "Tarea":
            S.append('<rect x="%d" y="%d" width="%d" height="%d" rx="10" fill="#EAF2FB" stroke="#2F5D8A" stroke-width="1.6"/>' % (x, y, w, h))
            S.append(_texto(cx, cy, v["nombre"], 13, 17))
        elif v["tipo"] in ("Exclusiva", "Paralela"):
            S.append('<polygon points="%d,%d %d,%d %d,%d %d,%d" fill="#FFF4D6" stroke="#9A7B00" stroke-width="1.6"/>' % (
                cx, y, x + w, cy, cx, y + h, x, cy))
            S.append('<text x="%d" y="%d" font-size="24" text-anchor="middle">%s</text>' % (
                cx, cy + 8, "✕" if v["tipo"] == "Exclusiva" else "+"))
            if v["nombre"]:
                S.append(_texto(cx, y + h + 22, v["nombre"], 11, 20))
        else:
            S.append('<circle cx="%d" cy="%d" r="%d" fill="white" stroke="#222" stroke-width="%s"/>' % (
                cx, cy, w / 2, "1.6" if v["tipo"] == "Inicio" else "4"))
            S.append(_texto(cx, y + h + 16, v["nombre"], 11, 14))
    S.append('<text x="10" y="%d" font-size="11" fill="#555">Carriles = recursos que comparten actividades (atributo Resource). '
             'Compuertas: + paralela (AND), ✕ exclusiva (XOR).</text>' % (alto + 20))
    S.append("</svg>")
    return "\n".join(S) + "\n"


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    carpeta = sys.argv[1]
    with open(os.path.join(carpeta, "traza.json"), encoding="utf-8") as fh:
        traza = json.load(fh)
    lanes, de = carriles(traza)
    g = construir(traza)
    g.titulo = "Proceso del %s" % traza["registro"]
    pos, filas, ancho, alto = acomodar(g, de, len(lanes))
    miembros = {}
    for n in g.nodos:
        cy = pos[n][1] + pos[n][3] / 2
        miembros[n] = next(i for i, (y, h) in enumerate(filas) if y <= cy <= y + h)
    with open(os.path.join(carpeta, "bpmn.bpmn"), "w", encoding="utf-8") as fh:
        fh.write(xml(g, pos, lanes, filas, miembros, ancho, alto))
    with open(os.path.join(carpeta, "bpmn.svg"), "w", encoding="utf-8") as fh:
        fh.write(svg(g, pos, lanes, filas, ancho, alto))
    print("BPMN: %d tareas, %d compuertas, %d flujos, %d carriles -> bpmn.bpmn, bpmn.svg" % (
        sum(1 for v in g.nodos.values() if v["tipo"] == "Tarea"),
        sum(1 for v in g.nodos.values() if v["tipo"] in ("Exclusiva", "Paralela")), len(g.flujos), len(lanes)))
    for l in lanes:
        print("  carril %s: %s" % (l["nombre"], ", ".join(l["actividades"])))


if __name__ == "__main__":
    main()
