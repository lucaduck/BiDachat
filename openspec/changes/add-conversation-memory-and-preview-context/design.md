## Context

Véase [proposal.md](proposal.md). La implementación actual registra cada
consulta en `queries` para métricas, incluyendo modelo, pregunta, respuesta,
estado y duración, pero no tiene una entidad de conversación ni pasa historia a
`LlmProvider.answer`. Por eso la persistencia existente es de auditoría y
métricas, no memoria para el modelo.

La ampliación aprobada el 18 de octubre añade aislamiento opcional por identidad
firmada. El servidor anfitrión emite una credencial HMAC de vida corta para un
seudónimo opaco; BIDACHAT comprueba chatbot, origen, vigencia y firma, y guarda
solo un hash del seudónimo en la conversación. La clave de firma se deriva de
una clave maestra para cada chatbot y origen y permanece en servidores. El widget
solicita una credencial nueva a un endpoint del propio sitio antes de cada mensaje.
Si está configurado y falla, no debe degradarse al modo anónimo. El reinicio por
inactividad tiene un valor inicial configurable de 30 minutos. La limpieza se
ejecuta en el ciclo de vida del backend, periódicamente y al iniciar.

El widget ya recopila `page_context` desde `data-context-selector` en cada
envío y lo limita a 6000 caracteres. Las pruebas externas lo confirman. La ruta
`/preview`, en cambio, no declara el atributo y por eso la demostración no usa
el tablero que muestra. `docs/database-design.md` define siete tablas iniciales
y será actualizado antes de aplicar una migración.

Vertex funciona localmente mediante LiteLLM con el proyecto
`bidachat-production-principal` y el modelo `gemini-3.1-flash-lite`. Actualmente
la configuración acepta un modelo único y el bootstrap registra una entrada
correspondiente.

## Goals / Non-Goals

**Goals:**

- Persistir una memoria conversacional mínima, anónima, aislada y expirable.
- Enviar al modelo una ventana de turnos recientes sin alterar RAG, guardrails,
  métricas, adjuntos ni el contrato REST de los proveedores.
- Hacer que la página Preview pruebe el contexto visible del tablero con el
  mecanismo ya usado por integraciones externas.
- Configurar varios modelos Vertex explícitos sin descubrir dinámicamente toda
  la oferta de Google ni permitir destinos arbitrarios.

**Non-Goals:**

- Cuentas de usuario para visitantes, memoria entre navegadores, perfiles
  personales, resúmenes generados por LLM, WebSocket, Redis, nueva base de
  datos, rastreo de toda la página por defecto o almacenamiento de imágenes de
  consultas.

## Decisions

### 1. Conversación anónima separada de las métricas

Se añadirán `conversations` y `conversation_messages`. Una conversación tendrá
un UUID opaco entregado por el widget, `chatbot_id`, una huella del origen
normalizado, estado y fechas de creación/última actividad/expiración. Cada
mensaje tendrá conversación, rol, contenido textual limitado, referencia
opcional a `query_id`, y fecha. La relación será:

```text
chatbots 1 ── N conversations 1 ── N conversation_messages
                         │
                         └── N queries (por conversation_id nullable)
```

`queries` seguirá siendo la fuente de métricas y de modelo ejecutado. La nueva
relación permite unir auditoría y conversación sin guardar la imagen ni duplicar
respuesta. Un `conversation_id` nullable mantiene compatibilidad con consultas
antiguas y clientes que aún no lo envíen. La eliminación de chatbot cascada a
conversaciones y mensajes; una limpieza por expiración elimina solo memoria,
no `queries`.

Alternativa descartada: reconstruir historia desde `queries` por chatbot. Eso
mezclaría visitantes distintos, no daría expiración independiente y expondría
datos de conversaciones ajenas.

### 2. Identificador y alcance del navegador

El widget generará `crypto.randomUUID()` y lo mantendrá en `sessionStorage`
con clave que incluya el `chatbot_id` y el origen. Así sobrevive a una recarga de
la pestaña, pero no se reutiliza en otro sitio u otro chatbot. Se enviará como
`conversation_id` en el cuerpo existente de `POST /api/v1/chatbots/{id}/queries`;
no se crean WebSocket, cookies de seguimiento ni endpoint de lectura.

FastAPI validará UUID, origen y chatbot. Para solicitudes sin identificador se
creará una conversación efímera compatible mientras se actualizan widgets. Se
recomienda requerirlo una vez completada la migración del widget.

### 3. Ventana de memoria y retención

