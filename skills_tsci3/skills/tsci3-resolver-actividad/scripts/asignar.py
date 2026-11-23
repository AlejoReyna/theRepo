#!/usr/bin/env python3
"""Asignación por matrícula (reglas-academicas.md R3) con la regla del medio curso AD26 (EX-MC, problema 1).

Uso: python3 asignar.py MATRICULA [--json]
Regla literal de EX-MC: «Utilizando REGEVEN y el registro correspondiente al último dígito de su
matrícula […] Si su matrícula termina en 0, 1 o 2 también elabore el diagrama YAWL, si termina en
3, 4 o 5, BPMN, y si termina en 6, 7, 8 o 9 el EDPC. Además, si su matrícula es impar elabore el
árbol de proceso, si es par, la red causal.» Las hojas de DL/REGEVEN.xlsx se llaman «Registro 01» …
«Registro 09» y «Registro 00».
Si un enunciado nuevo trae otra regla, se usa la del enunciado y este script no aplica.
"""
import json
import sys


def asignar(matricula):
    m = str(matricula).strip()
    if not m.isdigit():
        raise SystemExit("La matrícula debe ser numérica: %r" % matricula)
    d = int(m[-1])
    diagrama = "YAWL" if d <= 2 else "BPMN" if d <= 5 else "EDPC"
    modelo = "árbol de proceso" if d % 2 else "red causal"
    filas = [
        ["Regla del enunciado", "Condición", "Aplicación"],
        ["Registro = último dígito de la matrícula", "%s termina en %d" % (m, d), "Registro 0%d" % d],
        ["0, 1 o 2 → YAWL; 3, 4 o 5 → BPMN; 6, 7, 8 o 9 → EDPC", "último dígito %d" % d, diagrama],
        ["Impar → árbol de proceso; par → red causal", "%d es %s" % (d, "impar" if d % 2 else "par"), modelo],
    ]
    estado_p = [x for x in (diagrama, modelo) if x in ("YAWL", "EDPC", "red causal")]
    return {"matricula": m, "registro": "Registro 0%d" % d, "diagrama": diagrama, "modelo": modelo,
            "tabla": filas, "estado_P": estado_p}


def main():
    a = asignar(sys.argv[1])
    if "--json" in sys.argv:
        print(json.dumps(a, ensure_ascii=False, indent=1))
        return
    for f in a["tabla"]:
        print(" | ".join(f))
    if a["estado_P"]:
        print("AVISO: %s sin ejemplo ni método en las fuentes (estado P de tsci3-modelado-procesos): avisa al usuario." % ", ".join(a["estado_P"]))


if __name__ == "__main__":
    main()
