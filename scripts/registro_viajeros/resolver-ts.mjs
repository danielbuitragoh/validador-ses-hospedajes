// Hook de resolución de Node: permite importar los módulos TypeScript de registro-viajeros, que se importan entre
// sí sin extensión ('../oficial/paises'), probando con '.ts'. Node >= 22.18 ejecuta TypeScript quitando los tipos.
export async function resolve(especificador, contexto, siguiente) {
  const relativo = especificador.startsWith('./') || especificador.startsWith('../')
  if (relativo && !/\.(?:[cm]?[jt]sx?|json)$/.test(especificador)) {
    try {
      return await siguiente(`${especificador}.ts`, contexto)
    } catch {
      // no es un .ts: se resuelve tal cual
    }
  }
  return siguiente(especificador, contexto)
}
