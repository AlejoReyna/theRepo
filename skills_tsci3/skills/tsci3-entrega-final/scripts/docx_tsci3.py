#!/usr/bin/env python3
"""Procedimientos.docx de un problema con el formato de EF/editables/P4_Mochila.docx.

Se abre una COPIA de la plantilla (EG/AGENTS.md prohíbe tocar la original):
  * se conservan, clonados, el párrafo con los dos logotipos anclados y los párrafos del encabezado
    (universidad, facultad, «<Materia>  |  Problema N», alumno, docente), el título, el enunciado,
    el párrafo personal, la tabla de datos, «Procedimiento de resolución», la imagen de las cajas y
    «Fuentes del curso»; se reemplaza solo su texto;
  * se conserva el sectPr final (carta horizontal 15 840 × 12 240, márgenes y pie con PAGE a la derecha);
  * las páginas de pasos, código y comprobación se escriben con los formatos medidos en la plantilla:
    «Paso N» Arial 21 pt negrita + título normal; texto Arial 10 pt; fórmulas centradas Arial Unicode
    MS 11 pt; tablas con encabezado 565656 en blanco y filas alternas DADADA / EFEFEF con bordes
    blancos; código Courier New 8.5 pt sobre F2F2F2 bajo la etiqueta «Código Python» / «Código R».
No calcula nada: todo el texto viene de bloque.json.
"""
import copy
import os

from docx import Document
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Emu

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
PLANTILLA = "/Users/alexis/theCode/newSkills/Endgame/entrega_final/2026-10-15/editables/P4_Mochila.docx"
ANCHO_UTIL = 14180          # dxa: ancho de la tabla de código de la plantilla


