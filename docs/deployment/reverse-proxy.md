# Nginx como proxy inverso de BIDACHAT

## Flujo aprobado

```text
Navegador o widget externo
        |
        v
HTTPS del servidor (Apache, si existe)
        |
        v
Nginx en Docker · 127.0.0.1:3000
        |                       |
        | /api/v1/*             | resto de rutas
        v                       v
FastAPI:8000                Next.js:3000
        |
        v
PostgreSQL y Ollama internos
```

El navegador recibe panel, vista previa, script del widget y API bajo el mismo
origen. Nginx conserva la ruta y el método al enviar `/api/v1/*` a FastAPI; las
demás rutas van a Next.js. Las reglas están en
[`docker/nginx/default.conf`](../../docker/nginx/default.conf). El rewrite de
Next.js sigue disponible para ejecutar el frontend fuera de Compose durante
desarrollo. El widget envía sus consultas a la API REST por HTTP `POST`.

## Puertos y seguridad

`FRONTEND_PORT` conserva el puerto público local actual (3000 por defecto), pero
ahora lo publica el contenedor Nginx, limitado a `127.0.0.1`. En desarrollo,
FastAPI y PostgreSQL mantienen sus puertos locales de diagnóstico. En
producción, frontend, backend, PostgreSQL y Ollama permanecen dentro de la red
de Compose; solo Nginx publica el puerto local.

El contenedor recibe HTTP del propio servidor. En producción, Apache puede
terminar HTTPS y reenviar las solicitudes a `http://127.0.0.1:3000`, conservando
el encabezado `Host` y enviando `X-Forwarded-Proto: https`. Apache debe
reemplazar cualquier `X-Forwarded-For` aportado por clientes externos antes de
añadir la IP real. El TLS, el certificado y la redirección de HTTP a HTTPS se
configuran en ese punto de entrada público para cumplir `RS-03`. Si se usa otro
terminador TLS, debe cumplir las mismas condiciones.

Nginx permite cuerpos de hasta 25 MiB para que el límite documental de 20 MiB
y la codificación de las imágenes lleguen a la validación de FastAPI. Para la
API espera hasta 660 segundos entre lecturas, por encima del máximo configurado
para Ollama. El proxy reconsulta el DNS interno de Docker cuando se recrea un
contenedor. FastAPI acepta los encabezados de proxy porque en producción no
publica su puerto al host; así el límite de consultas del widget puede usar la
IP del cliente recibida a través del proxy.

## Arranque local

Con `.env` configurado y los modelos de Ollama descargados:

```bash
docker compose up -d --build
docker compose ps
curl --fail http://127.0.0.1:3000/api/v1/health
curl --fail http://127.0.0.1:3000/
```

La documentación interactiva de FastAPI está en
`http://127.0.0.1:3000/api/v1/docs` cuando `APP_ENV=development`. El script
embebible se sirve en `http://127.0.0.1:3000/bidachat-widget.js`. En producción
la documentación interactiva está deshabilitada.

## Verificación y aceptación

1. `docker compose config --quiet` y su variante de producción validan la
   estructura y los puertos.
2. `nginx -t` valida la configuración antes del despliegue.
3. `/`, `/preview`, `/bidachat-widget.js` y `/api/v1/health` responden por
   Nginx; una petición administrativa sin token mantiene el `401` de FastAPI.
4. Una carga superior al límite de Nginx recibe `413` sin llegar al backend.
5. Al recrear frontend o backend, Nginx vuelve a resolver sus direcciones
   internas sin cambiar el origen visible al navegador.

El pipeline de producción prueba la configuración, actualiza el contenedor y
recarga Nginx para aplicar cambios en el archivo montado. El script
[`docker/deploy-production.sh`](../../docker/deploy-production.sh) espera hasta
40 segundos a que la API responda a través del puerto publicado por Nginx.
