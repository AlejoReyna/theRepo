#!/usr/bin/env python3
"""Arma Demostración.xlsx de k-medoides con la convención de OD/DOLLY LIVES.xlsx Sheet2.

Hojas: Resultado, Datos, Normalizacion, KMeans (una iteración: DC0, DC1, DMIN, pertenencia,
C' = (SUMPRODUCT + C)/(n + 1)), Medoides (distancia a C0' y C1', mínimo, registro elegido con
MATCH, vectores M0 y M1 con INDEX), Asignacion (DM0, DM1, DMIN, pertenencia y costo: las
columnas que el archivo del profesor deja vacías), Distancias (matriz n × n) y Silueta
(a, b, s por registro para el criterio de clase y para PAM), PAM, Control.
Con más de 300 registros se omiten Distancias y Silueta (valores del programa en Resultado).

Uso: .venv/bin/python excel_kmedoides.py INCISO_DIR
"""
import csv
import json
import os
import sys

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter as L

AZUL, NEGRO, VERDE = Font(color="1F4E9E"), Font(color="000000"), Font(color="1E7B34")
NEGRO_N, VERDE_N, TITULO = Font(bold=True), Font(color="1E7B34", bold=True), Font(bold=True, size=13)
ENC = PatternFill("solid", fgColor="DDE4EE")


def enc(ws, fila, nombres, col=1):
    for j, x in enumerate(nombres):
        c = ws.cell(fila, col + j, x)
        c.font, c.fill = NEGRO_N, ENC


