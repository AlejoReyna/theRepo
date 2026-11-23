#!/usr/bin/env python3
"""Prepara una sesión de actividad (AF1..AF4) o examen (MC, ORD, EXT) dentro de TSCI3 sin sobrescribir trabajo previo.

Análogo a Endgame/preparar_examen.py. Crea:
  actividades/<nombre>/
    ├── AGENTS.md
    ├── CLAUDE.md
    ├── PROMPT.md
    ├── verificacion.md
    ├── enunciado/
    ├── datos/
    ├── prompts/
    ├── incisos/
    └── entrega/

Uso:
  python3 preparar_actividad.py --actividad AF3 --nombre AF3
  python3 preparar_actividad.py /ruta/a/enunciado.pdf /ruta/a/datos.csv --nombre Ordinario
"""
import argparse
from datetime import datetime
from pathlib import Path
import re
import shutil
import sys
import tempfile

BASE = Path(__file__).resolve().parent
OD = BASE / "fuentes" / "OD"
DL = BASE / "fuentes" / "DL"

CATALOGO = {
    "AF1": {
        "titulo": "AF1: Tratamiento de Datos",
        "enunciado": [OD / "AD26 TSCI3 AF1.png", OD / "SUBSET.pdf", OD / "AD26 TSCI3 CO PC.pdf"],
        "datos": [
            OD / "MTA_Metro-North_Delay_Verification__Beginning_2012.csv",
            OD / "Border_Crossing_Entry_Data.csv",
            OD / "ambx.csv",
        ],
        "referencia": ["SUBSET-mta", "SUBSET-border", "SUBSET-ambx", "MC-P2"],
    },
    "AF2": {
        "titulo": "AF2: Modelado de Procesos",
        "enunciado": [OD / "AD26 TSCI3 AF2.png", OD / "AD26 TSCI3 CO PC.pdf"],
        "datos": [DL / "REGEVEN.xlsx"],
        "referencia": ["MC-P1"],
    },
    "AF3": {
        "titulo": "AF3: Técnicas de Minería de Datos",
        "enunciado": [OD / "AD26 TSCI3 AF3.png", OD / "AD26 TSCI3 CO PC.pdf"],
        "datos": [
            DL / "gastank.csv",
            OD / "STARAD26.xlsx",
            OD / "Eelgrass_Beds_2006_Set DTME.xlsx",
            OD / "mochila_.xlsx",
            OD / "DOLLY LIVES.xlsx",
            OD / "DFA.csv",
            OD / "dataclu.csv",
            OD / "TSCI3 P6.R",
            OD / "AP (1).xlsx",
            OD / "apri poko.csv",
            OD / "arules R (2).txt",
            OD / "SEQMIN.csv",
            OD / "SEQMIN.R",
            OD / "SacramentocrimeJanuary2006mo.csv",
            OD / "EPISODES.R",
        ],
        "referencia": ["MC-P3", "KM-dolly", "KM-mochila", "KMED-dolly", "AP-clase", "AP-poko", "SEQ-clase", "EPI-sacramento"],
    },
    "AF4": {
        "titulo": "AF4: Regresión y Evaluación de Clasificadores",
        "enunciado": [OD / "AD26 TSCI3 AF4.png", OD / "AM R.pdf", OD / "AD26 TSCI3 CO PC.pdf"],
        "datos": [OD / "old.csv", OD / "BR (2).csv"],
        "referencia": [
            "MC-old", "BP-casos", "BIN-mtcars", "SW-boston", "SW-br", "RM-br",
            "REG-br", "LOG-br", "KNN-br", "CM-knn-br", "CM-ad25-11", "CM-ad25-03", "RF-br",
        ],
    },
    "MC": {
        "titulo": "Examen de Medio Curso (Práctica)",
        "enunciado": [DL / "AD26 TSCI3 MC (Práctica).pdf", BASE / "fuentes" / "retroalimentacion_MC.md"],
        "datos": [DL / "REGEVEN.xlsx", DL / "export.csv", DL / "gastank.csv"],
        "referencia": ["MC-P1", "MC-P2", "MC-P3"],
    },
}


def vincular_o_copiar(origen: Path, destino: Path):
    """Copia archivos pequeños (< 5 MB) y enlaza archivos grandes para no duplicar cientos de MB."""
    if destino.exists() or destino.is_symlink():
        return
    if origen.stat().st_size > 5 * 1024 * 1024:
        destino.symlink_to(origen)
    else:
        shutil.copy2(origen, destino)


