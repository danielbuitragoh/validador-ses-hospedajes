"""Presentación de los informes: texto legible (español o inglés) y JSON para máquinas."""

import json
from collections.abc import Sequence
from dataclasses import dataclass

from . import __version__
from .modelo import NOMBRE_TIPO, Gravedad, Idioma, Informe
from .reglas import REGLAS

DOCUMENTO = "Alta masiva de comunicaciones – Hospedajes, v1.1.0 (Ministerio del Interior)"


@dataclass(frozen=True, slots=True)
class NoLeido:
    """Ruta que no se pudo leer (no existe, sin permisos…)."""

    fichero: str
    motivo: str


_T: dict[str, dict[Idioma, str]] = {
    "cabecera": {
        "es": "validador-ses-hospedajes {v} · herramienta NO oficial · fuente: «{doc}»",
        "en": "validador-ses-hospedajes {v} · NOT an official tool · source: '{doc}'",
    },
    "tipo": {"es": "Tipo: {tipo} · {n}", "en": "Type: {tipo} · {n}"},
    "sin_tipo": {"es": "Tipo: no determinado", "en": "Type: not determined"},
    "linea": {"es": "línea {n}", "en": "line {n}"},
    "sin_linea": {"es": "fichero", "en": "file"},
    "regla": {"es": "Regla {codigo} ({desc}) · {ap}", "en": "Rule {codigo} ({desc}) · {ap}"},
    "pendiente": {"es": " · pendiente {p}", "en": " · pending {p}"},
    "valido": {"es": "Resultado: VÁLIDO (sin errores)", "en": "Result: VALID (no errors)"},
    "no_valido": {"es": "Resultado: NO VÁLIDO", "en": "Result: NOT VALID"},
    "avisos_ocultos": {"es": " ({n} ocultos con --sin-avisos)", "en": " ({n} hidden by --sin-avisos)"},
    "resumen": {
        "es": "Resumen: {f} · {v} · {e} · {te} y {ta} en total.",
        "en": "Summary: {f} · {v} · {e} · {te} and {ta} in total.",
    },
    "no_leidos": {"es": "No se pudieron leer: {n}.", "en": "Could not be read: {n}."},
    "pie": {
        "es": "Aviso: esta herramienta no es oficial. La validación final la hace el portal SES.Hospedajes.",
        "en": "Note: this is not an official tool. The final validation is done by the SES.Hospedajes portal.",
    },
    "ERROR": {"es": "[ERROR]", "en": "[ERROR]"},
    "AVISO": {"es": "[AVISO]", "en": "[WARN] "},
}

_PLURALES: dict[str, dict[Idioma, tuple[str, str]]] = {
    "error": {"es": ("error", "errores"), "en": ("error", "errors")},
    "aviso": {"es": ("aviso", "avisos"), "en": ("warning", "warnings")},
    "fichero": {"es": ("fichero", "ficheros"), "en": ("file", "files")},
    "valido": {"es": ("válido", "válidos"), "en": ("valid", "valid")},
    "con_errores": {"es": ("con errores", "con errores"), "en": ("with errors", "with errors")},
    "comunicacion": {"es": ("comunicación", "comunicaciones"), "en": ("communication", "communications")},
}


def _t(clave: str, idioma: Idioma, **kw: object) -> str:
    return _T[clave][idioma].format(**kw)


def contar(n: int, palabra: str, idioma: Idioma) -> str:
    singular, plural = _PLURALES[palabra][idioma]
    return f"{n} {singular if n == 1 else plural}"


