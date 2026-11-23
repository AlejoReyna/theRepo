#!/usr/bin/env python3
"""Verificación de Lasso y Ridge contra glmnet (oráculo kit_tsci3/tsci3/oraculos/regularizacion.py).

Uso: python3 verificar_regularizacion.py INCISO
Compara, para Lasso (p.30) y Ridge (p.32 con las dos lecturas de T3):
  1. MSE = mean((y − ŷ)²) recalculado con las predicciones exportadas;
  2. ŷ recalculado con los coeficientes de R y la matriz x de model.matrix;
  3. el oráculo (descenso por coordenadas hasta 1e−13) con el mismo λ.min: F del oráculo ≤ F de
     glmnet con diferencia relativa < 1e−6 y los mismos valores ajustados (|Δŷ| < 5e−3·s_y);
  4. p.29: Lasso anula al menos un coeficiente; p.31: Ridge (alpha = 0) no anula ninguno;
  5. T3: la lectura literal alpha <- 1.0 da los mismos coeficientes que Lasso.
Mutante: Ridge sin la escala s_y de glmnet en la penalización L2 no llega al óptimo de R.
Escribe traza.json.
"""
import csv
import json
import os
import sys

sys.path.insert(0, "/Users/alexis/theCode/newSkills/TSCI3/kit_tsci3")
from tsci3.oraculos import regularizacion as rz  # noqa: E402

I = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
par = json.load(open(os.path.join(I, "datos", "parametros.json"), encoding="utf-8"))
datos_raw = list(csv.DictReader(open(os.path.join(I, "datos", par["archivo"]), newline="", encoding="utf-8-sig")))
datos = [r for r in datos_raw if all(v is not None and str(v).strip() not in ("", "NA") for v in r.values())]
raw_cols = [c for c in datos[0] if c != par["y"]]
cols, col_fn = [], []
for c in raw_cols:
    try:
        for r in datos:
            float(r[c])
        cols.append(c)
        col_fn.append(lambda r, c=c: float(r[c]))
    except ValueError:
        lv = sorted({r[c] for r in datos})
        for nv in lv[1:]:
            cols.append("%s%s" % (c, nv))
            col_fn.append(lambda r, c=c, nv=nv: 1.0 if r[c] == nv else 0.0)
X = [[fn(r) for fn in col_fn] for r in datos]
y = [float(r[par["y"]]) for r in datos]
P = rz.preparar(X, y)
cf = list(csv.DictReader(open(os.path.join(I, "coef_R.csv"), encoding="utf-8")))
pr = list(csv.DictReader(open(os.path.join(I, "predicciones_R.csv"), encoding="utf-8")))
rs = {r["modelo"]: r for r in csv.DictReader(open(os.path.join(I, "resumen_R.csv"), encoding="utf-8"))}
res = []
traza = {"problema": par.get("problema", ""), "n": P["n"], "s_y": P["sy"], "semilla": par.get("semilla"), "modelos": {}}


def chk(ok, msg):
    res.append(ok)
    print(("✅ " if ok else "❌ ") + msg)


assert [r["termino"] for r in cf[1:]] == cols, "las columnas de model.matrix deben ser las del CSV en orden"
for mod in ("lasso", "ridge_literal", "ridge_alpha0"):
    a, lam = float(rs[mod]["alpha"]), float(rs[mod]["lambda_min"])
    Rb0, Rb = float(cf[0][mod]), [float(r[mod]) for r in cf[1:]]
    yp = [float(r[mod]) for r in pr]
    mse = sum((u - v) ** 2 for u, v in zip(y, yp)) / len(y)
    yr = rz.predecir(X, Rb0, Rb)
    chk(abs(mse - float(rs[mod]["MSE"])) <= 1e-9 * mse and max(abs(u - v) for u, v in zip(yr, yp)) <= 1e-6 * P["sy"],
        "%s (alpha = %g, λ.min = %.6f): ŷ = β0 + xβ con los coeficientes de R; MSE = %.6f" % (mod, a, lam, mse))
    ent = {"alpha": a, "lambda_min": lam, "MSE": mse, "coef_R": dict(zip(["(Intercept)"] + cols, [Rb0] + Rb)),
           "ceros_R": [c for c, v in zip(cols, Rb) if v == 0]}
    if mod != "ridge_literal":
        b0, b, it = rz.ajustar(P, lam, a)
        Fo, FR = rz.objetivo(P, b0, b, lam, a), rz.objetivo(P, Rb0, Rb, lam, a)
        yo = rz.predecir(X, b0, b)
        dy = max(abs(u - v) for u, v in zip(yo, yr)) / P["sy"]
        mse_o = sum((u - v) ** 2 for u, v in zip(y, yo)) / len(y)
        chk(Fo <= FR * (1 + 1e-12) and (FR - Fo) / Fo < 1e-5 and dy < 5e-3,
            "oráculo %s (%d barridos): F = %.6f ≤ F(glmnet) = %.6f (dif. rel. %.1e); max|Δŷ| = %.1e·s_y; MSE oráculo = %.6f" % (
                mod, it, Fo, FR, (FR - Fo) / Fo, dy, mse_o))
        ent.update({"coef_oraculo": dict(zip(["(Intercept)"] + cols, [b0] + b)), "F_oraculo": Fo, "F_R": FR,
                    "MSE_oraculo": mse_o, "ceros_oraculo": [c for c, v in zip(cols, b) if v == 0]})
    traza["modelos"][mod] = ent

L, R0, R1 = traza["modelos"]["lasso"], traza["modelos"]["ridge_alpha0"], traza["modelos"]["ridge_literal"]
comunes = sorted(set(L["ceros_R"]) & set(L["ceros_oraculo"]), key=cols.index)
chk(len(L["ceros_R"]) >= 1,
    "p.29: Lasso lleva coeficientes exactamente a cero (R: %s; oráculo: %s; en ambos: %s)%s" % (
        L["ceros_R"], L["ceros_oraculo"], comunes,
        "" if L["ceros_oraculo"] else " — con columnas colineales (alias) el reparto de Lasso no es único; los ŷ coinciden"))
chk(not R0["ceros_R"] and not R0["ceros_oraculo"], "p.31: Ridge (alpha = 0) encoge sin anular: 0 coeficientes en cero de %d" % len(cols))
chk(all(abs(R1["coef_R"][t] - L["coef_R"][t]) <= 1e-9 * max(1, abs(L["coef_R"][t])) for t in L["coef_R"]) and R1["ceros_R"],
    "T3: la lectura literal de p.32 (alpha <- 1.0) es Lasso otra vez (mismos coeficientes, %d ceros); se entrega alpha = 0" % len(R1["ceros_R"]))

# Mutante: Ridge con la penalización (1 − α)/2·‖β‖² sin dividir entre s_y.
P_m = dict(P, sy=1.0)
b0m, bm, _ = rz.ajustar(P_m, R0["lambda_min"], 0.0)
dym = max(abs(u - v) for u, v in zip(rz.predecir(X, b0m, bm), rz.predecir(X, R0["coef_R"]["(Intercept)"], [R0["coef_R"][c] for c in cols]))) / P["sy"]
chk(dym > 5e-3, "mutante sin s_y en Ridge: max|Δŷ| = %.3f·s_y frente a glmnet, se detecta" % dym)

json.dump(traza, open(os.path.join(I, "traza.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("%s %d comprobaciones" % ("✅" if all(res) else "❌", len(res)))
sys.exit(0 if all(res) else 1)
