"""Genera tests/ejemplos/invalidos/<regla>.xml: un ejemplo FICTICIO por regla, a partir de los ejemplos válidos.

Uso:
    uv run python scripts/generar_ejemplos.py              # (re)escribe los ejemplos
    uv run python scripts/generar_ejemplos.py --comprobar  # sale con 1 si no están al día (lo usa una prueba)

Cada ejemplo cambia lo mínimo para incumplir UNA regla y lleva en la línea 2 un comentario que lo marca como
ficticio y dice qué regla y qué apartado del documento oficial ilustra.
"""

import re
import sys
from collections.abc import Callable
from pathlib import Path

from validador_ses_hospedajes import REGLAS

RAIZ = Path(__file__).resolve().parent.parent
VALIDOS = RAIZ / "tests" / "ejemplos" / "validos"
DESTINO = RAIZ / "tests" / "ejemplos" / "invalidos"

PARTE = (VALIDOS / "parte-viajeros.xml").read_text(encoding="utf-8")
RESERVA = (VALIDOS / "reserva-hospedaje.xml").read_text(encoding="utf-8")


def cambiar(xml: str, buscar: str, poner: str, veces: int = 1) -> str:
    """Sustitución literal que exige que el texto exista (si los ejemplos válidos cambian, falla aquí)."""
    if buscar not in xml:
        raise ValueError(f"no aparece: {buscar!r}")
    return xml.replace(buscar, poner, veces)


def cambiar_re(xml: str, patron: str, poner: str) -> str:
    nuevo, n = re.subn(patron, poner, xml, count=1, flags=re.DOTALL)
    if not n:
        raise ValueError(f"no aparece: {patron!r}")
    return nuevo


def quitar(xml: str, etiqueta: str) -> str:
    return cambiar_re(xml, rf"\n\s*<{etiqueta}>[^<]*</{etiqueta}>", "")


def en_lucia(xml: str, buscar: str, poner: str) -> str:
    """Cambia algo solo dentro del bloque de Lucía (primera persona del parte)."""
    inicio = xml.index("<nombre>Lucía</nombre>")
    fin = xml.index("</persona>", inicio)
    return xml[:inicio] + cambiar(xml[inicio:fin], buscar, poner) + xml[fin:]


MENOR = PARTE.split("<persona>")[2].split("</persona>")[0]
COMUNICACION_RESERVA = RESERVA.split("<comunicacion>")[1].split("</comunicacion>")[0]
DOC_LUCIA = "<tipoDocumento>NIF</tipoDocumento>\n        <numeroDocumento>00000001R</numeroDocumento>"

Mutacion = Callable[[], str]

