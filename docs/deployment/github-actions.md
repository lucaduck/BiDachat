# Integración y despliegue con GitHub Actions

El repositorio utiliza dos ramas de entrega:

| Rama | Propósito |
| --- | --- |
| `develop` | Integración de cambios validados mediante pull request. |
| `production` | Versión liberada para el servidor de producción. Solo recibe cambios aprobados desde `develop`. |

`Continuous Integration` se ejecuta solo en pull requests dirigidos a `develop`
o `production`. Sus dos trabajos comprueban backend y frontend; el segundo
también construye el widget. No se ejecuta por `push` ni manualmente.

`Publish and deploy production` se activa únicamente al fusionar en
`production` un pull request de `develop`. Comprueba que una revisión aprobó el
último commit del PR y que `production` aún apunta al commit fusionado; entonces
valida Compose y publica las imágenes en GitHub Container Registry:

```text
ghcr.io/lucaduck/bidachat-backend:<commit-sha>
ghcr.io/lucaduck/bidachat-frontend:<commit-sha>
```

Las etiquetas `production` son una referencia práctica. El servidor recibe
siempre el SHA exacto validado por el flujo de integración.

## Preparar el repositorio

En GitHub, proteger `develop` y `production`: exigir pull request, al menos una
aprobación, invalidar aprobaciones tras nuevos commits y requerir los checks
`backend` y `frontend`. La publicación solo acepta PR de `develop` a
`production`; mantener esa política de ramas y no permitir saltarse la
protección. La CI corre antes de aprobar;
la publicación y el despliegue solo después de aprobar y fusionar. Configurar
el entorno `production` para limitar los secretos del despliegue.

Para habilitar el despliegue remoto, crear la variable de repositorio
`DEPLOY_ENABLED` con el valor `true` y, dentro del entorno `production`, crear
estos secretos:

| Secreto | Valor |
| --- | --- |
| `DEPLOY_HOST` | Nombre DNS o IP del servidor Linux. |
| `DEPLOY_USER` | Usuario limitado que ejecuta Docker Compose. |
| `DEPLOY_PATH` | Directorio donde está clonado el repositorio. |
| `DEPLOY_SSH_PRIVATE_KEY` | Clave privada SSH del usuario de despliegue. |
| `DEPLOY_KNOWN_HOSTS` | Resultado verificado de `ssh-keyscan` del servidor. |

También puede crearse la variable `PRODUCTION_URL` para que GitHub muestre el
enlace público del sistema después de cada despliegue.

El flujo no habilita una conexión SSH hasta que `DEPLOY_ENABLED=true`. Esto
permite publicar imágenes y comprobar el pipeline antes de disponer del
servidor final.

## Secuencia para el primer despliegue en un VPS

1. Apuntar el dominio al VPS y preparar HTTPS en el proxy público del servidor.
   Ese proxy debe reenviar el tráfico a `http://127.0.0.1:3000`, conservar
   `Host` y establecer `X-Forwarded-Proto: https`. El puerto 3000 queda
   accesible solo desde el propio VPS; no se abre PostgreSQL al exterior.
2. Instalar Docker Engine y Docker Compose. Seleccionar `OLLAMA_ACCELERATION=cpu`
   para un VPS sin GPU. Para GPU, establecer `OLLAMA_ACCELERATION=gpu`, instalar
   el controlador NVIDIA y NVIDIA Container Toolkit y comprobar que un
   contenedor puede usarla. El script de despliegue aplica el complemento GPU
   solo en ese segundo caso.
3. Crear un usuario de despliegue con acceso a Docker y acceso SSH por clave.
   Darle permiso de lectura al repositorio privado para que `git fetch` funcione
   desde el VPS. Clonar la rama `production` en la ruta que se pondrá en
   `DEPLOY_PATH`.
