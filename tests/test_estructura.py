"""Estructura y orden de elementos (figuras 1 y 2, §2: un solo tipo por fichero)."""

import pytest

from validador_ses_hospedajes import Gravedad, TipoComunicacion

from ayudas import avisos, errores, informe, parte, quitar, reserva, sustituir


def test_los_ejemplos_validos_no_tienen_incidencias() -> None:
    for xml, tipo in [(parte(), TipoComunicacion.PARTES), (reserva(), TipoComunicacion.RESERVAS)]:
        inf = informe(xml)
        assert inf.incidencias == ()
        assert inf.valido
        assert inf.tipo is tipo
        assert inf.comunicaciones == 2


def test_raiz_distinta_de_peticion() -> None:
    xml = parte().replace("<peticion>", "<peticiones>").replace("</peticion>", "</peticiones>")
    assert errores(xml) == {"estructura.raiz"}


def test_falta_solicitud() -> None:
    assert "estructura.falta" in errores("<peticion></peticion>", tipo="partes")


def test_tipo_indeterminado_sin_pistas() -> None:
    xml = quitar(parte(), "codigoEstablecimiento")
    assert errores(xml) == {"estructura.tipo-indeterminado"}


def test_tipo_forzado_cuando_no_hay_pistas() -> None:
    xml = quitar(parte(), "codigoEstablecimiento")
    inf = informe(xml, tipo="partes")
    assert inf.tipo is TipoComunicacion.PARTES
    assert {i.codigo for i in inf.errores} == {"estructura.falta"}


def test_tipo_forzado_que_no_coincide() -> None:
    assert errores(reserva(), tipo="partes") == {"estructura.tipo-distinto"}
    assert errores(parte(), tipo=TipoComunicacion.RESERVAS) == {"estructura.tipo-distinto"}


def test_un_solo_tipo_de_comunicacion_por_fichero() -> None:
    comunicacion_reserva = reserva().split("<comunicacion>")[1].split("</comunicacion>")[0]
    xml = parte().replace("</solicitud>", f"<comunicacion>{comunicacion_reserva}</comunicacion></solicitud>")
    assert errores(xml) == {"estructura.tipos-mezclados"}


def test_vehiculos_no_soportados() -> None:
    xml = "<peticion><solicitud><comunicacion><contrato/><vehiculo/></comunicacion></solicitud></peticion>"
    assert errores(xml) == {"estructura.tipo-no-soportado"}


def test_elemento_desconocido_con_ruta_y_linea() -> None:
    xml = parte().replace("<numPersonas>2</numPersonas>", "<numPersonas>2</numPersonas><habitacion>101</habitacion>")
    inf = informe(xml)
    [inc] = inf.errores
    assert inc.codigo == "estructura.elemento-desconocido"
    assert inc.ruta == "/peticion/solicitud/comunicacion[1]/contrato/habitacion"
    assert inc.linea == 13
    assert inc.apartado.startswith("§3")


def test_soporte_y_parentesco_no_existen_en_reservas() -> None:
    xml = reserva().replace("<sexo>M</sexo>", "<sexo>M</sexo><parentesco>PM</parentesco>")
    assert errores(xml) == {"estructura.elemento-desconocido"}
    xml = reserva().replace(
        "<fechaNacimiento>1990", "<soporteDocumento>ZZZ000003</soporteDocumento><fechaNacimiento>1990"
    )
    assert errores(xml) == {"estructura.elemento-desconocido"}


def test_orden_de_elementos() -> None:
    xml = sustituir(parte(), r"(<nombre>Lucía</nombre>)(\s*)(<apellido1>Prueba</apellido1>)", r"\3\2\1")
    inf = informe(xml)
    assert [i.codigo for i in inf.errores] == ["estructura.orden"]
    assert inf.errores[0].ruta.endswith("/persona[1]/nombre")


def test_orden_en_el_bloque_direccion() -> None:
    xml = sustituir(parte(), r"(<codigoPostal>28001</codigoPostal>)(\s*)(<pais>ESP</pais>)", r"\3\2\1")
    assert errores(xml) == {"estructura.orden"}


