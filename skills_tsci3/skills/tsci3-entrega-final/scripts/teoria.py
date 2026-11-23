#!/usr/bin/env python3
"""Parte_teórica (.docx) con el formato de «Teoría_pero_en_word.docx» de EF (copia en assets/teoria_base.docx):
bloque a la derecha con nombre, «Matrícula: …» y «Fecha: …»; título con el estilo Title; preguntas con
Heading 1; respuestas con Normal y List Bullet. No redacta: copia lo que trae entrega.json["teoria"].
"""
import copy
import os

from docx import Document

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "teoria_base.docx")


def construir(teoria, alumno, matricula, fecha, salida):
    doc = Document(BASE)
    body = doc.element.body
    ps = doc.paragraphs
    cab, tit = ps[0], ps[1]
    for el in list(body.iterchildren()):
        if el.tag.endswith("}sectPr") or el is cab._p or el is tit._p:
            continue
        body.remove(el)
    for r in cab.runs[1:]:
        r._r.getparent().remove(r._r)
    cab.runs[0].text = "%s\nMatrícula: %s\nFecha: %s" % (alumno, matricula, fecha)
    for r in tit.runs[1:]:
        r._r.getparent().remove(r._r)
    tit.runs[0].text = teoria["titulo"]
    for i, q in enumerate(teoria["preguntas"], 1):
        doc.add_paragraph("%d. %s" % (i, q["pregunta"]), style="Heading 1")
        for parr in q.get("respuesta", []):
            doc.add_paragraph(parr, style="Normal")
        for v in q.get("vinetas", []):
            doc.add_paragraph(v, style="List Bullet")
    doc.save(salida)
    return salida
