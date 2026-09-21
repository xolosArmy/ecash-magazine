# eCash Magazine México

Revista estática publicada en GitHub Pages en **https://magazine.ecash.mx**.
El sistema editorial conserva las 43 publicaciones históricas y sus URLs, y admite nuevas publicaciones editoriales sin alterar ese baseline de preservación.

## Fuente editorial y generación

- `editorial/catalog.json`: fuente de verdad de títulos, URLs, géneros, fichas,
  temas, imágenes y referencias documentadas. Cada campo tiene procedencia.
- `editorial/catalog.schema.json`: contrato de datos; los valores ausentes o
  ambiguos siguen siendo `null`, con su motivo registrado.
- `content/<ruta>.html`: cuerpos periodísticos fuente. Las 43 rutas históricas
  permanecen preservadas; las nuevas publicaciones se incorporan aquí antes de
  regenerar sus páginas públicas.
- `editorial/frontpage.json`: selección explícita de la historia principal.
- `editorial/media-map.json`: correspondencia de recursos históricos con sus
  versiones locales, dimensiones y variantes responsivas.
- `editorial/site.json`: configuración técnica; conserva la analítica anterior
  únicamente en las 31 rutas que ya la tenían.
- `editorial/metadata-removals.json`: reemplazos revisados de fichas repetidas;
  cada selector exige el texto original exacto antes de usar la cabecera común.
- `scripts/build_site.py`: genera HTML, navegación, catálogo consultable,
  perfiles, índices temáticos, metadatos, sitemap y RSS sin dependencias de
  ejecución en el servidor ni un framework de frontend.
- `assets/css/editorial.css` y `assets/js/editorial.js`: sistema visual compartido
  y búsqueda progresiva. `assets/js/navigation.js` se inserta después de la
  cabecera y antes del cuerpo para establecer el menú móvil antes de la primera
  pintura y evitar saltos de layout. La lectura y los índices funcionan sin JS.

El generador utiliza Python 3.11+ y una dependencia **de desarrollo**, lxml.
GitHub Pages sirve los archivos ya generados; no necesita Python, Node, base de
datos ni compilación en el navegador. `_config.yml` excluye fuentes y documentos
de revisión sin excluir la URL histórica que ya existe bajo `/editorial/`.

```sh
python -m pip install -r requirements-dev.txt
python scripts/build_site.py
git diff --exit-code
test -z "$(git ls-files --others --exclude-standard)"
python scripts/verify_site.py --report docs/qa/structural-after.json
python scripts/extract_legacy.py --verify-generated --output .
```

## Reglas de edición

1. Actualizar la ficha en el catálogo sólo con información comprobable.
2. Editar deliberadamente el cuerpo fuente si hay una modificación periodística
   autorizada; conservar enlaces, atribuciones, evidencia y URL.
3. Registrar fecha/nota de actualización únicamente cuando cambie la información
   editorial. Cambiar CSS o ejecutar el generador no cambia `dateModified`.
4. Regenerar y revisar el diff de los HTML de salida. No editar la misma ficha en
   distintas páginas manualmente.
5. Para esta migración, el gate de preservación compara los cuerpos con el
   manifiesto del commit `7b5cc72c05ee9deb74f26ff85edd209ee2d9b511`. Una futura
   edición periodística necesita revisión y actualización explícita de esa
   referencia; no se debe desactivar el gate para ocultar cambios.

No se infiere el género de la carpeta ni el autor/fecha por contexto. Los nueve
géneros son Noticia, Entrevista, Crónica, Reportaje, Columna, Opinión, Editorial,
Reseña y Análisis técnico. Una pieza pendiente permanece en archivo, búsqueda,
temas y firma disponibles; no se atribuye a un género confirmado.

La portada sólo muestra módulos con contenido real. La historia principal no se
duplica en otro módulo; sus metadatos pendientes no se completan por conveniencia.
El buscador descarga el índice de texto completo sólo al escribir una consulta;
los filtros por género, tema, firma y año trabajan sobre el HTML ya presente.

El RSS contiene todas las publicaciones del catálogo; las 43 históricas permanecen preservadas. `pubDate` sólo se emite cuando la fuente
conserva fecha, hora y zona; no se inventa medianoche para cumplir el formato RSS.

La comprobación de navegador se ejecuta en `.github/workflows/editorial-qa.yml`
sobre la rama y el commit base inmutable. `qa/` contiene únicamente dependencias
de revisión: Chromium, axe, Lighthouse y validación HTML; no se publican ni se
cargan en la revista. Los reportes distinguen medidas de laboratorio y errores
de terceros de las comprobaciones del código propio.

## Revisión y deuda

- [Decisiones editoriales pendientes](docs/editorial-pending.md).
- [Preservación y transformaciones técnicas](docs/content-preservation.md).
- [Imágenes, procedencia y pesos](docs/media-notes.md).
- [Pruebas, métricas y limitaciones](docs/qa/README.md).

Este cambio no mueve el dominio, no modifica el hosting y no hace merge.
