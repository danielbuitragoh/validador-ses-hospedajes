"""Validación de ficheros de alta masiva (§3 partes de viajeros y §4 reservas de hospedaje).

Fuente única de verdad: docs/oficial/Instrucciones.pdf (v1.1.0). Lo que el documento no define con claridad nunca
produce un error, como mucho un aviso (ver ``reglas.py`` y docs/oficial/NOTAS.md).
"""

import os
import re
from collections import Counter
from collections.abc import Iterator
from datetime import date
from pathlib import Path
from typing import Final

from . import documentos
from .esquema import ESQUEMA_PARTES, ESQUEMA_RESERVAS, Bloque, Campo, Def, Tipo
from .modelo import NOMBRE_TIPO, Incidencia, Informe, TipoComunicacion
from .oficial import PAIS_ESPANA
from .paises import PAISES_ALFA3
from .parseo import ErrorParseo, Limites, Nodo, codificacion_declarada, parsear
from .reglas import REGLAS

Entrada = bytes | str | os.PathLike[str]

#: PENDIENTE-OFICIAL (P6): el documento no define «mayor de edad»; 18 años (mayoría de edad en España).
MAYORIA_DE_EDAD: Final = 18

# [0-9] y no \d: \d admite cifras Unicode (p. ej. «２０２６»), que el formato oficial no contempla.
_RE_FECHA: Final = re.compile(r"([0-9]{4})-([0-9]{2})-([0-9]{2})")
_RE_FECHA_HORA: Final = re.compile(r"([0-9]{4}-[0-9]{2}-[0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2})")
_RE_NUMERICO: Final = re.compile(r"[+-]?[0-9]+(?:[.,][0-9]+)?")
_RE_ENTERO: Final = re.compile(r"[0-9]+")
_RE_INE: Final = re.compile(r"[0-9]{5}")
_RE_CADUCIDAD: Final = re.compile(r"(0[1-9]|1[0-2])/[0-9]{4}")
# PENDIENTE-OFICIAL (P9): «formato de dirección de correo electrónico válido» sin más detalle: algo@dominio.ext.
_RE_CORREO: Final = re.compile(r"[^\s@]+@[^\s@]+\.[^\s@]+")
_RE_TELEFONO: Final = re.compile(r"[0-9+()\-.\s]+")
_RE_ALFANUMERICO: Final = re.compile(r"[A-Za-z0-9]+")
_RE_CP_ESPANA: Final = re.compile(r"[0-9]{5}")


def es_fecha(valor: str) -> bool:
    """AAAA-MM-DD y fecha real del calendario."""
    m = _RE_FECHA.fullmatch(valor)
    if not m:
        return False
    try:
        date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return False
    return True


def es_fecha_hora(valor: str) -> bool:
    """AAAA-MM-DDThh:mm:ss, sin zona horaria ni fracciones, y fecha y hora reales."""
    m = _RE_FECHA_HORA.fullmatch(valor)
    if not m or not es_fecha(m.group(1)):
        return False
    return int(m.group(2)) <= 23 and int(m.group(3)) <= 59 and int(m.group(4)) <= 59


# --------------------------------------------------------------------------------------------------------------------
# API pública
# --------------------------------------------------------------------------------------------------------------------


def validar(
    entrada: Entrada,
    *,
    tipo: TipoComunicacion | str | None = None,
    limites: Limites | None = None,
    origen: str | None = None,
) -> Informe:
    """Valida un fichero de alta masiva y devuelve un :class:`Informe`.

    ``entrada`` puede ser:

    - ``bytes``: el contenido del fichero, tal cual;
    - ``str`` que empieza por ``<`` (tras espacios): el contenido XML como texto;
    - cualquier otro ``str`` o un ``os.PathLike``: la ruta del fichero.

    ``tipo`` fuerza el tipo de comunicación (``"partes"`` o ``"reservas"``); si se omite, se detecta.
    Nunca accede a la red ni escribe nada.
    """
    limites = limites or Limites()
    tipo_pedido = TipoComunicacion(tipo) if tipo is not None else None
    if isinstance(entrada, bytes):
        return validar_bytes(entrada, tipo=tipo_pedido, limites=limites, origen=origen)
    if isinstance(entrada, str) and entrada.lstrip("﻿ \t\r\n").startswith("<"):
        return _validar_texto(entrada, tipo_pedido, limites, origen)
    return validar_fichero(entrada, tipo=tipo_pedido, limites=limites, origen=origen)


