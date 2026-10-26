# Diseño de base de datos de BIDACHAT

**Versión:** 0.3 — esquema evolutivo de la aplicación completa

**Fecha:** 2026-10-15

**Alcance:** aplicación completa

**Estado:** esquema versionado mediante migraciones PostgreSQL + pgvector. Este documento conserva la justificación inicial y añade las ampliaciones aplicadas.

## 1. Resumen vigente

Se utiliza una única base **PostgreSQL + pgvector**, accesible exclusivamente desde FastAPI. El esquema inicial contenía siete tablas. Las migraciones posteriores incorporaron `login_attempts`, asociación compartida mediante `chatbot_documents`, memoria acotada mediante `conversations` y `conversation_messages` y satisfacción mediante `conversation_feedback`; el dominio vigente contiene doce tablas. El despliegue crea además `schema_migrations`, una tabla técnica sin datos de negocio que registra las migraciones reconocidas o aplicadas.

La relación central es **chatbot → documentos → fragmentos vectoriales**. Cada consulta pertenece a un chatbot y solo puede recuperar sus fragmentos. El registro de consultas contiene los datos necesarios para calcular las métricas sin mantener contadores duplicados.

Este diseño se deriva del [SRS.md](../SRS.md). [AGENTS.md](../AGENTS.md) establece PostgreSQL, pgvector, separación por chatbot y una implementación directa para la aplicación completa. Las migraciones son la fuente ejecutable cuando una decisión histórica de este documento difiere del esquema aplicado.

### Decisiones aplicadas

| Decisión                                                      | Justificación                                                       | Consecuencia vigente                                                                              |
| ------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| Un documento conserva un chatbot de origen y asociaciones N:M | Permite reutilizar una fuente procesada sin duplicar chunks         | `documents.chatbot_id` conserva el origen; `chatbot_documents` define qué bots pueden recuperarla |
| Modelos admitidos en `llm_models`                             | Centraliza las combinaciones seleccionables de proveedor y modelo   | Las combinaciones usadas históricamente se conservan y no se editan                               |
| Modelo e instrucciones seleccionados en `chatbots`            | El chatbot mantiene una sola configuración actual                   | Cambiar el modelo no conserva versiones completas de configuración                                |
| Sesiones revocables en PostgreSQL                             | Permiten invalidar inmediatamente la sesión al cerrar sesión, RF-03 | Se consulta la sesión en cada operación administrativa                                            |
| Métricas derivadas de `queries`                               | RF-24–RF-27 requieren consultas y duración                          | No existe una tabla `metrics` ni contadores que sincronizar                                       |
| Administradores autorizados comparten gestión                 | El SRS no define propietarios exclusivos ni roles distintos         | `created_by` identifica autoría, no restringe acceso por propietario                              |
| Eliminación física del chatbot y sus datos dependientes       | Ciclo de vida sencillo para RF-07                                   | Se pierden sus consultas y métricas; no hay histórico tras el borrado                             |
| Capturas temporales, sin archivo permanente                   | RF-12/RF-19 piden procesar imágenes, no conservarlas                | No se puede reconstruir posteriormente la imagen de una consulta                                  |
| Embeddings con un perfil global fijo                          | Evita comparar vectores incompatibles                               | Cambiar modelo o dimensión requiere regenerar todo el índice                                      |

Estas decisiones describen el esquema aplicado. La política institucional de retención conversacional permanece pendiente; los límites actuales son controles técnicos configurables y no una política institucional aprobada.

## 2. Diagrama de entidades y relaciones

`||` significa exactamente uno; `o{`, cero o muchos. PK es clave primaria, FK es clave foránea y UK es clave única.

```mermaid
erDiagram
    users ||--o{ auth_sessions : opens
    users ||--o{ chatbots : creates
    llm_models ||--o{ chatbots : configures
    llm_models ||--o{ queries : records
    chatbots ||--o{ documents : originates
    chatbots ||--o{ chatbot_documents : associates
    documents ||--o{ chatbot_documents : is_shared_through
    documents ||--o{ document_chunks : produces
    chatbots ||--o{ queries : receives
    chatbots ||--o{ conversations : scopes
    conversations ||--o{ conversation_messages : contains
    conversations o|--o{ queries : groups
    queries o|--o{ conversation_messages : produces

    users {
        uuid id PK
        text email UK
        text password_hash
        boolean is_active
        timestamptz created_at
        timestamptz updated_at
    }
    auth_sessions {
        uuid id PK
        uuid user_id FK
        text token_hash UK
        timestamptz created_at
        timestamptz expires_at
        timestamptz revoked_at
    }
    llm_models {
        uuid id PK
        text provider
        text model
    }
    chatbots {
        uuid id PK
        uuid created_by FK
        text name
        text description
        uuid configured_llm_model_id FK
        text behavior_instructions
        json widget_settings
        timestamptz created_at
        timestamptz updated_at
    }
    documents {
        uuid id PK
        uuid chatbot_id FK
        text original_filename
        text storage_key UK
        text media_type
        bigint size_bytes
        text status
        text error_code
        text embedding_model
        integer embedding_dimensions
        timestamptz created_at
        timestamptz updated_at
        timestamptz processed_at
    }
    chatbot_documents {
        uuid chatbot_id PK, FK
        uuid document_id PK, FK
    }
    document_chunks {
        uuid id PK
        uuid document_id FK
        integer chunk_index
        text content
        integer page_number
        vector embedding
    }
    queries {
        uuid id PK
        uuid chatbot_id FK
        text question
        text answer
        boolean has_image
        uuid executed_llm_model_id FK
        text status
        text error_code
        timestamptz received_at
        timestamptz completed_at
        bigint response_time_ms
        uuid conversation_id FK
    }
    conversations {
        uuid id PK
        uuid chatbot_id FK
        text origin
        text identity_hash
        timestamptz created_at
        timestamptz last_active_at
        timestamptz expires_at
    }
    conversation_messages {
        uuid id PK
        uuid conversation_id FK
        uuid query_id FK
        text role
        text content
        timestamptz created_at
    }
    login_attempts {
        text key PK
        integer failed_attempts
        timestamptz window_started_at
    }
```

