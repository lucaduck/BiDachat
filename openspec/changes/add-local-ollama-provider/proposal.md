## Why

El MVP debe permitir que cada chatbot use un proveedor externo o un modelo local mediante Ollama. La persistencia ya conserva el proveedor y modelo seleccionados, pero el backend todavía no puede ejecutar una consulta con Ollama.

## What Changes

- Incorporar Ollama como proveedor de inferencia funcional en Version 1.
- Mantener un adaptador de proveedores dentro del backend para resolver Gemini u Ollama según la configuración del chatbot.
- Usar una dirección `OLLAMA_BASE_URL` configurada solo en backend; el runtime Ollama y sus modelos se administran localmente fuera de la API.
- Validar que el modelo seleccionado esté disponible y sea compatible con el tipo de consulta antes de procesarla.
- Añadir pruebas de selección, fallos seguros y trazabilidad del modelo ejecutado.

## Capabilities

### New Capabilities

- `local-ollama-inference`: selección y ejecución segura de modelos Ollama locales por chatbot en Version 1.

### Modified Capabilities

Ninguna: no existen especificaciones consolidadas bajo `openspec/specs/`.

## Impact

El cambio afecta `backend/app/llm/`, la configuración de entorno, el servicio conversacional pendiente y sus pruebas. No añade acceso directo del frontend o widget al proveedor, conserva PostgreSQL y añade el perfil local `embeddinggemma:300m`/768, y incorpora Ollama como servicio de Docker Compose.

## Ampliación aprobada por el usuario

Instalar Ollama en Docker con GPU NVIDIA con Qwen3-VL 2B para texto/imagen y EmbeddingGemma 300M para embeddings. Configurar ejecución limitada a una solicitud/modelo a la vez, integrar RAG local y reprocesar documentos existentes sin mezclar perfiles. Referencias RF-08, RF-12, RF-14–RF-17 y RF-20–RF-26.

## Corrección de despliegue solicitada

El usuario requiere Ollama dockerizado. Compose incluye servicio GPU `ollama`, volumen `ollama_models`, red interna sin puerto publicado y URL backend `http://ollama:11434`. El proceso nativo instalado durante la preparación debe quedar detenido.
