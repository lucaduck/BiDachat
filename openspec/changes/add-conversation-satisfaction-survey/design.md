## Context

Véase [proposal.md](proposal.md). El widget ya guarda un `conversation_id` por pestaña y origen, permite «Nueva conversación» y obtiene el identificador definitivo de `POST /api/v1/chatbots/{chatbot_id}/queries`. `ConversationMemoryService` comprueba chatbot, origen, identidad firmada y vencimiento. La limpieza elimina `conversations` y sus mensajes; `queries.conversation_id` pasa a `NULL` y las métricas históricas sobreviven. `MetricsService` agrega `queries` por chatbot y periodo. El esquema vigente está en [docs/database-design.md](../../../docs/database-design.md).

## Goals / Non-Goals

**Goals:** un flujo voluntario corto; un solo resultado contabilizable por conversación; cálculo reproducible con denominadores explícitos; aislamiento equivalente al de las consultas; persistencia de agregados tras limpiar memoria; lectura administrativa accesible.

**Non-Goals:** convertir CSAT en exactitud de la IA, identificar personas, recopilar correo/nombre, atribuir una encuesta a un solo modelo cuando la conversación haya usado varios, crear un servicio nuevo o contactar una plataforma externa de encuestas.

## Decisions

### 1. Momento de la encuesta y continuidad del widget

Añadir «Finalizar conversación» junto a «Nueva conversación». Solo la primera acción ofrece encuesta tras una respuesta completada. «Cerrar asistente» oculta el panel y conserva su estado; «Nueva conversación» reinicia como hoy. El widget conserva el `conversation_id` mientras el formulario está abierto o se reintenta el envío. Tras omitir o enviar correctamente, limpia el borrador y crea un nuevo identificador. Si la red falla, muestra error y conserva las selecciones con acciones de reintentar u omitir. La vista puramente visual del editor mantiene controles deshabilitados; la vista de prueba funcional usa el mismo flujo.

Alternativa considerada: abrir encuesta tras cada respuesta o al cerrar el panel. Ambas opciones interrumpen el diálogo y confunden cierre visual con final de conversación.

### 2. Persistencia, cardinalidad y retención

Crear una tabla `conversation_feedback`: `id` UUID, `chatbot_id` FK con `ON DELETE CASCADE`, `conversation_id` UUID con `UNIQUE` pero **sin FK** a `conversations`, `offered_at` UTC, `submitted_at` UTC opcional, `satisfaction_score` 1–5 opcional hasta el envío, `resolution` valor restringido opcional, `clarity_score` 1–5 opcional y `comment` de máximo 1000 caracteres opcional. Índice `(chatbot_id, offered_at)` para los filtros. Restricción de fila: sin envío, los campos de respuesta son nulos; con envío, satisfacción no es nula. Se guarda una oferta por conversación y como máximo una respuesta en esa misma fila. No se duplica `origin`, identidad, pregunta, respuesta o imagen.

La ausencia de FK a `conversations` permite que `cleanup_expired` conserve ofertas y resultados. El servicio público **siempre** consulta la conversación viva y la última consulta completada antes de crear o actualizar la fila; una oferta huérfana nunca autoriza un envío. `chatbot_id` mantiene aislamiento y borrado en cascada. La transacción bloquea la conversación y la fila de evaluación, comprueba el estado y confirma una sola operación; la unicidad resuelve solicitudes simultáneas. La eliminación de chatbot deja a la base efectuar la cascada sin limpiar archivos, porque la evaluación no almacena ficheros.

Propuesta de retención a registrar en SRS antes de implementarla: borrar únicamente `comment` tras 90 días desde `submitted_at`, mediante la limpieza periódica existente; conservar puntuaciones y ofertas mientras exista el chatbot. La retención institucional definitiva y la política de exportación de comentarios quedan sujetas a revisión documental antes de activar la función.

Alternativa considerada: FK de evaluación a conversación con cascada; perdería los datos al vencer la memoria. Un contador agregado separado perdería la unicidad y complicaría auditoría y corrección de cálculos.

### 3. Contrato REST y acceso

