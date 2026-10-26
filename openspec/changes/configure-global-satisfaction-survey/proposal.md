## Why

La encuesta de RF-37 se ofrece hoy a todos los chatbots con textos y campos fijados en el widget. El investigador no puede administrarla sin modificar código, aunque RF-38 ya permite consultar los resultados por chatbot. El usuario decidió que la configuración sea global para todos; se necesita un único control administrativo que conserve el significado de las métricas históricas.

## What Changes

- Añadir «Cuestionario de satisfacción» en Configuración general, con activación común a todos los chatbots, textos editables, visibilidad de campos actuales y un editor de preguntas adicionales de opción única o texto libre. La satisfacción general de 1–5 permanece obligatoria para calcular CSAT de forma comparable.
- Guardar una única configuración global y versiones publicadas e inmutables del formulario. Relacionar cada oferta y respuesta con la versión mostrada al visitante; conservar las evaluaciones anteriores al editar o desactivar.
- Guardar preguntas, opciones y respuestas adicionales en relaciones normalizadas, sin duplicar configuraciones por chatbot ni convertir las respuestas en un JSON sin esquema.
- Entregar al widget la versión publicada necesaria para mostrar el formulario; el backend decide si acepta nuevas ofertas y valida cada respuesta contra la versión ofrecida.
- Mostrar vista previa y acción explícita de publicar en Configuración general. Métricas seguirá agrupando CSAT por chatbot y presentará resultados de preguntas personalizadas sin mezclar versiones con distinto significado.
- Añadir requisitos y criterios de aceptación al SRS antes de implementar código o migraciones.

El usuario confirmó alcance **global**, preguntas adicionales de **opción única o texto libre** y satisfacción general **obligatoria** de 1–5. No se incluyen preguntas de selección múltiple en este cambio.

## Capabilities

### New Capabilities

- `global-satisfaction-configuration`: administración y publicación global de formularios versionados, entrega segura al widget, respuestas a preguntas adicionales y conservación de evaluaciones históricas.

### Modified Capabilities

Ninguna. `openspec/specs/` no contiene todavía especificaciones principales; RF-37 a RF-39 y sus criterios en `SRS.md` son la referencia vigente.

## Impact

- PostgreSQL: migración aditiva de singleton global, versiones, preguntas, opciones y respuestas; FK de oferta a versión con backfill de evaluaciones existentes. `chatbots` y su relación con `conversation_feedback` se conservan.
- FastAPI: edición/publicación autenticada, lectura pública limitada al widget, validación de ofertas y respuestas por versión y consulta administrativa de resultados.
- Next.js: editor de preguntas y opciones dentro de Configuración general, vista previa y resultados por versión en Métricas.
- Widget JavaScript: cargar formulario publicado, presentar preguntas configuradas y enviar respuestas validadas sin afectar la conversación.
- Pruebas de migración y API en PostgreSQL + pgvector, integridad de versiones y respuestas, privacidad de texto libre y recorridos en ambos temas. Sin nuevos servicios ni dependencias.
