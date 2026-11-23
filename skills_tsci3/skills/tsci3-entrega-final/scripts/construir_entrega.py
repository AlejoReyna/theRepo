#!/usr/bin/env python3
"""Arma la entrega de TSCI3 con el formato de EF/1851265_TSOER2.zip (plan §5). No recalcula ningún número.

Uso:  .venv/bin/python construir_entrega.py entrega.json SALIDA_DIR
Códigos de salida: 0 = ZIP construido y comprobado; 2 = faltan archivos o datos (se listan y no se
construye nada); 3 = una comprobación falló (traza no reproducible, cifra clave distinta, Excel con «NO»).

Pasos:
  1. Condiciones previas por problema (incisos/<id>/): traza.json, Demostración.xlsx, codigo/resolver.py,
     codigo/script.R, salida_R.txt, bloque.json y verificacion.md con la línea «Estado: aprobado».
     Color y hora obligatorios (B1).
  2. Reproducción: copia el inciso a una carpeta temporal, borra traza.json, corre codigo/resolver.py y
     exige una traza idéntica (como EG/herramientas/reproducir_entrega.py).
  3. Excel: la hoja Control (valores ya recalculados) no tiene «NO».
  4. Procedimientos.docx (docx_tsci3.py) → Procedimientos.pdf con LibreOffice.
  5. Cifras clave: cada {"texto", "traza"} de bloque.json["numeros_clave"] coincide con la traza
     (redondeada a los decimales del texto) y aparece en el texto del PDF.
  6. Parte_teórica.pdf y «Por si acaso/Teoría_pero_en_word.docx» si entrega.json trae "teoria".
  7. Árbol y ZIP: <nombre>/Parte_práctica/P<n>_<Método>/{Demostración.xlsx, Procedimientos.pdf,
     codigo/resolver.py, codigo/script.R, salida_R.txt, datos/…, traza.json}.
"""
import ast
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import cajas  # noqa: E402
import docx_tsci3  # noqa: E402
import teoria as teo  # noqa: E402

REQUERIDOS_BASE = ["traza.json", "Demostración.xlsx", "codigo/resolver.py", "bloque.json", "verificacion.md"]
FIJOS = {"materia": "Tópicos Selectos de Ciencias de la Ingeniería III", "docente": "Dr. Raymundo Said Zamora Pequeño",
         "alumno": "Alexis Alberto Reyna Sánchez", "matricula": "1851265"}


def nombre_entrega(e):
    """OD/AD26 TSCI3 CO PC.pdf p.4: «Nombre: Matrícula + Color,Hora,#Tarea». Separador «_» (lectura declarada)."""
    fmt = e.get("formato_nombre", "{matricula}_{color}_{hora}_{tarea}")
    return fmt.format(matricula=e["alumno"].get("matricula", FIJOS["matricula"]), color=e["color"], hora=e["hora"], tarea=e["tarea"])


