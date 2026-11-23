"""Oráculo independiente de patrones secuenciales (no importa el resolver).

Otro algoritmo: crecimiento de patrones (extensión de secuencia <…, {x}> y de ítem
<…, E ∪ {x}>) con poda por soporte, y contención voraz (cada elemento se empareja con el
primer evento posterior que lo contiene). Compara el conjunto de patrones y sus soportes.
"""
import json


def leer_spmf(ruta):
    seqs = []
    for linea in open(ruta, encoding="utf-8-sig"):
        t = [int(x) for x in linea.split()]
        if not t:
            continue
        seq, ev = [], set()
        for x in t:
            if x < 0:
                if ev:
                    seq.append(frozenset(ev))
                    ev = set()
                if x == -2:
                    break
            else:
                ev.add(x)
        seqs.append(seq)
    return seqs


def contiene(seq, patron):
    i = 0
    for e in patron:
        while i < len(seq) and not e <= seq[i]:
            i += 1
        if i == len(seq):
            return False
        i += 1
    return True


def crecer(seqs, minsup, maxsize, maxlen):
    n = len(seqs)
    items = sorted({x for s in seqs for e in s for x in e})
    res = {}

    def soporte(p):
        return sum(1 for s in seqs if contiene(s, p))

    def visitar(p):
        cands = []
        if len(p) < maxlen:
            cands += [p + (frozenset([x]),) for x in items]
        if p and len(p[-1]) < maxsize:
            cands += [p[:-1] + (p[-1] | {x},) for x in items if x > max(p[-1])]
        for c in cands:
            k = soporte(c)
            if k / n >= minsup and c not in res:
                res[c] = k
                visitar(c)
    visitar(())
    return res


def verificar(ruta, ruta_traza):
    tr = json.load(open(ruta_traza, encoding="utf-8"))
    seqs = leer_spmf(ruta)
    res = []
    orac = crecer(seqs, tr["soporte_min"], tr["maxsize"], tr["maxlen"])
    traz = {tuple(frozenset(e) for e in p["patron"]): p["secuencias"] for p in tr["patrones"]}
    res.append((len(seqs) == tr["n"], "secuencias: %d" % len(seqs)))
    res.append((set(orac) == set(traz), "patrones frecuentes: oráculo %d, traza %d" % (len(orac), len(traz))))
    malos = [p for p in traz if p in orac and orac[p] != traz[p]]
    res.append((not malos, "secuencias que contienen cada patrón (contención voraz)" + (": difieren %d" % len(malos) if malos else "")))
    return res
