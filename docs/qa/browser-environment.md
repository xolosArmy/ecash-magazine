# Disponibilidad de QA en navegador

Fecha: 2026-09-19. Las herramientas se instalaron fuera del repositorio y no son dependencias de producción.

| Herramienta | Resultado comprobado |
|---|---|
| `agent-browser` 0.38.1 | Instalado. No pudo iniciar su daemon: `Failed to bind socket: Operation not permitted (os error 1)`. |
| Chrome for Testing 153.0.8010.52 | Descargado desde distribución oficial; ZIP verificado y ejecutable responde a `--version`. |
| Lighthouse CLI 13.5.0 | Instalado. No pudo conectarse a Chrome: `Unable to connect to Chrome`. Chrome aborta con `socket() failed: Operation not permitted (1)` en `process_singleton_posix.cc`. |
| html-validate 11.16.0 | Disponible y ejecutado sin navegador. |
| Validador estructural Python/lxml | Disponible y ejecutado sin navegador. |

El bloqueo de sockets del entorno impide usar el navegador local, aunque las herramientas estén instaladas. No se modificaron restricciones de seguridad ni se obtuvieron puntuaciones de Lighthouse. Ningún resultado estructural se presenta como Core Web Vitals de campo, Lighthouse o auditoría visual.

## Reproducir en un entorno con navegador permitido

1. Instalar las herramientas de QA fuera del sitio: `npm install --no-save agent-browser lighthouse html-validate`.
2. Ejecutar `agent-browser install`.
3. Servir el repositorio con `python3 -m http.server 8766`.
4. Abrir `http://127.0.0.1:8766` con `agent-browser open` y comprobar `snapshot -i`, `errors` y `console`.
5. Probar portada, archivo, búsqueda y artículos en anchos 320, 390, 768, 1440 y 1920 px con `agent-browser set viewport ANCHO ALTO`.
6. Verificar teclado, menú móvil, búsqueda, filtros, enlaces, índice y multimedia; capturar portada y artículo en escritorio y móvil.
7. Ejecutar auditoría axe mediante `agent-browser a11y --tags wcag2a,wcag2aa,wcag21aa --json`.
8. Ejecutar `lighthouse http://127.0.0.1:8766 --output=json --output=html --output-path=./lighthouse` en móvil y con `--preset=desktop`.

Las verificaciones de navegador pendientes deben completarse antes de considerar aprobado el resultado visual y de accesibilidad. No se confunden los chequeos estáticos con esas verificaciones.