def soffice_pdf(docx, outdir):
    perfil = tempfile.mkdtemp(prefix="lo_entrega_")
    for exe in ("soffice", "/Applications/LibreOffice.app/Contents/MacOS/soffice"):
        if shutil.which(exe) or os.path.exists(exe):
            subprocess.run([exe, "-env:UserInstallation=file://" + perfil, "--headless", "--convert-to", "pdf", "--outdir", outdir, docx],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            shutil.rmtree(perfil, ignore_errors=True)
            return os.path.join(outdir, os.path.splitext(os.path.basename(docx))[0] + ".pdf")
    raise SystemExit("Falta LibreOffice (soffice)")


def fragmentos(inciso, codigo):
    """[(etiqueta, líneas)] de bloque.json["codigo"]: python = [{"archivo", "funciones"}], r = [{"archivo", "lineas": [a, b]}]."""
    out = []
    for f in codigo.get("python", []):
        f = {"archivo": f} if isinstance(f, str) else f
        src = open(os.path.join(inciso, f["archivo"]), encoding="utf-8").read()
        lineas = src.split("\n")
        if f.get("funciones"):
            arbol = ast.parse(src)
            for nodo in arbol.body:
                if isinstance(nodo, ast.FunctionDef) and nodo.name in f["funciones"]:
                    out.append(("Código Python", lineas[nodo.lineno - 1:nodo.end_lineno]))
            faltan = set(f["funciones"]) - {n.name for n in arbol.body if isinstance(n, ast.FunctionDef)}
            if faltan:
                raise SystemExit("bloque.json: funciones que no están en %s: %s" % (f["archivo"], sorted(faltan)))
        else:
            a, b = f.get("lineas", [1, len(lineas)])
            out.append(("Código Python", lineas[a - 1:b]))
    for f in codigo.get("r", []):
        f = {"archivo": f} if isinstance(f, str) else f
        lineas = open(os.path.join(inciso, f["archivo"]), encoding="utf-8").read().split("\n")
        a, b = f.get("lineas", [1, len(lineas)])
        out.append(("Código R", lineas[a - 1:b]))
    return out


def valor_traza(tr, ruta):
    v = tr
    for k in ruta.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def cifra_ok(texto, v):
    t = texto.replace("−", "-").replace(" ", "").replace(" ", "")
    if isinstance(v, str):
        return t == v.replace(" ", "")
    dec = len(t.split(".")[1]) if "." in t else 0
    try:
        return abs(float(t) - round(float(v), dec)) < 10 ** (-dec) / 2 + 1e-12
    except ValueError:
        return False


def control_excel(xlsx):
    from openpyxl import load_workbook
    wb = load_workbook(xlsx, data_only=True)
    if "Control" not in wb.sheetnames:
        return ["sin hoja Control"]
    malos = []
    for fila in wb["Control"].iter_rows(values_only=True):
        for v in fila:
            if v == "NO":
                malos.append(str(fila[0]))
            if isinstance(v, str) and v.startswith("#"):
                malos.append("%s: %s" % (fila[0], v))
    return malos


def reproducir(inciso, argumentos=()):
    tmp = tempfile.mkdtemp(prefix="repro_")
    copia = os.path.join(tmp, "inciso")
    shutil.copytree(inciso, copia)
    os.remove(os.path.join(copia, "traza.json"))
    r = subprocess.run(["python3", os.path.join(copia, "codigo", "resolver.py")] + list(argumentos), cwd=copia,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    nueva = os.path.join(copia, "traza.json")
    if (r.returncode != 0 or not os.path.exists(nueva)) and not argumentos:
        r = subprocess.run(["python3", os.path.join(copia, "codigo", "resolver.py"), "."], cwd=copia,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    ok = r.returncode == 0 and os.path.exists(nueva) and json.load(open(nueva, encoding="utf-8")) == json.load(open(os.path.join(inciso, "traza.json"), encoding="utf-8"))
    shutil.rmtree(tmp, ignore_errors=True)
    return ok, (r.stderr or "")[-400:]


def main():
    e = json.load(open(sys.argv[1], encoding="utf-8"))
    salida = os.path.abspath(sys.argv[2])
    e.setdefault("alumno", {})
    faltan = []
    for k in ("color", "hora", "tarea"):
        if not e.get(k):
            faltan.append("entrega.json: «%s» (B1: OD/AD26 TSCI3 CO PC.pdf p.4)" % k)
    for p in e["problemas"]:
        b_path = os.path.join(p["inciso"], "bloque.json")
        b_meta = json.load(open(b_path, encoding="utf-8")) if os.path.exists(b_path) else {}
        lleva_r = not b_meta.get("sin_r", False)
        reqs = list(REQUERIDOS_BASE) + (["codigo/script.R", "salida_R.txt"] if lleva_r else [])
        for f in reqs:
            if not os.path.exists(os.path.join(p["inciso"], f)):
                faltan.append("%s: falta %s" % (p["inciso"], f))
        v = os.path.join(p["inciso"], "verificacion.md")
        if os.path.exists(v) and not re.search(r"^Estado: aprobado\s*$", open(v, encoding="utf-8").read(), re.M):
            faltan.append("%s: verificacion.md no dice «Estado: aprobado»" % p["inciso"])
    if faltan:
        print("No se construye la entrega. Falta:")
        for f in faltan:
            print("  - " + f)
        sys.exit(2)

    nombre = nombre_entrega(e)
    raiz = os.path.join(salida, nombre)
    if os.path.exists(raiz):
        shutil.rmtree(raiz)
    trabajo = os.path.join(salida, "_trabajo")
    os.makedirs(trabajo, exist_ok=True)
    errores, informe = [], []
    alumno = e["alumno"].get("nombre", FIJOS["alumno"])
    for p in e["problemas"]:
        I = p["inciso"]
        b = json.load(open(os.path.join(I, "bloque.json"), encoding="utf-8"))
        tr = json.load(open(os.path.join(I, "traza.json"), encoding="utf-8"))
        carpeta = os.path.join(raiz, "Parte_práctica", "P%d_%s" % (p["n"], b["metodo"]))
        ok, err = reproducir(I, p.get("argumentos", []))
        (informe if ok else errores).append("P%d: resolver.py %s la traza%s" % (p["n"], "reproduce" if ok else "NO reproduce", "" if ok else " (" + err + ")"))
        malos = control_excel(os.path.join(I, "Demostración.xlsx"))
        (errores if malos else informe).append("P%d: hoja Control de Demostración.xlsx %s" % (p["n"], ("con problemas: %s" % malos[:5]) if malos else "sin «NO» ni errores"))
        png = cajas.dibujar(b["cajas"], os.path.join(trabajo, "cajas_P%d.png" % p["n"]))
        dx = docx_tsci3.construir(b, {"materia": e.get("materia", FIJOS["materia"]), "alumno": alumno,
                                      "docente": e.get("docente", FIJOS["docente"]), "n": p["n"]},
                                  png, fragmentos(I, b.get("codigo", {})), os.path.join(trabajo, "Procedimientos_P%d.docx" % p["n"]),
                                  base_dir=I)
        pdf = soffice_pdf(dx, trabajo)
        import fitz
        texto = " ".join(pg.get_text() for pg in fitz.open(pdf)).replace("−", "-")
        texto_n = re.sub(r"\s+", " ", texto)
        for nc in b.get("numeros_clave", []):
            v = valor_traza(tr, nc["traza"])
            en_pdf = nc["texto"] in texto_n
            bien = cifra_ok(nc["texto"], v) and en_pdf
            (informe if bien else errores).append("P%d: cifra «%s» ↔ traza %s = %r: %s" % (
                p["n"], nc["texto"], nc["traza"], v, "coincide y está en el PDF" if bien else ("no está en el PDF" if not en_pdf else "NO coincide")))
        os.makedirs(os.path.join(carpeta, "codigo"), exist_ok=True)
        shutil.copy(pdf, os.path.join(carpeta, "Procedimientos.pdf"))
        for f in ("Demostración.xlsx", "traza.json", "salida_R.txt", "codigo/resolver.py", "codigo/script.R"):
            if os.path.exists(os.path.join(I, f)):
                shutil.copy(os.path.join(I, f), os.path.join(carpeta, f))
        shutil.copytree(os.path.join(I, "datos"), os.path.join(carpeta, "datos"))
        for extra in b.get("anexos", []):
            shutil.copy(os.path.join(I, extra), os.path.join(carpeta, os.path.basename(extra)))
        informe.append("P%d: %s, %d páginas" % (p["n"], os.path.relpath(carpeta, salida), len(fitz.open(pdf))))
    if e.get("teoria"):
        os.makedirs(os.path.join(raiz, "Por si acaso"), exist_ok=True)
        dx = teo.construir(e["teoria"], alumno, e["alumno"].get("matricula", FIJOS["matricula"]), e.get("fecha", ""),
                           os.path.join(raiz, "Por si acaso", "Teoría_pero_en_word.docx"))
        shutil.copy(soffice_pdf(dx, trabajo), os.path.join(raiz, "Parte_teórica.pdf"))
    if errores:
        print("Comprobaciones fallidas (no se comprime):")
        for x in errores:
            print("  ❌ " + x)
        sys.exit(3)
    zp = os.path.join(salida, nombre + ".zip")
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for d, _, fs in os.walk(raiz):
            for f in sorted(fs):
                ruta = os.path.join(d, f)
                z.write(ruta, os.path.relpath(ruta, salida))
    for x in informe:
        print("  ✅ " + x)
    print("ZIP: %s" % zp)


if __name__ == "__main__":
    main()
