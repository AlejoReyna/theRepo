"""Lectura de CSV y XLSX solo con la biblioteca estándar.

El XLSX se lee con zipfile + xml (como `MC/P1_REGEVEN_Procesos/Problema_1.py`):
devuelve los valores guardados en caché, no las fórmulas.
"""
import csv
import re
import zipfile
import xml.etree.ElementTree as ET

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"


def leer_csv(ruta, vacio=None, recortar=True):
    """Lista de dicts. Las celdas vacías se convierten en `vacio` (None = se dejan como "")."""
    with open(ruta, newline="", encoding="utf-8-sig") as fh:
        lector = csv.DictReader(fh)
        filas = []
        for f in lector:
            fila = {}
            for k, v in f.items():
                k = k.strip() if (recortar and k) else k
                v = v.strip() if (recortar and isinstance(v, str)) else v
                if vacio is not None and (v is None or v == ""):
                    v = vacio
                fila[k] = v
            filas.append(fila)
    return filas


def _col(ref):
    letras = re.match(r"[A-Z]+", ref).group(0)
    n = 0
    for ch in letras:
        n = n * 26 + (ord(ch) - 64)
    return n - 1, int(ref[len(letras):]) - 1


def hojas_xlsx(ruta):
    with zipfile.ZipFile(ruta) as z:
        libro = ET.fromstring(z.read("xl/workbook.xml"))
        return [h.get("name") for h in libro.find("m:sheets", NS)]


def leer_xlsx(ruta, hoja=None):
    """Matriz (lista de filas) con los valores en caché de una hoja.

    Números → float (o int si es entero), texto → str, vacío → None.
    """
    with zipfile.ZipFile(ruta) as z:
        compartidas = []
        if "xl/sharedStrings.xml" in z.namelist():
            raiz = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in raiz.findall("m:si", NS):
                compartidas.append("".join(t.text or "" for t in si.iter("{%s}t" % NS["m"])))
        libro = ET.fromstring(z.read("xl/workbook.xml"))
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        destino = {r.get("Id"): r.get("Target") for r in rels}
        hojas = libro.find("m:sheets", NS)
        elegida = None
        for h in hojas:
            if hoja is None or h.get("name") == hoja:
                elegida = h
                break
        if elegida is None:
            raise KeyError(f"no existe la hoja {hoja!r}; hay {[h.get('name') for h in hojas]}")
        objetivo = destino[elegida.get(REL)].lstrip("/")
        if not objetivo.startswith("xl/"):
            objetivo = "xl/" + objetivo
        raiz = ET.fromstring(z.read(objetivo))
    celdas = {}
    maxf = maxc = -1
    for c in raiz.iter("{%s}c" % NS["m"]):
        col, fila = _col(c.get("r"))
        tipo = c.get("t")
        v = c.find("m:v", NS)
        if tipo == "inlineStr":
            t = c.find("m:is", NS)
            val = "".join(x.text or "" for x in t.iter("{%s}t" % NS["m"])) if t is not None else None
        elif v is None or v.text is None:
            val = None
        elif tipo == "s":
            val = compartidas[int(v.text)]
        elif tipo in ("str", "e"):
            val = v.text
        elif tipo == "b":
            val = v.text == "1"
        else:
            x = float(v.text)
            val = int(x) if x.is_integer() and "." not in v.text and "E" not in v.text.upper() else x
        celdas[(fila, col)] = val
        maxf, maxc = max(maxf, fila), max(maxc, col)
    return [[celdas.get((f, c)) for c in range(maxc + 1)] for f in range(maxf + 1)]


def tabla_xlsx(ruta, hoja=None, fila_encabezado=0):
    """Lista de dicts usando la fila `fila_encabezado` (base 0) como nombres."""
    m = leer_xlsx(ruta, hoja)
    enc = [("" if x is None else str(x)).strip() for x in m[fila_encabezado]]
    salida = []
    for fila in m[fila_encabezado + 1:]:
        if all(x is None for x in fila):
            continue
        salida.append({enc[i]: (fila[i] if i < len(fila) else None) for i in range(len(enc)) if enc[i]})
    return salida
