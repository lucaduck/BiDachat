## Why

BIDACHAT mantiene adaptadores externos distintos y utiliza LiteLLM únicamente para Vertex. La alternativa B de la matriz de decisión permite unificar el transporte externo y sus controles manteniendo independientes la inferencia local y los embeddings. El usuario solicita planificar esta evolución; este cambio no autoriza su ejecución ni acredita aceptación real.

## What Changes

- Enrutar la generación externa de texto e imágenes de Vertex, OpenAI, Gemini y OpenRouter por el LiteLLM privado existente, incluida la descripción de fuentes visuales.
- Mantener Ollama y todos los embeddings en sus rutas actuales, sin regenerar vectores.
- Generalizar el arranque, catálogo y comprobaciones del gateway para no exigir credenciales Vertex cuando solo se usa otro proveedor.
- Conservar proveedor/modelo persistidos, API pública, memoria, contexto, guardrails y métricas; no introducir fallback ni reintentos automáticos.
- Migrar por proveedor con reversión explícita y validar contratos reales antes de retirar adaptadores externos redundantes.
- **BREAKING operativo:** al completar la transición, la generación externa dependerá de LiteLLM y sus credenciales estarán configuradas allí. La clave Gemini permanecerá también en backend si se emplea para embeddings.

## Capabilities

### New Capabilities

- `external-ai-gateway`: transporte privado unificado con catálogo inequívoco, compatibilidad, aislamiento de secretos y fallos explícitos.

### Modified Capabilities

Ninguna especificación consolidada: `openspec/specs/` está vacío. El cambio complementa el plan previo `add-vertex-ai-gateway` sin reescribir su evidencia histórica.

## Impact

Afecta `backend/app/llm/`, configuración, catálogo y estado de proveedores, pruebas, `docker/litellm/`, ambos Compose, scripts de entrega, `.env.example` y guías. No requiere nuevas tablas, migraciones SQL, Redis, otra base ni servicios SaaS. Se conserva el modelo relacional descrito en `docs/database-design.md`.

Trazabilidad: RF-08, RF-11, RF-12, RF-13, RF-16–RF-22, RF-24–RF-26; RNF-15; RS-04, RS-05, RS-07–RS-10; aceptación UC-03, UC-04, UC-06 y UC-07 del SRS. La ampliación del SRS se realizará al aprobar la implementación, antes de modificar código.
