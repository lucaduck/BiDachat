## Context

Véase [proposal.md](proposal.md), la [especificación](specs/global-satisfaction-configuration/spec.md) y el esquema actual en [docs/database-design.md](../../../docs/database-design.md). Hoy `conversation_feedback` guarda una oferta y, como máximo, una respuesta por conversación; `chatbot_id` conserva métricas por bot, mientras `conversation_id` no tiene FK a la memoria que expira. El widget tiene un formulario fijo. El usuario decidió una configuración global, preguntas adicionales de opción única o texto libre y satisfacción general 1–5 obligatoria.

## Goals / Non-Goals

**Goals:** editar y publicar un formulario global; conservar el texto y las opciones que vio cada visitante; respuestas relacionales normalizadas; CSAT comparable entre versiones; migración sin pérdida de las evaluaciones existentes.

**Non-Goals:** diferencias por chatbot, selección múltiple, saltos condicionales, preguntas calculadas, borrar puntuaciones históricas, cambiar la escala CSAT o agregar proveedores externos.

## Decisions

### 1. Relaciones y tercera forma normal

```text
survey_settings (id = 1, enabled, active_version_id)
       | 1                                      apunta a versión activa
       +---- 0..N survey_versions (id, version_no, textos, flags)
                         | 1
                         +---- 0..N survey_questions (id, kind, prompt, required, position)
                                            | 1
                                            +---- 0..N survey_options (id, label, position)

chatbots (id) 1 ---- 0..N conversation_feedback (id, chatbot_id,
                             conversation_id UNIQUE, survey_version_id, CSAT, ...)
                                    | 1                       | 1
                                    +---- 0..N survey_choice_answers
                                    +---- 0..N survey_text_answers
```

`survey_settings`: singleton con `id smallint PRIMARY KEY CHECK(id=1)`, `enabled boolean NOT NULL`, `active_version_id uuid NOT NULL REFERENCES survey_versions(id)` y `updated_at`. `survey_versions` tiene UUID PK, `survey_id smallint NOT NULL DEFAULT 1 CHECK(survey_id=1)` como FK a la fila global, `version_no` positivo único, título, introducción, agradecimiento, visibilidad de resolución/claridad/comentario y `published_at`. Hay una FK circular controlada solo durante la migración inicial: se inserta el singleton con `active_version_id` temporalmente nulo, se inserta versión 1 y se actualiza el puntero; al finalizar se exige `NOT NULL`. Las transacciones posteriores solo insertan versión nueva y cambian el puntero. El campo `enabled` no genera versión por sí solo.

`survey_questions`: UUID PK, `survey_version_id` FK, `kind` restringido a `single_choice` o `free_text`, `prompt` no vacío, `required boolean` y `position` positivo con `UNIQUE(survey_version_id, position)`. `survey_options`: UUID PK, `question_id` FK, `label` no vacío y `position` positivo con `UNIQUE(question_id, position)` y clave única compuesta `(id, question_id)` para validación de respuestas. Cada pregunta de opción única debe tener al menos dos opciones distintas al publicar; una de texto libre no tiene opciones. El servicio de publicación verifica esto en una transacción. Orden y contenido de las preguntas se copian a una nueva versión, sin actualizar la anterior.

`conversation_feedback` recibe `survey_version_id NOT NULL REFERENCES survey_versions(id) ON DELETE RESTRICT`. La migración crea una versión 1 equivalente a la encuesta actual, asigna esa versión a todas las ofertas/respuestas existentes y solo entonces marca la columna `NOT NULL`. Mantiene intactos `chatbot_id`, fechas, puntuaciones y comentario. Al crear una oferta nueva se fija la versión publicada; no se cambia cuando el administrador publica otra. La fila sigue sobreviviendo a limpieza de `conversations` y se borra en cascada con el chatbot.

