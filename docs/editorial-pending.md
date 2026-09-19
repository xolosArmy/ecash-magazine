# Catálogo editorial: trazabilidad y decisiones pendientes

Base de extracción: los 43 artículos publicados en la revisión `7b5cc72c05ee9deb74f26ff85edd209ee2d9b511`. Los dos índices existentes no son artículos. El catálogo conserva las 43 URLs, incluidos nombres de carpeta y la ruta `/reseñas/` con acento.

## Contrato y reglas

`editorial/catalog.json` es la fuente común para portada, archivo, búsqueda, filtros, páginas de autor/tema/género, relaciones, metadatos, sitemap y feed. `editorial/catalog.schema.json` describe su contrato JSON Schema 2020-12. Se añadieron `sourceRevision`, `sourcePath`, `language`, `evidenceLimitations` y `editorialNote` opcional para conservar trazabilidad y límites.

- `null` significa dato ausente o ambiguo, nunca una afirmación negativa. `pendingMetadata` enumera esos campos. `classificationStatus` describe únicamente la decisión sobre el género.
- `title` es el H1 original, con espacios normalizados. `summary` es una bajada existente y literal; no se escribió ni resumió contenido nuevo.
- `genre` sólo usa los nueve géneros autorizados o `null`. La carpeta, el contenido del cuerpo, la posición en portada y el schema no bastan para deducirlo.
- Se normalizan literalmente `News` y `Noticias` a Noticia; `Technical Analysis` a Análisis técnico; `Reportaje técnico` a Reportaje; `Reseña · Evaluación de Producto` a Reseña. «Reportaje; Investigación correlacional» conserva Reportaje por su declaración explícita. La etiqueta original se conserva.
- `topics` y `tags` sólo contienen rótulos de cabecera, etiquetas publicadas o keywords del JSON-LD original. No se generan desde nombres de carpeta, frecuencia de palabras o lectura del cuerpo. La sección sólo se toma de un rótulo visible inequívoco.
- `author` conserva firmas existentes. «Colaborador Editorial» y «EMG Technical Team» tienen `type:null`; no se convierten en personas. Fernando Ramírez ya aparece como Person en JSON-LD publicado. La marca editorial se reconoce como organización.
- Las fechas proceden de metadata publicada o una ficha editorial inequívoca. No se usan mtime, commits, slugs ni fechas de acontecimientos. `updatedAt` idéntica a publicación conserva el dato original, sin anunciar una actualización nueva.
- `readingMinutes` sólo conserva «Lectura: 9 minutos» en la pieza sobre binarios. No hay estimaciones nuevas.
- `image` conserva imagen editorial o metadata social existente; excluye logo/favicon e imágenes usadas exclusivamente como documentación de correspondencia. Dimensiones locales se miden en el archivo real. Un alt ausente sigue `null` y pendiente; no se redacta de oficio.
- `references[].url` puede ser `null`: documentos e identificadores ya publicados sin enlace no reciben una URL inventada. `locator` conserva un hash o TXID literal. `kind` identifica tipos literales de ruta/identificador.
- `references[].category` distingue fuente primaria explícita, referencia secundaria explícita o identificador técnico. Un dominio oficial por sí solo no convierte una referencia en primaria. Si el texto no clasifica la referencia, la categoría queda `null`.
- Un identificador técnico confirma su naturaleza como commit/PR/TXID/bloque, no la validez de lo afirmado. No se presenta esta migración como una auditoría nueva de los repositorios o transacciones citados.
- `evidenceLimitations` conserva pasajes literales sobre límites de comprobación. Las notas y evidencias originales siguen en el cuerpo.
- `related` sólo contiene enlaces existentes a otros artículos del catálogo. Cualquier recomendación de interfaz por etiquetas compartidas debe distinguirse de esta relación documentada y no escribir relaciones inferidas en el catálogo.

## Estado comprobado

- 43 artículos y 43 URLs únicas; los 43 H1 coinciden con el inventario auditado.
- 18 géneros confirmados; 25 decisiones de género pendientes.
- 16 firmas publicadas; 27 artículos sin firma inequívoca.
- 19 fechas de publicación documentadas; 24 pendientes.
- 11 fechas de modificación documentadas; no se asigna la fecha de este trabajo a artículos antiguos.
- 1 duración de lectura publicada; las demás permanecen vacías.
- 133 referencias conservadas con trazabilidad, de ellas 9 sin URL publicada.

