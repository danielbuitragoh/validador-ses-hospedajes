"""Letra de control de DNI/NIF y NIE.

§3 y §4 (``numeroDocumento``): «Deberá corresponder al tipo de documento del campo tipoDocumento, y tener un formato
válido en el caso de NIF o NIE». El algoritmo de la letra es público y estable (módulo 23; Orden EHA/451/2008).
"""

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Final

LETRAS_DNI: Final = "TRWAGMYFPDXBNJZSQVHLCKE"

_RE_DNI: Final = re.compile(r"(\d{8})([A-Z])")
_RE_NIE: Final = re.compile(r"([XYZ])(\d{7})([A-Z])")
# PENDIENTE-OFICIAL (P24): NIF de personas físicas que empiezan por K, L o M. El documento solo pide «formato válido»;
# se aceptan por su forma y se avisa de que su letra no se ha verificado.
_RE_NIF_ESPECIAL: Final = re.compile(r"[KLM]\d{7}[A-Z]")
_SEPARADORES: Final = re.compile(r"[\s.\-_/]")


class Motivo(StrEnum):
    FORMATO = "formato"
    LETRA = "letra"
    PARECE_NIE = "parece-nie"
    PARECE_DNI = "parece-dni"


@dataclass(frozen=True, slots=True)
class ResultadoDocumento:
    valido: bool
    normalizado: str
    motivo: Motivo | None = None
    #: Letra de control que correspondería (solo si ``motivo`` es LETRA).
    esperada: str | None = None
    #: NIF K/L/M: forma correcta, letra no verificada (P24).
    sin_verificar: bool = False
    #: Solo es válido tras pasar a mayúsculas y quitar separadores (P25).
    normalizable: bool = False


def normalizar(valor: str) -> str:
    """Mayúsculas y sin espacios, puntos, guiones, barras ni subrayados."""
    return _SEPARADORES.sub("", valor.upper())


def letra_dni(numero: str) -> str:
    return LETRAS_DNI[int(numero) % 23]


def validar_nif(valor: str) -> ResultadoDocumento:
    v = normalizar(valor)
    cambiado = v != valor
    if _RE_NIE.fullmatch(v):
        return ResultadoDocumento(False, v, Motivo.PARECE_NIE)
    if _RE_NIF_ESPECIAL.fullmatch(v):
        return ResultadoDocumento(True, v, sin_verificar=True, normalizable=cambiado)
    m = _RE_DNI.fullmatch(v)
    if not m:
        return ResultadoDocumento(False, v, Motivo.FORMATO)
    esperada = letra_dni(m.group(1))
    if esperada != m.group(2):
        return ResultadoDocumento(False, v, Motivo.LETRA, esperada)
    return ResultadoDocumento(True, v, normalizable=cambiado)


def validar_nie(valor: str) -> ResultadoDocumento:
    v = normalizar(valor)
    cambiado = v != valor
    if _RE_DNI.fullmatch(v):
        return ResultadoDocumento(False, v, Motivo.PARECE_DNI)
    m = _RE_NIE.fullmatch(v)
    if not m:
        return ResultadoDocumento(False, v, Motivo.FORMATO)
    esperada = letra_dni(str("XYZ".index(m.group(1))) + m.group(2))
    if esperada != m.group(3):
        return ResultadoDocumento(False, v, Motivo.LETRA, esperada)
    return ResultadoDocumento(True, v, normalizable=cambiado)


def parece_dni_o_nie_valido(valor: str) -> bool:
    """¿Es un DNI o NIE con su letra correcta? Sirve para avisar si se declaró como PAS u OTRO (P26)."""
    nif = validar_nif(valor)
    return (nif.valido and not nif.sin_verificar) or validar_nie(valor).valido