Las respuestas adicionales se guardan en dos tablas tipadas. `survey_choice_answers` tiene PK `(feedback_id, question_id)`, FK a `conversation_feedback`, FK a `survey_questions` y FK compuesta `(option_id, question_id)` a `survey_options`. `survey_text_answers` tiene PK `(feedback_id, question_id)`, mismas FK a evaluación y pregunta, `answer_text` limitado y `redacted_at`; una restricción exige texto presente o marca de redacción, pero no ambos. La limpieza a los 90 días borra `answer_text` y marca `redacted_at`, conservando el hecho de que se respondió. Los dos tipos no almacenan texto de pregunta, opción, chatbot, versión o métricas derivadas.

Una validación de base de datos mediante triggers de integridad comprueba en ambas tablas que `question.survey_version_id = feedback.survey_version_id` y que el tipo de pregunta coincide con el tipo de respuesta. La FK compuesta confirma que la opción pertenece a esa pregunta. Una versión se crea sin `published_at`, recibe preguntas/opciones dentro de la misma transacción y se marca publicada antes de mover el puntero activo. Triggers impiden después `INSERT`/`UPDATE`/`DELETE` de sus preguntas/opciones y cambios de la versión publicada; la reversión explícita de la migración retira primero esos triggers. La aplicación conserva además validación de solicitudes con esquemas tipados. La regla de una respuesta por pregunta y conversación se expresa con las PK compuestas y el envío de todo el formulario es atómico.

Estas tablas están en 3FN: cada atributo no clave depende de la clave de su propia entidad y no de otra columna no clave; los textos de preguntas/opciones existen una sola vez por versión. No se usa EAV ni un JSON de respuestas. La satisfacción general, resolución, claridad y comentario permanecen como campos tipados de `conversation_feedback` porque son indicadores fijos; las preguntas configurables van a tablas aparte. `survey_settings` no se copia a `chatbots`: es una política común, mientras `conversation_feedback.chatbot_id` identifica el bot que produjo cada evaluación.

### 2. Publicación y concurrencia

El administrador edita un borrador en memoria de la interfaz y ve una vista previa sin efectos. `GET /api/v1/settings/survey` devuelve estado global y versión activa completa. `PUT /api/v1/settings/survey` exige sesión administrativa, payload completo validado y `expected_version_id` para evitar sobrescribir una edición ajena. Bloquea `survey_settings`, compara el contenido; si cambia el formulario, inserta versión, preguntas y opciones con nuevos UUID y número secuencial, luego mueve `active_version_id` en la misma transacción. Si solo cambia `enabled`, actualiza la fila global sin nueva versión. Un error conserva la versión anterior. Cada versión publicada es inmutable.

`GET /api/v1/widget/survey-settings` exige un `Origin` autorizado y devuelve solo `enabled`, `version_id` y textos/preguntas/opciones visibles; no expone borradores ni resultados. Si la lectura falla, el widget conserva el chat y oculta la encuesta. Al pulsar «Finalizar conversación», `POST survey-offers` bloquea conversación y política global, valida activación y registra la versión activa en `conversation_feedback`. La respuesta de oferta devuelve **el formulario de esa versión fijada**; el widget lo presenta aunque una versión distinta haya sido publicada entre la carga inicial y el clic. Una oferta existente devuelve la misma versión de forma idempotente. Desactivar después de ofrecer no impide enviar mientras la conversación siga vigente.

`POST survey-responses` acepta CSAT 1–5, campos fijos opcionales y una lista de respuestas identificadas por `question_id`; el servidor deriva la versión de la oferta, valida opciones, tipos, longitudes y preguntas obligatorias, y guarda toda la respuesta o ninguna. Un reenvío idéntico se confirma sin duplicar; uno diferente devuelve conflicto. Se conserva aislamiento por chatbot/origen/identidad y la cuota existente. La publicación de nuevas versiones no altera conversaciones ya ofrecidas.

### 3. Experiencia administrativa, widget y resultados

