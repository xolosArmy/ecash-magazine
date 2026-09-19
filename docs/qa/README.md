# Verificación del sistema editorial

Fecha: 2026-09-19. Estas pruebas se ejecutaron sobre los archivos generados de la rama; no representan un despliegue ni una medición de producción.

## Resultados comprobados

| Verificación | Antes | Después | Método |
|---|---:|---:|---|
| Artículos alcanzables desde portada | 9/43 | 43/43 | Recorrido de enlaces HTML, sin JavaScript |
| Artículos enlazados desde archivo | 0/43 | 43/43 | Enlaces de `/blog/index.html` |
| URLs HTML históricas conservadas | 45 | 45/45 | Comparación contra copia del repositorio inicial |
| Catálogo común | Ausente | 43 artículos, sin URLs duplicadas | JSON y documentos de destino |
| HTML y accesibilidad estática | 30 errores en 14/45 páginas | 0 errores, 0 advertencias en 173 páginas generadas | html-validate 11.16.0, presets `standard,a11y` |
| Validaciones estructurales | Fallos de archivo, SEO y enlaces | 65/65 | `scripts/verify_site.py` |
| Menú, filtros, búsqueda e índice diferido | No implementados de forma común | 52/52 | jsdom 30.1.0; prueba de comportamiento DOM |
| Contraste de tokens de texto | No medido en esta prueba | 16/16 combinaciones AA; mínimo 4.82:1 | Luminancia sRGB WCAG, sin render |

Las 173 páginas son las 45 históricas más índices y páginas de descubrimiento generadas. La validación estructural cubre catálogo, géneros admitidos, títulos y géneros visibles frente al catálogo, referencias relacionadas, rutas y fragmentos internos, recursos locales, imágenes sociales, `srcset`, fuentes CSS, documento/viewport/landmarks/IDs/alt, encabezados, canonical, metadata, schema, sitemap y RSS.

Las pruebas DOM cubren menú móvil, Escape y devolución de foco en el DOM; filtros por género, tema, autor y año; búsqueda sin distinción de acentos, URL compartible, historial, reinicio y estado vacío. El índice completo sólo se solicita cuando existe consulta textual: se comprueba caché, búsqueda de un término presente en el texto pero ausente de las fichas, error de carga con alcance reducido anunciado, cambio de consulta durante la carga y borrado de consulta con respuesta pendiente.

El contraste calculado de tokens no sustituye una auditoría de todos los estados renderizados. Las pruebas DOM no certifican geometría, navegación por teclado en un navegador real, lector de pantalla, consola real ni comportamiento visual responsive.

## Límites que impiden cerrar QA visual

El entorno impide crear los sockets requeridos por `agent-browser` y Chrome; Lighthouse tampoco pudo conectarse. Véase [browser-environment.md](browser-environment.md). No hay puntuaciones Lighthouse, mediciones de Core Web Vitals ni capturas antes/después fabricadas.

Queda pendiente renderizar y revisar teléfono de 320 y 390 px, tablet de 768 px, escritorio de 1440 px y pantalla de 1920 px; comprobar navegación real por teclado, foco, consola y solicitudes fallidas; ejecutar axe en navegador; y obtener capturas de portada, artículo y móvil antes/después. Estos pendientes deben resolverse antes de afirmar que el resultado visual está aprobado.

## Reproducción

Con Python y las dependencias de desarrollo del repositorio:

```sh
python scripts/build_site.py
python scripts/verify_site.py --baseline /ruta/a/copia-inicial --report docs/qa/structural-after.json
python scripts/extract_legacy.py --verify-generated --output .
```

Las herramientas Node de QA se instalaron fuera del repositorio. Con `jsdom` disponible en `NODE_PATH`:

```sh
NODE_PATH=/ruta/a/qa/node_modules node docs/qa/check-interactions.cjs
```

Para HTML, ejecutar `html-validate` con presets `standard,a11y` sobre los HTML publicables, excluyendo `content/` y `docs/`. El archivo `html-before.json` contiene por separado las recomendaciones del preset general (incluye estilo); la comparación válida de semántica y accesibilidad es `html-standards-before.json` frente a `html-standards-after.json`.
