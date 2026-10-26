## Why

BIDACHAT necesita consumir Vertex AI mediante LiteLLM alojado en infraestructura propia, según la integración solicitada para la tesis. La incorporación debe conservar la API REST, el RAG local y la trazabilidad del modelo ejecutado, con código sencillo de mantener.

## What Changes

- Añadir el proveedor `vertex` mediante un adaptador HTTP del backend hacia LiteLLM; mantener las integraciones actuales.
- Ejecutar LiteLLM como contenedor interno opcional con configuración estática, autenticación y límites de recursos.
- Registrar un catálogo explícito de modelos Vertex y reutilizar la selección de proveedor/modelo del editor.
- Admitir consultas de texto e imagen según las capacidades verificadas del modelo. Permitir configurar Vertex como proveedor visual global sin cambiar automáticamente el OpenAI elegido para producción.
- Verificar errores, aislamiento RAG, métricas, credenciales y despliegue con pruebas de contrato y pruebas reales acotadas.
- Documentar instalación, operación y reversión; incorporar la ampliación aprobada al SRS antes de programarla.

Esta entrega autoriza planificación. Las especificaciones son propuestas de ampliación de RF-08, RF-12, RF-13, RF-18 a RF-27; se apoyan en CA-UC03-01, RNF-01, RNF-03, RNF-04, RNF-15 y RS-04, RS-07 a RS-09. No se cambia ahora el SRS ni la aplicación.

## Capabilities

### New Capabilities

- `vertex-ai-gateway`: selección, consumo multimodal y operación privada de Vertex AI a través de LiteLLM.

### Modified Capabilities

Ninguna especificación principal existente: el inventario `openspec list --specs` está vacío.

## Impact

- Backend: configuración, catálogo/bootstrap, adaptador LLM, estado administrativo y pruebas. Se reutilizan los servicios de conversación y procesamiento documental.
- Frontend: etiquetas, disponibilidad y tipos del proveedor; reutilización de los dos selectores existentes. Widget: contrato REST conservado.
- Infraestructura: Compose de desarrollo y producción, configuración estática del gateway, script de despliegue y lista de archivos transferidos por Actions.
- Datos: se prevé reutilizar `llm_models` y la referencia del modelo ejecutado en consultas. No se propone migración, base adicional ni reindexado de vectores.
- Dependencias: imagen oficial LiteLLM fijada a versión/digest verificado; sin SDK LiteLLM en el backend. La inferencia externa y su autenticación Google son las conexiones necesarias; no se habilitan servicios externos de backend, almacenamiento o telemetría.