`login_attempts` no tiene una FK: su clave opaca representa el alcance técnico del
límite de acceso y no crea una identidad de usuario adicional. `schema_migrations`
tampoco aparece porque es control técnico del despliegue, no una entidad del
dominio.

El tipo `vector` del diagrama representa **`vector(D)`**, con D recibida desde `EMBEDDING_DIMENSIONS` durante la inicialización. La base local se creó con `vector(768)`. El perfil global seleccionado el 2026-09-21 es `gemini-embedding-2` con salida de 768 dimensiones; cambiar la dimensión exige una migración y cambiar el modelo exige reindexar todo el corpus.

## 3. Justificación de las relaciones

| Relación                                | Cardinalidad | Justificación                                                                                | Integridad aplicada                                                  |
| --------------------------------------- | ------------ | -------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| `users → auth_sessions`                 | 1:N          | Un investigador puede abrir sesiones en distintos dispositivos; cada sesión tiene un usuario | FK obligatoria; borrar el usuario elimina sus sesiones               |
| `users → chatbots`                      | 1:N          | Permite identificar quién registró el chatbot                                                | FK `created_by` obligatoria; un usuario con chatbots no se elimina   |
| `llm_models → chatbots`                 | 1:N          | Una combinación admitida puede ser seleccionada por varios chatbots                          | FK obligatoria; un modelo configurado no se elimina                  |
| `llm_models → queries`                  | 1:N          | Conserva el proveedor y modelo realmente usados en cada consulta                             | FK obligatoria; un modelo con historial no se elimina                |
| `chatbots → documents`                  | 1:N          | Registra el chatbot en el que se cargó originalmente la fuente                               | FK obligatoria con borrado en cascada                                |
| `chatbots ↔ documents`                 | N:M          | Determina qué fuentes puede recuperar cada chatbot                                           | PK compuesta en `chatbot_documents`; ambas FK eliminan la asociación |
| `documents → document_chunks`           | 1:N          | Un documento se divide en fragmentos para recuperación semántica                             | FK obligatoria; borrar el documento elimina sus fragmentos           |
| `chatbots → queries`                    | 1:N          | Cada consulta y duración deben atribuirse a un solo chatbot                                  | FK obligatoria; borrar el chatbot elimina sus consultas              |
| `chatbots → conversations`              | 1:N          | La memoria siempre queda limitada a un chatbot                                               | FK obligatoria con borrado en cascada                                |
| `conversations → conversation_messages` | 1:N          | Conserva únicamente pares textuales completados                                              | FK obligatoria con borrado en cascada                                |
| `conversations → queries`               | 1:N opcional | Agrupa consultas anónimas sin convertir al visitante en usuario                              | FK nullable con `ON DELETE SET NULL`                                 |

No hay FK de `queries` a `users`: el usuario final del widget no necesita cuenta administrativa. No se crea una entidad de dashboard porque el SRS requiere integración, no administrar dashboards. El fragmento no duplica `chatbot_id`: los chatbots autorizados para recuperarlo se obtienen mediante `chatbot_documents`, evitando una segunda referencia contradictoria dentro del chunk.

Un documento en carga o procesamiento puede tener cero fragmentos. Para estar `ready` debe tener al menos uno y todos deben tener embedding válido. Esta condición entre tablas se verifica en la transacción del servicio de documentos; una FK por sí sola no la garantiza.

## 4. Diccionario de datos

Reglas comunes: PK `uuid` generada por el backend; tiempos `timestamptz`, gestionados en UTC; los campos son **NOT NULL salvo donde se indica nullable**. UUID evita depender de secuencias públicas, pero no sustituye autorización. `updated_at` lo actualiza explícitamente el servicio al escribir; un valor por defecto no actualiza el campo automáticamente.

### 4.1 `users` — investigadores autorizados

| Campo           | Tipo        | Regla / propósito                                                                   |
| --------------- | ----------- | ----------------------------------------------------------------------------------- |
| `id`            | uuid        | PK                                                                                  |
| `email`         | text        | No vacío; guardar normalizado con `lower(trim(email))`; UNIQUE sobre `lower(email)` |
| `password_hash` | text        | Hash de contraseña con algoritmo adecuado; nunca contraseña reversible              |
| `is_active`     | boolean     | DEFAULT true; desactivar impide usar incluso sesiones vigentes                      |
| `created_at`    | timestamptz | DEFAULT now()                                                                       |
| `updated_at`    | timestamptz | DEFAULT now(); actualización explícita                                              |

El aprovisionamiento inicial se realiza desde backend, sin registro público ni jerarquía de roles. Las contraseñas usan `scrypt` con sal aleatoria; no se almacenan claves de proveedores en esta tabla.

### 4.2 `auth_sessions` — acceso y cierre de sesión

| Campo        | Tipo        | Regla / propósito                                                               |
| ------------ | ----------- | ------------------------------------------------------------------------------- |
| `id`         | uuid        | PK                                                                              |
| `user_id`    | uuid        | FK → users.id, ON DELETE CASCADE                                                |
| `token_hash` | text        | UNIQUE; digest de token aleatorio de alta entropía, nunca el token reutilizable |
| `created_at` | timestamptz | DEFAULT now()                                                                   |
| `expires_at` | timestamptz | Mayor que `created_at`; vigencia configurable                                   |
| `revoked_at` | timestamptz | Nullable; si existe, >= `created_at`                                            |

