#!/usr/bin/env python3
"""Prueba de tsci3-entrega-final (plan §6 paso 23) con los bloques de S2 (DOLLY) y S4 (AP).

1. Caso completo: código 0; árbol como EF/1851265_TSOER2.zip salvo nombres; carta horizontal 792 × 612
   y teoría vertical 612 × 792; encabezado de la plantilla en la p.1; la traza se reproduce.
2. Sin color → código 2 (B1).  3. Inciso sin bloque.json ni resolver.py (RM-br) → código 2 y la lista.
4. Mutante: cifra clave alterada en bloque.json → código 3.  5. Mutante: traza.json alterada → código 3.
Uso: python3 test_entrega.py  (usa TSCI3/.venv/bin/python para construir)
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

T = "/Users/alexis/theCode/newSkills/TSCI3"
SK = os.path.join(T, "skills_tsci3", "skills", "tsci3-entrega-final")
PY = os.path.join(T, ".venv", "bin", "python")
BASE = json.load(open(os.path.join(SK, "pruebas", "entrega_prueba.json"), encoding="utf-8"))
fallas = 0


def ok(c, msg):
    global fallas
    fallas += not c
    print(("✅ " if c else "❌ ") + msg)


def correr(e, d):
    ruta = os.path.join(d, "entrega.json")
    json.dump(e, open(ruta, "w", encoding="utf-8"), ensure_ascii=False)
    r = subprocess.run([PY, os.path.join(SK, "scripts", "construir_entrega.py"), ruta, d], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return r.returncode, r.stdout


tmp = tempfile.mkdtemp(prefix="test_entrega_")
d1 = os.path.join(tmp, "completo")
os.makedirs(d1)
c, out = correr(BASE, d1)
ok(c == 0, "caso completo: código %d" % c)
raiz = os.path.join(d1, "1851265_Amarillo_N4_AF3")
esperado = ["Parte_teórica.pdf", "Por si acaso/Teoría_pero_en_word.docx"]
for p in ("P1_Kmeans", "P2_Apriori"):
    esperado += ["Parte_práctica/%s/%s" % (p, f) for f in ("Demostración.xlsx", "Procedimientos.pdf", "codigo/resolver.py", "codigo/script.R", "traza.json", "salida_R.txt")]
ok(all(os.path.exists(os.path.join(raiz, f)) for f in esperado) and os.path.exists(raiz + ".zip"),
   "árbol: Parte_práctica/P<n>_<Método>/{Demostración.xlsx, Procedimientos.pdf, codigo/, datos/, traza.json}, Parte_teórica.pdf, Por si acaso/ y el ZIP 1851265_Amarillo_N4_AF3.zip")
import fitz  # noqa: E402
pdf = fitz.open(os.path.join(raiz, "Parte_práctica", "P1_Kmeans", "Procedimientos.pdf"))
p1 = pdf[0].get_text()
ok(all(abs(pg.rect.width - 792) < 1 and abs(pg.rect.height - 612) < 1 for pg in pdf), "Procedimientos.pdf: %d páginas carta horizontal 792 × 612" % len(pdf))
ok(all(s in p1 for s in ("Universidad Autónoma de Nuevo León", "Facultad de Ingeniería Mecánica y Eléctrica",
                         "Tópicos Selectos de Ciencias de la Ingeniería III  |  Problema 1", "Alexis Alberto Reyna Sánchez",
                         "Docente: Dr. Raymundo Said Zamora Pequeño", "Procedimiento de resolución", "Fuentes del curso")),
   "p.1 con el encabezado, «Procedimiento de resolución» y «Fuentes del curso» de la plantilla")
ok(len(pdf[0].get_images()) >= 3, "p.1 con los dos logotipos y la imagen de las cajas (%d imágenes)" % len(pdf[0].get_images()))
teo = fitz.open(os.path.join(raiz, "Parte_teórica.pdf"))
ok(abs(teo[0].rect.width - 612) < 1 and "Matrícula: 1851265" in teo[0].get_text(), "Parte_teórica.pdf vertical 612 × 792 con el bloque de nombre y matrícula")
ok("reproduce la traza" in out and "NO reproduce" not in out, "resolver.py reproduce las dos trazas en una copia temporal")

d2 = os.path.join(tmp, "sincolor")
os.makedirs(d2)
e = json.loads(json.dumps(BASE))
e["color"] = ""
c, out = correr(e, d2)
ok(c == 2 and "color" in out, "sin color: código 2 y no construye (B1)")

d3 = os.path.join(tmp, "incompleto")
copia_inc = os.path.join(d3, "RM-br")
shutil.copytree(os.path.join(T, "incisos", "RM-br"), copia_inc)
for quitar in ("bloque.json", "verificacion.md", "codigo/resolver.py"):
    qp = os.path.join(copia_inc, quitar)
    if os.path.exists(qp):
        os.remove(qp)
e = json.loads(json.dumps(BASE))
e["problemas"].append({"n": 3, "inciso": copia_inc})
c, out = correr(e, d3)
ok(c == 2 and "RM-br: falta bloque.json" in out and "RM-br: falta codigo/resolver.py" in out, "inciso incompleto (RM-br): código 2 con la lista de faltantes")

for nombre, cambio in (("cifra", "bloque"), ("traza", "traza")):
    d = os.path.join(tmp, nombre)
    copia = os.path.join(d, "KM-dolly")
    shutil.copytree(os.path.join(T, "incisos", "KM-dolly"), copia)
    if cambio == "bloque":
        b = json.load(open(os.path.join(copia, "bloque.json"), encoding="utf-8"))
        b["numeros_clave"][1]["texto"] = "30"
        json.dump(b, open(os.path.join(copia, "bloque.json"), "w", encoding="utf-8"), ensure_ascii=False)
    else:
        t = json.load(open(os.path.join(copia, "traza.json"), encoding="utf-8"))
        t["resumen"]["n0"] = 30
        json.dump(t, open(os.path.join(copia, "traza.json"), "w", encoding="utf-8"), ensure_ascii=False)
    e = json.loads(json.dumps(BASE))
    e["problemas"] = [{"n": 1, "inciso": copia}]
    e.pop("teoria")
    c, out = correr(e, d)
    ok(c == 3, "mutante (%s alterada): código 3, no se comprime" % ("cifra clave" if cambio == "bloque" else "traza"))
shutil.rmtree(tmp, ignore_errors=True)
print("%s %d fallas" % ("✅" if not fallas else "❌", fallas))
sys.exit(1 if fallas else 0)