def main():
    I = sys.argv[1]
    tr = json.load(open(os.path.join(I, "traza.json"), encoding="utf-8"))
    par = json.load(open(os.path.join(I, "datos", "parametros.json"), encoding="utf-8"))
    cols = tr["columnas"]
    filas = []
    for f in csv.DictReader(open(os.path.join(I, "datos", par["archivo"]), newline="", encoding="utf-8-sig")):
        try:
            filas.append([float(str(f[c]).replace(",", "")) for c in cols])
        except (ValueError, TypeError):
            pass
    n, nv = len(filas), len(cols)
    R0, R1 = 7, 7 + n - 1
    V = [L(j) for j in range(2, nv + 2)]                       # columnas de variables
    NR = lambda c: "Normalizacion!$%s$%d:$%s$%d" % (c, R0, c, R1)
    c, control = tr["clase"], []
    wb = Workbook()
    res = wb.active
    res.title = "Resultado"

    ws = wb.create_sheet("Datos")
    enc(ws, 1, ["Registro"] + cols)
    for i, f in enumerate(filas, 2):
        ws.cell(i, 1, i - 1).font = AZUL
        for j, v in enumerate(f, 2):
            ws.cell(i, j, v).font = AZUL

    wn = wb.create_sheet("Normalizacion")
    wn.cell(1, 1, "y = m·x + b;  m = 1/(máx − mín);  b = −m·mín").font = TITULO
    enc(wn, 2, ["", *cols])
    for r, et in zip(range(3, 7), ("mín", "máx", "m", "b")):
        wn.cell(r, 1, et).font = NEGRO_N
    for j, col in enumerate(V):
        rng = "Datos!%s$2:%s$%d" % (col, col, n + 1)
        wn["%s3" % col], wn["%s4" % col] = "=MIN(%s)" % rng, "=MAX(%s)" % rng
        wn["%s5" % col], wn["%s6" % col] = "=1/(%s4-%s3)" % (col, col), "=-%s5*%s3" % (col, col)
        for i in range(n):
            wn.cell(R0 + i, j + 2, "=%s$5*Datos!%s%d+%s$6" % (col, col, i + 2, col)).font = VERDE
    for i in range(n):
        wn.cell(R0 + i, 1, i + 1).font = AZUL

    def distancia(fila_centro, hoja_centro, nr):
        return "=(%s)^0.5" % "+".join("(%s!%s$%d-Normalizacion!%s%d)^2" % (hoja_centro, col, fila_centro, col, nr) for col in V)

    wk = wb.create_sheet("KMeans")
    wk.cell(1, 1, "Iteración de k-means con C0 = mínimo y C1 = máximo; C' = (Σx·pertenencia + C)/(n + 1) (DOLLY Sheet2 AG2:AR3)").font = TITULO
    enc(wk, 3, ["", *cols])
    for r, et in ((4, "C0"), (5, "C1"), (7, "C0'"), (8, "C1'")):
        wk.cell(r, 1, et).font = NEGRO_N
    for j, col in enumerate(V):
        wk["%s4" % col], wk["%s5" % col] = "=MIN(%s)" % NR(col), "=MAX(%s)" % NR(col)
        wk["%s7" % col] = "=(SUMPRODUCT(%s,$E$12:$E$%d)+%s4)/($E$10+1)" % (NR(col), 11 + n, col)
        wk["%s8" % col] = "=(SUMPRODUCT(%s,$F$12:$F$%d)+%s5)/($F$10+1)" % (NR(col), 11 + n, col)
        control += [("C0' %s" % cols[j], "KMeans!%s7" % col, c["C0_nuevo"][j]), ("C1' %s" % cols[j], "KMeans!%s8" % col, c["C1_nuevo"][j])]
    enc(wk, 11, ["Registro", "DC0", "DC1", "DMIN", "C0", "C1"])
    wk.cell(10, 1, "Sumas").font = NEGRO_N
    for i in range(n):
        r = 12 + i
        wk.cell(r, 1, i + 1).font = AZUL
        wk.cell(r, 2, distancia(4, "KMeans", R0 + i)).font = VERDE
        wk.cell(r, 3, distancia(5, "KMeans", R0 + i)).font = VERDE
        wk.cell(r, 4, "=MIN(B%d:C%d)" % (r, r))
        wk.cell(r, 5, "=IF(D%d=B%d,1,0)" % (r, r))
        wk.cell(r, 6, "=IF(D%d=C%d,1,0)" % (r, r))
    for col in "DEF":
        wk["%s10" % col] = "=SUM(%s12:%s%d)" % (col, col, 11 + n)
    control += [("|C0| k-means", "KMeans!E10", c["n0_kmeans"]), ("|C1| k-means", "KMeans!F10", c["n1_kmeans"])]

    wm = wb.create_sheet("Medoides")
    wm.cell(1, 1, "Medoide = registro más cercano a cada centroide actualizado (DOLLY Sheet2 AF8:AG57 → AG4:AR5)").font = TITULO
    enc(wm, 3, ["Registro", "Dist. a C0'", "Dist. a C1'"])
    for i in range(n):
        r = 4 + i
        wm.cell(r, 1, i + 1).font = AZUL
        wm.cell(r, 2, distancia(7, "KMeans", R0 + i)).font = VERDE
        wm.cell(r, 3, distancia(8, "KMeans", R0 + i)).font = VERDE
    u = 3 + n
    filas_m = [("Mínimo", "=MIN(B4:B%d)" % u, "=MIN(C4:C%d)" % u),
               ("Registro elegido", "=INDEX($A$4:$A$%d,MATCH(B%d,B4:B%d,0))" % (u, u + 2, u),
                "=INDEX($A$4:$A$%d,MATCH(C%d,C4:C%d,0))" % (u, u + 2, u))]
    for k, (et, f0, f1) in enumerate(filas_m):
        wm.cell(u + 2 + k, 1, et).font = NEGRO_N
        wm.cell(u + 2 + k, 2, f0).font = NEGRO_N
        wm.cell(u + 2 + k, 3, f1).font = NEGRO_N
    control += [("Distancia mínima a C0'", "Medoides!B%d" % (u + 2), c["min_dist_C0"]), ("Distancia mínima a C1'", "Medoides!C%d" % (u + 2), c["min_dist_C1"]),
                ("Registro M0", "Medoides!B%d" % (u + 3), c["M0_registro"]), ("Registro M1", "Medoides!C%d" % (u + 3), c["M1_registro"])]
    fm = u + 6
    enc(wm, fm, ["Medoide", *cols])
    for k, (et, ref) in enumerate((("M0", "$B$%d" % (u + 3)), ("M1", "$C$%d" % (u + 3)))):
        wm.cell(fm + 1 + k, 1, et).font = NEGRO_N
        for j, col in enumerate(V):
            wm.cell(fm + 1 + k, j + 2, "=INDEX(%s,%s)" % (NR(col), ref)).font = VERDE
    filaM = {0: fm + 1, 1: fm + 2}

    wa = wb.create_sheet("Asignacion")
    wa.cell(1, 1, "Asignación a los medoides (las columnas DM0, DM1 y pertenencia que el Excel del profesor deja vacías)").font = TITULO
    enc(wa, 3, ["Registro", "DM0", "DM1", "DMIN", "M0", "M1", "Grupo"])
    for i in range(n):
        r = 4 + i
        wa.cell(r, 1, i + 1).font = AZUL
        wa.cell(r, 2, distancia(filaM[0], "Medoides", R0 + i)).font = VERDE
        wa.cell(r, 3, distancia(filaM[1], "Medoides", R0 + i)).font = VERDE
        wa.cell(r, 4, "=MIN(B%d:C%d)" % (r, r))
        wa.cell(r, 5, "=IF(D%d=B%d,1,0)" % (r, r))
        wa.cell(r, 6, "=IF(D%d=C%d,1,0)" % (r, r))
        wa.cell(r, 7, "=IF(E%d=1,1,2)" % r)
    u2 = 3 + n
    for k, (et, f) in enumerate((("|M0|", "=SUM(E4:E%d)" % u2), ("|M1|", "=SUM(F4:F%d)" % u2), ("Costo = ΣDMIN", "=SUM(D4:D%d)" % u2))):
        wa.cell(u2 + 2 + k, 1, et).font = NEGRO_N
        wa.cell(u2 + 2 + k, 2, f).font = NEGRO_N
    control += [("|M0|", "Asignacion!B%d" % (u2 + 2), c["n0"]), ("|M1|", "Asignacion!B%d" % (u2 + 3), c["n1"]),
                ("Costo criterio de clase", "Asignacion!B%d" % (u2 + 4), c["costo"])]

    p = tr.get("pam")
    if p:
        wp = wb.create_sheet("PAM")
        wp.cell(1, 1, "PAM (BUILD + SWAP de resolver.py; T6): medoides que minimizan el costo total").font = TITULO
        wp.cell(2, 1, "Medoides (registros)").font = NEGRO_N
        wp.cell(2, 2, p["medoides_registro"][0]).font = AZUL
        wp.cell(2, 3, p["medoides_registro"][1]).font = AZUL
        enc(wp, 4, ["Registro", "D a medoide 1", "D a medoide 2", "DMIN", "Grupo"])
        for i in range(n):
            r = 5 + i
            wp.cell(r, 1, i + 1).font = AZUL
            for k, colm in enumerate("BC"):
                wp.cell(r, 2 + k, "=(%s)^0.5" % "+".join("(INDEX(%s,$%s$2)-Normalizacion!%s%d)^2" % (NR(col), colm, col, R0 + i) for col in V)).font = VERDE
            wp.cell(r, 4, "=MIN(B%d:C%d)" % (r, r))
            wp.cell(r, 5, "=IF(B%d<=C%d,1,2)" % (r, r))
        wp.cell(n + 6, 1, "Costo PAM").font = NEGRO_N
        wp.cell(n + 6, 2, "=SUM(D5:D%d)" % (n + 4)).font = NEGRO_N
        control.append(("Costo PAM", "PAM!B%d" % (n + 6), p["costo"]))

    if n <= 300:
        wd = wb.create_sheet("Distancias")
        wd.cell(1, 1, "Distancia euclidiana entre registros normalizados").font = TITULO
        for i in range(n):
            wd.cell(2, i + 2, i + 1).font = NEGRO_N
            wd.cell(i + 3, 1, i + 1).font = NEGRO_N
            for j in range(n):
                wd.cell(i + 3, j + 2, "=(%s)^0.5" % "+".join("(Normalizacion!%s%d-Normalizacion!%s%d)^2" % (col, R0 + i, col, R0 + j) for col in V)).font = VERDE
        wsil = wb.create_sheet("Silueta")
        wsil.cell(1, 1, "Silueta s(i) = (b(i) − a(i))/máx{a(i), b(i)} (Novianti et al., ec. 3); a = media a su grupo, b = media al otro").font = TITULO
        bloques = [("Clase", "Asignacion!$G$%d" % 4, "Asignacion!G")]
        if p:
            bloques.append(("PAM", "PAM!$E$5", "PAM!E"))
        enc(wsil, 3, ["Registro"] + [x for nombre, _, _ in bloques for x in ("Grupo %s" % nombre, "a", "b", "s")])
        fila_g = {"Clase": 4, "PAM": 5}
        for i in range(n):
            r = 4 + i
            wsil.cell(r, 1, i + 1).font = AZUL
            fila = "Distancias!$B$%d:$%s$%d" % (i + 3, L(n + 1), i + 3)
            for k, (nombre, _, ref) in enumerate(bloques):
                g0 = fila_g[nombre]
                grupos = "%s$%d:%s$%d" % (ref, g0, ref.split("!")[1], g0 + n - 1)
                cg, ca, cb, cs = [L(2 + 4 * k + x) for x in range(4)]
                wsil["%s%d" % (cg, r)] = "=%s%d" % (ref, g0 + i)
                wsil["%s%d" % (cg, r)].font = VERDE
                trans = "TRANSPOSE(%s)" % grupos
                wsil["%s%d" % (ca, r)] = "=IFERROR(SUMPRODUCT(%s*(%s=%s%d))/(SUMPRODUCT(--(%s=%s%d))-1),0)" % (fila, trans, cg, r, grupos, cg, r)
                wsil["%s%d" % (cb, r)] = "=SUMPRODUCT(%s*(%s<>%s%d))/SUMPRODUCT(--(%s<>%s%d))" % (fila, trans, cg, r, grupos, cg, r)
                wsil["%s%d" % (cs, r)] = "=IF(SUMPRODUCT(--(%s=%s%d))=1,0,(%s%d-%s%d)/MAX(%s%d,%s%d))" % (grupos, cg, r, cb, r, ca, r, ca, r, cb, r)
        for k, (nombre, _, _) in enumerate(bloques):
            cs = L(5 + 4 * k)
            wsil.cell(n + 5, 1, "Silueta media").font = NEGRO_N
            wsil.cell(n + 5, 5 + 4 * k, "=AVERAGE(%s4:%s%d)" % (cs, cs, n + 3)).font = NEGRO_N
            control.append(("Silueta media %s" % nombre, "Silueta!%s%d" % (cs, n + 5), (c if nombre == "Clase" else p)["silueta_media"]))

    wc = wb.create_sheet("Control")
    wc.cell(1, 1, "Control: cifras del Excel contra traza.json (resolver.py)").font = TITULO
    enc(wc, 3, ["Concepto", "Excel", "Traza", "Diferencia", "¿Coincide?"])
    for i, (concepto, ref, v) in enumerate(control, 4):
        wc.cell(i, 1, concepto)
        wc.cell(i, 2, "=" + ref).font = VERDE
        wc.cell(i, 3, v).font = AZUL
        wc.cell(i, 4, "=B%d-C%d" % (i, i))
        wc.cell(i, 5, '=IF(ABS(D%d)<=1E-6*MAX(1,ABS(C%d)),"sí","NO")' % (i, i)).font = NEGRO_N
    uc = len(control) + 3
    wc.cell(uc + 2, 1, "Coinciden").font = NEGRO_N
    wc.cell(uc + 2, 2, '=COUNTIF(E4:E%d,"sí")&" de "&COUNTA(E4:E%d)' % (uc, uc)).font = NEGRO_N
    wc.column_dimensions["A"].width = 28

    res.cell(1, 1, "K-medoides: criterio de clase (DOLLY Sheet2) y PAM").font = TITULO
    filas_r = [("Problema", tr.get("problema", "")), ("Registros", n), ("Variables", ", ".join(cols)),
               ("Medoides de clase (registros)", "=Medoides!B%d&\" y \"&Medoides!C%d" % (u + 3, u + 3)),
               ("|M0|, |M1|", "=Asignacion!B%d&\", \"&Asignacion!B%d" % (u2 + 2, u2 + 3)),
               ("Costo (criterio de clase)", "=Asignacion!B%d" % (u2 + 4)),
               ("Silueta media (clase)", c["silueta_media"])]
    if p:
        filas_r += [("Medoides PAM (registros)", ", ".join(map(str, p["medoides_registro"]))), ("Costo PAM", "=PAM!B%d" % (n + 6)),
                    ("Silueta media (PAM)", p["silueta_media"])]
    filas_r.append(("Control", "=Control!B%d" % (uc + 2)))
    for i, (x, y) in enumerate(filas_r, 3):
        res.cell(i, 1, x).font = NEGRO_N
        res.cell(i, 2, y).font = VERDE_N if isinstance(y, str) and y.startswith("=") else AZUL
    res.cell(len(filas_r) + 4, 1, "T6: el criterio de clase toma el registro más cercano al centroide actualizado; PAM (cluster::pam) "
                                  "busca los medoides que minimizan el costo total. Se entregan los dos, rotulados.")
    res.column_dimensions["A"].width = 34
    wb.save(os.path.join(I, "Demostración.xlsx"))
    print("Excel: %s (%d comprobaciones)" % (os.path.join(I, "Demostración.xlsx"), len(control)))


if __name__ == "__main__":
    main()
