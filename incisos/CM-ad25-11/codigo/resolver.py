#!/usr/bin/env python3
"""Matriz de confusión (OD/AM R.pdf p.49-50; AD25-11 p.9; AD25-03 p.3 y p.11): oráculo y verificación.

Uso: python3 verificar_matriz.py INCISO
parametros.json:
  {"origen": "csv", "positiva": "alto"}                  → datos/clases.csv (real, pred) + R
  {"origen": "tabla", "TP", "FN", "FP", "TN", "N_declarado", "reportado": {...}, "tabla_publicada": {...}}
                                                          → caso de artículo + R (consistencia)
  {"origen": "reconstruir", "N", "reportado": {...}, "decimales", "promedio": "ponderado",
   "predichos_positivos"}                                  → enumera las tablas 2×2 compatibles (sin R)
Tabla con la clase real en las filas y la predicha en las columnas (p.49), márgenes p, n, p′, n′, N.
Métricas: exactitud = Σdiagonal/N (p.50); precisión = TP/(TP+FP) y recall = TP/(TP+FN) (AD25-03 p.3;
AD25-11 p.9); especificidad, F1 y kappa como en caret. Compara con caret y revisa T24 (p.50 literal
intercambia recall y precisión). Escribe traza.json.
"""
import csv
import json
import os
import sys
from fractions import Fraction as F

I = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
par = json.load(open(os.path.join(I, "datos", "parametros.json"), encoding="utf-8"))
res = []
traza = {"problema": par.get("problema", ""), "origen": par["origen"]}


def chk(ok, msg):
    res.append(ok)
    print(("✅ " if ok else "❌ ") + msg)


def metricas(tp, fn, fp, tn):
    N = tp + fn + fp + tn
    p, n, pp, nn = tp + fn, fp + tn, tp + fp, fn + tn
    d = lambda a, b: F(a, b) if b else None  # noqa: E731
    acc = F(tp + tn, N)
    pe = F(p * pp + n * nn, N * N)
    prec, rec = d(tp, pp), d(tp, p)
    return {"N": N, "p": p, "n": n, "p'": pp, "n'": nn, "Accuracy": acc, "Kappa": (acc - pe) / (1 - pe) if pe != 1 else None,
            "Recall": rec, "Specificity": d(tn, n), "Precision": prec, "NPV": d(tn, nn),
            "F1": (2 * prec * rec / (prec + rec)) if prec is not None and rec is not None and prec + rec else None}


def fl(v):
    return None if v is None else float(v)


def comparar_r(tp, fn, fp, tn, M):
    tr = list(csv.DictReader(open(os.path.join(I, "tabla_R.csv"), encoding="utf-8")))
    pos = par["positiva"]
    cel = {(r["real"] == pos, r["pred"] == pos): int(r["n"]) for r in tr}
    chk(cel == {(True, True): tp, (True, False): fn, (False, True): fp, (False, False): tn},
        "tabla de R = oráculo (real en filas, p.49): TP %d, FN %d, FP %d, TN %d" % (tp, fn, fp, tn))
    mr = {r["metrica"]: r for r in csv.DictReader(open(os.path.join(I, "metricas_R.csv"), encoding="utf-8"))}
    pares = [("Accuracy", "Accuracy"), ("Kappa", "Kappa"), ("Sensitivity", "Recall"), ("Specificity", "Specificity"),
             ("PPV", "Precision"), ("NPV", "NPV"), ("F1", "F1")]
    ok = all(M[b] is None or abs(float(mr[a]["correcta"]) - float(M[b])) < 1e-12 for a, b in pares)
    chk(ok, "caret confusionMatrix(pred, real) = oráculo en exactitud, kappa, recall, especificidad, precisión, VPN y F1")
    lit_ok = (abs(float(mr["Sensitivity"]["literal_p50"]) - float(M["Precision"])) < 1e-12
              and abs(float(mr["PPV"]["literal_p50"]) - float(M["Recall"])) < 1e-12
              and abs(float(mr["Accuracy"]["literal_p50"]) - float(M["Accuracy"])) < 1e-12)
    visible = M["Precision"] != M["Recall"]
    chk(lit_ok, "T24: p.50 literal (table(real, pred)) da Sensitivity = precisión %.6f y Pos Pred Value = recall %.6f%s" % (
        float(M["Precision"]), float(M["Recall"]), "" if visible else " (aquí FN = FP y el intercambio no se nota)"))
    return {"caret_literal_p50": {k: float(v["literal_p50"]) for k, v in mr.items()}}


def imprimir(tp, fn, fp, tn, M, pos="positivo", neg="negativo"):
    print("                 pred %-8s pred %-8s | total" % (pos, neg))
    print("   real %-8s  %8d       %8d     | p  = %d" % (pos, tp, fn, M["p"]))
    print("   real %-8s  %8d       %8d     | n  = %d" % (neg, fp, tn, M["n"]))
    print("   total          p' = %-6d    n' = %-6d   | N  = %d" % (M["p'"], M["n'"], M["N"]))


if par["origen"] == "csv":
    cl = list(csv.DictReader(open(os.path.join(I, "datos", "clases.csv"), encoding="utf-8")))
    pos = par["positiva"]
    tp = sum(1 for r in cl if r["real"] == pos and r["pred"] == pos)
    fn = sum(1 for r in cl if r["real"] == pos and r["pred"] != pos)
    fp = sum(1 for r in cl if r["real"] != pos and r["pred"] == pos)
    tn = sum(1 for r in cl if r["real"] != pos and r["pred"] != pos)
    M = metricas(tp, fn, fp, tn)
    neg = sorted({r["real"] for r in cl} - {pos})[0]
    imprimir(tp, fn, fp, tn, M, pos, neg)
    chk(M["p"] + M["n"] == M["N"] == M["p'"] + M["n'"] == len(cl), "márgenes: p + n = p′ + n′ = N = %d filas de prueba" % len(cl))
    traza.update(comparar_r(tp, fn, fp, tn, M))
