"""El README no puede quedarse atrás: todas las reglas, los pendientes, la autoría y los avisos obligatorios."""

import re
from pathlib import Path

from validador_ses_hospedajes import REGLAS

RAIZ = Path(__file__).parent.parent
README = (RAIZ / "README.md").read_text(encoding="utf-8")
NOTAS = (RAIZ / "docs" / "oficial" / "NOTAS.md").read_text(encoding="utf-8")


def test_la_tabla_de_reglas_esta_completa_y_al_dia() -> None:
    for regla in REGLAS.values():
        fila = re.search(rf"^\| `{re.escape(regla.codigo)}` \| (\w+) \| ([^|]+) \| ([^|]+) \|", README, re.MULTILINE)
        assert fila, f"falta {regla.codigo} en la tabla del README"
        gravedad, apartado, pendiente = (x.strip() for x in fila.groups())
        assert gravedad == ("Error" if regla.gravedad.value == "error" else "Aviso"), regla.codigo
        assert apartado == regla.apartado, regla.codigo
        assert pendiente == (regla.pendiente or "—"), regla.codigo


def test_cada_pendiente_usado_esta_explicado_en_las_notas() -> None:
    for regla in REGLAS.values():
        if regla.pendiente:
            assert f"| {regla.pendiente} |" in NOTAS, regla.pendiente


def test_autoria_y_avisos() -> None:
    assert (
        "Idea, especificación, revisión y pruebas: Daniel Buitrago (@danielbuitragoh). "
        "Código generado con Claude Code bajo su dirección."
    ) in README
    assert "no es oficial" in README.lower()
    assert "la validación final la hace el portal" in README.lower()
    assert "registro-viajeros" in README
    assert "## English summary" in README
    assert "MIT" in README