4. Copiar `.env.example` como `.env` en esa ruta. Configurar al menos
   `POSTGRES_DB`, `POSTGRES_USER`, una contraseña aleatoria fuerte en
   `POSTGRES_PASSWORD`, `EMBEDDING_DIMENSIONS=768`, `ADMIN_EMAIL`,
   `ADMIN_PASSWORD`, `OLLAMA_ACCELERATION`, `OLLAMA_MODEL` y los orígenes
   autorizados del widget. Para CPU usar `qwen3:1.7b`,
   `OLLAMA_MAX_LOADED_MODELS=1` y `OLLAMA_NUM_PARALLEL=1`. Para GPU pueden
   configurarse los modelos visuales aprobados según la VRAM disponible.
   Mantener el perfil de embeddings (`EMBEDDING_PROVIDER`, `EMBEDDING_MODEL`,
   `EMBEDDING_DIMENSIONS`) constante después de indexar documentos. Configurar
   claves de Gemini, OpenAI u OpenRouter solo si se usarán esos proveedores.
   `DATABASE_URL`, `BACKEND_PORT` y `DOCUMENT_STORAGE_PATH` del
   ejemplo no tienen que trasladarse a GitHub Actions: Compose construye la
   conexión interna y monta el volumen documental. `SESSION_TTL_MINUTES` sí
   puede ajustarse en el `.env` del VPS.
5. Si las imágenes GHCR son privadas, autenticar Docker en el VPS con una
   credencial de GitHub que tenga `read:packages`. Esta credencial es para
   `docker pull` en el VPS y no sustituye la clave SSH de despliegue. Si las
   imágenes son públicas, este paso no es necesario.
6. Descargar en Ollama los modelos configurados para respuesta y embeddings.
   Verificar que sus nombres coinciden exactamente con el `.env` antes del
   primer arranque; el bootstrap valida el modelo de respuesta.
7. Configurar en GitHub la variable de repositorio `DEPLOY_ENABLED=true`, la
   URL de producción y los cinco secretos SSH indicados arriba dentro del
   entorno `production`. Registrar en `DEPLOY_KNOWN_HOSTS` la clave pública del
   VPS solo después de contrastar su huella por un canal independiente.
8. Abrir un PR de `develop` a `production`, esperar los dos checks de CI,
   aprobar el último commit y fusionar. El flujo publica imágenes etiquetadas
   con el SHA fusionado y, si `DEPLOY_ENABLED=true`, las despliega en el VPS.
9. Comprobar el estado de los contenedores, `https://<dominio>/api/v1/health`,
   el inicio de sesión, una consulta real del widget y la persistencia de
   documentos. Mantener un respaldo de PostgreSQL y del volumen documental
   antes de actualizaciones con migraciones.

## Preparar el servidor

El servidor debe tener Docker Engine, Docker Compose y un clon de la rama
`production` en `DEPLOY_PATH`. Una GPU NVIDIA y su runtime de contenedores solo
son necesarios si `.env` selecciona `OLLAMA_ACCELERATION=gpu`. Crear allí un
archivo `.env` con las mismas variables privadas de `.env.example`; no se sube
a GitHub.

La aplicación se ejecuta con:

```bash
IMAGE_TAG=<sha-validado> sh docker/deploy-production.sh
```

El script toma `OLLAMA_ACCELERATION` de `.env`. Con `cpu` arranca únicamente
el Compose base; con `gpu` añade `docker-compose.gpu.yml`, que solicita una GPU
NVIDIA. Un valor distinto detiene el despliegue antes de actualizar contenedores.

Solo Nginx publica el puerto de la aplicación en `127.0.0.1:3000` (configurable
con `FRONTEND_PORT`). El frontend, backend y PostgreSQL permanecen dentro de la
red de Docker. Si Apache del servidor termina HTTPS, debe enviar todo el tráfico
de la aplicación a ese único puerto. Al finalizar, el flujo valida y recarga la
configuración de Nginx y consulta `/api/v1/health` a través de este proxy.
La topología y el ejemplo de configuración externa están en
[Proxy inverso con Nginx](reverse-proxy.md).

Las migraciones existentes se conservan en el clon del servidor y se montan de
solo lectura durante la inicialización de PostgreSQL. Antes de añadir una nueva
migración, probarla sobre una copia de la base y realizar un respaldo, tal como
establece la guía de base de datos.
