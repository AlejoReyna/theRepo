#!/usr/bin/env python3
"""Verificación de la regresión logística contra R (oráculo kit_tsci3/tsci3/oraculos/logistica.py).

Uso: python3 verificar_logistica.py INCISO
Binaria (p.40): mediana y conteo de precio_alto; coeficientes y errores estándar de glm; devianza;
probabilidad de los datos nuevos sustituida a mano en la sigmoide (p.37); Anova (LR tipo II) y VIF
con su lectura (p.39). Multinomial (p.41): percentiles 0.33/0.66 (tipo 7), conteos de cut(right =
FALSE), máximo de la log-verosimilitud, coeficientes y probabilidades de los datos nuevos (suman 1);
T25 (wts[1:3] no son interceptos). Mutante: precio_alto con ≥ (regla de p.48) o cut con right = TRUE.
Escribe traza.json.
"""
import csv
import json
import math
import os
import sys

sys.path.insert(0, "/Users/alexis/theCode/newSkills/TSCI3/kit_tsci3")
from tsci3 import estadistica as es  # noqa: E402
from tsci3.oraculos import logistica as lg  # noqa: E402

I = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
par = json.load(open(os.path.join(I, "datos", "parametros.json"), encoding="utf-8"))
datos = list(csv.DictReader(open(os.path.join(I, "datos", par["archivo"]), newline="", encoding="utf-8-sig")))
preds = par["predictores"]
X = [[1.0] + [float(r[p]) for p in preds] for r in datos]
precio = [float(r[par["y"]]) for r in datos]
nuevo = [1.0] + [float(par["nuevos"][p]) for p in preds]
rs = next(csv.DictReader(open(os.path.join(I, "resumen_R.csv"), encoding="utf-8")))
res = []


def chk(ok, msg):
    res.append(ok)
    print(("✅ " if ok else "❌ ") + msg)


def leer(n):
    return list(csv.DictReader(open(os.path.join(I, n), encoding="utf-8")))


def rel(a, b, t):
    return abs(a - b) <= t * max(1e-12, abs(b))


