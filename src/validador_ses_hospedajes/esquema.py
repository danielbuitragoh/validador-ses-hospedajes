"""Esquema declarativo transcrito de docs/oficial/Instrucciones.pdf (v1.1.0).

- Orden, obligatoriedad (línea continua) y repetición (1..∞) de las figuras 1 (§3), 2 (§4), 5 (§7.1) y 6 (§7.2).
- Tipo y longitud de las tablas de esos apartados. Las obligatoriedades **condicionales** de las tablas
  (apellido2 con NIF, soporte con NIF/NIE, documento si es mayor de edad, contacto, municipio según país,
  parentesco con menores…) no están aquí: las comprueba ``validador.py`` con su apartado.

PENDIENTE-OFICIAL (P1): el documento no incluye el XSD; esto es una transcripción de sus figuras y tablas.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum, auto

from . import oficial


class Tipo(StrEnum):
    TEXTO = auto()
    FECHA = auto()
    FECHA_HORA = auto()
    NUMERICO = auto()
    BOOLEANO = auto()
    CODIGO = auto()
    PAIS = auto()
    INE = auto()
    CADUCIDAD = auto()
    CORREO = auto()
    TELEFONO = auto()
    SOPORTE = auto()


@dataclass(frozen=True, slots=True)
class Campo:
    """Elemento con valor (hoja)."""

    nombre: str
    apartado: str
    obligatorio: bool = False
    tipo: Tipo = Tipo.TEXTO
    #: String(n) de la tabla.
    maximo: int | None = None
    tabla: Mapping[str, str] | None = None
    tabla_apartado: str | None = None
    #: Otros nombres con los que el documento llama a este campo (P2).
    alias: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Bloque:
    """Elemento con elementos hijos, en secuencia (o elección)."""

    nombre: str
    apartado: str
    hijos: tuple["Campo | Bloque", ...]
    obligatorio: bool = True
    repetible: bool = False
    #: Los hijos son alternativas: exactamente uno (§4, ``establecimiento``).
    eleccion: bool = False


Def = Campo | Bloque


def _texto(nombre: str, apartado: str, maximo: int, obligatorio: bool = False) -> Campo:
    return Campo(nombre, apartado, obligatorio, Tipo.TEXTO, maximo)


def _codigo(nombre: str, apartado: str, tabla: Mapping[str, str], tabla_ap: str, maximo: int, obl: bool) -> Campo:
    return Campo(nombre, apartado, obl, Tipo.CODIGO, maximo, tabla, tabla_ap)


def _direccion(obligatorio: bool, apartado_padre: str) -> Bloque:
    """§7.1, figura 5. ``codigoMunicipio`` y ``nombreMunicipio`` son condicionales según el país."""
    ap = "§7.1"
    return Bloque(
        "direccion",
        apartado_padre if apartado_padre == ap else f"{apartado_padre}; {ap}",
        (
            _texto("direccion", ap, 100, obligatorio=True),
            _texto("direccionComplementaria", ap, 100),
            Campo("codigoMunicipio", ap, False, Tipo.INE, 5),
            _texto("nombreMunicipio", ap, 100),
            _texto("codigoPostal", ap, 20, obligatorio=True),
            Campo("pais", ap, True, Tipo.PAIS, 3),
        ),
        obligatorio=obligatorio,
    )


def _pago() -> Bloque:
    """§7.2, figura 6 (actualizado en la v1.1.0)."""
    ap = "§7.2"
    return Bloque(
        "pago",
        ap,
        (
            _codigo("tipoPago", ap, oficial.TIPO_PAGO, "§8.7", 5, obl=True),
            Campo("fechaPago", ap, False, Tipo.FECHA),
            _texto("medioPago", ap, 50),
            _texto("titular", ap, 100),
            Campo("caducidadTarjeta", ap, False, Tipo.CADUCIDAD, 7),
        ),
    )


def _contrato(ap: str) -> Bloque:
    """§3 y §4: mismo contenido y orden (figuras 1 y 2)."""
    return Bloque(
        "contrato",
        ap,
        (
            _texto("referencia", ap, 50, obligatorio=True),
            Campo("fechaContrato", ap, True, Tipo.FECHA),
            Campo("fechaEntrada", ap, True, Tipo.FECHA_HORA),
            Campo("fechaSalida", ap, True, Tipo.FECHA_HORA),
            Campo("numPersonas", ap, True, Tipo.NUMERICO),
            Campo("numHabitaciones", ap, False, Tipo.NUMERICO),
            # PENDIENTE-OFICIAL (P3): Booleano sin formato definido.
            Campo("internet", ap, False, Tipo.BOOLEANO),
            _pago(),
        ),
    )


def _persona_comun_inicio(ap: str) -> tuple[Def, ...]:
    return (
        _codigo("rol", ap, oficial.ROL_PERSONA, ap, 2, obl=True),
        _texto("nombre", ap, 50, obligatorio=True),
        _texto("apellido1", ap, 50, obligatorio=True),
        _texto("apellido2", ap, 50),
        _codigo("tipoDocumento", ap, oficial.TIPO_DOCUMENTO, "§8.5", 5, obl=False),
    )


def _contacto(ap: str) -> tuple[Def, ...]:
    return (
        Campo("telefono", ap, False, Tipo.TELEFONO, 20),
        Campo("telefono2", ap, False, Tipo.TELEFONO, 20),
        Campo("correo", ap, False, Tipo.CORREO, 50),
    )


def _persona_parte() -> Bloque:
    """§3, figura 1."""
    ap = "§3"
    return Bloque(
        "persona",
        ap,
        (
            *_persona_comun_inicio(ap),
            # PENDIENTE-OFICIAL (P2): la tabla del §3 lo llama «documento»; la figura 1, «numeroDocumento».
            Campo("numeroDocumento", ap, False, Tipo.TEXTO, 15, alias=("documento",)),
            Campo("soporteDocumento", ap, False, Tipo.SOPORTE, 9),
            Campo("fechaNacimiento", ap, True, Tipo.FECHA),
            Campo("nacionalidad", ap, False, Tipo.PAIS, 3),
            _codigo("sexo", ap, oficial.SEXO, "§8.4", 1, obl=False),
            _direccion(True, ap),
            *_contacto(ap),
            _codigo("parentesco", ap, oficial.PARENTESCO, "§8.3", 5, obl=False),
        ),
        repetible=True,
    )


def _persona_reserva() -> Bloque:
    """§4, figura 2: sin ``soporteDocumento`` ni ``parentesco``."""
    ap = "§4"
    return Bloque(
        "persona",
        ap,
        (
            *_persona_comun_inicio(ap),
            Campo("numeroDocumento", ap, False, Tipo.TEXTO, 15),
            Campo("fechaNacimiento", ap, False, Tipo.FECHA),
            Campo("nacionalidad", ap, False, Tipo.PAIS, 3),
            _codigo("sexo", ap, oficial.SEXO, "§8.4", 1, obl=False),
            _direccion(False, ap),
            *_contacto(ap),
        ),
        repetible=True,
    )


def _establecimiento() -> Bloque:
    """§4, figura 2: elección entre ``codigo`` y ``datosEstablecimiento``."""
    ap = "§4"
    return Bloque(
        "establecimiento",
        ap,
        (
            _texto("codigo", ap, 10),
            Bloque(
                "datosEstablecimiento",
                ap,
                (
                    _codigo("tipo", ap, oficial.TIPO_ESTABLECIMIENTO, "§8.6", 10, obl=True),
                    _texto("nombre", ap, 50, obligatorio=True),
                    _direccion(True, ap),
                ),
                obligatorio=False,
            ),
        ),
        eleccion=True,
    )


ESQUEMA_PARTES = Bloque(
    "peticion",
    "§3",
    (
        Bloque(
            "solicitud",
            "§3",
            (
                _texto("codigoEstablecimiento", "§3", 10, obligatorio=True),
                Bloque("comunicacion", "§3", (_contrato("§3"), _persona_parte()), repetible=True),
            ),
        ),
    ),
)

ESQUEMA_RESERVAS = Bloque(
    "peticion",
    "§4",
    (
        Bloque(
            "solicitud",
            "§4",
            (
                Bloque(
                    "comunicacion",
                    "§4",
                    (_establecimiento(), _contrato("§4"), _persona_reserva()),
                    repetible=True,
                ),
            ),
        ),
    ),
)
