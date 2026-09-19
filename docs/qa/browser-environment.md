# Entornos de verificación de navegador

## Resultado final en GitHub Actions

La verificación real quedó completada en [la ejecución 35450868683](https://github.com/xolosArmy/ecash-magazine/actions/runs/35450868683), sobre el commit `39f378c81465cd332c2884ba3571193c04bb6e59`: **136/136 comprobaciones aprobadas**, doce capturas PNG originales y cuatro mediciones Lighthouse completas antes/después.

El workflow usa un runner de GitHub con Chromium 151.0.7922.34, Playwright 1.62.1, axe-core 4.13.0 y Lighthouse 13.5.0. Sirve la base inmutable y la rama mediante HTTP local en el runner. No publica la rama en el dominio ni modifica el hosting. Permisos del workflow: `contents: read`; límite: 15 minutos; artefactos: 30 días de retención.

Los [resultados finales](README.md) y [resúmenes compactos](final/ci-summary.json) sustituyen el estado inicial de bloqueo para la entrega. El bloqueo local descrito abajo sigue siendo una limitación del runtime de trabajo, pero ya no deja pendientes las comprobaciones de navegador del PR.

## Registro del bloqueo local inicial

Fecha: 2026-09-19. Se instalaron las herramientas fuera del sitio, sin añadir dependencias de producción.

| Herramienta | Resultado comprobado en el runtime local |
|---|---|
| `agent-browser` 0.38.1 | No inició su daemon: `Failed to bind socket: Operation not permitted (os error 1)`. |
| Chrome for Testing 153.0.8010.52 | ZIP oficial verificado; `--version` funciona, pero el navegador no puede crear los sockets requeridos. |
| Lighthouse CLI 13.5.0 | Chrome aborta con `socket() failed: Operation not permitted (1)` en `process_singleton_posix.cc`; Lighthouse responde `Unable to connect to Chrome`. |
| html-validate 11.16.0 | Disponible y ejecutado sin navegador. |
| Python/lxml y jsdom | Validación estática y funcional disponible. |

No se alteraron restricciones de seguridad para ejecutar Chrome localmente. Las puntuaciones publicadas proceden del runner de GitHub y están asociadas a su SHA y ejecución; no se atribuyen a los intentos locales fallidos.

## Alcance de los resultados

Se conservaron 12 capturas antes/después de portada, principal y artículo técnico P2SH en escritorio y móvil. Se probaron cinco anchos y los 43 artículos a 390 px, teclado, menú, búsqueda, fallback de red y contenido sin JavaScript.

La auditoría axe final no detectó violaciones en los escenarios probados; dejó una comprobación incompleta del símbolo no textual `✔` en Teyolia. Los errores Imgur 403 aparecen sólo en la referencia anterior y se conservan en los reportes. Lighthouse mide una corrida de laboratorio móvil por documento y revisión, no datos de usuarios de producción.
