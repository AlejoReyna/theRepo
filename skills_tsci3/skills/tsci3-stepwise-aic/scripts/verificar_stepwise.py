#!/usr/bin/env python3
"""Verificación de la regresión stepwise contra R (oráculo kit_tsci3/tsci3/oraculos/stepwise.py).

Uso: python3 verificar_stepwise.py INCISO
Compara: camino de pasos (cambio, RSS, AIC), coeficientes del modelo final, la vecindad del modelo
final (drop1/add1: ninguna variable sola baja el AIC, p.20-22) y el AIC de p.21 (2k − 2 ln L)
contra AIC() de R. Mutante: sin la penalización 2k el método no quita ninguna variable.
Escribe traza.json.
"""
import csv
import json
import math
import os
import sys

sys.path.insert(0, "/Users/alexis/theCode/newSkills/TSCI3/kit_tsci3")
from tsci3 import regresion as rg  # noqa: E402
from tsci3.oraculos import stepwise as sw  # noqa: E402

I = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
par = json.load(open(os.path.join(I, "datos", "parametros.json"), encoding="utf-8"))
filas = rg.leer(os.path.join(I, "datos", par["archivo"]))
preds = [c for c in filas[0].keys() if c != par["y"]]
aj = sw.Ajustador(filas, par["y"], preds)
res = []


def chk(ok, msg):
    res.append(ok)
    print(("✅ " if ok else "❌ ") + msg)


def leer(nombre):
    return list(csv.DictReader(open(os.path.join(I, nombre), encoding="utf-8")))


def cerca(a, b, rel=1e-9, abs_=1e-6):
    return abs(a - b) <= max(abs_, rel * abs(b))


out = sw.stepwise(aj, par.get("direccion", "both"))
pr = leer("pasos_R.csv")
ok = len(pr) == len(out["pasos"]) and all(
    a["paso"] == b[0] and int(a["gl_resid"]) == b[1] and cerca(float(b[2]), float(a["RSS"])) and cerca(b[3], float(a["AIC"]))
    for a, b in zip(pr, out["pasos"]))
print("   Paso                     gl     RSS                    AIC")
for p in out["pasos"]:
    print("   %-24s %4d  %22.4f  %.6f" % (p[0] or "(modelo inicial)", p[1], float(p[2]), p[3]))
chk(ok, "camino de stepAIC(direction = \"%s\"): %d pasos iguales a R (cambio, gl, RSS, AIC)" % (par.get("direccion", "both"), len(pr) - 1))

_, k, coef = aj.ajustar(out["modelo"])
fr = {f["termino"]: float(f["coef"]) for f in leer("final_R.csv")}
chk(set(fr) == set(coef) and all(cerca(float(coef[t]), fr[t], 1e-7, 1e-9) for t in fr),
    "modelo final (%d términos + intercepto) y coeficientes = R" % len(out["modelo"]))

vr = leer("vecinos_R.csv")
vp = {f[0]: f for f in sw.vecinos(aj, out["modelo"], preds)}
chk(all(f["cambio"] in vp and cerca(vp[f["cambio"]][3], float(f["AIC"])) for f in vr) and len(vr) == len(vp),
    "vecindad del modelo final: %d filas de drop1/add1 = R" % len(vr))
aic0 = vp["<none>"][3]
mejor = min((f for f in vp.values() if f[0] != "<none>" and f[1] != 0), key=lambda f: f[3])
chk(mejor[3] > aic0, "óptimo local: el mejor cambio de una variable (%s, AIC %.4f) no baja el AIC %.4f" % (mejor[0], mejor[3], aic0))

rr = next(iter(leer("resumen_R.csv")))
n = aj.n
rss = float(aj.ajustar(out["modelo"])[0])
lnL = -n / 2 * (math.log(2 * math.pi) + math.log(rss / n) + 1)
aic_p21 = 2 * (k + 1) - 2 * lnL                     # k coeficientes + la varianza del error
cte = n * (math.log(2 * math.pi) + 1) + 2
chk(cerca(lnL, float(rr["logLik"])) and cerca(aic_p21, float(rr["AIC_logLik"])) and cerca(aic_p21 - out["aic"], cte),
    "p.21: AIC = 2k − 2 ln L = %.6f (k = %d, ln L = %.6f) = AIC() de R; difiere de extractAIC en la constante %.6f" % (aic_p21, k + 1, lnL, cte))

# Mutante: AIC sin penalización (solo n·ln(RSS/n)); quitar una variable nunca baja el RSS.
orig = sw.Ajustador.aic
sw.Ajustador.aic = lambda self, t: self.n * math.log(float(self.ajustar(t)[0]) / self.n)
mut = sw.stepwise(aj, par.get("direccion", "both"))
sw.Ajustador.aic = orig
chk(set(mut["modelo"]) != set(out["modelo"]),
    "mutante sin 2k: conserva %d de %d variables (≠ %d de R), se detecta" % (len(mut["modelo"]), len(preds), len(out["modelo"])))

traza = {"problema": par.get("problema", ""), "n": n, "direccion": par.get("direccion", "both"),
         "pasos": [{"cambio": p[0], "gl_resid": p[1], "RSS": float(p[2]), "AIC": p[3]} for p in out["pasos"]],
         "modelo_final": out["modelo"], "coeficientes": {t: (None if v is None else float(v)) for t, v in coef.items()},
         "vecinos": [{"cambio": f[0], "Df": f[1], "RSS": float(f[2]), "AIC": f[3]} for f in vp.values()],
         "candidatos_por_paso": [[{"cambio": f[0], "Df": f[1], "RSS": float(f[2]), "AIC": f[3]} for f in c] for c in out["candidatos"]],
         "k": k + 1, "logLik": lnL, "AIC_p21": aic_p21, "extractAIC": out["aic"]}
json.dump(traza, open(os.path.join(I, "traza.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("%s %d comprobaciones" % ("✅" if all(res) else "❌", len(res)))
sys.exit(0 if all(res) else 1)
