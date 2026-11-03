"""Letra de control de DNI/NIF y NIE (§3: «formato válido en el caso de NIF o NIE»). Números ficticios."""

import pytest

from validador_ses_hospedajes.documentos import (
    LETRAS_DNI,
    Motivo,
    letra_dni,
    normalizar,
    parece_dni_o_nie_valido,
    validar_nie,
    validar_nif,
)


def test_tabla_de_letras() -> None:
    assert LETRAS_DNI == "TRWAGMYFPDXBNJZSQVHLCKE"


@pytest.mark.parametrize("resto", range(23))
def test_cada_una_de_las_23_letras(resto: int) -> None:
    numero = str(resto).zfill(8)
    assert letra_dni(numero) == LETRAS_DNI[resto]
    assert validar_nif(numero + LETRAS_DNI[resto]).valido
    otra = LETRAS_DNI[(resto + 1) % 23]
    r = validar_nif(numero + otra)
    assert not r.valido
    assert r.motivo is Motivo.LETRA
    assert r.esperada == LETRAS_DNI[resto]


def test_nif_valido() -> None:
    r = validar_nif("12345678Z")
    assert (r.valido, r.normalizado, r.motivo, r.sin_verificar, r.normalizable) == (
        True,
        "12345678Z",
        None,
        False,
        False,
    )


@pytest.mark.parametrize("valor", ["1234567Z", "123456789Z", "12345678", "ABCDEFGHZ", "12345678ZZ", ""])
def test_nif_formato_incorrecto(valor: str) -> None:
    r = validar_nif(valor)
    assert not r.valido
    assert r.motivo is Motivo.FORMATO


def test_un_nie_escrito_como_nif() -> None:
    r = validar_nif("X1234567L")
    assert not r.valido
    assert r.motivo is Motivo.PARECE_NIE


@pytest.mark.parametrize("valor", ["K1234567S", "L1234567S", "M1234567S"])
def test_nif_especiales_k_l_m_se_aceptan_sin_verificar_la_letra(valor: str) -> None:
    r = validar_nif(valor)
    assert r.valido
    assert r.sin_verificar


@pytest.mark.parametrize("valor", ["X1234567L", "Y1234567X", "Z1234567R"])
def test_nie_valido(valor: str) -> None:
    assert validar_nie(valor).valido


def test_nie_letra_incorrecta() -> None:
    r = validar_nie("X1234567A")
    assert not r.valido
    assert r.motivo is Motivo.LETRA
    assert r.esperada == "L"


def test_un_dni_escrito_como_nie() -> None:
    r = validar_nie("12345678Z")
    assert not r.valido
    assert r.motivo is Motivo.PARECE_DNI


@pytest.mark.parametrize("valor", ["X123456L", "W1234567L", "X12345678L", "XL"])
def test_nie_formato_incorrecto(valor: str) -> None:
    r = validar_nie(valor)
    assert not r.valido
    assert r.motivo is Motivo.FORMATO


def test_normalizar() -> None:
    assert normalizar(" 12.345.678-z ") == "12345678Z"
    assert normalizar("x-1234567/l") == "X1234567L"


@pytest.mark.parametrize(
    ("valor", "funcion"), [("12345678z", validar_nif), ("12.345.678-Z", validar_nif), ("x 1234567 l", validar_nie)]
)
def test_valido_solo_tras_normalizar(valor: str, funcion: object) -> None:
    assert callable(funcion)
    r = funcion(valor)
    assert r.valido
    assert r.normalizable


def test_parece_dni_o_nie_valido() -> None:
    assert parece_dni_o_nie_valido("12345678Z")
    assert parece_dni_o_nie_valido("X1234567L")
    assert not parece_dni_o_nie_valido("12345678A")
    assert not parece_dni_o_nie_valido("AB1234567")
