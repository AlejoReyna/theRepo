#!/usr/bin/env python3
"""Arma Demostración.xlsx del árbol de mínima entropía a partir de traza.json.

Hojas: Resultado, Datos, Nivel1..NivelK (una por nivel, R2), Reglas, [Comparacion], Control.
Todo conteo es una fórmula SUMPRODUCT(1*EXACT(...)*...) sobre la hoja Datos:
  * EXACT distingue mayúsculas («IQ Floor Model» ≠ «iQ Floor Model»);
  * SUMPRODUCT no trata «*» ni «?» como comodines, a diferencia de COUNTIFS (T20).
Colores (presentacion.md §1): azul = dato tecleado; negro = fórmula de la hoja;
verde = fórmula que trae datos de otra hoja.

Uso: .venv/bin/python excel_arbol.py INCISO_DIR [--comparacion comparacion.csv]
     (lee INCISO_DIR/traza.json, INCISO_DIR/datos/parametros.json y el CSV)
"""
import argparse
import csv
import json
import os

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter as L

AZUL = Font(color="1F4E9E")
AZUL_N = Font(color="1F4E9E", bold=True)
NEGRO = Font(color="000000")
NEGRO_N = Font(color="000000", bold=True)
VERDE = Font(color="1E7B34")
VERDE_N = Font(color="1E7B34", bold=True)
TITULO = Font(bold=True, size=13)
ENC = PatternFill("solid", fgColor="DDE4EE")
NODO = PatternFill("solid", fgColor="F3E9D2")
DEC = PatternFill("solid", fgColor="E2F0D9")
FINO = Border(bottom=Side(style="thin", color="999999"))
UMBRAL = "1E-12"


def q(s):
    """Texto como literal de fórmula."""
    return '"' + str(s).replace('"', '""') + '"'


