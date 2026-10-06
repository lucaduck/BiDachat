## Context

El repositorio comenzó con SRS.md, AGENTS.md y desing.md, sin código ni esquema existente. Véase [proposal.md](proposal.md) para la motivación. El SRS 0.1 está pendiente de aprobación. El usuario pidió explícitamente presentar la base de datos justificada para aprobarla.

El diseño detallado y autoritativo de esta propuesta está en [docs/database-design.md](../../../docs/database-design.md). Este artefacto resume decisiones; no duplica su diccionario de datos.

## Goals / Non-Goals

**Goals:** definir claves, cardinalidades, aislamiento y ciclos de vida suficientes para el MVP; producir una base revisable para migraciones y pruebas reales.

**Non-Goals:** implementar el MVP completo en este cambio, aplicar migraciones sin aprobación, administrar dashboards, mantener biblioteca documental compartida, versionar configuraciones o agregar visitantes identificados.

## Decisions

- Siete tablas: usuarios, sesiones, catálogo de modelos LLM, chatbots, documentos, fragmentos y consultas. Sus restricciones están en el documento principal.
- `llm_models` mantiene combinaciones únicas (`provider`, `model`). Un trigger impide modificar su identidad y las FK restringen el borrado de filas referenciadas. `configured_llm_model_id` representa la selección actual; `executed_llm_model_id` representa el hecho histórico.
- Relación 1:N entre chatbot y documentos; 1:N entre documento y fragmentos. El chatbot del fragmento se deriva por JOIN, sin duplicar una FK potencialmente contradictoria. Biblioteca N:M se reserva para un requisito aprobado de reutilización documental.
- Sesiones revocables guardadas como digest de tokens aleatorios. Permiten cierre inmediato sin agregar Redis. La autoría del chatbot no equivale a propiedad exclusiva.
- Configuración actual junto al chatbot y modelo utilizado junto a cada consulta. Una tabla 1:1 de configuración no aporta independencia necesaria en este MVP.
- Registro de duración y estado en consultas. Métricas por agregación; una tabla de contadores duplicaría información y exigiría sincronización.
- Perfil de embeddings global `gemini-embedding-2` con salida de 768 dimensiones y `vector(768)`. Documentos y consultas deben usar exactamente el mismo identificador y dimensión; coincidencia dimensional por sí sola no implica compatibilidad entre modelos.
- Procesamiento externo fuera de transacciones largas; publicación completa de fragmentos en una transacción corta. Recuperación filtra chatbot, estado y perfil antes de entregar contexto.
- Eliminación física propuesta con cascadas y limpieza posterior del volumen privado. Los originales no se almacenan en recursos públicos ni dentro de columnas base64.

## Risks / Trade-offs

- Omisión de filtro por chatbot → pruebas negativas de recuperación y acceso documental cruzado; las FK no sustituyen autorización.
- Borrado elimina métricas históricas → decisión explícita en aprobación; revisar esquema si se necesita conservación.
- Commit SQL no elimina archivos → limpieza posterior y conciliación de archivos huérfanos.
- Caída durante consulta → estado de fallo recuperable y duración nula cuando no fue observada.
- Cambio de modelo de embeddings → detener publicación incompatible, regenerar todo el corpus y validar antes de reabrir consultas.
- Búsqueda exacta crece con volumen → medir antes de introducir un índice aproximado.

## Migration Plan

1. Mantener registradas las decisiones y políticas pendientes del SRS; la inicialización local fue autorizada por el usuario.
2. Usar las versiones verificadas y el perfil `gemini-embedding-2`/768 tanto al procesar documentos como al consultar; cualquier cambio requiere detener publicaciones, reindexar y, si cambia la dimensión, migrar el esquema.
3. Conservar la migración inicial aplicada y añadir cambios posteriores como nuevas migraciones, sin usuarios ni secretos reales versionados.
4. Ejecutar pruebas PostgreSQL/pgvector para cada cambio de esquema y pruebas de servicios cuando se implemente el backend.
5. Documentar respaldo y restauración antes de usar datos persistentes. La reversión inicial se probó en desarrollo vacío; con datos un downgrade destructivo requiere respaldo y autorización.

### Local database applied

Por petición del usuario, se creó y levantó la base local el 2026-09-16 mediante Docker Compose. Se usan migraciones SQL de creación/reversión ejecutadas con `psql`, sin añadir dependencias Python antes de implementar el backend. La imagen pgvector está fijada por digest; se verificaron PostgreSQL 16.15 y pgvector 0.8.6.

La dimensión inicial y actual es 768. El 2026-09-21 se seleccionó `gemini-embedding-2` con salida de 768 dimensiones como perfil global; no se mezclan embeddings de otros modelos aunque tengan el mismo tamaño. Se verificaron creación, reversión en esquema vacío, reaplicación y conservación de tablas tras recrear el contenedor.

## Approval decisions

### FastAPI bootstrap

El usuario autorizó crear la aplicación FastAPI y su configuración como siguiente paso. Se añade arranque de API, `/api/v1/health`, documentación en desarrollo, configuración por entorno y contenedor backend. Este paso aplica RNF-01/RNF-03/RNF-04 y RS-04/RS-09, y no declara implementados conexión, modelos ORM ni autenticación. La salud inicial es de proceso, no de base de datos.

### Aprobación del usuario del 2026-09-22

El usuario aprobó el SRS 0.1 como referencia para implementar el MVP y confirmó estas decisiones: documentos exclusivos por chatbot; gestión compartida entre investigadores con `created_by` solo como trazabilidad; borrado físico en cascada de chatbot, documentos, fragmentos, consultas y métricas; originales en volumen privado para reproceso; capturas temporales fuera de la base de conocimiento; y duración medida desde la recepción en backend hasta que la respuesta queda lista, dejando nula la duración de errores sin respuesta observada.

También aprobó la carga administrativa de PDF, DOCX, TXT y CSV de hasta 20 MiB por archivo. El backend valida extensión, MIME declarado, contenido mínimo según el formato y tamaño antes de persistir el original bajo una clave generada, fuera de recursos públicos.

La inicialización local fue autorizada anteriormente. El perfil de embeddings quedó fijado en `gemini-embedding-2`/768 antes de incorporar conocimiento.

### Perfil de embeddings

El usuario autorizó continuar con la siguiente tarea y se seleccionó `gemini-embedding-2` con `output_dimensionality=768`, compatible con `vector(768)`. La documentación oficial de Gemini indica que el modelo admite entrada multimodal, dimensiones flexibles entre 128 y 3072, recomienda 768 entre sus tamaños habituales y normaliza automáticamente las salidas truncadas. El servicio rechaza lotes y consultas cuyo modelo o dimensión no coincidan exactamente. [Documentación oficial de embeddings de Gemini](https://ai.google.dev/gemini-api/docs/embeddings).

## Inference selection in Version 1

El usuario aprobó para Version 1 la selección por chatbot entre proveedor externo de IA y Ollama local. El detalle se registra en la sección 12 de [docs/database-design.md](../../../docs/database-design.md) y la implementación se planifica en `add-local-ollama-provider`.

El diseño incorpora `llm_models(id, provider, model)`. `chatbots.configured_llm_model_id` representa la selección actual y `queries.executed_llm_model_id` conserva el modelo usado. Credenciales y conexiones permanecerán en backend. La habilitación funcional de Ollama pertenece a Version 1.

El perfil de embeddings sigue siendo una decisión independiente: cambiar el motor generativo no obliga a reindexar. La compatibilidad multimodal de las combinaciones admitidas se validará durante la implementación de Version 1.
