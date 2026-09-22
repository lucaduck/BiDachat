# Backend

API FastAPI ejecutable con conexión asíncrona a PostgreSQL y modelos SQLAlchemy para las siete tablas del esquema inicial. Antes de crear servicios o migraciones adicionales, revisar [el diseño de datos](../docs/database-design.md).

`api/` delega en `services/`; `rag/` y `llm/` aíslan procesamiento y proveedor. Las pruebas se ubicarán en `tests/` y se relacionarán con RF, RNF, RS y criterios CA del SRS.

## Ejecutar con Docker

Desde la raíz del repositorio, con el `.env` local configurado:

```powershell
docker compose up -d --build backend
docker compose ps
Invoke-RestMethod http://localhost:8000/api/v1/health
```

La respuesta esperada es `{"status":"ok"}`. La documentación interactiva está en <http://localhost:8000/api/v1/docs>. Este endpoint comprueba que la API responde; no comprueba PostgreSQL.

La autenticación administrativa expone `POST /api/v1/auth/login` y `POST /api/v1/auth/logout`. El login devuelve un token Bearer temporal; el logout revoca inmediatamente su digest persistido. Las credenciales inválidas, sesiones vencidas o revocadas y usuarios desactivados reciben una respuesta no autorizada sin detalles sensibles.

La gestión administrativa de chatbots expone:

- `GET /api/v1/llm-models`
- `GET /api/v1/chatbots`
- `POST /api/v1/chatbots`
- `GET /api/v1/chatbots/{chatbot_id}`
- `PUT /api/v1/chatbots/{chatbot_id}`
- `DELETE /api/v1/chatbots/{chatbot_id}`
- `GET /api/v1/chatbots/{chatbot_id}/documents`
- `POST /api/v1/chatbots/{chatbot_id}/documents`

Todas estas rutas requieren una sesión Bearer válida. `PUT` conserva el identificador del chatbot y permite cambiar nombre, descripción, instrucciones y una combinación ya registrada en `llm_models`. `created_by` conserva trazabilidad; no representa permiso exclusivo. La carga documental asocia cada fuente a un único chatbot y acepta PDF, DOCX, TXT y CSV de hasta 20 MiB. El original se guarda en un volumen privado con un nombre generado; no se entrega mediante rutas públicas.

En este equipo, el puerto 8000 ya estaba ocupado: el `.env` local usa `BACKEND_PORT=8001`. Acceder a <http://localhost:8001/api/v1/health> y <http://localhost:8001/api/v1/docs>. En nuevos entornos se usa 8000 por defecto; ajustar `NEXT_PUBLIC_API_BASE_URL` al puerto elegido cuando se implemente el frontend.

## Configuración

`app/core/config.py` carga `APP_ENV`, `DATABASE_URL`, `EMBEDDING_MODEL`, `EMBEDDING_DIMENSIONS`, `SESSION_TTL_MINUTES`, `DOCUMENT_STORAGE_PATH` y `DOCUMENT_MAX_SIZE_BYTES` mediante Pydantic Settings. Valores admitidos para `APP_ENV`: `development`, `test`, `production`. Las variables del proceso tienen prioridad sobre el `.env` raíz. Las variables de otros componentes se ignoran. `DATABASE_URL` se trata como secreto y no se incluye en mensajes públicos. El perfil RAG global es `gemini-embedding-2`/768; el servicio rechaza otro modelo o dimensión. El límite documental aprobado es 20 MiB. `SESSION_TTL_MINUTES` vale 480 por defecto y puede configurarse entre 1 y 10 080 minutos. `debug` permanece desactivado; en producción también se desactivan Swagger y OpenAPI.

Compose pasa explícitamente `APP_ENV` al backend y usa `BACKEND_PORT` para publicar el puerto local (8000 por defecto). El `.env` no se copia a la imagen. El proceso del contenedor corre con un usuario sin privilegios. Los errores inesperados devuelven un mensaje genérico; las trazas quedan en los registros internos del backend. La publicación en `127.0.0.1` está destinada al desarrollo local.

## Persistencia

`app/database/` crea el motor y las sesiones asíncronas. Cada servicio debe delimitar su transacción y confirmar con `commit()` solo cuando la operación completa haya terminado; una excepción dentro del contexto de sesión ejecuta `rollback()`.

`app/models/` representa `users`, `auth_sessions`, `llm_models`, `chatbots`, `documents`, `document_chunks` y `queries`. Las migraciones SQL continúan siendo la fuente del esquema; los modelos no crean ni alteran tablas durante el arranque. La dimensión actual de `document_chunks.embedding` es 768 y debe migrarse junto con el modelo si se aprueba otro perfil.

