#!/usr/bin/env python3
"""Arma Demostración.xlsx de patrones secuenciales (conteo y cociente, como OD/AP (1).xlsx).

Hojas: Resultado, Datos (sequenceID, eventID, ítems), Secuencias (cada secuencia como texto
«|.1.|.3.|.4.5.|»), Ejemplo (los patrones de la secuencia 1, descompuestos a mano),
Nivel1..NivelK (patrones con k ítems: secuencias que lo contienen, N, soporte), Control.
Para patrones con un ítem por elemento el conteo es COUNTIF con comodines «*.a.*|*.b.*»
(el ítem b tiene que estar en un evento posterior); si un elemento tiene varios ítems, el
conteo viene del programa (azul) y lo verifica el oráculo.

Uso: .venv/bin/python excel_secuencias.py INCISO_DIR
"""
import json
import os
import sys

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

AZUL, NEGRO, VERDE = Font(color="1F4E9E"), Font(color="000000"), Font(color="1E7B34")
NEGRO_N, VERDE_N, TITULO = Font(bold=True), Font(color="1E7B34", bold=True), Font(bold=True, size=13)
ENC = PatternFill("solid", fgColor="DDE4EE")


def enc(ws, fila, nombres):
    for j, x in enumerate(nombres, 1):
        c = ws.cell(fila, j, x)
        c.font, c.fill = NEGRO_N, ENC


def codificar(seq):
    return "|" + "|".join("." + ".".join(str(x) for x in e) + "." for e in seq) + "|"


def comodin(patron):
    return "*" + "*|*".join(".%s." % e[0] for e in patron) + "*"


