#!/usr/bin/env python3
"""Prueba de la coordinadora: los 25 temas de rubricas.md (nombres literales de las rúbricas AF1–AF4),
los temas sin skill y los tres problemas de EX-MC deben ir a la skill de la tabla; la asignación por
matrícula con 1851265 (impar, termina en 5) y con una par terminada en 0 (1851260).
No es una prueba a ciegas: las reglas de seleccionar.py se escribieron conociendo estos nombres.
Uso: python3 test_coordinadora.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from asignar import asignar  # noqa: E402
from seleccionar import seleccionar  # noqa: E402

CASOS = [  # (tema, texto, skills esperadas)
    ("1", "AF1 Metro", {"tsci3-subset-r"}), ("1", "Border Crossing", {"tsci3-subset-r"}), ("1", "Set R", {"tsci3-subset-r"}),
    ("2", "Normalización min-max y z", {"tsci3-kmeans"}),
    ("3", "K means clustering", {"tsci3-kmeans"}), ("4", "K medoids", {"tsci3-kmedoides"}),
    ("5", "A priori", {"tsci3-apriori"}), ("6", "Secuencias", {"tsci3-secuencias"}), ("7", "Episodios", {"tsci3-episodios"}),
    ("8", "Árboles de decisión", {"tsci3-arbol-decision"}), ("9", "Mínimos cuadrados", {"tsci3-minimos-cuadrados"}),
    ("10", "Breusch-Pagan", {"tsci3-breusch-pagan"}), ("11", "Predictor binario", {"tsci3-predictor-binario"}),
    ("12", "Regresión múltiple", {"tsci3-regresion-multiple"}), ("13", "Regresión con predictor no binario", {"tsci3-regresion-multiple"}),
    ("14", "Regresión Stepwise", {"tsci3-stepwise-aic"}), ("15", "Regresión Lasso", {"tsci3-regularizacion"}),
    ("16", "Regresión Ridge", {"tsci3-regularizacion"}), ("17", "Regresión logística binaria", {"tsci3-regresion-logistica"}),
    ("18", "Regresión logística multinomial", {"tsci3-regresion-logistica"}), ("19", "Matriz de confusión", {"tsci3-matriz-confusion"}),
    ("20", "KNN", {"tsci3-knn"}), ("21", "Determinación de k para KNN", {"tsci3-knn"}), ("22", "Bosques aleatorios", {"tsci3-bosque-aleatorio"}),
    ("23", "Petri", {"tsci3-modelado-procesos"}), ("24", "BPMN", {"tsci3-modelado-procesos"}), ("24", "YAWL", {"tsci3-modelado-procesos"}),
    ("24", "EPC", {"tsci3-modelado-procesos"}), ("25", "P Tree", {"tsci3-modelado-procesos"}), ("25", "Red Causal", {"tsci3-modelado-procesos"}),
]
SIN = ["Disco", "Separación Disco", "Diagrama clase", "Diagrama transición", "Bupa R", "Proceso Minería", "Obj WB", "DBSCAN", "PCA"]
MC = [
    ("P1", "Utilizando REGEVEN y el registro correspondiente al último dígito de su matrícula, obtenga la red Petri correspondiente y su "
           "denominación de esta. Si su matrícula termina en 0, 1 o 2 también elabore el diagrama YAWL, si termina en 3, 4 o 5, BPMN, y si "
           "termina en 6, 7, 8 o 9 el EDPC. Además, si su matrícula es impar elabore el árbol de proceso, si es par, la red causal. (U.T.2)",
     {"tsci3-modelado-procesos"}),
    ("P2", "Analice el registro que export, proponga y realice (con subsettings variados) un tratamiento de datos en función de un "
           "objetivo de la minería.", {"tsci3-subset-r"}),
    ("P3", "Obtenga el árbol de decisión de mínima entropía para el dataset gastank, compare el resultado con ambos árboles obtenidos "
           "mediante R.", {"tsci3-arbol-decision"}),
]
fallas = 0


def ok(c, msg):
    global fallas
    fallas += not c
    print(("✅ " if c else "❌ ") + msg)


temas = set()
for tema, texto, esp in CASOS:
    r = seleccionar(texto)
    got = {o["skill"] for o in r["skills"]}
    ok(r["codigo"] == 0 and got == esp, "tema %-2s «%s» → %s" % (tema, texto, ", ".join(sorted(got)) or r))
    temas.add(tema)
ok(temas == {str(i) for i in range(1, 26)}, "los 25 temas de rubricas.md están cubiertos")
for texto in SIN:
    r = seleccionar(texto)
    ok(r["codigo"] == 2, "«%s» → sin skill (%s)" % (texto, r.get("sin_skill")))
for pid, texto, esp in MC:
    r = seleccionar(texto)
    got = {o["skill"] for o in r["skills"]}
    ok(r["codigo"] == 0 and got == esp, "EX-MC %s → %s%s" % (pid, ", ".join(sorted(got)), " (aviso: estado P)" if r.get("aviso") else ""))
a = asignar("1851265")
ok((a["registro"], a["diagrama"], a["modelo"], a["estado_P"]) == ("Registro 05", "BPMN", "árbol de proceso", []),
   "1851265 → Registro 05, BPMN, árbol de proceso (como RESP p.2)")
b = asignar("1851260")
ok((b["registro"], b["diagrama"], b["modelo"], b["estado_P"]) == ("Registro 00", "YAWL", "red causal", ["YAWL", "red causal"]),
   "1851260 → Registro 00, YAWL, red causal, con aviso de estado P")
ok(seleccionar("calcule el precio del boleto")["codigo"] == 3, "texto ajeno al curso → no reconocido")
print("%s %d fallas" % ("✅" if not fallas else "❌", fallas))
sys.exit(1 if fallas else 0)
