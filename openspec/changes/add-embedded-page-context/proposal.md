## Why

Un chatbot integrado en otra página conoce sus fuentes RAG, pero no los datos actuales que el usuario ve en el dashboard. El usuario aprobó añadir ese contexto a cada pregunta sin rastrear el sitio ni añadir WebSocket.

## What Changes

- El script de integración declara una región del documento mediante `data-context-selector`.
- El widget lee texto visible de esa región en el momento de enviar cada pregunta y lo limita a 6000 caracteres.
- La API REST acepta `page_context` opcional y el backend lo entrega al modelo separado del contexto RAG, identificado como datos no confiables.
- La documentación y una prueba externa verifican cambios dinámicos, exclusiones y ausencia de contexto cuando falta la región.

## Capabilities

### New Capabilities

- `embedded-page-context`: contexto actual de la página anfitriona para consultas del widget.

## Impact

- RF-31 y CA-UC06-07 en `SRS.md`.
- Widget, contrato de consulta, servicio conversacional y construcción del prompt.
- Sin migración de base de datos, servicio externo nuevo, rastreo de URLs ni conexión persistente.
