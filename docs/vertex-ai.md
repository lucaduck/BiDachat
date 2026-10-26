# Vertex AI mediante LiteLLM

BIDACHAT incorpora Vertex como proveedor opcional. El frontend y el widget usan
la API REST; FastAPI envía el contexto al gateway LiteLLM en la red Docker y este
se autentica ante Google. Los embeddings siguen usando el perfil RAG existente.

## Preparación

Se requiere un proyecto Google Cloud con facturación, API
`aiplatform.googleapis.com` habilitada y una cuenta de servicio con permiso de
inferencia (rol inicial `roles/aiplatform.user`). La cuenta de ejecución no
necesita permisos para habilitar APIs ni administrar facturación. Obtener un
token prueba la autenticación; generar una respuesta comprueba también permisos,
modelo y disponibilidad del servicio.

Guarda el JSON fuera del repositorio. En WSL utiliza una ruta `/mnt/d/...`;
Docker debe poder leerla. En Linux protege su carpeta y archivo con permisos
700/600 para su propietario. En una unidad Windows controla también sus ACL;
`chmod` sobre esa unidad puede no aplicar la protección esperada.

## Configuración local

Con el `.env` existente, desde la raíz y dentro de WSL:

```bash
python3 docker/litellm/configure-local.py \
  --credentials /ruta/privada/cuenta-de-servicio.json \
  --model gemini-3.1-flash-lite \
  --location global
```

El script conserva las otras variables, obtiene el proyecto del JSON y genera
una clave interna aleatoria si falta. Añade `vertex` a
`EXTERNAL_AI_GATEWAY_PROVIDERS` y el perfil `ai-gateway`. El archivo JSON no se
copia al repositorio. Selecciona un modelo habilitado en tu proyecto;
`global` no garantiza residencia en una región concreta.

```bash
docker compose -f docker-compose.yml -f docker-compose.vertex.yml \
  --profile ai-gateway config --quiet
docker compose -f docker-compose.yml -f docker-compose.vertex.yml \
  --profile ai-gateway up -d --wait litellm
docker compose exec -T litellm python /app/bidachat/verify.py
```

El último comando verifica autenticación y catálogo sin generar texto. Para
autorizar una única consulta facturable y comprobar la respuesta:

```bash
docker compose exec -T litellm python /app/bidachat/verify.py --generate
docker compose up -d --build
```

En el panel, abre **Chatbots → editar → Comportamiento**, selecciona
**Vertex AI**, el modelo configurado y guarda. Prueba una pregunta y un adjunto
desde Publicación. En Configuración, “configurado” indica presencia de ajustes,
no una comprobación continua de conectividad.

## Variables

| Variable | Uso |
| --- | --- |
| `VERTEX_ENABLED` | `true` habilita Vertex en FastAPI |
| `EXTERNAL_AI_GATEWAY_PROVIDERS` | Debe incluir `vertex` para enrutarlo mediante LiteLLM |
| `VERTEX_PROJECT` | Proyecto consumidor de Vertex |
| `VERTEX_LOCATION` | Ubicación compatible, por ejemplo `global` |
| `VERTEX_MODEL` | ID explícito de un modelo Gemini multimodal |
| `VERTEX_MODELS` | Lista separada por comas de modelos comprobados y seleccionables; debe contener `VERTEX_MODEL` |
| `VERTEX_CREDENTIALS_FILE` | Ruta absoluta del JSON en el host |
| `LITELLM_MASTER_KEY` | Secreto compartido de al menos 32 caracteres |
| `LITELLM_CPUS` | Límite de CPU obligatorio para ejecutar el gateway |
| `LITELLM_MEMORY_LIMIT` | Límite de memoria obligatorio para ejecutar el gateway |

Compose fija `LITELLM_BASE_URL=http://litellm:4000` en el backend y
`GOOGLE_APPLICATION_CREDENTIALS=/run/secrets/vertex-service-account.json` en
LiteLLM. Solamente el gateway monta el JSON, en lectura. Los valores de recurso
por defecto del YAML permiten resolver el perfil inactivo; el lanzador rechaza
el perfil activo si faltan límites explícitos en el entorno.

El perfil visual de fuentes es independiente. Para usar Vertex también en la
descripción de documentos PNG/JPEG/WebP, configura explícitamente
`VISION_PROVIDER=vertex` y `VISION_MODEL` igual a `VERTEX_MODEL`. Esto no cambia
las fuentes ya procesadas ni requiere reindexar al cambiar el modelo conversacional.

