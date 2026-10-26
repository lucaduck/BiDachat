## Context

Fecha: 2026-10-21. Estado: planificación, sin implementación. Ver `proposal.md`.

Evidencia del repositorio:
- `backend/app/llm/provider.py`: OpenAI Responses con `store:false`; Gemini generateContent; OpenRouter Chat Completions con cabeceras de atribución; Ollama `/api/chat`; embeddings Ollama/Gemini directos.
- `backend/app/llm/vertex_gateway.py`: gateway privado, validación de modelo devuelto, texto/imagen, timeout HTTP 45 s, sin streaming.
- `docker/litellm/start.py`: exige proyecto, catálogo y JSON Vertex; genera YAML temporal con permisos 0600. Los dos Compose activan el perfil `vertex` y montan obligatoriamente ese JSON.
- `docker/litellm/config.yaml`: timeouts 40 s, reintentos/fallbacks desactivados, sin callbacks, telemetría ni logs de contenido habilitados.
- `backend/app/api/settings.py` deriva disponibilidad de credenciales locales; `chatbot_service.py` aplica catálogo especial a Vertex. El script de despliegue activa LiteLLM por `VERTEX_ENABLED`.
- Imagen LiteLLM fijada por versión y digest. La compatibilidad de cada endpoint debe verificarse en ESA imagen, no inferirse de documentación más reciente.

## Goals / Non-Goals

**Goals:** transporte externo común, código legible, catálogo explícito, secretos acotados y evidencia de equivalencia funcional por proveedor.

**Non-Goals:** WebSocket/streaming, cambios visuales, nuevos proveedores/modelos, caché, Redis, base de LiteLLM, descubrimiento automático de modelos, nuevas métricas comerciales o modificación del perfil de embeddings.

## Decisions

### 1. Alternativa B y fundamento

Matriz original: escala 1–5, resultado = suma(peso × puntuación). Juicio técnico contextual, no benchmark.

| Criterio | Peso | A actual | B externos | C todo | D directo |
|---|---:|---:|---:|---:|---:|
| Seguridad/control | 25 % | 4 | 4 | 3 | 3 |
| Mantenimiento | 25 % | 3 | 4 | 5 | 2 |
| Capacidades actuales | 20 % | 5 | 4 | 3 | 5 |
| Aislamiento de fallos | 15 % | 4 | 3 | 2 | 5 |
| Riesgo/esfuerzo de migración | 10 % | 5 | 3 | 2 | 1 |
| Simplicidad del recorrido | 5 % | 4 | 4 | 3 | 5 |
| Total | 100 % | 4,05 | 3,75 | 3,30 | 3,35 |

A obtiene mejor resultado inmediato por evitar migración. El usuario selecciona planificar B como evolución de mantenimiento; no se alteran los pesos para justificar su elección. Se acepta dependencia común para generación externa, manteniendo independencia local. C acopla innecesariamente embeddings e inferencia local; D duplica trabajo de autenticación Vertex.

```text
Widget / Panel -> API REST -> conversación, memoria, guardrails, RAG
                                      |
                                      +-> Gateway privado LiteLLM
                                      |       +-> Vertex
                                      |       +-> OpenAI
                                      |       +-> Gemini
                                      |       +-> OpenRouter
                                      +-> Ollama (generación local directa)
                                      +-> Ollama/Gemini (embeddings directos)
```

### 2. Cliente común, contratos explícitos

Extraer de Vertex un cliente `external_gateway.py` para autenticación interna, HTTP, límites y errores seguros. Mantener pequeñas funciones de serialización/lectura para Responses y Chat Completions; evitar una jerarquía de clases por proveedor.

OpenAI conserva Responses y `store:false` a través de LiteLLM si la versión fijada demuestra soporte; la tarea de compatibilidad bloquea su migración si no lo soporta. No convertir a Chat Completions ni actualizar dependencias silenciosamente para superar esa barrera. Vertex conserva su contrato y comprobación de modelo. Gemini y OpenRouter usan el contrato compatible comprobado. Preservar instrucciones confiables separadas del contexto no confiable, imagen base64 y MIME, límites actuales por proveedor y rechazo de respuestas vacías, truncadas o bloqueadas. No fijar parámetros no admitidos por un modelo.

El mismo transporte se aplica a `VISION_PROVIDER` para descripción de documentos visuales. La lógica de embeddings permanece intacta, incluidos formato de entrada, dimensión 768 actual, task_type y modelo. Cambiar transporte no debe modificar memoria ni límites de RAG.

### 3. Catálogo y datos

Usar alias internos únicos derivados del par proveedor/modelo, evitando colisiones Gemini/Vertex y barras en identificadores OpenRouter. Mantener los IDs y nombres de `llm_models` y las referencias actuales de los chatbots; una tabla de correspondencias en configuración traduce alias internos, sin migración SQL. No seleccionar cualquier modelo del proveedor ni aceptar destinos arbitrarios enviados por el cliente.

Mantener esquema de métricas y registrar proveedor/modelo de ejecución con la semántica existente; resolver nombres de respuesta contra alias canónicos conocidos. Nunca inventar identidad del modelo cuando la respuesta no la permita comprobar. Catálogo configurado no equivale a conectividad verificada. Actualizar bootstrap, servicio de catálogo y estado administrativo para que mover claves no oculte proveedores configurados.

