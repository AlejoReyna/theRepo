#!/usr/bin/env python3
"""kit_tsci3: oráculos y utilidades de las skills tsci3-*.

Comandos:
  arbol-oraculo DATOS.csv TRAZA.json [--clase C] [--vacio V]
      Recalcula el árbol de mínima entropía por otro camino y lo compara con la traza
      (R1, R2, cifras de cada nodo, hojas y resumen). Sale con 1 si algo difiere.
  kmeans-oraculo DATOS.csv TRAZA.json
      Recalcula el k-means del ejercicio de clase (min-max, centroides mín/máx, regla T7)
      por otro camino y compara cada iteración. Sale con 1 si algo difiere.
  kmedoides-oraculo DATOS.csv TRAZA.json
      Criterio de clase (registro más cercano a C'), DM0/DM1, costo y silueta; PAM: costo de
      los medoides y que ningún intercambio lo mejore. Sale con 1 si algo difiere.
  apriori-oraculo DATOS.csv TRAZA.json
      Cuenta cada subconjunto de cada transacción, arma las reglas y las compara con la traza.
  secuencias-oraculo DATOS_SPMF TRAZA.json
      Crecimiento de patrones con contención voraz; compara patrones y soportes con la traza.
  episodios-oraculo DATOS.csv TRAZA.json
      Ventana deslizante por caso; compara pares y soporte global y por distrito.
  minimos-oraculo DATOS.csv TRAZA.json
      Recta por la forma centrada en fracciones; mutante (Σx)².
  procesos-oraculo REGEVEN.xlsx TRAZA.json
      Recalcula trazas, variantes, |x>y| y dependencias; revisa la red de la traza
      (alcanzabilidad, segura, sólida, WF, libre elección, aceptación de cada traza y
      lenguaje red = lenguaje del árbol). Sale con 1 si algo difiere.

Solo biblioteca estándar.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _informe(resultados):
    for ok, msg in resultados:
        print(("✅ " if ok else "❌ ") + msg)
    malos = sum(1 for ok, _ in resultados if not ok)
    print("RESULTADO: %s" % ("todo coincide" if not malos else "%d comprobaciones fallaron" % malos))
    return 1 if malos else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("arbol-oraculo")
    a.add_argument("datos")
    a.add_argument("traza")
    a.add_argument("--clase")
    a.add_argument("--vacio")
    p = sub.add_parser("procesos-oraculo")
    p.add_argument("datos")
    p.add_argument("traza")
    k = sub.add_parser("kmeans-oraculo")
    k.add_argument("datos")
    k.add_argument("traza")
    km = sub.add_parser("kmedoides-oraculo")
    km.add_argument("datos")
    km.add_argument("traza")
    apr = sub.add_parser("apriori-oraculo")
    apr.add_argument("datos")
    apr.add_argument("traza")
    sq = sub.add_parser("secuencias-oraculo")
    sq.add_argument("datos")
    sq.add_argument("traza")
    ep = sub.add_parser("episodios-oraculo")
    ep.add_argument("datos")
    ep.add_argument("traza")
    mc = sub.add_parser("minimos-oraculo")
    mc.add_argument("datos")
    mc.add_argument("traza")
    args = ap.parse_args(argv)
    if args.cmd == "arbol-oraculo":
        from tsci3.oraculos import arbol
        return _informe(arbol.verificar(args.datos, args.traza, args.clase, args.vacio))
    if args.cmd == "procesos-oraculo":
        from tsci3.oraculos import procesos
        return _informe(procesos.verificar(args.datos, args.traza))
    if args.cmd == "kmeans-oraculo":
        from tsci3.oraculos import kmeans
        return _informe(kmeans.verificar(args.datos, args.traza))
    if args.cmd == "kmedoides-oraculo":
        from tsci3.oraculos import kmedoides
        return _informe(kmedoides.verificar(args.datos, args.traza))
    if args.cmd == "apriori-oraculo":
        from tsci3.oraculos import apriori
        return _informe(apriori.verificar(args.datos, args.traza))
    if args.cmd == "secuencias-oraculo":
        from tsci3.oraculos import secuencias
        return _informe(secuencias.verificar(args.datos, args.traza))
    if args.cmd == "episodios-oraculo":
        from tsci3.oraculos import episodios
        return _informe(episodios.verificar(args.datos, args.traza))
    if args.cmd == "minimos-oraculo":
        from tsci3.oraculos import minimos
        return _informe(minimos.verificar(args.datos, args.traza))
    return 2


if __name__ == "__main__":
    sys.exit(main())
