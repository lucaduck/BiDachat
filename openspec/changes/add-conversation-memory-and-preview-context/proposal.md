## Why

Cada consulta pública se procesa hoy como una interacción independiente. Aunque
`queries` conserva pregunta, respuesta, modelo y tiempo para métricas, el
servicio conversacional no recupera turnos anteriores ni recibe un identificador
de conversación. Por ello el modelo olvida datos ya proporcionados, como el
nombre del visitante, y puede repetir preguntas de contexto.

La vista `/preview` monta el widget sin `data-context-selector`. El widget sí
recoge contenido visible en integraciones externas cuando recibe ese atributo,
pero la prueba interna no envía el tablero de demostración como `page_context`.
Esto impide validar localmente el comportamiento que se espera al publicar el
script en un dashboard.

## What Changes

- Añadir conversaciones anónimas y acotadas, identificadas por un token opaco
  generado por el widget y persistidas en PostgreSQL junto con sus turnos.
- Construir el contexto de cada respuesta con los últimos turnos válidos de la
  conversación, además de RAG, contexto de página e imagen de la consulta
  actual.
- Definir controles de retención, longitud, expiración, aislamiento, limpieza y
  exclusión de imágenes de la memoria conversacional.
- Hacer que la vista previa use un selector explícito del tablero de demostración
  para enviar su contenido visible mediante el mismo contrato REST del widget
  externo.
- Ampliar el catálogo de Vertex AI desde un único `VERTEX_MODEL` a una lista
  explícita de modelos permitidos, conservando el modelo actual como
  predeterminado y sin alterar referencias históricas.
- Registrar evidencia de la prueba local ya realizada: la aplicación completa,
  LiteLLM y Vertex respondieron con `gemini-3.1-flash-lite`; la consulta temporal
  devolvió una respuesta válida y el chatbot de prueba fue eliminado.
- Incorporar reinicio explícito y por inactividad, identidad anónima firmada
  opcional por el servidor anfitrión y limpieza periódica de memoria vencida.

## Capabilities

### New Capabilities

- `conversation-memory`: continuidad conversacional controlada para visitantes
  anónimos del widget, con persistencia y límites explícitos.
- `preview-page-context`: contexto del tablero de demostración enviado en la
  vista previa mediante el mecanismo existente del widget.
- `vertex-model-catalog`: catálogo explícito y validado de varios modelos Vertex
  seleccionables por chatbot.

### Modified Capabilities

- Ninguna. No existen especificaciones principales de OpenSpec que modificar.

## Impact

- Backend: esquema PostgreSQL/migraciones, modelos, esquema de consulta,
  `ConversationService`, servicio de persistencia, límites de entrada y pruebas
  de integración con PostgreSQL + pgvector.
- Widget: generación y conservación de un identificador de conversación por
  navegador, envío del identificador con la API REST y limpieza al caducar o
  cambiar de chatbot.
- Frontend: `/preview` recibirá `data-context-selector` para el tablero
  demostrativo; el editor reutilizará los selectores proveedor/modelo actuales.
- Infraestructura: nuevas variables de límites de memoria y catálogo Vertex;
  no se añade base de datos, caché, WebSocket ni servicio externo adicional.
- Seguridad y privacidad: los visitantes no se autentican, por lo que el token
  no identifica a una persona, se limita a un chatbot y origen, expira y nunca
  permite leer conversaciones mediante una ruta pública.