def preparar(archivos, actividad, nombre, sobreescribir=False):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", nombre):
        raise ValueError("Usa un nombre de 1 a 80 letras sin acentos, números, guiones o guiones bajos.")
    if not (BASE / "kit_tsci3" / "kit.py").is_file():
        raise ValueError("Falta el kit en TSCI3/kit_tsci3/kit.py.")
    extras = [Path(p).expanduser().resolve(strict=True) for p in archivos]
    if any(not p.is_file() for p in extras):
        raise ValueError("Cada entrada adicional debe ser un archivo existente.")
    cfg = CATALOGO.get(actividad, {"titulo": f"Sesión {nombre}", "enunciado": [], "datos": [], "referencia": []})
    enunciados = list(cfg["enunciado"]) + extras
    datos_base = list(cfg["datos"])
    if not enunciados and not datos_base:
        raise ValueError("Indica --actividad {AF1,AF2,AF3,AF4,MC} o pasa archivos de enunciado/datos.")

    sesiones = BASE / "actividades"
    sesiones.mkdir(exist_ok=True)
    destino = sesiones / nombre
    if destino.exists():
        if not sobreescribir:
            raise ValueError(f"Ya existe {destino}. Elige otro --nombre o usa --sobreescribir.")
        shutil.rmtree(destino)

    with tempfile.TemporaryDirectory(prefix=".preparando_", dir=sesiones) as temporal:
        trabajo = Path(temporal) / nombre
        trabajo.mkdir()
        for carpeta in ("enunciado", "datos", "prompts", "incisos", "entrega"):
            (trabajo / carpeta).mkdir()
        for f in enunciados:
            vincular_o_copiar(f, trabajo / "enunciado" / f.name)
        for f in datos_base:
            vincular_o_copiar(f, trabajo / "datos" / f.name)

        tarea_tag = actividad or nombre
        refs_txt = ", ".join(f"`{BASE / 'incisos' / r}`" for r in cfg["referencia"]) or "ver `TSCI3/incisos/`"
        instrucciones = f"""# Sesión TSCI3 — {cfg['titulo']}

Lee `{BASE / 'AGENTS.md'}` y usa las skills de `{BASE / 'skills_tsci3/skills'}`.
Variables de esta sesión:
- `T={BASE}`
- `SK={BASE / 'skills_tsci3/skills'}`
- `A={destino}`
- `PY={BASE / '.venv/bin/python'}`
- Alumno: Alexis Alberto Reyna Sánchez | Matrícula: `1851265` (impar, termina en 5) | Color: `Amarillo` | Hora: `N4` | Tarea: `{tarea_tag}`

Archivos de enunciado/rúbrica de esta sesión: `{destino / 'enunciado'}`
Datos preparados en: `{destino / 'datos'}`
Casos de referencia ya verificados en el repositorio: {refs_txt}

Guarda prompts en `prompts/`, cada inciso en `incisos/<id>/` y el ZIP final (`1851265_Amarillo_N4_{tarea_tag}.zip`) en `entrega/`.
No modifiques `{BASE / 'fuentes'}` ni `{BASE / 'plantilla_entrega'}`.
"""
        (trabajo / "AGENTS.md").write_text(instrucciones, encoding="utf-8")
        (trabajo / "CLAUDE.md").write_text(instrucciones, encoding="utf-8")

        lista_enun = "\n".join(f"- `{destino / 'enunciado' / p.name}`" for p in enunciados) or "- (añadir en `enunciado/`)"
        lista_datos = "\n".join(f"- `{destino / 'datos' / p.name}`" for p in datos_base) or "- (añadir en `datos/`)"
        prompt = f"""# Resolver {cfg['titulo']} (TSCI3)

Trabaja en esta sesión siguiendo `{BASE / 'AGENTS.md'}` y la skill coordinadora `{BASE / 'skills_tsci3/skills/tsci3-resolver-actividad/SKILL.md'}`.

## 1. Enunciado / Rúbrica
{lista_enun}

## 2. Datos disponibles en la sesión
{lista_datos}

## 3. Casos de clase de referencia ya verificados
{refs_txt}

## 4. Pasos a seguir
1. Revisa los archivos de `enunciado/` y `datos/`. Si el usuario aporta instrucciones o datos individuales adicionales para la actividad, incorpóralos en `enunciado/` y `datos/`.
2. Aplica primero la asignación por matrícula (`1851265`) con `python3 {BASE / 'skills_tsci3/skills/tsci3-resolver-actividad/scripts/asignar.py'} 1851265` si el enunciado la pide (`R3`).
3. Mapea cada elemento o problema a su skill con `python3 {BASE / 'skills_tsci3/skills/tsci3-resolver-actividad/scripts/seleccionar.py'} "<texto>"` y escribe un prompt por inciso en `{destino / 'prompts'}` más `indice.md`.
4. Resuelve o adapta cada inciso en `{destino / 'incisos'}/<id>/` (puedes delegar en paralelo a subagentes). Cada inciso debe cumplir las 4 comparaciones del contrato (`verificacion.md`), tener `Demostración.xlsx` con 0 «NO» en `Control`, `codigo/resolver.py`, `traza.json`, `bloque.json` y `verificacion.md` con `Estado: aprobado`.
5. Une los bloques en `{destino / 'entrega.json'}` y construye el ZIP final con:
   `{BASE / '.venv/bin/python'} {BASE / 'skills_tsci3/skills/tsci3-entrega-final/scripts/construir_entrega.py'} {destino / 'entrega.json'} {destino / 'entrega'}`
"""
        (trabajo / "PROMPT.md").write_text(prompt, encoding="utf-8")
        (trabajo / "verificacion.md").write_text(
            f"# Verificación de {cfg['titulo']}\n\nPendiente: ejecutar incisos, validar hojas Control y construir ZIP en `entrega/`.\n",
            encoding="utf-8",
        )
        trabajo.rename(destino)
    return destino


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("archivos", nargs="*", help="Archivos adicionales de enunciado o datos")
    ap.add_argument("--actividad", choices=sorted(CATALOGO.keys()), help="Pre-cargar rúbrica y datos del curso para AF1..AF4 o MC")
    ap.add_argument("--nombre", help="Nombre de la carpeta en actividades/ (por omisión el de --actividad o timestamp)")
    ap.add_argument("--sobreescribir", action="store_true", help="Recrear la carpeta si ya existe")
    args = ap.parse_args()
    nombre = args.nombre or args.actividad or ("actividad_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    try:
        destino = preparar(args.archivos, args.actividad, nombre, args.sobreescribir)
    except (OSError, ValueError) as err:
        ap.exit(1, f"Error: {err}\n")
    print(f"Sesión preparada: {destino}")
    print(f"Para comenzar, usa el prompt: {destino / 'PROMPT.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
