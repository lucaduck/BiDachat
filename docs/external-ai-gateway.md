# Gateway privado de proveedores externos

LiteLLM centraliza el tráfico de generación de los proveedores externos que
figuran en `EXTERNAL_AI_GATEWAY_PROVIDERS`. El gateway está dentro de la red de
Docker, no publica un puerto al host y solo acepta solicitudes autenticadas del
backend mediante `LITELLM_MASTER_KEY`.

```text
Widget / panel -> FastAPI -> LiteLLM privado -> API externa configurada
                         -> Ollama local
                         -> embeddings Ollama o Gemini
```

El gateway no recibe consultas de navegadores, no utiliza una base de datos ni
habilita callbacks, telemetría o registros de mensajes. FastAPI conserva RAG,
memoria, guardrails, rate limiting y métricas. Ollama y los embeddings no se
desvían al gateway: cambiar esa ruta requeriría revalidar las representaciones
vectoriales existentes.

## Configuración

Declara únicamente los proveedores que tienen un modelo explícito y una clave
válida. El ejemplo completa los cuatro proveedores admitidos:

```dotenv
EXTERNAL_AI_GATEWAY_PROVIDERS=gemini,openai,openrouter,vertex
GEMINI_MODEL=gemini-2.5-flash
OPENAI_MODEL=gpt-4.1-mini
OPENROUTER_MODEL=openai/gpt-4.1-mini
VERTEX_ENABLED=true
VERTEX_MODEL=gemini-3.1-flash-lite
LITELLM_MASTER_KEY=<valor-aleatorio-de-32-o-más-caracteres>
```

Se puede configurar más de un modelo por proveedor mediante `GEMINI_MODELS`,
`OPENAI_MODELS`, `OPENROUTER_MODELS` o `VERTEX_MODELS`, separados por comas.
El valor singular permanece como selección compatible cuando la lista está
vacía. El panel solo ofrece modelos del catálogo configurado.

| Proveedor | Identificador configurado | Ruta del gateway | Imagen | Credencial que usa LiteLLM |
| --- | --- | --- | --- | --- |
| Gemini API | `GEMINI_MODEL(S)` | Chat Completions | Según el modelo habilitado | `GEMINI_API_KEY` |
| OpenAI | `OPENAI_MODEL(S)` | Responses con `store:false` | Según el modelo habilitado | `OPENAI_API_KEY` |
| OpenRouter | `OPENROUTER_MODEL(S)` completo | Chat Completions | Según el modelo habilitado | `OPENROUTER_API_KEY` |
| Vertex AI | `VERTEX_MODEL(S)` | Chat Completions | Según el modelo habilitado | JSON de cuenta de servicio |

Los modelos de texto no se deben declarar como visuales. La capacidad de imagen
se confirma por modelo durante la aceptación real; el catálogo solo expresa qué
modelos puede solicitar la aplicación.

LiteLLM recibe un alias interno `proveedor/modelo`, por ejemplo
`vertex/gemini-3.1-flash-lite` u `openrouter/openai/gpt-4.1-mini`. El panel y la
base de datos conservan `proveedor` y `modelo` por separado; el alias evita que
dos proveedores con el mismo ID se confundan.

Para levantar el gateway:

```bash
docker compose --profile ai-gateway up -d --wait litellm
```

Si se incluye `vertex`, añada también el override que monta el JSON de la cuenta
de servicio en solo lectura:

```bash
docker compose -f docker-compose.yml -f docker-compose.vertex.yml \
  --profile ai-gateway up -d --wait litellm
```

`docker/deploy-production.sh` detecta la lista y añade el perfil y override
necesarios. La compatibilidad heredada `VERTEX_ENABLED=true` con el perfil
`vertex` sigue disponible mientras se completa la migración.

## Seguridad y límites

- Las claves permanecen en variables de entorno de contenedores; no se añaden a
  modelos, respuestas, frontend ni widget.
- Gemini puede requerir que FastAPI conserve su clave cuando se usa como
  proveedor de embeddings. Esa excepción no permite que el navegador la use.
- Mientras exista una ruta directa heredada, las claves de OpenAI y OpenRouter
  pueden seguir presentes en FastAPI para conservar instalaciones previas. Al
  migrar ambos proveedores, FastAPI no las consulta para generación; retirarlas
  del contenedor backend es el cierre pendiente de la transición.
- No hay fallback ni reintento automático: un fallo del gateway devuelve un
  error seguro para el proveedor/modelo elegido.
- OpenRouter puede decidir su enrutamiento interno; LiteLLM no controla esa
  decisión del proveedor.
- OpenAI mantiene `store:false` por medio de `/v1/responses`. El soporte real
  debe verificarse con el digest de LiteLLM desplegado antes de producción.

## Verificación

Las pruebas automatizadas cubren contrato HTTP con respuestas sintéticas. La
aceptación real requiere claves, presupuesto autorizado y una prueba por modelo
para texto e imagen. Registre proveedor, modelo, versión/digest, fecha,
resultado, latencia y consumo sin copiar prompts, respuestas o secretos.

Para revertir, retire el proveedor de `EXTERNAL_AI_GATEWAY_PROVIDERS`, restaure
la configuración o imagen anterior y recree los servicios. La operación no
elimina chatbots, conversaciones, consultas, documentos ni embeddings.
