# Informe de implementación editorial

Estado de revisión: implementación, verificación estática y comprobación real de navegador completadas. La ejecución final de GitHub Actions aprobó 136/136 checks. No se ha hecho merge ni modificado la publicación en producción.

Base: `7b5cc72c05ee9deb74f26ff85edd209ee2d9b511`.
Implementación verificada: `39f378c81465cd332c2884ba3571193c04bb6e59` en `feat/editorial-magazine-evolution`.
La relación exacta de rutas incorporadas o modificadas está en [changed-files.txt](changed-files.txt).

## Problema resuelto y alcance

La portada anterior permitía alcanzar nueve de los 43 artículos mediante navegación interna. El archivo no enlazaba ninguno. El nuevo archivo contiene los 43 y todos son alcanzables desde portada sin JavaScript. Se conservan las 45 URLs HTML históricas: 43 artículos y los dos índices existentes. La salida actual comprende 173 documentos HTML, incluidos 128 documentos nuevos de descubrimiento, principios, correcciones y error 404; el sitemap contiene las 172 URLs indexables.

El sitio continúa siendo HTML estático en GitHub Pages. La generación utiliza Python con lxml como dependencia de desarrollo. Las herramientas Node de QA están aisladas en `qa/` y excluidas de la publicación. No se introdujo un framework de frontend, servidor de aplicación, base de datos ni migración de hosting.

## Catálogo y componentes comunes

`editorial/catalog.json` contiene exactamente 43 registros; su contrato está en `editorial/catalog.schema.json`. Cada registro conserva URL, título y, cuando existe evidencia de origen, género, sección, temas, firma, fechas, bajada, imagen, etiquetas, lectura y referencias. Incluye procedencia por campo, revisión de origen, rótulos históricos, datos pendientes y límites de comprobación.

`null` conserva una ausencia o ambigüedad; no la resuelve por contexto. Los géneros usan exclusivamente los nueve valores autorizados. Ni carpetas, slugs, fechas de archivos ni frecuencia de palabras asignan género, fecha, autor o tema. Sólo una pieza tenía tiempo de lectura explícito; no se calcularon tiempos nuevos para completar fichas.

El catálogo y los cuerpos preservados generan:

- Primera Plana, archivo completo, búsqueda y últimas publicaciones.
- Índices de géneros y temas; 107 temas conservados y cinco perfiles de firma, sin biografías inventadas.
- Tarjetas, fichas de lectura, breadcrumbs, relaciones entre publicaciones y archivo agrupado por las fechas de publicación comprobadas. No se implementaron enlaces de artículo anterior/siguiente.
- Canonical, metadata social, schema, sitemap y RSS.

`editorial/frontpage.json` mantiene la selección explícita del principal. `content/` guarda los cuerpos fuente en sus rutas históricas. `editorial/media-map.json` relaciona imágenes originales con variantes locales. `scripts/build_site.py` genera las páginas completas. `_config.yml` excluye fuentes, scripts, QA y documentos de revisión, conservando el artículo histórico bajo `/editorial/`.

## Portada y lectura

La Primera Plana tiene un principal tipográfico dominante y un bloque secundario de últimas publicaciones. Después aparecen Últimas noticias, Grandes Reportajes, Análisis técnico, Crónicas, Cultura y Opinión / Columnas, con escalas y composiciones distintas. El principal no se repite en otra tarjeta. El acceso al archivo completo es explícito.

No se fabricaron Entrevistas ni Breves: faltan registros con clasificación comprobada para alimentar esos módulos. La pieza radiofónica existente aparece como «Radio y conversaciones», sin atribuirle género Entrevista. Los artículos con clasificación pendiente siguen accesibles y muestran su condición y el rótulo histórico disponible.

El sistema visual compartido define papel, tinta y cian, tipografía de lectura, escalas, espaciado, anchos, bordes y estados interactivos. Georgia se utiliza para titulares y cuerpo; Lexend local para navegación y fichas. La columna de lectura tiene máximo de 70 caracteres tipográficos (`70ch`), con adaptación a pantallas pequeñas. Se unificaron citas, captions, tablas, código, multimedia, notas y fuentes. Los textos con al menos cinco encabezados principales incorporan índice con anchors conservados.

La navegación móvil tiene control con estado expandido, cierre con Escape y devolución de foco. Su pequeña inicialización se inserta después de la cabecera y antes del cuerpo, para fijar el estado móvil antes de dibujar el contenido y evitar un salto de layout. Sin JavaScript permanecen disponibles navegación, lectura y los 43 registros del archivo. La búsqueda mejora progresivamente el HTML: filtros por género, tema, firma y año funcionan con las fichas existentes; el índice de texto completo se descarga sólo al escribir una consulta. Si falla esa descarga, continúa la búsqueda por título/ficha y se anuncia su alcance reducido.

## Fuentes, confianza y metadatos

