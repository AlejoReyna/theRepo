#!/usr/bin/env python3
"""Comprueba las citas de un documento del proyecto TSCI3.

Para cada cita con prefijo (`OD/…`, `DL/…`, `MC/…`, `EG/…`, `EF/…`, `EX-MC`,
`RESP`, `EJ26-14`, `AD25-11`, `EJ25-6`) verifica que:
  * la ruta exista;
  * cada «p.N» que la sigue no exceda las páginas del PDF;
  * cada «l.N» que la sigue no exceda las líneas del archivo de texto.

Uso:  .venv/bin/python herramientas/comprobar_citas.py DOC.md [DOC2.md ...]
Sale con código 1 si hay rutas inexistentes o páginas/líneas fuera de rango.
"""
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = os.path.join(RAIZ, "fuentes")
PREFIJOS = {
    "OD/": os.path.join(F, "OD"),
    "DL/": os.path.join(F, "DL"),
    "MC/": os.path.join(F, "MC"),
    "EJ25/": os.path.join(F, "EJ25"),
    "AD25/": os.path.join(F, "AD25"),
    "EJ26/": os.path.join(F, "EJ26"),
    "AD24/": os.path.join(F, "AD24"),
    "EG/": os.path.join(os.path.dirname(RAIZ), "Endgame"),
    "EF/": os.path.join(RAIZ, "plantilla_entrega"),
}
ALIAS = {
    "EX-MC": os.path.join(F, "DL", "AD26 TSCI3 MC (Práctica).pdf"),
    "RESP": os.path.join(F, "MC", "Respuestas_MC_TSCI3_1851265.pdf"),
    "DL/1851265_MC_TSCI3/": os.path.join(F, "MC"),
}
ARTICULO = {
    "EJ26": lambda n: os.path.join(F, "EJ26", f"EJ26 TSCI3 {int(n)}.pdf"),
    "AD25": lambda n: os.path.join(F, "AD25", f"tsci3ad25 {int(n):02d}.pdf"),
    "EJ25": lambda n: os.path.join(F, "EJ25", f"tsci3 {int(n)}.pdf"),
}

CITA = re.compile(r"`([^`]+)`")
NUMS = re.compile(r"(\d+)(?:\s?[–-]\s?(\d+))?")


def resolver(token):
    """Devuelve la ruta local de una cita o None si no es una cita de fuente."""
    if "…" in token or "<" in token:
        return None
    if token in ALIAS:
        return ALIAS[token]
    m = re.fullmatch(r"(EJ26|AD25|EJ25)-(\d+)", token)
    if m:
        return ARTICULO[m.group(1)](m.group(2))
    for p, base in PREFIJOS.items():
        if token.startswith(p):
            return os.path.join(base, token[len(p):])
    return None


def numeros_tras(texto, marca):
    """Números de la lista «p.3–6», «p.1, 5, 11 y 12» o «p.1, p.4» que sigue a la cita."""
    n = r"\d+(?:\s?[–-]\s?\d+)?"
    lista = re.match(r"[\s,]*(?:\([^)]*\)\s*)?" + re.escape(marca) + r"\s?(" + n
                     + r"(?:\s*(?:,|y)\s*(?:" + re.escape(marca) + r"\s?)?" + n + r"(?![\d\s]*\d{3}))*)", texto)
    if not lista:
        return []
    return [(int(a), int(b) if b else int(a)) for a, b in NUMS.findall(lista.group(1))]


_paginas = {}


def paginas(ruta):
    if ruta not in _paginas:
        try:
            import pymupdf
            with pymupdf.open(ruta) as d:
                _paginas[ruta] = d.page_count
        except Exception:
            _paginas[ruta] = None
    return _paginas[ruta]


def lineas(ruta):
    try:
        with open(ruta, encoding="utf-8", errors="replace") as fh:
            return sum(1 for _ in fh)
    except Exception:
        return None


def revisar(doc):
    errores, revisadas = [], 0
    with open(doc, encoding="utf-8") as fh:
        for nl, linea in enumerate(fh, 1):
            for m in CITA.finditer(linea):
                ruta = resolver(m.group(1))
                if ruta is None:
                    continue
                revisadas += 1
                if "*" in ruta:
                    import glob
                    if not glob.glob(ruta):
                        errores.append(f"{doc}:{nl}: ningún archivo con {m.group(1)}")
                    continue
                if not os.path.exists(ruta):
                    errores.append(f"{doc}:{nl}: no existe {m.group(1)}")
                    continue
                despues = linea[m.end():m.end() + 160]
                if ruta.lower().endswith(".pdf"):
                    total = paginas(ruta)
                    for a, b in numeros_tras(despues, "p."):
                        if total is not None and max(a, b) > total:
                            errores.append(f"{doc}:{nl}: {m.group(1)} p.{a}-{b} excede {total} páginas")
                elif os.path.isfile(ruta):
                    pares = numeros_tras(despues, "l.")
                    if pares:
                        total = lineas(ruta)
                        for a, b in pares:
                            if total is not None and max(a, b) > total:
                                errores.append(f"{doc}:{nl}: {m.group(1)} l.{a}-{b} excede {total} líneas")
    return errores, revisadas


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    total_err, total_rev = [], 0
    for doc in argv:
        e, r = revisar(doc)
        total_err += e
        total_rev += r
    for e in total_err:
        print("ERROR", e)
    print(f"citas revisadas: {total_rev}; errores: {len(total_err)}")
    return 1 if total_err else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