def validar_fichero(
    ruta: str | os.PathLike[str],
    *,
    tipo: TipoComunicacion | str | None = None,
    limites: Limites | None = None,
    origen: str | None = None,
) -> Informe:
    """Lee el fichero sin superar ``limites.max_bytes`` y lo valida. Lanza ``OSError`` si no se puede leer."""
    limites = limites or Limites()
    ruta = Path(ruta)
    origen = origen if origen is not None else str(ruta)
    tamano = ruta.stat().st_size
    if tamano > limites.max_bytes:
        return _informe_fallido(origen, "fichero.demasiado-grande", None, tamano=tamano, limite=limites.max_bytes)
    with ruta.open("rb") as f:
        datos = f.read(limites.max_bytes + 1)
    return validar_bytes(datos, tipo=tipo, limites=limites, origen=origen)


def validar_bytes(
    datos: bytes,
    *,
    tipo: TipoComunicacion | str | None = None,
    limites: Limites | None = None,
    origen: str | None = None,
) -> Informe:
    """Valida el contenido de un fichero (bytes tal cual se subirían al portal)."""
    return _validar_datos(datos, tipo, limites or Limites(), origen, codificacion_declarada(datos))


def _validar_datos(
    datos: bytes,
    tipo: TipoComunicacion | str | None,
    limites: Limites,
    origen: str | None,
    codificacion: str | None,
) -> Informe:
    tipo_pedido = TipoComunicacion(tipo) if tipo is not None else None
    try:
        raiz = parsear(datos, limites)
    except ErrorParseo as e:
        params: dict[str, str | int] = {"detalle": e.detalle, "limite": "", "tamano": len(datos)}
        if e.codigo == "fichero.demasiado-grande":
            params["limite"] = limites.max_bytes
        elif e.codigo == "xml.demasiado-profundo":
            params["limite"] = limites.max_profundidad
        elif e.codigo == "xml.demasiados-elementos":
            params["limite"] = limites.max_elementos
        return _informe_fallido(origen, e.codigo, e.linea, **params)
    v = _Validador(raiz, tipo_pedido)
    v.ejecutar(codificacion)
    return v.informe(origen)


def _validar_texto(texto: str, tipo: TipoComunicacion | str | None, limites: Limites, origen: str | None) -> Informe:
    """El texto ya está decodificado: se pasa a UTF-8 y, si la declaración XML dice otra codificación, se cambia
    a UTF-8 para que el parser no lo decodifique dos veces. El aviso se basa en la declaración original."""
    datos = texto.lstrip("\ufeff").encode("utf-8")
    declarada = codificacion_declarada(datos)
    if declarada and declarada.lower() not in ("utf-8", "utf8"):
        datos = datos.replace(declarada.encode("ascii"), b"UTF-8", 1)
    return _validar_datos(datos, tipo, limites, origen, declarada)


def _informe_fallido(origen: str | None, codigo: str, linea: int | None, **params: str | int) -> Informe:
    regla = REGLAS[codigo]
    inc = Incidencia(codigo, regla.gravedad, "/", linea, regla.apartado, regla.pendiente, params)
    return Informe(origen, None, 0, (inc,))


# --------------------------------------------------------------------------------------------------------------------
# Utilidades sobre el árbol
# --------------------------------------------------------------------------------------------------------------------


def _hijos(nodo: Nodo, nombre: str) -> list[Nodo]:
    return [h for h in nodo.hijos if h.nombre == nombre]


def _hijo(nodo: Nodo, *nombres: str) -> Nodo | None:
    for h in nodo.hijos:
        if h.nombre in nombres:
            return h
    return None


def _valor(nodo: Nodo | None, *nombres: str) -> str | None:
    """Texto (sin espacios a los lados) del primer hijo con alguno de esos nombres; ``None`` si falta o vacío."""
    if nodo is None:
        return None
    h = _hijo(nodo, *nombres)
    if h is None or h.hijos:
        return None
    t = h.texto.strip()
    return t or None


