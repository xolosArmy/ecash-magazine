# Preservación del contenido publicado

La migración utiliza 43 fragmentos editoriales en `content/<ruta-original>.html`.
Esos fragmentos conservan el contenido de los 43 artículos anteriores al
rediseño. Las páginas públicas siguen utilizando sus rutas originales.

## Origen y reproducción

`scripts/extract_legacy.py` lee una copia inmutable de la versión anterior.
La extracción inicial se hizo desde el snapshot de trabajo `baseline-ecash`;
el SHA-256 de cada HTML de origen está registrado en
`editorial/preservation.json`. No se debe ejecutar el extractor sobre los HTML
públicos ya generados. Para reproducirlo se utiliza un checkout de la revisión
base del PR, en otra carpeta:

```sh
python scripts/extract_legacy.py --source /ruta/al/checkout-base --output .
```

El extractor necesita `lxml` solamente durante esta operación de mantenimiento;
no añade una librería al navegador. El generador normal debe consumir los
fragmentos ya extraídos y el catálogo editorial común.

## Qué conserva

- Encabezados editoriales completos, incluso cuando estaban fuera de `main`.
- Titulares, bajadas, firmas, fechas y rótulos de género originales.
- Párrafos, listas, citas, tablas, números, hashes, referencias y orden de lectura.
- Recuadros laterales, advertencias, límites metodológicos y notas editoriales.
- Figuras, imágenes, captions, multimedia y textos alternativos existentes.
- Destinos de enlaces, valores de código y anchors originales.
- La conclusión de `opinion/economia-agentica-tokenizada.html`, que estaba
  etiquetada como `footer` pero forma parte del artículo.
- El pie de metadatos de `analisis/ecash-mining-variance.html` y el pie editorial
  de `analisis/gobernanza-rmz-ecash-mexico.html`.

Se verificaron 25 imágenes —15 eran fondos CSS—, 188 enlaces, cuatro elementos
de multimedia y 229 bloques o fragmentos de código. No se encontró ningún ID
duplicado dentro de los fragmentos ni ninguna imagen sin atributo `alt`.

## Cambios técnicos inevitables

1. Se retiraron los encabezados de marca/navegación global, la capa decorativa
   `scanline` y los pies de sitio. El texto y los enlaces de cada elemento
   retirado quedan separados en `removed_site_shell`; nunca se utiliza una
   regla que elimine cualquier `aside` o cualquier `footer` indiscriminadamente.
2. Las tres selecciones de idioma implementadas con botones y
   `window.location.href` se convirtieron en enlaces convencionales. Sus rótulos
   y destinos se conservaron en `nav.article-translations`.
3. Se retiraron estilos y scripts del documento anterior. También se retiraron
   53 atributos `style` para que la tipografía, los colores y los anchos dependan
   del sistema visual común. Los atributos de datos y el contenido permanecen.
4. Los 15 fondos de imagen de los heroes se materializaron como `img` con la
   misma URL, `alt=""` y `role="presentation"`. Antes eran imágenes decorativas
   CSS sin alternativa textual; no se inventó una descripción de su escena.
   El sistema de medios puede sustituir su URL por un derivado optimizado del
   mismo archivo, sin recorte editorial nuevo.
5. Los contenedores `main` y `article` anteriores se convirtieron a `div` porque
   la página generada proporciona el landmark principal y el elemento article.
   Los pies editoriales sustantivos se conservan como `section`.
6. Se retiraron comentarios de implementación, sin retirar texto visible.
7. Se normalizó la indentación de nodos de texto vacíos y líneas en blanco,
   fuera de `pre` y `code`. Se mantiene un espacio o salto de línea entre
   elementos inline para no unir palabras. El contenido de código permanece
   byte por byte, incluidos sus espacios.

### Visualización de Teyolia

En `analisis/teyolia-direct-to-pool.html` la gráfica dependía de Chart.js y el
flujo de fondos dependía de controladores inline. Se conservaron los datos
exactos del JavaScript publicado:

| Concepto original | Valor original |
| --- | ---: |
| Liquidez para THORChain | 99 |
| Infraestructura xolosArmy (1%) | 1 |

La gráfica circular se sustituyó por un medidor HTML nativo y una tabla
accesible con porcentajes. Los tres pasos se convirtieron a `details`/`summary`;
conservan los rótulos, descripciones, estados e iconos originales y funcionan
sin JavaScript. El primer paso permanece abierto inicialmente. Los otros dos
textos, que antes sólo aparecían después de pulsar un botón, ahora forman parte
del HTML. No se introdujeron cifras ni estados nuevos.

