# Contribuir a BIDACHAT

Esta guía es para personas que cambian el repositorio. El [SRS](SRS.md) define los requisitos aprobados y [AGENTS.md](AGENTS.md) las reglas de implementación para agentes. El [índice de documentación](docs/README.md) ayuda a localizar guías y referencias.

## Antes de cambiar el código

1. Identifica el requisito, criterio de aceptación y módulo afectado. Si se trata de una función nueva, registra primero su alcance aprobado en el SRS.
2. Revisa el código, las pruebas y la documentación del componente. Usa la [estructura del repositorio](docs/project-structure.md) para encontrar sus responsables.
3. Mantén juntos el cambio funcional, las pruebas necesarias y la actualización de la guía correspondiente. Las migraciones se añaden como archivos nuevos; no se modifica una migración ya aplicada.

## Flujo de revisión

`develop` integra cambios mediante pull request. `production` recibe un pull request aprobado desde `develop` para publicar imágenes identificadas por commit. El detalle de los checks, permisos y despliegue está en [GitHub Actions](docs/deployment/github-actions.md). Las ramas de trabajo usan nombres en inglés como `feature/document-upload` o `fix/authentication-error`; los commits siguen Conventional Commits, según [AGENTS.md](AGENTS.md#16-git-workflow).

Antes de solicitar revisión, ejecuta las pruebas del área afectada y sus comandos de formato o lint. Registra qué verificaste y qué quedó pendiente. Para cambios transversales, comprueba al menos el contrato de la API, la navegación o integración del widget, y las migraciones si aplican. Los resultados históricos de [docs/qa](docs/qa/README.md) no sustituyen una prueba del cambio nuevo.

## Dónde documentar

- Propósito y arranque breve: [README](README.md).
- Guía para una tarea: manual del componente o [docs/deployment](docs/deployment/).
- Rutas, estructura y sistema visual: [referencias](docs/README.md#consultar-una-referencia).
- Explicaciones y decisiones: [docs](docs/README.md#comprender-las-decisiones).
- Resultados reproducibles de una prueba: [docs/qa](docs/qa/README.md), con fecha, entorno, versión y limitaciones.

Usa enlaces relativos. Si cambias un nombre o ruta, actualiza las referencias en el mismo PR. No añadas claves, datos privados, `.env` real, copias de seguridad ni artefactos de compilación al repositorio; revisa la [política de seguridad](SECURITY.md).
