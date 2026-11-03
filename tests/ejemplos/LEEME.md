# Ficheros de ejemplo (FICTICIOS)

Todos los datos de estos ficheros son **inventados**: nombres de prueba, documentos de la forma `0000000X` con su
letra de control correcta (no emitidos), teléfonos `+346000000NN` y correos `@example.com/.org`. Cada fichero lleva
en sus primeras líneas un comentario `FICTICIO` (salvo `invalidos/fichero.vacio.xml`, que está vacío a propósito).

- `validos/`: un parte de viajeros (§3) y una reserva de hospedaje (§4) sin ningún error ni aviso.
- `invalidos/<regla>.xml`: un ejemplo por regla del catálogo, que cambia lo mínimo para incumplirla. Los genera
  `scripts/generar_ejemplos.py`; una prueba comprueba que están al día y que cada uno dispara su regla.
- `registro-viajeros/`: XML generados por el código de
  [registro-viajeros](https://github.com/danielbuitragoh/registro-viajeros) con sus propios datos ficticios
  (prueba cruzada, ver `scripts/registro_viajeros/`).

Pruébelos con la CLI:

```bash
uv run ses-validar tests/ejemplos/validos
uv run ses-validar tests/ejemplos/invalidos/documento.letra.xml
```