El botón «Apoyar a xolosArmy» no tenía enlace, formulario ni controlador.
Su texto se conservó como párrafo para evitar presentar un control inoperante.
Las afirmaciones periodísticas, el hash abreviado y los estados publicados en
esa pieza se conservan tal como existían: esta migración no los reclasifica
como evidencia técnica verificada.

## Contrato con el generador

El generador puede trasladar un titular o bajada a su encabezado común y
retirar únicamente su duplicado textual exacto del fragmento. Debe verificar
la presencia del texto original en la página completa, no exigir que conserve
su posición anterior. Una firma, fecha o rótulo ambiguo se conserva y se
documenta en el catálogo; el extractor no decide su clasificación.

Las 61 normalizaciones de metadatos de `editorial/metadata-removals.json`
identifican además un nodo exacto del fragmento mediante XPath y `expectedText`.
Su información se presenta en los campos comunes del nuevo encabezado:
género, rótulo histórico, autor, fecha, sección, temas o lectura. Se conserva
literalmente el origen en los fragmentos y en el manifest. Los géneros
ambiguos continúan pendientes con su rótulo histórico; esta normalización no
decide su clasificación.

Los IDs de los fragmentos se deben conservar. Un índice nuevo puede añadir
IDs a encabezados que no los tengan; no debe sustituir anchors existentes.

Clases disponibles para la presentación compartida:

| Clase | Uso |
| --- | --- |
| `editorial-legacy-image` | Fondo editorial materializado como imagen |
| `article-translations` | Versiones del artículo ya enlazadas en el original |
| `editorial-step` | Paso interactivo mediante details nativo |
| `editorial-data-chart` | Medidor y tabla del dataset publicado |
| `references`, `sources`, `links` | Secciones de referencias existentes |
| `evidence-strip`, `evidence-grid` | Recuadros de evidencia ya publicados |

El índice, las figuras y las fuentes deben estilizarse dentro del contenedor
de lectura. No es seguro interpretar todo `aside` como una referencia, ni
clasificar cualquier URL de GitHub como evidencia verificada. Los límites de
comprobación ya escritos forman parte del contenido que se debe preservar.

## Manifest de comprobación

`editorial/preservation.json` registra por artículo:

- hash del documento base y hash del fragmento extraído;
- segmentos de texto, títulos y anchors;
- enlaces, imágenes y sus atributos textuales;
- fuentes de multimedia y contenido exacto de código;
- shell retirado, estilos eliminados y fondos materializados;
- dataset original de la única visualización dinámica;
- resultado de la comprobación de preservación.

La extracción falla si pierde texto original o cambia enlaces, imágenes,
multimedia o código. Los assets localizados y las reparaciones técnicas de
enlaces posteriores deben comprobarse mediante su mapping explícito, sin
alterar este registro del origen. `content/` contiene fuentes de generación:
no debe aparecer en el sitemap ni tratarse como una segunda publicación.

La verificación de los HTML finales es reproducible con:

```sh
python scripts/extract_legacy.py --verify-generated --output .
```

Este modo no modifica archivos. Comprueba los 43 artículos dentro del landmark
principal, incluyendo el texto de los pasos de Teyolia que antes dependía de
JavaScript. Valida texto, enlaces con sus rótulos, código exacto, imágenes con
sus alt, multimedia y anchors. Acepta el mapping explícito de medios y la
reparación del enlace antiguo de archivo. Permite omitir únicamente dos fondos
decorativos Unsplash que devuelven HTTP 404; sus URLs permanecen documentadas
en el reporte y el manifest. No permite omitir imágenes de evidencia ni
sustituirlas por otra escena. Termina con código de salida distinto de cero
si detecta pérdida de contenido o si el inventario deja de tener 43 artículos.

Para aceptar una normalización de metadatos, el gate comprueba el hash del
fragmento, la coincidencia única del XPath y del texto esperado, la existencia
de cada campo declarado en el catálogo y su representación en el componente
correcto del encabezado. También verifica que todos los términos del rótulo
original estén cubiertos por esos campos; permite únicamente diferencias de
mayúsculas, acentos, puntuación, formato de fecha y las traducciones explícitas
`News`/`Noticia` y `Technical Analysis`/`Análisis técnico`. No permite utilizar
esta excepción para retirar nodos con enlaces, imágenes, código, tablas,
citas o encabezados. El texto restante conserva su comparación literal.
