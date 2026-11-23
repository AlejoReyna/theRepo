#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TRATAMIENTO DE DATOS CON SUBSETTINGS VARIADOS, DESDE UN PLAN EN JSON
====================================================================
Un solo plan (datos/plan.json) se ejecuta aqui en Python y se traduce a R (--r) con los
modismos de SUBSET.pdf (read.csv, subset, df[, c()], indices negativos, which, %in%,
grepl, complete.cases, is.na, colSums(is.na()), write.csv). Cada paso registra filas y
columnas en la bitacora; R escribe la suya y se comparan (comparar_bitacoras.py).

Semantica comun (igual que R):
  * celda vacia o "NA" (o los valores de "na") -> NA; numeros con coma de miles -> texto
    hasta que un paso "numero" los convierta;
  * "filtrar" = subset(): conserva solo filas donde la condicion es VERDADERA (NA se va);
  * "excluir" = d[-which(cond), ]: quita solo filas donde la condicion es VERDADERA (NA se queda).

Pasos: perfil | quitar_columnas | seleccionar | renombrar | numero | extraer | restar |
       filtrar (+select) | excluir | quitar_na | comunes | pivotear | completos |
       discretizar | muestra | guardar
Condicion: {"y": [...]} | {"o": [...]} | [columna, operador, valor]
Operadores: == != > >= < <= en no_en na no_na contiene  (+ "fecha": "%m/%d/%Y" para fechas)

Uso   python3 codigo/resolver.py                 (ejecuta datos/plan.json)
      python3 codigo/resolver.py --r codigo/script.R   (ademas escribe el script de R)