Las entidades, cardinalidades, restricciones, borrado y transacciones actuales de `docs/database-design.md` se conservan. El gateway no escribe datos ni asume la memoria; el backend continúa siendo responsable de los límites de persistencia y registro de consultas.

### 4. Configuración y secretos

Proponer `EXTERNAL_AI_GATEWAY_PROVIDERS` como lista explícita de proveedores migrados: durante transición `vertex`; al terminar todos los externos habilitados. Proveedor listado con gateway caído falla; nunca se desvía automáticamente al adaptador directo. La lista es configuración administrativa, no parámetro público.

Mantener nombres `OPENAI_API_KEY`, `OPENROUTER_API_KEY`, `GEMINI_API_KEY` en configuración privada para compatibilidad operativa; Compose los inyecta en LiteLLM. Retirar del entorno backend las claves de generación una vez migrado cada proveedor; Gemini es excepción documentada cuando los embeddings directos lo requieren. Durante transición la duplicación es temporal y explícita. Un backend sin claves debe conservar información no secreta de habilitación/catálogo.

Generalizar perfil a `ai-gateway`, conservando temporalmente alias `vertex`. Separar el montaje Vertex en overrides de desarrollo/producción utilizados únicamente cuando esté habilitado: no exigir JSON ni crear archivo ficticio para una instalación solo OpenAI. Validar perfiles en scripts, documentación y CI. No exponer puerto 4000 al host ni crear ruta pública en Nginx. Conservar límites de recursos y digest; no añadir BD, UI administrativa ni callbacks externos.

Limitar credenciales Google a la inferencia necesaria; mantener JSON read-only. Configuración temporal sin claves interpoladas, permisos restrictivos y referencias a entorno. No imprimir configuración expandida en CI ni en informes. Revisar logs en éxito, errores 401/403/429, timeout y respuestas inesperadas usando marcadores sintéticos.

### 5. Fiabilidad y privacidad

Mantener reintentos y fallbacks desactivados en cliente, gateway y proveedor configurable. En OpenRouter distinguir proveedor comercial seleccionado de su enrutamiento interno; comprobar sus opciones vigentes y documentar el límite de control. No afirmar que `fallbacks: []` de LiteLLM gobierna el enrutamiento interno de OpenRouter.

Reutilizar errores públicos seguros sin cuerpos del proveedor, tokens o URLs internas. Memoria, rate limiting, orígenes e identidad siguen en FastAPI. No habilitar caché compartida. La caída de LiteLLM no debe impedir consultas Ollama ni arranque del modo exclusivamente local.

## Risks / Trade-offs

- Responses o parámetros incompatibles con la imagen fijada → prueba de contrato antes de migrar OpenAI; mantener ruta previa hasta resolución explícita.
- Colisión de nombres → alias por par proveedor/modelo y prueba Gemini/Vertex con mismo nombre.
- Claves concentradas → servicio privado, mínima exposición y pruebas de redacción; centralización no garantiza ausencia de filtraciones.
- Latencia adicional → medir p50/p95 y error antes/después, con misma pregunta, modelo, longitud y concurrencia; no prometer mejora ni inventar SLA.
- Migración incompleta → matriz de proveedor/capacidad con estados real, simulado, pendiente y bloqueado; nunca aprobar globalmente con mocks.
- Cambio de política de retención → conservar `store:false` donde corresponda y verificar parámetros de cada proveedor, sin afirmar retención cero universal.

## Migration Plan

1. Aprobar este plan y registrar ampliación SRS antes de código. Capturar versión/digest, configuración no secreta y línea base de contratos y rendimiento.
2. Generalizar arranque/catálogo/Compose y comprobar instalación local sin Vertex y externa sin JSON Google.
3. Extraer cliente compartido preservando Vertex y pruebas existentes.
4. Migrar OpenAI, después Gemini, después OpenRouter; una entrega verificable por proveedor. Cubrir chat y perfil visual en cada paso.
5. Validar aplicación completa en ambas configuraciones Compose, actualizar documentación y cerrar tareas con evidencia.
6. Retirar adaptadores de generación redundantes cuando todos los proveedores habilitados hayan pasado aceptación. Mantener funciones de embeddings que comparten la clave Gemini.

Reversión durante transición: restaurar lista anterior y distribución anterior de claves, recrear servicios y probar salud más una consulta; nunca fallback en tiempo de petición. Tras retirar adaptadores: volver al commit/imágenes fijados de la versión anterior junto con su Compose y configuración. No borrar conversaciones ni regenerar vectores; no hay migración de datos. Ensayar rollback local antes de producción.

## Open Questions

- Catálogo concreto y capacidades reales de cada cuenta: obtenerlos de configuración y pruebas autorizadas, no del nombre del modelo.
- Presupuesto remanente de autorizaciones anteriores: no está contabilizado en este plan. Acordar límite antes de nuevas pruebas facturables; esta planificación no consume API.
- Sobrecoste de latencia aceptable: presentar mediciones para decisión; no existe umbral aprobado que permita inventar un criterio temporal.