MUTACIONES: dict[str, Mutacion] = {
    # Fichero y seguridad
    "xml.mal-formado": lambda: cambiar(PARTE, "</peticion>\n", ""),
    "xml.dtd-o-entidades": lambda: cambiar(
        cambiar(PARTE, "<peticion>", '<!DOCTYPE peticion [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>\n<peticion>'),
        "<nombre>Lucía</nombre>",
        "<nombre>&xxe;</nombre>",
    ),
    "xml.demasiado-profundo": lambda: (
        '<?xml version="1.0" encoding="UTF-8"?>\n<!-- @MARCA@ -->\n<peticion>'
        + "<x>" * 40
        + "</x>" * 40
        + "</peticion>\n"
    ),
    "xml.codificacion": lambda: cambiar(PARTE, 'encoding="UTF-8"', 'encoding="ISO-8859-1"'),
    # Estructura
    "estructura.raiz": lambda: cambiar(cambiar(PARTE, "<peticion>", "<peticiones>"), "</peticion>", "</peticiones>"),
    "estructura.tipo-indeterminado": lambda: quitar(PARTE, "codigoEstablecimiento"),
    "estructura.tipo-no-soportado": lambda: (
        '<?xml version="1.0" encoding="UTF-8"?>\n<!-- @MARCA@ -->\n<peticion>\n  <solicitud>\n    <comunicacion>\n'
        "      <contrato><referencia>FICTICIO-V-1</referencia></contrato>\n"
        "      <vehiculo><categoria>FICTICIA</categoria></vehiculo>\n    </comunicacion>\n  </solicitud>\n</peticion>\n"
    ),
    "estructura.tipos-mezclados": lambda: cambiar(
        PARTE, "  </solicitud>", f"    <comunicacion>{COMUNICACION_RESERVA}</comunicacion>\n  </solicitud>"
    ),
    "estructura.tipo-distinto": lambda: PARTE,
    "estructura.elemento-desconocido": lambda: cambiar(
        PARTE, "<numPersonas>2</numPersonas>", "<numPersonas>2</numPersonas><habitacion>101</habitacion>"
    ),
    "estructura.orden": lambda: cambiar_re(
        PARTE, r"(<nombre>Lucía</nombre>)(\s*)(<apellido1>Prueba</apellido1>)", r"\3\2\1"
    ),
    "estructura.duplicado": lambda: cambiar(PARTE, "<sexo>M</sexo>", "<sexo>M</sexo><sexo>M</sexo>"),
    "estructura.falta": lambda: quitar(PARTE, "referencia"),
    "estructura.texto-en-bloque": lambda: cambiar(PARTE, "<contrato>", "<contrato>texto suelto"),
    "estructura.hijos-en-campo": lambda: cambiar(PARTE, "<nombre>Lucía</nombre>", "<nombre><b>Lucía</b></nombre>"),
    "estructura.espacio-nombres": lambda: cambiar(PARTE, "<peticion>", '<peticion xmlns="urn:ejemplo:ficticio">'),
    "estructura.atributos": lambda: cambiar(PARTE, "<persona>", '<persona id="1">'),
    "estructura.documento-alias": lambda: cambiar(
        PARTE, "<numeroDocumento>00000001R</numeroDocumento>", "<documento>00000001R</documento>"
    ),
    "establecimiento.codigo-o-datos": lambda: cambiar(RESERVA, "<codigo>0000099999</codigo>", ""),
    # Valores
    "valor.vacio-obligatorio": lambda: cambiar(PARTE, "<nombre>Lucía</nombre>", "<nombre></nombre>"),
    "valor.vacio-opcional": lambda: cambiar(PARTE, "<nacionalidad>USA</nacionalidad>", "<nacionalidad/>"),
    "valor.longitud": lambda: cambiar(PARTE, "<nombre>Lucía</nombre>", f"<nombre>{'L' * 51}</nombre>"),
    "valor.fecha": lambda: cambiar(
        PARTE, "<fechaContrato>2026-10-20</fechaContrato>", "<fechaContrato>20/10/2026</fechaContrato>"
    ),
    "valor.fecha-hora": lambda: cambiar(PARTE, "2026-11-02T15:30:00", "2026-11-02T15:30"),
    "valor.numerico": lambda: cambiar(PARTE, "<numPersonas>2</numPersonas>", "<numPersonas>dos</numPersonas>"),
    "valor.numerico-entero": lambda: cambiar(
        PARTE, "<numHabitaciones>1</numHabitaciones>", "<numHabitaciones>0</numHabitaciones>"
    ),
    "valor.booleano": lambda: cambiar(
        PARTE, "<numHabitaciones>1</numHabitaciones>", "<numHabitaciones>1</numHabitaciones><internet>true</internet>"
    ),
    "valor.codigo": lambda: cambiar(PARTE, "<tipoPago>TARJT</tipoPago>", "<tipoPago>BIZUM</tipoPago>"),
    "valor.pais": lambda: cambiar(PARTE, "<nacionalidad>USA</nacionalidad>", "<nacionalidad>US</nacionalidad>"),
    "valor.municipio-ine": lambda: cambiar(
        PARTE, "<codigoMunicipio>28079</codigoMunicipio>", "<codigoMunicipio>2807</codigoMunicipio>"
    ),
    "valor.caducidad": lambda: cambiar(PARTE, "09/2028", "9/2028"),
    "valor.correo": lambda: cambiar(PARTE, "lucia@example.com", "lucia.example.com"),
    "valor.telefono": lambda: cambiar(
        PARTE, "<telefono>+34600000001</telefono>", "<telefono>por las tardes</telefono>"
    ),
    "valor.soporte": lambda: cambiar(PARTE, "ZZZ000001", "ZZZ-00001"),
    # Dirección
    "direccion.municipio-espana": lambda: quitar(PARTE, "codigoMunicipio"),
    "direccion.municipio-extranjero": lambda: quitar(PARTE, "nombreMunicipio"),
    "direccion.ine-fuera-espana": lambda: cambiar(
        PARTE,
        "<nombreMunicipio>Springfield</nombreMunicipio>",
        "<codigoMunicipio>28079</codigoMunicipio><nombreMunicipio>Springfield</nombreMunicipio>",
    ),
    "direccion.codigo-postal": lambda: cambiar(
        PARTE, "<codigoPostal>28001</codigoPostal>", "<codigoPostal>2800</codigoPostal>"
    ),
    "direccion.cp-provincia": lambda: cambiar(
        PARTE, "<codigoPostal>28001</codigoPostal>", "<codigoPostal>08001</codigoPostal>"
    ),
    # Documento de identidad
    "documento.nif-formato": lambda: cambiar(PARTE, "00000001R", "0000001R"),
    "documento.nie-formato": lambda: cambiar(RESERVA, "X0000003A", "X000003A"),
    "documento.letra": lambda: cambiar(PARTE, "00000001R", "00000001A"),
    "documento.nie-como-nif": lambda: cambiar(PARTE, "00000001R", "X0000003A"),
    "documento.nif-como-nie": lambda: cambiar(RESERVA, "X0000003A", "00000001R"),
    "documento.normalizable": lambda: cambiar(PARTE, "00000001R", "00000001r"),
    "documento.nif-sin-verificar": lambda: cambiar(PARTE, "00000001R", "K0000001Z"),
    "documento.tipo-no-corresponde": lambda: cambiar(PARTE, "ZZ0000001", "00000002W"),
    "documento.sin-tipo": lambda: quitar(RESERVA, "tipoDocumento"),
    "documento.sin-numero": lambda: quitar(RESERVA, "numeroDocumento"),
    # Persona
    "persona.apellido2-nif": lambda: en_lucia(PARTE, "\n        <apellido2>Ejemplo</apellido2>", ""),
    "persona.soporte-nif-nie": lambda: quitar(PARTE, "soporteDocumento"),
    "persona.documento-mayor": lambda: en_lucia(quitar(PARTE, "soporteDocumento"), DOC_LUCIA, ""),
    "persona.parentesco-menor": lambda: quitar(PARTE, "parentesco"),
    "persona.parentesco-varios-menores": lambda: cambiar(
        cambiar(PARTE, "<numPersonas>2</numPersonas>", "<numPersonas>3</numPersonas>"),
        "</persona>\n    </comunicacion>",
        f"</persona>\n      <persona>{MENOR}</persona>\n    </comunicacion>",
    ),
    "persona.parentesco-en-menor": lambda: cambiar(
        quitar(PARTE, "parentesco"),
        "<telefono>+34600000001</telefono>\n      </persona>",
        "<telefono>+34600000001</telefono>\n        <parentesco>HJ</parentesco>\n      </persona>",
    ),
    "persona.contacto": lambda: en_lucia(
        PARTE, "\n        <telefono>+34600000001</telefono>\n        <correo>lucia@example.com</correo>", ""
    ),
    "persona.nacimiento-posterior": lambda: cambiar(PARTE, "2016-07-20", "2027-01-01"),
    # Comunicación y contrato
    "comunicacion.sin-viajero": lambda: cambiar(PARTE, "<rol>VI</rol>", "<rol>TI</rol>", 2),
    "comunicacion.sin-titular": lambda: cambiar(RESERVA, "<rol>TI</rol>", "<rol>VI</rol>"),
    "comunicacion.varios-titulares": lambda: cambiar(RESERVA, "<rol>VI</rol>", "<rol>TI</rol>"),
    "contrato.salida-anterior": lambda: cambiar(PARTE, "2026-11-05T11:00:00", "2026-11-01T11:00:00"),
    "contrato.salida-igual": lambda: cambiar(PARTE, "2026-11-05T11:00:00", "2026-11-02T15:30:00"),
    "contrato.contrato-posterior": lambda: cambiar(PARTE, "<fechaContrato>2026-10-20", "<fechaContrato>2026-11-03"),
    "contrato.hora-cero-parte": lambda: cambiar(PARTE, "2026-11-02T15:30:00", "2026-11-02T00:00:00"),
    "contrato.num-personas": lambda: cambiar(PARTE, "<numPersonas>2</numPersonas>", "<numPersonas>1</numPersonas>"),
    "contrato.num-personas-faltan": lambda: cambiar(
        PARTE, "<numPersonas>2</numPersonas>", "<numPersonas>3</numPersonas>"
    ),
    "contrato.num-personas-reserva": lambda: cambiar(
        RESERVA, "<numPersonas>2</numPersonas>", "<numPersonas>1</numPersonas>"
    ),
    "solicitud.referencia-duplicada": lambda: cambiar(PARTE, "FICTICIO-0002", "FICTICIO-0001"),
}