Solo biblioteca estandar.
"""
import argparse
import collections
import csv
import datetime as dt
import json
import os
import random
import re

AQUI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(AQUI)
NA = None


# ---------------------------------------------------------------------------
# Datos como R: lista de columnas + filas (listas); NA = None
# ---------------------------------------------------------------------------
class Tabla:
    def __init__(self, cols, filas):
        self.cols, self.filas = list(cols), filas

    def idx(self, c):
        if c not in self.cols:
            raise SystemExit("No existe la columna %r. Columnas: %s" % (c, self.cols))
        return self.cols.index(c)

    def col(self, c):
        i = self.idx(c)
        return [f[i] for f in self.filas]

    def copia(self, filas=None, cols=None):
        return Tabla(cols if cols is not None else self.cols, filas if filas is not None else [list(f) for f in self.filas])


def a_num(v):
    if v is NA:
        return NA
    if isinstance(v, (int, float)):
        return v
    try:
        return float(v)
    except ValueError:
        return NA


def leer(ruta, na, recortar_nombres):
    with open(ruta, newline="", encoding="utf-8-sig") as fh:
        r = csv.reader(fh)
        enc = next(r)
        filas = [[NA if x in na else x for x in f] for f in r if f]
    if recortar_nombres:
        enc = [c.strip() for c in enc]
    # como read.csv: una columna cuyos valores no NA son todos numeros pasa a numerica
    for j in range(len(enc)):
        vals = [f[j] for f in filas if f[j] is not NA]
        if vals and all(re.fullmatch(r"\s*[-+]?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?\s*", v) for v in vals):
            for f in filas:
                if f[j] is not NA:
                    x = float(f[j])
                    f[j] = int(x) if x.is_integer() and "." not in f[j] and "e" not in f[j].lower() else x
    return Tabla(enc, filas)


# ---------------------------------------------------------------------------
# Condiciones con logica de tres valores (como R)
# ---------------------------------------------------------------------------
def evaluar(t, cond, fila):
    if isinstance(cond, dict):
        if "y" in cond:
            vs = [evaluar(t, c, fila) for c in cond["y"]]
            return False if False in vs else (NA if NA in vs else True)
        if "o" in cond:
            vs = [evaluar(t, c, fila) for c in cond["o"]]
            return True if True in vs else (NA if NA in vs else False)
        if "no" in cond:
            v = evaluar(t, cond["no"], fila)
            return NA if v is NA else not v
        raise SystemExit("condicion desconocida %r" % cond)
    col, op, *resto = cond
    v = fila[t.idx(col)]
    val = resto[0] if resto else None
    fmt = resto[1].get("fecha") if len(resto) > 1 and isinstance(resto[1], dict) else None
    if op == "na":
        return v is NA
    if op == "no_na":
        return v is not NA
    if v is NA:
        return NA
    if op == "en":
        return v in val or str(v) in [str(x) for x in val]
    if op == "no_en":
        return not (v in val or str(v) in [str(x) for x in val])
    if op == "contiene":
        return re.search(val, str(v)) is not None
    if fmt:
        try:
            a = dt.datetime.strptime(str(v), fmt).date()
        except ValueError:
            return NA
        b = dt.date.fromisoformat(val)
    elif isinstance(val, (int, float)):
        a, b = a_num(v), val
        if a is NA:
            return NA
    else:
        a, b = str(v), str(val)
    return {"==": a == b, "!=": a != b, ">": a > b, ">=": a >= b, "<": a < b, "<=": a <= b}[op]


# ---------------------------------------------------------------------------
# Pasos
# ---------------------------------------------------------------------------
def perfil(t):
    salida = []
    cols = {c: t.col(c) for c in t.cols}
    for c in t.cols:
        v = cols[c]
        no_na = [x for x in v if x is not NA]
        distintos = len(set(map(str, no_na)))
        dup = [o for o in t.cols if o != c and t.cols.index(o) < t.cols.index(c) and cols[o] == v]
        comas = sum(1 for x in no_na if isinstance(x, str) and re.fullmatch(r"\d{1,3}(,\d{3})+(\.\d+)?", x))
        salida.append(collections.OrderedDict([
            ("columna", c), ("tipo", "numérica" if no_na and all(isinstance(x, (int, float)) for x in no_na) else "texto"),
            ("no_na", len(no_na)), ("na", len(v) - len(no_na)), ("distintos", distintos),
            ("constante", distintos <= 1), ("igual_a", dup[0] if dup else ""),
            ("numeros_con_coma", comas), ("ejemplo", str(no_na[0])[:40] if no_na else "")]))
    return salida


def aplicar(paso, tablas, actual):
    tipo = paso["tipo"]
    t = tablas[paso.get("desde", actual)]
    if tipo == "quitar_columnas":
        quitar = [c for c in paso["columnas"] if c in t.cols]
        faltan = [c for c in paso["columnas"] if c not in t.cols]
        if faltan:
            raise SystemExit("quitar_columnas: no existen %s" % faltan)
        keep = [i for i, c in enumerate(t.cols) if c not in quitar]
        return Tabla([t.cols[i] for i in keep], [[f[i] for i in keep] for f in t.filas])
    if tipo == "seleccionar":
        ii = [t.idx(c) for c in paso["columnas"]]
        return Tabla(paso["columnas"], [[f[i] for i in ii] for f in t.filas])
    if tipo == "renombrar":
        n = t.copia()
        for a, b in paso["nombres"].items():
            n.cols[n.idx(a)] = b
        return n
    if tipo == "numero":
        n = t.copia()
        i = n.idx(paso["columna"])
        quitar = paso.get("quitar", ",")
        for f in n.filas:
            f[i] = NA if f[i] is NA else a_num(str(f[i]).replace(quitar, ""))
        return n
    if tipo == "extraer":                      # regex con grupos -> columnas numericas nuevas
        n = t.copia()
        i = n.idx(paso["columna"])
        rx = re.compile(paso["regex"])
        for f in n.filas:
            m = rx.search(str(f[i])) if f[i] is not NA else None
            f.extend([a_num(m.group(k + 1)) if m else NA for k in range(len(paso["nuevas"]))])
        n.cols += paso["nuevas"]
        if paso.get("quitar_origen"):
            n = aplicar({"tipo": "quitar_columnas", "columnas": [paso["columna"]]}, {"x": n}, "x")
        return n
    if tipo == "restar":
        n = t.copia()
        a, b = n.idx(paso["a"]), n.idx(paso["b"])
        for f in n.filas:
            x, y = a_num(f[a]), a_num(f[b])
            f.append(NA if x is NA or y is NA else x - y)
        n.cols.append(paso["nueva"])
        return n
    if tipo == "filtrar":
        n = t.copia(filas=[list(f) for f in t.filas if evaluar(t, paso["condicion"], f) is True])
        if paso.get("select"):
            n = aplicar({"tipo": "seleccionar", "columnas": paso["select"]}, {"x": n}, "x")
        return n
    if tipo == "discretizar":                   # cut(x, breaks, right = FALSE, labels)
        n = t.copia()
        i = n.idx(paso["columna"])
        cortes = [float("-inf") if c is None and k == 0 else float("inf") if c is None else c
                  for k, c in enumerate(paso["cortes"])]
        derecha = paso.get("derecha", False)
        for f in n.filas:
            x = a_num(f[i])
            et = NA
            if x is not NA:
                for k in range(len(cortes) - 1):
                    a, b = cortes[k], cortes[k + 1]
                    if (a <= x < b) if not derecha else (a < x <= b):
                        et = paso["etiquetas"][k]
                        break
            f.append(et)
        n.cols.append(paso["nueva"])
        return n
    if tipo == "excluir":
        return t.copia(filas=[list(f) for f in t.filas if evaluar(t, paso["condicion"], f) is not True])
    if tipo == "quitar_na":
        ii = [t.idx(c) for c in paso.get("columnas", t.cols)]
        return t.copia(filas=[list(f) for f in t.filas if all(f[i] is not NA for i in ii)])
    if tipo == "completos":
        return t.copia(filas=[list(f) for f in t.filas if all(x is not NA for x in f)])
    if tipo == "comunes":                       # valores de `columna` presentes en todos los grupos de `grupo`
        vc, vg = t.col(paso["columna"]), t.col(paso["grupo"])
        por = collections.defaultdict(set)
        for a, g in zip(vc, vg):
            por[g].add(a)
        comunes = set.intersection(*por.values()) if por else set()
        i = t.idx(paso["columna"])
        n = t.copia(filas=[list(f) for f in t.filas if f[i] in comunes])
        n.comunes = sorted(comunes)
        return n
    if tipo == "pivotear":                      # reshape(direction = "wide")
        claves, piv, val = paso["claves"], paso["columna"], paso["valor"]
        ik, ip, iv = [t.idx(c) for c in claves], t.idx(piv), t.idx(val)
        niveles = []
        filas = collections.OrderedDict()
        for f in t.filas:
            if f[ip] not in niveles:
                niveles.append(f[ip])
            filas.setdefault(tuple(f[i] for i in ik), {})[f[ip]] = f[iv]
        return Tabla(claves + ["%s.%s" % (val, p) for p in niveles],
                     [list(k) + [d.get(p, NA) for p in niveles] for k, d in filas.items()])
    if tipo == "muestra":                       # solo el tamano: el contenido depende del RNG de R
        k = round(paso["proporcion"] * len(t.filas)) if paso.get("parte", "muestra") == "muestra" else \
            len(t.filas) - round(paso["proporcion"] * len(t.filas))
        rng = random.Random(paso.get("semilla", 0))
        idx = sorted(rng.sample(range(len(t.filas)), round(paso["proporcion"] * len(t.filas))))
        if paso.get("parte", "muestra") == "resto":
            s = set(idx)
            idx = [i for i in range(len(t.filas)) if i not in s]
        n = t.copia(filas=[list(t.filas[i]) for i in idx])
        assert len(n.filas) == k
        return n
    if tipo == "guardar":
        return t
    raise SystemExit("paso desconocido %r" % tipo)


# ---------------------------------------------------------------------------
# Traduccion a R (modismos de SUBSET.pdf)
# ---------------------------------------------------------------------------
def r_val(v):
    if isinstance(v, str):
        return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return repr(v)


def r_cond(c, df):
    if isinstance(c, dict):
        if "y" in c:
            return "(" + " & ".join(r_cond(x, df) for x in c["y"]) + ")"
        if "o" in c:
            return "(" + " | ".join(r_cond(x, df) for x in c["o"]) + ")"
        return "!(" + r_cond(c["no"], df) + ")"
    col, op, *resto = c
    ref = "%s[[%s]]" % (df, r_val(col)) if df else ("`%s`" % col if not re.fullmatch(r"[A-Za-z.][A-Za-z0-9._]*", col) else col)
    val = resto[0] if resto else None
    fmt = resto[1].get("fecha") if len(resto) > 1 and isinstance(resto[1], dict) else None
    if op == "na":
        return "is.na(%s)" % ref
    if op == "no_na":
        return "!is.na(%s)" % ref
    if op in ("en", "no_en"):
        e = "%s %%in%% c(%s)" % (ref, ", ".join(r_val(x) for x in val))
        return e if op == "en" else "!(%s)" % e
    if op == "contiene":
        return "grepl(%s, %s)" % (r_val(val), ref)
    if fmt:
        return "as.Date(%s, format = %s) %s as.Date(%s)" % (ref, r_val(fmt), op, r_val(val))
    return "%s %s %s" % (ref, op, r_val(val))


def r_paso(p, nombre, actual):
    tipo, d = p["tipo"], p.get("desde", actual)
    o = nombre
    L = []
    if tipo == "quitar_columnas":
        L.append("%s <- %s[, -which(names(%s) %%in%% c(%s))]   # indice negativo por nombre" % (
            o, d, d, ", ".join(r_val(c) for c in p["columnas"])))
    elif tipo == "seleccionar":
        L.append("%s <- %s[, c(%s)]" % (o, d, ", ".join(r_val(c) for c in p["columnas"])))
    elif tipo == "renombrar":
        L.append("%s <- %s" % (o, d))
        for a, b in p["nombres"].items():
            L.append("names(%s)[names(%s) == %s] <- %s" % (o, o, r_val(a), r_val(b)))
    elif tipo == "numero":
        L += ["%s <- %s" % (o, d), "%s[[%s]] <- as.numeric(gsub(%s, \"\", %s[[%s]]))" % (
            o, r_val(p["columna"]), r_val(p.get("quitar", ",")), o, r_val(p["columna"]))]
    elif tipo == "extraer":
        L += ["%s <- %s" % (o, d), "m <- regmatches(%s[[%s]], regexec(%s, %s[[%s]]))" % (
            o, r_val(p["columna"]), r_val(p["regex"]), o, r_val(p["columna"]))]
        for k, nueva in enumerate(p["nuevas"]):
            L.append("%s[[%s]] <- as.numeric(sapply(m, function(x) if (length(x) > %d) x[%d] else NA))" % (
                o, r_val(nueva), k + 1, k + 2))
        if p.get("quitar_origen"):
            L.append("%s[[%s]] <- NULL" % (o, r_val(p["columna"])))
    elif tipo == "restar":
        L += ["%s <- %s" % (o, d), "%s[[%s]] <- %s[[%s]] - %s[[%s]]" % (
            o, r_val(p["nueva"]), o, r_val(p["a"]), o, r_val(p["b"]))]
    elif tipo == "filtrar":
        estilo = p.get("estilo", "subset")
        if estilo == "corchetes":
            L.append("%s <- %s[which(%s), ]" % (o, d, r_cond(p["condicion"], d)))
        elif p.get("select"):
            L.append("%s <- subset(%s, %s, select = c(%s))" % (o, d, r_cond(p["condicion"], None),
                                                             ", ".join(r_val(c) for c in p["select"])))
        else:
            L.append("%s <- subset(%s, %s)" % (o, d, r_cond(p["condicion"], None)))
    elif tipo == "discretizar":
        cortes = ["-Inf" if c is None and k == 0 else "Inf" if c is None else repr(c) for k, c in enumerate(p["cortes"])]
        L += ["%s <- %s" % (o, d), "%s[[%s]] <- as.character(cut(%s[[%s]], breaks = c(%s), right = %s, labels = c(%s)))" % (
            o, r_val(p["nueva"]), o, r_val(p["columna"]), ", ".join(cortes), "TRUE" if p.get("derecha") else "FALSE",
            ", ".join(r_val(e) for e in p["etiquetas"]))]
    elif tipo == "excluir":
        L += ["idx <- which(%s)" % r_cond(p["condicion"], d),
              "%s <- if (length(idx)) %s[-idx, ] else %s   # -integer(0) borraria todo" % (o, d, d)]
    elif tipo == "quitar_na":
        cols = p.get("columnas")
        L.append("%s <- %s[complete.cases(%s), ]" % (o, d, "%s[, c(%s)]" % (d, ", ".join(r_val(c) for c in cols)) if cols else d))
    elif tipo == "completos":
        L.append("%s <- %s[complete.cases(%s), ]" % (o, d, d))
    elif tipo == "comunes":
        L += ["comunes <- Reduce(intersect, split(%s[[%s]], %s[[%s]]))" % (d, r_val(p["columna"]), d, r_val(p["grupo"])),
              "%s <- %s[%s[[%s]] %%in%% comunes, ]" % (o, d, d, r_val(p["columna"]))]
    elif tipo == "pivotear":
        cols = p["claves"] + [p["columna"], p["valor"]]
        L.append("%s <- reshape(%s[, c(%s)], idvar = c(%s), timevar = %s, direction = \"wide\")" % (
            o, d, ", ".join(r_val(c) for c in cols), ", ".join(r_val(c) for c in p["claves"]), r_val(p["columna"])))
    elif tipo == "muestra":
        L += ["set.seed(%d)" % p.get("semilla", 0),
              "idx <- sample(nrow(%s), round(%s * nrow(%s)))" % (d, p["proporcion"], d),
              "%s <- %s[%sidx, ]" % (o, d, "-" if p.get("parte", "muestra") == "resto" else "")]
    elif tipo == "guardar":
        L.append("%s <- %s" % (o, d))
    else:
        raise SystemExit(tipo)
    if p.get("guardar") or tipo == "guardar":
        L.append("write.csv(%s, file.path(base, %s), row.names = FALSE)" % (o, r_val(p.get("guardar", nombre + ".csv"))))
    return L


def script_r(plan):
    na = plan.get("na", ["", "NA"])
    L = ["# " + "=" * 76,
         "# TRATAMIENTO DE DATOS: %s" % plan.get("problema", ""),
         "# Objetivo de mineria: %s" % plan.get("objetivo", ""),
         "# Generado desde datos/plan.json (el mismo plan que ejecuta codigo/resolver.py)",
         "# Modismos de SUBSET.pdf: read.csv, subset, df[, c()], indice negativo, which, %in%,",
         "# grepl, complete.cases, is.na, colSums(is.na()), write.csv",
         "# " + "=" * 76,
         'options(width = 200)',
         'args <- commandArgs(trailingOnly = FALSE)',
         'script <- sub("^--file=", "", args[grep("^--file=", args)])',
         'base <- if (length(script)) normalizePath(file.path(dirname(script), "..")) else getwd()',
         'crudo <- read.csv(file.path(base, "datos", %s), check.names = FALSE, na.strings = c(%s),' % (
             r_val(plan["archivo"]), ", ".join(r_val(x) for x in na)),
         '                  stringsAsFactors = FALSE)',
         "names(crudo) <- trimws(names(crudo))" if plan.get("recortar_nombres", True) else "",
         "bitacora <- data.frame(paso = character(0), operacion = character(0), filas = integer(0), columnas = integer(0))",
         "registrar <- function(paso, operacion, d) {",
         "  bitacora[nrow(bitacora) + 1, ] <<- list(paso, operacion, nrow(d), ncol(d))",
         '  cat(sprintf("%-4s %-60s %8d filas %3d columnas\\n", paso, operacion, nrow(d), ncol(d)))',
         "}",
         'cat("Faltantes por columna (colSums(is.na())):\\n"); print(colSums(is.na(crudo)))',
         "P0 <- crudo",
         'registrar("P0", "Carga del archivo original", P0)']
    actual = "P0"
    for i, p in enumerate(plan["pasos"], 1):
        if p["tipo"] == "perfil":
            continue
        nombre = p.get("id", "P%d" % i)
        L.append("# %s. %s" % (nombre, p.get("operacion", p["tipo"])))
        L += r_paso(p, nombre, actual)
        L.append('registrar(%s, %s, %s)' % (r_val(nombre), r_val(p.get("operacion", p["tipo"])), nombre))
        if p["tipo"] != "guardar":
            actual = nombre
        L.append("print(head(%s, 3))" % nombre)
    L += ['write.csv(bitacora, file.path(base, "bitacora_R.csv"), row.names = FALSE)',
          'cat("\\nBitacora:\\n"); print(bitacora, row.names = FALSE)']
    return "\n".join(x for x in L if x is not None) + "\n"


# ---------------------------------------------------------------------------
def escribir_csv(ruta, t):
    with open(ruta, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(t.cols)
        for f in t.filas:
            w.writerow(["NA" if x is NA else x for x in f])


def escribir_bitacora(ruta, bit):
    with open(ruta, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["paso", "operacion", "filas", "columnas"])
        for b in bit:
            w.writerow([b["paso"], b["operacion"], b["filas"], b["columnas"]])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plan", default=os.path.join(BASE, "datos", "plan.json"))
    ap.add_argument("--datos", help="ruta del CSV (por omision, datos/<archivo del plan>)")
    ap.add_argument("--r", help="escribe el script de R en esta ruta")
    ap.add_argument("--salida", default=BASE)
    a = ap.parse_args()
    plan = json.load(open(a.plan, encoding="utf-8"))
    ruta = a.datos or os.path.join(os.path.dirname(a.plan), plan["archivo"])
    if not os.path.exists(ruta):
        alt = os.path.expanduser(os.path.join("~/Downloads", plan["archivo"]))
        ruta = alt if os.path.exists(alt) else ruta
    t = leer(ruta, set(plan.get("na", ["", "NA"])), plan.get("recortar_nombres", True))
    print("TRATAMIENTO: %s" % plan.get("problema", ""))
    print("Objetivo de mineria: %s\n" % plan.get("objetivo", ""))
    tablas = {"P0": t}
    bit = [collections.OrderedDict([("paso", "P0"), ("operacion", "Carga del archivo original"),
                                    ("filas", len(t.filas)), ("columnas", len(t.cols))])]
    perf = None
    print("%-4s %-60s %8s %4s" % ("paso", "operacion", "filas", "col"))
    print("%-4s %-60s %8d %4d" % ("P0", "Carga del archivo original", len(t.filas), len(t.cols)))
    actual = "P0"
    for i, p in enumerate(plan["pasos"], 1):
        if p["tipo"] == "perfil":
            perf = perfil(tablas[p.get("desde", actual)])
            continue
        nombre = p.get("id", "P%d" % i)
        try:
            n = aplicar(p, tablas, actual)
        except SystemExit as e:                 # deja la bitacora parcial para compararla
            escribir_bitacora(os.path.join(a.salida, "bitacora.csv"), bit)
            raise SystemExit("DETENIDO en %s: %s" % (nombre, e))
        tablas[nombre] = n
        if p["tipo"] != "guardar":
            actual = nombre
        fila = collections.OrderedDict([("paso", nombre), ("operacion", p.get("operacion", p["tipo"])),
                                        ("filas", len(n.filas)), ("columnas", len(n.cols))])
        if hasattr(n, "comunes"):
            fila["comunes"] = n.comunes
        bit.append(fila)
        print("%-4s %-60s %8d %4d" % (nombre, fila["operacion"][:60], len(n.filas), len(n.cols)))
        if p.get("guardar"):
            escribir_csv(os.path.join(a.salida, p["guardar"]), n)
    final = tablas[actual]
    traza = collections.OrderedDict([("problema", plan.get("problema", "")), ("objetivo", plan.get("objetivo", "")),
                                     ("archivo", os.path.basename(ruta)), ("bitacora", bit),
                                     ("perfil", perf), ("final", {"filas": len(final.filas), "columnas": final.cols})])
    with open(os.path.join(a.salida, "traza.json"), "w", encoding="utf-8") as fh:
        json.dump(traza, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    escribir_bitacora(os.path.join(a.salida, "bitacora.csv"), bit)
    if perf:
        with open(os.path.join(a.salida, "perfil_columnas.csv"), "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(perf[0]))
            w.writeheader()
            w.writerows(perf)
    if a.r:
        with open(a.r, "w", encoding="utf-8") as fh:
            fh.write(script_r(plan))
        print("\nScript de R: %s" % a.r)
    print("\nEscritos: traza.json, bitacora.csv%s" % (", perfil_columnas.csv" if perf else ""))


if __name__ == "__main__":
    main()