La configuración propuesta es `CONVERSATION_MAX_TURNS=12`,
`CONVERSATION_MAX_CHARS=12000` y `CONVERSATION_TTL_HOURS=24`. Antes de enviar
al modelo se tomarán los mensajes más recientes que satisfagan ambos límites,
con sus roles claramente delimitados como historia no confiable. El mensaje
actual, RAG y contexto visible se conservan como bloques separados. Las imágenes
solo viajan en la consulta actual y nunca se convierten en memoria almacenada.

Los valores se documentan como valores iniciales de operación, no como umbrales
del SRS; se expondrán en `.env.example` y se validarán. Una tarea de limpieza
reutilizará PostgreSQL y será invocable desde el despliegue o un job controlado;
no se añade un scheduler o servicio nuevo.

Alternativa descartada: enviar todo el historial. Tiene crecimiento ilimitado,
costo impredecible y retención excesiva de información.

### 4. Transacción y fallos

Al recibir la consulta, el servicio validará o creará la conversación y
registrará `Query` en procesamiento. Tras una respuesta válida persistirá en la
misma unidad de trabajo el turno del usuario, el turno asistente y la consulta
completada. Si el proveedor falla, `Query` queda fallida y no se persiste una
respuesta de asistente inexistente. Se decidirá durante implementación si la
pregunta del usuario fallida queda como evento de auditoría conversacional;
la opción recomendada es conservarla con estado `failed` para explicar por qué
un siguiente turno puede carecer de respuesta.

### 5. Contexto de Preview

La sección `.preview-dashboard` recibirá un ID estable, por ejemplo
`preview-dashboard`, y el script que crea el widget incluirá
`data-context-selector="#preview-dashboard"`. El widget ya filtra elementos
ocultos, marcados `data-bidachat-ignore`, formularios y controles; la página no
debe seleccionar `body`, que abarcaría la navegación y el chat.

### 6. Catálogo Vertex explícito

Se añadirá `VERTEX_MODELS` como lista separada por comas de identificadores
válidos. Si falta, el sistema derivará la lista de `VERTEX_MODEL`, preservando
la configuración actual. El gateway definirá correspondencias explícitas para
cada modelo permitido; bootstrap añadirá, nunca modificará ni eliminará,
filas de `llm_models`. El editor reutilizará su filtro existente por proveedor.

Antes de habilitar un nuevo modelo, la verificación local deberá comprobar:
proyecto, región, generación de texto y, si se anuncia como multimodal, PNG,
JPEG y WebP. Un alias flotante sigue siendo la identidad que el proveedor expone;
no se afirmará revisión física inmutable si Google no la devuelve.

## Risks / Trade-offs

- [Retención de datos de visitantes] → TTL corto, límites de caracteres,
  exclusión de imágenes, limpieza controlada y sin endpoint público de historial.
- [Token de conversación adivinable o reutilizado] → UUID criptográfico, alcance
  chatbot+origen, validación backend y sin lectura pública.
- [Tokens/coste y latencia] → ventana de memoria acotada, medición de tamaños y
  comparación de la primera respuesta frente a respuestas posteriores.
- [Prompt injection desde historia] → historia delimitada como contenido no
  confiable y guardrails existentes conservados; no se promete inmunidad total.
- [Modelo Vertex no disponible en región] → lista explícita y prueba mínima por
  modelo antes de exponerlo en el editor.
- [Cambios de esquema] → migración revisable, pruebas con PostgreSQL + pgvector,
  despliegue y rollback antes de activar la nueva versión del widget.

## Migration Plan

1. Revisar y aprobar esta propuesta y actualizar el SRS/documentación de base
   para reflejar memoria conversacional y variables de retención.
2. Crear migración con entidades, índices y FK; probar alta, aislamiento,
   expiración y borrado de chatbot en PostgreSQL + pgvector.
3. Implementar backend y widget de manera compatible: el backend acepta la
   ausencia temporal de `conversation_id`; el widget empieza a enviarlo.
4. Actualizar Preview con su selector, verificar contenido enviado y ejecutar
   una conversación de varios turnos con dato conocido.
5. Activar el catálogo Vertex por lista; comprobar cada nuevo modelo y conservar
   el actual como valor por defecto.
6. Medir token/latencia de muestras con y sin historia, ejecutar regresiones y
   desplegar mediante PR aprobado. Rollback: retirar la nueva versión del widget,
   desactivar memoria por variable y mantener `queries`/modelos históricos.

## Open Questions

- La política institucional de retención puede exigir menos de 24 horas; si se
  define antes de implementar, sustituirá el valor inicial recomendado.
- Confirmar qué modelos Vertex estarán habilitados en el proyecto y región antes
  de colocarlos en `VERTEX_MODELS`; no se asumirán por nombre comercial.
