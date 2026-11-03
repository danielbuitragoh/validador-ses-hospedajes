"""Las tablas de códigos son copia literal del apartado 8 de docs/oficial/Instrucciones.pdf (v1.1.0)."""

from validador_ses_hospedajes import oficial
from validador_ses_hospedajes.paises import PAISES_ALFA3


def test_8_3_parentesco() -> None:
    assert dict(oficial.PARENTESCO) == {
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


def test_8_4_sexo() -> None:
    assert dict(oficial.SEXO) == {"H": "Hombre", "M": "Mujer", "O": "Otro"}


def test_8_5_tipos_de_documento_solo_cuatro() -> None:
    assert dict(oficial.TIPO_DOCUMENTO) == {
        "NIF": "NIF - Número de Identificación Fiscal",
        "NIE": "NIE - Número de Identidad de Extranjero",
        "PAS": "Número de pasaporte",
        "OTRO": "Otro",
    }


def test_8_6_tipos_de_establecimiento() -> None:
    assert dict(oficial.TIPO_ESTABLECIMIENTO) == {
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


def test_8_7_tipos_de_pago() -> None:
    assert dict(oficial.TIPO_PAGO) == {
        "EFECT": "Efectivo",
        "TARJT": "Tarjeta de crédito",
        "PLATF": "Plataforma de pago",
        "TRANS": "Transferencia",
        "MOVIL": "Pago por móvil",
        "TREG": "Tarjeta regalo",
        "DESTI": "Pago en destino",
        "OTRO": "Otros medios de pago",
    }


def test_roles_de_los_apartados_3_y_4() -> None:
    assert dict(oficial.ROL_PERSONA) == {"TI": "titular del contrato", "VI": "viajero"}


def test_los_codigos_caben_en_su_longitud_oficial() -> None:
    # §3/§4/§7.2: rol String(2), tipoDocumento String(5), sexo String(1), parentesco String(5),
    # datosEstablecimiento/tipo String(10), tipoPago String(5).
    for tabla, maximo in [
        (oficial.ROL_PERSONA, 2),
        (oficial.TIPO_DOCUMENTO, 5),
        (oficial.SEXO, 1),
        (oficial.PARENTESCO, 5),
        (oficial.TIPO_ESTABLECIMIENTO, 10),
        (oficial.TIPO_PAGO, 5),
    ]:
        assert all(len(codigo) <= maximo for codigo in tabla)


def test_paises_iso_3166_1_alfa_3() -> None:
    assert len(PAISES_ALFA3) == 249
    assert {"ESP", "FRA", "DEU", "USA", "GBR", "MAR", "PRT"} <= PAISES_ALFA3
    assert all(len(c) == 3 and c.isupper() and c.isalpha() for c in PAISES_ALFA3)
    assert "ES" not in PAISES_ALFA3
