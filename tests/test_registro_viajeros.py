"""Prueba cruzada con registro-viajeros (https://github.com/danielbuitragoh/registro-viajeros).

Los XML de tests/ejemplos/registro-viajeros/ los genera el PROPIO código de registro-viajeros (sus validadores del
modelo y su ``construirXml``, igual que su ``generarFichero``) con sus datos ficticios de prueba y de demo, mediante
scripts/registro_viajeros/generar.mjs, sin modificar aquel repositorio. Este validador debe aceptarlos todos.

Si la variable de entorno ``REGISTRO_VIAJEROS`` apunta a una copia de ese repositorio y hay Node ≥ 22, además se
regeneran en el momento y se comprueba que coinciden byte a byte con los guardados (la CI lo hace).
"""

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from validador_ses_hospedajes import validar

from ayudas import EJEMPLOS

CARPETA = EJEMPLOS / "registro-viajeros"
MANIFIESTO = CARPETA / "manifiesto.json"
GENERADOR = Path(__file__).parent.parent / "scripts" / "registro_viajeros" / "generar.mjs"
FICHEROS = sorted(CARPETA.glob("*.xml"))

#: Avisos (nunca errores) que se esperan en algún fichero, con su porqué. La demo de registro-viajeros incluye una
#: reserva con numPersonas = 3 y un solo viajero registrado; registro-viajeros también avisa («viajeros_cuenta»).
AVISOS_ESPERADOS: dict[str, set[str]] = {"ficticio-parte-demo.xml": {"contrato.num-personas-faltan"}}


def test_hay_partes_y_reservas_de_registro_viajeros() -> None:
    nombres = [p.name for p in FICHEROS]
    assert len(nombres) >= 6
    assert all(n.startswith("ficticio-") for n in nombres)
    assert any("parte" in n for n in nombres)
    assert any("reserva" in n for n in nombres)


@pytest.mark.parametrize("ruta", FICHEROS, ids=[p.stem for p in FICHEROS])
def test_el_validador_acepta_los_xml_de_registro_viajeros(ruta: Path) -> None:
    inf = validar(ruta)
    assert inf.valido, [(i.codigo, i.ruta) for i in inf.errores]
    assert {i.codigo for i in inf.avisos} == AVISOS_ESPERADOS.get(ruta.name, set())
    assert inf.tipo is not None
    assert inf.tipo.value == ("partes" if "-parte" in ruta.name else "reservas")


def test_manifiesto_con_origen_y_huellas() -> None:
    datos = json.loads(MANIFIESTO.read_text(encoding="utf-8"))
    assert datos["repositorio"] == "https://github.com/danielbuitragoh/registro-viajeros"
    assert len(datos["commit"]) == 40
    assert set(datos["ficheros"]) == {p.name for p in FICHEROS}
    for nombre, huella in datos["ficheros"].items():
        assert hashlib.sha256((CARPETA / nombre).read_bytes()).hexdigest() == huella


@pytest.mark.skipif(
    not os.environ.get("REGISTRO_VIAJEROS") or shutil.which("node") is None,
    reason="definir REGISTRO_VIAJEROS=<copia de registro-viajeros> y tener Node >= 22 para regenerar en vivo",
)
def test_regenerados_en_vivo_coinciden_y_son_validos(tmp_path: Path) -> None:
    origen = Path(os.environ["REGISTRO_VIAJEROS"]).resolve()
    node = shutil.which("node")
    assert node is not None
    r = subprocess.run([node, str(GENERADOR), str(origen), str(tmp_path)], capture_output=True, text=True, check=False)
    assert r.returncode == 0, r.stderr
    generados = sorted(tmp_path.glob("*.xml"))
    assert [p.name for p in generados] == [p.name for p in FICHEROS]
    for p in generados:
        inf = validar(p)
        assert inf.valido, p.name
        assert {i.codigo for i in inf.avisos} == AVISOS_ESPERADOS.get(p.name, set())
        assert p.read_bytes() == (CARPETA / p.name).read_bytes(), f"{p.name} ha cambiado en registro-viajeros"