El login entrega un token Bearer aleatorio y el frontend actual lo conserva en `localStorage`; la base almacena únicamente su SHA-256. Cada petición administrativa verifica token, expiración, revocación y usuario activo. Cerrar sesión revoca la fila y elimina la copia del navegador. La vigencia inicial es configurable mediante `SESSION_TTL_MINUTES` y no constituye una política institucional de retención. El riesgo de exposición ante XSS y una futura migración a cookie `HttpOnly` están registrados en la [revisión de seguridad](qa/security-review-2026-10-16.md).

### 4.3 `llm_models` — catálogo de modelos admitidos

| Campo      | Tipo | Regla / propósito                                                                              |
| ---------- | ---- | ---------------------------------------------------------------------------------------------- |
| `id`       | uuid | PK                                                                                             |
| `provider` | text | No vacío; normalizado en minúsculas y sin espacios exteriores; por ejemplo `gemini` u `ollama` |
| `model`    | text | No vacío y sin espacios exteriores; identificador reconocido por el proveedor                  |

La combinación (`provider`, `model`) es UNIQUE. El backend determinará qué proveedores están admitidos; guardar texto no autoriza destinos arbitrarios. Un trigger de PostgreSQL impide modificar la identidad de una combinación: para cambiarla se crea otra fila. Las FK con ON DELETE RESTRICT impiden borrar una combinación referenciada. Así, el historial no cambia indirectamente cuando se modifica el catálogo o la configuración de un chatbot.

Las credenciales del proveedor externo y la dirección del servicio Ollama permanecen en configuración del backend. No se almacenan claves, URLs ni parámetros de conexión en esta tabla.

### 4.4 `chatbots` — identidad y configuración actual

| Campo                     | Tipo        | Regla / propósito                                                    |
| ------------------------- | ----------- | -------------------------------------------------------------------- |
| `id`                      | uuid        | PK; identificador público estable del widget                         |
| `created_by`              | uuid        | FK → users.id, ON DELETE RESTRICT                                    |
| `name`                    | text        | `CHECK (length(trim(name)) > 0)`; no se exige unicidad no solicitada |
| `description`             | text        | Nullable; texto descriptivo                                          |
| `configured_llm_model_id` | uuid        | FK → llm_models.id, ON DELETE RESTRICT; selección actual             |
| `behavior_instructions`   | text        | DEFAULT ''; rol, tono y reglas como instrucciones unificadas         |
| `widget_settings`         | json        | Apariencia y bienvenida del widget con valores predeterminados       |
| `created_at`              | timestamptz | DEFAULT now()                                                        |
| `updated_at`              | timestamptz | DEFAULT now(); actualización explícita                               |

El modelo generativo seleccionado es independiente del modelo de embeddings. Cambiar `configured_llm_model_id` no modifica el identificador del widget ni obliga por sí mismo a reindexar documentos. Version 1 admite proveedor externo y Ollama local; su ejecución se formaliza y prueba en el cambio `add-local-ollama-provider`.

El snippet del widget se deriva del identificador y de las URLs de despliegue: no necesita tabla ni token secreto. Conocer este identificador permite llamar al endpoint público; las rutas administrativas siempre requieren sesión y los controles de abuso se aplican en backend.

### 4.5 `documents` — fuentes documentales y procesamiento

| Campo                  | Tipo        | Regla / propósito                                                          |
| ---------------------- | ----------- | -------------------------------------------------------------------------- |
| `id`                   | uuid        | PK                                                                         |
| `chatbot_id`           | uuid        | FK → chatbots.id, ON DELETE CASCADE; chatbot de carga original             |
| `original_filename`    | text        | Nombre informativo, nunca usado como ruta de almacenamiento                |
| `storage_key`          | text        | UNIQUE; clave interna generada, relativa al volumen privado                |
| `media_type`           | text        | Tipo validado por contenido y lista permitida                              |
| `size_bytes`           | bigint      | CHECK > 0; límite de carga configurable en backend                         |
| `status`               | text        | CHECK IN ('pending', 'processing', 'ready', 'failed'); DEFAULT 'pending'   |
| `error_code`           | text        | Nullable; código controlado, sin trazas ni secretos                        |
| `embedding_model`      | text        | Nullable antes de procesar; identificador del modelo del perfil global     |
| `embedding_dimensions` | integer     | Nullable antes de procesar; cuando exista debe coincidir con D del esquema |
| `created_at`           | timestamptz | DEFAULT now()                                                              |
| `updated_at`           | timestamptz | DEFAULT now(); seguimiento del procesamiento                               |
| `processed_at`         | timestamptz | Nullable hasta finalizar correctamente                                     |

Los campos de modelo y dimensión deben ser ambos nulos o ambos no nulos. En `pending` son nulos; en `processing` ya están definidos. En `ready`, ambos y `processed_at` son obligatorios; `error_code` es nulo. En `failed`, `error_code` es obligatorio y `processed_at` es nulo; en otros estados el error es nulo. El esquema exige la dimensión D y el servicio deberá validar el modelo del perfil global.

Los originales se conservan en un volumen privado para poder reprocesarlos, sin introducir un servicio de almacenamiento adicional. La BD guarda referencias y metadatos, no binarios ni base64. El endpoint valida PDF, DOCX, TXT y CSV hasta 20 MiB, e imágenes PNG, JPEG y WebP hasta 4 MiB.

### 4.6 `document_chunks` — unidad de recuperación RAG

| Campo         | Tipo      | Regla / propósito                                                        |
| ------------- | --------- | ------------------------------------------------------------------------ |
| `id`          | uuid      | PK                                                                       |
| `document_id` | uuid      | FK → documents.id, ON DELETE CASCADE                                     |
| `chunk_index` | integer   | CHECK >= 0; UNIQUE (`document_id`, `chunk_index`)                        |
| `content`     | text      | Texto no vacío utilizado como contexto                                   |
| `page_number` | integer   | Nullable; CHECK > 0 cuando exista; ubicación en documentos paginados     |
| `embedding`   | vector(D) | NOT NULL; D fija; vector finito y no nulo en norma para distancia coseno |

