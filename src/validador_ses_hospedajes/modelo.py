"""Tipos públicos del informe de validación."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Literal

Idioma = Literal["es", "en"]


class Gravedad(StrEnum):
    #: Incumple algo que el documento oficial establece: el portal probablemente lo rechazará.
    ERROR = "error"
    #: El documento no lo define con claridad (pendiente) o es una incoherencia probable: revisar.
    AVISO = "aviso"


class TipoComunicacion(StrEnum):
    #: Partes de viajeros (§3, figura 1).
    PARTES = "partes"
    #: Reservas de hospedaje (§4, figura 2).
    RESERVAS = "reservas"


NOMBRE_TIPO: Mapping[TipoComunicacion, Mapping[Idioma, str]] = {
    TipoComunicacion.PARTES: {"es": "parte de viajeros (§3)", "en": "traveller report (§3)"},
    TipoComunicacion.RESERVAS: {"es": "reserva de hospedaje (§4)", "en": "accommodation booking (§4)"},
}


@dataclass(frozen=True, slots=True)
class Incidencia:
    """Un error o aviso, con la regla incumplida y dónde está."""

    codigo: str
    gravedad: Gravedad
    #: Ruta del elemento, p. ej. ``/peticion/solicitud/comunicacion[1]/persona[2]/nombre``.
    ruta: str
    #: Línea del fichero (la del elemento, o la de su bloque si el elemento falta).
    linea: int | None
    #: Apartado del documento oficial (p. ej. ``§3``, ``§7.1; §8.7``).
    apartado: str
    #: Pendiente del documento al que se refiere (``P3``…), si lo hay.
    pendiente: str | None = None
    params: Mapping[str, str | int] = field(default_factory=dict)

    def mensaje(self, idioma: Idioma = "es") -> str:
        from .reglas import REGLAS

        regla = REGLAS[self.codigo]
        plantilla = regla.mensaje_es if idioma == "es" else regla.mensaje_en
        return plantilla.format_map(dict(self.params))

    def regla(self, idioma: Idioma = "es") -> str:
        from .reglas import REGLAS

        regla = REGLAS[self.codigo]
        return regla.descripcion_es if idioma == "es" else regla.descripcion_en

    def a_dict(self, idioma: Idioma = "es") -> dict[str, object]:
        return {
            "codigo": self.codigo,
            "gravedad": self.gravedad.value,
            "ruta": self.ruta,
            "linea": self.linea,
            "apartado": self.apartado,
            "pendiente": self.pendiente,
            "mensaje": self.mensaje(idioma),
            "regla": self.regla(idioma),
        }


@dataclass(frozen=True, slots=True)
class Informe:
    """Resultado de validar un fichero."""

    #: Nombre o ruta del fichero (``None`` si se validó texto o bytes sin nombre).
    origen: str | None
    #: Tipo detectado (o forzado). ``None`` si no se pudo determinar.
    tipo: TipoComunicacion | None
    #: Número de bloques ``comunicacion`` del fichero.
    comunicaciones: int
    incidencias: tuple[Incidencia, ...]

    @property
    def errores(self) -> tuple[Incidencia, ...]:
        return tuple(i for i in self.incidencias if i.gravedad is Gravedad.ERROR)

    @property
    def avisos(self) -> tuple[Incidencia, ...]:
        return tuple(i for i in self.incidencias if i.gravedad is Gravedad.AVISO)

    @property
    def valido(self) -> bool:
        """``True`` si no hay errores (puede haber avisos)."""
        return not self.errores

    def a_dict(self, idioma: Idioma = "es") -> dict[str, object]:
        return {
            "fichero": self.origen,
            "tipo": self.tipo.value if self.tipo else None,
            "comunicaciones": self.comunicaciones,
            "valido": self.valido,
            "errores": len(self.errores),
            "avisos": len(self.avisos),
            "incidencias": [i.a_dict(idioma) for i in self.incidencias],
        }