«Fuentes y evidencia» presenta las referencias publicadas y sus localizadores, sin convertir su presencia en validación independiente. Admite fuente primaria, referencia secundaria y evidencia técnica, además de límites de comprobación. El catálogo conserva 133 referencias: 13 clasificadas como primarias, 20 como técnicas y 100 pendientes de clasificación. No se llenan categorías vacías con asignaciones supuestas.

Se repararon los dos canonicals inexistentes para que apunten a las URLs públicas ya existentes. Los 45 documentos históricos tienen ahora canonical, descripción, Open Graph, imagen social, Twitter card y viewport. El generador produce schema según género conocido, BreadcrumbList y Organization; Person se utiliza únicamente cuando la naturaleza de la firma está documentada. Una firma organizacional o no identificada no se convierte en persona.

Se reconstruyó el sitemap completo y se añadió `/feed.xml` con las 43 publicaciones. El RSS sólo emite `pubDate` cuando existe fecha con hora y zona; no inventa medianoche. El rediseño no cambia fechas editoriales ni utiliza la fecha de compilación como actualización periodística.

La configuración conserva la analítica anterior únicamente en las 31 rutas que ya la incluían. No añade seguimiento a nuevas rutas.

## Preservación y reparaciones técnicas

El gate de preservación pasa para los 43 artículos. Comprueba texto, enlaces y rótulos, imágenes y alt, multimedia, código y anchors contra la base inmutable. El inventario incluye 188 enlaces, cuatro elementos multimedia y 229 bloques o fragmentos de código. Las 61 normalizaciones de fichas repetidas tienen selector y texto exacto de origen; trasladan información a la cabecera común y se verifican individualmente. Los cuerpos fuente y el manifest conservan su procedencia literal.

Las reparaciones estructurales incluyen documento y viewport de la crónica incompleta; normalización de landmarks, jerarquía de encabezados y etiquetas accesibles; IDs de lectura conservados; y el enlace de archivo roto en el reportaje del faucet. Los estilos y scripts de presentación anteriores se sustituyeron por componentes comunes.

En la pieza de Teyolia, los datos originales de Chart.js —99 y 1— se materializaron en tabla y medidor HTML accesibles; sus tres pasos conservan exactamente el texto publicado mediante `details`/`summary`. No se corrigieron afirmaciones periodísticas, números, citas, opiniones ni estados técnicos por criterio de esta migración. El detalle de transformaciones está en [content-preservation.md](content-preservation.md).

## Métricas comprobables

Estos son bytes de archivos, no transferencia medida en navegador. La columna comprimida se calculó con gzip nivel 9 y fecha fija, por igual en ambas versiones. No asegura la configuración de compresión de GitHub Pages.

| Documento | Bytes antes → después | Gzip reproducible antes → después |
|---|---:|---:|
| Portada | 9,011 → 19,813 | 3,411 → 5,193 |
| Archivo | 10,330 → 55,774 | 2,902 → 12,799 |
| Principal Tonalli Memo | 19,211 → 22,664 | 6,638 → 7,133 |
| Reportaje técnico P2SH | 48,002 → 65,746 | 14,264 → 15,765 |

La portada y el archivo contienen más navegación y contenido real; por eso su HTML crece. El archivo ahora entrega las 43 fichas completas. El índice de texto completo se separó para no incluirlo en la descarga inicial.

| Recurso compartido | Bytes de archivo | Gzip reproducible |
|---|---:|---:|
| CSS editorial | 34,840 | 6,942 |
| JavaScript de búsqueda | 6,077 | 2,104 |
| Fuente de navegación, insertada en el HTML | 989 | 457 |
| Índice de texto completo, carga diferida | 339,783 | 118,463 |
| Fuente Lexend WOFF2 | 39,680 | 39,713 |

El logo original pesaba 822,119 bytes. Sus variantes conservadas pesan 4,752 bytes a 256 px y 1,850 bytes a 128 px; la mayor reduce el peso del archivo un 99.4%. El nuevo masthead utiliza identidad tipográfica. Nueve páginas dejan de ejecutar Tailwind CDN; no queda Tailwind en ejecución. Las imágenes existentes disponen de variantes WebP y dimensiones reales; las capturas documentales conservan su detalle mediante copia o conversión sin pérdida.

La cobertura de imágenes Open Graph en las 45 URLs históricas pasa de 11 a 45; las descripciones de 38 a 45; los canonicals de 23 a 45. El sitemap pasa de 26 a 172 URLs, incluyendo los nuevos índices. El inventario y los bytes reproducibles están en [qa/static-metrics.json](qa/static-metrics.json); la procedencia y los pesos de medios están en [media-notes.md](media-notes.md).

## Verificación final

