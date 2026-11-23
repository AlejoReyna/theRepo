"""Escritura determinista de trazas JSON (mismo contenido → mismos bytes)."""
import json
from fractions import Fraction


def _plano(x):
    if isinstance(x, Fraction):
        return {"fraccion": f"{x.numerator}/{x.denominator}", "valor": round(float(x), 12)}
    if isinstance(x, float):
        return round(x, 12)
    if isinstance(x, dict):
        return {str(k): _plano(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_plano(v) for v in x]
    return x


def a_texto(traza):
    return json.dumps(_plano(traza), ensure_ascii=False, indent=2, sort_keys=False) + "\n"


def escribir(traza, ruta):
    with open(ruta, "w", encoding="utf-8") as fh:
        fh.write(a_texto(traza))


def leer(ruta):
    with open(ruta, encoding="utf-8") as fh:
        return json.load(fh)
