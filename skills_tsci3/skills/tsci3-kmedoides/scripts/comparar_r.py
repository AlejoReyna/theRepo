#!/usr/bin/env python3
"""Comparación 2 del contrato para k-medoides: Python contra R.

Lee INCISO/traza.json, medoides_R.csv y kmedoides_R.csv (los escribe codigo/script.R):
medoides de clase y de PAM (registros), grupos y silueta de cada registro (cluster::silhouette).
Uso: python3 comparar_r.py INCISO
"""
import csv
import json
import os
import sys


def main():
    I = sys.argv[1]
    tr = json.load(open(os.path.join(I, "traza.json"), encoding="utf-8"))
    med = next(csv.DictReader(open(os.path.join(I, "medoides_R.csv"), encoding="utf-8")))
    filas = list(csv.DictReader(open(os.path.join(I, "kmedoides_R.csv"), encoding="utf-8")))
    malos = []
    c = tr["clase"]
    if (c["M0_registro"], c["M1_registro"]) != (int(med["M0"]), int(med["M1"])):
        malos.append("medoides de clase: Python %s, R %s" % ((c["M0_registro"], c["M1_registro"]), (med["M0"], med["M1"])))
    gr = [int(f["grupo_clase"]) - 1 for f in filas]
    if gr != c["grupo"]:
        malos.append("grupos del criterio de clase")
    if any(abs(float(f["sil_clase"]) - s) > 1e-9 for f, s in zip(filas, c["silueta"])):
        malos.append("silueta del criterio de clase")
    if "pam" in tr:
        p = tr["pam"]
        if sorted(p["medoides_registro"]) != sorted([int(med["pam_medoide_1"]), int(med["pam_medoide_2"])]):
            malos.append("medoides PAM: Python %s, R %s" % (p["medoides_registro"], [med["pam_medoide_1"], med["pam_medoide_2"]]))
        # R numera los grupos por orden de medoide; se comparan como particiones
        part_py = {frozenset(i for i, g in enumerate(p["grupo"]) if g == k) for k in (0, 1)}
        part_r = {frozenset(i for i, f in enumerate(filas) if f["grupo_pam"] == k) for k in ("1", "2")}
        if part_py != part_r:
            malos.append("grupos PAM")
        elif any(abs(float(f["sil_pam"]) - s) > 1e-9 for f, s in zip(filas, p["silueta"])):
            malos.append("silueta PAM")
    for m in malos:
        print("❌", m)
    print("%s k-medoides: Python contra R (medoides, grupos y silueta de %d registros), %d diferencias" % (
        "✅" if not malos else "❌", len(filas), len(malos)))
    return 1 if malos else 0


if __name__ == "__main__":
    sys.exit(main())