## Decisiones de género pendientes

| URL | Rótulo observado | Decisión necesaria |
| --- | --- | --- |
| `/analisis/proof-of-stake-2011-ecash-avalanche-hibrido.html` | Análisis histórico-técnico | Se publica como «Análisis histórico-técnico» y JSON-LD TechArticle / articleSection «Análisis». Falta aprobación para su equivalencia con Análisis técnico. |
| `/analisis/teyolia-direct-to-pool.html` | Especial: Infraestructura XEC | «Especial: Infraestructura XEC» identifica un especial y su tema; no declara uno de los nueve géneros. |
| `/blog/npm-xolosarmy-tonalli-core-ecash-mexico.html` | Noticia + Análisis Técnico | Cabecera híbrida «Noticia + Análisis Técnico»; elegir un género requiere decisión editorial o división sustantiva fuera de este PR. |
| `/blog/xolosarmy-despliega-stack-de-infraestructura-soberana-ecash-mexico.html` | Boletín de Infraestructura; Ficha de Noticia Ampliada | «Boletín de Infraestructura» y «Ficha de Noticia Ampliada» no constituyen una clasificación inequívoca de toda la pieza. |
| `/columna/2026-06-02-precio-ecash-xec.html` | Análisis de Mercado | Cabecera «Análisis de Mercado» dentro de /columna/. No se convierte en Columna ni Análisis técnico por directorio o interpretación. |
| `/columna/gnc-ecash-irrelevance-crypto-winter.html` | Opinion; Analysis Column | Cabecera «Opinion» y ficha «Analysis Column»; Opinión y Columna son géneros distintos del manual. |
| `/cronica/2026-06-16-xolosarmy-weekly-update.html` | Crónica-Análisis | La cabecera dice «Crónica-Análisis», género híbrido. |
| `/cronica/alias-ecash-mexico.html` | Crónica + Análisis Técnico | La cabecera combina «Crónica + Análisis Técnico». |
| `/cronica/asamblea-rmz-governanza-ecash-mexico.html` | Crónica + Análisis Técnico | La cabecera combina «Crónica + Análisis Técnico». |
| `/cronica/compra-parcial-rmz-tonalli-wallet.html` | Crónica + Análisis Técnico | La cabecera combina «Crónica + Análisis Técnico». |
| `/cronica/integracion-xec-thorchain.html` | Crónica + Análisis Técnico | La cabecera combina «Crónica + Análisis Técnico». |
| `/cronica/liquidez-soberana-ecash-xec-thorchain.html` | Crónica-Análisis | La cabecera dice «Crónica-Análisis»; el documento original además era un fragmento HTML. |
| `/cronica/oraculo-tonalli-app-ecash-mexico.html` | Reportaje + Análisis Técnico | La cabecera dice «Reportaje + Análisis Técnico» aunque la carpeta sea /cronica/. |
| `/cronica/xolosarmy-thorchain-podcast.html` | Crónica / Análisis | La cabecera combina «Crónica / Análisis». |
| `/cultura/sin-cultura-no-hay-adopcion.html` | Cultura // Tesis; ensayo | «Cultura // Tesis» y descripción «ensayo»; Cultura es sección, no género, y Ensayo no está entre los nueve solicitados. |
| `/noticia/cashaddr-decode-oob-bitcoinabc-tonalli-wallet.html` | Seguridad | «Seguridad» es sección; no hay género explícito. /noticia/ no se usa como evidencia de género. |
| `/noticia/xolosarmy-technical-governance-review-package-teyolia-xec-rune-liquidity-bootstrap.html` | Technical Note · Draft v0.1 · Review Request | «Technical Note · Draft v0.1 · Review Request» no equivale inequívocamente a Noticia. |
| `/opinion/rothbard-ecash-bitcoinabc-xolosarmy-jurisdiccion.html` | Opinión; nota: columna | Cabecera «Opinión» pero p.disclaimer afirma «Esta columna»; resolver Opinión frente a Columna sin suposición. |
| `/opinion/tonalli-shield-ia-evidencia-rbitcoin.html` | Opinión; nota: columna de opinión | Cabecera y schema dicen Opinión, pero la nota editorial dice «columna de opinión»; resolver Opinión frente a Columna. |
| `/reportajes/avalanche-stakers-tonalli-core-roadmap-publico.html` | Investigación exploratoria | Cabecera «Investigación exploratoria», schema AnalysisNewsArticle / articleSection «Reportajes» y ubicación en Grandes Reportajes. No se impone Reportaje desde la sección. |
| `/reportajes/firma-alpha-tonalli-wallet-mainnet-agora.html` | Investigación técnica; Auditoría de infraestructura financiera | Cabecera «Investigación técnica» / «Auditoría de infraestructura financiera», schema TechArticle / articleSection «Reportajes» y texto que menciona reportaje. Requiere una clasificación única. |
| `/reportajes/firma-wallet-seed-tonalli-interoperabilidad-mainnet.html` | Prueba mainnet; Rampa fiat → eCash probada con fondos reales | Cabecera «Investigación técnica», schema TechArticle y articleSection «Reportajes». La sección y el tipo schema no resuelven el género. |
| `/reportajes/tonalli-faucet-ecash-mexico.html` | Reportaje · Análisis Técnico | La cabecera combina «Reportaje · Análisis Técnico». |
| `/reportajes/tonalli-memo-alias-xec-identidad-agentes-humanos.html` | Primera Plana · Identidad | Cabecera «Primera Plana · Identidad», schema NewsArticle y colocación en Grandes Reportajes. Primera Plana es posición; la evidencia de género es contradictoria. |
| `/reportajes/tonalli-memo-mainnet-capa-social-ecash.html` | Primera Plana · Infraestructura | Cabecera «Primera Plana · Infraestructura», schema NewsArticle y carpeta /reportajes/. Ninguno fija inequívocamente el género visible. |

