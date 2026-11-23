#!/usr/bin/env python3
"""Verificación de KNN contra R (oráculo kit_tsci3/tsci3/oraculos/knn.py).

Uso: python3 verificar_knn.py INCISO
Con los índices de entrenamiento y los pliegues exportados por R (set.seed(42) no se reproduce en
Python): predicciones de class::knn con k de p.48 (empates de votos listados, T15) y su exactitud;
validación cruzada de p.53 pliegue por pliegue para cada k; mejor k; WCSS de p.46 recalculado con
los grupos de R y el codo (p.47). Mutante: con normalización min-max (T5) las predicciones cambian.
Escribe traza.json con el detalle del punto que el Excel desarrolla.
"""
import csv
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, "/Users/alexis/theCode/newSkills/TSCI3/kit_tsci3")
from tsci3.oraculos import knn as kn  # noqa: E402

I = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
par = json.load(open(os.path.join(I, "datos", "parametros.json"), encoding="utf-8"))
datos = list(csv.DictReader(open(os.path.join(I, "datos", par["archivo"]), newline="", encoding="utf-8-sig")))
cols, K = par["columnas"], par["k"]
col_y = par.get("y") or ("precio" if "precio" in datos[0] else [c for c in datos[0] if c not in cols][0])
X = [[float(r[c]) for c in cols] for r in datos]
precio = [float(r[col_y]) for r in datos]
s = sorted(precio)
med = (s[len(s) // 2 - 1] + s[len(s) // 2]) / 2
clase = ["alto" if v >= med else "bajo" for v in precio]          # p.48 usa ≥
res = []


def chk(ok, msg):
    res.append(ok)
    print(("✅ " if ok else "❌ ") + msg)


def leer(n):
    return list(csv.DictReader(open(os.path.join(I, n), encoding="utf-8")))


rs = leer("resumen_R.csv")[0]
tr_idx = [int(r["fila"]) - 1 for r in leer("train_index_R.csv")]
te_idx = [i for i in range(len(X)) if i not in set(tr_idx)]
prop_esp = par.get("prop_train")
ok_tam = (len(tr_idx) == int(prop_esp * len(X))) if prop_esp else (len(tr_idx) in (int(0.75 * len(X)), int(0.70 * len(X)), int(0.80 * len(X))))
chk(float(rs["mediana"]) == med and ok_tam,
    "p.48: mediana %.2f (alto si %s ≥ mediana: %d); entrenamiento %d, prueba %d" % (med, col_y, clase.count("alto"), len(tr_idx), len(te_idx)))
Xtr, ctr = [X[i] for i in tr_idx], [clase[i] for i in tr_idx]
pr = leer("predicciones_R.csv")
iguales, empates, detalle = 0, [], []
for r in pr:
    i = int(r["fila"]) - 1
    g, votos, idx, gan = kn.votar(X[i], Xtr, ctr, K)
    if g is None:
        empates.append(i + 1)
        iguales += r["pred"] in gan
    else:
        iguales += g == r["pred"]
    detalle.append((i, g, votos, idx))
chk(iguales == len(pr), "knn(k = %d): %d de %d predicciones = R (%d empates de votos resueltos al azar por R: %s)" % (
    K, iguales, len(pr), len(empates), empates[:10]))
acc = sum(1 for r in pr if r["pred"] == r["real"]) / len(pr)
chk(abs(acc - float(rs["exactitud_k3"])) < 1e-12 and all(r["real"] == clase[int(r["fila"]) - 1] for r in pr),
    "exactitud en prueba = %.6f = caret (matriz en tsci3-matriz-confusion)" % acc)

# ---- p.53: validación cruzada con los pliegues de caret
cvp = leer("cv_pred_R.csv")
por = defaultdict(list)
for r in cvp:
    por[(int(r["k"]), r["fold"])].append(r)
cvr = {int(r["k"]): float(r["Accuracy"]) for r in leer("cv_resultados_R.csv")}
tabla, ok_cv, emp_cv = {}, True, 0
for k in par["k_valores"]:
    accs = []
    for (kk, f), filas in sorted(por.items()):
        if kk != k:
            continue
        fuera = {int(r["fila_train"]) - 1 for r in filas}
        dentro = [j for j in range(len(tr_idx)) if j not in fuera]
        Xd, cd = [Xtr[j] for j in dentro], [ctr[j] for j in dentro]
        bien = 0
        for r in filas:
            j = int(r["fila_train"]) - 1
            g, _, _, gan = kn.votar(Xtr[j], Xd, cd, k)
            if g is None:
                emp_cv += 1
                ok_cv &= r["pred"] in gan
            else:
                ok_cv &= g == r["pred"]
            bien += r["pred"] == r["obs"]
        accs.append(bien / len(filas))
    tabla[k] = sum(accs) / len(accs)
    ok_cv &= abs(tabla[k] - cvr[k]) < 1e-12
print("   k : " + "  ".join("%2d → %.4f" % (k, v) for k, v in tabla.items()))
chk(ok_cv, "p.53: 10 pliegues × %d valores de k: cada predicción = oráculo (%d empates de votos) y exactitud media = caret" % (len(tabla), emp_cv))
best = max(tabla, key=lambda k: (tabla[k], -k))
chk(best == int(rs["best_k"]), "mejor k = %d (exactitud %.6f)" % (best, tabla[best]))

# ---- p.45-47: WCSS y codo
wr = leer("wcss_R.csv")
gr = leer("wcss_grupos_R.csv")
w = [kn.wcss(X, [r["V%d" % k] for r in gr]) for k in range(1, len(wr) + 1)]
chk(all(abs(a - float(r["WCSS"])) <= 1e-9 * a for a, r in zip(w, wr)), "p.46: WCSS = Σ‖x − μ‖² recalculado con los grupos de R para k = 1..%d" % len(w))
seg = {k: (w[k - 2] - w[k - 1]) - (w[k - 1] - w[k]) for k in range(2, len(w))}
codo = max(seg, key=seg.get)
print("   WCSS: " + ", ".join("%d: %.4g" % (k, v) for k, v in enumerate(w, 1)))
print("   codo (máxima segunda diferencia, p.47): k = %d; no monótono en k = %s (óptimo local de kmeans)" % (
    codo, [k + 1 for k in range(1, len(w)) if w[k] > w[k - 1]]))

# ---- Mutante: normalización min-max (T5)
mn = [min(c) for c in zip(*X)]
mx = [max(c) for c in zip(*X)]
Xn = [[(a - lo) / (hi - lo) for a, lo, hi in zip(x, mn, mx)] for x in X]
Xntr = [Xn[i] for i in tr_idx]
cambia = sum(1 for r in pr if kn.votar(Xn[int(r["fila"]) - 1], Xntr, ctr, K)[0] not in (r["pred"], None))
chk(cambia > 0, "mutante con min-max (T5): %d de %d predicciones cambian, se detecta" % (cambia, len(pr)))

# Detalle del punto de prueba que desarrolla el Excel
p = par.get("punto_excel", 1) - 1
i, g, votos, idx = detalle[p]
traza = {"problema": par.get("problema", ""), "mediana": med, "train_index": [t + 1 for t in tr_idx], "k": K,
         "exactitud": acc, "empates_prueba": empates, "cv": tabla, "best_k": best, "wcss": w, "codo": codo,
         "punto": {"fila": i + 1, "x": X[i], "real": clase[i], "pred": g, "votos": votos,
                   "vecinos": [{"fila": tr_idx[j] + 1, "clase": ctr[j], "d": kn.distancias(X[i], [Xtr[j]])[0]} for j in idx]}}
json.dump(traza, open(os.path.join(I, "traza.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("   punto de prueba fila %d: vecinos %s → %s" % (i + 1, [(v["fila"], v["clase"], round(v["d"], 3)) for v in traza["punto"]["vecinos"]], g))
print("%s %d comprobaciones" % ("✅" if all(res) else "❌", len(res)))
sys.exit(0 if all(res) else 1)
