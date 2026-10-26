# Revisión de documentación y diagramas

Fecha: 17 de octubre de 2026.

## Decisión comprobada

La [matriz documental](../documentation-decision.md) conserva tres decisiones
complementarias:

1. Diátaxis organiza la navegación según la necesidad del lector.
2. El SRS mantiene la autoridad sobre requisitos y criterios de aceptación.
3. C4 estructura la explicación arquitectónica y Mermaid renderiza sus diagramas
   desde texto versionado. El esquema de datos utiliza `erDiagram` de Mermaid.

## Comprobaciones realizadas

- Se recorrieron README, SRS, AGENTS y todos los Markdown de `docs/`.
- Se comprobaron archivos y anclas de los enlaces Markdown locales.
- Se confirmó que los bloques Mermaid tienen cierres equilibrados.
- Se contrastó la arquitectura con Compose y con los módulos actuales de FastAPI.
- Se contrastó el modelo de datos con las migraciones 001–005.

## Correcciones aplicadas

- La [arquitectura](../architecture.md) muestra ahora el perfil opcional
  FastAPI → LiteLLM → Vertex y separa las API externas directas.
- Se añadió el nivel de componentes lógicos de FastAPI sin presentar esos módulos
  como microservicios.
- La [decisión documental](../documentation-decision.md) distingue C4, Mermaid y
  el diagrama entidad-relación.
- El [diseño de datos](../database-design.md) representa las once tablas del
  dominio, las asociaciones compartidas, la memoria conversacional y el límite de
  acceso. También se retiraron afirmaciones que describían como futuras funciones
  ya implementadas.
- Se corrigió el enlace histórico afectado por el nuevo título de la sección 11.

## Resultado y límites

La comprobación local terminó sin destinos Markdown rotos. Prettier aprobó los
documentos modificados. Esta revisión verifica coherencia estructural y referencias
locales; no constituye una auditoría formal de conformidad ISO/IEC/IEEE ni valida
la disponibilidad futura de enlaces web externos. Los documentos de
`docs/design-history/`, `docs/qa/` y OpenSpec pueden conservar lenguaje histórico
cuando su fecha y propósito dejan claro que no describen el estado actual.