def test_falta_un_elemento_obligatorio() -> None:
    inf = informe(quitar(parte(), "referencia"))
    [inc] = inf.errores
    assert inc.codigo == "estructura.falta"
    assert inc.ruta == "/peticion/solicitud/comunicacion[1]/contrato/referencia"
    assert inc.linea == 8


@pytest.mark.parametrize("etiqueta", ["fechaNacimiento", "nombre", "apellido1", "rol"])
def test_obligatorios_de_persona_en_partes(etiqueta: str) -> None:
    assert "estructura.falta" in errores(quitar(parte(), etiqueta))


def test_direccion_obligatoria_en_partes_y_opcional_en_reservas() -> None:
    sin_direccion = sustituir(parte(), r"\n\s*<direccion>\s*<direccion>Calle.*?</pais>\s*</direccion>", "")
    assert "estructura.falta" in errores(sin_direccion)
    sin_direccion = sustituir(reserva(), r"\n\s*<direccion>\s*<direccion>Avenida.*?</pais>\s*</direccion>", "")
    assert errores(sin_direccion) == set()


def test_bloque_pago_obligatorio() -> None:
    assert "estructura.falta" in errores(sustituir(parte(), r"\n\s*<pago>\s*<tipoPago>EFECT</tipoPago>\s*</pago>", ""))


def test_elemento_unico_duplicado() -> None:
    xml = parte().replace("<sexo>M</sexo>", "<sexo>M</sexo><sexo>M</sexo>")
    assert errores(xml) == {"estructura.duplicado"}


def test_texto_suelto_en_un_bloque() -> None:
    xml = parte().replace("<contrato>", "<contrato>texto suelto", 1)
    assert errores(xml) == {"estructura.texto-en-bloque"}


def test_un_campo_no_puede_tener_hijos() -> None:
    xml = parte().replace("<nombre>Lucía</nombre>", "<nombre><b>Lucía</b></nombre>")
    assert errores(xml) == {"estructura.hijos-en-campo"}


def test_establecimiento_codigo_o_datos_y_solo_uno() -> None:
    sin_nada = reserva().replace("<codigo>0000099999</codigo>", "")
    assert errores(sin_nada) == {"establecimiento.codigo-o-datos"}
    datos = reserva().split("<establecimiento>")[2].split("</establecimiento>")[0]
    ambos = reserva().replace("<codigo>0000099999</codigo>", f"<codigo>0000099999</codigo>{datos}")
    assert errores(ambos) == {"establecimiento.codigo-o-datos"}


def test_datos_establecimiento_obligatorios() -> None:
    assert "estructura.falta" in errores(quitar(reserva(), "tipo"))


def test_espacio_de_nombres_y_atributos_solo_avisan() -> None:
    xml = parte().replace("<peticion>", '<peticion xmlns="urn:ejemplo:ficticio">')
    assert errores(xml) == set()
    assert avisos(xml) == {"estructura.espacio-nombres"}
    xml = parte().replace("<persona>", '<persona id="1">')
    assert errores(xml) == set()
    assert avisos(xml) == {"estructura.atributos"}


def test_documento_en_lugar_de_numero_documento_en_partes_avisa() -> None:
    xml = parte().replace("<numeroDocumento>00000001R</numeroDocumento>", "<documento>00000001R</documento>")
    assert errores(xml) == set()
    assert avisos(xml) == {"estructura.documento-alias"}
    xml = parte().replace("<numeroDocumento>00000001R</numeroDocumento>", "<documento>00000001A</documento>")
    assert "documento.letra" in errores(xml)


def test_documento_no_es_alias_en_reservas() -> None:
    xml = reserva().replace("<numeroDocumento>X0000003A</numeroDocumento>", "<documento>X0000003A</documento>")
    assert "estructura.elemento-desconocido" in errores(xml)


def test_internet_se_admite_con_aviso() -> None:
    xml = parte().replace(
        "<numHabitaciones>1</numHabitaciones>", "<numHabitaciones>1</numHabitaciones><internet>true</internet>"
    )
    assert errores(xml) == set()
    assert avisos(xml) == {"valor.booleano"}


def test_gravedad_y_resumen_del_informe() -> None:
    inf = informe(quitar(parte(), "referencia"))
    assert not inf.valido
    assert len(inf.errores) == 1
    assert inf.avisos == ()
    assert inf.errores[0].gravedad is Gravedad.ERROR
