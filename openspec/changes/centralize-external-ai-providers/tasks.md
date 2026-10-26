## 1. Planificación y punto de reanudación

- [x] 1.1 Inspeccionar rutas de proveedores, configuración, Compose, catálogo y SRS; registrar hallazgos y matriz A/B/C/D en design.md.
- [x] 1.2 Redactar propuesta, diseño y escenarios verificables de external-ai-gateway.
- [x] 1.3 Obtener instrucción de implementación y registrar en SRS la ampliación de RF-08/RF-12/RF-13/RF-21, respetando RNF-15 y RS-04/RS-09 antes de tocar código.

Estado al 2026-10-21: implementación local en curso. Se añadió el contrato del gateway, configuración por catálogo, perfil Compose `ai-gateway`, override Vertex y pruebas HTTP sintéticas; no se modificaron secretos ni se realizaron consultas facturables. Sigue pendiente la verificación contra el digest desplegado y la aceptación real autorizada. Para reanudar, leer proposal.md, design.md y specs/external-ai-gateway/spec.md; comprobar Git y actualizar cada casilla solo con evidencia. Un fallo de compatibilidad se registra como bloqueo del proveedor, no se resuelve con fallback silencioso.

## 2. Contratos y línea base

- [x] 2.1 Construir matriz de modelos configurados por proveedor: chat textual, imagen adjunta y descripción de fuente, instrucciones, endpoint, límites, privacidad, errores y nombre retornado. No copiar secretos.
- [x] 2.2 Añadir pruebas de caracterización sobre adaptadores existentes y registrar comandos/resultados; usar PostgreSQL con pgvector para persistencia/métricas y mocks solo para contratos HTTP.
- [ ] 2.3 Verificar en la imagen/digest actual el soporte de Responses para OpenAI y su `store:false`, traducción Gemini, cabeceras OpenRouter y validación de nombres Vertex. Documentar capacidades incompatibles; bloquear su migración hasta resolución explícita.
- [ ] 2.4 Acordar consumo disponible para pruebas reales y recoger línea base comparable de latencia p50/p95 y errores; registrar tamaño de muestra, modelo, prompt, longitud, concurrencia y condiciones. Si no hay presupuesto, dejar evidencia real pendiente.

## 3. Gateway y configuración Docker

- [x] 3.1 Generalizar start.py y config.yaml para catálogos explícitos por proveedor, alias únicos y validación independiente de credenciales; probar colisión de nombres Gemini/Vertex y modelos OpenRouter con barras.
- [x] 3.2 Incorporar lista de proveedores migrados y configuración no secreta compartida con backend; rechazar habilitación incompleta sin exponer valores sensibles.
- [x] 3.3 Adaptar ambos Compose al perfil ai-gateway y compatibilidad temporal vertex; aislar montaje Google en overrides condicionales y probar arranque externo sin Vertex y local sin gateway.
- [x] 3.4 Ajustar deploy-production.sh, verify.py y configuración de entrega para iniciar/comprobar gateway según proveedores migrados; validar Compose con fixtures, sin imprimir entorno expandido.
- [ ] 3.5 Mover claves de generación al gateway por proveedor, preservando clave Gemini en backend solo si la necesitan embeddings o ruta transitoria. Comprobar JSON read-only, puerto privado, ausencia de callbacks y logs de contenido, recursos y digest.

## 4. Cliente compartido y catálogo

- [x] 4.1 Extraer external_gateway.py de VertexGateway: reutilizar errores seguros y transporte HTTP; mantener serializadores explícitos Responses/Chat Completions y límites por modelo sin abstracciones adicionales.
- [ ] 4.2 Migrar Vertex al cliente común y ejecutar test_vertex_gateway.py y test_vertex_integration.py; conservar instrucciones, imágenes, timeout, validación de modelo y rechazo de resultados incompletos.
- [x] 4.3 Adaptar bootstrap, chatbot_service.py y configuración/estado administrativo para usar catálogo explícito sin depender de claves en backend; conservar IDs existentes, selección y modelos históricos.
- [x] 4.4 Comprobar respuestas 401/403/429/5xx, timeout, vacías y truncadas; verificar una sola petición externa por operación sin reintentos/fallback y redacción de logs/error público.

## 5. Migración por proveedor

- [x] 5.1 OpenAI: implementar ruta Responses del gateway conservando store:false, instrucciones, imagen y errores; probar chat y VISION_PROVIDER con un modelo habilitado. Mantener ruta previa hasta cerrar aceptación.
- [x] 5.2 Gemini: implementar generación textual/visual por gateway y comprobar instrucción de sistema; demostrar que embed/embed_batch conservan endpoint, formato, modelo, task_type y dimensiones.
- [x] 5.3 OpenRouter: conservar identificador completo y atribución de aplicación; verificar texto/imagen, parámetros y política de enrutamiento interno documentada, distinguiéndola del fallback LiteLLM.
- [ ] 5.4 En cada proveedor migrado, activar únicamente tras contrato y aceptación real autorizada; registrar filas no probadas o bloqueadas y ensayar reversión de configuración antes de continuar.

## 6. Aceptación transversal

- [ ] 6.1 Probar RF-08/RF-21: crear bot, seleccionar proveedor/modelo, consultar, cambiar modelo y verificar ejecución nueva y conservación de métricas históricas.
- [ ] 6.2 Probar memoria y aislamiento: dos chatbots, dos identidades/orígenes, seguimiento de nombre, contexto del body/selector y fuentes RAG; comprobar ausencia de cruce y de regresión de guardrails.
- [ ] 6.3 Probar imagen adjunta y PNG/JPEG/WebP como fuentes por proveedor habilitado; no declarar capacidad visual en modelos textuales ni usar mocks como aceptación real.
- [ ] 6.4 Detener gateway: externos fallan de forma controlada, Ollama y embeddings directos siguen disponibles; probar arranque local sin gateway y sin Google JSON.
- [ ] 6.5 Verificar con marcadores sintéticos que logs/configuración/errores no contienen claves ni mensajes; probar autenticación interna ausente/inválida, ausencia de puerto público y acceso solo vía API desde widget.
- [ ] 6.6 Comparar p50/p95, errores y consumo contra línea base con mismas condiciones; presentar diferencias y limitaciones sin inventar SLA. Confirmar ninguna reindexación ni alteración de vectores persistidos.
- [ ] 6.7 Ensayar rollback a versión/configuración anterior y comprobar chatbots, conversaciones, métricas y fuentes; guardar evidencia redactada.

## 7. Cierre y entrega

- [ ] 7.1 Retirar adaptadores externos redundantes solo tras aceptar todos los proveedores habilitados; mantener embeddings y soporte local directo. Documentar rollback por versión tras esta retirada.
- [x] 7.2 Actualizar .env.example, README, backend/README, docs/vertex-ai.md, arquitectura C4, guía de gateway y despliegue; explicar excepción Gemini embeddings, límites de seguridad y matriz de capacidades verificadas.
- [ ] 7.3 Ejecutar pruebas afectadas, Ruff, lint/formato frontend si se modifica, validación Compose dev/prod y OpenSpec; registrar evidencia por escenario y pendientes reales.
- [ ] 7.4 Preparar cambio revisable con diff y escaneo de secretos. Ejecutar commit/push/despliegue únicamente cuando se soliciten; no reutilizar la autorización de subida anterior como autorización de esta entrega.