`app/services/authentication_service.py` valida credenciales, emite sesiones, comprueba expiración y actividad del usuario, y revoca sesiones. Las contraseñas se almacenan con scrypt y una sal aleatoria; los tokens de sesión se generan con entropía criptográfica y PostgreSQL conserva únicamente su digest SHA-256. BIDACHAT no ofrece registro público de investigadores.

`app/services/rag_knowledge_service.py` reclama documentos pendientes o fallidos, publica el lote completo de fragmentos mediante una unidad transaccional corta y recupera por distancia coseno. La consulta SQL filtra `chatbot_id`, estado `ready`, modelo y dimensión antes de ordenar resultados. Un fallo elimina resultados parciales y el reintento sustituye el conjunto sin duplicarlo. Este servicio cubre CA-UC04-03 a CA-UC04-05.

`app/services/document_service.py` cubre CA-UC03-02 y CA-UC04-01/02: valida y almacena originales privados, crea el documento en estado `pending` y lista únicamente las fuentes del chatbot solicitado. El procesamiento y publicación RAG se mantiene separado en `rag_knowledge_service.py`.

`app/services/query_service.py` crea el registro al admitir una consulta y conserva el modelo configurado en ese instante. Después marca éxito, fallo con duración observada o interrupción sin duración. `app/services/metrics_service.py` agrupa esos registros por chatbot; `GET /api/v1/chatbots/{chatbot_id}/metrics` exige sesión administrativa y acepta opcionalmente un periodo UTC semiabierto mediante `started_at` y `ended_at`, que deben enviarse juntos. El resumen separa estados y reporta la media de respuestas exitosas junto con su número de muestras; si no hay muestras devuelve `null`, no `0`.

`app/services/chatbot_deletion_service.py` bloquea el chatbot, obtiene las claves privadas de sus documentos y elimina la fila en la transacción. Las cascadas eliminan documentos, fragmentos y consultas. Solo tras el `commit` el endpoint elimina los originales del volumen; un rollback conserva los archivos. Las admisiones de carga y consulta toman un bloqueo compatible, por lo que no pueden crear trabajo durante el borrado. Una limpieza física fallida queda registrada internamente y nunca expone el archivo mediante la API.

## Desarrollo local

Se requiere Python 3.12 o posterior y [uv](https://docs.astral.sh/uv/). Desde la raíz:

```powershell
uv sync --project backend --locked
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

`pyproject.toml` declara dependencias; `uv.lock` fija versiones y `requirements.txt` exporta las dependencias de ejecución con hashes para Docker. Después de cambiar dependencias:

```powershell
uv sync --project backend
uv export --project backend --no-dev --no-emit-project --locked --output-file backend/requirements.txt
```

Ejecutar esos dos comandos desde la raíz del repositorio.

## Verificación

Desde `backend/`:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\ruff.exe format --check .
```

La prueba marcada `integration` usa `DATABASE_URL` y escribe datos temporales en PostgreSQL para comprobar persistencia y rollback; elimina el registro confirmado al finalizar. Si no existe la variable, pytest la omite:

```powershell
.\.venv\Scripts\python.exe -m pytest -m integration -vv
```

Las veintiuna pruebas comprueban salud/esquema API (RNF-01/RNF-04), configuración por entorno y secretos (RS-04), documentación desactivada en producción, errores sin detalles privados (RS-09), correspondencia de las siete tablas, persistencia y rollback, hashing de credenciales, sesiones revocables, CRUD/configuración de chatbots, carga documental autenticada, formatos y tamaño permitidos, aislamiento por chatbot, publicación RAG atómica, reintento, rechazo de perfiles incompatibles, aislamiento A/B, registros/agrupación de métricas con fallos e interrupciones y borrado con cascadas, rollback, limpieza privada y admisiones concurrentes. La ejecución y salud del contenedor verifican el arranque Docker (RNF-03); no validan todavía el despliegue completo del MVP.

Verificado el 2026-09-22: veintiuna pruebas aprobadas con Python 3.14.6, incluidas las integraciones PostgreSQL de autenticación, chatbots, documentos, RAG, métricas y borrado; Ruff sin errores y formato correcto. TestClient emitió dos avisos de deprecación de sus dependencias; las pruebas no fallaron. La imagen base Docker está fijada por digest y las dependencias de ejecución por versión y hash.

Referencias oficiales: [configuración FastAPI](https://fastapi.tiangolo.com/advanced/settings/) y [pruebas FastAPI](https://fastapi.tiangolo.com/tutorial/testing/).
