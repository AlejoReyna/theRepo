#!/usr/bin/env python3
"""Verificación del bosque aleatorio contra R (oráculo kit_tsci3/tsci3/oraculos/bosque.py).

Uso: python3 verificar_bosque.py INCISO
Comprueba: tamaños de la partición 80/20; muestras bootstrap con reemplazo de tamaño n (inbag);
mtry = ⌊p/3⌋; cada observación de prueba recorre cada árbol hasta la hoja que R predice; cada hoja
es el promedio de su muestra bootstrap; la predicción del bosque es el promedio de los árboles
(p.54); RMSE, MAE y R² (p.55) recalculados; IncNodePurity recalculada; reproducibilidad con la
misma semilla. Mutante: tomar la mediana de los árboles en lugar del promedio. Escribe traza.json.
"""
import csv
import json
import math
import os
import statistics
import sys

sys.path.insert(0, "/Users/alexis/theCode/newSkills/TSCI3/kit_tsci3")
from tsci3.oraculos import bosque as bq  # noqa: E402

I = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
par = json.load(open(os.path.join(I, "datos", "parametros.json"), encoding="utf-8"))
datos = list(csv.DictReader(open(os.path.join(I, "datos", par["archivo"]), newline="", encoding="utf-8-sig")))
rs = next(csv.DictReader(open(os.path.join(I, "resumen_R.csv"), encoding="utf-8")))
variables = rs["variables"].split("|")
# T26: los doubles tal como los leyó R (read.csv difiere en 1 ulp de Python en algunos valores)
xr = list(csv.DictReader(open(os.path.join(I, "X_R.csv"), encoding="utf-8")))
X = [[float(r[v]) for v in variables] for r in xr]
ulp = sum(1 for a, b in zip(xr, datos) for v in variables if float(a[v]) != float(b[v]))
y = [float(r[par["y"]]) for r in datos]
res = []
print("   T26: %d valores de %s difieren en 1 ulp entre read.csv de R y float() de Python; se usan los de R" % (ulp, par["archivo"]))


def chk(ok, msg):
    res.append(ok)
    print(("✅ " if ok else "❌ ") + msg)


def leer(n):
    return list(csv.DictReader(open(os.path.join(I, n), encoding="utf-8")))


tr = [int(r["fila"]) - 1 for r in leer("train_index_R.csv")]
pr = leer("predicciones_R.csv")
te = [int(r["fila"]) - 1 for r in pr]
ntree = int(rs["ntree"])
chk(len(tr) == int(0.8 * len(X)) and len(te) == len(X) - len(tr) and not set(tr) & set(te),
    "p.55: entrenamiento %d (80 %%) y prueba %d, sin filas en común" % (len(tr), len(te)))
inbag = [[int(float(v)) for v in r.values()] for r in leer("inbag_R.csv")]   # filas = entrenamiento, columnas = árboles
tam = [sum(fila[t] for fila in inbag) for t in range(ntree)]
oob = sum(sum(1 for fila in inbag if fila[t] == 0) for t in range(ntree)) / (ntree * len(tr))
rep = sum(1 for t in range(ntree) for fila in inbag if fila[t] > 1)
chk(all(s == len(tr) for s in tam) and rep > 0,
    "p.54: cada árbol usa una muestra con reemplazo de %d filas; %.1f %% de filas fuera de la bolsa (≈ (1 − 1/n)^n = %.1f %%)" % (
        len(tr), 100 * oob, 100 * (1 - 1 / len(tr)) ** len(tr)))
