#!/usr/bin/env python3
"""Batería completa de validación del sistema TSCI3 (Paso 24 de PLAN_TSCI3.md §6).

Ejecuta y verifica:
  1. Integridad de fuentes (manifiesto.py --comprobar) y citas (comprobar_citas.py);
  2. Pruebas unitarias del kit (test_base.py, test_kmeans.py, test_apriori.py), de la coordinadora
     (test_coordinadora.py) y de la entrega final (test_entrega.py);
  3. Los 10 casos con oráculo en kit.py (MC-P3, MC-P1, KM-dolly, KM-mochila, KMED-dolly, AP-clase,
     AP-poko, SEQ-clase, EPI-sacramento, MC-old) y los 4 casos de tsci3-subset-r;
  4. Los 11 casos de AF4 con sus verificadores independientes (BP-casos, RM-br, SW-boston, SW-br,
     REG-br, LOG-br, CM-knn-br, CM-ad25-11, CM-ad25-03, KNN-br, RF-br);
  5. Revisión de hojas Control de todos los Demostración.xlsx en incisos/ (0 «NO» y 0 errores de fórmula).

Uso: /Users/alexis/theCode/newSkills/TSCI3/.venv/bin/python skills_tsci3/validacion/validar_todo.py
"""
import glob
import os
import subprocess
import sys

from openpyxl import load_workbook

T = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PY = os.path.join(T, ".venv", "bin", "python")
SK = os.path.join(T, "skills_tsci3", "skills")
KIT = os.path.join(T, "kit_tsci3", "kit.py")
INC = os.path.join(T, "incisos")


def correr(titulo, cmd, cwd=T):
    r = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    ok = r.returncode == 0
    print(("%s %s" % ("✅" if ok else "❌", titulo)))
    if not ok:
        print("   Comando:", " ".join(cmd))
        for ln in r.stdout.strip().splitlines()[-15:]:
            print("   ", ln)
    return ok


def revisar_excel(xlsx):
    wb = load_workbook(xlsx, data_only=True)
    if "Control" not in wb.sheetnames:
        return False, "sin hoja Control"
    malos = []
    n_si = 0
    for fila in wb["Control"].iter_rows(values_only=True):
        for v in fila:
            if v == "sí":
                n_si += 1
            elif v == "NO":
                malos.append(str(fila[0]))
            elif isinstance(v, str) and v.startswith("#"):
                malos.append("%s:%s" % (fila[0], v))
    return (not malos and n_si > 0), ("%d/0 sí/NO" % n_si if not malos else "fallos: %s" % malos[:5])


