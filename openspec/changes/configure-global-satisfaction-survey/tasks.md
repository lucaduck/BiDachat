## 1. Requisitos y diseño aprobado

- [x] 1.1 Confirmar con el usuario configuración global, preguntas adicionales de opción única o texto libre y CSAT 1–5 siempre obligatorio; verificar estas decisiones en propuesta, especificación y diseño OpenSpec.
- [ ] 1.2 Añadir a `SRS.md` RF y CA para activación, editor de preguntas/opciones, publicación versionada, envío y consulta histórica; verificar trazabilidad con RF-37–RF-39 y escenarios de este cambio.
- [ ] 1.3 Actualizar `docs/database-design.md` con ERD, cardinalidades, 3FN, claves, restricciones, versionado y retención; verificar que coincida con la migración 008.

## 2. Migración y persistencia normalizada

- [ ] 2.1 Crear migración 008 para `survey_settings`, `survey_versions`, `survey_questions` y `survey_options`; verificar en PostgreSQL + pgvector singleton, posiciones únicas, FK, límites y versión inicial equivalente al formulario actual.
- [ ] 2.2 Añadir `conversation_feedback.survey_version_id`, asociar todas las ofertas históricas a versión 1 y establecer FK/NOT NULL sin cambiar puntuaciones ni fechas; verificar conteos y agregados antes/después en base aislada.
- [ ] 2.3 Crear `survey_choice_answers` y `survey_text_answers` con PK/FK compuestas, restricciones y redacción de texto libre; verificar inserción válida y rechazo de opción ajena, versión cruzada o tipo incompatible mediante pruebas SQL.
- [ ] 2.4 Proteger versiones publicadas y sus preguntas/opciones contra cambios directos; verificar que SQL de `INSERT`/`UPDATE`/`DELETE` sobre una versión publicada falla y que una nueva versión se puede construir y publicar transaccionalmente.
- [ ] 2.5 Registrar migración 008 y reversión en inicialización y corredor versionado; verificar volumen nuevo, existente, reaplicación controlada y reversión en copia aislada sin borrar `conversation_feedback` previo.

## 3. Administración y reglas del servidor

- [ ] 3.1 Implementar lectura administrativa y publicación atómica con `expected_version_id`, validación de hasta 10 preguntas y 10 opciones, orden, tipos y textos; verificar conflicto de edición, rollback ante error y que solo activar/desactivar no cree versión.
- [ ] 3.2 Implementar lectura pública del formulario activo con comprobación exacta de origen y sin datos administrativos; verificar rechazo de origen ajeno y que un fallo de carga no bloquee consultas.
- [ ] 3.3 Fijar y devolver la versión al crear una oferta, manteniendo idempotencia y rechazando nuevas ofertas desactivadas; verificar carrera entre publicación y oferta con pruebas de integración concurrente.
- [ ] 3.4 Validar y guardar en una transacción CSAT obligatorio y respuestas adicionales contra preguntas/opciones de la versión ofrecida; verificar pregunta requerida, opción ajena, duplicados, reenvío idéntico y conflicto sin escrituras parciales.
- [ ] 3.5 Extender limpieza periódica para redactar texto libre a los 90 días preservando la fila y su conteo; verificar retención, borrado en cascada de chatbot y conservación de versiones referenciadas.

## 4. Configuración, widget y resultados

- [ ] 4.1 Crear sección global de encuesta con estado, título, textos, campos actuales y editor para añadir/reordenar/quitar preguntas y opciones; verificar borrador conservado ante error, teclado, móvil y ambos temas.
- [ ] 4.2 Mostrar vista previa no interactiva y acción explícita «Guardar y publicar» con alcance global y número de versión; verificar que cambiar el borrador no afecta al widget antes de publicar.
- [ ] 4.3 Hacer que el widget lea estado inicial, registre oferta y renderice el formulario de la versión devuelta por la oferta; verificar cambios entre GET/POST, desactivación, omisión y reintento en una página externa autorizada.
- [ ] 4.4 Presentar y enviar preguntas de opción única y texto libre con estados accesibles, validación de requeridas y CSAT fijo; verificar que los datos no se envían al LLM ni se ejecuta HTML.
- [ ] 4.5 Añadir resultados administrativos por chatbot, periodo y versión: distribución de opciones y textos libres paginados; verificar que CSAT histórico permanece comparable y que preguntas de versiones distintas no se agregan juntas.

## 5. Aceptación y operación

- [ ] 5.1 Ejecutar pruebas integradas en PostgreSQL + pgvector para versión histórica, claves, integridad cruzada, concurrencia, redacción y cascada; documentar evidencia sin tocar datos del usuario.
- [ ] 5.2 Ejecutar pruebas afectadas de API, frontend y widget, Ruff, ESLint/Prettier, compilaciones y `openspec validate --strict`; registrar resultados y limitaciones reales.
- [ ] 5.3 Actualizar README y guías de encuesta, API y migración/reversión; verificar enlaces, ausencia de secretos y `git diff --check`.