No se crea otra tabla de embeddings: hay un vector por fragmento. `page_number` identifica el inicio si un fragmento abarca más de una página. El orden se mantiene con `chunk_index`.

### 4.7 `queries` — consulta, resultado y medición

| Campo                   | Tipo        | Regla / propósito                                                                |
| ----------------------- | ----------- | -------------------------------------------------------------------------------- |
| `id`                    | uuid        | PK; identifica un intento aceptado                                               |
| `chatbot_id`            | uuid        | FK → chatbots.id, ON DELETE CASCADE                                              |
| `question`              | text        | No vacío después de trim                                                         |
| `answer`                | text        | Nullable durante procesamiento o ante fallo; obligatoria y no vacía al completar |
| `has_image`             | boolean     | DEFAULT false; indica si se incorporó una imagen admitida                        |
| `executed_llm_model_id` | uuid        | FK → llm_models.id, ON DELETE RESTRICT; modelo usado en este intento             |
| `conversation_id`       | uuid        | Nullable; FK → conversations.id, ON DELETE SET NULL                              |
| `status`                | text        | CHECK IN ('processing', 'completed', 'failed'); DEFAULT 'processing'             |
| `error_code`            | text        | Nullable; obligatorio solo en fallo, con código controlado                       |
| `received_at`           | timestamptz | Momento de recepción de la solicitud en el backend                               |
| `completed_at`          | timestamptz | Nullable hasta terminar; >= `received_at`                                        |
| `response_time_ms`      | bigint      | Nullable durante procesamiento; CHECK >= 0 cuando exista                         |

Invariante aplicada: `processing` no tiene respuesta, error ni tiempos finales; `completed` tiene respuesta, tiempos finales y ningún error; `failed` tiene error y no respuesta. En fallos normales se registran tiempos finales. En interrupciones del proceso se permite `failed` con ambos tiempos finales nulos, porque la duración real no pudo observarse. No se fabrica un tiempo para esos casos.

Cada solicitud válida aceptada crea una fila y copia la referencia `configured_llm_model_id` del chatbot en `executed_llm_model_id` al admitirla. Las solicitudes rechazadas por validación o control de abuso quedan fuera de estas métricas funcionales. Un reenvío del usuario es otro intento. No se implementa deduplicación por texto: dos preguntas iguales pueden ser consultas legítimas.

Se conservan pregunta y respuesta para identificar el registro y alimentar métricas. La memoria reciente se guarda separadamente en `conversation_messages`; no existe una interfaz de historial para visitantes. El plazo institucional de retención debe aprobarse. No se conservan capturas, IP ni huellas de visitantes en `queries`.

### 4.8 `login_attempts` — límite de acceso

| Campo               | Tipo        | Regla / propósito                                    |
| ------------------- | ----------- | ---------------------------------------------------- |
| `key`               | text        | PK opaca del alcance controlado                      |
| `failed_attempts`   | integer     | DEFAULT 0; CHECK >= 0                                |
| `window_started_at` | timestamptz | Inicio de la ventana persistida de intentos fallidos |

### 4.9 `chatbot_documents` — fuentes asociadas

| Campo         | Tipo | Regla / propósito                        |
| ------------- | ---- | ---------------------------------------- |
| `chatbot_id`  | uuid | PK compuesta; FK → chatbots.id, CASCADE  |
| `document_id` | uuid | PK compuesta; FK → documents.id, CASCADE |

La recuperación filtra mediante esta tabla. Retirar una asociación no borra el
archivo ni sus fragmentos mientras el documento de origen permanezca.

### 4.10 `conversations` — memoria anónima acotada

| Campo            | Tipo        | Regla / propósito                                  |
| ---------------- | ----------- | -------------------------------------------------- |
| `id`             | uuid        | PK opaca generada por el cliente                   |
| `chatbot_id`     | uuid        | FK → chatbots.id, ON DELETE CASCADE                |
| `origin`         | text        | Origen HTTP(S) normalizado y no vacío              |
| `identity_hash`  | text        | Nullable; hash de identidad firmada, sin identificador directo |
| `created_at`     | timestamptz | DEFAULT now()                                      |
| `last_active_at` | timestamptz | Actividad más reciente; no anterior a `created_at` |
| `expires_at`     | timestamptz | Vencimiento deslizante posterior a `created_at`    |

### 4.11 `conversation_messages` — turnos recordados

| Campo             | Tipo        | Regla / propósito                              |
| ----------------- | ----------- | ---------------------------------------------- |
| `id`              | uuid        | PK                                             |
| `conversation_id` | uuid        | FK → conversations.id, ON DELETE CASCADE       |
| `query_id`        | uuid        | Nullable; FK → queries.id, ON DELETE SET NULL  |
| `role`            | text        | `user` o `assistant`                           |
| `content`         | text        | Texto no vacío; no contiene imágenes ni base64 |
| `created_at`      | timestamptz | DEFAULT now()                                  |

## 5. Normalización y decisiones de simplicidad

Cada tabla representa una entidad con su propia clave. Los datos de usuario no se copian en chatbots, ni los datos documentales en cada consulta. Las relaciones se expresan con FK obligatorias.

Las dos referencias a `llm_models` son deliberadas: `queries.executed_llm_model_id` describe un hecho histórico, mientras `chatbots.configured_llm_model_id` describe la configuración actual. `documents.embedding_model` y su dimensión documentan cómo se procesó cada fuente y permiten detectar índices obsoletos. Ningún dato histórico se actualiza al cambiar el modelo del chatbot.

Alternativas consideradas:

