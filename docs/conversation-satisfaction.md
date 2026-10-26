# Satisfacción de las conversaciones

La encuesta responde a RF-37–RF-39 y CA-UC06-14–16/CA-UC08-08–09 de [SRS.md](../SRS.md). Es voluntaria y se ofrece únicamente al pulsar «Finalizar conversación» después de recibir una respuesta. «Cerrar asistente» conserva el formulario; «Omitir» y «Nueva conversación» reinician sin enviar una valoración.

## API y seguridad

El widget llama a `POST /api/v1/chatbots/{chatbot_id}/survey-offers` con `conversation_id` y, si existe, `identity_token`. Después llama a `POST /api/v1/chatbots/{chatbot_id}/survey-responses` con esos campos, `satisfaction_score` (1–5) y, opcionalmente, `resolution` (`yes`, `partial`, `no`), `clarity_score` (1–5) y `comment` (hasta 1000 caracteres). Ambas rutas requieren un único `Origin` autorizado, comprueban chatbot, identidad, conversación vigente y al menos una respuesta completada, y tienen una cuota propia de 20 solicitudes por minuto y cliente/chatbot. Una oferta repetida y una respuesta idéntica son idempotentes; modificar una valoración ya enviada produce 409. No hay lectura pública.

El panel autenticado utiliza `GET /api/v1/chatbots/{chatbot_id}/satisfaction-metrics` y `GET /api/v1/chatbots/{chatbot_id}/survey-responses` (comentarios, `limit` 1–50 y `offset`). Aceptan `started_at` inclusivo y `ended_at` exclusivo con zona horaria; el primer endpoint admite `interval=day|week|month`. Los comentarios nunca entregan identificadores de conversación, origen ni identidad y se dibujan como texto, sin ejecutar HTML.

## Cálculo

La cohorte se define por `offered_at` en UTC. Una respuesta posterior actualiza el periodo en que se ofreció la encuesta. Participación = respuestas / ofertas. CSAT = puntuaciones 4 o 5 / respuestas. Claridad media y tasa de resolución consideran solo respuestas que llenaron esos campos. Si falta denominador, la API devuelve `null` y la interfaz presenta «Sin datos». El filtro «Estado» de Métricas corresponde únicamente a consultas. Estas cifras miden percepción, no exactitud factual de la IA.

## Retención y operación

La migración `007_conversation_feedback` es aditiva. El corredor versionado la aplica a un volumen existente antes de sustituir el backend; un volumen nuevo la crea en la inicialización. La limpieza periódica borra el texto de comentarios 90 días después del envío y conserva oferta y puntuaciones mientras exista el chatbot. La memoria conversacional puede expirar antes: `conversation_id` es único, pero no tiene FK a `conversations`. El borrado del chatbot elimina sus evaluaciones mediante la FK de `chatbot_id`.

Antes de revertir, realiza un respaldo. La reversión de aplicación puede retirar panel, widget y API y conservar la tabla para revisión. `007_conversation_feedback.down.sql` elimina la tabla y todas sus evaluaciones; usarlo requiere decisión explícita sobre la pérdida de esos datos.

## Verificación local

Ejecuta las migraciones con `docker/postgres/migrate-database.sh` en una copia aislada. Prueba `backend/tests/test_satisfaction_api.py` sobre esa copia para cubrir concurrencia, aislamiento, validación, agregados, retención y cascada. `frontend/e2e/widget-satisfaction.spec.ts` prueba los dos temas, página externa, omisión, reintento y vista de apariencia. `frontend/e2e/metrics.spec.ts` comprueba filtros y representación segura del comentario.
