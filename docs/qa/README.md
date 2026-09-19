# Verificación del sistema editorial

**Resultado final: 136/136 comprobaciones de navegador aprobadas.** La ejecución corresponde al commit `39f378c81465cd332c2884ba3571193c04bb6e59`, comparado con la base inmutable `7b5cc72c05ee9deb74f26ff85edd209ee2d9b511`.

- [GitHub Actions: ejecución 35450868683](https://github.com/xolosArmy/ecash-magazine/actions/runs/35450868683).
- Artefacto completo: `10587040638`, publicado por esa ejecución; contiene los PNG originales y los informes completos de Lighthouse y axe.
- [Resumen compacto y procedencia](final/ci-summary.json).
- [Capturas antes/después](screenshots/capturas.md).

Las pruebas se ejecutaron en un runner de GitHub sobre copias HTTP locales de ambas revisiones. No representan un despliegue ni datos de campo de producción.

## Resultados comprobados

| Verificación | Antes | Después | Método |
|---|---:|---:|---|
| Artículos alcanzables desde portada | 9/43 | 43/43 | Recorrido de enlaces HTML, sin JavaScript |
| Artículos enlazados desde archivo | 0/43 | 43/43 | Enlaces de `/blog/index.html` |
| URLs HTML históricas conservadas | 45 | 45/45 | Archivos y respuestas HTTP 200 en CI |
| Catálogo común | Ausente | 43 artículos, sin URLs duplicadas | JSON y documentos de destino |
| HTML y accesibilidad de marcado | 30 errores en 14/45 páginas | 0 errores y advertencias en 173 páginas | html-validate 11.16.0, `standard,a11y` |
| Estructura, enlaces, recursos y SEO | Fallos de archivo, SEO y enlaces | 65/65 | `scripts/verify_site.py` |
| Preservación editorial | Base de comparación | 43/43 artículos y 61/61 normalizaciones | Texto, código, enlaces, imágenes, multimedia y anchors |
| Menú, filtros e índice de búsqueda diferido | Sin sistema común | 52/52 | jsdom 30.1.0 |
| Navegador, responsive y accesibilidad renderizada | Base de comparación | 136/136 | Chromium 151.0.7922.34, Playwright y axe |
| Contraste de tokens de texto | No medido en esta prueba | 16/16 AA; mínimo 4.82:1 | Luminancia sRGB WCAG |

Las 173 páginas incluyen las 45 históricas y los nuevos índices de descubrimiento. La verificación estática cubre catálogo, vocabulario de géneros, títulos y géneros frente al catálogo, relacionados, rutas y fragmentos internos, imágenes sociales, `srcset`, fuentes CSS, documento/viewport/landmarks/IDs/alt, encabezados, canonical, metadata, schema, sitemap y RSS.

## Navegador y accesibilidad

Se comprobaron portada, principal y archivo a **320, 390, 768, 1440 y 1920 px**. Los **43 artículos** pasaron la revisión de desbordamiento horizontal a 390 px. Las pruebas reales verificaron acceso por teclado, enlace de salto al contenido, foco visible, menú móvil, Escape, búsqueda de texto completo, filtros, ausencia de resultados, reinicio, descarga diferida y recuperación ante fallo del índice. Sin JavaScript, el archivo conserva las 43 fichas y la navegación móvil permanece disponible.

Las primeras comprobaciones reales detectaron tres desbordamientos de imágenes: el principal a 320 px y dos versiones de una noticia con una captura de 576 px. Se corrigió el límite responsive conservando los archivos originales. También se adelantó la inicialización del menú a antes del cuerpo para evitar un desplazamiento de layout al colapsarlo después de la primera pintura. Las regiones desplazables de código recibieron contenedores nativos y nombres únicos.

Las auditorías axe finales sobre portada, principal, P2SH, Teyolia, archivo y buscador no detectaron violaciones WCAG en los escenarios probados. Queda **una comprobación automática incompleta**: contraste del símbolo no textual `✔` de Teyolia (`.text-green-600`). No se presenta ese resultado como certificación completa de accesibilidad ni como un fallo contrastado de contenido textual.

En las páginas nuevas no hubo errores inesperados de consola ni de recursos propios. El fallo de descarga del índice se provocó deliberadamente en un caso y su fallback fue comprobado. Los ocho registros de error externo pertenecen exclusivamente a la versión anterior: respuestas Imgur 403 y sus mensajes de consola para el logo y la fotografía P2SH, en escritorio y móvil. Las solicitudes canceladas al cambiar de página se registran aparte. Estos resultados están en [browser-summary.json](final/browser-summary.json).

## Lighthouse móvil: comparación de la misma ejecución

Lighthouse 13.5.0; una corrida por documento y revisión, con emulación móvil y el mismo servidor local sin compresión. Los recursos externos anteriores conservaron su comportamiento de red. Son métricas de laboratorio; no son Core Web Vitals de campo ni garantizan esos tiempos en todos los dispositivos.

| Métrica | Portada antes → después | Principal antes → después |
|---|---:|---:|
| Rendimiento | **73 → 99** | **72 → 98** |
| Accesibilidad automatizada | 91 → 100 | 100 → 100 |
| Buenas prácticas | 96 → 100 | 92 → 100 |
| SEO | 100 → 100 | 100 → 100 |
| FCP | 2.476 → 1.353 s | 4.120 → 1.354 s |
| LCP | **3.445 → 1.878 s** | **5.047 → 1.504 s** |
| CLS | **0.268519 → 0.000139** | **0 → 0.092667** |
| Tiempo total de bloqueo | 137 → 44 ms | 42 → 36.5 ms |
| Peso total observado | 265,416 → 483,862 B | 417,954 → 299,482 B |

La portada entrega más contenido e imágenes, y su peso observado aumenta. Además, los 403 de Imgur en la referencia condicionan la comparación de transferencia y capturas. No se afirma una reducción general del peso ni una mejora de todas las métricas: el CLS del principal pasa de 0 a 0.092667. Los informes completos permiten revisar cada medición; sus cifras compactas y límites están en [ci-summary.json](final/ci-summary.json).

## Reproducción y archivos conservados

```sh
python -m pip install -r requirements-dev.txt
python scripts/build_site.py
git diff --exit-code
test -z "$(git ls-files --others --exclude-standard)"
python scripts/verify_site.py --baseline /ruta/a/copia-inicial --report docs/qa/structural-after.json
python scripts/extract_legacy.py --verify-generated --output .
npm ci --prefix qa
npm run --prefix qa html
NODE_PATH=qa/node_modules node docs/qa/check-interactions.cjs
```

La ejecución de navegador está definida en `.github/workflows/editorial-qa.yml` y requiere un entorno que permita Chrome y servidores HTTP locales. El bloqueo del runtime de trabajo y su resolución mediante CI se documentan en [browser-environment.md](browser-environment.md).

`final/` conserva los resultados compactos de navegador, estructura, preservación, DOM y HTML, más un resumen de axe/Lighthouse con referencia al run y SHA. Los informes completos y PNG originales permanecen en el artefacto de CI; las capturas optimizadas para revisión tienen su propio manifest. Los JSON anteriores fuera de `final/` son registros históricos de la verificación local, no los resultados finales de navegador.
