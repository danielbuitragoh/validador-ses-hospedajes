"""Catálogo de reglas: código estable, gravedad, apartado del documento oficial y textos en español e inglés.

Cada incidencia del informe apunta a una de estas reglas. Las de gravedad AVISO corresponden a lo que el documento no
define con claridad (columna ``pendiente``, ver docs/oficial/NOTAS.md) o a incoherencias probables que el documento no
menciona. «—» en el apartado indica una regla de seguridad de esta herramienta, no del documento.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from .modelo import Gravedad

E = Gravedad.ERROR
A = Gravedad.AVISO


@dataclass(frozen=True, slots=True)
class Regla:
    codigo: str
    gravedad: Gravedad
    apartado: str
    descripcion_es: str
    descripcion_en: str
    mensaje_es: str
    mensaje_en: str
    pendiente: str | None = None


# fmt: off
_LISTA: Final[tuple[Regla, ...]] = (
    # --- Fichero y seguridad -------------------------------------------------------------------------------------
    Regla(
        "fichero.vacio", E, "§2",
        "El fichero contiene un documento XML", "The file contains an XML document",
        "El fichero está vacío.", "The file is empty.",
    ),
    Regla(
        "fichero.demasiado-grande", E, "—",
        "Tamaño máximo (límite de seguridad)", "Maximum size (safety limit)",
        "El fichero ocupa {tamano} bytes y supera el límite de {limite} bytes (límite de seguridad de esta "
        "herramienta, ajustable con --max-mb).",
        "The file is {tamano} bytes, over the {limite}-byte limit (a safety limit of this tool; see --max-mb).",
    ),
    Regla(
        "xml.mal-formado", E, "§2",
        "XML bien formado", "Well-formed XML",
        "El fichero no es XML bien formado: {detalle}.", "The file is not well-formed XML: {detalle}.",
    ),
    Regla(
        "xml.dtd-o-entidades", E, "—",
        "Sin DOCTYPE ni entidades (protección XXE)", "No DOCTYPE or entities (XXE protection)",
        "El fichero contiene una declaración DOCTYPE o entidades XML. Se rechaza por seguridad (XXE, «billion "
        "laughs»): la plantilla oficial no las usa.",
        "The file contains a DOCTYPE declaration or XML entities. It is rejected for safety (XXE, billion laughs): "
        "the official template does not use them.",
    ),
    Regla(
        "xml.demasiado-profundo", E, "—",
        "Profundidad máxima (límite de seguridad)", "Maximum depth (safety limit)",
        "El XML anida más de {limite} niveles (límite de seguridad).",
        "The XML is nested more than {limite} levels deep (safety limit).",
    ),
    Regla(
        "xml.demasiados-elementos", E, "—",
        "Número máximo de elementos (límite de seguridad)", "Maximum number of elements (safety limit)",
        "El XML tiene más de {limite} elementos (límite de seguridad).",
        "The XML has more than {limite} elements (safety limit).",
    ),
    Regla(
        "xml.codificacion", A, "§2",
        "Codificación de caracteres", "Character encoding",
        "El fichero declara la codificación «{codificacion}». El documento no fija ninguna; lo habitual es UTF-8.",
        "The file declares the encoding '{codificacion}'. The document does not set one; UTF-8 is the usual choice.",
        "P21",
    ),
    # --- Estructura ----------------------------------------------------------------------------------------------
    Regla(
        "estructura.raiz", E, "§3 fig. 1; §4 fig. 2",
        "El elemento raíz es «peticion»", "The root element is 'peticion'",
        "El elemento raíz es «{elemento}» y debe ser «peticion».",
        "The root element is '{elemento}' and must be 'peticion'.",
    ),
    Regla(
        "estructura.tipo-indeterminado", E, "§2",
        "Se puede saber el tipo de comunicación", "The communication type can be determined",
        "No se puede saber si el fichero es de partes de viajeros (§3) o de reservas de hospedaje (§4): no hay "
        "«codigoEstablecimiento» en «solicitud» ni «establecimiento» en ninguna «comunicacion». Indíquelo con "
        "--tipo partes o --tipo reservas.",
        "Cannot tell whether the file holds traveller reports (§3) or accommodation bookings (§4): there is no "
        "'codigoEstablecimiento' in 'solicitud' and no 'establecimiento' in any 'comunicacion'. Use --tipo.",
    ),
    Regla(
        "estructura.tipo-no-soportado", E, "§5; §6",
        "Solo partes de viajeros y reservas de hospedaje", "Only traveller reports and accommodation bookings",
        "El fichero parece de alquiler o de reserva de vehículos (§5/§6: lleva «vehiculo»). Esta herramienta solo "
        "valida partes de viajeros (§3) y reservas de hospedaje (§4).",
        "The file looks like a vehicle rental or booking (§5/§6: it has 'vehiculo'). This tool only validates "
        "traveller reports (§3) and accommodation bookings (§4).",
    ),
    Regla(
        "estructura.tipos-mezclados", E, "§2",
        "Un solo tipo de comunicación por fichero", "One communication type per file",
        "El fichero mezcla tipos de comunicación ({tipos}). Todas las comunicaciones de un fichero deben ser del "
        "mismo tipo: sepárelas en ficheros distintos.",
        "The file mixes communication types ({tipos}). All communications in a file must be of the same type: "
        "split them into separate files.",
    ),
    Regla(
        "estructura.tipo-distinto", E, "§2",
        "El fichero es del tipo pedido", "The file is of the requested type",
        "Se pidió validar como «{pedido}», pero el fichero tiene forma de «{detectado}».",
        "Validation was requested as '{pedido}', but the file looks like '{detectado}'.",
    ),
    Regla(
        "estructura.elemento-desconocido", E, "§3 fig. 1; §4 fig. 2",
        "Solo elementos definidos en el documento", "Only elements defined in the document",
        "«{elemento}» no es un elemento admitido dentro de «{padre}». Admitidos, en este orden: {permitidos}.",
        "'{elemento}' is not allowed inside '{padre}'. Allowed, in this order: {permitidos}.",
    ),
    Regla(
        "estructura.orden", E, "§3 fig. 1; §4 fig. 2",
        "Orden de los elementos según la figura", "Element order as in the figure",
        "«{elemento}» está fuera de orden: según la figura del documento debe ir antes de «{despues}».",
        "'{elemento}' is out of order: according to the document's figure it must come before '{despues}'.",
    ),
    Regla(
        "estructura.duplicado", E, "§3 fig. 1; §4 fig. 2",
        "Bloques y campos únicos no se repiten", "Single blocks and fields are not repeated",
        "«{elemento}» aparece más de una vez y es único.",
        "'{elemento}' appears more than once but must be unique.",
    ),
    Regla(
        "estructura.falta", E, "§3; §4; §7",
        "Elementos obligatorios presentes", "Mandatory elements present",
        "Falta el elemento obligatorio «{elemento}» dentro de «{padre}».",
        "The mandatory element '{elemento}' is missing inside '{padre}'.",
    ),
    Regla(
        "estructura.texto-en-bloque", E, "§3 fig. 1; §4 fig. 2",
        "Los bloques solo contienen elementos", "Blocks only contain elements",
        "«{elemento}» es un bloque y no puede contener texto suelto.",
        "'{elemento}' is a block and cannot contain loose text.",
    ),
    Regla(
        "estructura.hijos-en-campo", E, "§3 fig. 1; §4 fig. 2",
        "Los campos solo contienen texto", "Fields only contain text",
        "«{elemento}» es un campo de valor y no puede contener otros elementos.",
        "'{elemento}' is a value field and cannot contain other elements.",
    ),
    Regla(
        "estructura.espacio-nombres", A, "§2",
        "Espacio de nombres", "XML namespace",
        "Los elementos usan el espacio de nombres «{espacio}». El documento no define ninguno: compruébelo con la "
        "plantilla del portal.",
        "Elements use the namespace '{espacio}'. The document does not define any: check the portal's template.",
        "P1",
    ),
    Regla(
        "estructura.atributos", A, "§2",
        "Atributos", "Attributes",
        "«{elemento}» lleva atributos ({atributos}). El documento no define atributos.",
        "'{elemento}' has attributes ({atributos}). The document does not define attributes.",
        "P1",
    ),
    Regla(
        "estructura.documento-alias", A, "§3",
        "«numeroDocumento» (figura 1) y no «documento»", "'numeroDocumento' (figure 1), not 'documento'",
        "Se usa «documento»: la tabla del §3 lo llama así, pero la figura 1 y el §4 lo llaman «numeroDocumento». "
        "Use «numeroDocumento» salvo que la plantilla del portal diga otra cosa.",
        "'documento' is used: the §3 table calls it that, but figure 1 and §4 call it 'numeroDocumento'. "
        "Use 'numeroDocumento' unless the portal's template says otherwise.",
        "P2",
    ),
    Regla(
        "establecimiento.codigo-o-datos", E, "§4",
        "Establecimiento: «codigo» o «datosEstablecimiento»", "Establishment: 'codigo' or 'datosEstablecimiento'",
        "«establecimiento» debe llevar «codigo» o «datosEstablecimiento»: uno de los dos y solo uno (hay {presentes}).",
        "'establecimiento' must contain 'codigo' or 'datosEstablecimiento': exactly one of them ({presentes} found).",
    ),
    # --- Valores -------------------------------------------------------------------------------------------------
    Regla(
        "valor.vacio-obligatorio", E, "§3; §4; §7",
        "Campos obligatorios con valor", "Mandatory fields have a value",
        "«{campo}» es obligatorio y está vacío.", "'{campo}' is mandatory and empty.",
    ),
    Regla(
        "valor.vacio-opcional", A, "§3; §4; §7",
        "Campos opcionales vacíos", "Empty optional fields",
        "«{campo}» está vacío. Es opcional: mejor omitir el elemento.",
        "'{campo}' is empty. It is optional: better to leave the element out.",
        "P18",
    ),
    Regla(
        "valor.longitud", E, "§3; §4; §7",
        "Longitud máxima String(n)", "Maximum length String(n)",
        "«{campo}» tiene {longitud} caracteres y el máximo es {max} (String({max})).",
        "'{campo}' has {longitud} characters and the maximum is {max} (String({max})).",
    ),
    Regla(
        "valor.fecha", E, "§3; §4; §7.2",
        "Fechas AAAA-MM-DD", "Dates YYYY-MM-DD",
        "«{campo}» no es una fecha válida con formato AAAA-MM-DD.",
        "'{campo}' is not a valid date in YYYY-MM-DD format.",
    ),
    Regla(
        "valor.fecha-hora", E, "§3; §4",
        "Fecha y hora AAAA-MM-DDThh:mm:ss", "Date and time YYYY-MM-DDThh:mm:ss",
        "«{campo}» no es una fecha y hora válidas con formato AAAA-MM-DDThh:mm:ss.",
        "'{campo}' is not a valid date and time in YYYY-MM-DDThh:mm:ss format.",
    ),
    Regla(
        "valor.numerico", E, "§3; §4",
        "Campos numéricos", "Numeric fields",
        "«{campo}» debe ser numérico.", "'{campo}' must be numeric.",
    ),
    Regla(
        "valor.numerico-entero", A, "§3; §4",
        "Numérico: entero mayor que 0", "Numeric: integer greater than 0",
        "«{campo}» vale «{valor}». El documento solo dice «Numérico»; se espera un número entero mayor que 0.",
        "'{campo}' is '{valor}'. The document only says 'Numeric'; a whole number greater than 0 is expected.",
        "P19",
    ),
    Regla(
        "valor.booleano", A, "§3; §4",
        "Formato del booleano «internet»", "Format of the 'internet' boolean",
        "«{campo}» vale «{valor}». El documento no define el formato de los booleanos: compruébelo con la "
        "plantilla del portal.",
        "'{campo}' is '{valor}'. The document does not define the boolean format: check the portal's template.",
        "P3",
    ),
    Regla(
        "valor.codigo", E, "§8",
        "Códigos de las tablas oficiales", "Codes from the official tables",
        "«{valor}» no es un código válido para «{campo}». Códigos de la tabla: {permitidos}.",
        "'{valor}' is not a valid code for '{campo}'. Codes in the table: {permitidos}.",
    ),
    Regla(
        "valor.pais", E, "§3; §4; §7.1",
        "País ISO 3166-1 alfa-3", "Country ISO 3166-1 alpha-3",
        "«{valor}» no es un código de país ISO 3166-1 alfa-3 (p. ej. ESP, FRA, DEU).",
        "'{valor}' is not an ISO 3166-1 alpha-3 country code (e.g. ESP, FRA, DEU).",
    ),
    Regla(
        "valor.municipio-ine", E, "§7.1",
        "Código de municipio INE de 5 dígitos", "5-digit INE municipality code",
        "«codigoMunicipio» debe ser el código de municipio del INE: 5 dígitos.",
        "'codigoMunicipio' must be the INE municipality code: 5 digits.",
    ),
    Regla(
        "valor.caducidad", E, "§7.2",
        "Caducidad de tarjeta MM/AAAA", "Card expiry MM/YYYY",
        "«caducidadTarjeta» debe tener formato MM/AAAA.", "'caducidadTarjeta' must use the MM/YYYY format.",
    ),
    Regla(
        "valor.correo", E, "§3; §4",
        "Correo electrónico con formato válido", "Valid e-mail address format",
        "«{campo}» no tiene formato de dirección de correo electrónico válido.",
        "'{campo}' is not a valid e-mail address.",
    ),
    Regla(
        "valor.telefono", A, "§3; §4",
        "Formato del teléfono", "Phone number format",
        "«{campo}» contiene caracteres poco habituales en un teléfono. El documento no define su formato.",
        "'{campo}' contains characters unusual in a phone number. The document does not define its format.",
        "P9",
    ),
    Regla(
        "valor.soporte", A, "§3",
        "Formato del número de soporte", "Document support number format",
        "«soporteDocumento» contiene caracteres que no son letras ni cifras. El documento no define su formato.",
        "'soporteDocumento' contains characters other than letters and digits. The document does not define its "
        "format.",
        "P10",
    ),
    # --- Dirección (§7.1) ----------------------------------------------------------------------------------------
    Regla(
        "direccion.municipio-espana", E, "§7.1",
        "En España, «codigoMunicipio» obligatorio", "In Spain, 'codigoMunicipio' is mandatory",
        "La dirección está en España (pais = ESP): «codigoMunicipio» es obligatorio.",
        "The address is in Spain (pais = ESP): 'codigoMunicipio' is mandatory.",
    ),
    Regla(
        "direccion.municipio-extranjero", E, "§7.1",
        "Fuera de España, «nombreMunicipio» obligatorio", "Outside Spain, 'nombreMunicipio' is mandatory",
        "La dirección no está en España: «nombreMunicipio» es obligatorio.",
        "The address is not in Spain: 'nombreMunicipio' is mandatory.",
    ),
    Regla(
        "direccion.ine-fuera-espana", A, "§7.1",
        "Código INE solo en España", "INE code only in Spain",
        "Hay «codigoMunicipio» en una dirección fuera de España; el código del INE solo se define para España.",
        "There is a 'codigoMunicipio' in an address outside Spain; INE codes only exist for Spain.",
    ),
    Regla(
        "direccion.codigo-postal", A, "§7.1",
        "Código postal español de 5 cifras", "Spanish postcode with 5 digits",
        "El código postal de una dirección en España suele tener 5 cifras. El documento solo dice String(20).",
        "A postcode in Spain normally has 5 digits. The document only says String(20).",
        "P23",
    ),
    Regla(
        "direccion.cp-provincia", A, "§7.1",
        "Código postal y municipio de la misma provincia", "Postcode and municipality in the same province",
        "El código postal empieza por {cp} y el código de municipio por {ine}: no parecen de la misma provincia.",
        "The postcode starts with {cp} and the municipality code with {ine}: they do not look like the same "
        "province.",
        "P23",
    ),
    # --- Documento de identidad (§3, §4, §8.5) -------------------------------------------------------------------
    Regla(
        "documento.nif-formato", E, "§3; §8.5",
        "NIF con formato válido", "NIF with a valid format",
        "El número de un NIF debe tener 8 cifras y una letra (por ejemplo, 12345678Z).",
        "A NIF number must have 8 digits and a letter (for example, 12345678Z).",
    ),
    Regla(
        "documento.nie-formato", E, "§3; §8.5",
        "NIE con formato válido", "NIE with a valid format",
        "El número de un NIE debe tener X, Y o Z, 7 cifras y una letra (por ejemplo, X1234567L).",
        "A NIE number must have X, Y or Z, 7 digits and a letter (for example, X1234567L).",
    ),
    Regla(
        "documento.letra", E, "§3; §8.5",
        "Letra de control de NIF y NIE", "NIF and NIE check letter",
        "La letra de control del {tipo} no es correcta: debería ser «{esperada}».",
        "The {tipo} check letter is wrong: it should be '{esperada}'.",
    ),
    Regla(
        "documento.nie-como-nif", E, "§3; §8.5",
        "El número corresponde al tipo (NIF)", "The number matches the type (NIF)",
        "El número tiene forma de NIE, pero «tipoDocumento» es NIF.",
        "The number looks like a NIE, but 'tipoDocumento' is NIF.",
    ),
    Regla(
        "documento.nif-como-nie", E, "§3; §8.5",
        "El número corresponde al tipo (NIE)", "The number matches the type (NIE)",
        "El número tiene forma de DNI/NIF, pero «tipoDocumento» es NIE.",
        "The number looks like a DNI/NIF, but 'tipoDocumento' is NIE.",
    ),
    Regla(
        "documento.normalizable", A, "§3; §4",
        "Número de documento sin separadores", "Document number without separators",
        "El número solo es válido en mayúsculas y sin espacios, puntos ni guiones: escríbalo así.",
        "The number is only valid in capitals and without spaces, dots or hyphens: write it that way.",
        "P25",
    ),
    Regla(
        "documento.nif-sin-verificar", A, "§3; §8.5",
        "NIF K, L o M", "NIF starting with K, L or M",
        "NIF que empieza por K, L o M: se acepta por su forma, pero su letra de control no se ha verificado.",
        "NIF starting with K, L or M: accepted by its shape, but its check letter has not been verified.",
        "P24",
    ),
    Regla(
        "documento.tipo-no-corresponde", A, "§3; §4",
        "El número corresponde al tipo (PAS, OTRO)", "The number matches the type (PAS, OTRO)",
        "El tipo de documento es {tipo}, pero el número es un DNI o NIE válido. ¿Debería ser NIF o NIE?",
        "The document type is {tipo}, but the number is a valid DNI or NIE. Should it be NIF or NIE?",
        "P26",
    ),
    Regla(
        "documento.sin-tipo", E, "§3; §4",
        "Número de documento con su tipo", "Document number with its type",
        "Hay número de documento pero no «tipoDocumento»: el número debe corresponder a un tipo de documento.",
        "There is a document number but no 'tipoDocumento': the number must match a document type.",
    ),
    Regla(
        "documento.sin-numero", A, "§3; §4",
        "Tipo de documento con su número", "Document type with its number",
        "Hay «tipoDocumento» pero no número de documento.",
        "There is a 'tipoDocumento' but no document number.",
        "P27",
    ),
    # --- Persona (condicionales) ---------------------------------------------------------------------------------
    Regla(
        "persona.apellido2-nif", E, "§3",
        "Segundo apellido obligatorio con NIF", "Second surname mandatory with NIF",
        "Con tipo de documento NIF, «apellido2» es obligatorio.",
        "With document type NIF, 'apellido2' is mandatory.",
    ),
    Regla(
        "persona.soporte-nif-nie", E, "§3",
        "Número de soporte obligatorio con NIF o NIE", "Support number mandatory with NIF or NIE",
        "Con tipo de documento {tipo}, «soporteDocumento» es obligatorio.",
        "With document type {tipo}, 'soporteDocumento' is mandatory.",
    ),
    Regla(
        "persona.documento-mayor", E, "§3",
        "Documento obligatorio para mayores de edad", "Identity document mandatory for adults",
        "La persona es mayor de edad en la fecha de entrada: «tipoDocumento» y «numeroDocumento» son obligatorios.",
        "The person is an adult on the arrival date: 'tipoDocumento' and 'numeroDocumento' are mandatory.",
        "P6",
    ),
    Regla(
        "persona.parentesco-menor", E, "§3",
        "Con menores, parentesco en al menos un adulto", "With minors, relationship in at least one adult",
        "Hay {menores} persona(s) menor(es) de edad y ninguna mayor de edad tiene informado «parentesco».",
        "There are {menores} minor(s) and no adult has 'parentesco' (relationship) filled in.",
        "P6",
    ),
    Regla(
        "persona.parentesco-varios-menores", A, "§3",
        "Parentesco con varios menores", "Relationship with several minors",
        "Hay {menores} menores: el documento no dice cómo indicar el parentesco con cada uno (es un solo campo por "
        "persona).",
        "There are {menores} minors: the document does not say how to give the relationship with each one (it is a "
        "single field per person).",
        "P7",
    ),
    Regla(
        "persona.parentesco-en-menor", A, "§3",
        "Parentesco en la persona adulta", "Relationship on the adult",
        "«parentesco» está informado en una persona menor de edad; el documento lo pide en la persona mayor de edad.",
        "'parentesco' is filled in on a minor; the document asks for it on the adult.",
        "P7",
    ),
    Regla(
        "persona.contacto", E, "§3; §4",
        "Al menos un teléfono o correo", "At least one phone or e-mail",
        "Falta un medio de contacto: hay que incluir al menos uno de «telefono», «telefono2» o «correo».",
        "A means of contact is missing: include at least one of 'telefono', 'telefono2' or 'correo'.",
    ),
    Regla(
        "persona.nacimiento-posterior", A, "§3; §4",
        "Nacimiento anterior a la entrada", "Birth before arrival",
        "La fecha de nacimiento es posterior a la fecha de entrada.",
        "The date of birth is after the arrival date.",
        "P23",
    ),
    # --- Comunicación y contrato (coherencias) -------------------------------------------------------------------
    Regla(
        "comunicacion.sin-viajero", E, "§3",
        "Al menos una persona con rol VI", "At least one person with role VI",
        "La comunicación no tiene ninguna persona con rol VI (viajero); es obligatorio al menos una.",
        "The communication has no person with role VI (traveller); at least one is mandatory.",
    ),
    Regla(
        "comunicacion.sin-titular", E, "§4",
        "Una persona con rol TI (titular)", "One person with role TI (holder)",
        "La reserva no tiene ninguna persona con rol TI (titular del contrato); es obligatorio incluirla.",
        "The booking has no person with role TI (contract holder); it is mandatory.",
    ),
    Regla(
        "comunicacion.varios-titulares", A, "§4",
        "Un solo titular", "A single holder",
        "La reserva tiene {num} personas con rol TI; el documento habla de un bloque con el titular del contrato.",
        "The booking has {num} people with role TI; the document speaks of one block for the contract holder.",
        "P8",
    ),
    Regla(
        "contrato.salida-anterior", E, "§3; §4",
        "Salida posterior a la entrada", "Departure after arrival",
        "La fecha de salida es anterior a la de entrada.", "The departure date is before the arrival date.",
    ),
    Regla(
        "contrato.salida-igual", A, "§3; §4",
        "Salida distinta de la entrada", "Departure different from arrival",
        "La fecha y hora de salida son iguales a las de entrada.", "Departure and arrival date-times are equal.",
        "P23",
    ),
    Regla(
        "contrato.contrato-posterior", A, "§3; §4",
        "Contrato no posterior a la entrada", "Contract not after arrival",
        "La fecha del contrato es posterior a la fecha de entrada.", "The contract date is after the arrival date.",
        "P23",
    ),
    Regla(
        "contrato.hora-cero-parte", A, "§3",
        "Hora real en los partes", "Actual time in traveller reports",
        "«{campo}» lleva la hora T00:00:00. En los partes (§3) se espera la hora real; T00:00:00 como «hora "
        "desconocida» solo se prevé en las reservas (§4).",
        "'{campo}' has the time T00:00:00. Traveller reports (§3) expect the actual time; T00:00:00 as 'unknown "
        "time' is only foreseen for bookings (§4).",
        "P20",
    ),
    Regla(
        "contrato.num-personas", E, "§3",
        "No más personas que «numPersonas»", "No more people than 'numPersonas'",
        "«numPersonas» vale {num}, pero la comunicación incluye {total} persona(s), {vi} con rol VI.",
        "'numPersonas' is {num}, but the communication includes {total} person(s), {vi} with role VI.",
        "P8",
    ),
    Regla(
        "contrato.num-personas-faltan", A, "§3",
        "Una persona por cada alojado declarado", "One person per declared guest",
        "«numPersonas» vale {num}, pero la comunicación solo incluye {total} persona(s). ¿Falta alguna por incluir?",
        "'numPersonas' is {num}, but the communication only includes {total} person(s). Is anyone missing?",
        "P28",
    ),
    Regla(
        "contrato.num-personas-reserva", A, "§4",
        "Viajeros (VI) no superan «numPersonas»", "Travellers (VI) do not exceed 'numPersonas'",
        "«numPersonas» vale {num}, pero la reserva incluye {vi} personas con rol VI.",
        "'numPersonas' is {num}, but the booking includes {vi} people with role VI.",
        "P8",
    ),
    Regla(
        "solicitud.referencia-duplicada", A, "§3; §4",
        "Referencias de contrato distintas", "Distinct contract references",
        "La referencia de contrato «{referencia}» se repite en las comunicaciones {posiciones}.",
        "The contract reference '{referencia}' is repeated in communications {posiciones}.",
        "P22",
    ),
)

# fmt: on

REGLAS: Final[Mapping[str, Regla]] = MappingProxyType({r.codigo: r for r in _LISTA})