chk(int(rs["mtry"]) == max(1, len(variables) // 3), "p.54: variables al azar en cada nodo: mtry = ⌊%d/3⌋ = %s" % (len(variables), rs["mtry"]))

arboles = bq.leer_arboles(leer("arboles_R.csv"))
ok_rec, ok_media = 0, 0
for r, i in zip(pr, te):
    ind = [float(r["arbol%d" % t]) for t in range(1, ntree + 1)]
    ok_rec += all(abs(bq.predecir(arboles[t], X[i]) - ind[t - 1]) <= 1e-6 * max(1, abs(ind[t - 1])) for t in range(1, ntree + 1))
    ok_media += abs(sum(ind) / ntree - float(r["y_pred"])) <= 1e-6 * abs(float(r["y_pred"]))
chk(ok_rec == len(pr), "recorrido: %d × %d (observación, árbol) llegan a la hoja que predice R (x ≤ corte → izquierda)" % (len(pr), ntree))
chk(ok_media == len(pr), "p.54: la predicción del bosque es el promedio de los %d árboles en las %d observaciones de prueba" % (ntree, len(pr)))

Xtr, ytr = [X[i] for i in tr], [y[i] for i in tr]
hojas_ok, hojas, vacias, pureza = 0, 0, [], [0.0] * len(variables)
for t in range(1, ntree + 1):
    a = arboles[t]
    est = bq.estadisticos_nodo(a, Xtr, ytr, [fila[t - 1] for fila in inbag])
    padre = {}
    for n, nd in enumerate(a, 1):
        if nd["estado"] != -1:
            padre[nd["izq"]], padre[nd["der"]] = n, n
    for n, nd in enumerate(a, 1):
        e = est[n - 1]
        if nd["estado"] == -1:
            hojas += 1
            if e[0] > 0:
                hojas_ok += abs(e[1] / e[0] - nd["pred"]) <= 1e-6 * max(1, abs(nd["pred"]))
            else:                                   # T27: rama vacía de un nodo con y constante
                ep = est[padre[n] - 1]
                pa = a[padre[n] - 1]
                hermano = pa["der"] if pa["izq"] == n else pa["izq"]
                ok = ep[0] > 0 and bq.rss(ep) <= 1e-9 * ep[2] and est[hermano - 1][0] == ep[0]
                hojas_ok += ok
                vacias.append((t, n, variables[pa["var"] - 1], pa["corte"], nd["pred"], ep[1] / ep[0]))
        else:
            pureza[nd["var"] - 1] += bq.rss(e) - bq.rss(est[nd["izq"] - 1]) - bq.rss(est[nd["der"] - 1])
for v in vacias[:4]:
    print("   T27: árbol %d, hoja %d: rama vacía de «%s ≤ %g» con predicción sobrante %.0f; el padre tiene y constante = %.0f" % v)
chk(hojas_ok == hojas, "cada una de las %d hojas predice el promedio de y de su muestra bootstrap (con repeticiones), salvo %d ramas vacías de nodos con y constante (T27)" % (hojas, len(vacias)))
imp = {r["variable"]: r for r in leer("importancia_R.csv")}
pureza = [p / ntree for p in pureza]
chk(all(abs(p - float(imp[v]["IncNodePurity"])) <= 1e-6 * float(imp[v]["IncNodePurity"]) for v, p in zip(variables, pureza)),
    "IncNodePurity = Σ disminuciones de RSS por variable / ntree = R (las 3 mayores: %s)" % ", ".join(
        "%s %.4g" % (v, p) for v, p in sorted(zip(variables, pureza), key=lambda z: -z[1])[:3]))

yt = [float(r["y"]) for r in pr]
yp = [float(r["y_pred"]) for r in pr]
rmse = math.sqrt(sum((a - b) ** 2 for a, b in zip(yt, yp)) / len(yt))
mae = sum(abs(a - b) for a, b in zip(yt, yp)) / len(yt)
mt = sum(yt) / len(yt)
r2 = 1 - sum((a - b) ** 2 for a, b in zip(yt, yp)) / sum((a - mt) ** 2 for a in yt)
chk(all(abs(a - float(rs[k])) <= 1e-9 * abs(a) for a, k in ((rmse, "RMSE"), (mae, "MAE"), (r2, "R2"))) and all(y[i] == v for i, v in zip(te, yt)),
    "p.55: RMSE = %.4f, MAE = %.4f, R² = %.6f recalculados con y_test y y_pred" % (rmse, mae, r2))
chk(rs["reproducible"] == "TRUE", "T15: con set.seed(42) de nuevo, R da las mismas predicciones")

med = [statistics.median(float(r["arbol%d" % t]) for t in range(1, ntree + 1)) for r in pr]
rm_med = math.sqrt(sum((a - b) ** 2 for a, b in zip(yt, med)) / len(yt))
chk(any(abs(a - b) > 1e-6 * abs(b) for a, b in zip(med, yp)), "mutante (mediana de los árboles): RMSE %.4f ≠ %.4f, se detecta" % (rm_med, rmse))

o = par.get("observacion_excel", 1) - 1
traza = {"problema": par.get("problema", ""), "variables": variables, "n_train": len(tr), "n_test": len(te), "mtry": int(rs["mtry"]),
         "ntree": ntree, "RMSE": rmse, "MAE": mae, "R2": r2, "oob": oob, "IncNodePurity": dict(zip(variables, pureza)),
         "IncMSE": {v: float(imp[v]["IncMSE"]) for v in variables}, "ramas_vacias_T27": len(vacias), "ulp_T26": ulp,
         "observacion": {"fila": te[o] + 1, "y": yt[o], "y_pred": yp[o], "arboles": [float(pr[o]["arbol%d" % t]) for t in range(1, ntree + 1)]}}
json.dump(traza, open(os.path.join(I, "traza.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("%s %d comprobaciones" % ("✅" if all(res) else "❌", len(res)))
sys.exit(0 if all(res) else 1)
