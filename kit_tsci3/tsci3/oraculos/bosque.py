"""Oráculo de bosque aleatorio de regresión (OD/AM R.pdf p.54-55), independiente de R.

No vuelve a sortear (la semilla de R no se reproduce en Python); recibe la estructura de cada árbol
(getTree: hijo izquierdo, hijo derecho, variable, punto de corte, estado, predicción) y los conteos
de bootstrap (inbag) y comprueba lo que p.54 dice del método:
  * cada árbol se entrena con una muestra con reemplazo del tamaño del entrenamiento;
  * una observación baja por el árbol (x ≤ corte → izquierda) hasta una hoja;
  * la hoja predice el promedio de y de la muestra bootstrap que cae en ella (con repeticiones);
  * la predicción del bosque es el promedio de los árboles.
IncNodePurity = Σ_árboles Σ_nodos que dividen por la variable [RSS(nodo) − RSS(izq) − RSS(der)]
/ ntree, con RSS de la muestra bootstrap.
"""


def leer_arboles(filas):
    arboles = {}
    for r in filas:
        t = int(r["arbol"])
        arboles.setdefault(t, []).append({
            "izq": int(r["left daughter"]), "der": int(r["right daughter"]), "var": int(r["split var"]),
            "corte": float(r["split point"]), "estado": int(r["status"]), "pred": float(r["prediction"])})
    return arboles


def hoja(arbol, x):
    n = 1
    while arbol[n - 1]["estado"] != -1:
        nd = arbol[n - 1]
        n = nd["izq"] if x[nd["var"] - 1] <= nd["corte"] else nd["der"]
    return n


def predecir(arbol, x):
    return arbol[hoja(arbol, x) - 1]["pred"]


def nodos_de(arbol, x):
    """Camino de nodos (1-based) de la raíz a la hoja."""
    n, camino = 1, [1]
    while arbol[n - 1]["estado"] != -1:
        nd = arbol[n - 1]
        n = nd["izq"] if x[nd["var"] - 1] <= nd["corte"] else nd["der"]
        camino.append(n)
    return camino


def estadisticos_nodo(arbol, Xtr, ytr, conteos):
    """Para cada nodo: (Σw, Σw·y, Σw·y²) con w = veces que la fila entra en la muestra bootstrap."""
    est = [[0.0, 0.0, 0.0] for _ in arbol]
    for x, y, w in zip(Xtr, ytr, conteos):
        if w:
            for n in nodos_de(arbol, x):
                e = est[n - 1]
                e[0] += w
                e[1] += w * y
                e[2] += w * y * y
    return est


def rss(e):
    return e[2] - e[1] * e[1] / e[0] if e[0] else 0.0