def main():
    resultados = []
    print("=== 1. Integridad de fuentes y citas ===")
    resultados.append(correr("manifiesto.py --comprobar (132 fuentes con SHA-256)", ["python3", os.path.join(T, "herramientas", "manifiesto.py"), "--comprobar"]))
    docs = [os.path.join(os.path.dirname(T), "PLAN_TSCI3.md"), os.path.join(T, "README.md"), os.path.join(T, "AGENTS.md"),
            os.path.join(T, "skills_tsci3", "MATRIZ_SKILLS.md")]
    docs += sorted(glob.glob(os.path.join(SK, "*", "SKILL.md")))
    docs += sorted(glob.glob(os.path.join(SK, "tsci3-comun", "references", "*.md")))
    resultados.append(correr("comprobar_citas.py (%d documentos)" % len(docs), [PY, os.path.join(T, "herramientas", "comprobar_citas.py")] + docs))

    print("\n=== 2. Pruebas unitarias del kit, coordinadora y entrega ===")
    for t in ("test_base.py", "test_kmeans.py", "test_apriori.py"):
        resultados.append(correr("kit_tsci3/pruebas/" + t, ["python3", os.path.join(T, "kit_tsci3", "pruebas", t)]))
    resultados.append(correr("tsci3-resolver-actividad/pruebas/test_coordinadora.py (46 casos)", ["python3", os.path.join(SK, "tsci3-resolver-actividad", "pruebas", "test_coordinadora.py")]))
    resultados.append(correr("tsci3-entrega-final/pruebas/test_entrega.py (11 casos)", [PY, os.path.join(SK, "tsci3-entrega-final", "pruebas", "test_entrega.py")]))

    print("\n=== 3. Oráculos de kit.py y bitácoras de tsci3-subset-r ===")
    oraculos = [
        ("arbol-oraculo", "MC-P3", "datos/gastank.csv"),
        ("procesos-oraculo", "MC-P1", "datos/REGEVEN.xlsx"),
        ("kmeans-oraculo", "KM-dolly", "datos/dolly_sheet1.csv"),
        ("kmeans-oraculo", "KM-mochila", "datos/mochila_.csv"),
        ("kmedoides-oraculo", "KMED-dolly", "datos/dolly_sheet1.csv"),
        ("apriori-oraculo", "AP-clase", "datos/ap_clase.csv"),
        ("apriori-oraculo", "AP-poko", "datos/apri_poko.csv"),
        ("secuencias-oraculo", "SEQ-clase", "datos/SEQMIN.csv"),
        ("episodios-oraculo", "EPI-sacramento", "datos/SacramentocrimeJanuary2006mo.csv"),
        ("minimos-oraculo", "MC-old", "datos/old.csv"),
    ]
    for cmd, inc, dat in oraculos:
        p_inc = os.path.join(INC, inc)
        resultados.append(correr(f"kit.py {cmd} ({inc})", ["python3", KIT, cmd, os.path.join(p_inc, dat), os.path.join(p_inc, "traza.json")]))

    comp_bit = os.path.join(SK, "tsci3-subset-r", "scripts", "comparar_bitacoras.py")
    for inc in ("MC-P2", "SUBSET-mta", "SUBSET-border", "SUBSET-ambx"):
        resultados.append(correr(f"tsci3-subset-r comparar_bitacoras ({inc})", ["python3", comp_bit, os.path.join(INC, inc)]))

    comp_tr = os.path.join(SK, "tsci3-comun", "scripts", "comparar_traza_r.py")
    resultados.append(correr("tsci3-predictor-binario comparar_traza_r (BIN-mtcars)", ["python3", comp_tr, os.path.join(INC, "BIN-mtcars"), "binario_R.csv"]))

    print("\n=== 4. Verificadores independientes de AF4 ===")
    verificadores = [
        ("tsci3-breusch-pagan", "verificar_bp.py", "BP-casos"),
        ("tsci3-regresion-multiple", "verificar_multiple.py", "RM-br"),
        ("tsci3-stepwise-aic", "verificar_stepwise.py", "SW-boston"),
        ("tsci3-stepwise-aic", "verificar_stepwise.py", "SW-br"),
        ("tsci3-regularizacion", "verificar_regularizacion.py", "REG-br"),
        ("tsci3-regresion-logistica", "verificar_logistica.py", "LOG-br"),
        ("tsci3-matriz-confusion", "verificar_matriz.py", "CM-knn-br"),
        ("tsci3-matriz-confusion", "verificar_matriz.py", "CM-ad25-11"),
        ("tsci3-matriz-confusion", "verificar_matriz.py", "CM-ad25-03"),
        ("tsci3-knn", "verificar_knn.py", "KNN-br"),
        ("tsci3-bosque-aleatorio", "verificar_bosque.py", "RF-br"),
    ]
    for sk, scr, inc in verificadores:
        resultados.append(correr(f"{sk}/{scr} ({inc})", ["python3", os.path.join(SK, sk, "scripts", scr), os.path.join(INC, inc)]))

    print("\n=== 5. Hojas Control de Demostración.xlsx en incisos/ ===")
    for xlsx in sorted(glob.glob(os.path.join(INC, "*", "Demostración.xlsx"))):
        inc = os.path.basename(os.path.dirname(xlsx))
        ok, msg = revisar_excel(xlsx)
        print(("%s Demostración.xlsx (%s): %s" % ("✅" if ok else "❌", inc, msg)))
        resultados.append(ok)

    total = len(resultados)
    pasaron = sum(1 for x in resultados if x)
    print("\n============================================================")
    print(f"RESUMEN DE VALIDACIÓN TSCI3: {pasaron}/{total} comprobaciones en verde")
    print("============================================================")
    return 0 if pasaron == total else 1


if __name__ == "__main__":
    sys.exit(main())