- `POST /api/v1/chatbots/{chatbot_id}/survey-offers`: cuerpo con `conversation_id` y `identity_token` opcional. Devuelve estado de oferta, sin contenido previo.
- `POST /api/v1/chatbots/{chatbot_id}/survey-responses`: mismo alcance más `satisfaction_score`, `resolution`, `clarity_score`, `comment`. Devuelve confirmación sin eco del comentario.
- `GET /api/v1/chatbots/{chatbot_id}/satisfaction-metrics`: requiere sesión administrativa; acepta los mismos límites UTC y agrupación del módulo Métricas.
- Si se incluyen comentarios en el panel, `GET /api/v1/chatbots/{chatbot_id}/survey-responses` será administrativo, paginado, filtrado por periodo y devolverá solo el comentario y fecha, sin identificador de conversación o identidad.

Reutilizar `require_widget_origin`, `verify_widget_identity` y una cuota específica para los dos POST públicos. Ambos deben verificar una `Conversation` vigente que coincida con el chatbot, origen e identidad, y tenga una `Query` completada. Errores de conversación ajena o vencida usan el mismo mensaje público sin indicar cuál condición falló. El backend valida todos los campos y no acepta HTML ejecutable; el frontend muestra comentarios como texto. Reenvío idéntico tras respuesta devuelve confirmación idempotente; intento de cambiarla devuelve conflicto. No se expone endpoint público de lectura.

Alternativa considerada: incorporar feedback al endpoint de consultas; mezclaría envío de preguntas con una acción posterior y permitiría valoraciones accidentales.

### 4. Cálculo y presentación

Usar la **fecha de oferta** como cohorte para tarjetas, series y tablas: ofertas en el periodo seleccionado, respuestas a esas ofertas aunque lleguen después. Participación = respuestas / ofertas. CSAT = respuestas con 4 o 5 / respuestas con satisfacción válida. Claridad y resolución usan solamente respuestas que incluyeron ese campo. La API devuelve contadores base, distribuciones y serie temporal; el panel muestra tamaño de muestra y «Sin datos» cuando el denominador es cero. Una respuesta tardía puede actualizar un periodo anterior, conducta que se explica en la interfaz.

Reutilizar los filtros de chatbot, periodo y agrupación UTC del panel. El filtro existente «Estado» corresponde a consultas y no modifica satisfacción; mostrar esta distinción junto a la sección de encuesta. Agregar una tabla accesible con las cifras de cada periodo y representar los comentarios como texto seguro. No atribuir por modelo: `queries` registra el modelo ejecutado por turno y una conversación puede incluir más de uno. Ese análisis requeriría un diseño adicional.

## Risks / Trade-offs

- [Identificador anónimo copiado] → exigir conversación vigente, origen exacto, identidad firmada si aplica, cuota y no exponer lectura pública; documentar que sin identidad firmada el UUID funciona como secreto de sesión.
- [Participación inflada por ofertas repetidas] → `UNIQUE (conversation_id)` e inserción idempotente; una oferta se cuenta una sola vez.
- [Encuesta visible sin oferta registrada por fallo de red] → confirmar oferta antes de mostrar formulario; informar el fallo y ofrecer reintento o cierre.
- [Comentario con datos personales o contenido malicioso] → avisar que no incluya datos personales, limitar longitud, borrar texto a los 90 días propuestos, presentar como texto y no enviarlo al LLM.
- [Cohortes históricas cambian por respuesta tardía] → mostrar denominadores y explicar que los periodos pueden actualizarse mientras la conversación esté vigente.
- [La cifra de satisfacción se confunde con corrección factual] → etiquetar métricas como percepción del visitante y mantener pruebas de exactitud separadas.

## Migration Plan

1. Registrar en SRS los nuevos RF, criterios de aceptación y plazo de comentario antes de código. Documentar el esquema propuesto en `docs/database-design.md` y revisar la política de retención.
2. Aplicar migración versionada y desplegar API sin alterar filas existentes de `queries` o `conversations`. No se requiere reprocesar documentos ni embeddings.
3. Añadir widget y panel tras comprobar la API y pruebas de integración. El widget anterior sigue conversando porque las rutas existentes conservan su contrato.
4. Validar en vista previa y en una página de otro origen autorizado; comprobar que solo el panel autenticado lee agregados y comentarios.
5. Reversión de aplicación: retirar widget y API de encuesta; conservar la tabla durante la revisión para no perder evaluaciones recibidas. Su eliminación requiere decisión separada de retención y copia de seguridad.

## Open Questions

- La política institucional definitiva de retención y acceso a comentarios puede sustituir los 90 días propuestos antes del despliegue; los campos y el flujo seguirían siendo los mismos.
