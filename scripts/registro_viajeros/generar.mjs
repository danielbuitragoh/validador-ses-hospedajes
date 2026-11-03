// Prueba cruzada: genera ficheros XML con el PROPIO código de registro-viajeros, sin modificar aquel repositorio.
//
//   node scripts/registro_viajeros/generar.mjs <copia de registro-viajeros> <carpeta destino>
//
// Hace lo mismo que su `generarFichero` (src/exportador/index.ts): barrera 1 con sus validadores del modelo
// (`validarEstablecimiento`, `validarReserva`) y después su `construirXml`. Su barrera 2 (`validarXml`) usa
// DOMParser, que existe en el navegador y en jsdom pero no en Node sin dependencias, así que aquí no se ejecuta:
// ese papel lo hace precisamente este validador. Datos: sus fixtures ficticias (tests/fixtures.ts) y su demo
// (src/demo/datos.ts) con una fecha fija. Escribe los .xml y un manifiesto.json con el commit de origen y la
// huella SHA-256 de cada fichero. Requiere Node >= 22.18 (ejecuta TypeScript sin compilar).
import { execFileSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import { mkdirSync, writeFileSync } from 'node:fs'
import { register } from 'node:module'
import { join, resolve } from 'node:path'
import { pathToFileURL } from 'node:url'

process.env.TZ = 'UTC' // la demo usa horas locales: zona fija para que el resultado sea reproducible

const [origenArg, destinoArg] = process.argv.slice(2)
if (!origenArg || !destinoArg) {
  console.error('Uso: node generar.mjs <copia de registro-viajeros> <carpeta destino>')
  process.exit(2)
}
const origen = resolve(origenArg)
const destino = resolve(destinoArg)
register('./resolver-ts.mjs', import.meta.url)

const modulo = (ruta) => import(pathToFileURL(join(origen, ruta)).href)
const { validarEstablecimiento } = await modulo('src/exportador/index.ts')
const { construirXml } = await modulo('src/exportador/construir.ts')
const { validarReserva } = await modulo('src/validators/reserva.ts')
const f = await modulo('tests/fixtures.ts')
const { crearDatosDemo } = await modulo('src/demo/datos.ts')

const AHORA = new Date('2026-11-02T10:00:00Z')

/** Errores de la barrera 1 de registro-viajeros (los avisos no bloquean, igual que en su generarFichero). */
function erroresModelo(establecimiento, reservas, tipo) {
  const incidencias = [...validarEstablecimiento(establecimiento, tipo), ...reservas.flatMap((r) => validarReserva(r, tipo))]
  return incidencias.filter((i) => i.gravedad === 'error')
}

function exportar(establecimiento, reservas, tipo) {
  const errores = erroresModelo(establecimiento, reservas, tipo)
  if (errores.length > 0) throw new Error(`registro-viajeros rechaza la exportación: ${JSON.stringify(errores)}`)
  return construirXml(establecimiento, reservas, tipo)
}

/** De la demo, las reservas que registro-viajeros deja exportar (las incompletas las bloquea él mismo). */
function exportablesDemo(tipo) {
  const { establecimiento, reservas } = crearDatosDemo(AHORA)
  const ok = reservas.filter((r) => erroresModelo(establecimiento, [r], tipo).length === 0)
  if (ok.length === 0) throw new Error(`ninguna reserva de la demo se puede exportar como ${tipo}`)
  return exportar(establecimiento, ok, tipo)
}

const conTarjeta = f.reserva({
  id: 'r2',
  referencia: 'RES-2026-0002',
  numHabitaciones: 2,
  numPersonas: 1,
  pago: { tipoPago: 'TARJT', fechaPago: '2026-10-20', medioPago: 'VISA ****0000', titular: 'Lucía Prueba', caducidadTarjeta: '09/2028' },
  viajeros: [f.extranjero()],
})

const casos = {
  'ficticio-parte-adulto-y-menor.xml': () =>
    exportar(f.establecimiento(), [f.reserva({ viajeros: [f.adulto(), f.menor()], numPersonas: 2 })], 'partes'),
  'ficticio-parte-extranjero.xml': () =>
    exportar(f.establecimiento(), [f.reserva({ viajeros: [f.extranjero()] })], 'partes'),
  'ficticio-parte-varias-reservas.xml': () => exportar(f.establecimiento(), [f.reserva(), conTarjeta], 'partes'),
  'ficticio-parte-demo.xml': () => exportablesDemo('partes'),
  'ficticio-reserva-titular-y-extranjero.xml': () =>
    exportar(
      f.establecimiento(),
      [f.reserva({ viajeros: [f.adulto({ esTitular: true }), f.extranjero()], numPersonas: 2 })],
      'reservas',
    ),
  'ficticio-reserva-sin-codigo-establecimiento.xml': () =>
    exportar(
      f.establecimiento({ codigoEstablecimiento: '' }),
      [f.reserva({ viajeros: [f.adulto({ esTitular: true })] })],
      'reservas',
    ),
  'ficticio-reserva-demo.xml': () => exportablesDemo('reservas'),
}

mkdirSync(destino, { recursive: true })
const huellas = {}
for (const [nombre, generar] of Object.entries(casos)) {
  const xml = generar()
  writeFileSync(join(destino, nombre), xml, 'utf8')
  huellas[nombre] = createHash('sha256').update(xml, 'utf8').digest('hex')
}

let commit = 'desconocido'
try {
  commit = execFileSync('git', ['-C', origen, 'rev-parse', 'HEAD'], { encoding: 'utf8' }).trim()
} catch {
  // sin git: el manifiesto lo indica
}
const manifiesto = {
  descripcion:
    'XML FICTICIOS generados por registro-viajeros (validadores del modelo + construirXml) con sus datos de prueba y de demo. ' +
    'No los edite a mano: regénerelos con scripts/registro_viajeros/generar.mjs.',
  repositorio: 'https://github.com/danielbuitragoh/registro-viajeros',
  commit,
  fecha_fija: AHORA.toISOString(),
  ficheros: huellas,
}
writeFileSync(join(destino, 'manifiesto.json'), `${JSON.stringify(manifiesto, null, 2)}\n`, 'utf8')
console.log(`${Object.keys(casos).length} ficheros generados en ${destino} (registro-viajeros ${commit.slice(0, 7)})`)