class Libro:
    def __init__(self, traza, filas, encabezado):
        self.t = traza
        self.d = traza["datos"]
        self.clases = self.d["clases"]
        self.k = len(self.clases)
        self.wb = Workbook()
        self.n = len(filas)
        self.col = {nombre: L(i + 1) for i, nombre in enumerate(encabezado)}
        self.filas = filas
        self.encabezado = encabezado
        self.control = []          # (concepto, referencia Excel, valor de la traza, tipo)

    def rango(self, atributo):
        c = self.col[atributo]
        return "Datos!$%s$2:$%s$%d" % (c, c, self.n + 1)

    def conds(self, ruta_celdas):
        """ruta_celdas: lista de (atributo, referencia de celda con el valor)."""
        return ["EXACT(%s,%s)" % (self.rango(a), ref) for a, ref in ruta_celdas]

    def conteo(self, ruta_celdas, ref_clase):
        partes = ["1"] + self.conds(ruta_celdas) + ["EXACT(%s,%s)" % (self.rango(self.d["clase"]), ref_clase)]
        return "=SUMPRODUCT(" + "*".join(partes) + ")"

    # ---------------------------------------------------------------- Datos
    def hoja_datos(self):
        ws = self.wb.create_sheet("Datos")
        for j, nombre in enumerate(self.encabezado, 1):
            c = ws.cell(1, j, nombre)
            c.font, c.fill = NEGRO_N, ENC
        for i, f in enumerate(self.filas, 2):
            for j, nombre in enumerate(self.encabezado, 1):
                ws.cell(i, j, f[nombre]).font = AZUL
        for j in range(1, len(self.encabezado) + 1):
            ws.column_dimensions[L(j)].width = 26
        ws.freeze_panes = "A2"
        nota = len(self.encabezado) + 2
        ws.cell(1, nota, "Notas").font = NEGRO_N
        r = 2
        for a, k in self.d["recodificados"].items():
            ws.cell(r, nota, "%s: %d celdas vacías se escribieron como «%s» (T16)." % (a, k, self.d["vacio"]))
            r += 1
        ws.cell(r, nota, "Clase: %s. Atributos: %s (todos, R1)." % (self.d["clase"], ", ".join(self.d["atributos"])))
        ws.column_dimensions[L(nota)].width = 70

    # ---------------------------------------------------------------- Niveles
    def bloque_nodo(self, ws, r, nodo):
        """Escribe un nodo impuro con todos sus candidatos. Devuelve la fila siguiente."""
        k = self.k
        cH, cP, cA = L(3 + k), L(4 + k), L(5 + k)        # columnas H, peso, aporte
        ruta = nodo["ruta"]
        ws.cell(r, 1, "Nodo %s" % nodo["id"]).font = NEGRO_N
        ws.cell(r, 2, "Ruta:").font = NEGRO_N
        celdas_ruta = []
        for i, (a, v) in enumerate(ruta):
            ws.cell(r, 3 + 2 * i, a).font = AZUL
            cv = ws.cell(r, 4 + 2 * i, v)
            cv.font = AZUL_N
            celdas_ruta.append((a, "$%s$%d" % (L(4 + 2 * i), r)))
        if not ruta:
            ws.cell(r, 3, "(raíz: todos los registros)").font = AZUL
        for j in range(1, 6 + k):
            ws.cell(r, j).fill = NODO
        r += 1
        # fila de clases del nodo
        ws.cell(r, 1, "Clase →").font = NEGRO_N
        ws.cell(r, 2, "n").font = NEGRO_N
        for j, c in enumerate(self.clases):
            ws.cell(r, 3 + j, c).font = NEGRO_N
        ws.cell(r, 3 + k, "H(nodo)").font = NEGRO_N
        for j in range(1, 4 + k):
            ws.cell(r, j).fill = ENC
        hdr = r
        r += 1
        ws.cell(r, 1, "Conteo del nodo").font = NEGRO
        for j in range(k):
            ws.cell(r, 3 + j, self.conteo(celdas_ruta, "%s$%d" % (L(3 + j), hdr))).font = VERDE
        ws.cell(r, 2, "=SUM(C%d:%s%d)" % (r, L(2 + k), r)).font = NEGRO
        ws.cell(r, 3 + k, "=IF(B{r}=0,0,-SUMPRODUCT((C{r}:{e}{r}>0)*(C{r}:{e}{r}/B{r}),LOG(C{r}:{e}{r}/B{r}+(C{r}:{e}{r}=0),2)))".format(
            r=r, e=L(2 + k))).font = NEGRO_N
        n_ref, h_ref = "$B$%d" % r, "$%s$%d" % (L(3 + k), r)
        self.control.append(("%s H(nodo)" % nodo["id"], "'%s'!%s" % (ws.title, h_ref.replace("$", "")), nodo["H"], "num"))
        self.control.append(("%s n" % nodo["id"], "'%s'!%s" % (ws.title, n_ref.replace("$", "")), nodo["n"], "num"))
        r += 2
        resumen = []        # (atributo, celda E, celda ganancia, celda razón)
        for cand in nodo["candidatos"]:
            a = cand["atributo"]
            ws.cell(r, 1, "Atributo: %s" % a).font = NEGRO_N
            r += 1
            ws.cell(r, 1, a).font = NEGRO_N
            ws.cell(r, 2, "n").font = NEGRO_N
            for j, c in enumerate(self.clases):
                ws.cell(r, 3 + j, c).font = NEGRO_N
            ws.cell(r, 3 + k, "H(Sv)").font = NEGRO_N
            ws.cell(r, 4 + k, "peso |Sv|/|S|").font = NEGRO_N
            ws.cell(r, 5 + k, "aporte peso·H").font = NEGRO_N
            for j in range(1, 6 + k):
                ws.cell(r, j).fill = ENC
            th = r
            r += 1
            primera = r
            for fila in cand["tabla"]:
                ws.cell(r, 1, fila["valor"]).font = AZUL
                cr = celdas_ruta + [(a, "$A%d" % r)]
                for j in range(k):
                    ws.cell(r, 3 + j, self.conteo(cr, "%s$%d" % (L(3 + j), th))).font = VERDE
                ws.cell(r, 2, "=SUM(C%d:%s%d)" % (r, L(2 + k), r)).font = NEGRO
                ws.cell(r, 3 + k, "=IF(B{r}=0,0,-SUMPRODUCT((C{r}:{e}{r}>0)*(C{r}:{e}{r}/B{r}),LOG(C{r}:{e}{r}/B{r}+(C{r}:{e}{r}=0),2)))".format(
                    r=r, e=L(2 + k))).font = NEGRO
                ws.cell(r, 4 + k, "=B%d/%s" % (r, n_ref)).font = NEGRO
                ws.cell(r, 5 + k, "=%s%d*%s%d" % (cP, r, cH, r)).font = NEGRO
                r += 1
            ultima = r - 1
            etiquetas = [("E(%s) = Σ aporte" % a, "=SUM(%s%d:%s%d)" % (cA, primera, cA, ultima)),
                         ("Ganancia = H(nodo) − E", None),
                         ("Split info = −Σ peso·log2(peso)", "=-SUMPRODUCT(%s%d:%s%d,LOG(%s%d:%s%d,2))" % (
                             cP, primera, cP, ultima, cP, primera, cP, ultima)),
                         ("Razón de ganancia (comentario, no decide)", None)]
            fe = r
            ws.cell(r, 1, etiquetas[0][0]).font = NEGRO_N
            ws.cell(r, 5 + k, etiquetas[0][1]).font = NEGRO_N
            ws.cell(r + 1, 1, etiquetas[1][0]).font = NEGRO_N
            ws.cell(r + 1, 5 + k, "=%s-%s%d" % (h_ref, cA, fe)).font = NEGRO_N
            ws.cell(r + 2, 1, etiquetas[2][0]).font = NEGRO
            ws.cell(r + 2, 5 + k, etiquetas[2][1]).font = NEGRO
            ws.cell(r + 3, 1, etiquetas[3][0]).font = NEGRO
            ws.cell(r + 3, 5 + k, '=IF(%s%d>%s,%s%d/%s%d,"—")' % (cA, r + 2, UMBRAL, cA, r + 1, cA, r + 2)).font = NEGRO
            resumen.append((a, "%s%d" % (cA, fe), "%s%d" % (cA, fe + 1), "%s%d" % (cA, fe + 3)))
            self.control.append(("%s E(%s)" % (nodo["id"], a), "'%s'!%s%d" % (ws.title, cA, fe), cand["E"], "num"))
            self.control.append(("%s ganancia(%s)" % (nodo["id"], a), "'%s'!%s%d" % (ws.title, cA, fe + 1), cand["ganancia"], "num"))
            r += 5
        # resumen del nodo y decisión
        ws.cell(r, 1, "Decisión del nodo %s" % nodo["id"]).font = NEGRO_N
        r += 1
        ws.cell(r, 1, "Atributo").font = NEGRO_N
        ws.cell(r, 2, "E(A)").font = NEGRO_N
        ws.cell(r, 3, "Ganancia").font = NEGRO_N
        ws.cell(r, 4, "Razón").font = NEGRO_N
        for j in range(1, 5):
            ws.cell(r, j).fill = ENC
        r += 1
        p = r
        for a, ce, cg, cz in resumen:
            ws.cell(r, 1, a).font = AZUL
            ws.cell(r, 2, "=" + ce).font = NEGRO
            ws.cell(r, 3, "=" + cg).font = NEGRO
            ws.cell(r, 4, "=" + cz).font = NEGRO
            r += 1
        u = r - 1
        mayor = "INDEX($C${h}:${e}${h},MATCH(MAX($C${c}:${e}${c}),$C${c}:${e}${c},0))".format(
            h=hdr, c=hdr + 1, e=L(2 + k))
        f = '=IF(MAX(C{p}:C{u})<={tol},"hoja "&{may},"dividir por "&INDEX(A{p}:A{u},MATCH(MIN(B{p}:B{u}),B{p}:B{u},0)))'.format(
            p=p, u=u, tol=UMBRAL, may=mayor)
        ws.cell(r, 1, "Regla: menor E(A); si la mejor ganancia es 0, hoja con la clase mayoritaria").font = NEGRO
        c = ws.cell(r, 3, f)
        c.font = NEGRO_N
        for j in range(1, 6):
            ws.cell(r, j).fill = DEC
        dec = nodo["decision"]
        texto = ("dividir por %s" % dec["atributo"]) if dec["tipo"] == "dividir" else ("hoja %s" % dec["clase"])
        self.control.append(("%s decisión" % nodo["id"], "'%s'!C%d" % (ws.title, r), texto, "txt"))
        return r + 3

    def hojas_niveles(self):
        for niv in self.t["niveles"]:
            ws = self.wb.create_sheet("Nivel%d" % niv["nivel"])
            ws.cell(1, 1, "Nivel %d: cada nodo impuro con la tabla por valor de cada atributo candidato (R2)" % niv["nivel"]).font = TITULO
            ws.cell(2, 1, "H = −Σ p·log2 p; E(A) = Σ |Sv|/|S|·H(Sv); Ganancia = H − E(A) (EJ26-14 p.3, ecs. 2.1–2.3). "
                          "Se divide por la menor E(A); un nodo es hoja si es puro, si la mejor ganancia es 0 o si no quedan atributos.")
            r = 4
            for nodo in niv["nodos"]:
                if nodo["candidatos"]:
                    r = self.bloque_nodo(ws, r, nodo)
            ws.column_dimensions["A"].width = 44
            for j in range(2, 6 + self.k):
                ws.column_dimensions[L(j)].width = 17

    # ---------------------------------------------------------------- Reglas
    def hoja_reglas(self):
        ws = self.wb.create_sheet("Reglas")
        hojas = self.t["hojas"]
        prof = max(len(h["ruta"]) for h in hojas)
        k = self.k
        ws.cell(1, 1, "Hojas del árbol (reglas SI–ENTONCES) y exactitud de re-sustitución").font = TITULO
        enc = ["Hoja"]
        for i in range(prof):
            enc += ["Atributo %d" % (i + 1), "Valor %d" % (i + 1)]
        enc += list(self.clases) + ["n", "Clase de la hoja", "Aciertos", "Profundidad", "Motivo"]
        for j, e in enumerate(enc, 1):
            c = ws.cell(3, j, e)
            c.font, c.fill = NEGRO_N, ENC
        c0 = 2 + 2 * prof                     # primera columna de clases
        r = 4
        for i, h in enumerate(hojas, 1):
            ws.cell(r, 1, "H%d" % i).font = NEGRO
            celdas = []
            for j, (a, v) in enumerate(h["ruta"]):
                ws.cell(r, 2 + 2 * j, a).font = AZUL
                ws.cell(r, 3 + 2 * j, v).font = AZUL
                celdas.append((a, "$%s%d" % (L(3 + 2 * j), r)))
            for j in range(k):
                ws.cell(r, c0 + j, self.conteo(celdas, "%s$3" % L(c0 + j))).font = VERDE
            rc = "%s%d:%s%d" % (L(c0), r, L(c0 + k - 1), r)
            ws.cell(r, c0 + k, "=SUM(%s)" % rc).font = NEGRO
            ws.cell(r, c0 + k + 1, "=INDEX($%s$3:$%s$3,MATCH(MAX(%s),%s,0))" % (L(c0), L(c0 + k - 1), rc, rc)).font = NEGRO
            ws.cell(r, c0 + k + 2, "=MAX(%s)" % rc).font = NEGRO
            ws.cell(r, c0 + k + 3, len(h["ruta"])).font = AZUL
            ws.cell(r, c0 + k + 4, h["motivo"]).font = AZUL
            r += 1
        u = r - 1
        ca = L(c0 + k + 2)
        ws.cell(r + 1, 1, "Hojas").font = NEGRO_N
        ws.cell(r + 1, 2, "=COUNTA(A4:A%d)" % u).font = NEGRO_N
        ws.cell(r + 2, 1, "Aciertos").font = NEGRO_N
        ws.cell(r + 2, 2, "=SUM(%s4:%s%d)" % (ca, ca, u)).font = NEGRO_N
        ws.cell(r + 3, 1, "Registros").font = NEGRO_N
        ws.cell(r + 3, 2, "=COUNTA(%s)" % self.rango(self.d["clase"])).font = VERDE_N
        ws.cell(r + 4, 1, "Exactitud de re-sustitución").font = NEGRO_N
        ws.cell(r + 4, 2, "=B%d/B%d" % (r + 2, r + 3)).font = NEGRO_N
        ws.cell(r + 4, 2).number_format = "0.00%"
        ws.cell(r + 5, 1, "Profundidad").font = NEGRO_N
        cp = L(c0 + k + 3)
        ws.cell(r + 5, 2, "=MAX(%s4:%s%d)" % (cp, cp, u)).font = NEGRO_N
        res = self.t["resumen"]
        self.control += [("Hojas", "Reglas!B%d" % (r + 1), res["hojas"], "num"),
                         ("Aciertos", "Reglas!B%d" % (r + 2), res["aciertos"], "num"),
                         ("Exactitud", "Reglas!B%d" % (r + 4), res["exactitud"], "num"),
                         ("Profundidad", "Reglas!B%d" % (r + 5), res["profundidad"], "num")]
        self.reglas_ref = {"hojas": "Reglas!B%d" % (r + 1), "aciertos": "Reglas!B%d" % (r + 2),
                           "exactitud": "Reglas!B%d" % (r + 4), "profundidad": "Reglas!B%d" % (r + 5)}
        ws.column_dimensions["A"].width = 30
        for j in range(2, c0 + k + 5):
            ws.column_dimensions[L(j)].width = 18
        ws.freeze_panes = "B4"

    # ---------------------------------------------------------------- Comparación con R
    def hoja_comparacion(self, ruta_csv):
        ws = self.wb.create_sheet("Comparacion")
        ws.cell(1, 1, "Comparación del árbol de mínima entropía con los árboles de R").font = TITULO
        with open(ruta_csv, newline="", encoding="utf-8") as fh:
            filas = list(csv.reader(fh))
        for i, fila in enumerate(filas, 3):
            for j, v in enumerate(fila, 1):
                c = ws.cell(i, j, v)
                c.font = NEGRO_N if i == 3 else AZUL
                if i == 3:
                    c.fill = ENC
        ws.cell(len(filas) + 4, 1, "Valores copiados de salida_R.txt (azul). La fila ID3 se contrasta en Control.").font = NEGRO
        for j in range(1, len(filas[0]) + 1):
            ws.column_dimensions[L(j)].width = 24

    # ---------------------------------------------------------------- Control
    def hoja_control(self):
        ws = self.wb.create_sheet("Control")
        ws.cell(1, 1, "Control: cada cifra del Excel contra traza.json (resolver.py)").font = TITULO
        for j, e in enumerate(["Concepto", "Excel", "Traza", "Diferencia", "¿Coincide?"], 1):
            c = ws.cell(3, j, e)
            c.font, c.fill = NEGRO_N, ENC
        r = 4
        for concepto, ref, valor, tipo in self.control:
            ws.cell(r, 1, concepto).font = NEGRO
            ws.cell(r, 2, "=" + ref).font = VERDE
            ws.cell(r, 3, valor).font = AZUL
            if tipo == "num":
                ws.cell(r, 4, "=B%d-C%d" % (r, r)).font = NEGRO
                ws.cell(r, 5, '=IF(ABS(D%d)<=1E-9,"sí","NO")' % r).font = NEGRO_N
            else:
                ws.cell(r, 5, '=IF(EXACT(B%d,C%d),"sí","NO")' % (r, r)).font = NEGRO_N
            r += 1
        ws.cell(r + 1, 1, "Comprobaciones").font = NEGRO_N
        ws.cell(r + 1, 2, "=COUNTA(E4:E%d)" % (r - 1)).font = NEGRO_N
        ws.cell(r + 2, 1, "Coinciden").font = NEGRO_N
        ws.cell(r + 2, 2, '=COUNTIF(E4:E%d,"sí")' % (r - 1)).font = NEGRO_N
        self.control_ref = ("Control!B%d" % (r + 1), "Control!B%d" % (r + 2))
        ws.column_dimensions["A"].width = 40
        for j in "BCDE":
            ws.column_dimensions[j].width = 22

    # ---------------------------------------------------------------- Resultado
    def hoja_resultado(self):
        ws = self.wb["Resultado"]
        d, res = self.d, self.t["resumen"]
        ws.cell(1, 1, "Árbol de decisión de mínima entropía (ID3), calculado por niveles").font = TITULO
        ws.cell(2, 1, self.t.get("problema", "")).font = NEGRO
        filas = [
            ("Registros", "=COUNTA(%s)" % self.rango(d["clase"]), VERDE_N),
            ("Clase", d["clase"], AZUL),
            ("Atributos evaluados (todos, R1)", ", ".join(d["atributos"]), AZUL),
            ("H(%s) en la raíz" % d["clase"], "=Nivel1!%s" % self._celda_h_raiz, VERDE_N),
            ("Decisión en la raíz", "=Nivel1!%s" % self._celda_dec_raiz, VERDE_N),
            ("Hojas", "=" + self.reglas_ref["hojas"], VERDE_N),
            ("Profundidad", "=" + self.reglas_ref["profundidad"], VERDE_N),
            ("Aciertos", "=" + self.reglas_ref["aciertos"], VERDE_N),
            ("Exactitud de re-sustitución", "=" + self.reglas_ref["exactitud"], VERDE_N),
            ("Control: cifras que coinciden con resolver.py", "=%s&\" de \"&%s" % (self.control_ref[1], self.control_ref[0]), VERDE_N),
        ]
        for i, (a, b, fuente) in enumerate(filas, 4):
            ws.cell(i, 1, a).font = NEGRO_N
            c = ws.cell(i, 2, b)
            c.font = fuente
        ws.cell(12, 2).number_format = "0.00%"
        nota = self._nota_r1()
        if nota:
            ws.cell(15, 1, "Comentario (después del resultado, R1)").font = NEGRO_N
            ws.cell(16, 1, nota).alignment = Alignment(wrap_text=True, vertical="top")
            ws.merge_cells("A16:B19")
        ws.cell(21, 1, "Colores: azul = dato tecleado; negro = fórmula de esta hoja; verde = fórmula que trae datos de otra hoja.")
        ws.column_dimensions["A"].width = 48
        ws.column_dimensions["B"].width = 60

    def _nota_r1(self):
        raiz = self.t["niveles"][0]["nodos"][0]
        cands = raiz["candidatos"]
        if not cands:
            return ""
        por_e = min(cands, key=lambda c: c["E"])
        con_razon = [c for c in cands if c["razon"] is not None]
        por_r = max(con_razon, key=lambda c: c["razon"]) if con_razon else por_e
        if por_r["atributo"] == por_e["atributo"]:
            return ""
        return ("%s tiene %d valores distintos y la menor E(A) = %.4f, así que el árbol de mínima entropía lo pone en la raíz. "
                "La razón de ganancia de C4.5 elegiría %s (%.4f contra %.4f), por el sesgo de ID3 hacia atributos con muchos valores. "
                "Se informa como comentario; el método pedido es mínima entropía y no excluye atributos." % (
                    por_e["atributo"], self.d["valores_distintos"][por_e["atributo"]], por_e["E"],
                    por_r["atributo"], por_r["razon"], por_e["razon"] or 0))

    def construir(self, comparacion=None):
        ws = self.wb.active
        ws.title = "Resultado"
        self.hoja_datos()
        self.hojas_niveles()
        # celdas de la raíz (primer bloque de Nivel1)
        wsn = self.wb["Nivel1"]
        for row in wsn.iter_rows(min_row=1, max_row=12):
            for c in row:
                if isinstance(c.value, str) and c.value.startswith("=IF(B") and "SUMPRODUCT((C" in c.value:
                    self._celda_h_raiz = c.coordinate
                    break
            if hasattr(self, "_celda_h_raiz"):
                break
        for row in wsn.iter_rows():
            for c in row:
                if isinstance(c.value, str) and c.value.startswith('=IF(MAX(C') and "dividir por" in c.value:
                    self._celda_dec_raiz = c.coordinate
                    break
            if hasattr(self, "_celda_dec_raiz"):
                break
        self.hoja_reglas()
        if comparacion:
            self.hoja_comparacion(comparacion)
        self.hoja_control()
        self.hoja_resultado()
        return self.wb


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inciso")
    ap.add_argument("--comparacion")
    ap.add_argument("--salida")
    a = ap.parse_args()
    with open(os.path.join(a.inciso, "traza.json"), encoding="utf-8") as fh:
        traza = json.load(fh)
    with open(os.path.join(a.inciso, "datos", "parametros.json"), encoding="utf-8") as fh:
        par = json.load(fh)
    ruta = os.path.join(a.inciso, "datos", par["archivo"])
    with open(ruta, newline="", encoding="utf-8-sig") as fh:
        lector = csv.DictReader(fh)
        encabezado = lector.fieldnames
        filas = []
        for f in lector:
            for col in encabezado:
                if col != par["clase"] and (f[col] is None or f[col].strip() == ""):
                    f[col] = par.get("vacio", "Sin especificar")
            filas.append(f)
    libro = Libro(traza, filas, encabezado)
    wb = libro.construir(a.comparacion)
    salida = a.salida or os.path.join(a.inciso, "Demostración.xlsx")
    wb.save(salida)
    print("Excel: %s (%d comprobaciones en Control)" % (salida, len(libro.control)))


if __name__ == "__main__":
    main()
