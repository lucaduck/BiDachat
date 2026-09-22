# Contenedores

Contiene la inicialización de PostgreSQL + pgvector del MVP (RNF-03). `docker-compose.yml` se encuentra en la raíz y monta `postgres_data` como volumen persistente.

`postgres/init-database.sh` valida la dimensión de embeddings y la pasa a `psql` para ejecutar la migración inicial únicamente cuando Docker crea un volumen de datos vacío. La imagen está fijada por digest y la base solo se publica en `127.0.0.1:5433` para desarrollo local.

`backend.Dockerfile` ejecuta FastAPI con Python 3.12 y Uvicorn, dependencias fijadas y usuario sin privilegios. Compose publica la API en `127.0.0.1:8000` y comprueba `/api/v1/health`. El backend todavía no abre conexiones a PostgreSQL; ambos servicios pueden arrancar de forma independiente. `.dockerignore` limita el contexto de construcción a código y dependencias, excluyendo secretos y archivos locales.

Los Dockerfiles del frontend y widget se añadirán cuando esos servicios sean ejecutables. Los originales documentales necesitarán un volumen privado persistente separado de los recursos públicos.
