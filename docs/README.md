# Documentación de BIDACHAT

El [README principal](../README.md) permite arrancar el proyecto. Aquí se agrupan los documentos por la necesidad del lector, siguiendo [la decisión documental](documentation-decision.md). Los enlaces conservan la ubicación de los archivos existentes.

## Aprender con un recorrido

- [Arranque local y primera consulta](../README.md#arranque-local): levantar los servicios y abrir el panel.
- [Probar el widget en un sitio externo](../widget/README.md): integrar el script, configurar el origen y enviar una consulta.

## Realizar una tarea

- [Configurar Ollama en Docker](local-ollama.md).
- [Configurar Vertex AI mediante LiteLLM en Docker](vertex-ai.md).
- [Operar la memoria conversacional y el contexto de página](conversation-memory.md).
- [Preparar y desplegar con GitHub Actions](deployment/github-actions.md).
- [Respaldar y comprobar la restauración](deployment/backups.md).
- [Configurar el proxy inverso](deployment/reverse-proxy.md).
- [Trabajar con la base de datos y sus migraciones](../database/README.md).
- [Ejecutar y probar la API](../backend/README.md).
- [Desarrollar el panel](../frontend/README.md).
- [Revisar la publicación web](web-release-checklist.md).

## Consultar una referencia

- [Requisitos y criterios de aceptación](../SRS.md).
- [Reglas de implementación](../AGENTS.md).
- [Rutas de la API](api-routes.md); el contrato ejecutable se genera desde FastAPI.
- [Estructura y responsabilidades del repositorio](project-structure.md).
- [Sistema visual vigente](../DESIGN.md).
- [Política de seguridad](../SECURITY.md).

## Comprender las decisiones

- [Arquitectura y límites entre componentes](architecture.md): diagramas C4
  versionados con Mermaid.
- [Diseño de datos y justificación histórica](database-design.md). Para el esquema aplicado, consultar las [migraciones](../database/migrations/).
- [Decisión sobre documentación y repositorio](documentation-decision.md).
- [Plan crítico de recomendaciones de tesis](recommendations-review-plan.md).

## Consultar evidencia e historia

- [Índice de evidencias de pruebas](qa/README.md). Los resultados están fechados y describen el entorno en que se obtuvieron.
- [Revisión de inicialización](initialization-review.md): registro histórico de una etapa anterior.
- [Diseño visual anterior](design-history/desing-before-professionalization.md): referencia histórica, no especificación vigente.
- [Propuestas y tareas OpenSpec](../openspec/changes/): historia de cambios; la aprobación de un documento se comprueba en su contexto.

Las imágenes de identidad están en [brand](brand/). Los originales privados de documentos y las credenciales no pertenecen a `docs/` ni se versionan.
