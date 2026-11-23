"""Oráculo de regresión stepwise con AIC (OD/AM R.pdf p.20-24), independiente de R.

Cada modelo candidato se ajusta por ecuaciones normales en fracciones exactas (XᵀX se arma una
sola vez con todas las columnas; cada submodelo usa su submatriz). Una columna que no aumenta el
rango queda como alias y no cuenta como parámetro, igual que en lm.

AIC = n·ln(RSS/n) + 2k (extractAIC de R para lm). Difiere de la fórmula de p.21,
AIC = 2k − 2 ln L, en la constante n(ln 2π + 1) + 2, la misma para todos los modelos con los mismos
datos; el orden de los modelos, que es lo único que usa el método (p.22), no cambia.

Reglas de decisión, tomadas de MASS::stepAIC 7.3 (la función que llaman p.23-24):
1. Si al quitar un término el número de parámetros no cambia (Df = 0, alias) y el AIC no cambia
   en más de 0.01, se quita primero el último de esos términos, sin comparar con los demás.
2. Si no, se ordenan «<none>», los «− término» del modelo y los «+ término» del alcance que falten
   (según la dirección) por AIC, sin las filas con Df = 0; si el mejor es «<none>», se detiene.
3. Después del cambio, si AIC nuevo ≥ AIC anterior + 1e−7, se detiene sin aceptar el cambio.
"""
import math
from fractions import Fraction


def _num(v):
    return Fraction(v.strip())


class Ajustador:
    def __init__(self, filas, y, predictores):
        self.pred = list(predictores)
        self.n = len(filas)
        cols = [[Fraction(1)] * self.n]
        self.nombres_col = ["(Intercept)"]
        self.term_cols = {}
        for p in self.pred:
            vals = [f[p] for f in filas]
            try:
                cols.append([_num(v) for v in vals])
                self.term_cols[p] = [len(cols) - 1]
                self.nombres_col.append(p)
            except (ValueError, ZeroDivisionError):
                lv = sorted(set(vals))
                idxs = []
                for nv in lv[1:]:
                    cols.append([Fraction(1) if v == nv else Fraction(0) for v in vals])
                    idxs.append(len(cols) - 1)
                    self.nombres_col.append("%s%s" % (p, nv))
                self.term_cols[p] = idxs
        yy = [_num(f[y]) for f in filas]
        m = len(cols)
        self.XtX = [[sum(a * b for a, b in zip(cols[i], cols[j])) for j in range(m)] for i in range(m)]
        self.Xty = [sum(a * b for a, b in zip(cols[i], yy)) for i in range(m)]
        self.yty = sum(v * v for v in yy)
        self._cache = {}

    def ajustar(self, terminos):
        """Devuelve (RSS exacto, k parámetros sin alias, coeficientes {nombre: Fraction|None})."""
        clave = tuple(sorted(terminos, key=self.pred.index))
        if clave in self._cache:
            return self._cache[clave]
        idx = [0] + [j for t in clave for j in self.term_cols[t]]
        usadas = []                     # en orden de columnas: la que no aumenta el rango es alias
        for j in idx:
            if _rango_completo([[self.XtX[a][b] for b in usadas + [j]] for a in usadas + [j]]):
                usadas.append(j)
        A = [[self.XtX[a][b] for b in usadas] for a in usadas]
        b = [self.Xty[a] for a in usadas]
        beta = _resolver(A, b)
        rss = self.yty - sum(bi * xi for bi, xi in zip(beta, b))
        coef = {self.nombres_col[j]: None for j in idx}
        for j, bj in zip(usadas, beta):
            coef[self.nombres_col[j]] = bj
        res = (rss, len(usadas), coef)
        self._cache[clave] = res
        return res

    def aic(self, terminos):
        rss, k, _ = self.ajustar(terminos)
        return self.n * math.log(float(rss) / self.n) + 2 * k


def _rango_completo(A):
    M = [list(r) for r in A]
    n = len(M)
    for c in range(n):
        piv = next((r for r in range(c, n) if M[r][c] != 0), None)
        if piv is None:
            return False
        M[c], M[piv] = M[piv], M[c]
        for r in range(c + 1, n):
            if M[r][c] != 0:
                f = M[r][c] / M[c][c]
                M[r] = [a - f * bb for a, bb in zip(M[r], M[c])]
    return True


def _resolver(A, b):
    n = len(A)
    M = [list(A[i]) + [b[i]] for i in range(n)]
    for c in range(n):
        piv = next(r for r in range(c, n) if M[r][c] != 0)
        M[c], M[piv] = M[piv], M[c]
        p = M[c][c]
        M[c] = [v / p for v in M[c]]
        for r in range(n):
            if r != c and M[r][c] != 0:
                f = M[r][c]
                M[r] = [a - f * bb for a, bb in zip(M[r], M[c])]
    return [M[i][n] for i in range(n)]


def vecinos(aj, modelo, alcance, atras=True, adelante=True):
    """Filas (cambio, Df, RSS, AIC) como drop1/add1: «<none>», «- t» y «+ t»."""
    rss0, k0, _ = aj.ajustar(modelo)
    filas = [("<none>", None, rss0, aj.aic(modelo))]
    if atras:
        for t in modelo:
            m = [x for x in modelo if x != t]
            rss, k, _ = aj.ajustar(m)
            filas.append(("- " + t, k0 - k, rss, aj.aic(m)))
    if adelante:
        for t in alcance:
            if t not in modelo:
                m = modelo + [t]
                rss, k, _ = aj.ajustar(m)
                filas.append(("+ " + t, k - k0, rss, aj.aic(m)))
    return filas


def stepwise(aj, direccion="both"):
    """Camino de stepAIC: lista de pasos (cambio, gl_resid, RSS, AIC) y modelo final."""
    alcance = list(aj.pred)
    modelo = [] if direccion == "forward" else list(alcance)
    atras, adelante = direccion in ("both", "backward"), direccion in ("both", "forward")
    rss, k, _ = aj.ajustar(modelo)
    aic = aj.aic(modelo)
    pasos = [("", aj.n - k, rss, aic)]
    candidatos_por_paso = []
    while True:
        filas = vecinos(aj, modelo, alcance, atras, adelante)
        candidatos_por_paso.append(filas)
        cambio = None
        if atras:                                            # regla 1 (Df = 0)
            cero = [f for f in filas[1:] if f[0].startswith("- ") and f[1] == 0 and abs(f[3] - filas[0][3]) <= 0.01]
            if cero:
                cambio = cero[-1][0]
        if cambio is None:                                   # regla 2
            orden = sorted([filas[0]] + [f for f in filas[1:] if f[1] != 0], key=lambda f: f[3])
            if orden[0][0] == "<none>":
                break
            cambio = orden[0][0]
        nuevo = [x for x in modelo if x != cambio[2:]] if cambio.startswith("- ") else modelo + [cambio[2:]]
        rss_n, k_n, _ = aj.ajustar(nuevo)
        aic_n = aj.aic(nuevo)
        if aic_n >= aic + 1e-7:                              # regla 3
            break
        modelo, aic = nuevo, aic_n
        pasos.append((cambio, aj.n - k_n, rss_n, aic_n))
    return {"pasos": pasos, "modelo": modelo, "aic": aic, "candidatos": candidatos_por_paso}
