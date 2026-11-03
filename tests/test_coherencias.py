"""Coherencias entre campos: fechas, número de personas y referencias. Datos FICTICIOS."""

from ayudas import avisos, errores, informe, parte, reserva, sustituir


def test_salida_anterior_a_la_entrada_es_error() -> None:
    xml = parte().replace(
        "<fechaSalida>2026-11-05T11:00:00</fechaSalida>", "<fechaSalida>2026-11-01T11:00:00</fechaSalida>"
    )
    inf = informe(xml)
    [inc] = inf.errores
    assert inc.codigo == "contrato.salida-anterior"
    assert inc.ruta == "/peticion/solicitud/comunicacion[1]/contrato/fechaSalida"


def test_salida_igual_a_la_entrada_solo_avisa() -> None:
    xml = parte().replace(
        "<fechaSalida>2026-11-05T11:00:00</fechaSalida>", "<fechaSalida>2026-11-02T15:30:00</fechaSalida>"
    )
    assert errores(xml) == set()
    assert avisos(xml) == {"contrato.salida-igual"}


def test_salida_el_mismo_dia_pero_mas_tarde_es_valida() -> None:
    xml = parte().replace(
        "<fechaSalida>2026-11-05T11:00:00</fechaSalida>", "<fechaSalida>2026-11-02T23:00:00</fechaSalida>"
    )
    assert informe(xml).incidencias == ()


def test_con_fechas_mal_formadas_no_se_comparan() -> None:
    xml = parte().replace("<fechaSalida>2026-11-05T11:00:00</fechaSalida>", "<fechaSalida>2026-11-01</fechaSalida>")
    assert errores(xml) == {"valor.fecha-hora"}


def test_contrato_posterior_a_la_entrada_avisa() -> None:
    xml = parte().replace("<fechaContrato>2026-10-20</fechaContrato>", "<fechaContrato>2026-11-03</fechaContrato>")
    assert errores(xml) == set()
    assert avisos(xml) == {"contrato.contrato-posterior"}
    mismo_dia = parte().replace(
        "<fechaContrato>2026-10-20</fechaContrato>", "<fechaContrato>2026-11-02</fechaContrato>"
    )
    assert informe(mismo_dia).incidencias == ()


def test_hora_desconocida_en_partes_avisa_y_en_reservas_no() -> None:
    xml = parte().replace("2026-11-02T15:30:00", "2026-11-02T00:00:00")
    assert errores(xml) == set()
    assert avisos(xml) == {"contrato.hora-cero-parte"}
    assert informe(reserva()).incidencias == ()  # la reserva 1 usa T00:00:00 (§4 lo prevé)


def test_nacimiento_posterior_a_la_entrada_avisa() -> None:
    xml = parte().replace(
        "<fechaNacimiento>2016-07-20</fechaNacimiento>", "<fechaNacimiento>2027-01-01</fechaNacimiento>"
    )
    assert errores(xml) == set()
    assert avisos(xml) == {"persona.nacimiento-posterior"}


def test_mas_personas_en_el_parte_que_num_personas_es_error() -> None:
    xml = parte().replace("<numPersonas>2</numPersonas>", "<numPersonas>1</numPersonas>")
    inf = informe(xml)
    [inc] = inf.errores
    assert inc.codigo == "contrato.num-personas"
    assert inc.ruta == "/peticion/solicitud/comunicacion[1]/contrato/numPersonas"
    assert "2 persona(s), 2 con rol VI" in inc.mensaje()


def test_menos_personas_en_el_parte_que_num_personas_avisa() -> None:
    # El documento no dice expresamente que haya que incluir un bloque por cada persona alojada (P28).
    xml = parte().replace("<numPersonas>2</numPersonas>", "<numPersonas>3</numPersonas>")
    assert errores(xml) == set()
    assert avisos(xml) == {"contrato.num-personas-faltan"}


def test_num_personas_admite_contar_o_no_al_titular_del_parte() -> None:
    # P8: con un TI además de los VI, numPersonas puede contar todas las personas o solo los viajeros.
    titular = (
        "<persona><rol>TI</rol><nombre>Tito</nombre><apellido1>Ficticio</apellido1><fechaNacimiento>1970-01-01"
        "</fechaNacimiento><tipoDocumento>PAS</tipoDocumento></persona>"
    )
    xml = sustituir(
        parte(),
        r"(<persona>\s*<rol>VI</rol>\s*<nombre>Lucía)",
        titular.replace("<tipoDocumento>PAS</tipoDocumento>", "") + r"\1",
    )
    base = errores(xml) - {"contrato.num-personas"}
    assert "contrato.num-personas" not in errores(xml)  # 2 VI = numPersonas 2
    con_3 = xml.replace("<numPersonas>2</numPersonas>", "<numPersonas>3</numPersonas>")
    assert errores(con_3) - base == set()  # 3 personas en total


def test_reserva_con_mas_viajeros_que_num_personas_avisa() -> None:
    xml = reserva().replace("<numPersonas>2</numPersonas>", "<numPersonas>1</numPersonas>")
    assert errores(xml) == set()
    assert avisos(xml) == {"contrato.num-personas-reserva"}


def test_reserva_con_menos_viajeros_que_num_personas_es_valida() -> None:
    # §4: «tantos bloques como información de viajeros se disponga».
    xml = reserva().replace("<numPersonas>2</numPersonas>", "<numPersonas>4</numPersonas>")
    assert informe(xml).incidencias == ()


def test_referencia_de_contrato_repetida_avisa() -> None:
    xml = parte().replace("FICTICIO-0002", "FICTICIO-0001")
    assert errores(xml) == set()
    inf = informe(xml)
    [inc] = inf.avisos
    assert inc.codigo == "solicitud.referencia-duplicada"
    assert "1, 2" in inc.mensaje()
