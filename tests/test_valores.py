"""Formatos de los campos (tablas de §3, §4, §7.1, §7.2) y códigos de las tablas del §8. Datos FICTICIOS."""

import pytest

from ayudas import avisos, errores, informe, parte, reserva, sustituir


def cambiar(xml: str, etiqueta: str, valor: str, veces: int = 1) -> str:
    return sustituir(xml, rf"<{etiqueta}>[^<]*</{etiqueta}>", f"<{etiqueta}>{valor}</{etiqueta}>", veces)


# --- vacíos ---


def test_obligatorio_vacio_es_error() -> None:
    assert errores(cambiar(parte(), "nombre", "   ")) == {"valor.vacio-obligatorio"}
    assert errores(parte().replace("<referencia>FICTICIO-0001</referencia>", "<referencia/>")) == {
        "valor.vacio-obligatorio"
    }


def test_opcional_vacio_es_aviso() -> None:
    xml = cambiar(parte(), "nacionalidad", "")
    assert errores(xml) == set()
    assert avisos(xml) == {"valor.vacio-opcional"}


def test_los_espacios_alrededor_no_cuentan() -> None:
    assert informe(cambiar(parte(), "tipoPago", "  TARJT \n ")).incidencias == ()


# --- longitudes String(n) ---


@pytest.mark.parametrize(
    ("etiqueta", "maximo"),
    [
        ("codigoEstablecimiento", 10),
        ("referencia", 50),
        ("nombre", 50),
        ("apellido1", 50),
        ("apellido2", 50),
        ("numeroDocumento", 15),
        ("soporteDocumento", 9),
        ("direccion", 100),
        ("codigoPostal", 20),
        ("medioPago", 50),
        ("titular", 100),
        ("telefono", 20),
    ],
)
def test_longitud_maxima(etiqueta: str, maximo: int) -> None:
    relleno = "9" if etiqueta in ("telefono", "codigoPostal") else "A"
    justo = cambiar(parte(), etiqueta, relleno * maximo)
    assert "valor.longitud" not in errores(justo)
    largo = cambiar(parte(), etiqueta, relleno * (maximo + 1))
    assert "valor.longitud" in errores(largo)


def test_longitud_cuenta_caracteres_no_bytes() -> None:
    assert "valor.longitud" not in errores(cambiar(parte(), "nombre", "ñ" * 50))


def test_longitud_del_correo_y_de_datos_establecimiento() -> None:
    assert "valor.longitud" in errores(cambiar(parte(), "correo", "a" * 40 + "@example.com"))
    assert "valor.longitud" in errores(cambiar(reserva(), "codigo", "12345678901"))
    assert "valor.longitud" in errores(cambiar(reserva(), "nombre", "C" * 51, veces=0))


def test_el_mensaje_no_repite_datos_personales() -> None:
    inf = informe(cambiar(parte(), "nombre", "Secretísimo" * 6))
    [inc] = inf.errores
    assert "Secretísimo" not in inc.mensaje()
    assert "Secretísimo" not in inc.mensaje("en")


# --- fechas ---


@pytest.mark.parametrize(
    "valor", ["20/10/2026", "2026-10-20T00:00:00", "2026-02-30", "2026-13-01", "26-10-20", "2026-1-5"]
)
def test_fecha_aaaa_mm_dd(valor: str) -> None:
    assert errores(cambiar(parte(), "fechaContrato", valor)) >= {"valor.fecha"}


def test_fecha_de_nacimiento_y_de_pago() -> None:
    assert "valor.fecha" in errores(cambiar(parte(), "fechaNacimiento", "12/04/1985"))
    assert "valor.fecha" in errores(cambiar(parte(), "fechaPago", "2026-10-32"))


def test_fecha_bisiesta() -> None:
    assert "valor.fecha" not in errores(cambiar(parte(), "fechaContrato", "2024-02-29"))
    assert "valor.fecha" in errores(cambiar(parte(), "fechaContrato", "2025-02-29"))


@pytest.mark.parametrize(
    "valor",
    [
        "2026-11-02T15:30",
        "2026-11-02 15:30:00",
        "2026-11-02",
        "2026-11-02T24:00:00",
        "2026-11-02T15:60:00",
        "02/11/2026",
    ],
)
def test_fecha_hora_aaaa_mm_ddThh_mm_ss(valor: str) -> None:
    assert "valor.fecha-hora" in errores(cambiar(parte(), "fechaEntrada", valor))


