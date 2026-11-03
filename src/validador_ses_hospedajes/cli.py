"""Línea de órdenes: ``ses-validar fichero.xml [más ficheros o carpetas]``.

Códigos de salida: 0 sin errores · 1 hay errores (o avisos con --estricto) · 2 uso incorrecto o rutas ilegibles.
"""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from . import __version__
from .modelo import Idioma, Informe, TipoComunicacion
from .parseo import Limites
from .salida import NoLeido, como_json, reglas_json, reglas_texto, texto
from .validador import validar_fichero

SIN_ERRORES, CON_ERRORES, USO_INCORRECTO = 0, 1, 2


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ses-validar",
        description=(
            "Valida ficheros XML de alta masiva de SES.Hospedajes (partes de viajeros §3 y reservas de hospedaje §4) "
            "según el documento oficial «Alta masiva de comunicaciones – Hospedajes» v1.1.0, ANTES de subirlos al "
            "portal. Herramienta NO oficial: la validación final la hace el portal."
        ),
        epilog="Códigos de salida: 0 sin errores · 1 con errores · 2 uso incorrecto o fichero ilegible.",
    )
    p.add_argument(
        "rutas", nargs="*", metavar="RUTA", help="fichero .xml o carpeta (se buscan .xml dentro, recursivamente)"
    )
    p.add_argument("--json", action="store_true", help="salida JSON para máquinas")
    p.add_argument("--ingles", "--english", dest="ingles", action="store_true", help="mensajes en inglés")
    p.add_argument(
        "--tipo",
        choices=[t.value for t in TipoComunicacion],
        help="fuerza el tipo de comunicación en lugar de detectarlo",
    )
    p.add_argument("--max-mb", type=float, default=10.0, help="tamaño máximo por fichero en MB (por defecto, 10)")
    p.add_argument("--estricto", action="store_true", help="los avisos también hacen fallar (código de salida 1)")
    p.add_argument("--sin-avisos", action="store_true", help="no mostrar los avisos en la salida de texto")
    p.add_argument("--reglas", action="store_true", help="muestra las reglas que se comprueban y sale")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return p


def _expandir(rutas: Sequence[str]) -> tuple[list[Path], list[NoLeido]]:
    ficheros: list[Path] = []
    no_leidos: list[NoLeido] = []
    for r in rutas:
        ruta = Path(r)
        if ruta.is_dir():
            dentro = sorted(p for p in ruta.rglob("*") if p.is_file() and p.suffix.lower() == ".xml")
            if not dentro:
                no_leidos.append(NoLeido(str(ruta), "la carpeta no contiene ficheros .xml"))
            ficheros.extend(dentro)
        else:
            ficheros.append(ruta)
    return ficheros, no_leidos


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    idioma: Idioma = "en" if args.ingles else "es"
    if args.reglas:
        sys.stdout.write(reglas_json(idioma) if args.json else reglas_texto(idioma))
        return SIN_ERRORES
    if not args.rutas:
        _parser().print_usage(sys.stderr)
        sys.stderr.write("ses-validar: indique al menos un fichero o carpeta\n")
        return USO_INCORRECTO

    limites = Limites(max_bytes=max(1, int(args.max_mb * 1024 * 1024)))
    ficheros, no_leidos = _expandir(args.rutas)
    informes: list[Informe] = []
    for f in ficheros:
        try:
            informes.append(validar_fichero(f, tipo=args.tipo, limites=limites))
        except OSError as e:
            no_leidos.append(NoLeido(str(f), e.strerror or type(e).__name__))

    for n in no_leidos:
        sys.stderr.write(f"ses-validar: {n.fichero}: {n.motivo}\n")
    if args.json:
        sys.stdout.write(como_json(informes, no_leidos, idioma))
    else:
        sys.stdout.write(texto(informes, no_leidos, idioma, avisos=not args.sin_avisos))

    if no_leidos:
        return USO_INCORRECTO
    if any(not i.valido for i in informes) or (args.estricto and any(i.avisos for i in informes)):
        return CON_ERRORES
    return SIN_ERRORES


def ejecutar() -> None:  # pragma: no cover - punto de entrada
    for flujo in (sys.stdout, sys.stderr):
        reconfigurar = getattr(flujo, "reconfigure", None)
        if reconfigurar is not None:
            reconfigurar(errors="replace")
    sys.exit(main())