def main():
    I = sys.argv[1]
    tr = json.load(open(os.path.join(I, "traza.json"), encoding="utf-8"))
    n = tr["n"]
    control = []
    wb = Workbook()
    res = wb.active
    res.title = "Resultado"
    ws = wb.create_sheet("Datos")
    enc(ws, 1, ["sequenceID", "eventID", "items"])
    r = 2
    for sid, s in enumerate(tr["secuencias"], 1):
        for eid, e in enumerate(s, 1):
            for j, v in enumerate((sid, eid, " ".join(map(str, e))), 1):
                ws.cell(r, j, v).font = AZUL
            r += 1
    wq = wb.create_sheet("Secuencias")
    enc(wq, 1, ["sequenceID", "Secuencia", "Texto para COUNTIF"])
    for sid, s in enumerate(tr["secuencias"], 1):
        wq.cell(sid + 1, 1, sid).font = AZUL
        wq.cell(sid + 1, 2, "<%s>" % ",".join("{%s}" % ",".join(map(str, e)) for e in s)).font = AZUL
        wq.cell(sid + 1, 3, codificar(s)).font = AZUL
    rng = "Secuencias!$C$2:$C$%d" % (n + 1)
    wq.column_dimensions["B"].width = 30
    wq.column_dimensions["C"].width = 30

    we = wb.create_sheet("Ejemplo")
    we.cell(1, 1, "Secuencia 1 = %s: sus patrones (maxsize %d, maxlen %d)" % (wb["Secuencias"]["B2"].value, tr["maxsize"], tr["maxlen"])).font = TITULO
    enc(we, 3, ["Patrón", "¿La secuencia 1 lo contiene?"])
    for i, p in enumerate(tr["ejemplo_secuencia_1"], 4):
        we.cell(i, 1, p).font = AZUL
        elems = [x.strip("{}").split(",") for x in p.strip("<>").split("},{")]
        if all(len(e) == 1 for e in elems):
            we.cell(i, 2, '=IF(COUNTIF(Secuencias!$C$2,"%s")>0,"sí","no")' % comodin(elems)).font = VERDE
        else:
            we.cell(i, 2, "sí").font = AZUL
    we.cell(len(tr["ejemplo_secuencia_1"]) + 5, 1, "Patrones de la secuencia 1").font = NEGRO_N
    we.cell(len(tr["ejemplo_secuencia_1"]) + 5, 2, '=COUNTIF(B4:B%d,"sí")' % (len(tr["ejemplo_secuencia_1"]) + 3)).font = NEGRO_N
    control.append(("Patrones de la secuencia 1", "Ejemplo!B%d" % (len(tr["ejemplo_secuencia_1"]) + 5), len(tr["ejemplo_secuencia_1"])))
    we.column_dimensions["A"].width = 30

    niveles = {}
    for p in tr["patrones"]:
        niveles.setdefault(sum(len(e) for e in p["patron"]), []).append(p)
    for k in sorted(niveles):
        wn = wb.create_sheet("Nivel%d" % k)
        wn.cell(1, 1, "Patrones con %d ítems: soporte = secuencias que lo contienen / N (support >= %g)" % (k, tr["soporte_min"])).font = TITULO
        wn.cell(2, 1, "N").font = NEGRO_N
        wn.cell(2, 2, "=ROWS(%s)" % rng).font = VERDE_N
        enc(wn, 4, ["Patrón", "Secuencias que lo contienen", "Soporte", "¿Frecuente?", "Origen del conteo"])
        for i, p in enumerate(niveles[k], 5):
            wn.cell(i, 1, p["texto"]).font = AZUL
            if all(len(e) == 1 for e in p["patron"]):
                wn.cell(i, 2, '=COUNTIF(%s,"%s")' % (rng, comodin(p["patron"]))).font = VERDE
                wn.cell(i, 5, "COUNTIF").font = NEGRO
                control.append(("%s" % p["texto"], "Nivel%d!B%d" % (k, i), p["secuencias"]))
            else:
                wn.cell(i, 2, p["secuencias"]).font = AZUL
                wn.cell(i, 5, "programa (elemento con varios ítems)").font = NEGRO
            wn.cell(i, 3, "=B%d/$B$2" % i)
            wn.cell(i, 4, '=IF(C%d>=%s,"sí","no")' % (i, tr["soporte_min"]))
        wn.column_dimensions["A"].width = 34

    wc = wb.create_sheet("Control")
    wc.cell(1, 1, "Control: conteos del Excel contra traza.json (resolver.py)").font = TITULO
    enc(wc, 3, ["Concepto", "Excel", "Traza", "Diferencia", "¿Coincide?"])
    for i, (concepto, ref, v) in enumerate(control, 4):
        wc.cell(i, 1, concepto)
        wc.cell(i, 2, "=" + ref).font = VERDE
        wc.cell(i, 3, v).font = AZUL
        wc.cell(i, 4, "=B%d-C%d" % (i, i))
        wc.cell(i, 5, '=IF(ABS(D%d)<=1E-9,"sí","NO")' % i).font = NEGRO_N
    uc = len(control) + 3
    wc.cell(uc + 2, 1, "Coinciden").font = NEGRO_N
    wc.cell(uc + 2, 2, '=COUNTIF(E4:E%d,"sí")&" de "&COUNTA(E4:E%d)' % (uc, uc)).font = NEGRO_N
    wc.column_dimensions["A"].width = 34

    res.cell(1, 1, "Patrones secuenciales (cspade)").font = TITULO
    for i, (x, y) in enumerate([("Problema", tr["problema"]), ("Secuencias (N)", n), ("support / maxsize / maxlen", "%g / %d / %d" % (
            tr["soporte_min"], tr["maxsize"], tr["maxlen"])), ("Patrones frecuentes", tr["n_patrones"]),
            ("Por número de ítems", ", ".join("%s: %s" % kv for kv in tr["por_numero_de_items"].items())),
            ("Control", "=Control!B%d" % (uc + 2))], 3):
        res.cell(i, 1, x).font = NEGRO_N
        res.cell(i, 2, y).font = VERDE_N if isinstance(y, str) and y.startswith("=") else AZUL
    res.column_dimensions["A"].width = 30
    wb.save(os.path.join(I, "Demostración.xlsx"))
    print("Excel: %s (%d comprobaciones)" % (os.path.join(I, "Demostración.xlsx"), len(control)))


if __name__ == "__main__":
    main()
