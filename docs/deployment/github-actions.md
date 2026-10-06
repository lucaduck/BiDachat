# Integración y despliegue con GitHub Actions

El repositorio utiliza dos ramas de entrega:

| Rama | Propósito |
| --- | --- |
| `develop` | Integración de cambios validados mediante pull request. |
| `production` | Versión liberada para el servidor de producción. Solo recibe cambios aprobados desde `develop`. |

`Continuous Integration` se ejecuta en cada pull request dirigido a cualquiera
de las dos ramas y en cada actualización de `develop` o `production`. Comprueba
formato, lint, pruebas de backend sobre PostgreSQL con pgvector, pruebas del
frontend, construcción del widget y construcción de las dos imágenes Docker.

Cuando la ejecución de integración para `production` termina correctamente,
`Publish and deploy production` publica las imágenes inmutables del backend y
frontend en GitHub Container Registry:

```text
ghcr.io/lucaduck/bidachat-backend:<commit-sha>
ghcr.io/lucaduck/bidachat-frontend:<commit-sha>
```

Las etiquetas `production` son una referencia práctica. El servidor recibe
siempre el SHA exacto validado por el flujo de integración.

## Preparar el repositorio

En GitHub, proteger `production` y exigir el resultado de `Continuous
Integration` antes de aceptar un pull request. Configurar el entorno
`production` y, si se desea, requerir aprobación manual antes del trabajo de
despliegue. El entorno permite limitar secretos y aprobar despliegues desde la
interfaz de GitHub.

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

## Preparar el servidor

El servidor debe tener Docker Engine, Docker Compose, una GPU NVIDIA con el
runtime de contenedores si se usará Ollama con GPU, y un clon de la rama
`production` en `DEPLOY_PATH`. Crear allí un archivo `.env` con las mismas
variables privadas de `.env.example`; no se sube a GitHub.

La aplicación se ejecuta con:

```bash
IMAGE_TAG=<sha-validado> docker compose -f docker-compose.production.yml up -d
```

Los puertos de frontend, backend y PostgreSQL se enlazan a `127.0.0.1`. Apache
o Nginx del servidor puede publicar HTTPS y redirigir al frontend. Al finalizar,
el flujo consulta `/api/v1/health` a través del frontend para confirmar que la
API quedó disponible.

Las migraciones existentes se conservan en el clon del servidor y se montan de
solo lectura durante la inicialización de PostgreSQL. Antes de añadir una nueva
migración, probarla sobre una copia de la base y realizar un respaldo, tal como
establece la guía de base de datos.
