# Respaldo y comprobación de restauración

Este procedimiento corresponde a RNF-03, RNF-14 y RNF-15. El respaldo incluye el volcado lógico de PostgreSQL y los originales del volumen documental. Ejecútalo desde el checkout de producción con el usuario de despliegue; los archivos deben quedar fuera del repositorio y con acceso restringido.

## Preparar

En el VPS, crea un directorio privado. Ajusta la ruta a la ubicación real del checkout y del almacenamiento de respaldos:

```bash
install -d -m 700 /home/lucaduck/backups/bidachat
cd /home/lucaduck/domains/bidachat.lucaduck.com/docker/bidachat
```

El usuario de despliegue debe tener acceso a Docker y permisos de escritura en el directorio de respaldos. No copies `.env`, claves ni respaldos al repositorio. Antes de programar una tarea, ejecuta una vez el respaldo manual y la restauración aislada.

## Respaldar

```bash
BACKUP_DIR=/home/lucaduck/backups/bidachat \
BACKUP_RETENTION_DAYS=7 \
sh docker/backup-production.sh
```

El script valida Compose, detiene temporalmente el backend para impedir escrituras, ejecuta `pg_dump`, copia el volumen documental desde el contenedor, verifica el formato de ambos archivos, calcula SHA-256 y vuelve a iniciar el backend incluso si falla el respaldo. Publica el conjunto solo después de validarlo. La retención elimina directorios completos con manifiesto después de un respaldo exitoso; los conjuntos parciales se descartan. Durante la pausa, las consultas a la API pueden fallar: programa la tarea en una ventana acordada.

Comprueba que el backend vuelva a estar sano por el proxy y que el destino contiene `database.dump`, `documents.tar.gz`, `manifest.sha256` y `metadata.txt`.

## Restaurar en aislamiento para verificar

```bash
sh docker/verify-production-backup.sh \
  /home/lucaduck/backups/bidachat/bidachat-AAAAMMDDTHHMMSSZ
```

La verificación comprueba las huellas, crea un PostgreSQL temporal sin puerto de host, restaura el volcado, consulta las tablas principales y coteja cada archivo original asociado con el archivo comprimido. El contenedor y volumen temporales se eliminan al terminar, incluso ante error. **No modifica la base ni los documentos de producción.** Esta prueba confirma integridad técnica, pero una recuperación operativa completa también debe comprobar login, bots, asociaciones y consulta RAG en un despliegue aislado.

No programes la tarea diaria hasta observar un respaldo y una restauración aislada exitosos en el VPS. Entonces instala una entrada de `crontab` del usuario de despliegue, por ejemplo a las 02:15 UTC:

```cron
15 2 * * * cd /home/lucaduck/domains/bidachat.lucaduck.com/docker/bidachat && BACKUP_DIR=/home/lucaduck/backups/bidachat BACKUP_RETENTION_DAYS=7 sh docker/backup-production.sh >> /home/lucaduck/backups/bidachat/backup.log 2>&1
```

La hora de cron depende de la zona configurada en el VPS. Revisa el resultado y el espacio disponible; una tarea programada sin verificación de restauración no demuestra recuperabilidad. Define con el responsable la pérdida de datos y el tiempo de recuperación tolerables antes de aceptar el despliegue.
