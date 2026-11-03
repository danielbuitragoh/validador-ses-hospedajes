"""Validador no oficial de ficheros XML de alta masiva de SES.Hospedajes (partes de viajeros y reservas).

Uso básico::

    from validador_ses_hospedajes import validar

    informe = validar("partes.xml")
    if not informe.valido:
        for e in informe.errores:
            print(e.linea, e.ruta, e.mensaje())

La única fuente de verdad es el documento oficial «Alta masiva de comunicaciones – Hospedajes» v1.1.0 del Ministerio
del Interior. La validación final la hace siempre el portal SES.Hospedajes.
"""

from .modelo import Gravedad, Idioma, Incidencia, Informe, TipoComunicacion
from .parseo import Limites
from .reglas import REGLAS, Regla
from .validador import validar, validar_bytes, validar_fichero

__version__ = "0.1.0"

__all__ = [
    "REGLAS",
    "Gravedad",
    "Idioma",
    "Incidencia",
    "Informe",
    "Limites",
    "Regla",
    "TipoComunicacion",
    "__version__",
    "validar",
    "validar_bytes",
    "validar_fichero",
]
