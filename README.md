# validador-ses-hospedajes

[![CI](https://github.com/danielbuitragoh/validador-ses-hospedajes/actions/workflows/ci.yml/badge.svg)](https://github.com/danielbuitragoh/validador-ses-hospedajes/actions/workflows/ci.yml)

Valida los ficheros XML de **alta masiva de SES.Hospedajes** (partes de viajeros y reservas de hospedaje) **antes de
subirlos al portal**, venga el fichero de donde venga: la app [registro-viajeros](https://github.com/danielbuitragoh/registro-viajeros),
un programa de gestión hotelera como AM HOTEL o cualquier otro. Herramienta de línea de órdenes y librería de
Python 3.12+, sin red y sin dependencias más allá de `defusedxml`.

> **Aviso importante.** Esta herramienta **no es oficial** ni está relacionada con el Ministerio del Interior.
> No envía nada a ningún sitio. **La validación final la hace el portal SES.Hospedajes**: un fichero que pasa aquí
> puede ser rechazado allí (y el establecimiento sigue siendo el único responsable de comunicar a tiempo). Su única
> fuente de verdad es el documento oficial «Alta masiva de comunicaciones – Hospedajes» v1.1.0
> ([`docs/oficial/Instrucciones.pdf`](docs/oficial/Instrucciones.pdf)); lo que ese documento no deja claro **no se
> inventa**: se marca como pendiente y, como mucho, produce un aviso.

## Qué problema resuelve y para quién

Desde el RD 933/2021, alojamientos y viviendas de uso turístico comunican partes de viajeros y reservas a
SES.Hospedajes. Para hacerlo en bloque, el portal admite un fichero XML con un formato concreto. Cuando ese fichero
tiene un fallo (una letra de DNI mal, una fecha con otro formato, un menor sin adulto con parentesco, un código de
municipio que falta…), el portal lo dice **después de subirlo**, comunicación a comunicación, y hay que corregir a
mano dentro del portal.

`ses-validar` revisa el fichero **antes**, en su ordenador, y le dice **qué está mal, en qué línea, en qué elemento,
qué regla incumple y en qué apartado del documento oficial está esa regla**. Es para:

- **Dueños y personal de alojamientos** que exportan los partes desde su programa de gestión y quieren subirlos a la
  primera.
- **Desarrolladores** de programas de gestión, PMS o integraciones que generan estos XML y quieren comprobarlos en sus
  pruebas o en su CI (salida `--json`, códigos de salida, librería importable).
- **Gestorías y asesorías** que revisan ficheros de varios clientes (acepta carpetas enteras).

## Instalación

Requiere Python 3.12 o posterior. El paquete está **listo para PyPI pero aún no publicado**; mientras tanto, instálelo
desde GitHub:

```bash
uv tool install git+https://github.com/danielbuitragoh/validador-ses-hospedajes
```

o con `pipx`:

```bash
pipx install git+https://github.com/danielbuitragoh/validador-ses-hospedajes
```

Cuando se publique en PyPI bastará con `uv tool install validador-ses-hospedajes` (o `pipx install …`).

Para desarrollar:

```bash
git clone https://github.com/danielbuitragoh/validador-ses-hospedajes
cd validador-ses-hospedajes
uv sync
uv run pytest
```

## Uso

```bash
ses-validar partes.xml                     # un fichero
ses-validar enero.xml febrero.xml          # varios
ses-validar exportaciones/                 # una carpeta (busca .xml dentro, también en subcarpetas)
ses-validar --json partes.xml              # para máquinas
ses-validar --ingles partes.xml            # mensajes en inglés (también --english)
ses-validar --tipo reservas fichero.xml    # forzar el tipo si no se puede detectar
ses-validar --estricto partes.xml          # los avisos también hacen fallar
ses-validar --sin-avisos partes.xml        # ocultar avisos en la salida de texto
ses-validar --max-mb 20 grande.xml         # límite de tamaño (por defecto, 10 MB)
ses-validar --reglas                       # lista de reglas (con --json, en JSON)
```

**Códigos de salida:** `0` sin errores (puede haber avisos) · `1` hay errores (o avisos, con `--estricto`) ·
`2` uso incorrecto, fichero que no existe o carpeta sin `.xml`.

### Ejemplo de salida

Un parte con una letra de NIF equivocada, un municipio que falta y el campo `internet` con un valor que el
documento no define (datos ficticios):

```text
$ ses-validar partes-noviembre.xml reservas-diciembre.xml
validador-ses-hospedajes 0.1.0 · herramienta NO oficial · fuente: «Alta masiva de comunicaciones – Hospedajes, v1.1.0 (Ministerio del Interior)»

partes-noviembre.xml
  Tipo: parte de viajeros (§3) · 2 comunicaciones
  [AVISO] línea 15 · /peticion/solicitud/comunicacion[1]/contrato/internet
          «internet» vale «S». El documento no define el formato de los booleanos: compruébelo con la plantilla del portal.
          Regla valor.booleano (Formato del booleano «internet») · §3 · pendiente P3
  [ERROR] línea 30 · /peticion/solicitud/comunicacion[1]/persona[1]/numeroDocumento
          La letra de control del NIF no es correcta: debería ser «R».
          Regla documento.letra (Letra de control de NIF y NIE) · §3; §8.5
  [ERROR] línea 35 · /peticion/solicitud/comunicacion[1]/persona[1]/direccion/codigoMunicipio
          La dirección está en España (pais = ESP): «codigoMunicipio» es obligatorio.
          Regla direccion.municipio-espana (En España, «codigoMunicipio» obligatorio) · §7.1
  Resultado: NO VÁLIDO · 2 errores · 1 aviso

reservas-diciembre.xml
  Tipo: reserva de hospedaje (§4) · 2 comunicaciones
  Resultado: VÁLIDO (sin errores) · 0 errores · 0 avisos

Resumen: 2 ficheros · 1 válido · 1 con errores · 2 errores y 1 aviso en total.
Aviso: esta herramienta no es oficial. La validación final la hace el portal SES.Hospedajes.
```

Con `--json` (recortado):

```json
{
  "herramienta": "validador-ses-hospedajes",
  "version": "0.1.0",
  "oficial": false,
  "idioma": "es",
  "ficheros": [
    {
      "fichero": "partes-noviembre.xml",
      "tipo": "partes",
      "comunicaciones": 2,
      "valido": false,
      "errores": 2,
      "avisos": 1,
      "incidencias": [
        {
          "codigo": "documento.letra",
          "gravedad": "error",
          "ruta": "/peticion/solicitud/comunicacion[1]/persona[1]/numeroDocumento",
          "linea": 30,
          "apartado": "§3; §8.5",
          "pendiente": null,
          "mensaje": "La letra de control del NIF no es correcta: debería ser «R».",
          "regla": "Letra de control de NIF y NIE"
        }
      ]
    }
  ],
  "no_leidos": [],
  "resumen": { "ficheros": 1, "validos": 0, "con_errores": 1, "errores": 2, "avisos": 1, "no_leidos": 0 }
}
```

**Privacidad:** los mensajes nunca repiten nombres, números de documento, fechas de nacimiento ni otros datos
personales del fichero; solo códigos de las tablas oficiales, longitudes y posiciones. Así se pueden guardar o
compartir los informes (por ejemplo, en los registros de una CI) sin exponer datos de huéspedes.

### Como librería

```python
from validador_ses_hospedajes import Gravedad, validar

informe = validar("partes.xml")  # ruta (str o Path), bytes del fichero o el XML como texto
print(informe.tipo, informe.comunicaciones, informe.valido)
for inc in informe.incidencias:
    print(inc.gravedad, inc.linea, inc.ruta, inc.codigo, inc.apartado, inc.mensaje())  # mensaje("en") en inglés

informe = validar(contenido_bytes, tipo="reservas", origen="subida.xml")
datos = informe.a_dict()  # listo para json.dumps
```

`validar()` devuelve un `Informe` inmutable y tipado (`tipo`, `comunicaciones`, `incidencias`, `errores`, `avisos`,
`valido`). Cada `Incidencia` lleva `codigo`, `gravedad`, `ruta`, `linea`, `apartado`, `pendiente` y los textos en los
dos idiomas. Un `str` que empieza por `<` se trata como XML; cualquier otro, como ruta. También hay `validar_bytes()`
y `validar_fichero()`. El paquete incluye `py.typed` y pasa `mypy --strict`.

## Qué se valida

Todas las reglas salen de los apartados 2, 3, 4, 7 y 8 del documento oficial, incluidas sus **figuras** (que dan el
orden y la obligatoriedad de cada elemento). Mi lectura completa, campo por campo, está en
[`docs/oficial/NOTAS.md`](docs/oficial/NOTAS.md).

- **Seguridad del fichero:** XML bien formado, sin `DOCTYPE` ni entidades (protección contra XXE y «billion laughs»,
  con `defusedxml`), límites de tamaño, profundidad y número de elementos. Nunca se accede a la red.
- **Tipo de comunicación (§2):** detecta si es un parte de viajeros (§3) o una reserva de hospedaje (§4), y da error
  si un fichero **mezcla tipos**. Reconoce los de vehículos (§5 y §6) y dice que no los valida.
- **Estructura y orden (figuras 1, 2, 5 y 6):** raíz `peticion`, elementos desconocidos, fuera de orden, repetidos,
  obligatorios que faltan, texto suelto en bloques, y `establecimiento` con `codigo` **o** `datosEstablecimiento`.
- **Formatos:** longitudes `String(n)`, fechas `AAAA-MM-DD`, fecha y hora `AAAA-MM-DDThh:mm:ss`, numéricos, códigos de
  las tablas 8.3 a 8.7 (parentesco, sexo, tipo de documento, tipo de establecimiento, tipo de pago) y roles TI/VI,
  país ISO 3166-1 alfa-3, municipio INE de 5 dígitos, caducidad `MM/AAAA` y correo electrónico.
- **Obligatoriedades condicionales:** segundo apellido con NIF; número de soporte con NIF o NIE; tipo y número de
  documento para mayores de edad; parentesco en al menos un adulto si hay menores; al menos un teléfono o correo;
  `codigoMunicipio` en España y `nombreMunicipio` fuera; al menos un viajero (VI) en los partes y un titular (TI) en
  las reservas.
- **Documento de identidad:** letra de control de **DNI/NIF y NIE**, y que el número corresponda al tipo.
- **Coherencias:** salida posterior a la entrada; `numPersonas` frente a las personas incluidas; referencias de
  contrato repetidas; contrato posterior a la entrada; nacimiento posterior a la entrada.

### Tabla de reglas

**Error**: incumple algo que el documento establece; el portal probablemente lo rechazará. **Aviso**: el documento no
lo define con claridad (columna *Pendiente*, explicada en [`NOTAS.md`](docs/oficial/NOTAS.md)) o es una incoherencia
probable que el documento no menciona: revíselo. «—» en *Apartado* indica un límite de seguridad de esta herramienta.
Una prueba comprueba que esta tabla coincide con el catálogo del código (`ses-validar --reglas`).

| Regla | Gravedad | Apartado | Pendiente | Qué comprueba |
|---|---|---|---|---|
| `fichero.vacio` | Error | §2 | — | El fichero contiene un documento XML |
| `fichero.demasiado-grande` | Error | — | — | Tamaño máximo (límite de seguridad) |
| `xml.mal-formado` | Error | §2 | — | XML bien formado |
| `xml.dtd-o-entidades` | Error | — | — | Sin DOCTYPE ni entidades (protección XXE) |
| `xml.demasiado-profundo` | Error | — | — | Profundidad máxima (límite de seguridad) |
| `xml.demasiados-elementos` | Error | — | — | Número máximo de elementos (límite de seguridad) |
| `xml.codificacion` | Aviso | §2 | P21 | Codificación de caracteres |
| `estructura.raiz` | Error | §3 fig. 1; §4 fig. 2 | — | El elemento raíz es «peticion» |
| `estructura.tipo-indeterminado` | Error | §2 | — | Se puede saber el tipo de comunicación |
| `estructura.tipo-no-soportado` | Error | §5; §6 | — | Solo partes de viajeros y reservas de hospedaje |
| `estructura.tipos-mezclados` | Error | §2 | — | Un solo tipo de comunicación por fichero |
| `estructura.tipo-distinto` | Error | §2 | — | El fichero es del tipo pedido |
| `estructura.elemento-desconocido` | Error | §3 fig. 1; §4 fig. 2 | — | Solo elementos definidos en el documento |
| `estructura.orden` | Error | §3 fig. 1; §4 fig. 2 | — | Orden de los elementos según la figura |
| `estructura.duplicado` | Error | §3 fig. 1; §4 fig. 2 | — | Bloques y campos únicos no se repiten |
| `estructura.falta` | Error | §3; §4; §7 | — | Elementos obligatorios presentes |
| `estructura.texto-en-bloque` | Error | §3 fig. 1; §4 fig. 2 | — | Los bloques solo contienen elementos |
| `estructura.hijos-en-campo` | Error | §3 fig. 1; §4 fig. 2 | — | Los campos solo contienen texto |
| `estructura.espacio-nombres` | Aviso | §2 | P1 | Espacio de nombres |
| `estructura.atributos` | Aviso | §2 | P1 | Atributos |
| `estructura.documento-alias` | Aviso | §3 | P2 | «numeroDocumento» (figura 1) y no «documento» |
| `establecimiento.codigo-o-datos` | Error | §4 | — | Establecimiento: «codigo» o «datosEstablecimiento» |
| `valor.vacio-obligatorio` | Error | §3; §4; §7 | — | Campos obligatorios con valor |
| `valor.vacio-opcional` | Aviso | §3; §4; §7 | P18 | Campos opcionales vacíos |
| `valor.longitud` | Error | §3; §4; §7 | — | Longitud máxima String(n) |
| `valor.fecha` | Error | §3; §4; §7.2 | — | Fechas AAAA-MM-DD |
| `valor.fecha-hora` | Error | §3; §4 | — | Fecha y hora AAAA-MM-DDThh:mm:ss |
| `valor.numerico` | Error | §3; §4 | — | Campos numéricos |
| `valor.numerico-entero` | Aviso | §3; §4 | P19 | Numérico: entero mayor que 0 |
| `valor.booleano` | Aviso | §3; §4 | P3 | Formato del booleano «internet» |
| `valor.codigo` | Error | §8 | — | Códigos de las tablas oficiales |
| `valor.pais` | Error | §3; §4; §7.1 | — | País ISO 3166-1 alfa-3 |
| `valor.municipio-ine` | Error | §7.1 | — | Código de municipio INE de 5 dígitos |
| `valor.caducidad` | Error | §7.2 | — | Caducidad de tarjeta MM/AAAA |
| `valor.correo` | Error | §3; §4 | — | Correo electrónico con formato válido |
| `valor.telefono` | Aviso | §3; §4 | P9 | Formato del teléfono |
| `valor.soporte` | Aviso | §3 | P10 | Formato del número de soporte |
| `direccion.municipio-espana` | Error | §7.1 | — | En España, «codigoMunicipio» obligatorio |
| `direccion.municipio-extranjero` | Error | §7.1 | — | Fuera de España, «nombreMunicipio» obligatorio |
| `direccion.ine-fuera-espana` | Aviso | §7.1 | — | Código INE solo en España |
| `direccion.codigo-postal` | Aviso | §7.1 | P23 | Código postal español de 5 cifras |
| `direccion.cp-provincia` | Aviso | §7.1 | P23 | Código postal y municipio de la misma provincia |
| `documento.nif-formato` | Error | §3; §8.5 | — | NIF con formato válido |
| `documento.nie-formato` | Error | §3; §8.5 | — | NIE con formato válido |
| `documento.letra` | Error | §3; §8.5 | — | Letra de control de NIF y NIE |
| `documento.nie-como-nif` | Error | §3; §8.5 | — | El número corresponde al tipo (NIF) |
| `documento.nif-como-nie` | Error | §3; §8.5 | — | El número corresponde al tipo (NIE) |
| `documento.normalizable` | Aviso | §3; §4 | P25 | Número de documento sin separadores |
| `documento.nif-sin-verificar` | Aviso | §3; §8.5 | P24 | NIF K, L o M |
| `documento.tipo-no-corresponde` | Aviso | §3; §4 | P26 | El número corresponde al tipo (PAS, OTRO) |
| `documento.sin-tipo` | Error | §3; §4 | — | Número de documento con su tipo |
| `documento.sin-numero` | Aviso | §3; §4 | P27 | Tipo de documento con su número |
| `persona.apellido2-nif` | Error | §3 | — | Segundo apellido obligatorio con NIF |
| `persona.soporte-nif-nie` | Error | §3 | — | Número de soporte obligatorio con NIF o NIE |
| `persona.documento-mayor` | Error | §3 | P6 | Documento obligatorio para mayores de edad |
| `persona.parentesco-menor` | Error | §3 | P6 | Con menores, parentesco en al menos un adulto |
| `persona.parentesco-varios-menores` | Aviso | §3 | P7 | Parentesco con varios menores |
| `persona.parentesco-en-menor` | Aviso | §3 | P7 | Parentesco en la persona adulta |
| `persona.contacto` | Error | §3; §4 | — | Al menos un teléfono o correo |
| `persona.nacimiento-posterior` | Aviso | §3; §4 | P23 | Nacimiento anterior a la entrada |
| `comunicacion.sin-viajero` | Error | §3 | — | Al menos una persona con rol VI |
| `comunicacion.sin-titular` | Error | §4 | — | Una persona con rol TI (titular) |
| `comunicacion.varios-titulares` | Aviso | §4 | P8 | Un solo titular |
| `contrato.salida-anterior` | Error | §3; §4 | — | Salida posterior a la entrada |
| `contrato.salida-igual` | Aviso | §3; §4 | P23 | Salida distinta de la entrada |
| `contrato.contrato-posterior` | Aviso | §3; §4 | P23 | Contrato no posterior a la entrada |
| `contrato.hora-cero-parte` | Aviso | §3 | P20 | Hora real en los partes |
| `contrato.num-personas` | Error | §3 | P8 | No más personas que «numPersonas» |
| `contrato.num-personas-faltan` | Aviso | §3 | P28 | Una persona por cada alojado declarado |
| `contrato.num-personas-reserva` | Aviso | §4 | P8 | Viajeros (VI) no superan «numPersonas» |
| `solicitud.referencia-duplicada` | Aviso | §3; §4 | P22 | Referencias de contrato distintas |

Cada regla tiene un fichero de ejemplo inválido, ficticio y marcado como tal, en
[`tests/ejemplos/invalidos/`](tests/ejemplos/invalidos/) (salvo los dos límites de tamaño, que se prueban con límites
reducidos).

## Qué NO se valida (y por qué)

- **Que los códigos de municipio del INE existan.** El documento solo dice «INE, 5 dígitos» y no incluye la tabla
  (P4, P15): se comprueba el formato, no la existencia.
- **El espacio de nombres, los atributos y la declaración XML** de la plantilla real: el documento no incluye el XSD
  ni la plantilla descargable (P1). Se compara por nombre local y se avisa si hay espacio de nombres o atributos.
- **El formato del booleano `internet`** (P3), **del teléfono** (P9), **del número de soporte** y **de los
  pasaportes** (P10): no están definidos; como mucho, avisos.
- **Lo que solo sabe el portal:** que el código de establecimiento exista y sea suyo, duplicados con comunicaciones ya
  enviadas, plazos de comunicación (RD 933/2021), etc.
- **Alquiler y reserva de vehículos** (§5 y §6): fuera del alcance de un alojamiento.

Pendientes del documento que afectan a las reglas: **P1–P4, P6–P10, P15–P28** (ver la tabla completa en
[`NOTAS.md`](docs/oficial/NOTAS.md)). Los más relevantes:

| # | Lo que no dice el documento | Qué hace el validador |
|---|---|---|
| P1 | XSD, espacio de nombres, atributos | Compara por nombre local; aviso si hay espacio de nombres o atributos |
| P2 | La tabla del §3 dice `documento`; la figura 1, `numeroDocumento` | Exige `numeroDocumento`; si aparece `documento`, lo valida y avisa |
| P3 | Formato del booleano `internet` | Lo admite en su sitio, con aviso |
| P6 | Cuándo se es «mayor de edad» | 18 años cumplidos en la fecha de entrada |
| P7 | A qué menor se refiere el parentesco si hay varios | Aviso si hay varios menores |
| P8 | Si el titular que se aloja se repite como viajero y si cuenta en `numPersonas` | Se aceptan las dos lecturas |
| P18 | Si un elemento opcional puede ir vacío | Aviso (mejor omitirlo) |
| P20 | La hora `T00:00:00` como «desconocida» solo figura en reservas | Aviso si aparece en un parte |
| P28 | Si un parte debe incluir un bloque por cada alojado declarado | Aviso si hay menos personas que `numPersonas` |

## Relación con registro-viajeros

[registro-viajeros](https://github.com/danielbuitragoh/registro-viajeros) es una app libre y local para que un
alojamiento pequeño registre a sus huéspedes y **genere** estos ficheros. Este validador es su complemento
independiente: **comprueba** ficheros de cualquier origen. Comparten la misma fuente de verdad (el mismo PDF, con la
misma huella SHA-256) y la misma numeración de pendientes (P1–P17; los del validador siguen desde P18).

**Prueba cruzada:** [`scripts/registro_viajeros/generar.mjs`](scripts/registro_viajeros/generar.mjs) ejecuta con Node
el **código real** de registro-viajeros (sus validadores del modelo y su `construirXml`) sobre sus propios datos
ficticios de prueba y de demo, **sin modificar aquel repositorio**, y guarda los XML en
[`tests/ejemplos/registro-viajeros/`](tests/ejemplos/registro-viajeros/) con un manifiesto (commit de origen y huellas
SHA-256). Las pruebas exigen que este validador los acepte **sin errores**; en la CI, además, se regeneran en vivo
desde la última versión de registro-viajeros y se comparan byte a byte. Discrepancias encontradas y resueltas:

- La demo de registro-viajeros exporta un parte con `numPersonas` = 3 y un solo viajero (allí es un aviso,
  `viajeros_cuenta`). Como el documento no dice expresamente que deba haber un bloque por alojado, aquí también es un
  **aviso** (P28), no un error.
- registro-viajeros no emite `internet` (P3) y su validador lo rechazaría; este lo admite con aviso, porque el
  documento sí lo define como campo opcional.

```bash
REGISTRO_VIAJEROS=../registro-viajeros uv run pytest tests/test_registro_viajeros.py   # regenerar en vivo (Node >= 22.18)
```

## Desarrollo

```bash
uv sync
uv run pytest                 # pruebas (incluye un ejemplo por regla y la prueba cruzada)
uv run ruff check && uv run ruff format --check
uv run mypy                   # modo --strict
uv run python scripts/generar_ejemplos.py   # regenerar tests/ejemplos/invalidos/
uv build                      # sdist y wheel (el PDF oficial no se incluye en el paquete)
```

La CI ([`ci.yml`](.github/workflows/ci.yml)) ejecuta todo con Python 3.12 y 3.13, la prueba cruzada en vivo y una
comprobación del paquete. La publicación en PyPI ([`publicar.yml`](.github/workflows/publicar.yml)) se lanza al subir
una etiqueta `vX.Y.Z`, con *trusted publishing* (sin tokens); las instrucciones de la configuración inicial están en
el propio fichero. **Todavía no se ha publicado.**

Método: TDD con commits pequeños (`test:` primero, luego `feat:`). Estructura del código:

| Módulo | Qué hace |
|---|---|
| `parseo.py` | Parseo seguro con `defusedxml`, límites y número de línea de cada elemento |
| `esquema.py` | Esquema declarativo transcrito de las figuras y tablas (orden, tipos, longitudes) |
| `oficial.py`, `paises.py` | Tablas del §8 (copia literal) y lista ISO 3166-1 alfa-3 |
| `documentos.py` | Letra de control de DNI/NIF y NIE |
| `reglas.py` | Catálogo de reglas: código, gravedad, apartado, pendiente y textos en español e inglés |
| `validador.py` | Detección del tipo, estructura, formatos, condicionales y coherencias |
| `salida.py`, `cli.py` | Salida de texto y JSON; la orden `ses-validar` |

## Autoría

Idea, especificación, revisión y pruebas: Daniel Buitrago (@danielbuitragoh). Código generado con Claude Code bajo su dirección.

## Licencia

[MIT](LICENSE). El documento oficial de `docs/oficial/` es del Ministerio del Interior y se incluye solo como
referencia; no forma parte del paquete publicado.

## English summary

**validador-ses-hospedajes** checks the XML bulk-upload files for Spain's **SES.Hospedajes** system (traveller
reports, §3, and accommodation bookings, §4) **before you upload them to the portal**, whatever produced them
(the [registro-viajeros](https://github.com/danielbuitragoh/registro-viajeros) app, a hotel management system such as
AM HOTEL, or anything else). It reports each problem with its element path, line number, the rule broken and the
section of the official document (*Alta masiva de comunicaciones – Hospedajes* v1.1.0, Ministry of the Interior),
which is its single source of truth.

- **Not an official tool.** It sends nothing anywhere; **the portal does the final validation**.
- Command line: `ses-validar file.xml [more files or folders]`, `--json` for machines, `--ingles`/`--english` for
  English messages, exit code 0/1/2. Library: `validar(bytes | str | path) -> Informe`.
- 71 rules (45 errors, 26 warnings): structure and element order from the document's figures, mandatory and
  conditional fields, date formats, official code tables, DNI/NIE check letters, consistency checks. Anything the
  document leaves unclear is **never invented**: it is listed as pending (P1–P28 in
  [`docs/oficial/NOTAS.md`](docs/oficial/NOTAS.md)) and yields at most a warning.
- Safe by design: `defusedxml` (no DTDs or entities, no XXE), size/depth limits, no network access, and messages
  never echo personal data.
- Requires Python 3.12+. Install with `uv tool install git+https://github.com/danielbuitragoh/validador-ses-hospedajes`
  (ready for PyPI, not published yet). MIT licence.

Idea, specification, review and testing: Daniel Buitrago. Code generated with Claude Code under the author's direction.
