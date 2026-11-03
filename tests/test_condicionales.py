"""Obligatoriedades condicionales (§3, §4, §7.1) y documento de identidad (§3, §4, §8.5). Datos FICTICIOS.

En parte-viajeros.xml, la comunicación 1 tiene un adulto (Lucía, NIF, parentesco PM) y un menor (Mateo, sin
documento); la comunicación 2, un adulto extranjero con pasaporte. En reserva-hospedaje.xml, la comunicación 1 tiene
un titular con NIE y dos viajeros con solo nombre, apellido y teléfono.
"""

import pytest

from ayudas import avisos, errores, informe, parte, quitar, reserva, sustituir

LUCIA_DOC = (
    "<tipoDocumento>NIF</tipoDocumento>\n        <numeroDocumento>00000001R</numeroDocumento>\n"
    "        <soporteDocumento>ZZZ000001</soporteDocumento>"
)


def lucia(xml: str, buscar: str, poner: str) -> str:
    """Cambia algo en el bloque de Lucía (primera persona del parte)."""
    inicio = xml.index("<nombre>Lucía</nombre>")
    fin = xml.index("</persona>", inicio)
    return xml[:inicio] + sustituir(xml[inicio:fin], buscar, poner) + xml[fin:]


# --- §3: segundo apellido y soporte ---


def test_apellido2_obligatorio_con_nif_en_partes() -> None:
    inf = informe(lucia(parte(), r"\s*<apellido2>Ejemplo</apellido2>", ""))
    [inc] = inf.errores
    assert inc.codigo == "persona.apellido2-nif"
    assert inc.ruta == "/peticion/solicitud/comunicacion[1]/persona[1]/apellido2"
    assert inc.apartado == "§3"


def test_apellido2_vacio_con_nif_tambien_es_error() -> None:
    assert "persona.apellido2-nif" in errores(lucia(parte(), r"<apellido2>Ejemplo</apellido2>", "<apellido2/>"))


def test_sin_apellido2_con_pasaporte_no_es_error() -> None:
    assert errores(parte()) == set()  # John (PAS) no tiene apellido2


def test_apellido2_no_obligatorio_en_reservas() -> None:
    xml = reserva().replace("<tipoDocumento>NIE</tipoDocumento>", "<tipoDocumento>NIF</tipoDocumento>")
    xml = xml.replace("<numeroDocumento>X0000003A</numeroDocumento>", "<numeroDocumento>00000001R</numeroDocumento>")
    assert errores(quitar(xml, "apellido2")) == set()


def test_soporte_obligatorio_con_nif() -> None:
    assert errores(lucia(parte(), r"\s*<soporteDocumento>ZZZ000001</soporteDocumento>", "")) == {
        "persona.soporte-nif-nie"
    }


def test_soporte_obligatorio_con_nie() -> None:
    xml = lucia(parte(), LUCIA_DOC, "<tipoDocumento>NIE</tipoDocumento><numeroDocumento>X0000003A</numeroDocumento>")
    inf = informe(xml)
    assert {i.codigo for i in inf.errores} == {"persona.soporte-nif-nie"}
    assert "NIE" in inf.errores[0].mensaje()


# --- §3: documento obligatorio si es mayor de edad (P6: 18 años en la fecha de entrada) ---


def test_adulto_sin_documento_en_partes() -> None:
    xml = lucia(parte(), LUCIA_DOC, "")
    assert errores(xml) == {"persona.documento-mayor"}


def test_menor_sin_documento_no_es_error() -> None:
    assert informe(parte()).incidencias == ()


@pytest.mark.parametrize(("nacimiento", "es_error"), [("2008-11-02", True), ("2008-11-03", False)])
def test_mayoria_de_edad_se_calcula_en_la_fecha_de_entrada(nacimiento: str, es_error: bool) -> None:
    # Entrada de la comunicación 1: 2026-11-02. Mateo (sin documento) cumple 18 ese día o al día siguiente.
    xml = parte().replace(
        "<fechaNacimiento>2016-07-20</fechaNacimiento>", f"<fechaNacimiento>{nacimiento}</fechaNacimiento>"
    )
    assert ("persona.documento-mayor" in errores(xml)) is es_error


def test_en_reservas_el_documento_no_es_obligatorio() -> None:
    xml = quitar(quitar(reserva(), "tipoDocumento"), "numeroDocumento")
    assert errores(xml) == set()


def test_tipo_de_documento_sin_numero() -> None:
    xml = lucia(parte(), r"\s*<numeroDocumento>00000001R</numeroDocumento>", "")
    assert errores(xml) == {"persona.documento-mayor"}
    xml = quitar(reserva(), "numeroDocumento")
    assert errores(xml) == set()
    assert avisos(xml) == {"documento.sin-numero"}


def test_numero_de_documento_sin_tipo() -> None:
    xml = quitar(reserva(), "tipoDocumento")
    assert errores(xml) == {"documento.sin-tipo"}


# --- §3/§4: formato del NIF y del NIE (letra de control) ---


@pytest.mark.parametrize(
    ("tipo", "numero", "codigo"),
    [
        ("NIF", "00000001A", "documento.letra"),
        ("NIF", "0000001R", "documento.nif-formato"),
        ("NIF", "X0000003A", "documento.nie-como-nif"),
        ("NIE", "X0000003B", "documento.letra"),
        ("NIE", "X000003A", "documento.nie-formato"),
        ("NIE", "00000001R", "documento.nif-como-nie"),
    ],
)
def test_formato_del_nif_y_del_nie(tipo: str, numero: str, codigo: str) -> None:
    xml = lucia(
        parte(),
        LUCIA_DOC,
        f"<tipoDocumento>{tipo}</tipoDocumento><numeroDocumento>{numero}</numeroDocumento>"
        "<soporteDocumento>ZZZ000001</soporteDocumento>",
    )
    assert errores(xml) == {codigo}