| Alternativa                             | Motivo para no incluirla inicialmente                             | Qué cambio la justificaría                                               |
| --------------------------------------- | ----------------------------------------------------------------- | ------------------------------------------------------------------------ |
| `chatbot_configurations` 1:1            | Mismos permisos y ciclo de vida que chatbot                       | Versionado o varias configuraciones aprobadas                            |
| `metrics` separada                      | Duplica hechos que ya existen en consultas                        | Métricas independientes o agregación materializada medida como necesaria |
| Perfil persistente del visitante        | La memoria aprobada es anónima, acotada y temporal                | Identidad del visitante y política institucional aprobadas               |
| `dashboards`, integraciones por dominio | El widget puede usar un chatbot por identificador estable         | Gestión de dashboards o políticas por integración aprobadas              |
| `query_sources`                         | La reconstrucción histórica exacta del contexto no está requerida | Auditoría/citas persistentes con requisitos de retención                 |
| Catálogo de roles                       | La aplicación no requiere roles diferenciados                     | Administración de roles aprobada                                         |

## 6. Aislamiento y consulta vectorial

El backend resuelve el chatbot desde la ruta y limita todos los accesos a ese contexto. Para leer/modificar un documento se busca por **id del documento y id del chatbot**, nunca solo por el id recibido. Las FK impiden huérfanos, pero no autorizan al llamante.

Ejemplo conceptual de recuperación parametrizada (solo documentación):

```sql
SELECT c.id, c.content, c.page_number,
       c.embedding <=> CAST(:query_embedding AS vector) AS distance
FROM document_chunks AS c
JOIN documents AS d ON d.id = c.document_id
WHERE d.chatbot_id = :chatbot_id
  AND d.status = 'ready'
  AND d.embedding_model = :embedding_model
  AND d.embedding_dimensions = :embedding_dimensions
ORDER BY distance, c.id
LIMIT :top_k;
```

Los parámetros de embedding y `top_k` proceden del servicio RAG, con validación. Nunca se hace una búsqueda global para después filtrar en Python. El contexto y la configuración se obtienen para el mismo chatbot; el cliente no puede sustituirlos mediante campos del cuerpo.

