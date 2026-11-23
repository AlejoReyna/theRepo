#!/usr/bin/env python3
"""Verificación de la regresión múltiple contra R (kit_tsci3/tsci3/regresion.py, fracciones exactas).

Uso: python3 verificar_multiple.py INCISO
Compara: coeficientes del modelo de p.28, predicción con datos nuevos, y_pred de prueba
(reajustando con las mismas filas de entrenamiento), MSE/MAE/R² de prueba y coeficientes del
modelo con factores (número de ficticias = niveles − 1). Escribe traza.json.
"""
import csv
import json
import os
import sys

sys.path.insert(0, "/Users/alexis/theCode/newSkills/TSCI3/kit_tsci3")
from tsci3 import regresion as rg  # noqa: E402

I = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
par = json.load(open(os.path.join(I, "datos", "parametros.json"), encoding="utf-8"))
filas = rg.leer(os.path.join(I, "datos", par["archivo"]))
y = [rg._num(f[par["y"]]) for f in filas]
res, traza = [], {"problema": par.get("problema", "")}


def chk(ok, msg):
    res.append(ok)
    print(("✅ " if ok else "❌ ") + msg)


X, nombres, niv1 = rg.disenar(filas, par["predictores"])
beta, _, rss = rg.mco(X, y)
r_coef = {f["termino"]: (None if f["coef"] == "NA" else float(f["coef"])) for f in csv.DictReader(open(os.path.join(I, "coef_R.csv"), encoding="utf-8"))}
chk(all((b is None and r_coef[n] is None) or (b is not None and r_coef[n] is not None and abs(float(b) - r_coef[n]) <= 1e-9 * max(1, abs(r_coef[n]))) for b, n in zip(beta, nombres)),
    "coeficientes p.28: %s" % ", ".join("%s = %s" % (n, "NA" if b is None else "%.6f" % float(b)) for n, b in zip(nombres, beta)))
nuevo_x, _, _ = rg.disenar([par["nuevos"]], par["predictores"], niveles=niv1)
pred = sum(b * v for b, v in zip(beta, nuevo_x[0]) if b is not None)
rm = next(csv.DictReader(open(os.path.join(I, "multiple_R.csv"), encoding="utf-8")))
chk(abs(float(pred) - float(rm["prediccion"])) < 1e-6, "predicción con %s = %.6f" % (par["nuevos"], float(pred)))
prueba = list(csv.DictReader(open(os.path.join(I, "prueba_R.csv"), encoding="utf-8")))
test_idx = {int(f["fila"]) - 1 for f in prueba}
tr_rows = [i for i in range(len(filas)) if i not in test_idx]
bt, _, _ = rg.mco([X[i] for i in tr_rows], [y[i] for i in tr_rows])
yp = {int(f["fila"]) - 1: sum(b * x for b, x in zip(bt, X[int(f["fila"]) - 1]) if b is not None) for f in prueba}
chk(all(abs(float(yp[int(f["fila"]) - 1]) - float(f["y_pred"])) < 1e-6 for f in prueba), "y_pred de las %d filas de prueba (mismo entrenamiento)" % len(prueba))
yt = [float(y[i]) for i in sorted(test_idx)]
ypp = [float(yp[i]) for i in sorted(test_idx)]
mse = sum((a - b) ** 2 for a, b in zip(yt, ypp)) / len(yt)
mae = sum(abs(a - b) for a, b in zip(yt, ypp)) / len(yt)
mt = sum(yt) / len(yt)
r2 = 1 - sum((a - b) ** 2 for a, b in zip(yt, ypp)) / sum((a - mt) ** 2 for a in yt)
chk(abs(mse - float(rm["MSE"])) < 1e-6 * mse and abs(mae - float(rm["MAE"])) < 1e-9 * mae and abs(r2 - float(rm["R2"])) < 1e-9,
    "prueba: MSE = %.6f, MAE = %.6f, R² = %.6f (p.25-27)" % (mse, mae, r2))
Xf, nf, niv = rg.disenar(filas, par["predictores_factor"], par["factores"])
bf, _, _ = rg.mco(Xf, y)
rf = {f["termino"]: (None if f["coef"] == "NA" else float(f["coef"])) for f in csv.DictReader(open(os.path.join(I, "coef_factor_R.csv"), encoding="utf-8"))}
ok = len(rf) == len(nf) and all((b is None and rf[n] is None) or (b is not None and rf[n] is not None and abs(float(b) - rf[n]) <= 1e-7 * max(1, abs(rf[n])))
                                for b, n in zip(bf, nf))
alias = [n for b, n in zip(bf, nf) if b is None]
print("   alias (NA en R): %s" % alias)
fict = sum(len(niv[f]) - 1 for f in par["factores"])
chk(ok and fict == int(rm["ficticias"]), "modelo con factores: %d coeficientes, %d ficticias = niveles − 1 (%s)" % (
    len(nf), fict, ", ".join("%s: %d niveles" % (f, len(niv[f])) for f in par["factores"])))
traza.update({"coeficientes": dict(zip(nombres, [None if b is None else float(b) for b in beta])), "prediccion": float(pred), "MSE": mse, "MAE": mae, "R2": r2,
              "coeficientes_factor": dict(zip(nf, [None if b is None else float(b) for b in bf])), "alias": alias, "ficticias": fict})
json.dump(traza, open(os.path.join(I, "traza.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("%s %d comprobaciones" % ("✅" if all(res) else "❌", len(res)))
sys.exit(0 if all(res) else 1)