def test_letra_esperada_en_el_mensaje() -> None:
    xml = lucia(parte(), "00000001R", "00000001A")
    [inc] = informe(xml).errores
    assert "«R»" in inc.mensaje()
    assert "'R'" in inc.mensaje("en")


def test_la_letra_tambien_se_comprueba_en_reservas() -> None:
    assert errores(reserva().replace("X0000003A", "X0000003B")) == {"documento.letra"}


def test_nif_en_minusculas_o_con_separadores_solo_avisa() -> None:
    for numero in ("00000001r", "00.000.001-R"):
        xml = lucia(parte(), "00000001R", numero)
        assert errores(xml) == set()
        assert avisos(xml) == {"documento.normalizable"}


def test_nif_k_l_m_avisa_que_no_se_verifica() -> None:
    xml = lucia(parte(), "00000001R", "K0000001Z")
    assert errores(xml) == set()
    assert avisos(xml) == {"documento.nif-sin-verificar"}


def test_pasaporte_con_numero_de_dni_avisa() -> None:
    xml = parte().replace(
        "<numeroDocumento>ZZ0000001</numeroDocumento>", "<numeroDocumento>00000002W</numeroDocumento>"
    )
    assert errores(xml) == set()
    assert avisos(xml) == {"documento.tipo-no-corresponde"}


# --- §3: parentesco cuando hay menores (aclaración de la v1.1.0) ---


def test_menor_sin_ningun_adulto_con_parentesco() -> None:
    inf = informe(quitar(parte(), "parentesco"))
    [inc] = inf.errores
    assert inc.codigo == "persona.parentesco-menor"
    assert inc.ruta == "/peticion/solicitud/comunicacion[1]"


def test_parentesco_en_el_menor_en_vez_del_adulto() -> None:
    xml = quitar(parte(), "parentesco").replace(
        "<telefono>+34600000001</telefono>\n      </persona>",
        "<telefono>+34600000001</telefono><parentesco>HJ</parentesco>\n      </persona>",
    )
    assert errores(xml) == {"persona.parentesco-menor"}
    assert avisos(xml) == {"persona.parentesco-en-menor"}


def test_varios_menores_avisa() -> None:
    menor = parte().split("<persona>")[2].split("</persona>")[0]
    xml = parte().replace("<numPersonas>2</numPersonas>", "<numPersonas>3</numPersonas>")
    xml = xml.replace(
        "</persona>\n    </comunicacion>", f"</persona><persona>{menor}</persona>\n    </comunicacion>", 1
    )
    assert errores(xml) == set()
    assert avisos(xml) == {"persona.parentesco-varios-menores"}


# --- §3/§4: al menos un medio de contacto ---


def test_sin_telefono_ni_correo() -> None:
    xml = lucia(parte(), r"\s*<telefono>\+34600000001</telefono>\s*<correo>lucia@example.com</correo>", "")
    assert errores(xml) == {"persona.contacto"}
    assert errores(quitar(reserva(), "correo")) == {"persona.contacto"}


def test_basta_con_telefono2() -> None:
    xml = lucia(
        parte(),
        r"<telefono>\+34600000001</telefono>\s*<correo>lucia@example.com</correo>",
        "<telefono2>600000009</telefono2>",
    )
    assert errores(xml) == set()


# --- §7.1: municipio según el país ---


def test_espana_sin_codigo_de_municipio() -> None:
    xml = quitar(parte(), "codigoMunicipio")
    assert errores(xml) == {"direccion.municipio-espana"}


def test_espana_con_nombre_de_municipio_pero_sin_codigo() -> None:
    xml = parte().replace("<codigoMunicipio>28079</codigoMunicipio>", "<nombreMunicipio>Madrid</nombreMunicipio>", 1)
    assert errores(xml) == {"direccion.municipio-espana"}


def test_extranjero_sin_nombre_de_municipio() -> None:
    assert errores(quitar(parte(), "nombreMunicipio")) == {"direccion.municipio-extranjero"}


def test_codigo_ine_en_direccion_extranjera_avisa() -> None:
    xml = parte().replace(
        "<nombreMunicipio>Springfield</nombreMunicipio>",
        "<codigoMunicipio>28079</codigoMunicipio><nombreMunicipio>Springfield</nombreMunicipio>",
    )
    assert errores(xml) == set()
    assert avisos(xml) == {"direccion.ine-fuera-espana"}


def test_direccion_del_establecimiento() -> None:
    xml = reserva().replace("<codigoMunicipio>44001</codigoMunicipio>", "")
    inf = informe(xml)
    [inc] = inf.errores
    assert inc.codigo == "direccion.municipio-espana"
    assert "/establecimiento/datosEstablecimiento/direccion" in inc.ruta


# --- §3/§4: roles TI y VI ---


def test_parte_sin_ningun_viajero_vi() -> None:
    xml = parte().replace("<rol>VI</rol>", "<rol>TI</rol>", 2)
    assert "comunicacion.sin-viajero" in errores(xml)


def test_parte_con_titular_y_viajeros_es_valido() -> None:
    xml = parte().replace("<rol>VI</rol>", "<rol>TI</rol>", 1)
    assert errores(xml) == set()


def test_reserva_sin_titular() -> None:
    assert errores(reserva().replace("<rol>TI</rol>", "<rol>VI</rol>", 1)) == {"comunicacion.sin-titular"}


def test_reserva_con_dos_titulares_avisa() -> None:
    xml = reserva().replace("<rol>VI</rol>", "<rol>TI</rol>", 1)
    assert errores(xml) == set()
    assert avisos(xml) == {"comunicacion.varios-titulares"}