La búsqueda exacta inicial evita introducir un índice aproximado sin volumen ni mediciones. pgvector permite búsqueda exacta y aproximada; sus operadores y restricciones se verificarán contra la versión fijada al implementar. [Referencia oficial de pgvector](https://github.com/pgvector/pgvector).

El perfil seleccionado es `gemini-embedding-2` con `output_dimensionality=768`. La documentación oficial indica que admite entrada multimodal, permite dimensiones entre 128 y 3072, recomienda 768 entre sus tamaños habituales y normaliza automáticamente las salidas truncadas. Esto conserva `vector(768)` y el alcance multimodal de la aplicación. Documentos y consultas deben usar exactamente ese modelo y dimensión; no se mezclarán modelos del mismo tamaño como si fueran equivalentes. El modelo generativo configurado por chatbot sigue siendo independiente. [Documentación oficial de embeddings de Gemini](https://ai.google.dev/gemini-api/docs/embeddings).

No se propone RLS inicialmente: el aislamiento se implementa en los servicios y consultas SQL, con pruebas negativas obligatorias. Una omisión del filtro sería una vulnerabilidad; la estructura relacional por sí sola no la evita.

## 7. Índices e integridad

| Tabla             | Índice / restricción                                                    | Acceso que resuelve                                  |
| ----------------- | ----------------------------------------------------------------------- | ---------------------------------------------------- |
| Todas             | PK en `id`                                                              | Identidad y referencias                              |
| `users`           | UNIQUE en `lower(email)`                                                | Login sin duplicados por mayúsculas                  |
| `auth_sessions`   | UNIQUE (`token_hash`), índice (`user_id`), índice (`expires_at`)        | Validación, revocación y limpieza                    |
| `llm_models`      | UNIQUE (`provider`, `model`) y comprobaciones de texto no vacío         | Evitar combinaciones duplicadas                      |
| `chatbots`        | Índices (`created_by`) y (`configured_llm_model_id`)                    | Comprobación de referencias a usuario y modelo       |
| `documents`       | UNIQUE (`storage_key`), índice (`chatbot_id`, `status`)                 | Archivos sin colisión y selección de fuentes listas  |
| `document_chunks` | UNIQUE (`document_id`, `chunk_index`)                                   | Orden y acceso por documento sin duplicar fragmentos |
| `queries`         | Índice (`chatbot_id`, `received_at`) e índice (`executed_llm_model_id`) | Métricas por chatbot y protección de referencias     |

No se duplican índices ya cubiertos por PK/UNIQUE ni se supone que una FK crea automáticamente índice en la tabla hija. PostgreSQL permite especificar FK, unicidad y acciones de borrado; las restricciones entre filas/tablas que no cubran estas herramientas se resuelven con transacciones y pruebas. [Restricciones de PostgreSQL](https://www.postgresql.org/docs/current/ddl-constraints.html).

## 8. Transacciones y ciclo de vida

### Carga y procesamiento

1. Validar sesión, chatbot, archivo y límites antes de incorporarlo al RAG.
2. Escribir el original con clave generada en volumen privado; crear fila `pending`. Si falla el alta, retirar el archivo temporal.
3. Reclamar el documento con cambio condicional `pending → processing`; un solo procesamiento puede ganarlo. Registrar el perfil de embeddings.
4. Extraer texto, dividir y generar vectores fuera de una transacción larga de BD.
5. En una transacción corta, verificar que el documento aún existe y pertenece al chatbot esperado, insertar el conjunto completo de fragmentos y pasar a `ready`.
6. Ante error, marcar `failed`; los fragmentos incompletos nunca están disponibles para recuperar.

Para reintentar, cambiar `failed → pending` y sustituir el conjunto en una transacción. La restricción UNIQUE impide duplicados. La recuperación de trabajos interrumpidos debe distinguir procesos activos de detenidos; con el proceso único actual se pueden marcar fallidos al reiniciarlo. Antes de usar varios procesos se debe definir reclamación/recuperación segura, sin asumir que todos los trabajos `processing` son huérfanos.

### Consulta y medición

Se toma un reloj monotónico al recibir la petición. Tras validación y admisión se copia `configured_llm_model_id` en `executed_llm_model_id` y se registra `processing` con el `received_at` original. Al finalizar se guardan resultado, estado y duración. No se mantiene una transacción abierta mientras se espera al proveedor configurado.

`response_time_ms` mide desde recepción hasta respuesta lista para entregar desde backend, incluyendo RAG y LLM. No mide el transporte hasta el navegador ni el renderizado: si RNF-06 se interpreta como entrega efectiva al usuario, habrá que añadir medición cliente/confirmación y revisar esta decisión. Las interrupciones no observadas dejan duración nula y se reportan por separado.

### Eliminación y archivos

La eliminación bloquea la fila de chatbot; admisión de consultas/cargas usa un bloqueo compatible que impide aceptar trabajo durante el borrado. Las FK y cascadas eliminan metadatos, fragmentos y consultas atómicamente. Los trabajos que terminen tarde deben detectar que ya no existe el destino y no recrearlo.

La transacción SQL **no elimina archivos del volumen**. El servicio obtiene sus claves antes del borrado, confirma la transacción y después elimina los binarios. Si esta limpieza falla, quedan archivos inaccesibles: una conciliación controlada entre claves de BD y archivos permite retirarlos. No borrar archivos antes del commit, porque un rollback dejaría documentos sin original. Las copias de seguridad deben incluir BD y volumen de forma consistente.

## 9. Métricas sin duplicación

El servicio de métricas agrupa `queries` por chatbot y periodo: consultas aceptadas, completadas, fallidas y en procesamiento. Las duraciones se presentan con su cantidad de muestras y los casos sin medición se distinguen. Para un chatbot sin consultas, el conteo es 0 y la media no está disponible, no 0 ms.

```sql
SELECT COUNT(*) AS total_queries,
       COUNT(*) FILTER (WHERE status = 'completed') AS completed_queries,
       COUNT(*) FILTER (WHERE status = 'failed') AS failed_queries,
       COUNT(*) FILTER (WHERE status = 'processing') AS processing_queries,
       COUNT(response_time_ms) FILTER (
           WHERE status = 'completed'
       ) AS measured_completed_queries,
       AVG(response_time_ms) FILTER (
           WHERE status = 'completed'
       ) AS average_response_time_ms
FROM queries
WHERE chatbot_id = :chatbot_id
  AND received_at >= :start_at
  AND received_at < :end_at;
```

El intervalo es semiabierto para evitar doble conteo entre periodos consecutivos. La media ilustrada corresponde a éxitos; las duraciones de fallos se consultan separadamente. No se establece un objetivo de latencia ni métricas de visitantes únicos que el SRS no exige.

## 10. Trazabilidad y pruebas de aceptación

Las pruebas de autenticación, CRUD/configuración, carga documental, publicación/recuperación RAG, proveedores, widget, memoria y métricas se ejecutan contra servicios aislados. Los resultados fechados y sus límites se conservan en el [índice de QA](qa/README.md); este diseño no sustituye esa evidencia.

| Requisitos                       | Criterios                                       | Elementos                       | Verificación                                                               |
| -------------------------------- | ----------------------------------------------- | ------------------------------- | -------------------------------------------------------------------------- |
| RF-01–RF-03, RS-01/RS-02         | CA-UC01-01 a CA-UC01-04                         | users, auth_sessions            | Login válido/inválido; revocación inmediata; expiración y cuenta inactiva  |
| RF-04–RF-07                      | CA-UC02-01 a CA-UC02-04                         | chatbots                        | CRUD; referencia de autor; eliminación sin dependientes huérfanos          |
| RF-08/RF-09/RF-11, RNF-05/RNF-10 | CA-UC03-01 a CA-UC03-04                         | llm_models, chatbots, documents | Configuración persistida, modelo admitido y asociación correcta            |
| RF-13–RF-15, RS-05/RS-06         | CA-UC04-01 a CA-UC04-03                         | documents, document_chunks      | Carga válida; rechazo de tipo/tamaño; atomicidad y reintentos              |
| RF-16/RF-17, RS-07               | CA-UC04-04/CA-UC04-05                           | JOIN filtrado                   | Vector de A nunca devuelve contenido de B; acceso cruzado por id rechazado |
| RF-10/RF-23, RNF-01/RNF-02       | CA-UC05-01 a CA-UC05-04                         | chatbot id estable              | Widget llama API; cambiar modelo no cambia snippet                         |
| RF-18/RF-20–RF-22                | CA-UC06-01 a CA-UC06-04                         | queries y servicios             | Texto + contexto correcto; respuesta e indicador de procesamiento          |
| RF-12/RF-19/RF-20                | CA-UC07-01 a CA-UC07-04                         | has_image y flujo temporal      | Imagen llega al contexto; no se persiste como fuente de otro chatbot       |
| RF-24–RF-27, RNF-06/RNF-07       | CA-UC06-05, CA-UC07-05, CA-UC08-01 a CA-UC08-04 | queries y agregación            | Medición, asociación, fallos, cero consultas, acceso autorizado            |
| RS-03/RS-04/RS-08/RS-09          | Revisión de seguridad de la aplicación          | Infraestructura y backend       | TLS, secretos externos, control de abuso y errores sanitizados             |

Además: rechazar FK inexistentes, fragmentos repetidos, vectores de otra dimensión/perfil, duraciones negativas y estados incompatibles; probar borrado concurrente con procesamiento/consulta y limpieza del volumen. Las pruebas de FK, cascadas y vectores deben ejecutarse contra PostgreSQL con pgvector, no sustituirse por SQLite.

## 11. Historial de decisiones iniciales

- [x] Confirmar el SRS 0.1 como referencia de la primera implementación: aprobado por el usuario el 2026-09-22. El SRS 0.2 de la versión completa es ahora la fuente vigente.
- [x] Inicialización local de las siete tablas y sus relaciones autorizada por el usuario el 2026-09-16.
- [x] Confirmar inicialmente documentos exclusivos por chatbot. La migración 004 incorporó después asociaciones compartidas sin duplicar chunks.
- [x] Confirmar gestión compartida entre investigadores; `created_by` no es permiso de propietario.
- [x] Aprobar borrado en cascada, incluida pérdida de consultas y métricas del chatbot.
- [x] Definir retención de originales, preguntas y respuestas; confirmar capturas temporales.
- [x] Aprobar la definición de tiempo de respuesta y tratamiento de fallos sin medición.
- [x] Seleccionar un perfil de embeddings compatible con la dimensión local 768 o migrarla antes de cargar documentos: `gemini-embedding-2` con salida 768, seleccionado el 2026-09-21.

El usuario aprobó la base inicial el 2026-09-22. Las migraciones posteriores ampliaron esa decisión con documentos asociados a varios chatbots y memoria conversacional anónima. Los investigadores autenticados comparten la gestión; el borrado es físico en cascada; los originales se conservan en volumen privado para reproceso; las capturas de consulta son temporales; y la duración se mide hasta que backend deja lista la respuesta, con duración nula para fallos no observados. La carga administrativa admite documentos de hasta 20 MiB e imágenes de hasta 4 MiB. Aplicar el esquema no equivale por sí solo a autorizar una publicación.

## 12. Decisión integrada: inferencia seleccionable

**Decisión aplicada:** la inferencia puede ejecutarse con proveedores externos admitidos o con un modelo local mediante Ollama. Las opciones habilitadas aparecen en la configuración del chatbot. `llm_models` representa cada combinación admitida y conserva las referencias históricas.

Redacción del requisito para incorporar a la versión correspondiente:

> El sistema deberá permitir seleccionar, para cada chatbot, el proveedor y el modelo de inferencia, admitiendo un proveedor externo de IA o un modelo ejecutado localmente mediante Ollama.

### Representación en los datos

- `llm_models` almacena cada pareja única (`provider`, `model`), por ejemplo proveedor `gemini` u `ollama` y el identificador de su modelo.
- `chatbots.configured_llm_model_id` selecciona una fila del catálogo como configuración actual.
- `queries.executed_llm_model_id` conserva la fila realmente utilizada en cada intento. La edición del chatbot no cambia este registro histórico.
- Mantener credenciales y direcciones de conexión en configuración controlada del backend. El selector del chatbot no necesita guardar claves privadas ni URLs arbitrarias.
- Conservar las demás entidades y relaciones sin cambiar la asociación entre documentos y chatbots.

### Impacto previsto en el RAG

La recuperación de contexto sigue usando PostgreSQL/pgvector y el filtro por chatbot. El backend entrega ese contexto al proveedor y modelo seleccionados. El widget conserva su comunicación con la API.

La elección del modelo generativo es independiente del perfil de embeddings. Cambiar solo la inferencia no requiere regenerar los vectores. Seleccionar Ollama para inferencia no garantiza funcionamiento sin Internet si los embeddings u otros componentes siguen dependiendo de servicios externos.

Cada combinación se valida según sus capacidades, especialmente para consultas con imágenes. La conmutación automática a otro proveedor no forma parte del comportamiento aprobado.

## 13. Funcionamiento en contenedores Docker

### Despliegue local actual

`docker-compose.yml` levanta el servicio `database` usando una imagen pgvector fijada por digest. Se verificaron PostgreSQL **16.15** y pgvector **0.8.6**. El volumen `bidachat_postgres_data` conserva la base al detener o recrear el contenedor; el puerto se publica únicamente en `127.0.0.1:5433`.

```text
Equipo de desarrollo → localhost:5433 → contenedor database:5432
                                            │
                                            └── volumen postgres_data

Backend FastAPI en Compose → database:5432
Frontend y widget → API FastAPI
```

Las credenciales se leen del `.env` local, que Git ignora. FastAPI usa el nombre de servicio `database` dentro de la red Compose; `localhost` dentro de un contenedor identifica ese mismo contenedor, no PostgreSQL. El usuario configurado por Compose es la identidad de conexión de la aplicación.

### Flujo de datos de una consulta

1. El investigador selecciona una fila de `llm_models`; `chatbots.configured_llm_model_id` queda asociado a esa combinación.
2. Al aceptar una consulta, el backend obtiene esa configuración y la guarda como `queries.executed_llm_model_id`. Ese mismo modelo se utiliza durante toda la ejecución, aunque se edite después el chatbot.
3. El RAG recupera fragmentos mediante `document_chunks → documents → chatbot_documents`, filtrando por el chatbot de la consulta.
4. El backend entrega pregunta y contexto al proveedor/modelo referenciado por la consulta, no a una configuración releída después.
5. Guarda respuesta, estado y duración en `queries`. Las métricas se calculan desde esos registros.

Ejemplo: una consulta ejecutada con Gemini conserva esa referencia. Cambiar `configured_llm_model_id` a una fila Ollama solo afecta a las consultas nuevas. No mantiene una llamada activa ni una dependencia de Gemini para leer la respuesta histórica.

### Inicialización y actualización

El script `docker/postgres/init-database.sh` valida `EMBEDDING_DIMENSIONS` y ejecuta `database/migrations/001_initial_schema.up.sql` con una variable de `psql`. Docker lo ejecuta solo al crear un volumen vacío. Los archivos SQL se montan como solo lectura; editarlos no altera una base existente automáticamente.

Los cambios posteriores se aplicarán como migraciones nuevas. La reversión `001_initial_schema.down.sql` se probó únicamente sobre la base local sin filas y se reaplicó inmediatamente; no es un procedimiento de actualización de una base con datos.

### Comprobaciones ejecutadas

`database/tests/verify_initial_schema.sql` comprobó las siete tablas y la extensión vector; la separación entre configuración actual e historial; unicidad de proveedor/modelo; protección contra edición y borrado del modelo histórico; FK inexistentes; expiración inválida de sesiones; estados finales incompletos; duración negativa; fragmentos duplicados; vectores de dimensión incompatible y vectores de norma cero; y borrado en cascada de dependientes del chatbot.

Las pruebas usan una transacción con ROLLBACK, de modo que no dejan usuarios, modelos, documentos ni consultas de prueba. La base quedó sin filas y disponible para integrar el backend. Los controles de autorización, publicación de documentos listos, llamadas LLM y aislamiento de servicios aún requieren código y pruebas de aplicación.

## 14. Ampliación vigente: memoria conversacional anónima

La migración `005_conversation_memory` añade memoria textual reciente sin convertirla en un perfil de usuario ni almacenar imágenes. El cliente conserva un UUID opaco en `sessionStorage`; el backend es quien decide si ese identificador todavía pertenece al chatbot y origen actuales.

```mermaid
erDiagram
    chatbots ||--o{ conversations : scopes
    conversations ||--o{ conversation_messages : contains
    conversations o|--o{ queries : groups
    queries o|--o{ conversation_messages : produces

    conversations {
        uuid id PK
        uuid chatbot_id FK
        text origin
        text identity_hash
        timestamptz created_at
        timestamptz last_active_at
        timestamptz expires_at
    }
    conversation_messages {
        uuid id PK
        uuid conversation_id FK
        uuid query_id FK
        text role
        text content
        timestamptz created_at
    }
    queries {
        uuid id PK
        uuid conversation_id FK
        uuid chatbot_id FK
        uuid executed_llm_model_id FK
    }
```

| Elemento                   | Regla vigente                                                                                                            |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `conversations.chatbot_id` | Alcance obligatorio; el borrado del chatbot elimina su memoria.                                                          |
| `conversations.origin`     | Origen HTTP(S) normalizado. Un identificador presentado desde otro origen no recupera mensajes.                          |
| `conversations.identity_hash` | Hash opcional vinculado a la identidad firmada, chatbot y origen; `NULL` para sesiones anónimas. |
| `expires_at`               | Vencimiento deslizante. El valor operativo inicial es 24 horas y se configura con `CONVERSATION_TTL_HOURS`.              |
| `conversation_messages`    | Solo roles `user` y `assistant`; se crean juntos después de una respuesta completada. No contienen imágenes ni base64.   |
| `queries.conversation_id`  | Referencia nullable con `ON DELETE SET NULL`; limpiar memoria no elimina consultas, tiempos, estado ni modelo ejecutado. |
| Ventana enviada al LLM     | Hasta 12 turnos y 12000 caracteres por defecto, ajustables con `CONVERSATION_MAX_TURNS` y `CONVERSATION_MAX_CHARS`.      |

Los índices `(chatbot_id, origin, expires_at)` y `expires_at` resuelven validación y limpieza. El índice `(conversation_id, created_at, id)` recupera los mensajes recientes de forma determinista. La eliminación de una conversación borra sus mensajes en cascada y desacopla las consultas históricas.

La migración `006_conversation_identity` agrega `identity_hash`. El backend elimina conversaciones vencidas al arrancar y periódicamente; `python -m app.cleanup_conversations` también puede ejecutarse manualmente de forma segura. La limpieza conserva los registros de consultas y sus textos. La retención de 24 horas, 12 turnos y 12000 caracteres es el valor técnico inicial y permanece sujeta a confirmación de la política institucional.

## 15. Satisfacción de la conversación

La migración `007_conversation_feedback` incorpora una oferta y como máximo una respuesta por conversación (`conversation_id UNIQUE`). Ese UUID no tiene FK a `conversations`: al limpiar la memoria, permanecen la oferta y las puntuaciones. El servicio exige una conversación vigente, del mismo chatbot, origen e identidad, con al menos una consulta completada antes de aceptar oferta o envío. `chatbot_id` tiene FK con `ON DELETE CASCADE`, por lo que borrar el chatbot elimina sus evaluaciones.

```mermaid
erDiagram
    chatbots ||--o{ conversation_feedback : receives
    conversations ||..o| conversation_feedback : identified_by_uuid_only
    conversation_feedback {
        uuid id PK
        uuid chatbot_id FK
        uuid conversation_id UK
        timestamptz offered_at
        timestamptz submitted_at
        smallint satisfaction_score
        text resolution
        smallint clarity_score
        text comment
    }
```

Una fila sin `submitted_at` mantiene nulos todos los campos de respuesta. Una fila enviada requiere `satisfaction_score` entre 1 y 5; `clarity_score` también queda entre 1 y 5, `resolution` solo admite `yes`, `partial` o `no`, y el comentario no excede 1000 caracteres. El índice `(chatbot_id, offered_at)` soporta filtros UTC; el índice parcial por `submitted_at` facilita borrar texto vencido. La limpieza periódica pone `comment = NULL` a los 90 días del envío sin alterar puntuaciones, oferta o agregados. No se almacenan nombre, correo, imagen, origen, identidad, pregunta ni respuesta en esta tabla. La reversión SQL elimina la tabla y pierde sus evaluaciones; debe usarse solo después de respaldar los datos y decidir expresamente esa pérdida.
