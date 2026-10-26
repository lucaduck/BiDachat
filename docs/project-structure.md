# Estructura del repositorio

El árbol se organiza por responsabilidad del componente y se mantiene en un único repositorio. La [matriz de decisión](documentation-decision.md) explica esta elección y el [índice de documentación](README.md) orienta por tarea. Este mapa describe carpetas presentes en la versión actual, sin representar carpetas planeadas como si ya existieran.

| Ruta                                           | Responsabilidad y fuente principal                                                                                                                                                     |
| ---------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `frontend/`                                    | Panel Next.js: rutas en `app/`, componentes en `components/`, cliente API en `services/`, utilidades en `lib/`, tipos en `types/`, recursos públicos en `public/` y pruebas en `e2e/`. |
| `backend/app/api/`                             | Rutas REST y dependencias de petición. Las descripciones de OpenAPI se generan desde estas rutas y sus esquemas.                                                                       |
| `backend/app/services/`                        | Reglas de aplicación, documentos, recuperación RAG, conversación, autenticación y métricas. No hay un directorio `backend/app/rag/` en el árbol actual.                                |
| `backend/app/llm/`                             | Adaptadores de proveedores de modelos.                                                                                                                                                 |
| `backend/app/models/` y `backend/app/schemas/` | Modelos SQLAlchemy y contratos de entrada/salida, respectivamente.                                                                                                                     |
| `backend/app/database/` y `backend/app/core/`  | Sesiones de PostgreSQL, configuración y seguridad compartida.                                                                                                                          |
| `backend/tests/`                               | Pruebas de API, servicios, persistencia y proveedores.                                                                                                                                 |
| `widget/src/`                                  | Fuente del cliente JavaScript embebible.                                                                                                                                               |
| `widget/example/`                              | Página de demostración y prueba externa. Su HTML no depende del panel, aunque la compilación copia un ejemplo a `frontend/public/` para probar la integración local.                   |
| `widget/dist/`                                 | Artefacto generado por el build; ignorado por Git.                                                                                                                                     |
| `database/migrations/` y `database/tests/`     | Esquema SQL versionado y comprobaciones de integridad. Las migraciones aplicadas, junto con la base activa, determinan el esquema real.                                                |
| `docker/` y `docker-compose*.yml`              | Dockerfiles, Nginx, inicialización de PostgreSQL, script de despliegue y topología local/de producción.                                                                                |
| `docs/`                                        | Entrada, guías, referencias y explicaciones transversales. `docs/qa/` conserva evidencia fechada; `docs/brand/`, imágenes de identidad; `docs/design-history/`, material histórico.    |
| `openspec/changes/`                            | Propuestas, diseños, tareas y especificaciones de cambios. Su presencia no confirma por sí sola que una función esté implementada.                                                     |
| `.github/workflows/`                           | CI para PR y publicación/despliegue de la rama de producción según el flujo documentado.                                                                                               |
| `.agents/skills/`                              | Habilidades locales de trabajo de Codex; no son código de ejecución del producto.                                                                                                      |

## Documentos de raíz

| Archivo                                 | Función                                                                                         |
| --------------------------------------- | ----------------------------------------------------------------------------------------------- |
| [`README.md`](../README.md)             | Entrada al proyecto y arranque local.                                                           |
| [`SRS.md`](../SRS.md)                   | Requisitos y aceptación: fuente de verdad funcional.                                            |
| [`AGENTS.md`](../AGENTS.md)             | Reglas de implementación para agentes.                                                          |
| [`PRODUCT.md`](../PRODUCT.md)           | Contexto y objetivo de producto.                                                                |
| [`DESIGN.md`](../DESIGN.md)             | Sistema visual vigente.                                                                         |
| [`CONTRIBUTING.md`](../CONTRIBUTING.md) | Pasos de contribución para personas.                                                            |
| [`SECURITY.md`](../SECURITY.md)         | Política de comunicación y tratamiento de vulnerabilidades.                                     |
| `.env.example`                          | Nombres y ejemplos de configuración; el `.env` real contiene valores privados y no se versiona. |

## Límites y artefactos

El frontend y el widget hablan con FastAPI por `/api/v1`; solo el backend accede a PostgreSQL, archivos privados y proveedores de IA. Esta separación corresponde a RNF-01, RNF-04, RNF-14 y RNF-15 del [SRS](../SRS.md). El flujo visual está en [arquitectura](architecture.md).

`storage/`, `.env`, `node_modules/`, `.next/`, `widget/dist/` y copias de build en `frontend/public/` son datos locales o generados e ignorados por Git. Las capturas y reportes versionados en `docs/qa/` tienen una función diferente: son evidencia identificable de pruebas concretas, no archivos de ejecución del sistema. Al actualizar una ruta o un contrato se revisan sus enlaces, manuales y pruebas afectadas en el mismo cambio.
