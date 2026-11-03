"""Parseo XML seguro: sin DTD ni entidades (XXE, «billion laughs»), con límites y sin red."""

import socket
from collections.abc import Iterator

import pytest

from validador_ses_hospedajes.parseo import ErrorParseo, Limites, codificacion_declarada, parsear


@pytest.fixture
def sin_red(monkeypatch: pytest.MonkeyPatch) -> Iterator[list[object]]:
    """Cualquier intento de abrir una conexión de red hace fallar la prueba."""
    intentos: list[object] = []

    def prohibido(*args: object, **kwargs: object) -> None:
        intentos.append(args)
        raise AssertionError("intento de acceso a la red")

    monkeypatch.setattr(socket.socket, "connect", prohibido)
    monkeypatch.setattr(socket, "create_connection", prohibido)
    monkeypatch.setattr(socket, "getaddrinfo", prohibido)
    yield intentos
    assert intentos == []


def test_construye_el_arbol_con_numeros_de_linea() -> None:
    raiz = parsear(
        b'<?xml version="1.0" encoding="UTF-8"?>\n<peticion>\n  <solicitud>\n    <a>x</a>\n  </solicitud>\n</peticion>'
    )
    assert raiz.nombre == "peticion"
    assert raiz.linea == 2
    solicitud = raiz.hijos[0]
    assert (solicitud.nombre, solicitud.linea) == ("solicitud", 3)
    assert (solicitud.hijos[0].nombre, solicitud.hijos[0].linea, solicitud.hijos[0].texto) == ("a", 4, "x")


def test_separa_espacio_de_nombres_y_atributos() -> None:
    raiz = parsear(b'<p:peticion xmlns:p="urn:x" id="1"><p:solicitud/></p:peticion>')
    assert raiz.nombre == "peticion"
    assert raiz.espacio == "urn:x"
    assert raiz.atributos == {"id": "1"}
    assert raiz.hijos[0].espacio == "urn:x"


def test_ignora_comentarios_e_instrucciones_de_proceso() -> None:
    raiz = parsear(b"<a><!-- FICTICIO --><?pi x?><b>1</b></a>")
    assert [h.nombre for h in raiz.hijos] == ["b"]


def test_texto_suelto_entre_hijos_se_conserva_para_detectarlo() -> None:
    raiz = parsear(b"<a>hola<b>1</b>adios</a>")
    assert "hola" in raiz.texto
    assert "adios" in raiz.texto


def test_conserva_acentos_y_respeta_la_codificacion_declarada() -> None:
    utf8 = parsear("<a>Núñez</a>".encode())
    latin1 = parsear('<?xml version="1.0" encoding="ISO-8859-1"?><a>Núñez</a>'.encode("latin-1"))
    assert utf8.texto == latin1.texto == "Núñez"


def test_codificacion_declarada() -> None:
    assert codificacion_declarada(b'<?xml version="1.0" encoding="UTF-8"?><a/>') == "UTF-8"
    assert codificacion_declarada(b"\xef\xbb\xbf<?xml version='1.0' encoding='iso-8859-1'?><a/>") == "iso-8859-1"
    assert codificacion_declarada(b"<a/>") is None


@pytest.mark.parametrize("datos", [b"", b"   \n  "])
def test_fichero_vacio(datos: bytes) -> None:
    with pytest.raises(ErrorParseo) as e:
        parsear(datos)
    assert e.value.codigo == "fichero.vacio"


def test_xml_mal_formado_indica_la_linea() -> None:
    with pytest.raises(ErrorParseo) as e:
        parsear(b"<peticion>\n<solicitud>\n</peticion>")
    assert e.value.codigo == "xml.mal-formado"
    assert e.value.linea == 3


def test_entidad_no_declarada_es_xml_mal_formado() -> None:
    with pytest.raises(ErrorParseo) as e:
        parsear(b"<a>&desconocida;</a>")
    assert e.value.codigo == "xml.mal-formado"


XXE_FICHERO = b"""<?xml version="1.0"?>
<!DOCTYPE peticion [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
<peticion><solicitud>&xxe;</solicitud></peticion>"""

XXE_RED = b"""<?xml version="1.0"?>
<!DOCTYPE peticion [<!ENTITY xxe SYSTEM "http://127.0.0.1:9/robado">]>
<peticion>&xxe;</peticion>"""

DTD_EXTERNA = b"""<?xml version="1.0"?>
<!DOCTYPE peticion SYSTEM "http://127.0.0.1:9/plantilla.dtd">
<peticion/>"""

ENTIDAD_PARAMETRO = b"""<?xml version="1.0"?>
<!DOCTYPE peticion [<!ENTITY % ext SYSTEM "http://127.0.0.1:9/x.dtd"> %ext;]>
<peticion/>"""

BILLION_LAUGHS = b"""<?xml version="1.0"?>
<!DOCTYPE lolz [
 <!ENTITY lol "lol">
 <!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
 <!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;">
 <!ENTITY lol4 "&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;">
]>
<lolz>&lol4;</lolz>"""

DOCTYPE_INOFENSIVO = b'<?xml version="1.0"?>\n<!DOCTYPE peticion>\n<peticion/>'


@pytest.mark.parametrize(
    "datos",
    [XXE_FICHERO, XXE_RED, DTD_EXTERNA, ENTIDAD_PARAMETRO, BILLION_LAUGHS, DOCTYPE_INOFENSIVO],
    ids=["xxe-fichero", "xxe-red", "dtd-externa", "entidad-parametro", "billion-laughs", "doctype"],
)
def test_rechaza_cualquier_dtd_o_entidad_sin_tocar_la_red(datos: bytes, sin_red: list[object]) -> None:
    with pytest.raises(ErrorParseo) as e:
        parsear(datos)
    assert e.value.codigo == "xml.dtd-o-entidades"
    assert "root:" not in str(e.value)


def test_limite_de_tamano() -> None:
    datos = b"<a>" + b"x" * 2000 + b"</a>"
    with pytest.raises(ErrorParseo) as e:
        parsear(datos, Limites(max_bytes=1000))
    assert e.value.codigo == "fichero.demasiado-grande"
    assert parsear(datos, Limites(max_bytes=5000)).nombre == "a"


def test_limite_de_profundidad() -> None:
    profundo = b"<a>" * 40 + b"</a>" * 40
    with pytest.raises(ErrorParseo) as e:
        parsear(profundo)
    assert e.value.codigo == "xml.demasiado-profundo"
    assert parsear(b"<a>" * 10 + b"</a>" * 10).nombre == "a"


def test_limite_de_numero_de_elementos() -> None:
    muchos = b"<a>" + b"<b/>" * 50 + b"</a>"
    with pytest.raises(ErrorParseo) as e:
        parsear(muchos, Limites(max_elementos=20))
    assert e.value.codigo == "xml.demasiados-elementos"


def test_los_limites_por_defecto_son_razonables() -> None:
    limites = Limites()
    assert limites.max_bytes == 10 * 1024 * 1024
    assert limites.max_profundidad == 32
    assert limites.max_elementos >= 100_000
