# Contenedores

Contiene la inicialización de PostgreSQL + pgvector del MVP (RNF-03). `docker-compose.yml` se encuentra en la raíz y monta `postgres_data` como volumen persistente.

`postgres/init-database.sh` valida la dimensión de embeddings y la pasa a `psql` para ejecutar la migración inicial únicamente cuando Docker crea un volumen de datos vacío. La imagen está fijada por digest y la base solo se publica en `127.0.0.1:5433` para desarrollo local.

`backend.Dockerfile` ejecuta FastAPI con Python 3.12 y Uvicorn, dependencias
fijadas y usuario sin privilegios. Compose publica la API en `127.0.0.1:8000`,
comprueba `/api/v1/health` y espera a PostgreSQL antes de iniciarla.
`.dockerignore` limita el contexto de construcción a código y dependencias,
excluyendo secretos y archivos locales.

`frontend.Dockerfile` compila Next.js y publica el panel, el widget y la página
de ejemplo. Compose incluye `frontend` en el puerto local 3000. El backend
inicializa el administrador y los modelos desde variables privadas al arrancar.
Los originales documentales se conservan en el volumen privado
`bidachat_document_storage`.

## Ollama con GPU

Compose incorpora `ollama` con una GPU NVIDIA y volumen `ollama_models`, sin
publicar su API al host. FastAPI se conecta a `http://ollama:11434`.
Instalación de modelos y verificación: [guía local](../docs/local-ollama.md).
