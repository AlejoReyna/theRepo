#!/usr/bin/env python3
"""Caso de prueba del plan (§6 paso 23): bloques de S2 (DOLLY, incisos/KM-dolly) y S4 (AP, incisos/AP-clase).

Escribe en cada inciso:
  * verificacion.md con la salida del oráculo del kit (kit.py kmeans-oraculo / apriori-oraculo) y
    «Estado: aprobado» solo si el oráculo sale con 0;
  * bloque.json armado desde traza.json (ninguna cifra se teclea: todas se formatean de la traza).
Después escribe pruebas/entrega_prueba.json (tarea «AF3», color Amarillo, hora N4).
Uso: python3 bloques_prueba.py
"""
import csv
import json
import os
import subprocess

T = "/Users/alexis/theCode/newSkills/TSCI3"
AQUI = os.path.dirname(os.path.abspath(__file__))


def f4(x):
    return "%.4f" % x


def verificacion(inciso, comando, datos):
    r = subprocess.run(["python3", os.path.join(T, "kit_tsci3", "kit.py"), comando, datos, os.path.join(inciso, "traza.json")],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    estado = "aprobado" if r.returncode == 0 else "rechazado"
    open(os.path.join(inciso, "verificacion.md"), "w", encoding="utf-8").write(
        "# Verificación de %s\n\n## 1. Oráculo contra traza (`kit.py %s`)\n\n```\n%s```\n\n"
        "## 2–4. R, caso de referencia y mutante\nRegistrados en `TSCI3/README.md` (fila de la skill) y en la sección «Casos» de su SKILL.md.\n\n"
        "Estado: %s\n" % (os.path.basename(inciso), comando, r.stdout, estado))
    return estado


def bloque_kmeans():
    I = os.path.join(T, "incisos", "KM-dolly")
    tr = json.load(open(os.path.join(I, "traza.json"), encoding="utf-8"))
    cols = tr["columnas"]
    norm = tr["normalizacion"]
    pasos = [{"titulo": "Paso 1 Normalización min-max",
              "texto": "Cada variable se lleva a [0, 1] con y = m·x + b, m = 1/(máx − mín), b = −m·mín, como en el Excel de clase.",
              "formulas": ["y = m·x + b,  m = 1/(máx − mín),  b = −m·mín"],
              "tablas": [[["Variable", "mín", "máx", "m", "b"]] + [[c, "%g" % norm[c]["min"], "%g" % norm[c]["max"], "%.6g" % norm[c]["m"], "%.6g" % (norm[c]["b"] or 0.0)] for c in cols]]}]
    for it in tr["iteraciones"]:
        filas = [["Registro", "DC0", "DC1", "DMIN", "C0", "C1"]]
        for i, (a, b, p) in enumerate(zip(it["DC0"], it["DC1"], it["pertenencia"]), 1):
            filas.append([str(i), f4(a), f4(b), f4(min(a, b)), "1" if a <= b else "0", "1" if b <= a else "0"])
        cen = [["Centroide"] + cols] + [["C0"] + [f4(v) for v in it["C0"]], ["C1"] + [f4(v) for v in it["C1"]],
                                         ["C0'"] + [f4(v) for v in it["C0_nuevo"]], ["C1'"] + [f4(v) for v in it["C1_nuevo"]]]
        pasos.append({"titulo": "Paso %d Iteración %d" % (it["iteracion"] + 1, it["iteracion"]),
                      "texto": "Distancia euclidiana de cada registro a C0 y C1; pertenencia al más cercano. n0 = %d, n1 = %d, Σ DMIN = %s. "
                               "Actualización de clase (T7): C' = (Σ x·pertenencia + C)/(n + 1)." % (it["n0"], it["n1"], f4(it["suma_dmin"])),
                      "tablas": [{"titulo": "Centroides", "filas": cen}, {"titulo": "Distancias y pertenencia", "filas": filas}]})
    rs = tr["resumen"]
    b = {"id": "KM-dolly", "metodo": "Kmeans", "titulo": "K-means con la convención del ejercicio de clase",
         "enunciado": "Se pide agrupar las 49 canciones de DOLLY LIVES (12 variables) en dos grupos con k-means, con el procedimiento del ejercicio de clase.",
         "datos": [["Dato", "Valor", "Dato", "Valor"], ["Registros", str(tr["n"]), "Variables", str(len(cols))],
                   ["k", "2", "Centroides iniciales", "mínimo y máximo normalizados"], ["Normalización", "min-max", "Actualización", "(Σx·p + C)/(n + 1)"]],
         "cajas": [{"titulo": "Normalizar", "texto": "Min-max de cada variable con m y b.", "cita": 1},
                   {"titulo": "Centroides", "texto": "C0 = vector mínimo y C1 = vector máximo.", "cita": 1},
                   {"titulo": "Distancias", "texto": "DC0, DC1 euclidianas y pertenencia al menor.", "cita": 1},
                   {"titulo": "Actualizar", "texto": "C' = (Σx·p + C)/(n + 1), regla del Excel.", "cita": 2},
                   {"titulo": "Repetir", "texto": "Hasta que ninguna pertenencia cambie.", "cita": 2}],
         "fuentes": ["OD/mochila_.xlsx B4:L10 (normalización, distancias y pertenencia).", "OD/DOLLY LIVES.xlsx Sheet1 AG2:AR3 (actualización de centroides)."],
         "pasos": pasos,
         "codigo": {"python": [{"archivo": "codigo/resolver.py", "funciones": ["normalizar", "iterar"]}],
                    "r": [{"archivo": "codigo/script.R", "lineas": [1, 40]}]},
         "comprobacion": "Un programa independiente recalcula por otro camino la normalización y cada iteración y coincide con la traza. "
                         "La primera iteración reproduce las cifras en caché del Excel del profesor (con la réplica de T1).\n\n"
                         "Convergió en %d iteraciones: n0 = %d, n1 = %d y Σ DMIN = %s." % (rs["iteraciones"], rs["n0"], rs["n1"], f4(rs["suma_dmin"])),
         "respuesta": "Grupo C0 con %d canciones y grupo C1 con %d canciones después de %d iteraciones." % (rs["n0"], rs["n1"], rs["iteraciones"]),
         "numeros_clave": [{"texto": str(rs["iteraciones"]), "traza": "resumen.iteraciones"}, {"texto": str(rs["n0"]), "traza": "resumen.n0"},
                           {"texto": str(rs["n1"]), "traza": "resumen.n1"}, {"texto": f4(rs["suma_dmin"]), "traza": "resumen.suma_dmin"}]}
    json.dump(b, open(os.path.join(I, "bloque.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return verificacion(I, "kmeans-oraculo", os.path.join(I, "datos", "dolly_sheet1.csv"))


def bloque_apriori():
    I = os.path.join(T, "incisos", "AP-clase")
    tr = json.load(open(os.path.join(I, "traza.json"), encoding="utf-8"))
    pasos = []
    for nv in tr["niveles"]:
        filas = [["Itemset", "Frecuencia", "Soporte"]] + [[", ".join(s), str(c), f4(c / tr["n"])] for s, c in nv["muestra"]]
        pasos.append({"titulo": "Paso %d Itemsets frecuentes de tamaño %d" % (nv["nivel"], nv["nivel"]),
                      "texto": "Itemsets de %d ítems con soporte ≥ %g: %d (todo subconjunto de un itemset frecuente es frecuente)." % (nv["nivel"], tr["soporte_min"], nv["itemsets"]),
                      "tablas": [filas]})
    rp = [["SI X", "ENTONCES Y", "NX", "NY", "NX∧Y", "S", "C", "L"]] + [
        [", ".join(r["lhs"]), r["rhs"], str(r["NX"]), str(r["NY"]), str(r["NXY"]), f4(r["soporte"]), f4(r["confianza"]), f4(r["lift"])] for r in tr["reglas_pedidas"]]
    pasos.append({"titulo": "Paso %d Reglas pedidas" % (len(pasos) + 1), "texto": "S = NX∧Y/N, C = NX∧Y/NX y L = NX∧Y·N/(NX·NY), con N = %d." % tr["n"],
                  "formulas": ["S = NX∧Y / N", "C = NX∧Y / NX", "L = NX∧Y · N / (NX · NY)"], "tablas": [rp]})
    r0 = tr["reglas_pedidas"][0]
    b = {"id": "AP-clase", "metodo": "Apriori", "titulo": "Reglas de asociación con Apriori",
         "enunciado": "Se pide obtener las reglas de asociación entre HeartDisease, Smoking, AlcoholDrinking y Stroke con soporte mínimo 0.01 y confianza mínima 0.1, y evaluar las reglas del ejercicio de clase.",
         "datos": [["Dato", "Valor", "Dato", "Valor"], ["Transacciones", str(tr["n"]), "Columnas", str(len(tr["columnas"]))],
                   ["Soporte mínimo", "%g" % tr["soporte_min"], "Confianza mínima", "%g" % tr["confianza_min"]]],
         "cajas": [{"titulo": "Ítems", "texto": "Cada celda columna=valor es un ítem.", "cita": 1},
                   {"titulo": "Nivel 1", "texto": "Contar los ítems y quedarse con S ≥ 0.01.", "cita": 2},
                   {"titulo": "Niveles k", "texto": "Combinar los frecuentes del nivel anterior.", "cita": 2},
                   {"titulo": "Reglas", "texto": "Generar X ⇒ Y con C ≥ 0.1.", "cita": 1},
                   {"titulo": "Medidas", "texto": "S, C y L de las reglas pedidas.", "cita": 1}],
         "fuentes": ["OD/AP (1).xlsx I2:O11 (S, C y L).", "EJ26-24 p.6 (Apriori por niveles).", "OD/arules R (2).txt (umbrales)."],
         "pasos": pasos,
         "codigo": {"python": [{"archivo": "codigo/resolver.py", "funciones": ["apriori", "reglas"]}], "r": [{"archivo": "codigo/script.R", "lineas": [1, 30]}]},
         "comprobacion": "Un programa independiente cuenta cada subconjunto de cada transacción y arma las reglas por otro camino; coincide con la traza. "
                         "R (arules) da las mismas %d reglas." % tr["n_reglas"],
         "respuesta": "%d reglas; SI %s ENTONCES %s: S = %s, C = %s, L = %s." % (tr["n_reglas"], r0["lhs"][0], r0["rhs"], f4(r0["soporte"]), f4(r0["confianza"]), f4(r0["lift"])),
         "numeros_clave": [{"texto": str(tr["n_reglas"]), "traza": "n_reglas"}, {"texto": f4(r0["confianza"]), "traza": "reglas_pedidas.0.confianza"},
                           {"texto": f4(r0["lift"]), "traza": "reglas_pedidas.0.lift"}]}
    json.dump(b, open(os.path.join(I, "bloque.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return verificacion(I, "apriori-oraculo", os.path.join(I, "datos", "ap_clase.csv"))


if __name__ == "__main__":
    print("KM-dolly:", bloque_kmeans())
    print("AP-clase:", bloque_apriori())
    e = {"alumno": {"nombre": "Alexis Alberto Reyna Sánchez", "matricula": "1851265"}, "color": "Amarillo", "hora": "N4", "tarea": "AF3",
         "fecha": "13 de noviembre de 2026",
         "problemas": [{"n": 1, "inciso": os.path.join(T, "incisos", "KM-dolly")}, {"n": 2, "inciso": os.path.join(T, "incisos", "AP-clase")}],
         "teoria": {"titulo": "Prueba de la parte teórica", "preguntas": [{"pregunta": "¿Qué mide el lift de una regla?",
                    "respuesta": ["El lift compara la confianza de la regla con la frecuencia del consecuente: L = NX∧Y·N/(NX·NY) (OD/AP (1).xlsx O4)."],
                    "vinetas": ["L > 1: X y Y aparecen juntos más de lo esperado.", "L = 1: independencia."]}]}}
    json.dump(e, open(os.path.join(AQUI, "entrega_prueba.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