## Inventario completo de datos pendientes

Los campos vacíos no se rellenan para conseguir una tarjeta visualmente uniforme. La interfaz debe omitirlos o mostrar una indicación honesta de clasificación pendiente. «Actualización pendiente» significa fecha no documentada, no que el texto deba actualizarse.

| Artículo | Género | Autor | Publicación | Otros datos pendientes |
| --- | --- | --- | --- | --- |
| `/analisis/bitcoin-abc-corrige-error-raro-en-chronik-en-ultima-version.html` | Análisis técnico | Pendiente | Pendiente | sección, fecha de actualización, imagen editorial, lectura, temas |
| `/analisis/ecash-mining-variance.html` | Análisis técnico | eCash Magazine México | Pendiente | sección, fecha de actualización, imagen editorial, lectura, temas, clasificación de referencias |
| `/analisis/gobernanza-rmz-ecash-mexico.html` | Análisis técnico | Pendiente | Pendiente | sección, fecha de actualización, imagen editorial, lectura, temas |
| `/analisis/multifirma-tonalli-wallet-bovedas-p2sh-ecash.html` | Análisis técnico | Pendiente | Pendiente | sección, fecha de actualización, lectura, clasificación de referencias |
| `/analisis/proof-of-stake-2011-ecash-avalanche-hibrido.html` | Pendiente | Pendiente | 2026-08-09 | imagen editorial, lectura, clasificación de referencias |
| `/analisis/teyolia-2-1-direct-to-pool.html` | Análisis técnico | Pendiente | Pendiente | sección, fecha de actualización, imagen editorial, lectura |
| `/analisis/teyolia-direct-to-pool.html` | Pendiente | Pendiente | Pendiente | fecha de actualización, imagen editorial, lectura |
| `/blog/2026-05-29-xolosarmy-weekly-update.html` | Crónica | Pendiente | Pendiente | sección, fecha de actualización, imagen editorial, lectura |
| `/blog/npm-xolosarmy-tonalli-core-ecash-mexico.html` | Pendiente | Pendiente | Pendiente | sección, fecha de actualización, bajada, lectura, temas |
| `/blog/xolosarmy-despliega-stack-de-infraestructura-soberana-ecash-mexico.html` | Pendiente | Pendiente | Pendiente | sección, fecha de actualización, bajada, lectura, temas |
| `/columna/2026-06-02-precio-ecash-xec.html` | Pendiente | eCash Magazine México | 2026-06-02 | sección, fecha de actualización, imagen editorial, lectura, temas |
| `/columna/gnc-ecash-irrelevance-crypto-winter.html` | Pendiente | eCash Magazine México | Pendiente | fecha de actualización, imagen editorial, lectura |
| `/cronica/2026-06-16-xolosarmy-weekly-update.html` | Pendiente | Pendiente | Pendiente | sección, fecha de actualización, imagen editorial, lectura, temas |
| `/cronica/alias-ecash-mexico.html` | Pendiente | Pendiente | Pendiente | sección, fecha de actualización, imagen editorial, lectura, temas |
| `/cronica/asamblea-rmz-governanza-ecash-mexico.html` | Pendiente | Pendiente | Pendiente | sección, fecha de actualización, imagen editorial, lectura, temas, clasificación de referencias |
| `/cronica/compra-parcial-rmz-tonalli-wallet.html` | Pendiente | Pendiente | Pendiente | sección, fecha de actualización, imagen editorial, lectura, temas |
| `/cronica/integracion-xec-thorchain.html` | Pendiente | Pendiente | Pendiente | sección, fecha de actualización, imagen editorial, lectura, temas |
| `/cronica/liquidez-soberana-ecash-xec-thorchain.html` | Pendiente | Pendiente | 2026-06-17 | sección, fecha de actualización, imagen editorial, lectura, temas |
| `/cronica/oraculo-tonalli-app-ecash-mexico.html` | Pendiente | Pendiente | Pendiente | sección, fecha de actualización, imagen editorial, lectura, temas |
| `/cronica/xolosarmy-thorchain-podcast.html` | Pendiente | EMG Technical Team | Pendiente | sección, fecha de actualización, imagen editorial, lectura, temas, clasificación de referencias |
| `/cultura/sin-cultura-no-hay-adopcion.html` | Pendiente | Fernando Ramírez | 2026-07-06 | fecha de actualización, lectura, clasificación de referencias, imagen editorial |
| `/editorial/ecash-mexico-machine-economy.html` | Análisis técnico | Fernando Ramírez | 2026-06-25 | sección, fecha de actualización, lectura, alt de imagen social |
| `/noticia/cashaddr-decode-oob-bitcoinabc-tonalli-wallet.html` | Pendiente | Redacción técnica · eCash Magazine México | 2026-08-29 | fecha de actualización, imagen editorial, lectura, clasificación de referencias |
| `/noticia/comunicaciones-integracion-xec-thorchain-con-teyolia.html` | Noticia | Pendiente | Pendiente | sección, fecha de actualización, imagen editorial, lectura, temas, clasificación de referencias |
| `/noticia/comunications-integration-xec-thorchain-with-teyolia.html` | Noticia | Pendiente | Pendiente | sección, fecha de actualización, imagen editorial, lectura, temas, clasificación de referencias |
| `/noticia/mexico-kyc-aml-cripto-transferencias-2026.html` | Noticia | Pendiente | 2026-08-12 | imagen editorial, lectura, clasificación de referencias |
| `/noticia/xolosarmy-technical-governance-review-package-teyolia-xec-rune-liquidity-bootstrap.html` | Pendiente | Pendiente | Pendiente | sección, fecha de actualización, imagen editorial, lectura, temas, clasificación de referencias |
| `/opinion/economia-agentica-tokenizada.html` | Opinión | Colaborador Editorial | Pendiente | sección, fecha de actualización, imagen editorial, lectura, temas |
| `/opinion/finalidad-puente-drivechains-subnets-tonalli-shield.html` | Opinión | Fernando Ramírez | 2026-09-09T00:00:00-06:00 | imagen editorial, lectura, clasificación de referencias |
| `/opinion/ia-binarios-open-source-nueva-ventaja.html` | Opinión | Fernando Ramírez | 2026-09-05T00:00:00-06:00 | clasificación de referencias |
| `/opinion/ia-y-codigo-verificable-en-cripto.html` | Opinión | Fernando Ramírez | Pendiente | sección, fecha de actualización, lectura, temas, clasificación de referencias, alt de imagen social |
| `/opinion/rothbard-ecash-bitcoinabc-xolosarmy-jurisdiccion.html` | Pendiente | Colaborador Editorial | 2026-08-28 | sección, fecha de actualización, imagen editorial, lectura, clasificación de referencias |
| `/opinion/tonalli-shield-ia-evidencia-rbitcoin.html` | Pendiente | Fernando Ramírez | 2026-08-20 | lectura, clasificación de referencias, alt de imagen social |
| `/reportajes/avalanche-stakers-tonalli-core-roadmap-publico.html` | Pendiente | Fernando Ramírez | 2026-08-24 | imagen editorial, lectura, clasificación de referencias |
| `/reportajes/bip-110-bitcoin-cash-forks-consenso.html` | Reportaje | Pendiente | 2026-08-09 | sección, lectura, clasificación de referencias |
| `/reportajes/firma-alpha-tonalli-wallet-mainnet-agora.html` | Pendiente | Pendiente | 2026-08-10 | sección, imagen editorial, lectura, clasificación de referencias |
| `/reportajes/firma-wallet-seed-tonalli-interoperabilidad-mainnet.html` | Pendiente | Pendiente | 2026-08-14 | sección, imagen editorial, lectura, clasificación de referencias |
| `/reportajes/tonalli-faucet-ecash-mexico.html` | Pendiente | Pendiente | Pendiente | sección, fecha de actualización, lectura, alt de imagen social |
| `/reportajes/tonalli-memo-alias-xec-identidad-agentes-humanos.html` | Pendiente | Pendiente | 2026-09-14 | lectura |
| `/reportajes/tonalli-memo-mainnet-capa-social-ecash.html` | Pendiente | Pendiente | 2026-09-10 | imagen editorial, lectura, clasificación de referencias |
| `/reportajes/xec-client-utxo-real-thornode.html` | Análisis técnico | eCash Magazine México | 2026-08-16 | fecha de actualización, imagen editorial, lectura, clasificación de referencias |
| `/reportajes/xec-thorchain-starsquid-xec-client.html` | Reportaje | eCash Magazine México | 2026-08-16 | fecha de actualización, imagen editorial, lectura, clasificación de referencias |
| `/reseñas/como-comprar-etoken-cultural-xolos-rmz.html` | Reseña | Pendiente | Pendiente | fecha de actualización, imagen editorial, lectura |