La [ejecución 35450868683 de GitHub Actions](https://github.com/xolosArmy/ecash-magazine/actions/runs/35450868683) probó el commit `39f378c81465cd332c2884ba3571193c04bb6e59` frente a la base inmutable. El artefacto `10587040638` contiene los PNG originales y los informes completos. Los [resultados compactos](qa/final/ci-summary.json) y las [capturas antes/después](qa/screenshots/capturas.md) quedan vinculados a esa ejecución.

| Gate | Resultado final |
|---|---|
| Estructura, catálogo, URLs, recursos, SEO, sitemap y RSS | 65/65 |
| Preservación de publicaciones y normalizaciones de ficha | 43/43 artículos; 61/61 normalizaciones |
| HTML y accesibilidad de marcado, 173 documentos | 0 errores y advertencias |
| Interacciones DOM, índice diferido y fallos de descarga | 52/52 |
| Navegador, responsive, teclado, axe y Lighthouse | **136/136** |
| Contraste matemático de tokens de texto | 16/16 AA; mínimo 4.82:1 |

Portada, principal y archivo se probaron a 320, 390, 768, 1440 y 1920 px. Los 43 artículos pasaron la comprobación de desbordamiento a 390 px; las 45 URLs históricas respondieron HTTP 200 en la copia de CI. Se verificaron teclado, enlace de salto, foco visible, menú, Escape, filtros, texto completo, estado vacío, reinicio, recuperación ante fallo de red y acceso sin JavaScript.

Las primeras ejecuciones detectaron desbordamiento de tres imágenes, desplazamiento tardío al colapsar la navegación y etiquetas ambiguas en regiones de código. Se corrigieron antes de la ejecución final. Las auditorías axe finales no registraron violaciones en los escenarios probados; quedó una comprobación incompleta de contraste del símbolo no textual `✔` de Teyolia. Esto no equivale a una certificación completa de accesibilidad.

No hubo errores inesperados propios en consola ni en recursos de las páginas nuevas. El caso de fallo del índice fue provocado y su recuperación comprobada. Ocho registros externos corresponden sólo a la referencia anterior: Imgur devolvió 403 para el logo y la fotografía P2SH en escritorio y móvil. Las solicitudes canceladas al navegar se registraron aparte.

### Lighthouse móvil de la misma ejecución

Lighthouse 13.5.0 y Chromium 151.0.7922.34, una corrida por revisión/documento sobre el mismo servidor HTTP local sin compresión. Los resultados son de laboratorio; no son Core Web Vitals de campo ni garantizan el comportamiento de todos los dispositivos.

| Métrica | Portada antes → después | Principal antes → después |
|---|---:|---:|
| Rendimiento | **73 → 99** | **72 → 98** |
| Accesibilidad automatizada | 91 → 100 | 100 → 100 |
| Buenas prácticas | 96 → 100 | 92 → 100 |
| SEO | 100 → 100 | 100 → 100 |
| LCP | **3.445 → 1.878 s** | **5.047 → 1.504 s** |
| CLS | **0.268519 → 0.000139** | **0 → 0.092667** |
| Tiempo total de bloqueo | 137 → 44 ms | 42 → 36.5 ms |
| Peso observado | 265,416 → 483,862 B | 417,954 → 299,482 B |

La portada contiene más contenido e imágenes y su peso observado crece. Los 403 de Imgur en la referencia también condicionan la comparación de transferencia y capturas. No se afirma que todas las métricas mejoren: el CLS del principal aumenta de 0 a 0.092667. Las cifras exactas, alcance de axe y errores de terceros están preservados en los reportes.

El navegador no pudo ejecutarse en el runtime inicial por restricciones de sockets. La comprobación se completó en el runner de GitHub sin alterar esas restricciones ni publicar la rama en producción. El [registro de entornos](qa/browser-environment.md) distingue ambos contextos.

## Decisiones editoriales y deuda restante

- **25 géneros pendientes, 27 firmas ausentes o ambiguas y 24 fechas de publicación pendientes.** Se documentan por URL y motivo en [editorial-pending.md](editorial-pending.md); ningún caso queda huérfano.
- **Tiempo de lectura:** sólo se muestra el dato explícitamente publicado; los demás permanecen pendientes.
- **Imagen principal Tonalli Memo de 320 × 213 px:** no existe un original mayor comprobable. La portada usa un principal tipográfico; la imagen pequeña se conserva sin ampliación engañosa en la lectura. Se necesita un archivo original de mayor resolución para un hero fotográfico grande.
- **Dos fondos decorativos Unsplash devuelven 404.** Se omiten únicamente esas imágenes rotas y se conservan sus URLs en el registro de procedencia; no se sustituyeron por escenas inventadas.
- **Taxonomía y evidencia:** los temas conservan rótulos previamente publicados. Unificar sinónimos, resolver géneros contradictorios y clasificar 100 referencias requiere decisión editorial explícita.
- **Validación factual y de enlaces externos:** conservar una referencia o una captura no equivale a verificar su afirmación; este PR no reescribe ni vuelve a investigar los artículos.
- **Accesibilidad y rendimiento:** axe deja una comprobación incompleta sobre el símbolo no textual de Teyolia. El CLS del principal es 0.092667 en esta corrida; las métricas de usuarios reales y pruebas exhaustivas de lectores de pantalla quedan fuera del alcance de esta ejecución automatizada.

No se borraron artículos ni se cambiaron URLs públicas. El contenido sustantivo, sus atribuciones y sus datos técnicos permanecen preservados. No se hizo merge ni se publicó esta rama en el dominio.
