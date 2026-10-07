# Contenedores

Contiene la inicialización de PostgreSQL + pgvector del MVP (RNF-03). `docker-compose.yml` se encuentra en la raíz y monta `postgres_data` como volumen persistente.

`postgres/init-database.sh` valida la dimensión de embeddings y la pasa a `psql` para ejecutar la migración inicial únicamente cuando Docker crea un volumen de datos vacío. La imagen está fijada por digest y la base solo se publica en `127.0.0.1:5433` para desarrollo local.

`backend.Dockerfile` ejecuta FastAPI con Python 3.12 y Uvicorn, dependencias
fijadas y usuario sin privilegios. Compose publica la API en `127.0.0.1:8000`,
comprueba `/api/v1/health` y espera a PostgreSQL antes de iniciarla.
`.dockerignore` limita el contexto de construcción a código y dependencias,
excluyendo secretos y archivos locales.

`frontend.Dockerfile` compila Next.js, el widget y la página de ejemplo.
`nginx/default.conf` dirige `/api/v1/*` al backend y el resto al frontend.
Compose publica Nginx en el puerto local 3000; el frontend queda en la red
interna. El backend inicializa el administrador y los modelos desde variables
privadas al arrancar.
Los originales documentales se conservan en el volumen privado
`bidachat_document_storage`.

## Ollama con CPU o GPU

El Compose base incorpora `ollama` y el volumen `ollama_models`, sin publicar
su API al host. FastAPI se conecta a `http://ollama:11434`.

La producción selecciona el perfil mediante `OLLAMA_ACCELERATION` en `.env`:

- `cpu`: perfil predeterminado, compatible con VPS sin GPU.
- `gpu`: añade `docker-compose.gpu.yml` y requiere NVIDIA Container Toolkit.

El script `deploy-production.sh` valida el valor y aplica el archivo adicional
solo para el perfil GPU. Instalación de modelos y verificación:
[guía local](../docs/local-ollama.md).
