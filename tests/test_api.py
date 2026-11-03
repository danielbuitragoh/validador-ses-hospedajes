"""API de librería: validar(bytes | str | ruta) -> Informe."""

import json
from pathlib import Path

import pytest

from validador_ses_hospedajes import (
    REGLAS,
    Gravedad,
    Informe,
    Limites,
    TipoComunicacion,
    validar,
    validar_bytes,
    validar_fichero,
)

from ayudas import EJEMPLOS, parte

PARTE = EJEMPLOS / "validos" / "parte-viajeros.xml"


def test_acepta_bytes_texto_ruta_y_pathlike() -> None:
    informes = [
        validar(PARTE.read_bytes()),
        validar(PARTE.read_text(encoding="utf-8")),
        validar(str(PARTE)),
        validar(PARTE),
        validar_bytes(PARTE.read_bytes()),
        validar_fichero(PARTE),
    ]
    for inf in informes:
        assert isinstance(inf, Informe)
        assert inf.valido
        assert inf.tipo is TipoComunicacion.PARTES


def test_origen() -> None:
    assert validar(PARTE).origen == str(PARTE)
    assert validar(PARTE.read_bytes()).origen is None
    assert validar(PARTE.read_bytes(), origen="subido.xml").origen == "subido.xml"


def test_texto_con_bom_y_espacios_iniciales() -> None:
    assert validar("﻿\n  " + parte()).valido


def test_texto_que_declara_otra_codificacion() -> None:
    xml = parte().replace('encoding="UTF-8"', 'encoding="ISO-8859-1"')
    inf = validar(xml)
    assert [i.codigo for i in inf.incidencias] == ["xml.codificacion"]
    latin1 = validar(xml.encode("latin-1"))
    assert [i.codigo for i in latin1.incidencias] == ["xml.codificacion"]


def test_ruta_inexistente_lanza_file_not_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="no-existe"):
        validar(tmp_path / "no-existe.xml")


def test_fichero_demasiado_grande_no_se_lee(tmp_path: Path) -> None:
    grande = tmp_path / "grande.xml"
    grande.write_bytes(b"<peticion>" + b" " * 5000 + b"</peticion>")
    inf = validar(grande, limites=Limites(max_bytes=1000))
    assert [i.codigo for i in inf.errores] == ["fichero.demasiado-grande"]
    assert "5021" in inf.errores[0].mensaje()


def test_errores_de_parseo_en_el_informe() -> None:
    inf = validar(b"<peticion>\n<solicitud>\n</peticion>")
    [inc] = inf.errores
    assert (inc.codigo, inc.linea, inc.gravedad) == ("xml.mal-formado", 3, Gravedad.ERROR)
    assert inf.tipo is None
    assert validar(b"").errores[0].codigo == "fichero.vacio"


def test_tipo_forzado_como_texto_o_enum() -> None:
    assert validar(PARTE, tipo="partes").tipo is TipoComunicacion.PARTES
    assert validar(PARTE, tipo=TipoComunicacion.PARTES).valido
    with pytest.raises(ValueError, match="vehiculos"):
        validar(PARTE, tipo="vehiculos")


def test_incidencias_ordenadas_por_linea() -> None:
    xml = (
        parte()
        .replace("<sexo>H</sexo>", "<sexo>X</sexo>")
        .replace("<tipoPago>TARJT</tipoPago>", "<tipoPago>Y</tipoPago>")
    )
    lineas = [i.linea or 0 for i in validar(xml).incidencias]
    assert lineas == sorted(lineas)
    assert len(lineas) == 3


def test_a_dict_es_serializable_en_json_y_en_ingles() -> None:
    xml = parte().replace("<sexo>H</sexo>", "<sexo>X</sexo>", 1)
    inf = validar(xml)
    datos = json.loads(json.dumps(inf.a_dict()))
    assert datos["valido"] is False
    [inc] = datos["incidencias"]
    assert set(inc) == {"codigo", "gravedad", "ruta", "linea", "apartado", "pendiente", "mensaje", "regla"}
    assert inc["codigo"] == "valor.codigo"
    assert "no es un código válido" in inc["mensaje"]
    en = inf.a_dict("en")["incidencias"]
    assert isinstance(en, list)
    assert "is not a valid code" in en[0]["mensaje"]


#: Reglas que el documento SÍ establece, pero cuyo cálculo depende de un pendiente: se aplica la interpretación más
#: tolerante. P6: «mayor de edad» = 18 años en la fecha de entrada. P8: numPersonas puede contar o no al titular.
ERRORES_CON_CALCULO_PENDIENTE = {"persona.documento-mayor", "persona.parentesco-menor", "contrato.num-personas"}


def test_catalogo_de_reglas_coherente() -> None:
    for codigo, regla in REGLAS.items():
        assert regla.codigo == codigo
        assert regla.apartado
        assert regla.descripcion_es
        assert regla.descripcion_en
        if regla.gravedad is Gravedad.ERROR and codigo not in ERRORES_CON_CALCULO_PENDIENTE:
            assert regla.pendiente is None, f"{codigo}: un pendiente nunca debe producir por sí solo un error"


def test_los_errores_con_calculo_pendiente_existen() -> None:
    for codigo in ERRORES_CON_CALCULO_PENDIENTE:
        assert REGLAS[codigo].gravedad is Gravedad.ERROR
        assert REGLAS[codigo].pendiente in ("P6", "P8")