elif par["origen"] == "tabla":
    tp, fn, fp, tn = (par[k] for k in ("TP", "FN", "FP", "TN"))
    M = metricas(tp, fn, fp, tn)
    imprimir(tp, fn, fp, tn, M)
    chk(M["p"] + M["n"] == M["N"] == M["p'"] + M["n'"], "márgenes: p + n = p′ + n′ = N = %d" % M["N"])
    traza.update(comparar_r(tp, fn, fp, tn, M))
    # Consistencia del artículo (T4)
    incons = []
    if par.get("N_declarado") and par["N_declarado"] != M["N"]:
        incons.append("N de las fórmulas = %d ≠ %d datos de prueba declarados" % (M["N"], par["N_declarado"]))
    tpub = par.get("tabla_publicada")
    if tpub:
        Np = sum(tpub.values())
        if tpub.get("TP") != tp:
            incons.append("la tabla publicada pone TP = %d y las fórmulas usan %d" % (tpub["TP"], tp))
        if Np != par.get("N_declarado", Np):
            incons.append("la tabla publicada suma %d ≠ %d" % (Np, par["N_declarado"]))
    for k, v in par.get("reportado", {}).items():
        exacto = float(M[k])
        d = len(repr(v).split(".")[1]) if "." in repr(v) else 0
        modo = "redondeo" if round(exacto, d) == v else "truncamiento" if int(exacto * 10 ** d) / 10 ** d == v else None
        if modo is None:
            incons.append("%s reportado %s ≠ %.6f" % (k, v, exacto))
        else:
            print("   %s reportado %s; exacto %.6f (%s a %d decimales)" % (k, v, exacto, modo, d))
    for x in incons:
        print("   ⚠️  " + x)
    esperado = par.get("esperado_inconsistente", False)
    chk(bool(incons) == esperado, "consistencia del artículo: %s" % ("inconsistente, se marca T4 (%d hallazgos)" % len(incons) if incons else "consistente"))
    traza["inconsistencias"] = incons
else:                                                       # reconstruir
    N, dec, rep = par["N"], par.get("decimales", 3), par["reportado"]
    r = lambda x: round(float(x) + 1e-12, dec)  # noqa: E731
    sols = []
    for tp in range(N + 1):
        for fn in range(N + 1 - tp):
            for fp in range(N + 1 - tp - fn):
                tn = N - tp - fn - fp
                M = metricas(tp, fn, fp, tn)
                if None in (M["Precision"], M["Recall"], M["NPV"], M["Specificity"]):
                    continue
                f1n = 2 * M["NPV"] * M["Specificity"] / (M["NPV"] + M["Specificity"]) if M["NPV"] + M["Specificity"] else 0
                w = lambda a, b: (M["p"] * a + M["n"] * b) / N  # noqa: E731  promedio ponderado por clase real (Orange)
                calc = {"CA": M["Accuracy"], "Precision": w(M["Precision"], M["NPV"]), "Recall": w(M["Recall"], M["Specificity"]),
                        "F1": w(M["F1"] or 0, f1n)}
                if all(r(calc[k]) == v for k, v in rep.items()):
                    sols.append({"TP": tp, "FN": fn, "FP": fp, "TN": tn, "p": M["p"], "p'": M["p'"]})
    print("   %d tablas 2×2 con N = %d reproducen %s (promedio ponderado por clase)" % (len(sols), N, rep))
    for s in sols:
        print("     TP %2d  FN %2d  FP %2d  TN %2d   (reales positivos %d, predichos positivos %d)" % (s["TP"], s["FN"], s["FP"], s["TN"], s["p"], s["p'"]))
    chk(len(sols) > 0, "reconstrucción: el reporte es compatible con %d tablas; no determina una sola" % len(sols))
    pp = par.get("predichos_positivos")
    if pp is not None:
        u = [s for s in sols if s["p'"] == pp]
        chk(len(u) == 1, "si los %d predichos positivos de p.11 son de los mismos %d datos, la tabla es única: %s" % (pp, N, u))
        traza["hipotesis_predichos"] = u
    ok_rec = all(abs(float(F(s["TP"] + s["TN"], N)) - rep.get("CA", 0)) < 0.0005 for s in sols)
    chk(ok_rec, "recall ponderado = exactitud en las %d tablas (identidad: Σ p_c·recall_c / N = Σdiagonal / N)" % len(sols))
    traza["tablas_compatibles"] = sols

if par["origen"] != "reconstruir":
    traza.update({"TP": tp, "FN": fn, "FP": fp, "TN": tn, "metricas": {k: fl(v) for k, v in M.items()}})
    # Mutante: tabla con la predicción en las filas (AD25-03 p.3) leída como si fuera p.49
    if fn != fp:
        Mm = metricas(tp, fp, fn, tn)
        chk(Mm["Recall"] != M["Recall"], "mutante (orientación de AD25-03 p.3 leída como p.49): recall %.6f ≠ %.6f, se detecta" % (
            float(Mm["Recall"]), float(M["Recall"])))
    else:
        print("   mutante de orientación: no aplica (FN = FP = %d, la tabla es simétrica)" % fn)
json.dump(traza, open(os.path.join(I, "traza.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("%s %d comprobaciones" % ("✅" if all(res) else "❌", len(res)))
sys.exit(0 if all(res) else 1)
