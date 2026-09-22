# Base de datos

El diseño principal está en [docs/database-design.md](../docs/database-design.md). Contiene entidades, relaciones, restricciones, justificación, operación Docker y decisiones aprobadas para el MVP.

- `migrations/`: migración inicial SQL de creación y reversión del esquema.
- `seeds/`: inicialización controlada sin secretos ni datos privados versionados.
- `tests/`: comprobaciones de integridad ejecutadas dentro de PostgreSQL y revertidas al finalizar.

## Ejecución local con Docker

Desde la raíz del repositorio:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
# Completar POSTGRES_PASSWORD y revisar EMBEDDING_DIMENSIONS en .env
docker compose up -d database
docker compose ps
```

La primera creación del volumen ejecuta `001_initial_schema.up.sql`. `psql` recibe la dimensión desde `EMBEDDING_DIMENSIONS` después de validar que sea un entero positivo. Cambiarla después de crear el volumen no modifica una columna existente: requiere una migración y regenerar embeddings.

La inicialización local usa `vector(768)`. El perfil aprobado es `gemini-embedding-2`/768; cambiarlo exige una migración compatible y regenerar los embeddings.

Comprobación de integridad:

```powershell
Get-Content database/tests/verify_initial_schema.sql -Raw |
  docker compose exec -T database sh -c 'psql --set ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --set embedding_dimensions="$EMBEDDING_DIMENSIONS"'
```

Para detener la base sin borrar datos:

```powershell
docker compose stop database
```

El archivo `001_initial_schema.down.sql` documenta la reversión destructiva para una base de desarrollo vacía. No debe aplicarse sobre datos que deban conservarse sin respaldo y autorización explícita.

Esta configuración es local. Las credenciales permanecen en `.env`, excluido por Git; `.env.example` solo documenta variables. FastAPI es el único cliente de la base desde la aplicación; frontend y widget usan la API.

## Conexiones y persistencia

- Desde el equipo: `localhost:5433`, base `bidachat`, con las credenciales del `.env` local.
- Desde el futuro backend en la misma red Compose: host `database`, puerto `5432`.
- Frontend y widget se conectarán a la API, nunca a PostgreSQL.
- El volumen `bidachat_postgres_data` conserva los datos al detener o recrear el contenedor. `docker compose down` conserva el volumen; añadir `-v` lo eliminaría y no es una operación normal de apagado.
- Los scripts de inicialización solo se ejecutan en un volumen vacío. Editar el SQL no actualiza una base existente automáticamente.

Para aplicar la creación manualmente sobre un esquema vacío:

```powershell
docker compose exec -T database sh /docker-entrypoint-initdb.d/01-init-database.sh
```

La migración de reversión se comprobó en la base local sin filas, seguida inmediatamente de la creación. Las migraciones posteriores deberán añadirse como nuevos cambios SQL; no se borrará el volumen para actualizar una base con datos.

## Migraciones posteriores

No se editan migraciones ya aplicadas. Cada cambio de esquema añade una pareja numerada, por ejemplo `002_description.up.sql` y, cuando sea viable, `002_description.down.sql`. Antes de aplicarla se realiza un respaldo y se prueba en una copia de desarrollo. La migración debe ejecutarse en orden, con `ON_ERROR_STOP`, y registrar cualquier operación no reversible.

Para aplicar una migración adicional ya incluida en la imagen:

```powershell
Get-Content database/migrations/002_description.up.sql -Raw |
  docker compose exec -T database sh -c 'psql --set ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB"'
```

Después, ejecutar la comprobación de integridad y las pruebas del backend. No se usa `docker compose down -v` como mecanismo de migración: elimina datos.

## Respaldo y restauración

Los datos persistentes se dividen entre PostgreSQL (`postgres_data`) y los originales privados de documentos (`bidachat_document_storage`). Un respaldo recuperable debe incluir ambos, tomados mientras el backend está detenido para evitar escrituras durante la copia.

```powershell
docker compose stop backend
New-Item -ItemType Directory -Force backups | Out-Null
$backupName = "bidachat-$(Get-Date -Format yyyyMMdd-HHmmss)"
docker compose exec -T database sh -c 'pg_dump --format=custom --username "$POSTGRES_USER" --dbname "$POSTGRES_DB"' `
  > "backups/$backupName.postgres.dump"
docker run --rm -v bidachat_document_storage:/source:ro -v "${PWD}/backups:/backup" alpine `
  tar -C /source -czf "/backup/$backupName.documents.tar.gz" .
docker compose start backend
```

Los archivos de `backups/` están ignorados por Git. Guardarlos cifrados y con control de acceso fuera del repositorio, porque contienen preguntas, respuestas y documentos privados. Verificar el archivo de PostgreSQL sin modificar la base:

```powershell
Get-Content "backups/$backupName.postgres.dump" -AsByteStream |
  docker compose exec -T database sh -c 'pg_restore --list --username "$POSTGRES_USER"'
```

La restauración sobrescribe el contenido de los volúmenes. Requiere una ventana de mantenimiento, un respaldo actual y autorización explícita. Detener backend, restaurar PostgreSQL y después los originales en el volumen privado:

```powershell
docker compose stop backend
Get-Content "backups/$backupName.postgres.dump" -AsByteStream |
  docker compose exec -T database sh -c 'pg_restore --clean --if-exists --no-owner --username "$POSTGRES_USER" --dbname "$POSTGRES_DB"'
docker run --rm -e BACKUP_NAME=$backupName -v bidachat_document_storage:/target -v "${PWD}/backups:/backup:ro" alpine `
  sh -c 'rm -rf /target/* && tar -C /target -xzf "/backup/$BACKUP_NAME.documents.tar.gz"'
docker compose start backend
```

Tras restaurar, verificar `docker compose ps`, `GET /api/v1/health`, el conteo esperado de documentos y una consulta administrativa autenticada. Nunca restaurar solo PostgreSQL si se necesita reprocesar los originales asociados.
