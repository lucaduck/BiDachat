# Integración y despliegue con GitHub Actions

El repositorio utiliza dos ramas de entrega:

| Rama         | Propósito                                                                                       |
| ------------ | ----------------------------------------------------------------------------------------------- |
| `develop`    | Integración de cambios validados mediante pull request.                                         |
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

| Secreto                  | Valor                                                                             |
| ------------------------ | --------------------------------------------------------------------------------- |
| `DEPLOY_HOST`            | Nombre DNS o IP del servidor Linux.                                               |
| `DEPLOY_USER`            | Usuario limitado que ejecuta Docker Compose.                                      |
| `DEPLOY_PATH`            | Directorio del VPS que contiene `.env` y recibirá el paquete del commit aprobado. |
| `DEPLOY_SSH_PRIVATE_KEY` | Clave privada SSH del usuario de despliegue.                                      |
| `DEPLOY_KNOWN_HOSTS`     | Resultado verificado de `ssh-keyscan` del servidor.                               |

También puede crearse la variable `PRODUCTION_URL` para que GitHub muestre el
enlace público del sistema después de cada despliegue.

El flujo no habilita una conexión SSH hasta que `DEPLOY_ENABLED=true`. Esto
permite publicar imágenes y comprobar el pipeline antes de disponer del
servidor final.

## Secuencia para el primer despliegue en un VPS

1. Apuntar el dominio al VPS y preparar HTTPS en el proxy público del servidor.
   Ese proxy debe reenviar el tráfico a `http://127.0.0.1:<FRONTEND_PORT>`, conservar
   `Host` y establecer `X-Forwarded-Proto: https`. El puerto elegido queda
   accesible solo desde el propio VPS; no se abre PostgreSQL al exterior.
2. Instalar Docker Engine y Docker Compose. Seleccionar `OLLAMA_ACCELERATION=cpu`
   para un VPS sin GPU. Para GPU, establecer `OLLAMA_ACCELERATION=gpu`, instalar
   el controlador NVIDIA y NVIDIA Container Toolkit y comprobar que un
   contenedor puede usarla. El script de despliegue aplica el complemento GPU
   solo en ese segundo caso.
3. Crear un usuario de despliegue con acceso a Docker y acceso SSH por clave.
   Crear la ruta de `DEPLOY_PATH` con permiso de escritura para ese usuario.
   GitHub Actions transfiere los archivos de Compose y despliegue del commit
   aprobado por SSH; el VPS no necesita una clave adicional para clonar el
   repositorio privado.
4. Copiar `.env.example` como `.env` en esa ruta. Configurar al menos
   `POSTGRES_DB`, `POSTGRES_USER`, una contraseña aleatoria fuerte en
   `POSTGRES_PASSWORD`, `EMBEDDING_DIMENSIONS=768`, `ADMIN_EMAIL`,
   `ADMIN_PASSWORD`, `OLLAMA_ACCELERATION`, `OLLAMA_MODEL`, los diez límites
   `*_CPU_LIMIT` / `*_MEMORY_LIMIT` y los orígenes autorizados del widget.
   Los límites de `.env.example` son valores iniciales de desarrollo; obtener
   `nproc`, `free -h` y carga de los otros servicios en el VPS antes de fijar
   sus valores. Para procesar imágenes, elegir `VISION_PROVIDER` y
   `VISION_MODEL`. Por defecto se usa `OLLAMA_MODEL` si el proveedor visual es
   Ollama; debe tener capacidad visual, por ejemplo `qwen3-vl:2b-instruct`.
   En CPU, partir de `OLLAMA_MAX_LOADED_MODELS=1` y `OLLAMA_NUM_PARALLEL=1`.
   La prueba local de tres imágenes simples tardó cerca de siete minutos y
   observó al menos 2,88 GiB de RAM durante una descripción. En un VPS
   compartido puede elegirse una API visual externa autorizada; su clave
   queda solo en el backend y el envío de imágenes puede generar cargos.
   No prometer tiempos de ingestión sin medir el VPS.
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
6. El script de despliegue inicia Ollama y descarga los modelos configurados
   que todavía no estén en el volumen persistente: `OLLAMA_MODEL`,
   `EMBEDDING_MODEL` si el proveedor de embeddings es Ollama y `VISION_MODEL`
   cuando se haya configurado Ollama para descripción visual. Verificar que sus
   nombres coinciden exactamente con el `.env`; el bootstrap valida el modelo
   de respuesta antes de iniciar la API.
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

El servidor debe tener Docker Engine, Docker Compose y una ruta `DEPLOY_PATH`
escribible por el usuario de despliegue. `.env` permanece en esa ruta. Una GPU
NVIDIA y su runtime de contenedores solo
son necesarios si `.env` selecciona `OLLAMA_ACCELERATION=gpu`. Crear allí un
archivo `.env` con las mismas variables privadas de `.env.example`; no se sube
a GitHub.

La aplicación se ejecuta con:

```bash
IMAGE_TAG=<sha-validado> sh docker/deploy-production.sh
```