def test_fecha_hora_con_zona_o_milisegundos_no_es_el_formato_oficial() -> None:
    assert "valor.fecha-hora" in errores(cambiar(parte(), "fechaSalida", "2026-11-05T11:00:00Z"))
    assert "valor.fecha-hora" in errores(cambiar(parte(), "fechaSalida", "2026-11-05T11:00:00.000"))


# --- numéricos y booleano ---


@pytest.mark.parametrize("valor", ["dos", "2 personas", "", "1e3"])
def test_numerico(valor: str) -> None:
    codigos = errores(cambiar(parte(), "numPersonas", valor))
    assert codigos & {"valor.numerico", "valor.vacio-obligatorio"}


@pytest.mark.parametrize("valor", ["0", "2.5", "-1"])
def test_numerico_no_entero_positivo_es_aviso(valor: str) -> None:
    assert "valor.numerico-entero" in avisos(cambiar(parte(), "numHabitaciones", valor))
    assert "valor.numerico" not in errores(cambiar(parte(), "numHabitaciones", valor))


# --- códigos de las tablas del §8 ---


@pytest.mark.parametrize(
    ("xml_base", "etiqueta", "valor"),
    [
        ("parte", "rol", "XX"),
        ("parte", "rol", "vi"),
        ("parte", "tipoDocumento", "DNI"),
        ("parte", "sexo", "F"),
        ("parte", "parentesco", "PA"),
        ("parte", "tipoPago", "BIZUM"),
        ("parte", "tipoPago", "efect"),
        ("reserva", "tipo", "HOTELITO"),
    ],
)
def test_codigo_fuera_de_la_tabla_oficial(xml_base: str, etiqueta: str, valor: str) -> None:
    xml = parte() if xml_base == "parte" else reserva()
    inf = informe(cambiar(xml, etiqueta, valor))
    incs = [i for i in inf.errores if i.codigo == "valor.codigo"]
    assert incs, inf.incidencias
    assert valor in incs[0].mensaje()
    assert "§8" in incs[0].apartado or etiqueta == "rol"


@pytest.mark.parametrize("valor", ["H", "M", "O"])
def test_todos_los_codigos_de_sexo(valor: str) -> None:
    assert "valor.codigo" not in errores(cambiar(parte(), "sexo", valor))


# --- país, INE, caducidad, correo, teléfono, soporte ---


@pytest.mark.parametrize("valor", ["ES", "esp", "XXX", "España", "724"])
def test_pais_iso_alfa_3(valor: str) -> None:
    assert "valor.pais" in errores(cambiar(parte(), "nacionalidad", valor))


def test_pais_de_la_direccion() -> None:
    assert "valor.pais" in errores(
        cambiar(parte(), "pais", "US", veces=0).replace("<pais>US</pais>", "<pais>ESP</pais>", 1)
    )


@pytest.mark.parametrize("valor", ["2807", "280790", "28O79", "28 079"])
def test_codigo_municipio_ine_5_digitos(valor: str) -> None:
    assert "valor.municipio-ine" in errores(cambiar(parte(), "codigoMunicipio", valor))


@pytest.mark.parametrize("valor", ["9/2028", "13/2028", "2028-09", "09/28", "00/2028"])
def test_caducidad_tarjeta_mm_aaaa(valor: str) -> None:
    assert "valor.caducidad" in errores(cambiar(parte(), "caducidadTarjeta", valor))


@pytest.mark.parametrize(
    "valor", ["lucia.example.com", "lucia@", "@example.com", "lucia@example", "lu cia@example.com"]
)
def test_correo_con_formato_valido(valor: str) -> None:
    assert "valor.correo" in errores(cambiar(parte(), "correo", valor))


def test_telefono_con_letras_solo_avisa() -> None:
    xml = cambiar(parte(), "telefono", "llamar por la tarde")
    assert errores(xml) == set()
    assert "valor.telefono" in avisos(xml)
    assert "valor.telefono" not in avisos(cambiar(parte(), "telefono", "+34 (600) 00-00.01"))


def test_soporte_no_alfanumerico_solo_avisa() -> None:
    xml = cambiar(parte(), "soporteDocumento", "ZZZ-00001")
    assert errores(xml) == set()
    assert avisos(xml) == {"valor.soporte"}


def test_codigo_postal_espanol() -> None:
    xml = cambiar(parte(), "codigoPostal", "2800")
    assert errores(xml) == set()
    assert "direccion.codigo-postal" in avisos(xml)
    otra_provincia = cambiar(parte(), "codigoPostal", "08001")
    assert errores(otra_provincia) == set()
    assert avisos(otra_provincia) == {"direccion.cp-provincia"}
