# Ollama en Docker para BIDACHAT

## Estructura

Next.js y el widget llaman exclusivamente a FastAPI. El backend usa el servicio
`ollama` de Docker Compose para respuestas e embeddings, y PostgreSQL + pgvector
para recuperación. URL interna: `http://ollama:11434`. No se publica el puerto de
Ollama en Windows ni se requieren una instalación o un proceso nativo.

## Perfiles de hardware y modelos

El perfil se declara con `OLLAMA_ACCELERATION` en `.env`. El Compose base es
compatible con CPU; `docker-compose.gpu.yml` se añade únicamente en producción
cuando el despliegue selecciona `gpu`.

- CPU: `qwen3:1.7b`, un modelo cargado y una solicitud concurrente. Es el
  perfil recomendado para VPS sin GPU y para consultas textuales.
- GPU NVIDIA: `qwen3-vl:2b-instruct`, hasta dos modelos cargados. Permite
  respuestas, capturas y descripción de imágenes de conocimiento con mejor
  tiempo de respuesta.
- `embeddinggemma:300m`: embeddings textuales de 768 dimensiones.

El tamaño de descarga no equivale a VRAM utilizada. Imágenes y contexto consumen
memoria adicional. El modelo pequeño necesita evaluación con capturas del dominio.

## Puesta en marcha

El perfil GPU requiere Docker Desktop con WSL 2 y controlador NVIDIA compatible
en desarrollo, o NVIDIA Container Toolkit en un VPS Linux. El perfil CPU no
requiere ninguno de esos componentes. Ambos persisten los modelos en
`ollama_models`.

Para desarrollo con GPU, añadir el complemento explícitamente:

```bash
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d ollama
```

En producción no se escribe ese comando manualmente: `deploy-production.sh`
lee `OLLAMA_ACCELERATION` y selecciona el complemento adecuado.

```bash
docker compose up -d ollama
docker compose exec ollama ollama pull embeddinggemma:300m
docker compose exec ollama ollama pull qwen3:1.7b
docker compose exec ollama ollama list
docker compose up -d --build backend frontend
```

Descargar los modelos antes de iniciar el backend: el bootstrap comprueba que el
modelo de respuestas existe antes de registrarlo en el selector administrativo.
No usar `docker compose down -v` si se quieren conservar modelos y base de datos.

## Configuración

En `.env`, sin credenciales externas para el perfil local:

```dotenv
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=embeddinggemma:300m
EMBEDDING_DIMENSIONS=768
OLLAMA_ACCELERATION=cpu
OLLAMA_MAX_LOADED_MODELS=1
OLLAMA_NUM_PARALLEL=1
OLLAMA_MODEL=qwen3:1.7b
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_CONTEXT_LENGTH=2048
OLLAMA_TIMEOUT_SECONDS=600
```

Compose fija la URL interna del backend. Seleccionar `ollama / qwen3-vl:2b-instruct` en
cada chatbot que deba usar inferencia local; se conservan las selecciones previas
hasta editarlas. La sección Configuración muestra el proveedor de embeddings.

Para un VPS sin GPU, usar `qwen3:1.7b` para texto y no prometer análisis de
imágenes. Para usar capturas, elegir explícitamente el perfil GPU, instalar el
modelo `qwen3-vl:2b-instruct`, ajustar `OLLAMA_MODEL` y, si la VRAM lo permite,
configurar `OLLAMA_MAX_LOADED_MODELS=2`. Cambiar el modelo generativo no
reindexa los documentos; cambiar embeddings sí exige reindexación.

El perfil CPU limita la ejecución a un modelo cargado y una solicitud por modelo,
con servicios cloud deshabilitados. El backend usa `keep_alive=0` para liberar
modelos después de cada operación. Esto reduce VRAM retenida pero aumenta latencia.
Los documentos se procesan en lotes de hasta 16 fragmentos por carga.
La API verifica capacidades mediante `/api/show` antes de inferencia con imágenes.
El contexto local inicial incluye hasta dos fragmentos documentales.

## Cambio de perfil documental

No mezclar vectores de distintos modelos aunque tengan las mismas dimensiones.
La recuperación filtra por chatbot, modelo y dimensiones. Para reprocesar
pendientes, fallidos o documentos listos con un perfil anterior:

```bash
docker compose exec backend python -m app.reindex_documents
```

Ejecutar sin cargas concurrentes. Sustituye los vectores del perfil anterior;
no requiere migración de columnas mientras se conserven 768 dimensiones.

## Verificación y diagnóstico

```bash
docker compose ps
docker compose exec ollama ollama ps
docker compose logs --tail=50 ollama
```

En el perfil GPU, comprobar además la VRAM visible:

```bash
docker compose -f docker-compose.yml -f docker-compose.gpu.yml exec ollama nvidia-smi
```

Consultar `ollama ps` durante una pregunta: con `keep_alive=0` la lista puede quedar
vacía al terminar. Verificar carga → fragmentos → recuperación → respuesta → métricas,
y una consulta con captura. Requisitos RF-08, RF-12, RF-14–RF-17 y RF-20–RF-26.

Fuentes oficiales:
- https://docs.ollama.com/docker
- https://docs.docker.com/desktop/features/gpu/
- https://docs.ollama.com/api/embed

El proxy de Next.js permite hasta 15 minutos para peticiones de procesamiento
documental; cada llamada individual a Ollama conserva su límite del backend.

Prueba real reproducible (crea dos chatbots temporales y los elimina al finalizar):

```bash
docker compose exec -T backend python < backend/scripts/verify_local_ollama.py
```

Ejecutarla después de que termine el reprocesamiento documental. Comprueba un
valor recuperado desde un documento, aislamiento entre chatbots, una imagen
sintética con dos barras y registro de métricas. No imprime credenciales.
La primera carga de modelos puede tardar varios minutos; el límite por llamada
local es 600 segundos. Este límite es operativo, no un objetivo de rendimiento.

## Resultado verificado en este equipo (2026-09-30)

- Ollama 0.35.0 dockerizado; instalación nativa retirada.
- GPU NVIDIA RTX 3050 Laptop, 4096 MiB visibles dentro del contenedor.
- `ollama ps`: Qwen3-VL 2B 100 % GPU, 1,7 GB reportados; EmbeddingGemma
  300M 100 % GPU, 681 MB reportados. Estas cifras no representan todo el
  consumo de VRAM del sistema.
- Tres documentos existentes listos, con 205 fragmentos locales en pgvector.
- Prueba real: carga de TXT, recuperación aislada por chatbot, respuesta correcta
  «137 unidades», reconocimiento de barra roja más alta y dos métricas exitosas.
- Consultas de prueba: 24,153 s (RAG) y 20,818 s (imagen). Son mediciones de esta
  ejecución, no garantías de latencia. La prueba inicial concurrente con
  reprocesamiento superó 180 s; ejecutar reprocesamiento sin consultas simultáneas.
- Backend: suite de 59 pruebas y prueba adicional de indisponibilidad de conexión
  aprobadas; frontend: 15 pruebas, compilación, TypeScript y lint aprobados.
- Los chatbots y documentos sintéticos de prueba se eliminaron al terminar.
- Las selecciones previas de proveedor de los chatbots existentes se conservan.
  Elegir `ollama / qwen3-vl:2b-instruct` en su configuración para usar respuestas locales.