## Casos de fecha e imagen que requieren atención

- `blog/2026-05-29-xolosarmy-weekly-update.html`: cabecera 28 de mayo, transmisión del mismo día y slug 29 de mayo. No se decide cuál es la fecha de publicación.
- `analisis/multifirma-tonalli-wallet-bovedas-p2sh-ecash.html`: el corte metodológico del 31 de julio no se usa como publicación.
- `blog/xolosarmy-despliega-stack-de-infraestructura-soberana-ecash-mexico.html`: «Publicación Oficial Actualizada — Mayo 2026» sólo aporta un mes; falta fecha inequívoca para publicar y actualizar.
- `cronica/xolosarmy-thorchain-podcast.html`: la firma aporta sólo «2026 (Tiempo de Red)».
- `noticia/xolosarmy-technical-governance-review-package-teyolia-xec-rune-liquidity-bootstrap.html`: sólo «July 2026»; la marca en esa ficha tampoco es una firma atribuida explícitamente.
- `reportajes/tonalli-memo-alias-xec-identidad-agentes-humanos.html`: la imagen declaraba 768 × 512, pero el archivo publicado real mide 320 × 213. El catálogo usa el tamaño medido; no se inventa una imagen de alta resolución.
- `analisis/gobernanza-rmz-ecash-mexico.html`: el og:image declarado apuntaba a `/assets/img/og-gobernanza-rmz.jpg`, archivo inexistente. No se promueve a imagen válida.
- Los alt ausentes en metadata social no se sustituyen por descripciones inventadas.

## Temas y relaciones incompletos

Las piezas sin tags/rótulos temáticos permanecen accesibles en el archivo completo y en búsqueda textual. No deben desaparecer porque carezcan de clasificación. Una página de tema no representa una taxonomía editorial completa: reúne las etiquetas comprobadas. No se han añadido biografías, perfiles externos, credenciales ni fotografías de autores.

La inexistencia actual de piezas inequívocas de Entrevista, Columna o Editorial no autoriza a rellenar esos módulos. Breves necesita una designación editorial real o nuevas publicaciones; no se determina por longitud ni por duración de lectura.

## Mantenimiento

Para corregir un dato pendiente, incorporar primero evidencia editorial verificable, actualizar su campo y `metadataProvenance`, retirar la entrada correspondiente de `pendingMetadata`, ejecutar la generación y validar el conjunto. Publicar una corrección periodística sustantiva sigue siendo una decisión editorial distinta de regenerar metadatos.
