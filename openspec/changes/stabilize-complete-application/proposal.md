## Why

El flujo principal de BIDACHAT funciona en Docker local, pero la evidencia del 6 de octubre de 2026 conserva avisos de dependencias, un fallo de inferencia con `qwen3-vl:2b` y aceptación real incompleta de formatos y proveedores. Esta continuación prioriza estabilidad y verificación de los requisitos ya aprobados antes de ampliar el producto o declararlo listo para publicación.

## What Changes

- Actualizar dependencias afectadas en lotes compatibles y contrastar los avisos con el uso real; conservar compilación standalone, identidad visual y contratos de API.
- Reproducir y corregir la inferencia vacía de Ollama con límites adecuados a los modelos admitidos y a la memoria disponible; preservar errores seguros y métricas de fallos.
- Completar aceptación real de documentos PDF/DOCX/TXT/CSV e imágenes como conocimiento, además de consultas visuales y proveedores externos efectivamente habilitados.
- Medir el patrón de solicitudes por chatbot y la carga documental síncrona; reducir trabajo redundante y corregir fallos de recuperación demostrados con el stack existente.
- Automatizar pruebas críticas y registrar por requisito la diferencia entre prueba simulada, integración real y comprobación humana.
- Cerrar pendientes manuales de interfaz y verificar HTTPS, respaldo/restauración y sesión antes de publicar en un destino definido.
- Mantener pendientes del cambio `professionalize-frontend-experience` hasta disponer de evidencia; esta propuesta no los marca completados.

## Capabilities

### New Capabilities

- `complete-application-stability`: contrato de aceptación verificable para los flujos existentes de conversación, fuentes, métricas, seguridad y despliegue. Es una representación en OpenSpec de RF/RNF/RS actuales, no una nueva función del producto.

### Modified Capabilities

Ninguna especificación principal se modifica durante la planificación. `openspec/specs/` no contiene capacidades publicadas en este checkout; los cambios anteriores conservan sus propios deltas.

## Impact

- Áreas: `frontend/package*.json`, herramientas de pruebas, `docker/frontend.Dockerfile`, `backend/app/llm/provider.py`, configuración del proveedor, servicios existentes de procesamiento/RAG/consultas/métricas y documentación de QA.
- API: conservar `/api/v1` y respuestas existentes. Un agregado del resumen solo se añadirá si la medición demuestra la necesidad; se documentará su contrato y autorización antes de implementarlo.
- Datos: conservar PostgreSQL/pgvector y dimensión 768; sin migración de esquema prevista. Si una corrección la exige, registrar la decisión y su migración explícita antes de aplicarla.
- Entidades: conservar asociaciones compartidas de documentos, aislamiento de contexto y modelo ejecutado en cada consulta. Pruebas reales con usuario y fuentes aislados; limpieza limitada a esos datos.
- Trazabilidad: RF-01–03, RF-08–09, RF-12–27; RNF-01–07, RNF-09–12; RS-01–09; CA-UC04-01–06, CA-UC05-01–04, CA-UC06-01–05, CA-UC07-01–06 y UI-01–07.
- Alcance autorizado ahora: planificación. No se cambian versiones, modelos de chatbots existentes, secretos, contratos ni infraestructura en este paso.
- Exclusiones: configuración editable de credenciales/orígenes, MFA, nuevos roles, nuevos gráficos, rediseño visual, microservicios, Redis y colas externas.

Base factual: [estado de módulos](../../../docs/qa/frontend/module-status.md), [aceptación](../../../docs/qa/frontend/acceptance.md) y [auditoría](../../../docs/qa/frontend/dependency-audit-summary.json).
