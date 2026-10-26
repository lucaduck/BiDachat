## 1. Requisitos y decisión de datos

- [x] 1.1 Revisar SRS, widget, API de consultas, memoria, limpieza, métricas y esquema PostgreSQL; registrar propuesta, especificación y diseño en este cambio.
- [x] 1.2 Incorporar a SRS un RF de encuesta, otro de consulta de satisfacción y criterios CA para oferta, omisión, envío único, seguridad, métricas y eliminación; confirmar allí la retención de comentario propuesta de 90 días.
- [x] 1.3 Actualizar docs/database-design.md con cardinalidad 1:0..1 por conversación, independencia de la limpieza de memoria, restricciones, índices y política de eliminación; contrastar el diseño con las migraciones vigentes.

## 2. Persistencia y servicio

- [x] 2.1 Crear migraciones de subida y reversión para `conversation_feedback`, con FK a chatbot, `conversation_id` único sin FK a memoria, controles de valores y fechas UTC; agregar el modelo SQLAlchemy.
- [x] 2.2 Implementar servicio transaccional de oferta que compruebe conversación vigente, chatbot, origen, identidad y al menos una consulta completada; insertar una sola oferta pese a peticiones concurrentes.
- [x] 2.3 Implementar envío con satisfacción obligatoria, campos opcionales, comentario máximo de 1000 caracteres, reenvío idéntico idempotente y conflicto si se intenta cambiar una respuesta guardada.
- [x] 2.4 Integrar borrado del texto de comentarios vencidos en la limpieza periódica sin eliminar las puntuaciones ni las ofertas.

## 3. Contrato y seguridad de API

- [x] 3.1 Crear esquemas y dos POST públicos de oferta/respuesta bajo `/api/v1/chatbots/{chatbot_id}/`, reutilizando comprobación estricta de origen, identidad firmada y cuotas específicas; devolver errores indistinguibles para conversación ajena, desconocida o vencida.
- [x] 3.2 Crear GET administrativo de agregados filtrados por chatbot, periodo UTC y agrupación; incluir contadores base, distribución y serie para que el frontend no recalcule denominadores incompatibles.
- [x] 3.3 Si se muestran comentarios, crear GET administrativo paginado y filtrado que no entregue identificadores de conversación, origen ni identidad; verificar representación como texto seguro.

## 4. Experiencia del widget

- [x] 4.1 Añadir «Finalizar conversación» sin alterar «Nueva conversación» ni «Cerrar asistente»; ofrecer encuesta solo tras respuesta completada y confirmar la oferta con la API antes de mostrarla.
- [x] 4.2 Diseñar formulario accesible con escala de 1 a 5, resolución, claridad, comentario opcional, «Enviar» y «Omitir»; admitir teclado, lectores de pantalla y ambos temas.
- [x] 4.3 Conservar identificador y borrador ante fallos de red; reiniciar después de envío u omisión; evitar doble envío y envío automático al cerrar panel, cambiar identidad o vencer la conversación.
- [x] 4.4 Verificar el flujo en la vista previa funcional y en una página externa autorizada; mantener la vista puramente visual del editor sin llamadas de encuesta.

## 5. Métricas del panel

- [x] 5.1 Añadir tipos y servicio frontend para métricas de satisfacción, compartiendo chatbot, periodo y agrupación UTC con las métricas de consultas; indicar que el filtro «Estado» solo aplica a consultas.
- [x] 5.2 Mostrar ofertas, respuestas, participación, CSAT, claridad y resolución con denominadores y estados vacíos; añadir distribución, evolución y tabla accesible de los mismos agregados.
- [x] 5.3 Mostrar comentarios únicamente en vista administrativa, con paginación y texto sin ejecución; explicar que satisfacción expresa percepción y que una respuesta tardía actualiza la cohorte de su oferta.

## 6. Verificación y entrega

- [x] 6.1 Probar en PostgreSQL + pgvector la unicidad concurrente, transacciones, limpieza de memoria, retención de comentario, cascada de chatbot, agregados y reversión de migración.
- [x] 6.2 Probar API con origen autorizado/no autorizado, chatbot cruzado, identidad firmada válida/inválida, conversación vencida, ausencia de respuesta completada, campos inválidos, duplicados, cuota y lectura administrativa protegida.
- [x] 6.3 Probar widget con teclado, tema claro/oscuro, error y reintento, omisión, reinicio y página externa; comprobar que el frontend muestra las mismas cifras que la API en cada filtro.
- [x] 6.4 Ejecutar pruebas afectadas, Ruff, ESLint/Prettier, compilación de widget/frontend y validación OpenSpec; documentar resultados y limitaciones en este cambio.
- [x] 6.5 Revisar el diff y patrones de secretos; actualizar README y documentación operativa con el comportamiento final y el procedimiento de reversión.

## Evidencia de cierre — 21 de octubre de 2026

- Migraciones `001`–`007` aplicadas en una base PostgreSQL + pgvector aislada; `007` revertida y reaplicada correctamente. La base temporal se eliminó al finalizar.
- `backend/tests/test_satisfaction_api.py`: 1 prueba de integración aprobada. Incluye oferta concurrente, origen, chatbot e identidad, conversación vencida o sin respuesta, validación, cuota, acceso administrativo, cohorte UTC, redacción de comentario y cascada.
- `backend/tests/test_conversation_cleanup_service.py` y `test_widget_identity.py`: 4 pruebas aprobadas.
- `frontend/e2e/widget-satisfaction.spec.ts`: 4 pruebas aprobadas en temas claro y oscuro, página externa, teclado, omisión, reintento y vista de apariencia. `frontend/e2e/metrics.spec.ts`: pruebas nuevas del panel y vista previa funcional aprobadas contra una instancia compilada local.
- Compilaciones de widget y Next.js, TypeScript, Ruff, ESLint/Prettier y validación OpenSpec aprobadas; `git diff --check` sin errores.
- La prueba de una instancia desplegada en VPS queda fuera de esta ejecución. La cuota pública en memoria se aplica por proceso FastAPI, como la cuota de consultas existente; si se usan varias réplicas, deberá colocarse el límite compartido en el proxy o diseñar un mecanismo distribuido antes de considerarla una cuota global.
