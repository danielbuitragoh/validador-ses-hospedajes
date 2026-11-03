"""Utilidades comunes. Todos los datos de prueba son FICTICIOS."""

import re
from pathlib import Path

from validador_ses_hospedajes import Gravedad, Informe, validar

EJEMPLOS = Path(__file__).parent / "ejemplos"


def leer(nombre: str) -> str:
    return (EJEMPLOS / nombre).read_text(encoding="utf-8")


def parte() -> str:
    return leer("validos/parte-viajeros.xml")


def reserva() -> str:
    return leer("validos/reserva-hospedaje.xml")


def informe(xml: str, **kwargs: object) -> Informe:
    return validar(xml, **kwargs)  # type: ignore[arg-type]


def errores(xml: str, **kwargs: object) -> set[str]:
    return {i.codigo for i in informe(xml, **kwargs).incidencias if i.gravedad is Gravedad.ERROR}


def avisos(xml: str, **kwargs: object) -> set[str]:
    return {i.codigo for i in informe(xml, **kwargs).incidencias if i.gravedad is Gravedad.AVISO}


def sustituir(xml: str, patron: str, por: str, veces: int = 1) -> str:
    """Sustituye con expresión regular y falla si el patrón no aparece (para que ninguna prueba pase en vano)."""
    nuevo, n = re.subn(patron, por, xml, count=veces if veces > 0 else 0, flags=re.DOTALL)
    assert n > 0, f"el patrón {patron!r} no aparece"
    return nuevo


def quitar(xml: str, etiqueta: str, veces: int = 1) -> str:
    """Elimina el elemento ``etiqueta`` (sin hijos del mismo nombre) y su línea."""
    return sustituir(xml, rf"\n\s*<{etiqueta}>.*?</{etiqueta}>", "", veces)
