#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARBOL DE DECISION DE MINIMA ENTROPIA (ID3), CALCULADO NIVEL POR NIVEL
=====================================================================
Datos       datos/<archivo>.csv y datos/parametros.json (clase, valor para vacios).
Metodo      Info(D)   = -sum p_i log2 p_i
            Info_A(D) = sum |D_j|/|D| * Info(D_j)        (entropia ponderada, E(A))
            Ganancia  = Info(D) - Info_A(D)
            (Karaolis et al. 2010, ecs. 2.1-2.3; EJ26-14 p.3)
Regla       En cada nodo se evaluan TODOS los atributos que quedan y se divide por el
            de menor E(A) (= mayor ganancia). El nodo es hoja si es puro, si la mejor
            ganancia es 0 o si no quedan atributos; la hoja predice la clase mayoritaria.
Salida      el desarrollo por niveles en pantalla y traza.json (todas las cifras).

Uso         python3 codigo/resolver.py
            python3 codigo/resolver.py --datos otra.csv --clase Type
Solo usa la biblioteca estandar de Python 3.
"""
import argparse
import csv
import json
import math
import os
from collections import Counter, OrderedDict

AQUI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(AQUI)
TOL = 1e-12          # una ganancia menor que esto se considera 0


# ---------------------------------------------------------------------------
# 1. Datos
# ---------------------------------------------------------------------------
def leer_parametros(ruta):
    with open(ruta, encoding="utf-8") as fh:
        return json.load(fh)


def leer_datos(ruta, clase, vacio):
    """Lee el CSV; las celdas vacias de los atributos pasan a la categoria `vacio`."""
    with open(ruta, newline="", encoding="utf-8-sig") as fh:
        filas = [dict(f) for f in csv.DictReader(fh)]
    atributos = [c for c in filas[0].keys() if c != clase]
    recodificados = OrderedDict()
    for f in filas:
        for a in atributos:
            if f[a] is None or f[a].strip() == "":
                f[a] = vacio
                recodificados[a] = recodificados.get(a, 0) + 1
    return filas, atributos, recodificados


# ---------------------------------------------------------------------------
# 2. Entropia y entropia ponderada de un atributo
# ---------------------------------------------------------------------------
def entropia(conteo):
    n = sum(conteo.values())
    return 0.0 - sum((c / n) * math.log2(c / n) for c in conteo.values() if c)


def evaluar(filas, atributo, clase, clases, n_padre, h_padre):
    """Tabla por valor del atributo, E(A), ganancia, split info y razon de ganancia."""
    grupos = OrderedDict()
    for f in filas:
        grupos.setdefault(f[atributo], []).append(f)
    tabla, e, split = [], 0.0, 0.0
    for valor in sorted(grupos, key=lambda v: (-len(grupos[v]), v)):
        g = grupos[valor]
        conteo = Counter(f[clase] for f in g)
        peso = len(g) / n_padre
        h = entropia(conteo)
        e += peso * h
        split -= peso * math.log2(peso)
        tabla.append(OrderedDict([
            ("valor", valor), ("n", len(g)),
            ("conteo", OrderedDict((c, conteo.get(c, 0)) for c in clases)),
            ("H", h), ("peso", peso), ("aporte", peso * h)]))
    ganancia = h_padre - e
    if abs(ganancia) < TOL:
        ganancia = 0.0
    return OrderedDict([
        ("atributo", atributo), ("tabla", tabla), ("E", e), ("ganancia", ganancia),
        ("split", split), ("razon", ganancia / split if split > TOL else None),
    ]), grupos


def mayoritaria(conteo):
    """Clase con mas casos; empate -> orden alfabetico (se declara)."""
    mejor = max(conteo.values())
    return sorted(c for c, k in conteo.items() if k == mejor)[0]


# ---------------------------------------------------------------------------
# 3. Construccion nivel por nivel (anchura primero)
# ---------------------------------------------------------------------------
def construir(filas, atributos, clase):
    clases = sorted({f[clase] for f in filas})
    niveles, hojas = [], []
    pendientes = [([], filas, list(atributos))]          # (ruta, filas, atributos libres)
    nivel = 0
    while pendientes:
        nivel += 1
        nodos, siguientes = [], []
        for ruta, sub, libres in pendientes:
            conteo = Counter(f[clase] for f in sub)
            h = entropia(conteo)
            nodo = OrderedDict([
                ("id", "N%d.%d" % (nivel, len(nodos) + 1)),
                ("ruta", [[a, v] for a, v in ruta]), ("n", len(sub)),
                ("conteo", OrderedDict((c, conteo.get(c, 0)) for c in clases)),
                ("H", h), ("candidatos", []), ("decision", None)])
            if h == 0 or not libres:
                motivo = "pura" if h == 0 else "sin atributos"
                hoja = OrderedDict([("ruta", nodo["ruta"]), ("nivel", nivel),
                                    ("clase", mayoritaria(conteo)), ("n", len(sub)),
                                    ("aciertos", conteo[mayoritaria(conteo)]), ("H", h),
                                    ("motivo", motivo)])
                hojas.append(hoja)
                if h == 0 and nivel > 1:
                    continue                      # las hojas puras no se repiten en el nivel
                nodo["decision"] = OrderedDict([("tipo", "hoja"), ("clase", hoja["clase"]),
                                                ("motivo", motivo)])
                nodos.append(nodo)
                continue
            grupos_por_atr = {}
            for a in libres:
                cand, grupos = evaluar(sub, a, clase, clases, len(sub), h)
                nodo["candidatos"].append(cand)
                grupos_por_atr[a] = grupos
            # menor E(A); empate -> el atributo que aparece primero en el archivo
            mejor = min(nodo["candidatos"], key=lambda c: (round(c["E"], 12), libres.index(c["atributo"])))
            if mejor["ganancia"] <= 0:
                clase_h = mayoritaria(conteo)
                hojas.append(OrderedDict([("ruta", nodo["ruta"]), ("nivel", nivel),
                                          ("clase", clase_h), ("n", len(sub)),
                                          ("aciertos", conteo[clase_h]), ("H", h),
                                          ("motivo", "ganancia 0")]))
                nodo["decision"] = OrderedDict([("tipo", "hoja"), ("clase", clase_h),
                                                ("motivo", "ganancia 0")])
            else:
                a = mejor["atributo"]
                nodo["decision"] = OrderedDict([("tipo", "dividir"), ("atributo", a),
                                                ("ramas", len(grupos_por_atr[a]))])
                resto = [x for x in libres if x != a]
                for fila_t in mejor["tabla"]:
                    v = fila_t["valor"]
                    siguientes.append((ruta + [(a, v)], grupos_por_atr[a][v], resto))
            nodos.append(nodo)
        if nodos:
            niveles.append(OrderedDict([("nivel", nivel), ("nodos", nodos)]))
        pendientes = siguientes
    return clases, niveles, hojas


# ---------------------------------------------------------------------------
# 4. Programa principal: imprime el desarrollo y escribe traza.json
# ---------------------------------------------------------------------------
def f4(x):
    return "—" if x is None else "%.4f" % x


def imprimir(traza):
    d = traza["datos"]
    print("ARBOL DE MINIMA ENTROPIA — %s (%d registros)" % (d["archivo"], d["n"]))
    print("Clase: %s   Atributos evaluados: %s" % (d["clase"], ", ".join(d["atributos"])))
    for a, k in d["recodificados"].items():
        print("  %s: %d celdas vacias -> '%s'" % (a, k, d["vacio"]))
    for niv in traza["niveles"]:
        print("\n" + "=" * 78 + "\nNIVEL %d" % niv["nivel"] + "\n" + "=" * 78)
        for nodo in niv["nodos"]:
            ruta = " y ".join("%s = %s" % (a, v) for a, v in nodo["ruta"]) or "raiz"
            print("\nNodo %s (%s): n = %d, H = %s, %s" % (
                nodo["id"], ruta, nodo["n"], f4(nodo["H"]),
                ", ".join("%s %d" % (c, k) for c, k in nodo["conteo"].items() if k)))
            for cand in nodo["candidatos"]:
                print("  Atributo %s:" % cand["atributo"])
                for t in cand["tabla"]:
                    if len(cand["tabla"]) > 12 and t["H"] == 0:
                        continue
                    print("    %-28s n=%4d  H=%s  peso=%s  aporte=%s" % (
                        str(t["valor"])[:28], t["n"], f4(t["H"]), f4(t["peso"]), f4(t["aporte"])))
                if len(cand["tabla"]) > 12:
                    puros = sum(1 for t in cand["tabla"] if t["H"] == 0)
                    print("    (%d valores puros con H = 0 omitidos en pantalla; estan en traza.json)" % puros)
                print("    E(%s) = %s   ganancia = %s   split = %s   razon = %s" % (
                    cand["atributo"], f4(cand["E"]), f4(cand["ganancia"]), f4(cand["split"]), f4(cand["razon"])))
            dec = nodo["decision"]
            if dec["tipo"] == "dividir":
                print("  -> se divide por %s (menor E) en %d ramas" % (dec["atributo"], dec["ramas"]))
            else:
                print("  -> hoja %s (%s)" % (dec["clase"], dec["motivo"]))
    r = traza["resumen"]
    print("\nHojas: %d   Profundidad: %d   Exactitud de re-sustitucion: %d/%d = %.2f %%" % (
        r["hojas"], r["profundidad"], r["aciertos"], traza["datos"]["n"], 100 * r["exactitud"]))
    impuras = [h for h in traza["hojas"] if h["H"] > 0]
    if impuras:
        print("Hojas impuras:")
        for h in impuras:
            print("  %s -> %s (%d/%d)" % (" y ".join("%s = %s" % (a, v) for a, v in h["ruta"]),
                                         h["clase"], h["aciertos"], h["n"]))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--parametros", default=os.path.join(BASE, "datos", "parametros.json"))
    ap.add_argument("--datos", help="CSV (por omision, el de parametros.json)")
    ap.add_argument("--traza", default=os.path.join(BASE, "traza.json"))
    args = ap.parse_args()
    par = leer_parametros(args.parametros)
    ruta = args.datos or os.path.join(os.path.dirname(args.parametros), par["archivo"])
    filas, atributos, recod = leer_datos(ruta, par["clase"], par.get("vacio", "Sin especificar"))
    excluir = par.get("excluir", [])
    if excluir:
        print("AVISO: se excluyen %s. La regla R1 del curso pide usar todos los atributos." % excluir)
        atributos = [a for a in atributos if a not in excluir]
    clases, niveles, hojas = construir(filas, atributos, par["clase"])
    aciertos = sum(h["aciertos"] for h in hojas)
    traza = OrderedDict([
        ("problema", par.get("problema", "")),
        ("metodo", "ID3 de minima entropia, nivel por nivel"),
        ("fuentes", ["EJ26-14 p.3, ecs. 2.1-2.3", "EJ26-21 p.3"]),
        ("datos", OrderedDict([("archivo", os.path.basename(ruta)), ("n", len(filas)),
                               ("clase", par["clase"]), ("clases", clases), ("atributos", atributos),
                               ("excluidos", excluir), ("vacio", par.get("vacio", "Sin especificar")),
                               ("recodificados", recod),
                               ("valores_distintos", OrderedDict((a, len({f[a] for f in filas})) for a in atributos))])),
        ("H_raiz", niveles[0]["nodos"][0]["H"]),
        ("niveles", niveles),
        ("hojas", hojas),
        ("resumen", OrderedDict([("raiz", niveles[0]["nodos"][0]["decision"].get("atributo")),
                                 ("hojas", len(hojas)), ("profundidad", max(len(h["ruta"]) for h in hojas)),
                                 ("aciertos", aciertos), ("exactitud", aciertos / len(filas))])),
    ])
    imprimir(traza)
    with open(args.traza, "w", encoding="utf-8") as fh:
        json.dump(traza, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("\ntraza escrita en %s" % args.traza)


if __name__ == "__main__":
    main()
