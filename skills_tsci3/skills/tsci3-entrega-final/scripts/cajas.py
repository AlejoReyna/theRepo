#!/usr/bin/env python3
"""Imagen «Procedimiento de resolución»: cinco cajas numeradas unidas por flechas, cada una con su cita [n]
(EF/…/P4_Mochila/Procedimientos.pdf p.1). Se dibuja con Graphviz (dot) a la proporción de la plantilla
(9 006 840 × 1 267 179 EMU ≈ 7.1 : 1).

Uso como módulo: cajas.dibujar(cajas, ruta_png)   cajas = [{"titulo", "texto", "cita"}] × 5
"""
import html
import subprocess
import textwrap


def _celda(i, c):
    txt = c["texto"] + (" [%s]" % c["cita"] if c.get("cita") not in (None, "") else "")
    lineas = "<BR/>".join(html.escape(l) for l in textwrap.wrap(txt, 22))
    return ('<<TABLE BORDER="0" CELLPADDING="1" CELLSPACING="0" WIDTH="150">'
            '<TR><TD><FONT FACE="Times-Bold" POINT-SIZE="12">%d %s</FONT></TD></TR>'
            '<TR><TD><FONT FACE="Times-Roman" POINT-SIZE="11">%s</FONT></TD></TR></TABLE>>') % (i, html.escape(c["titulo"]), lineas)


def dibujar(cajas, ruta_png):
    if len(cajas) != 5:
        raise SystemExit("bloque.json: «cajas» debe tener 5 elementos (tiene %d)" % len(cajas))
    dot = ['digraph G {', 'rankdir=LR; nodesep=0.15; ranksep=0.32; bgcolor="white"; pad=0.05;',
           'node [shape=box, style="rounded", color="#9a9a9a", penwidth=1.2, width=1.95, height=1.3, fixedsize=false, margin="0.08,0.06"];',
           'edge [color="#444444", arrowsize=0.6, penwidth=1.0];']
    for i, c in enumerate(cajas, 1):
        dot.append('c%d [label=%s];' % (i, _celda(i, c)))
    dot.append(" -> ".join("c%d" % i for i in range(1, 6)) + ";")
    dot.append("}")
    subprocess.run(["dot", "-Tpng", "-Gdpi=220", "-o", ruta_png], input="\n".join(dot).encode("utf-8"), check=True)
    return ruta_png
