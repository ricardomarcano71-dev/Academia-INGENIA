# Herramientas (tablas, fórmulas, constantes)

- Cada herramienta es un HTML independiente en `herramientas/<id>.html` (público, sin cifrar, funciona sin internet salvo las fuentes).
- Con `?hoja` al final de la dirección, la página muestra su "hoja" para imprimir (A4).
- `node fuente/herramientas/generar_descargas.js [id ...]` crea `herramientas/descargas/<id>.png` y `<id>.pdf` desde esa hoja. Agrega cada id nuevo a `HOJAS` con su tamaño en mm.
- Para publicar una herramienta nueva, márcala con `true` en la lista `H` de `herramientas.html`.

## Herramientas de fórmulas (kit)
- `kit.html` es la plantilla común (lista de fórmulas, dibujo interactivo con controles, ejemplo que se escribe solo paso a paso, voz y hoja para imprimir que ajusta sola el tamaño de letra).
- Cada herramienta es un archivo `datos/<id>.js` con `// TITULO:` y `// ICONO:` arriba y un objeto `TOOL` con sus grupos e ítems (`t`, `f`, `x`, `v`, `ej`).
- `python3 fuente/herramientas/build.py [id ...]` arma `herramientas/<id>.html`. Luego genera la imagen y el PDF con `generar_descargas.js`.
