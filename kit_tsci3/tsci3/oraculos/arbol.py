"""Oráculo independiente del árbol de mínima entropía (no importa el resolver de la skill).

Otro camino de cálculo:
  * E(A) en forma de conteos: E(A) = (1/N)·Σ_v [ n_v·log2 n_v − Σ_c n_vc·log2 n_vc ].
  * Ganancia cero exacta, con enteros: Info(D) = E(A) ⇔ n_vc·N = n_c·n_v para todo v, c.
  * Recorrido en profundidad (el resolver va por anchura).

Comprueba contra traza.json:
  R1  la traza usa todos los atributos del CSV menos la clase;
  R2  cada nodo impuro del oráculo aparece en algún nivel de la traza con todos sus candidatos;
  cifras: n, conteos, H, tablas por valor, E(A), ganancia y decisión de cada nodo; hojas y resumen.
"""
import csv
import json
import math
from collections import Counter, defaultdict

TOL = 1e-9


def _xlogx(n):
    return n * math.log2(n) if n > 0 else 0.0


def leer(ruta_csv, clase, vacio):
    with open(ruta_csv, newline="", encoding="utf-8-sig") as fh:
        lector = csv.reader(fh)
        enc = next(lector)
        filas = [r for r in lector if r]
    ic = enc.index(clase)
    atrs = [a for i, a in enumerate(enc) if i != ic]
    datos = []
    for r in filas:
        reg = {a: (r[i] if r[i].strip() != "" else vacio) for i, a in enumerate(enc) if i != ic}
        reg["__clase__"] = r[ic]
        datos.append(reg)
    return enc, atrs, datos


def _info(regs):
    n = len(regs)
    return (_xlogx(n) - sum(_xlogx(k) for k in Counter(r["__clase__"] for r in regs).values())) / n


def _e_atributo(regs, a):
    n = len(regs)
    grupos = defaultdict(list)
    for r in regs:
        grupos[r[a]].append(r)
    total = 0.0
    for g in grupos.values():
        total += _xlogx(len(g)) - sum(_xlogx(k) for k in Counter(r["__clase__"] for r in g).values())
    return total / n, grupos


def _ganancia_cero(regs, grupos):
    n = len(regs)
    nc = Counter(r["__clase__"] for r in regs)
    for g in grupos.values():
        cg = Counter(r["__clase__"] for r in g)
        for c, k in nc.items():
            if cg.get(c, 0) * n != k * len(g):
                return False
    return True


def construir(regs, libres, ruta=(), nivel=1, salida=None):
    """Devuelve dict ruta -> nodo del oráculo (impuros con candidatos; hojas con clase)."""
    if salida is None:
        salida = {}
    conteo = Counter(r["__clase__"] for r in regs)
    mejor_n = max(conteo.values())
    clase_m = sorted(c for c, k in conteo.items() if k == mejor_n)[0]
    nodo = {"nivel": nivel, "n": len(regs), "conteo": dict(conteo), "H": _info(regs),
            "candidatos": {}, "decision": None}
    salida[tuple(ruta)] = nodo
    if len(conteo) == 1 or not libres:
        nodo["decision"] = ("hoja", clase_m, "pura" if len(conteo) == 1 else "sin atributos")
        return salida
    evals = []
    for orden, a in enumerate(libres):
        e, grupos = _e_atributo(regs, a)
        cero = _ganancia_cero(regs, grupos)
        tabla = {v: (len(g), dict(Counter(r["__clase__"] for r in g))) for v, g in grupos.items()}
        nodo["candidatos"][a] = {"E": e, "cero": cero, "tabla": tabla}
        evals.append((round(e, 12), orden, a, grupos, cero))
    _, _, a, grupos, cero = min(evals)
    if cero:
        nodo["decision"] = ("hoja", clase_m, "ganancia 0")
        return salida
    nodo["decision"] = ("dividir", a, len(grupos))
    resto = [x for x in libres if x != a]
    for v, g in grupos.items():
        construir(g, resto, list(ruta) + [(a, v)], nivel + 1, salida)
    return salida