El script toma `OLLAMA_ACCELERATION` de `.env`. Con `cpu` arranca únicamente
el Compose de producción; con `gpu` añade `docker-compose.gpu.yml`, que solicita
una GPU NVIDIA. Ambos casos requieren los diez límites de CPU y memoria del
`.env`. Un valor ausente detiene el despliegue antes de descargar imágenes o
actualizar contenedores.

Solo Nginx publica el puerto de la aplicación en `127.0.0.1:3000` (configurable
con `FRONTEND_PORT`). El frontend, backend y PostgreSQL permanecen dentro de la
red de Docker. Si Apache del servidor termina HTTPS, debe enviar todo el tráfico
de la aplicación a ese único puerto. Al finalizar, el flujo valida y recarga la
configuración de Nginx y consulta `/api/v1/health` a través de este proxy.
La topología y el ejemplo de configuración externa están en
[Proxy inverso con Nginx](reverse-proxy.md).

Las migraciones y su corredor se transfieren con el commit aprobado. Tras
iniciar PostgreSQL, el despliegue registra instalaciones heredadas verificadas y
aplica únicamente migraciones pendientes antes de sustituir el backend. Un
esquema parcialmente aplicado detiene el despliegue. Antes de liberar una nueva
migración, probarla sobre una copia y realizar un respaldo verificado, tal como
establece la guía de base de datos.

## Puertos y recursos en un VPS compartido

El Compose de producción solo publica el puerto del Nginx contenedorizado:
`127.0.0.1:${FRONTEND_PORT:-3000}:80`. `FRONTEND_PORT=3005` puede usarse si el
3000 ya está ocupado, después de verificarlo con `ss -ltn` y actualizar el
destino del proxy HTTPS del host. Los puertos `BACKEND_PORT` y `POSTGRES_PORT`
del `.env.example` sirven para desarrollo; no publican backend ni PostgreSQL en
producción. Ollama tampoco publica puerto al host. La publicación en loopback
impide conexiones directas desde otra máquina, pero no sustituye las reglas de
red y TLS del servidor.

Los límites son obligatorios tanto en desarrollo como en producción. Los
valores de `.env.example` se eligieron para el entorno de desarrollo que muestra
7,7 GiB de RAM en Docker; el equipo físico dispone de 16 GB, pero Docker ve
menos. El inventario de lectura del 15 de octubre encontró en el VPS 4 CPU,
7,8 GiB de RAM, sin swap y alrededor de 2,5 GiB usados por otros servicios.
Su `.env` ya contiene los diez límites obligatorios: Ollama 2 CPU / 3 GiB,
backend 1 CPU / 768 MiB, frontend 1 CPU / 512 MiB, Nginx 0,25 CPU / 128 MiB y
PostgreSQL 1 CPU / 768 MiB. También se seleccionó OpenAI
(`VISION_PROVIDER=openai`, `VISION_MODEL=gpt-5.6-luna`) para describir fuentes
visuales. La [documentación del modelo](https://developers.openai.com/api/docs/models/gpt-5.6-luna)
confirma que acepta imágenes. El perfil de embeddings continúa en Ollama local.
La prueba del 15 de octubre devolvió `401 invalid_api_key` con la clave
configurada. Sustituir esa credencial en el `.env` privado y comprobar una
descripción real antes de dar por habilitada la ingestión de imágenes.
Antes del primer
despliegue, medir los picos de BIDACHAT durante ingestión y consultas. Fijar
presupuestos para los cinco servicios sin agotar la memoria del host; Ollama
merece especial atención por el tamaño de los modelos. Un límite demasiado
estricto puede producir OOM o errores al cargar un modelo. Definir en el `.env`
de cada máquina cada pareja `*_CPU_LIMIT` / `*_MEMORY_LIMIT` para `OLLAMA`,
`BACKEND`, `FRONTEND`, `NGINX` y `DATABASE`.
Las CPU admiten números como `1.5` y la memoria unidades Docker como `2g`.
Esos valores son ejemplos de formato, no presupuestos recomendados.

Antes de desplegar, validar el perfil que corresponde al VPS:

```bash
IMAGE_TAG=<sha-publicado> docker compose -f docker-compose.production.yml config --quiet
```

Si se usa GPU, añadir `-f docker-compose.gpu.yml`. El script de despliegue
selecciona los archivos automáticamente a
partir del `.env`. Después de arrancar, comprobar la publicación efectiva con
`docker compose -f docker-compose.production.yml ps` y los límites aplicados
con `docker inspect` sobre cada contenedor (`HostConfig.NanoCpus` y
`HostConfig.Memory`). Observar `docker stats`, fallos OOM y latencias de
consultas reales; ajustar los presupuestos a partir de esas mediciones. La
validación de Compose confirma sintaxis y configuración, pero no que el VPS
tenga capacidad suficiente. El máximo de memoria configurado para BIDACHAT es
aproximadamente 5,1 GiB; los otros servicios ya usaban alrededor de 2,5 GiB
cuando se tomó el inventario. El margen del host es pequeño: vigilar OOM y
reducir concurrencia o ampliar memoria si la medición real lo exige.