def _t(texto):
    texto = str(texto)
    return '<w:t xml:space="preserve">%s</w:t>' % (texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _run(texto, fuente="Arial", sz=20, b=False, color="000000", i=False):
    partes = str(texto).split("\n")
    cuerpo = "<w:br/>".join(_t(p) for p in partes)
    return ('<w:r><w:rPr><w:rFonts w:ascii="{f}" w:hAnsi="{f}" w:eastAsia="{f}" w:cs="{f}"/>{b}{i}<w:color w:val="{c}"/>'
            '<w:sz w:val="{s}"/><w:szCs w:val="{s}"/></w:rPr>{t}</w:r>').format(
        f=fuente, b="<w:b/>" if b else '<w:b w:val="0"/>', i="<w:i/>" if i else "", c=color, s=sz, t=cuerpo)


def _p(runs, jc="left", before=0, after=60, salto=False, keep=False, ind=0):
    return parse_xml('<w:p %s><w:pPr>%s%s<w:spacing w:before="%d" w:after="%d" w:line="240" w:lineRule="auto"/>'
                     '<w:ind w:left="%d" w:right="0" w:firstLine="0"/><w:jc w:val="%s"/></w:pPr>%s</w:p>' % (
                         nsdecls("w"), "<w:pageBreakBefore/>" if salto else "", "<w:keepNext/>" if keep else "",
                         before, after, ind, jc, "".join(runs)))


def _poner_texto(p_el, texto):
    """Reemplaza el texto de un párrafo clonado conservando el rPr de su primer texto y sus dibujos."""
    runs = p_el.findall(qn("w:r"))
    rpr = None
    for r in runs:
        if r.find(qn("w:t")) is not None and rpr is None:
            rp = r.find(qn("w:rPr"))
            rpr = copy.deepcopy(rp) if rp is not None else None
        if r.find(qn("w:drawing")) is None:
            p_el.remove(r)
    for k, parte in enumerate(str(texto).split("\n")):
        r = parse_xml("<w:r %s>%s%s</w:r>" % (nsdecls("w"), "<w:br/>" if k else "", _t(parte)))
        if rpr is not None:
            r.insert(0, copy.deepcopy(rpr))
        p_el.append(r)


def _celda(texto, ancho, fill, color="000000", b=False, fuente="Arial", sz=18, jc="center", borde="FFFFFF"):
    return ('<w:tc><w:tcPr><w:tcW w:w="%d" w:type="dxa"/><w:tcBorders>'
            '<w:top w:val="single" w:sz="8" w:space="0" w:color="{b}"/><w:left w:val="single" w:sz="8" w:space="0" w:color="{b}"/>'
            '<w:bottom w:val="single" w:sz="8" w:space="0" w:color="{b}"/><w:right w:val="single" w:sz="8" w:space="0" w:color="{b}"/>'
            '</w:tcBorders><w:shd w:val="clear" w:color="auto" w:fill="%s"/><w:tcMar><w:top w:w="16" w:type="dxa"/>'
            '<w:left w:w="50" w:type="dxa"/><w:bottom w:w="16" w:type="dxa"/><w:right w:w="50" w:type="dxa"/></w:tcMar>'
            '<w:vAlign w:val="center"/></w:tcPr><w:p><w:pPr><w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/>'
            '<w:jc w:val="%s"/></w:pPr>%s</w:p></w:tc>').replace("{b}", borde) % (ancho, fill, jc, _run(texto, fuente, sz, b, color))


def tabla(filas, anchos=None, sz=18):
    """Tabla del estilo de los pasos (P4_Mochila, tablas 16 y 61): encabezado repetido en cada página."""
    n = max(len(f) for f in filas)
    filas = [list(f) + [""] * (n - len(f)) for f in filas]
    if anchos is None:
        largo = [max(len(str(f[j])) for f in filas) for j in range(n)]
        anchos = [min(max(int(l * (100 if sz <= 16 else 115)) + 250, 1000), 5000) for l in largo]
        if sum(anchos) > ANCHO_UTIL:
            anchos = [int(a * ANCHO_UTIL / sum(anchos)) for a in anchos]
    trs = []
    for k, f in enumerate(filas):
        if k == 0:
            celdas = "".join(_celda(v, a, "565656", "FFFFFF", True, sz=sz) for v, a in zip(f, anchos))
            trs.append('<w:tr><w:trPr><w:cantSplit/><w:tblHeader/></w:trPr>%s</w:tr>' % celdas)
        else:
            fill = "DADADA" if k % 2 else "EFEFEF"
            celdas = "".join(_celda(v, a, fill, fuente="Arial", sz=sz) for v, a in zip(f, anchos))
            trs.append('<w:tr><w:trPr><w:cantSplit/></w:trPr>%s</w:tr>' % celdas)
    return parse_xml('<w:tbl %s><w:tblPr><w:tblW w:w="0" w:type="auto"/><w:jc w:val="center"/><w:tblLayout w:type="fixed"/>'
                     '<w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0" w:firstColumn="1" w:lastColumn="0" w:noHBand="0" w:noVBand="1"/>'
                     '</w:tblPr><w:tblGrid>%s</w:tblGrid>%s</w:tbl>' % (
                         nsdecls("w"), "".join('<w:gridCol w:w="%d"/>' % a for a in anchos), "".join(trs)))


def _bloque_codigo(etiqueta, lineas):
    lab = ('<w:tr><w:tc><w:tcPr><w:tcW w:w="%d" w:type="dxa"/><w:shd w:val="clear" w:color="auto" w:fill="F2F2F2"/></w:tcPr>'
           '<w:p><w:pPr><w:spacing w:before="60" w:after="40"/><w:ind w:left="200"/></w:pPr>%s</w:p></w:tc></w:tr>') % (
        ANCHO_UTIL, _run(etiqueta, "Arial", 20, True))
    ps = "".join('<w:p><w:pPr><w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/><w:ind w:left="100"/></w:pPr>%s</w:p>'
                 % _run(l.replace("\t", "    ") or " ", "Courier New", 17) for l in lineas)
    cod = '<w:tr><w:tc><w:tcPr><w:tcW w:w="%d" w:type="dxa"/><w:shd w:val="clear" w:color="auto" w:fill="F7F7F7"/></w:tcPr>%s</w:tc></w:tr>' % (ANCHO_UTIL, ps)
    return parse_xml('<w:tbl %s><w:tblPr><w:tblW w:w="0" w:type="auto"/><w:tblLayout w:type="fixed"/></w:tblPr>'
                     '<w:tblGrid><w:gridCol w:w="%d"/></w:tblGrid>%s%s</w:tbl>' % (nsdecls("w"), ANCHO_UTIL, lab, cod))


def construir(bloque, enc, png_cajas, fragmentos, salida, base_dir=None):
    """enc: {"materia", "alumno", "docente", "n"}; fragmentos: [(etiqueta, [líneas])]."""
    doc = Document(PLANTILLA)
    body = doc.element.body
    els = list(body.iterchildren())
    sect = copy.deepcopy(els[-1])
    proto = {k: copy.deepcopy(els[i]) for k, i in (("logos", 0), ("facultad", 1), ("materia", 2), ("alumno", 3), ("docente", 4),
                                                    ("titulo", 5), ("enunciado", 6), ("personal", 7), ("datos", 8),
                                                    ("proc", 9), ("imagen", 10), ("fuentes_t", 11), ("fuentes", 12))}
    for e in els:
        body.remove(e)
    add = body.append
    for k in ("logos", "facultad"):
        add(copy.deepcopy(proto[k]))
    for k, txt in (("materia", "%s  |  Problema %s" % (enc["materia"], enc["n"])), ("alumno", enc["alumno"]),
                   ("docente", "Docente: %s" % enc["docente"]), ("titulo", bloque["titulo"]), ("enunciado", bloque["enunciado"])):
        p = copy.deepcopy(proto[k])
        _poner_texto(p, txt)
        add(p)
    if bloque.get("personal"):
        p = copy.deepcopy(proto["personal"])
        _poner_texto(p, bloque["personal"])
        add(p)
    if bloque.get("asignacion"):                       # R3: tabla de asignación por matrícula
        add(tabla(bloque["asignacion"], sz=20))
        add(_p([_run("", sz=8)], after=40))
    # Tabla de datos: se clona la de la plantilla (4 columnas) y se rellenan sus filas
    datos = bloque["datos"]
    t = copy.deepcopy(proto["datos"])
    trs = t.findall(qn("w:tr"))
    cuerpo_proto = trs[1]
    for tr in trs[1:]:
        t.remove(tr)
    for k, fila in enumerate(datos):
        tr = copy.deepcopy(trs[0] if k == 0 else cuerpo_proto)
        for tc, v in zip(tr.findall(qn("w:tc")), list(fila) + [""] * 4):
            _poner_texto(tc.find(qn("w:p")), v)
        t.append(tr)
    t.remove(trs[0])
    add(t)
    add(copy.deepcopy(proto["proc"]))
    p_img = copy.deepcopy(proto["imagen"])
    add(p_img)
    # Imagen nueva de las cajas en el mismo marco (ancho de la plantilla)
    rid, _ = doc.part.get_or_add_image(png_cajas)
    blip = p_img.find(".//" + qn("a:blip"))
    blip.set(qn("r:embed"), rid)
    import struct
    with open(png_cajas, "rb") as fh:            # cabecera IHDR del PNG: ancho y alto en bytes 16-24
        w_px, h_px = struct.unpack(">II", fh.read(24)[16:24])
    ext = p_img.find(".//" + qn("wp:extent"))
    cx = int(ext.get("cx"))
    cy = int(cx * h_px / w_px)
    ext.set("cy", str(cy))
    for e in p_img.iter(qn("a:ext")):
        e.set("cx", str(cx))
        e.set("cy", str(cy))
    add(copy.deepcopy(proto["fuentes_t"]))
    p = copy.deepcopy(proto["fuentes"])
    _poner_texto(p, " ".join("[%d] %s" % (i, f) for i, f in enumerate(bloque["fuentes"], 1)))
    add(p)
    if bloque.get("convencion"):
        add(_p([_run("Convención del desarrollo. ", "Times New Roman", 20, True), _run(bloque["convencion"], "Times New Roman", 20)], before=80))

    for paso in bloque["pasos"]:
        num, _, resto = paso["titulo"].partition(" ")
        num2, _, resto2 = resto.partition(" ")
        cab = "%s %s" % (num, num2) if num.lower() == "paso" else num
        tit = resto2 if num.lower() == "paso" else resto
        add(_p([_run(cab, "Arial", 42, True), _run(" " + tit, "Arial", 42)], salto=True, after=160, keep=True))
        for parr in [x for x in paso.get("texto", "").split("\n\n") if x.strip()]:
            add(_p([_run(parr, "Arial", 20)], after=100))
        for f in paso.get("formulas", []):
            add(_p([_run(f, "Arial Unicode MS", 22)], jc="center", after=60))
        for tb in paso.get("tablas", []):
            if isinstance(tb, dict):
                if tb.get("titulo"):
                    add(_p([_run(tb["titulo"], "Arial", 22, True)], before=120, after=60, keep=True))
                filas = tb["filas"]
            else:
                filas = tb
            add(tabla(filas, sz=16 if len(filas[0]) > 9 else 18))
            if isinstance(tb, dict) and tb.get("nota"):
                add(_p([_run(tb["nota"], "Arial", 18)], before=60))
            add(_p([_run("", sz=8)], after=60))
        for nota in paso.get("notas", []):
            add(_p([_run("• " + nota, "Arial", 20)], after=60))
        for img in paso.get("imagenes", []):
            im_arch = img["archivo"] if isinstance(img, dict) else img
            im_tit = img.get("titulo") if isinstance(img, dict) else None
            im_ruta = im_arch if os.path.isabs(im_arch) or not base_dir else os.path.join(base_dir, im_arch)
            if os.path.exists(im_ruta):
                if im_tit:
                    add(_p([_run(im_tit, "Arial", 20, True)], jc="center", before=80, after=40, keep=True))
                with open(im_ruta, "rb") as fh:
                    w_px, h_px = struct.unpack(">II", fh.read(24)[16:24])
                max_w, max_h = 6800000, 3400000
                esc = min(max_w / max(w_px, 1), max_h / max(h_px, 1))
                p_im = doc.add_paragraph()
                p_im.alignment = 1
                p_im.add_run().add_picture(im_ruta, width=Emu(int(w_px * esc)), height=Emu(int(h_px * esc)))

    add(_p([_run("Código", "Arial", 42, True), _run(" Funciones que hicieron los cálculos", "Arial", 42)], salto=True, after=120))
    if bloque.get("codigo_texto"):
        add(_p([_run(bloque["codigo_texto"], "Arial", 20)], after=120))
    for etiqueta, lineas in fragmentos:
        add(_bloque_codigo(etiqueta, lineas))
        add(_p([_run("", sz=8)], after=80))

    add(_p([_run(bloque.get("comprobacion_titulo", "Comprobación"), "Arial", 30, True)], salto=True, before=100, after=100))
    for parr in [x for x in bloque["comprobacion"].split("\n\n") if x.strip()]:
        add(_p([_run(parr, "Arial", 20)], before=60, after=60))
    if bloque.get("respuesta"):
        add(_p([_run("Respuesta. ", "Arial", 20, True), _run(bloque["respuesta"], "Arial", 20)], before=120))
    add(sect)
    doc.save(salida)
    return salida
