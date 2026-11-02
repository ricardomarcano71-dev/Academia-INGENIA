# Herramientas (tablas, fórmulas, constantes)

- Cada herramienta es un HTML independiente en `herramientas/<id>.html` (público, sin cifrar, funciona sin internet salvo las fuentes).
- Con `?hoja` al final de la dirección, la página muestra su "hoja" para imprimir (A4).
- `node fuente/herramientas/generar_descargas.js [id ...]` crea `herramientas/descargas/<id>.png` y `<id>.pdf` desde esa hoja. Agrega cada id nuevo a `HOJAS` con su tamaño en mm.
- Para publicar una herramienta nueva, márcala con `true` en la lista `H` de `herramientas.html`.