Para habilitar más de una opción, verifica cada identificador antes de añadirlo:

```bash
VERTEX_MODELS=gemini-3.1-flash-lite,otro-modelo-comprobado
VERTEX_MODEL=gemini-3.1-flash-lite
docker compose up -d --force-recreate litellm backend
docker compose exec -T litellm python /app/bidachat/verify.py --model otro-modelo-comprobado --generate
docker compose exec -T backend python -m app.bootstrap
```

`VERTEX_MODEL` define el modelo predeterminado y debe pertenecer a
`VERTEX_MODELS`. El bootstrap registra de forma idempotente cada combinación
habilitada. Las filas retiradas permanecen para conservar el modelo ejecutado en
consultas anteriores, pero dejan de aparecer en el editor. La generación real
debe confirmar acceso, ubicación, texto y visión en el proyecto que realizará el
despliegue antes de exponer un identificador nuevo.

## Operación y reversión

La imagen LiteLLM está fijada por versión/digest; funciona sin base adicional,
panel administrativo, fallback ni reintentos automáticos. No publica el puerto
4000 al host. `docker compose ps` puede mostrar `4000/tcp`: eso identifica el
puerto interno de la imagen, no un puerto publicado.

Para renovar una credencial, reemplaza la ruta privada con el script local y
ejecuta `docker compose up -d --force-recreate litellm`; después vuelve a verificar.
La revocación de la clave antigua se administra en Google cuando hayas confirmado
que ningún entorno la necesita.

Para desactivar: reasigna los chatbots a un proveedor disponible y restaura el
perfil visual si apuntaba a Vertex. Establece `VERTEX_ENABLED=false`, retira
`vertex` de `EXTERNAL_AI_GATEWAY_PROVIDERS`, detén LiteLLM y recrea el backend. Los modelos
retirados conservan sus referencias históricas, pero no se pueden seleccionar.

En producción, `docker/deploy-production.sh` activa el perfil según
`VERTEX_ENABLED`, verifica archivos/variables y espera la salud del gateway.
Actions transfiere su configuración, nunca el JSON. Ajusta los recursos antes
de desplegar en un VPS compartido. El despliegue sigue el PR aprobado e integrado.

## Comprobaciones y límites

### Verificación local de credencial

El 15 de octubre de 2026 se actualizó la credencial local y se recreó el gateway.
La autenticación dentro de Docker y una generación real se verificaron en el
proyecto `bidachat-production-principal`, con `gemini-3.1-flash-lite`.
La prueba mínima devolvió «listo»: 5 tokens de entrada, 1 de salida y 2011 ms.
Es una muestra de conectividad, no una medición representativa del chatbot.
El JSON permanece fuera del repositorio y no se incluye en las imágenes.

El 16 de octubre de 2026 se verificó también `gemini-3.5-flash` y se incorporó
al catálogo local. La prueba de texto devolvió «listo» con 5 tokens de entrada,
97 de salida incluidos 95 de razonamiento y 35078 ms. Las pruebas visuales de
ambos modelos identificaron correctamente un PNG rojo de 1 × 1 píxel:
`gemini-3.1-flash-lite` utilizó 1099 tokens de entrada, 2 de salida y 1622 ms;
`gemini-3.5-flash` utilizó 1099 de entrada, 121 de salida incluidos 119 de
razonamiento y 10492 ms. Estas llamadas comprueban acceso y modalidad en este
proyecto; no comparan calidad ni representan latencia habitual.

Siguen pendientes la aceptación completa de una captura real a través del widget
desde otro origen y el despliegue al VPS. El detalle se mantiene en
[las tareas del cambio](../openspec/changes/add-vertex-ai-gateway/tasks.md).

### Diagnóstico

- Sin clave interna: rechazo 401. Credenciales Google inválidas: error de autenticación.
- 403: comprobar permisos y API; 429: cuota; timeout/503: disponibilidad.
- Respuesta vacía, bloqueada, incompleta o de otro modelo: error seguro, sin éxito falso.
- El historial conserva el modelo solicitado y validado. Un nombre flotante de Google
  no identifica necesariamente la revisión física interna del modelo.
- El gateway sin base de datos no impone un presupuesto monetario global.
  Las pruebas deben acotar llamadas/tokens y registrar uso; las alertas de Google
  no equivalen a un corte automático.

Referencias: [Vertex en LiteLLM](https://docs.litellm.ai/docs/providers/vertex),
[ejecución sin base adicional](https://docs.litellm.ai/docs/proxy/docker_quick_start),
[precios de Google](https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing).
