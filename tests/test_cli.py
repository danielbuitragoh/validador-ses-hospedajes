"""CLI ``ses-validar``: salida legible, JSON, inglés, varios ficheros o carpetas y códigos de salida."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from validador_ses_hospedajes.cli import main

from validador_ses_hospedajes import REGLAS, __version__

from ayudas import EJEMPLOS, parte

VALIDOS = EJEMPLOS / "validos"
PARTE = VALIDOS / "parte-viajeros.xml"
RESERVA = VALIDOS / "reserva-hospedaje.xml"


@pytest.fixture
def con_errores(tmp_path: Path) -> Path:
    ruta = tmp_path / "con-errores.xml"
    xml = parte().replace(
        "<numeroDocumento>00000001R</numeroDocumento>", "<numeroDocumento>00000001A</numeroDocumento>"
    )
    ruta.write_text(
        xml.replace(
            "<numHabitaciones>1</numHabitaciones>", "<numHabitaciones>1</numHabitaciones><internet>S</internet>"
        ),
        encoding="utf-8",
    )
    return ruta


def ejecutar(capsys: pytest.CaptureFixture[str], *args: str) -> tuple[int, str, str]:
    codigo = main(list(args))
    salida = capsys.readouterr()
    return codigo, salida.out, salida.err


def test_fichero_valido_sale_con_0(capsys: pytest.CaptureFixture[str]) -> None:
    codigo, out, _ = ejecutar(capsys, str(PARTE))
    assert codigo == 0
    assert "VÁLIDO" in out
    assert "parte de viajeros (§3)" in out
    assert "2 comunicaciones" in out
    assert "no es oficial" in out
    assert "portal SES.Hospedajes" in out


def test_errores_legibles_con_ruta_linea_regla_y_apartado(
    capsys: pytest.CaptureFixture[str], con_errores: Path
) -> None:
    codigo, out, _ = ejecutar(capsys, str(con_errores))
    assert codigo == 1
    assert "[ERROR]" in out
    assert "línea 25" in out
    assert "/peticion/solicitud/comunicacion[1]/persona[1]/numeroDocumento" in out
    assert "La letra de control del NIF no es correcta: debería ser «R»." in out
    assert "documento.letra" in out
    assert "§3; §8.5" in out
    assert "[AVISO]" in out
    assert "pendiente P3" in out
    assert "NO VÁLIDO" in out
    assert "1 error" in out
    assert "1 aviso" in out


def test_resumen_de_varios_ficheros(capsys: pytest.CaptureFixture[str], con_errores: Path) -> None:
    codigo, out, _ = ejecutar(capsys, str(PARTE), str(RESERVA), str(con_errores))
    assert codigo == 1
    assert "Resumen: 3 ficheros · 2 válidos · 1 con errores · 1 error y 1 aviso en total." in out


def test_carpeta_recursiva(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    (tmp_path / "sub").mkdir()
    shutil.copy(PARTE, tmp_path / "a.xml")
    shutil.copy(RESERVA, tmp_path / "sub" / "b.XML")
    (tmp_path / "notas.txt").write_text("no es xml", encoding="utf-8")
    codigo, out, _ = ejecutar(capsys, str(tmp_path))
    assert codigo == 0
    assert "Resumen: 2 ficheros · 2 válidos" in out


def test_carpeta_sin_xml(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    codigo, _, err = ejecutar(capsys, str(tmp_path))
    assert codigo == 2
    assert "no contiene ficheros .xml" in err


def test_fichero_inexistente(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    codigo, _, err = ejecutar(capsys, str(PARTE), str(tmp_path / "no-existe.xml"))
    assert codigo == 2
    assert "no-existe.xml" in err


def test_sin_argumentos_es_uso_incorrecto(capsys: pytest.CaptureFixture[str]) -> None:
    codigo, _, err = ejecutar(capsys)
    assert codigo == 2
    assert "ses-validar" in err


def test_json(capsys: pytest.CaptureFixture[str], con_errores: Path) -> None:
    codigo, out, _ = ejecutar(capsys, "--json", str(PARTE), str(con_errores))
    assert codigo == 1
    datos = json.loads(out)
    assert datos["herramienta"] == "validador-ses-hospedajes"
    assert datos["version"] == __version__
    assert datos["oficial"] is False
    assert datos["idioma"] == "es"
    assert datos["resumen"] == {
        "ficheros": 2,
        "validos": 1,
        "con_errores": 1,
        "errores": 1,
        "avisos": 1,
        "no_leidos": 0,
    }
    malo = datos["ficheros"][1]
    assert malo["valido"] is False
    codigos = [i["codigo"] for i in malo["incidencias"]]
    assert codigos == ["valor.booleano", "documento.letra"]
    assert malo["incidencias"][1]["linea"] == 25


def test_json_con_no_leidos(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    codigo, out, _ = ejecutar(capsys, "--json", str(tmp_path / "x.xml"))
    assert codigo == 2
    datos = json.loads(out)
    assert datos["no_leidos"][0]["fichero"].endswith("x.xml")
    assert datos["resumen"]["no_leidos"] == 1


def test_ingles(capsys: pytest.CaptureFixture[str], con_errores: Path) -> None:
    codigo, out, _ = ejecutar(capsys, "--ingles", str(con_errores))
    assert codigo == 1
    assert "The NIF check letter is wrong: it should be 'R'." in out
    assert "line 25" in out
    assert "NOT VALID" in out
    assert "not an official tool" in out
    codigo, out, _ = ejecutar(capsys, "--english", "--json", str(con_errores))
    assert json.loads(out)["idioma"] == "en"


def test_estricto_y_sin_avisos(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    ruta = tmp_path / "aviso.xml"
    ruta.write_text(
        parte()
        .replace("<sexo>M</sexo>", "<sexo>M</sexo>\n<telefono2/>".replace("\n<telefono2/>", ""))
        .replace(
            "<numHabitaciones>1</numHabitaciones>", "<numHabitaciones>1</numHabitaciones><internet>true</internet>"
        ),
        encoding="utf-8",
    )
    assert ejecutar(capsys, str(ruta))[0] == 0
    assert ejecutar(capsys, "--estricto", str(ruta))[0] == 1
    codigo, out, _ = ejecutar(capsys, "--sin-avisos", str(ruta))
    assert codigo == 0
    assert "[AVISO]" not in out


def test_tipo_forzado(capsys: pytest.CaptureFixture[str]) -> None:
    codigo, out, _ = ejecutar(capsys, "--tipo", "reservas", str(PARTE))
    assert codigo == 1
    assert "estructura.tipo-distinto" in out


def test_limite_de_tamano(capsys: pytest.CaptureFixture[str]) -> None:
    codigo, out, _ = ejecutar(capsys, "--max-mb", "0.001", str(PARTE))
    assert codigo == 1
    assert "fichero.demasiado-grande" in out


def test_lista_de_reglas(capsys: pytest.CaptureFixture[str]) -> None:
    codigo, out, _ = ejecutar(capsys, "--reglas")
    assert codigo == 0
    for regla in REGLAS:
        assert regla in out
    codigo, out, _ = ejecutar(capsys, "--reglas", "--json")
    assert {r["codigo"] for r in json.loads(out)} == set(REGLAS)


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as e:
        main(["--version"])
    assert e.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_ejecutable_como_modulo() -> None:
    r = subprocess.run(
        [sys.executable, "-m", "validador_ses_hospedajes", str(PARTE)], capture_output=True, text=True, check=False
    )
    assert r.returncode == 0, r.stderr
    assert "VÁLIDO" in r.stdout


def test_comando_instalado() -> None:
    ejecutable = shutil.which("ses-validar", path=str(Path(sys.executable).parent))
    assert ejecutable is not None
    r = subprocess.run([ejecutable, "--json", str(RESERVA)], capture_output=True, text=True, check=False)
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["ficheros"][0]["tipo"] == "reservas"
