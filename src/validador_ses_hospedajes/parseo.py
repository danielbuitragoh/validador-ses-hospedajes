"""Parseo XML seguro y con números de línea.

Seguridad (el fichero puede venir de cualquier programa, o de cualquiera):
- Se usa ``defusedxml`` con DTD, entidades y referencias externas **prohibidas**: no hay XXE, ni «billion laughs»,
  ni descargas. El documento oficial no usa DTD, así que cualquier ``<!DOCTYPE`` se rechaza.
- Límites de tamaño, de profundidad y de número de elementos, comprobados antes y durante el parseo.
- Nada de red: el parser nunca resuelve recursos externos.
"""

import re
from dataclasses import dataclass, field
from typing import Final
from xml.etree.ElementTree import ParseError

from defusedxml import DefusedXmlException
from defusedxml.ElementTree import DefusedXMLParser

BOM_UTF8: Final = b"\xef\xbb\xbf"
_RE_DECLARACION: Final = re.compile(rb"^\s*<\?xml[^>]*?encoding\s*=\s*[\"']([A-Za-z0-9._-]+)[\"']")


@dataclass(frozen=True, slots=True)
class Limites:
    """Límites defensivos (no proceden del documento oficial, que no fija ninguno)."""

    max_bytes: int = 10 * 1024 * 1024
    max_profundidad: int = 32
    max_elementos: int = 500_000


@dataclass(slots=True)
class Nodo:
    """Elemento XML ya parseado. ``nombre`` es el nombre local (sin espacio de nombres)."""

    nombre: str
    espacio: str | None
    atributos: dict[str, str]
    linea: int
    texto: str = ""
    hijos: list["Nodo"] = field(default_factory=list)


class ErrorParseo(Exception):
    """El fichero no se ha podido leer como XML seguro. ``codigo`` es una regla del catálogo."""

    def __init__(self, codigo: str, linea: int | None = None, detalle: str = "") -> None:
        super().__init__(f"{codigo}: {detalle}" if detalle else codigo)
        self.codigo = codigo
        self.linea = linea
        self.detalle = detalle


def _separar(etiqueta: str) -> tuple[str | None, str]:
    if etiqueta.startswith("{"):
        espacio, _, local = etiqueta[1:].partition("}")
        return espacio, local
    return None, etiqueta


class _Constructor:
    """«Target» del parser: construye ``Nodo`` y anota la línea de cada elemento."""

    def __init__(self, limites: Limites) -> None:
        self.limites = limites
        self.parser: DefusedXMLParser | None = None
        self.pila: list[Nodo] = []
        self.raiz: Nodo | None = None
        self.elementos = 0

    def _linea(self) -> int:
        if self.parser is None:  # pragma: no cover - se asigna antes de alimentar el parser
            raise RuntimeError("parser no inicializado")
        return int(self.parser.parser.CurrentLineNumber)

    def start(self, etiqueta: str, atributos: dict[str, str]) -> None:
        self.elementos += 1
        if self.elementos > self.limites.max_elementos:
            raise ErrorParseo("xml.demasiados-elementos", self._linea(), f"más de {self.limites.max_elementos}")
        if len(self.pila) >= self.limites.max_profundidad:
            raise ErrorParseo("xml.demasiado-profundo", self._linea(), f"más de {self.limites.max_profundidad}")
        espacio, nombre = _separar(etiqueta)
        attrs = {_separar(k)[1]: v for k, v in atributos.items()}
        nodo = Nodo(nombre=nombre, espacio=espacio, atributos=attrs, linea=self._linea())
        if self.pila:
            self.pila[-1].hijos.append(nodo)
        else:
            self.raiz = nodo
        self.pila.append(nodo)

    def end(self, etiqueta: str) -> None:
        self.pila.pop()

    def data(self, texto: str) -> None:
        if self.pila:
            self.pila[-1].texto += texto

    def close(self) -> Nodo | None:
        return self.raiz


def codificacion_declarada(datos: bytes) -> str | None:
    """Codificación que declara ``<?xml … encoding="…"?>``, o ``None`` si no declara ninguna."""
    m = _RE_DECLARACION.match(datos.removeprefix(BOM_UTF8)[:300])
    return m.group(1).decode("ascii") if m else None


def parsear(datos: bytes, limites: Limites | None = None) -> Nodo:
    """Parsea ``datos`` de forma segura. Lanza :class:`ErrorParseo` si no se puede."""
    limites = limites or Limites()
    if len(datos) > limites.max_bytes:
        raise ErrorParseo("fichero.demasiado-grande", None, f"{len(datos)} bytes > {limites.max_bytes}")
    if not datos.removeprefix(BOM_UTF8).strip():
        raise ErrorParseo("fichero.vacio")

    constructor = _Constructor(limites)
    parser = DefusedXMLParser(target=constructor, forbid_dtd=True, forbid_entities=True, forbid_external=True)
    constructor.parser = parser
    try:
        parser.feed(datos)
        raiz = parser.close()
    except DefusedXmlException as e:
        raise ErrorParseo("xml.dtd-o-entidades", _linea_segura(constructor), type(e).__name__) from None
    except ParseError as e:
        linea, _columna = e.position
        raise ErrorParseo("xml.mal-formado", linea, str(e)) from None
    if not isinstance(raiz, Nodo):  # pragma: no cover - el parser garantiza un elemento raíz
        raise ErrorParseo("xml.mal-formado", None, "sin elemento raíz")
    return raiz


def _linea_segura(constructor: _Constructor) -> int | None:
    try:
        return constructor._linea()
    except Exception:  # pragma: no cover - solo si el parser ya no existe
        return None