_RE_MARCA_BASE = re.compile(r"<!-- FICTICIO: [^\n]*-->")


def marca(codigo: str) -> str:
    regla = REGLAS[codigo]
    return (
        f"FICTICIO: ejemplo inválido de la regla {codigo} ({regla.apartado}): {regla.descripcion_es}. "
        "Generado por scripts/generar_ejemplos.py; no son personas ni documentos reales."
    )


def contenido(codigo: str) -> bytes:
    if codigo == "fichero.vacio":
        return b""
    xml = MUTACIONES[codigo]()
    texto_marca = marca(codigo).replace("--", "-")
    if "@MARCA@" in xml:
        xml = xml.replace("@MARCA@", texto_marca)
    else:
        xml, n = _RE_MARCA_BASE.subn(f"<!-- {texto_marca} -->", xml, count=1)
        if n != 1:
            raise ValueError(f"{codigo}: no se encuentra el comentario FICTICIO de la línea 2")
    if codigo == "xml.codificacion":
        return xml.encode("iso-8859-1")
    return xml.encode("utf-8")


def ejemplos() -> dict[str, bytes]:
    codigos = ["fichero.vacio", *MUTACIONES]
    return {c: contenido(c) for c in codigos}


def main(argv: list[str]) -> int:
    comprobar = "--comprobar" in argv
    esperados = ejemplos()
    desconocidos = set(esperados) - set(REGLAS)
    if desconocidos:
        print(f"Ejemplos de reglas que no existen: {sorted(desconocidos)}")
        return 1
    actuales = {p.stem: p.read_bytes() for p in DESTINO.glob("*.xml")} if DESTINO.exists() else {}
    if comprobar:
        if actuales != esperados:
            distintos = sorted(
                set(actuales) ^ set(esperados) | {c for c in esperados if actuales.get(c) != esperados[c]}
            )
            print(f"Ejemplos desactualizados: {distintos}. Ejecute: uv run python scripts/generar_ejemplos.py")
            return 1
        return 0
    DESTINO.mkdir(parents=True, exist_ok=True)
    for sobrante in set(actuales) - set(esperados):
        (DESTINO / f"{sobrante}.xml").unlink()
    for codigo, datos in esperados.items():
        (DESTINO / f"{codigo}.xml").write_bytes(datos)
    print(f"{len(esperados)} ejemplos en {DESTINO.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