En Configuración general, la sección «Cuestionario de satisfacción» indica «Se aplica a todos los chatbots» y muestra el estado activo. El editor permite añadir, reordenar, duplicar y quitar preguntas; para opción única, añadir, ordenar y quitar opciones. Cada pregunta marca si es obligatoria. El bloque de satisfacción 1–5 es visible y no eliminable. El borrador muestra validación local, vista previa realista en claro/oscuro y botón «Guardar y publicar» con aviso de impacto global. El widget muestra preguntas en el orden publicado, permite omitir todo el cuestionario y conserva borrador ante fallo de red. Los textos libres se presentan sin ejecutar HTML.

Métricas mantiene CSAT por chatbot y periodo sobre el campo fijo de `conversation_feedback`. Para preguntas nuevas, una vista administrativa filtra por chatbot, periodo UTC y versión: distribución por opción, número de respuestas y textos libres paginados. Nunca mezcla preguntas de IDs/versiones distintas aunque sus títulos coincidan. No expone identificadores de conversación u origen en los resultados. Los textos libres y el comentario fijo se redactan a los 90 días; sus conteos pueden permanecer. Si una pregunta era opcional, el denominador visible incluye solo quienes respondieron a esa pregunta.

### 4. Límites y compatibilidad

El servidor fija límites de contenido: hasta 10 preguntas adicionales, 10 opciones por pregunta de opción única, 200 caracteres por pregunta, 100 por opción y 1000 por respuesta de texto libre. La publicación rechaza opciones duplicadas después de normalizar espacios y mayúsculas. Son límites de tamaño y usabilidad, no objetivos de rendimiento. La versión 1 no tiene preguntas adicionales y conserva todos los campos fijos visibles, por lo que los widgets y métricas actuales siguen funcionando tras migrar. Un script embebido antiguo obtiene la configuración por API sin necesitar reemplazo.

## Risks / Trade-offs

- [Respuestas mezcladas entre versiones] → FK de evaluación a versión, FKs y triggers de integridad, publicación por copia inmutable y agregados separados por versión.
- [Carrera entre GET, oferta y publicación] → la oferta fija y devuelve el formulario de la versión registrada; el widget presenta ese resultado autoritativo.
- [Edición concurrente del cuestionario global] → `expected_version_id` y bloqueo transaccional del singleton; conflicto recuperable en el panel.
- [Fallo parcial de publicación o respuesta] → una transacción para cada operación y restricciones de base; se conserva versión o respuesta anterior completa.
- [Texto libre con datos personales o HTML] → advertencia en formulario, límites, acceso administrativo, salida como texto y redacción a 90 días.
- [Migración de evaluaciones antiguas] → backfill a versión 1 en una sola transacción, comprobación de conteos antes/después y reversión solo sobre copia o respaldo.
- [Complejidad del editor] → tipos limitados a opción única y texto libre; no hay lógica condicional ni selección múltiple.

## Migration Plan

1. Actualizar `SRS.md` con RF y CA para edición, publicación, versionado, respuesta y lectura administrativa; ampliar [docs/database-design.md](../../../docs/database-design.md) con entidades, FKs, cardinalidades, restricciones y retención.
2. Crear migración 008 aditiva para singleton, versiones, preguntas, opciones, FK `conversation_feedback.survey_version_id`, respuestas tipadas y triggers. Insertar versión 1 y backfill de todas las ofertas existentes antes del `NOT NULL`. Registrar 008 en inicialización y corredor versionado.
3. Desplegar backend compatible primero: administración, lectura pública, oferta con versión y recepción validada. Después desplegar Configuración general, widget y resultados. La migración no borra ni reprocesa evaluaciones existentes.
4. Verificar en PostgreSQL + pgvector claves, normalización, versión inmutable, importación histórica, integridad cruzada, concurrencia, redacción, cascada y reversión en base aislada. Probar widget externo y panel en ambos temas.
5. Revertir primero aplicación/UI conservando tablas y datos si hay un defecto. La migración de bajada elimina únicamente objetos nuevos tras respaldo y decisión explícita; debe poder restaurar el contrato anterior sin perder `conversation_feedback` existente.
