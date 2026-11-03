# Lectura del documento oficial (Instrucciones.pdf v1.1.0)

Fuente única de verdad: [`Instrucciones.pdf`](Instrucciones.pdf), «Alta masiva de comunicaciones – Hospedajes»,
versión 1.1.0 (08-01-2024), Ministerio del Interior, Secretaría de Estado de Seguridad (SGSICS). 34 páginas.
Copia idéntica (SHA-256 `02df3f40d7022ffe00875f18edf4e8aa5b75bf411b00b8a06aa125d0d07fc664`) de la que usa
[registro-viajeros](https://github.com/danielbuitragoh/registro-viajeros/tree/main/docs/oficial).

Este fichero resume **lo que dice el documento** (con su apartado) y **lo que no dice** (pendientes). Si el código y
este fichero discrepan con el PDF, manda el PDF. En el código, cada pendiente lleva el marcador `PENDIENTE-OFICIAL`.

## Cómo se ha leído

Se ha leído el PDF entero: texto de las 34 páginas y las seis figuras (diagramas del esquema XML generados con una
herramienta XSD). En las figuras, un recuadro de **línea continua** es un elemento obligatorio y uno de **línea
discontinua**, opcional; `1..∞` indica repetición; el símbolo de «elección» indica que va uno u otro. Las figuras
dan además el **orden** de los elementos (secuencia). Las tablas dan tipo, longitud y obligatoriedad (incluidas las
condicionales). Donde figura y tabla coinciden, se aplica tal cual; donde discrepan, se marca como pendiente.

## Lo que establece el documento (y valida esta herramienta)

- **§2**: el fichero es **XML** y sigue una plantilla. Un fichero puede llevar varias comunicaciones, pero **todas
  del mismo tipo** (partes de viajeros, reservas de hospedaje, alquiler de vehículos…).
- **§3, figura 1 — Partes de viajeros**: `peticion > solicitud > (codigoEstablecimiento, comunicacion 1..n)`;
  `comunicacion > (contrato, persona 1..n)`.
  - `codigoEstablecimiento` String(10), obligatorio.
  - `contrato`: `referencia` String(50) · `fechaContrato` AAAA-MM-DD · `fechaEntrada` y `fechaSalida`
    AAAA-MM-DDThh:mm:ss · `numPersonas` Numérico · `numHabitaciones` Numérico (opc.) · `internet` Booleano (opc.) ·
    `pago` (bloque §7.2).
  - `persona` (en este orden): `rol` String(2) TI|VI (al menos un bloque **VI**) · `nombre` String(50) ·
    `apellido1` String(50) · `apellido2` String(50), **obligatorio si el tipo de documento es NIF** ·
    `tipoDocumento` String(5), **obligatorio si la persona es mayor de edad** · `numeroDocumento` String(15), ídem,
    «deberá corresponder al tipo de documento … y tener un formato válido en el caso de NIF o NIE» ·
    `soporteDocumento` String(9), **obligatorio si el tipo de documento es NIF o NIE** · `fechaNacimiento`
    AAAA-MM-DD, obligatoria · `nacionalidad` ISO 3166-1 alfa-3 (opc.) · `sexo` String(1) (opc.) · `direccion`
    (bloque §7.1), obligatoria · `telefono`, `telefono2` String(20) y `correo` String(50): **obligatorio incluir al
    menos una de las tres**; el correo «deberá tener formato de dirección de correo electrónico válido» ·
    `parentesco` String(5): **si alguna persona es menor de edad, al menos una de las mayores de edad ha de tener
    informado su parentesco** (aclaración de la v1.1.0).
- **§4, figura 2 — Reservas de hospedaje**: `peticion > solicitud > comunicacion 1..n` (sin
  `codigoEstablecimiento`); `comunicacion > (establecimiento, contrato, persona 1..n)`.
  - `establecimiento`: **elección** entre `codigo` String(10) y `datosEstablecimiento` (`tipo` String(10) de la
    tabla 8.6, `nombre` String(50) y `direccion` §7.1, los tres obligatorios).
  - `contrato`: igual que en §3. Si se desconoce la hora de entrada o de salida, se envía `AAAA-MM-DDT00:00:00`.
  - `persona`: `rol`, `nombre` y `apellido1` obligatorios; `apellido2`, `tipoDocumento`, `numeroDocumento`,
    `fechaNacimiento`, `nacionalidad`, `sexo` y `direccion` opcionales; contacto (uno de los tres) obligatorio.
    **No existen** `soporteDocumento` ni `parentesco`. Debe haber un bloque con el **titular (TI)** y tantos como
    viajeros se conozcan.
- **§7.1, figura 5 — Bloque `direccion`**: `direccion` String(100) · `direccionComplementaria` String(100) (opc.) ·
  `codigoMunicipio` String(5), INE de 5 dígitos, **obligatorio si el país es España** · `nombreMunicipio`
  String(100), **obligatorio si el país no es España** · `codigoPostal` String(20) · `pais` ISO 3166-1 alfa-3.
- **§7.2, figura 6 — Bloque `pago`**: `tipoPago` String(5) (tabla 8.7), obligatorio · `fechaPago` AAAA-MM-DD ·
  `medioPago` String(50) · `titular` String(100) · `caducidadTarjeta` String(7) con formato MM/AAAA.
- **§8 — Tablas de códigos**: 8.3 parentesco, 8.4 sexo, 8.5 tipos de documento (**solo** NIF, NIE, PAS y OTRO),
  8.6 tipos de establecimiento y 8.7 tipos de pago. Se transcriben en
  [`oficial.py`](../../src/validador_ses_hospedajes/oficial.py) y una prueba comprueba su contenido exacto.
- **§5 y §6** (alquiler y reserva de vehículos) no aplican a un alojamiento: la herramienta los **reconoce** (por el
  bloque `vehiculo` de las figuras 3 y 4) y dice que no los valida. Las tablas 8.1, 8.2, 8.8 y 8.9 son de vehículos.

## Pendientes: lo que el documento NO deja claro

Numeración compartida con registro-viajeros (P1–P17); los puntos propios del validador empiezan en P18.
Ningún pendiente produce un **error**: como mucho, un **aviso**.

| # | Lo que no dice el documento | Qué hace el validador |
|---|-----------------------------|------------------------|
| P1 | No incluye el XSD ni la plantilla: ni **espacio de nombres**, ni prefijos, ni atributos, ni declaración XML. Las figuras nombran tipos con prefijo `hospe:`, pero no el espacio de nombres de los elementos. | Compara por nombre local. **Aviso** si los elementos llevan espacio de nombres o atributos. |
| P2 | La tabla del §3 llama `documento` al campo que la figura 1 (y el §4) llaman `numeroDocumento`. | Exige `numeroDocumento` (figura = esquema). Si en un parte aparece `documento` en su lugar, lo valida igual y da **aviso**. |
| P3 | No define el formato del Booleano `internet` (¿`true/false`, `1/0`, `S/N`?). | Acepta el elemento en su sitio y da **aviso** con cualquier valor. |
| P4 | No incluye la tabla de municipios del INE ni la de países (solo cita «INE, 5 dígitos» e «ISO 3166-1 Alfa-3»). | INE: solo formato (5 dígitos). País: formato y pertenencia a la lista ISO 3166-1 alfa-3 (norma citada, no incluida en el PDF; revisar vigencia). |
| P6 | No define **cuándo es «mayor de edad»** ni respecto a qué fecha. | 18 años cumplidos en la fecha de entrada. |
| P7 | `parentesco` es un único campo por persona: no dice con qué menor se relaciona si hay varios. | Exige el parentesco en al menos un adulto (lo que sí dice); **aviso** si hay varios menores o si el parentesco está en un menor. |
| P8 | No dice si el titular que también se aloja se repite (TI + VI), ni si el TI cuenta en `numPersonas`. | Parte: `numPersonas` debe coincidir con el total de personas **o** con las de rol VI. Reserva: **aviso** si hay más VI que `numPersonas` o más de un TI. |
| P9 | No define el formato del teléfono; del correo solo pide «formato válido». | Teléfono: **aviso** si lleva caracteres que no sean cifras, espacios, `+ ( ) - .`. Correo: comprobación básica `algo@dominio.ext` (error). |
| P10 | No define el formato del número de soporte ni de los pasaportes. | Soporte: longitud ≤ 9 (error) y **aviso** si no es alfanumérico. Pasaporte y OTRO: solo longitud. |
| P15 | «Código INE, 5 dígitos» no aclara si incluye el dígito de control del INE. | 5 dígitos exactos (provincia + municipio, sin dígito de control). |
| P16 | La tabla 8.5 solo tiene NIF, NIE, PAS y OTRO. | Solo admite esos cuatro códigos. |
| P17 | Erratas de referencia: el §3 y el §4 remiten a «la tabla del apartado 6» (las tablas están en el **8**) y el §4 remite a «4.1 Bloque direccion» y «4.2 Bloque pago» (son el **7.1** y el **7.2**). | Se citan los apartados correctos (8.x, 7.1, 7.2). |
| P18 | No dice si un elemento **opcional vacío** (`<apellido2/>`) se admite o debe omitirse. | Obligatorio vacío = falta (error). Opcional vacío: **aviso** (mejor omitirlo). |
| P19 | «Numérico» no dice si es entero ni si admite 0. | No numérico: error. Numérico pero no entero positivo: **aviso**. |
| P20 | La hora `T00:00:00` como «hora desconocida» solo se prevé en el §4 (reservas). | En partes (§3), **aviso** si la entrada o la salida llevan `T00:00:00`. |
| P21 | No define la codificación de caracteres. | Se lee lo que declare el XML; **aviso** si declara otra distinta de UTF-8. |
| P22 | No dice si la `referencia` del contrato debe ser única en el fichero. | **Aviso** si se repite. |
| P23 | No exige expresamente coherencias de fechas (salida = entrada, contrato posterior a la entrada, nacimiento posterior a la entrada) ni la forma del código postal español. | **Avisos** orientativos. Solo «salida anterior a la entrada» es error (las fechas dejarían de tener sentido). |
| P24 | No dice si los NIF que empiezan por K, L o M son «formato válido». | Se aceptan con **aviso** (su letra de control no se verifica). |
| P25 | No dice si el número de documento admite minúsculas, espacios o guiones. | Si solo es válido tras normalizarlo, **aviso** (escríbalo en mayúsculas y sin separadores). |
| P26 | «Deberá corresponder al tipo de documento»: solo se puede comprobar para NIF y NIE. | **Aviso** si con PAS u OTRO se escribe un DNI o NIE válido. |
| P27 | No dice qué hacer con un tipo de documento sin número (o al revés) cuando no son obligatorios. | Número sin tipo: error (no puede «corresponder» a nada). Tipo sin número: **aviso**. |

## Fuera del alcance del documento (y de esta herramienta)

- Cómo se sube el fichero al portal y qué errores devuelve el sistema (P14 de registro-viajeros). **La validación
  final la hace siempre el portal SES.Hospedajes.**
- Plazos de comunicación y de conservación: vienen del RD 933/2021, no de este documento.
