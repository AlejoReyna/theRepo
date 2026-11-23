#!/usr/bin/env python3
"""Recalcula un .xlsx con LibreOffice (sin interfaz) y revisa su hoja Control.

openpyxl escribe fórmulas sin valores en caché; este paso los calcula para que el
Excel abra con números y para comprobar que las fórmulas dan lo mismo que la traza.

  * Usa un perfil propio de LibreOffice con «recalcular siempre al cargar» (OOXMLRecalcMode = 0).
  * Reemplaza el archivo por la versión recalculada (fórmulas + valores).
  * Lee la hoja Control: cada fila con «¿Coincide?» debe decir «sí».

Uso: .venv/bin/python recalcular_excel.py LIBRO.xlsx [--hoja Control] [--columna E]
Sale con 1 si alguna comprobación dice «NO», si hay errores de fórmula o si falta LibreOffice.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

SOFFICE = ["soffice", "/Applications/LibreOffice.app/Contents/MacOS/soffice"]
XCU = """<?xml version="1.0" encoding="UTF-8"?>
<oor:items xmlns:oor="http://openoffice.org/2001/registry" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<item oor:path="/org.openoffice.Office.Calc/Formula/Load"><prop oor:name="OOXMLRecalcMode" oor:op="fuse"><value>0</value></prop></item>
<item oor:path="/org.openoffice.Office.Calc/Formula/Load"><prop oor:name="ODFRecalcMode" oor:op="fuse"><value>0</value></prop></item>
</oor:items>
"""


def soffice():
    for s in SOFFICE:
        if shutil.which(s) or os.path.exists(s):
            return shutil.which(s) or s
    return None


def recalcular(ruta):
    exe = soffice()
    if not exe:
        raise SystemExit("LibreOffice no está instalado (soffice). Instálalo con: brew install --cask libreoffice")
    perfil = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))))), ".lo_perfil")
    user = os.path.join(perfil, "user")
    os.makedirs(user, exist_ok=True)
    with open(os.path.join(user, "registrymodifications.xcu"), "w", encoding="utf-8") as fh:
        fh.write(XCU)
    with tempfile.TemporaryDirectory() as tmp:
        r = subprocess.run([exe, "-env:UserInstallation=file://" + perfil, "--headless", "--calc",
                            "--convert-to", "xlsx:Calc MS Excel 2007 XML", "--outdir", tmp, ruta],
                           capture_output=True, text=True, timeout=900)
        salida = os.path.join(tmp, os.path.basename(ruta))
        if r.returncode != 0 or not os.path.exists(salida):
            raise SystemExit("LibreOffice falló: %s %s" % (r.stdout, r.stderr))
        shutil.copyfile(salida, ruta)


def revisar(ruta, hoja, columna):
    from openpyxl import load_workbook
    wb = load_workbook(ruta, data_only=True)
    errores = []
    for ws in wb.worksheets:
        for fila in ws.iter_rows():
            for c in fila:
                if isinstance(c.value, str) and c.value.startswith("#") and c.value.rstrip("!?0/").upper() in (
                        "#DIV", "#VALUE", "#REF", "#NAME", "#N/A", "#NUM", "#NULL", "ERR:502", "#VALOR"):
                    errores.append("%s!%s = %s" % (ws.title, c.coordinate, c.value))
    malos, total = [], 0
    if hoja in wb.sheetnames:
        ws = wb[hoja]
        col = ord(columna.upper()) - 64
        for r in range(1, ws.max_row + 1):
            v = ws.cell(r, col).value
            if v in ("sí", "NO"):
                total += 1
                if v != "sí":
                    malos.append("%s: Excel %s, traza %s" % (ws.cell(r, 1).value, ws.cell(r, 2).value, ws.cell(r, 3).value))
            elif v is None and ws.cell(r, 1).value and r > 3 and ws.cell(r, 3).value is not None:
                malos.append("%s: sin valor calculado" % ws.cell(r, 1).value)
    return errores, malos, total


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("libro")
    ap.add_argument("--hoja", default="Control")
    ap.add_argument("--columna", default="E")
    ap.add_argument("--sin-recalcular", action="store_true")
    a = ap.parse_args()
    if not a.sin_recalcular:
        recalcular(os.path.abspath(a.libro))
    errores, malos, total = revisar(a.libro, a.hoja, a.columna)
    for e in errores[:20]:
        print("❌ error de fórmula:", e)
    for m in malos[:30]:
        print("❌", m)
    ok = not errores and not malos and total > 0
    print("%s %s: %d comprobaciones en %s, %d no coinciden, %d errores de fórmula" % (
        "✅" if ok else "❌", os.path.basename(a.libro), total, a.hoja, len(malos), len(errores)))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