def texto(informes: Sequence[Informe], no_leidos: Sequence[NoLeido], idioma: Idioma = "es", avisos: bool = True) -> str:
    lineas = [_t("cabecera", idioma, v=__version__, doc=DOCUMENTO), ""]
    for inf in informes:
        lineas.append(inf.origen or "-")
        if inf.tipo is not None:
            n = contar(inf.comunicaciones, "comunicacion", idioma)
            lineas.append("  " + _t("tipo", idioma, tipo=NOMBRE_TIPO[inf.tipo][idioma], n=n))
        else:
            lineas.append("  " + _t("sin_tipo", idioma))
        for inc in inf.incidencias:
            if inc.gravedad is Gravedad.AVISO and not avisos:
                continue
            etiqueta = _t("ERROR" if inc.gravedad is Gravedad.ERROR else "AVISO", idioma)
            donde = _t("linea", idioma, n=inc.linea) if inc.linea else _t("sin_linea", idioma)
            regla = _t("regla", idioma, codigo=inc.codigo, desc=inc.regla(idioma), ap=inc.apartado)
            if inc.pendiente:
                regla += _t("pendiente", idioma, p=inc.pendiente)
            lineas.append(f"  {etiqueta} {donde} · {inc.ruta}")
            lineas.append(f"          {inc.mensaje(idioma)}")
            lineas.append(f"          {regla}")
        resultado = _t("valido" if inf.valido else "no_valido", idioma)
        detalle = (
            f"{resultado} · {contar(len(inf.errores), 'error', idioma)} · {contar(len(inf.avisos), 'aviso', idioma)}"
        )
        if not avisos and inf.avisos:
            detalle += _t("avisos_ocultos", idioma, n=len(inf.avisos))
        lineas.extend(["  " + detalle, ""])
    validos = sum(1 for i in informes if i.valido)
    lineas.append(
        _t(
            "resumen",
            idioma,
            f=contar(len(informes), "fichero", idioma),
            v=contar(validos, "valido", idioma),
            e=contar(len(informes) - validos, "con_errores", idioma),
            te=contar(sum(len(i.errores) for i in informes), "error", idioma),
            ta=contar(sum(len(i.avisos) for i in informes), "aviso", idioma),
        )
    )
    if no_leidos:
        lineas.append(_t("no_leidos", idioma, n=len(no_leidos)))
    lineas.append(_t("pie", idioma))
    return "\n".join(lineas) + "\n"


def como_json(informes: Sequence[Informe], no_leidos: Sequence[NoLeido], idioma: Idioma = "es") -> str:
    validos = sum(1 for i in informes if i.valido)
    datos = {
        "herramienta": "validador-ses-hospedajes",
        "version": __version__,
        "oficial": False,
        "documento": DOCUMENTO,
        "idioma": idioma,
        "ficheros": [i.a_dict(idioma) for i in informes],
        "no_leidos": [{"fichero": n.fichero, "motivo": n.motivo} for n in no_leidos],
        "resumen": {
            "ficheros": len(informes),
            "validos": validos,
            "con_errores": len(informes) - validos,
            "errores": sum(len(i.errores) for i in informes),
            "avisos": sum(len(i.avisos) for i in informes),
            "no_leidos": len(no_leidos),
        },
    }
    return json.dumps(datos, ensure_ascii=False, indent=2) + "\n"


def reglas_texto(idioma: Idioma = "es") -> str:
    cab = ("código", "gravedad", "apartado", "pendiente", "descripción")
    if idioma == "en":
        cab = ("code", "severity", "section", "pending", "description")
    filas = [cab]
    for r in REGLAS.values():
        gravedad = r.gravedad.value if idioma == "es" else ("error" if r.gravedad is Gravedad.ERROR else "warning")
        desc = r.descripcion_es if idioma == "es" else r.descripcion_en
        filas.append((r.codigo, gravedad, r.apartado, r.pendiente or "-", desc))
    anchos = [max(len(f[i]) for f in filas) for i in range(4)]
    return (
        "\n".join("  ".join(c.ljust(a) for c, a in zip(f[:4], anchos, strict=True)) + "  " + f[4] for f in filas) + "\n"
    )


def reglas_json(idioma: Idioma = "es") -> str:
    return (
        json.dumps(
            [
                {
                    "codigo": r.codigo,
                    "gravedad": r.gravedad.value,
                    "apartado": r.apartado,
                    "pendiente": r.pendiente,
                    "descripcion": r.descripcion_es if idioma == "es" else r.descripcion_en,
                }
                for r in REGLAS.values()
            ],
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
