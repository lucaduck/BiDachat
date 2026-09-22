## Why

BIDACHAT necesita definir cómo persisten usuarios, configuración, conocimiento y consultas antes de implementar el MVP. Un diseño revisable permite aprobar aislamiento, relaciones y conservación de datos antes de crear tablas.

## What Changes

- Proponer siete entidades PostgreSQL/pgvector, incluido el catálogo `llm_models`, sus relaciones y restricciones en [el diseño de datos](../../../docs/database-design.md).
- Especificar persistencia de sesiones revocables, configuración de chatbots, fuentes aisladas y consultas con duración.
- Documentar las decisiones aprobadas: documentos exclusivos, gestión compartida, borrado, retención y perfil de embeddings.
- Preparar tareas de migración y validación para después de la aprobación.

La inicialización de OpenSpec y las carpetas fueron autorizadas por el usuario. El 2026-09-16 también solicitó levantar la base local: el esquema inicial está aplicado en Docker y pasó pruebas SQL. El 2026-09-22 el usuario aprobó el SRS 0.1 como referencia de implementación del MVP y las políticas de documentos, permisos, borrado, retención y métricas; no se declara implementado el MVP completo.

El usuario definió inferencia seleccionable por chatbot entre proveedor externo y Ollama local. El diseño incorpora una tabla `llm_models` con `provider` y `model`; la versión en que Ollama quedará habilitado funcionalmente sigue pendiente.

## Capabilities

### New Capabilities

- `mvp-persistence`: persistencia mínima de autenticación, chatbots, documentos, embeddings y consultas, derivada de RF-01–RF-27 en sus aspectos de datos, RS-01/RS-02/RS-04–RS-07/RS-09 y RNF-06/RNF-07.

### Modified Capabilities

Ninguna: `openspec/specs/` no contiene especificaciones consolidadas.

## Impact

La implementación local incluye `docker-compose.yml`, inicialización, migración SQL y pruebas PostgreSQL/pgvector. La integración posterior afectará modelos, conexión y servicios de backend. La API seguirá las rutas de AGENTS.md; la base por sí sola no añade endpoints.

OpenSpec y Prettier son herramientas de desarrollo del repositorio. La arquitectura conserva un único backend y una única base PostgreSQL; el diseño no añade infraestructura. RF-10/RF-23 usan el identificador estable del chatbot y RF-12/RF-19 requieren procesamiento visual, cuya implementación no queda resuelta por la persistencia.
