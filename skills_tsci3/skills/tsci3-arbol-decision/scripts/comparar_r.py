#!/usr/bin/env python3
"""Comparación 2 del contrato (traza contra R) y tabla de comparación de árboles.

Lee INCISO/traza.json, INCISO/id3_R.csv, INCISO/comparacion_R.csv y INCISO/predicciones_R.csv
(los escribe codigo/script.R) y:
  1. compara E(A) y ganancia de cada candidato de cada nodo: ID3 de Python contra ID3 de R;
  2. escribe INCISO/comparacion.csv: fila ID3 (de la traza) + filas de R;
  3. calcula el porcentaje de predicciones iguales entre ID3 y cada árbol de R.
Sale con 1 si la parte 1 encuentra diferencias. Solo biblioteca estándar.

Uso: python3 comparar_r.py INCISO [--tol 1e-9]
"""
import argparse
import csv
import json
import os
import sys


def ruta_txt(ruta):
    return " y ".join("%s = %s" % (a, v) for a, v in ruta) or "raiz"


def predicciones_id3(traza, ruta_csv):
    d = traza["datos"]
    with open(ruta_csv, newline="", encoding="utf-8-sig") as fh:
        filas = list(csv.DictReader(fh))
    for f in filas:
        for a in d["atributos"]:
            if f[a] is None or f[a].strip() == "":
                f[a] = d["vacio"]
    hojas = [(h["ruta"], h["clase"]) for h in traza["hojas"]]
    pred = []
    for f in filas:
        clase = None
        for ruta, c in hojas:
            if all(f[a] == v for a, v in ruta):
                clase = c
                break
        pred.append(clase)
    return filas, pred


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inciso")
    ap.add_argument("--tol", type=float, default=1e-9)
    a = ap.parse_args()
    I = a.inciso
    with open(os.path.join(I, "traza.json"), encoding="utf-8") as fh:
        tr = json.load(fh)
    malos = 0

    # 1. ID3 de Python contra ID3 de R
    py = {}
    for niv in tr["niveles"]:
        for nd in niv["nodos"]:
            for c in nd["candidatos"]:
                py[(niv["nivel"], ruta_txt(nd["ruta"]), c["atributo"])] = (c["E"], c["ganancia"])
    with open(os.path.join(I, "id3_R.csv"), newline="", encoding="utf-8") as fh:
        rr = {(int(f["nivel"]), f["ruta"], f["atributo"]): (float(f["E"]), float(f["ganancia"]))
              for f in csv.DictReader(fh)}
    if set(py) != set(rr):
        malos += 1
        print("❌ nodos o candidatos distintos: solo Python %s; solo R %s" % (
            sorted(set(py) - set(rr))[:3], sorted(set(rr) - set(py))[:3]))
    difs = [(k, py[k], rr[k]) for k in set(py) & set(rr)
            if abs(py[k][0] - rr[k][0]) > a.tol or abs(py[k][1] - rr[k][1]) > a.tol]
    for k, p, r in difs[:5]:
        print("❌ %s: Python E=%.9f g=%.9f; R E=%.9f g=%.9f" % (k, p[0], p[1], r[0], r[1]))
    malos += len(difs)
    print("%s ID3 Python contra ID3 R: %d candidatos comparados, %d diferencias (tol %g)" % (
        "✅" if not difs and set(py) == set(rr) else "❌", len(set(py) & set(rr)), len(difs), a.tol))

    # 2. tabla de comparación
    d = tr["datos"]
    filas, pred = predicciones_id3(tr, os.path.join(I, "datos", d["archivo"]))
    res = tr["resumen"]
    enc = ["Modelo", "Criterio", "Raiz", "Hojas", "Profundidad", "Clases_que_predice", "Exactitud",
           "Coincidencia_con_ID3"]
    tabla = [enc, ["ID3 (mínima entropía)", "menor E(A) (ganancia de información), una rama por valor",
                   res["raiz"], res["hojas"], res["profundidad"],
                   "; ".join(sorted(set(pred))), "%.4f" % res["exactitud"], "1.0000"]]
    with open(os.path.join(I, "predicciones_R.csv"), newline="", encoding="utf-8") as fh:
        pr = list(csv.DictReader(fh))
    if len(pr) != len(pred):
        print("❌ predicciones_R.csv tiene %d filas y los datos %d" % (len(pr), len(pred)))
        malos += 1
    col = {"rpart": "rpart", "rpart (information)": "rpart_information", "ctree": "ctree"}
    with open(os.path.join(I, "comparacion_R.csv"), newline="", encoding="utf-8") as fh:
        for f in csv.DictReader(fh):
            c = col.get(f["Modelo"])
            coinc = sum(1 for p, q in zip(pred, pr) if p == q[c]) / len(pred) if c else float("nan")
            tabla.append([f["Modelo"], f["Criterio"], f["Raiz"], f["Hojas"], f["Profundidad"],
                          f["Clases_que_predice"], "%.4f" % float(f["Exactitud"]), "%.4f" % coinc])
    with open(os.path.join(I, "comparacion.csv"), "w", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerows(tabla)
    for t in tabla:
        print(" | ".join(str(x) for x in t))
    return 1 if malos else 0


if __name__ == "__main__":
    sys.exit(main())