def verificar(ruta_csv, ruta_traza, clase=None, vacio=None):
    """Lista de (ok, mensaje). La traza manda clase y vacío si no se dan."""
    with open(ruta_traza, encoding="utf-8") as fh:
        tr = json.load(fh)
    d = tr["datos"]
    clase = clase or d["clase"]
    vacio = vacio or d.get("vacio", "Sin especificar")
    enc, atrs, regs = leer(ruta_csv, clase, vacio)
    res = []

    def chk(ok, msg):
        res.append((bool(ok), msg))

    # R1
    chk(d["atributos"] == atrs and not d.get("excluidos"),
        "R1: la traza usa todos los atributos %s" % atrs if d["atributos"] == atrs and not d.get("excluidos")
        else "R1: la traza usa %s y excluye %s; el CSV tiene %s" % (d["atributos"], d.get("excluidos"), atrs))
    chk(d["n"] == len(regs), "registros: traza %d, CSV %d" % (d["n"], len(regs)))

    orac = construir(regs, atrs)
    # nodos de la traza por ruta
    tnodos = {}
    for niv in tr["niveles"]:
        for nd in niv["nodos"]:
            tnodos[tuple(tuple(x) for x in nd["ruta"])] = (niv["nivel"], nd)

    impuros = {r: n for r, n in orac.items() if n["candidatos"]}
    faltan = [r for r in impuros if r not in tnodos]
    chk(not faltan, "R2: los %d nodos impuros del oráculo están en los niveles de la traza" % len(impuros)
        if not faltan else "R2: faltan en la traza los nodos %s" % faltan[:5])

    errores_nodo = 0
    for ruta, on in impuros.items():
        if ruta not in tnodos:
            continue
        nivel, tn = tnodos[ruta]
        malos = []
        if nivel != on["nivel"]:
            malos.append("nivel %s≠%s" % (nivel, on["nivel"]))
        if tn["n"] != on["n"] or {k: v for k, v in tn["conteo"].items() if v} != on["conteo"]:
            malos.append("conteo")
        if abs(tn["H"] - on["H"]) > TOL:
            malos.append("H %.6f≠%.6f" % (tn["H"], on["H"]))
        tc = {c["atributo"]: c for c in tn["candidatos"]}
        if set(tc) != set(on["candidatos"]):
            malos.append("candidatos %s≠%s" % (sorted(tc), sorted(on["candidatos"])))
        for a, oc in on["candidatos"].items():
            if a not in tc:
                continue
            c = tc[a]
            if abs(c["E"] - oc["E"]) > TOL:
                malos.append("E(%s) %.9f≠%.9f" % (a, c["E"], oc["E"]))
            if oc["cero"] != (c["ganancia"] == 0):
                malos.append("ganancia cero de %s: traza %s, exacto %s" % (a, c["ganancia"] == 0, oc["cero"]))
            ttab = {t["valor"]: (t["n"], {k: v for k, v in t["conteo"].items() if v}) for t in c["tabla"]}
            if ttab != oc["tabla"]:
                malos.append("tabla por valor de %s" % a)
        dec = tn["decision"]
        od = on["decision"]
        if od[0] == "dividir":
            if dec["tipo"] != "dividir" or dec["atributo"] != od[1] or dec["ramas"] != od[2]:
                malos.append("decisión: traza %s, oráculo divide por %s" % (dec, od[1]))
        else:
            if dec["tipo"] != "hoja" or dec["clase"] != od[1]:
                malos.append("decisión: traza %s, oráculo hoja %s" % (dec, od[1]))
        if malos:
            errores_nodo += 1
            chk(False, "nodo %s: %s" % (" y ".join("%s=%s" % p for p in ruta) or "raíz", "; ".join(malos)))
    chk(errores_nodo == 0, "cifras y decisiones de %d nodos impuros" % len(impuros))

    ohojas = {r: n for r, n in orac.items() if n["decision"][0] == "hoja"}
    thojas = {tuple(tuple(x) for x in h["ruta"]): h for h in tr["hojas"]}
    iguales = set(ohojas) == set(thojas) and all(
        thojas[r]["clase"] == ohojas[r]["decision"][1]
        and thojas[r]["aciertos"] == max(ohojas[r]["conteo"].values())
        and thojas[r]["n"] == ohojas[r]["n"] for r in ohojas)
    chk(iguales, "hojas: %d en el oráculo, %d en la traza, clase y aciertos iguales" % (len(ohojas), len(thojas))
        if iguales else "hojas distintas: oráculo %d, traza %d" % (len(ohojas), len(thojas)))
    aciertos = sum(max(n["conteo"].values()) for n in ohojas.values())
    raiz = orac[()]["decision"]
    chk(tr["resumen"]["aciertos"] == aciertos and tr["resumen"]["raiz"] == (raiz[1] if raiz[0] == "dividir" else None),
        "resumen: raíz %s, %d/%d aciertos" % (raiz[1], aciertos, len(regs)))
    return res