def _recorrer(nodo: Nodo) -> Iterator[Nodo]:
    yield nodo
    for h in nodo.hijos:
        yield from _recorrer(h)


# --------------------------------------------------------------------------------------------------------------------
# Validador
# --------------------------------------------------------------------------------------------------------------------


class _Validador:
    def __init__(self, raiz: Nodo, tipo_pedido: TipoComunicacion | None) -> None:
        self.raiz = raiz
        self.tipo_pedido = tipo_pedido
        self.tipo: TipoComunicacion | None = None
        self.incidencias: list[Incidencia] = []
        self.comunicaciones: list[Nodo] = []

    # -- infraestructura --------------------------------------------------------------------------------------------

    def add(self, codigo: str, ruta: str, linea: int | None, apartado: str | None = None, **params: str | int) -> None:
        regla = REGLAS[codigo]
        self.incidencias.append(
            Incidencia(codigo, regla.gravedad, ruta, linea, apartado or regla.apartado, regla.pendiente, params)
        )

    def informe(self, origen: str | None) -> Informe:
        ordenadas = sorted(self.incidencias, key=lambda i: i.linea or 0)
        return Informe(origen, self.tipo, len(self.comunicaciones), tuple(ordenadas))

    # -- flujo ------------------------------------------------------------------------------------------------------

    def ejecutar(self, codificacion: str | None) -> None:
        if codificacion and codificacion.lower().replace("_", "-") not in ("utf-8", "utf8"):
            self.add("xml.codificacion", "/", 1, codificacion=codificacion)
        if self.raiz.nombre != "peticion":
            self.add("estructura.raiz", f"/{self.raiz.nombre}", self.raiz.linea, elemento=self.raiz.nombre)
            return
        self._espacios_y_atributos()
        tipo = self._detectar_tipo()
        if tipo is None:
            return
        self.tipo = tipo
        esquema = ESQUEMA_PARTES if tipo is TipoComunicacion.PARTES else ESQUEMA_RESERVAS
        self._bloque(self.raiz, esquema, "/peticion")
        solicitud = _hijo(self.raiz, "solicitud")
        self.comunicaciones = _hijos(solicitud, "comunicacion") if solicitud else []
        for i, com in enumerate(self.comunicaciones, start=1):
            self._comunicacion(com, f"/peticion/solicitud/comunicacion[{i}]")

    def _espacios_y_atributos(self) -> None:
        espacio_avisado = atributos_avisados = False
        for nodo in _recorrer(self.raiz):
            if nodo.espacio and not espacio_avisado:
                self.add("estructura.espacio-nombres", f"/{nodo.nombre}", nodo.linea, espacio=nodo.espacio)
                espacio_avisado = True
            if nodo.atributos and not atributos_avisados:
                attrs = ", ".join(sorted(nodo.atributos))
                self.add("estructura.atributos", f"/{nodo.nombre}", nodo.linea, elemento=nodo.nombre, atributos=attrs)
                atributos_avisados = True

    def _detectar_tipo(self) -> TipoComunicacion | None:
        """§2: un solo tipo por fichero. Pistas: ``codigoEstablecimiento`` en ``solicitud`` (§3, figura 1),
        ``establecimiento`` en ``comunicacion`` (§4, figura 2) y ``vehiculo`` (§5 y §6, figuras 3 y 4)."""
        solicitud = _hijo(self.raiz, "solicitud")
        pistas: set[str] = set()
        if solicitud is not None:
            if _hijo(solicitud, "codigoEstablecimiento") is not None:
                pistas.add("partes")
            for com in _hijos(solicitud, "comunicacion"):
                if _hijo(com, "vehiculo") is not None:
                    pistas.add("vehiculos")
                elif _hijo(com, "establecimiento") is not None:
                    pistas.add("reservas")
        linea = solicitud.linea if solicitud is not None else self.raiz.linea
        nombres = {
            "partes": "partes de viajeros (§3)",
            "reservas": "reservas de hospedaje (§4)",
            "vehiculos": "vehículos (§5/§6)",
        }
        if len(pistas) > 1:
            tipos = ", ".join(nombres[p] for p in sorted(pistas))
            self.add("estructura.tipos-mezclados", "/peticion/solicitud", linea, tipos=tipos)
            return None
        if pistas == {"vehiculos"}:
            self.add("estructura.tipo-no-soportado", "/peticion/solicitud", linea)
            return None
        detectado = TipoComunicacion(pistas.pop()) if pistas else None
        if self.tipo_pedido is not None:
            if detectado is not None and detectado is not self.tipo_pedido:
                self.add(
                    "estructura.tipo-distinto",
                    "/peticion/solicitud",
                    linea,
                    pedido=NOMBRE_TIPO[self.tipo_pedido]["es"],
                    detectado=NOMBRE_TIPO[detectado]["es"],
                )
                return None
            return self.tipo_pedido
        if detectado is None:
            self.add("estructura.tipo-indeterminado", "/peticion/solicitud", linea)
        return detectado

    # -- estructura (figuras 1, 2, 5 y 6) ---------------------------------------------------------------------------

    @staticmethod
    def _buscar(defn: Bloque, nombre: str) -> tuple[int, Def | None, bool]:
        for i, d in enumerate(defn.hijos):
            if d.nombre == nombre:
                return i, d, False
            if isinstance(d, Campo) and nombre in d.alias:
                return i, d, True
        return -1, None, False

    def _bloque(self, nodo: Nodo, defn: Bloque, ruta: str) -> None:
        if nodo.texto.strip():
            self.add("estructura.texto-en-bloque", ruta, nodo.linea, defn.apartado, elemento=defn.nombre)
        ultimo = -1
        cuenta: Counter[str] = Counter()
        for h in nodo.hijos:
            i, d, por_alias = self._buscar(defn, h.nombre)
            if d is None:
                permitidos = ", ".join(x.nombre for x in defn.hijos)
                self.add(
                    "estructura.elemento-desconocido",
                    f"{ruta}/{h.nombre}",
                    h.linea,
                    defn.apartado,
                    elemento=h.nombre,
                    padre=defn.nombre,
                    permitidos=permitidos,
                )
                continue
            cuenta[d.nombre] += 1
            n = cuenta[d.nombre]
            repetible = isinstance(d, Bloque) and d.repetible
            sub = f"{ruta}/{h.nombre}[{n}]" if repetible else f"{ruta}/{h.nombre}"
            if por_alias:
                self.add("estructura.documento-alias", sub, h.linea, d.apartado)
            if not defn.eleccion and i < ultimo:
                despues = defn.hijos[ultimo].nombre
                self.add("estructura.orden", sub, h.linea, defn.apartado, elemento=h.nombre, despues=despues)
            ultimo = max(ultimo, i)
            if n > 1 and not repetible:
                self.add("estructura.duplicado", sub, h.linea, d.apartado, elemento=h.nombre)
                continue
            if isinstance(d, Bloque):
                self._bloque(h, d, sub)
            else:
                self._campo(h, d, sub)
        if defn.eleccion:
            presentes = sum(1 for d in defn.hijos if cuenta[d.nombre])
            if presentes != 1:
                self.add("establecimiento.codigo-o-datos", ruta, nodo.linea, defn.apartado, presentes=presentes)
            return
        for d in defn.hijos:
            if d.obligatorio and not cuenta[d.nombre]:
                self.add(
                    "estructura.falta",
                    f"{ruta}/{d.nombre}",
                    nodo.linea,
                    d.apartado,
                    elemento=d.nombre,
                    padre=defn.nombre,
                )

    def _campo(self, nodo: Nodo, defn: Campo, ruta: str) -> None:
        if nodo.hijos:
            self.add("estructura.hijos-en-campo", ruta, nodo.linea, defn.apartado, elemento=defn.nombre)
            return
        valor = nodo.texto.strip()
        if not valor:
            codigo = "valor.vacio-obligatorio" if defn.obligatorio else "valor.vacio-opcional"
            self.add(codigo, ruta, nodo.linea, defn.apartado, campo=defn.nombre)
            return
        self._valor(valor, nodo, defn, ruta)

    def _valor(self, valor: str, nodo: Nodo, defn: Campo, ruta: str) -> None:
        """Formato según el tipo de la tabla. Los mensajes no repiten valores personales: solo códigos."""
        ap, campo, linea, t = defn.apartado, defn.nombre, nodo.linea, defn.tipo
        if t is Tipo.CODIGO and defn.tabla is not None:
            if valor not in defn.tabla:
                apartado = f"{ap}; {defn.tabla_apartado}" if defn.tabla_apartado != ap else ap
                permitidos = ", ".join(defn.tabla)
                self.add("valor.codigo", ruta, linea, apartado, campo=campo, valor=valor[:20], permitidos=permitidos)
            return
        if defn.maximo is not None and len(valor) > defn.maximo and t is not Tipo.PAIS:
            self.add("valor.longitud", ruta, linea, ap, campo=campo, longitud=len(valor), max=defn.maximo)
        if t is Tipo.FECHA and not es_fecha(valor):
            self.add("valor.fecha", ruta, linea, ap, campo=campo)
        elif t is Tipo.FECHA_HORA and not es_fecha_hora(valor):
            self.add("valor.fecha-hora", ruta, linea, ap, campo=campo)
        elif t is Tipo.NUMERICO:
            if not _RE_NUMERICO.fullmatch(valor):
                self.add("valor.numerico", ruta, linea, ap, campo=campo)
            elif not _RE_ENTERO.fullmatch(valor) or int(valor) == 0:
                self.add("valor.numerico-entero", ruta, linea, ap, campo=campo, valor=valor)
        elif t is Tipo.BOOLEANO:
            # PENDIENTE-OFICIAL (P3): el documento no define el formato del Booleano.
            self.add("valor.booleano", ruta, linea, ap, campo=campo, valor=valor[:20])
        elif t is Tipo.PAIS and valor not in PAISES_ALFA3:
            self.add("valor.pais", ruta, linea, ap, valor=valor[:20])
        elif t is Tipo.INE and not _RE_INE.fullmatch(valor):
            # PENDIENTE-OFICIAL (P4, P15): sin tabla del INE; solo el formato de 5 dígitos.
            self.add("valor.municipio-ine", ruta, linea, ap)
        elif t is Tipo.CADUCIDAD and not _RE_CADUCIDAD.fullmatch(valor):
            self.add("valor.caducidad", ruta, linea, ap)
        elif t is Tipo.CORREO and not _RE_CORREO.fullmatch(valor):
            self.add("valor.correo", ruta, linea, ap, campo=campo)
        elif t is Tipo.TELEFONO and not _RE_TELEFONO.fullmatch(valor):
            # PENDIENTE-OFICIAL (P9): formato de teléfono no definido.
            self.add("valor.telefono", ruta, linea, ap, campo=campo)
        elif t is Tipo.SOPORTE and not _RE_ALFANUMERICO.fullmatch(valor):
            # PENDIENTE-OFICIAL (P10): formato del soporte no definido.
            self.add("valor.soporte", ruta, linea, ap)

    # -- reglas por comunicación ------------------------------------------------------------------------------------

    def _comunicacion(self, com: Nodo, base: str) -> None:
        partes = self.tipo is TipoComunicacion.PARTES
        ap = "§3" if partes else "§4"
        contrato = _hijo(com, "contrato")
        entrada = _valor(contrato, "fechaEntrada")
        fecha_ref = date.fromisoformat(entrada[:10]) if entrada and es_fecha_hora(entrada) else None

        for ruta, direccion in self._direcciones(com, base):
            self._direccion(direccion, ruta)

        personas = _hijos(com, "persona")
        menores = 0
        adultos_con_parentesco = 0
        for pi, persona in enumerate(personas, start=1):
            ruta = f"{base}/persona[{pi}]"
            self._contacto(persona, ruta, ap)
            adulto = self._es_adulto(persona, fecha_ref)
            self._documento(persona, ruta, ap, adulto)
            if partes:
                tiene_parentesco = _valor(persona, "parentesco") is not None
                if adulto is False:
                    menores += 1
                    if tiene_parentesco:
                        nodo = _hijo(persona, "parentesco")
                        linea = nodo.linea if nodo else persona.linea
                        self.add("persona.parentesco-en-menor", f"{ruta}/parentesco", linea, ap)
                elif adulto and tiene_parentesco:
                    adultos_con_parentesco += 1

        if partes and menores:
            # §3 (aclaración v1.1.0): «al menos una de las personas mayores de edad ha de tener informada su relación
            # de parentesco con esta persona menor de edad».
            if not adultos_con_parentesco:
                self.add("persona.parentesco-menor", base, com.linea, ap, menores=menores)
            if menores > 1:
                # PENDIENTE-OFICIAL (P7): un solo campo por persona, sin indicar a qué menor se refiere.
                self.add("persona.parentesco-varios-menores", base, com.linea, ap, menores=menores)
        if personas:
            self._roles(personas, base, com.linea, partes)

    def _roles(self, personas: list[Nodo], base: str, linea: int, partes: bool) -> None:
        roles = [_valor(p, "rol") for p in personas]
        if partes:
            # §3: «Será obligatorio indicar al menos un bloque de este tipo con rol VI – viajero».
            if "VI" not in roles:
                self.add("comunicacion.sin-viajero", f"{base}/persona", linea, "§3")
            return
        # §4: «Se deberá incluir un bloque de este tipo con la información del titular del contrato».
        titulares = roles.count("TI")
        if titulares == 0:
            self.add("comunicacion.sin-titular", f"{base}/persona", linea, "§4")
        elif titulares > 1:
            # PENDIENTE-OFICIAL (P8).
            self.add("comunicacion.varios-titulares", f"{base}/persona", linea, "§4", num=titulares)

    def _contacto(self, persona: Nodo, ruta: str, ap: str) -> None:
        """§3/§4: «Obligatorio incluir una de estas tres etiquetas: telefono, telefono2 o correo»."""
        if not any(_valor(persona, n) for n in ("telefono", "telefono2", "correo")):
            self.add("persona.contacto", ruta, persona.linea, ap)

    def _es_adulto(self, persona: Nodo, fecha_ref: date | None) -> bool | None:
        """PENDIENTE-OFICIAL (P6): «mayor de edad» = 18 años cumplidos en la fecha de entrada.
        ``None`` si no se puede calcular."""
        nacimiento = _valor(persona, "fechaNacimiento")
        if fecha_ref is None or nacimiento is None or not es_fecha(nacimiento):
            return None
        n = date.fromisoformat(nacimiento)
        if n > fecha_ref:
            return None
        edad = fecha_ref.year - n.year - ((fecha_ref.month, fecha_ref.day) < (n.month, n.day))
        return edad >= MAYORIA_DE_EDAD

    @staticmethod
    def _direcciones(com: Nodo, base: str) -> list[tuple[str, Nodo]]:
        out: list[tuple[str, Nodo]] = []
        datos = _hijo(_hijo(com, "establecimiento") or com, "datosEstablecimiento")
        if datos is not None and (d := _hijo(datos, "direccion")) is not None:
            out.append((f"{base}/establecimiento/datosEstablecimiento/direccion", d))
        for pi, persona in enumerate(_hijos(com, "persona"), start=1):
            if (d := _hijo(persona, "direccion")) is not None:
                out.append((f"{base}/persona[{pi}]/direccion", d))
        return out

    def _direccion(self, d: Nodo, ruta: str) -> None:
        """§7.1, bloque direccion."""
        pais = _valor(d, "pais")
        cp = _valor(d, "codigoPostal")
        ine = _valor(d, "codigoMunicipio")
        nodo_cp = _hijo(d, "codigoPostal")
        if pais == PAIS_ESPANA and not ine:
            self.add("direccion.municipio-espana", f"{ruta}/codigoMunicipio", d.linea)
        elif pais and pais != PAIS_ESPANA:
            if not _valor(d, "nombreMunicipio"):
                self.add("direccion.municipio-extranjero", f"{ruta}/nombreMunicipio", d.linea)
            if ine:
                nodo_ine = _hijo(d, "codigoMunicipio")
                linea = nodo_ine.linea if nodo_ine else d.linea
                self.add("direccion.ine-fuera-espana", f"{ruta}/codigoMunicipio", linea)
        if pais == PAIS_ESPANA and cp and nodo_cp is not None:
            # PENDIENTE-OFICIAL (P23): el documento solo dice String(20); en España el código postal tiene 5 cifras
            # y sus dos primeras son las de la provincia, como en el código del INE.
            if not _RE_CP_ESPANA.fullmatch(cp):
                self.add("direccion.codigo-postal", f"{ruta}/codigoPostal", nodo_cp.linea)
            elif ine and _RE_INE.fullmatch(ine) and cp[:2] != ine[:2]:
                self.add("direccion.cp-provincia", f"{ruta}/codigoPostal", nodo_cp.linea, cp=cp[:2], ine=ine[:2])

    def _documento(self, persona: Nodo, ruta: str, ap: str, adulto: bool | None) -> None:
        """Documento de identidad: §3 (condicionales) y §3/§4 (el número «deberá corresponder al tipo de documento …
        y tener un formato válido en el caso de NIF o NIE»)."""
        partes = self.tipo is TipoComunicacion.PARTES
        nombres = ("numeroDocumento", "documento") if partes else ("numeroDocumento",)
        tipo_doc = _valor(persona, "tipoDocumento")
        numero = _valor(persona, *nombres)
        nodo_num = _hijo(persona, *nombres)
        ruta_num = f"{ruta}/{nodo_num.nombre if nodo_num else 'numeroDocumento'}"
        linea_num = nodo_num.linea if nodo_num else persona.linea

        if partes:
            if tipo_doc == "NIF" and _valor(persona, "apellido2") is None:
                nodo = _hijo(persona, "apellido2")
                self.add("persona.apellido2-nif", f"{ruta}/apellido2", (nodo or persona).linea, ap)
            if tipo_doc in ("NIF", "NIE") and _valor(persona, "soporteDocumento") is None:
                nodo = _hijo(persona, "soporteDocumento")
                self.add(
                    "persona.soporte-nif-nie", f"{ruta}/soporteDocumento", (nodo or persona).linea, ap, tipo=tipo_doc
                )
            if adulto and (tipo_doc is None or numero is None):
                falta = "tipoDocumento" if tipo_doc is None else nodo_num.nombre if nodo_num else "numeroDocumento"
                self.add("persona.documento-mayor", f"{ruta}/{falta}", persona.linea, ap)
                return

        if numero is not None and tipo_doc is None:
            self.add("documento.sin-tipo", ruta_num, linea_num, ap)
            return
        if tipo_doc is not None and numero is None:
            nodo = _hijo(persona, "tipoDocumento")
            self.add("documento.sin-numero", f"{ruta}/tipoDocumento", (nodo or persona).linea, ap)
            return
        if tipo_doc is None or numero is None:
            return
        apd = f"{ap}; §8.5"
        if tipo_doc in ("PAS", "OTRO"):
            # PENDIENTE-OFICIAL (P26): solo se puede comprobar que no sea, en realidad, un DNI o NIE.
            if documentos.parece_dni_o_nie_valido(numero):
                self.add("documento.tipo-no-corresponde", ruta_num, linea_num, ap, tipo=tipo_doc)
            return
        if tipo_doc == "NIF":
            r = documentos.validar_nif(numero)
        elif tipo_doc == "NIE":
            r = documentos.validar_nie(numero)
        else:
            return  # código fuera de la tabla 8.5: ya es un error de valor
        if r.valido:
            if r.normalizable:
                self.add("documento.normalizable", ruta_num, linea_num, ap)  # P25
            if r.sin_verificar:
                self.add("documento.nif-sin-verificar", ruta_num, linea_num, apd)  # P24
            return
        if r.motivo is documentos.Motivo.LETRA:
            self.add("documento.letra", ruta_num, linea_num, apd, tipo=tipo_doc, esperada=r.esperada or "")
        elif r.motivo is documentos.Motivo.PARECE_NIE:
            self.add("documento.nie-como-nif", ruta_num, linea_num, apd)
        elif r.motivo is documentos.Motivo.PARECE_DNI:
            self.add("documento.nif-como-nie", ruta_num, linea_num, apd)
        else:
            codigo = "documento.nif-formato" if tipo_doc == "NIF" else "documento.nie-formato"
            self.add(codigo, ruta_num, linea_num, apd)