# ---------------- Binaria (p.40)
s = sorted(precio)
med = (s[len(s) // 2 - 1] + s[len(s) // 2]) / 2 if len(s) % 2 == 0 else s[len(s) // 2]
y = [1 if v > med else 0 for v in precio]
chk(med == float(rs["mediana"]) and sum(y) == int(rs["n_alto_bin"]), "p.40: mediana = %.2f; precio_alto = 1 en %d de %d" % (med, sum(y), len(y)))
b, V, dev, it = lg.binaria(X, y)
cb = leer("coef_bin_R.csv")
nombres = ["(Intercept)"] + preds
chk(all(rel(bj, float(r["coef"]), 1e-7) and rel(math.sqrt(V[j][j]), float(r["SE"]), 1e-6) for j, (bj, r) in enumerate(zip(b, cb)))
    and rel(dev, float(rs["deviance_bin"]), 1e-10),
    "glm binomial (Newton, %d iteraciones): β y errores estándar = R; devianza = %.6f" % (it, dev))
eta = sum(bj * xj for bj, xj in zip(b, nuevo))
pn = 1 / (1 + math.exp(-eta))
print("   η = %s = %.6f" % (" + ".join("%.6g·%g" % (bj, xj) for bj, xj in zip(b, nuevo)), eta))
chk(rel(pn, float(rs["p_bin"]), 1e-7), "p.37: P(precio_alto | %s) = 1/(1 + e^(−η)) = %.6f = predict(type = \"response\")" % (par["nuevos"], pn))
an = {r["termino"]: r for r in leer("anova_R.csv")}
anova = {}
for j, p in enumerate(preds, 1):
    Xr = [[x[i] for i in range(len(x)) if i != j] for x in X]
    _, _, dev_r, _ = lg.binaria(Xr, y)
    lr = dev_r - dev
    anova[p] = (lr, es.p_chi2(lr, 1))
chk(all(rel(anova[p][0], float(an[p]["LR"]), 1e-7) and rel(anova[p][1], float(an[p]["p"]), 1e-5) for p in preds),
    "Anova tipo II (LR χ², 1 gl) = car::Anova: %s" % ", ".join("%s %.4f (p = %.3g)" % (p, *anova[p]) for p in preds))
vf = lg.vif(V)
vr = {r["termino"]: float(r["VIF"]) for r in leer("vif_R.csv")}
lectura = lambda v: "sin colinealidad" if abs(v - 1) < 1e-9 else "moderada" if v <= 5 else "preocupante"  # noqa: E731
chk(all(rel(v, vr[p], 1e-6) for v, p in zip(vf, preds)),
    "p.39: VIF = car::vif: %s" % ", ".join("%s %.4f (%s)" % (p, v, lectura(v)) for p, v in zip(preds, vf)))

# ---------------- Multinomial (p.41)
q33, q66 = lg.cuantil7(precio, 0.33), lg.cuantil7(precio, 0.66)
cat = lg.cortar(precio, [q33, q66], ["bajo", "medio", "alto"])
cnt = {c: cat.count(c) for c in ("bajo", "medio", "alto")}
chk(rel(q33, float(rs["p33"]), 1e-12) and rel(q66, float(rs["p66"]), 1e-12) and all(cnt[c] == int(rs["n_" + c]) for c in cnt),
    "p.41: percentiles 0.33 = %.2f y 0.66 = %.2f (tipo 7); cut(right = FALSE): %s" % (q33, q66, cnt))
clases = ["bajo", "medio", "alto"]
yi = [clases.index(c) for c in cat]
B, ll, itm, probs = lg.multinomial(X, yi, clases)
llR = float(rs["loglik_multi"])
cm = {(r["categoria"], r["termino"]): float(r["coef"]) for r in leer("coef_multi_R.csv")}
dif_coef = max(abs(B[c - 1][j] - cm[(clases[c], nombres[j])]) / max(1e-3, abs(B[c - 1][j])) for c in (1, 2) for j in range(len(nombres)))
chk(ll >= llR - 1e-9 and ll - llR < 1e-4,
    "multinom: máximo de la log-verosimilitud %.6f (oráculo, %d iteraciones de Newton) vs %.6f de nnet (dif. %.1e)" % (ll, itm, llR, ll - llR))
pr = probs(nuevo)
pR = [float(rs["prob_" + c]) for c in clases]
chk(abs(sum(pr) - 1) < 1e-12 and abs(sum(pR) - 1) < 1e-9 and max(abs(a - b_) for a, b_ in zip(pr, pR)) < 1e-4,
    "predict(type = \"probs\") con %s: %s (suman 1); oráculo = R a < 1e−4; coeficientes a %.1e relativo" % (
        par["nuevos"], ", ".join("%s %.6f" % (c, p) for c, p in zip(clases, pr)), dif_coef))
wts = [float(rs["wts_%d" % i]) for i in (1, 2, 3)]
chk(all(w == 0 for w in wts) and any(B[c][0] != 0 for c in range(2)),
    "T25: p.41 wts[1:3] = %s son los pesos de la clase base, no los interceptos (medio %.6f, alto %.6f = coef[, 1])" % (wts, B[0][0], B[1][0]))

# ---------------- Mutantes
y_m = [1 if v >= med else 0 for v in precio]
cat_m = ["bajo" if v <= q33 else "medio" if v <= q66 else "alto" for v in precio]
dif_m = sum(y_m) != sum(y) or any(cat_m.count(c) != cnt[c] for c in cnt)
print("   mutantes: precio ≥ mediana → %d altos (vs %d); right = TRUE → %s" % (sum(y_m), sum(y), {c: cat_m.count(c) for c in clases}))
chk(dif_m, "mutante de frontera (≥ en lugar de >, o right = TRUE) cambia los conteos y se detecta")

traza = {"problema": par.get("problema", ""), "mediana": med, "n_alto": sum(y), "coef_bin": dict(zip(nombres, b)),
         "SE_bin": dict(zip(nombres, [math.sqrt(V[j][j]) for j in range(len(b))])), "devianza": dev, "eta_nuevo": eta, "p_nuevo": pn,
         "anova": {p: {"LR": v[0], "p": v[1]} for p, v in anova.items()}, "VIF": dict(zip(preds, vf)),
         "p33": q33, "p66": q66, "conteos": cnt, "coef_multi": {clases[c]: dict(zip(nombres, B[c - 1])) for c in (1, 2)},
         "loglik_multi": ll, "probs_nuevo": dict(zip(clases, pr)), "nuevo": par["nuevos"]}
json.dump(traza, open(os.path.join(I, "traza.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("%s %d comprobaciones" % ("✅" if all(res) else "❌", len(res)))
sys.exit(0 if all(res) else 1)
