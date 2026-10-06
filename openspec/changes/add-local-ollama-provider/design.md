## Context

La persistencia del MVP ya registra combinaciones inmutables en `llm_models`, conserva la configuración actual del chatbot y captura el modelo ejecutado en cada consulta. `OLLAMA_BASE_URL` existe como configuración privada, pero no hay adaptador LLM ni endpoint conversacional. Véanse `proposal.md` y la sección 12 de `docs/database-design.md`.

## Goals / Non-Goals

**Goals:**

- Resolver el proveedor desde el modelo capturado al aceptar una consulta.
- Ejecutar Ollama mediante una URL privada configurable y responder con errores seguros.
- Mantener Gemini y Ollama detrás de un contrato interno único.
- Validar las capacidades requeridas por tipo de consulta antes de enviarla al proveedor.

**Non-Goals:**

- Administrar el runtime desde la API pública.
- Permitir URLs, claves o parámetros arbitrarios por chatbot.
- Añadir una segunda base vectorial.
- Implementar conmutación automática entre proveedores o preservar capturas de usuarios.

## Decisions

- **Adaptador de inferencia en backend:** un servicio selecciona la implementación por `provider` de la combinación capturada, en lugar de condicionar rutas API o clientes. Esto conserva endpoints delgados y permite añadir proveedores sin exponer detalles. Se descarta llamar Ollama desde widget/frontend porque rompe RNF-01 y expone la red local.
- **Endpoint privado configurado:** `OLLAMA_BASE_URL` se valida al arrancar y se usa solo por el backend. Se descarta guardarlo en `llm_models` porque el catálogo identifica modelos, no destinos de red, y sería una vía de configuración insegura.
- **Modelo verificado por el proveedor:** antes de habilitar una combinación Ollama, el backend comprueba disponibilidad y capacidades requeridas. El bootstrap registra el modelo configurado después de verificar `/api/show`; cada inferencia vuelve a verificar capacidades y disponibilidad; se descarta aceptar cualquier texto de modelo por riesgo de fallos tardíos.
- **Trazabilidad existente:** `QueryService.start_query` continúa copiando `configured_llm_model_id` a `executed_llm_model_id`; la llamada LLM usa esta última referencia. No se requiere migración de datos.
- **Límites de la primera entrega:** el flujo textual se prueba contra Ollama local. La admisión de imagen exige que la combinación seleccionada declare soporte visual; si no, la API rechaza la entrada antes de llamar al proveedor.

## Risks / Trade-offs

- [Ollama no está disponible o el modelo no fue descargado] → validación de disponibilidad, error público seguro y registro de fallo.
- [La URL local difiere entre host y contenedor] → documentar `OLLAMA_BASE_URL` para cada entorno y probar conectividad desde el backend, sin asumir `localhost` dentro de Compose.
- [Modelo local sin capacidad visual] → validar capacidades antes de aceptar consultas con imagen.
- [Latencia y recursos del equipo] → conservar métricas existentes y no fijar umbrales no aprobados.

## Migration Plan

1. Añadir la configuración privada y el adaptador de proveedores, sin migración SQL.
2. Registrar combinaciones Ollama admitidas en `llm_models` mediante una operación administrativa controlada.
3. Probar consulta textual local, fallo seguro, aislamiento y trazabilidad del modelo capturado.
4. Documentar cómo ejecutar Ollama localmente y configurar la URL desde el backend.
5. Revertir retirando las combinaciones Ollama no referenciadas y deshabilitando el adaptador; las consultas históricas conservan su referencia de modelo.

## Ejecución local aprobada

Ollama en Docker con GPU NVIDIA, Qwen3-VL 2B y EmbeddingGemma 300M. El backend selecciona EMBEDDING_PROVIDER de forma independiente del proveedor de respuestas. Ambos perfiles vectoriales usan 768 dimensiones; la recuperación filtra por modelo y chatbot. Los documentos deben reprocesarse al cambiar modelo. Se comienza con contexto 2048 y dos fragmentos RAG en consultas locales; keep_alive=0 libera modelos entre operaciones; el procesamiento documental agrupa hasta 16 fragmentos por llamada. El tiempo de espera local es configurable para cargas iniciales. No se exponen URLs privadas en la interfaz.

## Corrección de despliegue solicitada

El usuario requiere Ollama dockerizado. Compose incluye servicio GPU `ollama`, volumen `ollama_models`, red interna sin puerto publicado y URL backend `http://ollama:11434`. El proceso nativo instalado durante la preparación debe quedar detenido.
