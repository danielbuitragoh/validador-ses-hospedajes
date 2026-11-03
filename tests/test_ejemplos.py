"""Un fichero de ejemplo por regla: tests/ejemplos/invalidos/<codigo>.xml (FICTICIOS y marcados como tales).

Los genera scripts/generar_ejemplos.py a partir de los dos ficheros válidos; esta prueba comprueba que cada
ejemplo dispara su regla con su gravedad, que todas las reglas tienen ejemplo y que los ficheros están al día.
"""

import subprocess
import sys
from pathlib import Path

import pytest

from validador_ses_hospedajes import REGLAS, validar

from ayudas import EJEMPLOS

INVALIDOS = EJEMPLOS / "invalidos"
RAIZ = Path(__file__).parent.parent

#: Reglas sin fichero de ejemplo, con el motivo y dónde se prueban.
SIN_EJEMPLO = {
    "fichero.demasiado-grande": "necesitaría un fichero de más de 10 MB (test_parseo y test_api con límite reducido)",
    "xml.demasiados-elementos": "necesitaría más de 500 000 elementos (test_parseo con límite reducido)",
}
#: Opciones con las que se valida un ejemplo concreto.
OPCIONES: dict[str, dict[str, str]] = {"estructura.tipo-distinto": {"tipo": "reservas"}}
#: Ficheros que no pueden llevar la marca FICTICIO (estarían vacíos o dejarían de ser lo que prueban).
SIN_MARCA = {"fichero.vacio"}

EJEMPLOS_INVALIDOS = sorted(INVALIDOS.glob("*.xml"))


def test_todas_las_reglas_tienen_ejemplo() -> None:
    con_ejemplo = {p.stem for p in EJEMPLOS_INVALIDOS}
    assert con_ejemplo | set(SIN_EJEMPLO) == set(REGLAS)
    assert not con_ejemplo & set(SIN_EJEMPLO)


@pytest.mark.parametrize("ruta", EJEMPLOS_INVALIDOS, ids=[p.stem for p in EJEMPLOS_INVALIDOS])
def test_cada_ejemplo_dispara_su_regla(ruta: Path) -> None:
    codigo = ruta.stem
    inf = validar(ruta, **OPCIONES.get(codigo, {}))  # type: ignore[arg-type]
    encontradas = [i for i in inf.incidencias if i.codigo == codigo]
    assert encontradas, f"{ruta.name}: {[i.codigo for i in inf.incidencias]}"
    assert all(i.gravedad is REGLAS[codigo].gravedad for i in encontradas)
    for inc in inf.incidencias:  # todos los mensajes se pueden componer en los dos idiomas
        assert inc.mensaje("es")
        assert inc.mensaje("en")


@pytest.mark.parametrize("ruta", EJEMPLOS_INVALIDOS, ids=[p.stem for p in EJEMPLOS_INVALIDOS])
def test_los_ejemplos_estan_marcados_como_ficticios(ruta: Path) -> None:
    if ruta.stem in SIN_MARCA:
        return
    assert b"FICTICIO" in ruta.read_bytes()[:400]


@pytest.mark.parametrize("ruta", sorted((EJEMPLOS / "validos").glob("*.xml")), ids=lambda p: p.stem)
def test_los_ejemplos_validos_son_validos_y_ficticios(ruta: Path) -> None:
    assert "FICTICIO" in ruta.read_text(encoding="utf-8")[:400]
    assert validar(ruta).incidencias == ()


def test_los_ejemplos_estan_al_dia_con_el_generador() -> None:
    r = subprocess.run(
        [sys.executable, str(RAIZ / "scripts" / "generar_ejemplos.py"), "--comprobar"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stdout + r.stderr
