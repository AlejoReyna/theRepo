#!/usr/bin/env python3
"""Elige la skill tsci3-* de un elemento de rúbrica o de un problema de examen (tabla de §3.1 del plan).

Uso:
  python3 seleccionar.py "texto del elemento o del problema" [--json]
Salida: una línea por skill que aplica, con el tema (#) de rubricas.md y la palabra que la activó.
Código de salida: 0 = al menos una skill; 2 = tema sin skill de resolución (AF1 redactada, AF2 sin
fuente, temas solo de PIA: preguntar al usuario); 3 = no se reconoce el texto.

Las reglas van de lo específico a lo general: «k para KNN» va a tsci3-knn antes de que «k» o
«codo» lo manden a k-means; «predictor no binario» va a regresión múltiple antes que «binario».
"""
import json
import re
import sys
import unicodedata


def norm(t):
    t = unicodedata.normalize("NFD", t.lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


# (patrón sobre texto normalizado, skill, temas de rubricas.md, nota)
REGLAS = [
    (r"red(es)? (de )?petri|petri", "tsci3-modelado-procesos", "23", "Petri y su denominación"),
    (r"\bbpmn\b|\byawl\b|\bepc\b|\bedpc\b", "tsci3-modelado-procesos", "24", "diagrama asignado por el último dígito"),
    (r"arbol de proceso|process tree|p ?tree|red causal", "tsci3-modelado-procesos", "25", "modelo asignado por paridad"),
    (r"regeven|registro de eventos|event log", "tsci3-modelado-procesos", "23", "registro de eventos"),
    (r"(determinacion|eleccion|elegir|seleccion)( de)? (la )?k (para|de|en) (el )?knn|k para knn|k en knn", "tsci3-knn", "21", "k para KNN"),
    (r"\bknn\b|vecinos mas cercanos|k vecinos|nearest neighbo", "tsci3-knn", "20", "KNN"),
    (r"matriz de confusion|confusion matrix|confusionmatrix|exactitud|accuracy|precision y recall|sensibilidad", "tsci3-matriz-confusion", "19", "evaluar un clasificador"),
    (r"bosque(s)? aleatorio|random ?forest|randomforest", "tsci3-bosque-aleatorio", "22", "bosque aleatorio"),
    (r"logistic|multinom|\bvif\b|sigmoide", "tsci3-regresion-logistica", "17, 18", "logística binaria o multinomial"),
    (r"stepwise|stepaic|\baic\b|forward|backward|seleccion automatica de variables", "tsci3-stepwise-aic", "14", "selección por AIC"),
    (r"lasso|ridge|glmnet|regulariza", "tsci3-regularizacion", "15, 16", "Lasso o Ridge"),
    (r"breusch|pagan|heterocedastic|bptest", "tsci3-breusch-pagan", "10", "Breusch-Pagan"),
    (r"predictor no binario|no binario|categoric|as\.factor|kitchen sink|regresion multiple|multiple regression", "tsci3-regresion-multiple", "12, 13", "regresión múltiple o con factor"),
    (r"predictor binario|variable binaria|dummy|ficticia", "tsci3-predictor-binario", "11", "predictor binario"),
    (r"minimos cuadrados|least squares|regresion lineal simple|recta de regresion", "tsci3-minimos-cuadrados", "9", "mínimos cuadrados"),
    (r"(arbol(es)? de decision|minima entropia|entropia|\bid3\b|rpart|ctree|gastank)", "tsci3-arbol-decision", "8", "árbol de mínima entropía"),
    (r"episodio", "tsci3-episodios", "7", "episodios"),
    (r"secuencia|cspade|sequential pattern|seqmin", "tsci3-secuencias", "6", "patrones secuenciales"),
    (r"a ?priori|reglas de asociacion|association rule|arules|itemset", "tsci3-apriori", "5", "Apriori"),
    (r"k[- ]?medoid|medoide|\bpam\b|\bclara\b", "tsci3-kmedoides", "4", "k-medoides"),
    (r"k[- ]?means|k[- ]?medias|clustering|agrupamiento|conglomerado|wcss|codo", "tsci3-kmeans", "3", "k-means"),
    (r"normaliza|min-?max|z-?score|scale\(", "tsci3-kmeans", "2", "normalización: va dentro de k-means, k-medoides y KNN (T5); elige la de su método"),
    (r"subset|subconjunto|tratamiento de datos|limpieza|\bexport\b|metro\b|\bmta\b|border crossing|set r\b", "tsci3-subset-r", "1", "subconjuntos y tratamiento con objetivo"),
]

# Temas calificados sin método en las fuentes (rubricas.md, «Sin skill de resolución»; plan §7 B2, B3).
SIN_SKILL = [
    (r"\bdisco\b|separacion disco", "AF2 Disco / Separación Disco (B2: sin fuente del método)"),
    (r"diagrama (de )?clase|diagrama (de )?transicion", "AF2 Diagrama de clase o de transición (B2)"),
    (r"bupa ?r", "AF2 bupaR (B2)"),
    (r"proceso (de )?mineria|fases|\bobj\b|objetivo(s)? (de|del) (wb|datagov|datos gob)|^1\.1\b|world ?bank|datagov|datos\.?gob", "AF1 con respuesta redactada (sin cálculo)"),
    (r"jerarquic|\bward\b|dbscan|\bpca\b|componentes principales|birch|\bsvm\b|tf-?idf", "tema solo de artículos de PIA (B3)"),
]

# S18 en estado P: YAWL, EPC/EDPC y red causal no tienen ejemplo en las fuentes.
ESTADO_P = r"\byawl\b|\bepc\b|\bedpc\b|red causal"


def seleccionar(texto):
    t = norm(texto)
    for pat, nota in SIN_SKILL:
        if re.search(pat, t):
            return {"codigo": 2, "skills": [], "sin_skill": nota}
    out, vistas = [], set()
    for pat, skill, tema, nota in REGLAS:
        m = re.search(pat, t)
        if m and skill not in vistas:
            # «k para KNN» no debe arrastrar k-means por «codo»/«k»; «no binario» no arrastra binario
            if skill == "tsci3-kmeans" and "tsci3-knn" in vistas:
                continue
            if skill == "tsci3-predictor-binario" and "tsci3-regresion-multiple" in vistas:
                continue
            vistas.add(skill)
            out.append({"skill": skill, "tema": tema, "motivo": "«%s» → %s" % (m.group(0), nota)})
    # Un clasificador lleva matriz de confusión aunque el texto no la nombre (S14, S16, S17 la usan).
    if any(o["skill"] in ("tsci3-knn", "tsci3-bosque-aleatorio") for o in out) and "tsci3-matriz-confusion" not in vistas \
            and re.search(r"evalu|desempeno|compar", t):
        out.append({"skill": "tsci3-matriz-confusion", "tema": "19", "motivo": "evaluar el clasificador"})
    if not out:
        return {"codigo": 3, "skills": []}
    res = {"codigo": 0, "skills": out}
    if re.search(ESTADO_P, t):
        res["aviso"] = "YAWL, EPC/EDPC y red causal están en estado P (sin ejemplo en las fuentes): avisar al usuario antes de resolver"
    return res


def main():
    args = [a for a in sys.argv[1:] if a != "--json"]
    r = seleccionar(" ".join(args))
    if "--json" in sys.argv:
        print(json.dumps(r, ensure_ascii=False))
    else:
        if r["codigo"] == 2:
            print("SIN SKILL: %s. Pregunta al usuario cómo proceder." % r["sin_skill"])
        elif r["codigo"] == 3:
            print("NO RECONOCIDO: revisa el texto contra rubricas.md y pregunta al usuario.")
        for o in r["skills"]:
            print("%-28s tema %-6s %s" % (o["skill"], o["tema"], o["motivo"]))
        if r.get("aviso"):
            print("AVISO: " + r["aviso"])
    sys.exit(r["codigo"])


if __name__ == "__main__":
    main()
