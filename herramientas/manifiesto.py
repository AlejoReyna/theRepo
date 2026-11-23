#!/usr/bin/env python3
"""Escribe (o comprueba) fuentes/MANIFIESTO.tsv: ruta relativa, bytes y SHA-256.

Uso:
    python3 herramientas/manifiesto.py            # escribe el manifiesto
    python3 herramientas/manifiesto.py --comprobar  # sale con 1 si una copia cambió
"""
import hashlib
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = os.path.join(RAIZ, "fuentes")
MAN = os.path.join(F, "MANIFIESTO.tsv")


def filas():
    for base, dirs, archivos in os.walk(F):
        dirs.sort()
        for a in sorted(archivos):
            if a.startswith(".") or a == "MANIFIESTO.tsv":
                continue
            p = os.path.join(base, a)
            h = hashlib.sha256()
            with open(p, "rb") as fh:
                for bloque in iter(lambda: fh.read(1 << 20), b""):
                    h.update(bloque)
            yield os.path.relpath(p, F), os.path.getsize(p), h.hexdigest()


def main():
    actuales = list(filas())
    if "--comprobar" in sys.argv:
        esperado = {}
        with open(MAN, encoding="utf-8") as fh:
            next(fh)
            for l in fh:
                r, b, h = l.rstrip("\n").split("\t")
                esperado[r] = h
        mal = [r for r, _, h in actuales if esperado.get(r) != h]
        faltan = sorted(set(esperado) - {r for r, _, _ in actuales})
        for r in mal:
            print("CAMBIO", r)
        for r in faltan:
            print("FALTA", r)
        print(f"{len(actuales)} archivos; cambios {len(mal)}; faltan {len(faltan)}")
        return 1 if (mal or faltan) else 0
    with open(MAN, "w", encoding="utf-8") as fh:
        fh.write("ruta\tbytes\tsha256\n")
        for r, b, h in actuales:
            fh.write(f"{r}\t{b}\t{h}\n")
    print(f"{len(actuales)} archivos en {MAN}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
