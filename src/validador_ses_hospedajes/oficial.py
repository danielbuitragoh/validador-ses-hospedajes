"""Tablas de códigos transcritas LITERALMENTE de docs/oficial/Instrucciones.pdf (v1.1.0, 08-01-2024).

- Apartado 8.3 a 8.7 (las tablas 8.1, 8.2, 8.8 y 8.9 son de vehículos y no aplican a un alojamiento).
- Roles TI/VI: tablas de ``persona`` de los apartados 3 y 4.

NO añadir códigos que no estén en ese documento. PENDIENTE-OFICIAL (P17): el texto de los apartados 3 y 4 remite a
«la tabla … en el apartado 6. Tablas de códigos», pero las tablas están en el apartado 8 (errata del documento).
"""

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final


def _tabla(d: dict[str, str]) -> Mapping[str, str]:
    return MappingProxyType(d)


#: §3 y §4 (campo ``rol``): «TI – titular del contrato», «VI - viajero».
ROL_PERSONA: Final = _tabla({"TI": "titular del contrato", "VI": "viajero"})

#: §8.3 Relación de parentesco.
PARENTESCO: Final = _tabla(
    {
        "AB": "Abuelo/a",
        "BA": "Bisabuelo/a",
        "BN": "Bisnieto/a",
        "CD": "Cuñado/a",
        "CY": "Cónyuge",
        "HJ": "Hijo/a",
        "HR": "Hermano/a",
        "NI": "Nieto/a",
        "PM": "Padre o madre",
        "SB": "Sobrino/a",
        "SG": "Suegro/a",
        "TI": "Tío/a",
        "YN": "Yerno o nuera",
        "TU": "Tutor/a",
        "OT": "Otro",
    }
)

#: §8.4 Sexo.
SEXO: Final = _tabla({"H": "Hombre", "M": "Mujer", "O": "Otro"})

#: §8.5 Tipos de documento. PENDIENTE-OFICIAL (P16): solo estos cuatro; no hay código para otros documentos.
TIPO_DOCUMENTO: Final = _tabla(
    {
        "NIF": "NIF - Número de Identificación Fiscal",
        "NIE": "NIE - Número de Identidad de Extranjero",
        "PAS": "Número de pasaporte",
        "OTRO": "Otro",
    }
)

#: §8.6 Tipos de establecimiento.
TIPO_ESTABLECIMIENTO: Final = _tabla(
    {
        "ALBERGUE": "Albergue",
        "APART": "Apartamento",
        "APARTHOTEL": "Apartahotel",
        "AP_RURAL": "Apartamento rural",
        "BALNEARIO": "Balneario",
        "CAMPING": "Camping",
        "CASA_HUESP": "Casa de huéspedes",
        "CASA_RURAL": "Casa rural",
        "HOSTAL": "Hostal",
        "HOTEL": "Hotel",
        "H_RURAL": "Hotel rural",
        "MOTEL": "Motel",
        "OFIC_VEHIC": "Oficina de alquiler de vehículos",
        "OTROS": "Otro",
        "PARADOR": "Parador de turismo",
        "PENSION": "Pensión",
        "RESIDENCIA": "Residencia",
    }
)

#: §8.7 Tipos de pago.
TIPO_PAGO: Final = _tabla(
    {
        "EFECT": "Efectivo",
        "TARJT": "Tarjeta de crédito",
        "PLATF": "Plataforma de pago",
        "TRANS": "Transferencia",
        "MOVIL": "Pago por móvil",
        "TREG": "Tarjeta regalo",
        "DESTI": "Pago en destino",
        "OTRO": "Otros medios de pago",
    }
)

#: §7.1: el código de país de España en ISO 3166-1 alfa-3 (la norma que cita el documento).
PAIS_ESPANA: Final = "ESP"
