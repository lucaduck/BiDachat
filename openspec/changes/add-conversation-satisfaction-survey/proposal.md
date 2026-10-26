## Why

BIDACHAT registra consultas y tiempos, pero no conoce si el visitante considera útil y clara la ayuda recibida. Una encuesta breve al finalizar una conversación permitirá evaluar la experiencia del chatbot sin interrumpir cada respuesta. La solicitud del usuario amplía la evaluación de UC-06 y UC-08; todavía no consta como requisito funcional en SRS.md.

## What Changes

- Incorporar al widget una acción explícita para finalizar la conversación y ofrecer una encuesta opcional: satisfacción de 1 a 5, resolución percibida (sí/parcialmente/no), claridad de 1 a 5 y comentario libre opcional.
- Aceptar como máximo una evaluación por conversación con una respuesta completada; validar origen, identidad firmada cuando exista, límites de entrada y uso abusivo mediante la API REST.
- Guardar el resultado para métricas aun cuando se elimine la memoria conversacional vencida, sin conservar nombre, correo, imagen, texto de las consultas ni respuesta del modelo en la evaluación.
- Mostrar en el módulo Métricas satisfacción, resolución, claridad, distribución, evolución y participación, filtradas por chatbot y periodo. Mantener separadas las métricas de satisfacción de las pruebas de exactitud de respuestas.
- Añadir criterios de aceptación al SRS antes de implementar código o migraciones. La propuesta de tabla, plazo de retención del comentario y tratamiento de duplicados se revisan en el diseño.

## Capabilities

### New Capabilities

- `conversation-satisfaction`: encuesta opcional por conversación, recepción segura y métricas administrativas agregadas.

### Modified Capabilities

Ninguna. No existen especificaciones principales en `openspec/specs/` que modificar.

## Impact

- Widget JavaScript y su vista de prueba: acción de cierre, formulario accesible, estados de envío, omisión y reinicio.
- API FastAPI: contrato público de envío y lectura administrativa de agregados; servicio y esquema de validación.
- PostgreSQL: migración y modelo para evaluación con unicidad por conversación y relación con chatbot, independientes de la limpieza de memoria.
- Panel Métricas: visualizaciones y filtros sobre agregados con denominadores visibles.
- Pruebas: unidad y contratos HTTP; integración con PostgreSQL + pgvector para aislamiento, unicidad, limpieza, eliminación y agregación; verificación de widget externo.
- Relación con requisitos vigentes: RF-22, RF-24 a RF-27, RF-32, RF-34, RNF-01, RNF-08, RNF-12, RS-05, RS-07 a RS-10 y CA-UC06-08/09/11, CA-UC08-01 a 07. La encuesta necesitará nuevos identificadores y criterios en SRS antes de su implementación.
