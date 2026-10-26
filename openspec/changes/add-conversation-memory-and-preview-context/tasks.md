## 0. Evidencia y decisiones ya realizadas

- [x] 0.1 Inspeccionar persistencia actual: `queries` almacena auditoría y métricas, pero no tiene `conversation_id` ni el servicio recupera turnos anteriores.
- [x] 0.2 Confirmar que el widget externo ya recoge `data-context-selector` por turno, con límite de 6000 caracteres y exclusión de controles; la ruta `/preview` no entrega ese atributo.
- [x] 0.3 Verificar Vertex local mediante LiteLLM: aplicación saludable, `gemini-3.1-flash-lite` respondió a una consulta temporal y el chatbot de prueba fue eliminado.
- [x] 0.4 Documentar propuesta, especificaciones, diseño, riesgos, reversión y ruta de continuación en este cambio de OpenSpec.

## 1. Aprobación de datos y configuración

- [x] 1.1 Incorporar al SRS el requisito aprobado de memoria conversacional anónima, contexto de Preview y catálogo Vertex múltiple; relacionarlo con RF-18 a RF-27, RNF-01, RNF-04, RNF-05, RS-04, RS-07 y RS-09.
- [x] 1.2 Actualizar `docs/database-design.md` con `conversations`, `conversation_messages`, relación opcional desde `queries`, cardinalidades, índices, retención y eliminación.
- [ ] 1.3 Confirmar la política institucional de retención; usar como valor inicial solo si no se define otra: 24 horas, 12 turnos y 12000 caracteres.
- [x] 1.4 Definir variables validadas de memoria y `VERTEX_MODELS`; preservar `VERTEX_MODEL` como valor predeterminado compatible y no incluir modelos no comprobados.

## 2. Persistencia y memoria conversacional

- [x] 2.1 Crear migración PostgreSQL para conversaciones, mensajes e índice de búsqueda de actividad; aplicar y revertir en una base de prueba con pgvector.
- [x] 2.2 Implementar modelos, esquemas y servicio de conversación con UUID opaco, alcance por chatbot y origen, expiración y límites de contenido.
- [x] 2.3 Extender `POST /api/v1/chatbots/{chatbot_id}/queries` con `conversation_id` opcional, manteniendo compatibilidad de clientes y validando identificador, origen y chatbot.
- [x] 2.4 Integrar la ventana de turnos recientes en el proveedor como bloque delimitado no confiable, separado de instrucciones, RAG, `page_context` e imagen actual.
- [x] 2.5 Implementar transacción de éxito y fallo: registrar turnos solo de manera coherente con el estado de `Query`, conservar métricas y no persistir imágenes ni respuestas inexistentes.
- [x] 2.6 Implementar limpieza controlada de conversaciones vencidas sin borrar consultas, métricas, fuentes ni configuraciones históricas.

## 3. Widget y vista previa

- [x] 3.1 Generar y conservar en `sessionStorage` el identificador por chatbot y origen; enviarlo en cada consulta y renovarlo cuando expire, cambie el chatbot o sea rechazado.
- [x] 3.2 Montar el widget de `/preview` con un selector específico de `.preview-dashboard` o ID estable, sin seleccionar `body`, navegación ni el panel del chat.
- [x] 3.3 Mantener la recolección de contexto visible por turno y verificar que cambios de KPI actualizan `page_context` sin reutilizar valores anteriores.
- [x] 3.4 Mostrar un mensaje recuperable al expirar o invalidarse una conversación, sin revelar motivos internos ni historial de otra sesión.

## 4. Catálogo de modelos Vertex

- [x] 4.1 Ampliar configuración y LiteLLM para una lista explícita de modelos Vertex permitidos, sus correspondencias y su modelo predeterminado.
- [x] 4.2 Actualizar bootstrap y servicio de chatbots para registrar modelos nuevos de forma idempotente, filtrar modelos retirados y conservar filas referenciadas por historial.
- [x] 4.3 Verificar cada modelo candidato con proyecto, ubicación, texto y capacidades visuales antes de exponerlo en el editor; registrar evidencia sanitizada y consumo dentro del presupuesto autorizado.
- [x] 4.4 Probar en el editor el filtro proveedor/modelo, carga de una selección previa, cambio de modelo y persistencia del modelo histórico de consultas.

## 5. Pruebas y aceptación

- [x] 5.1 Añadir pruebas unitarias de UUID, alcance chatbot+origen, expiración, límites, limpieza y ausencia de imágenes en memoria.
- [x] 5.2 Añadir pruebas de integración con PostgreSQL + pgvector para dos chatbots, dos conversaciones, aislamiento RAG, cambio de modelo, éxito y fallo del proveedor.
- [x] 5.3 Añadir pruebas Playwright de vista previa: `page_context` del tablero, KPI actualizado, historial de varios turnos, recarga y aislamiento por chatbot.
- [x] 5.4 Ejecutar una aceptación local real con un dato conocido: presentar nombre, preguntar nuevamente por ese dato, preguntar por un KPI del Preview y confirmar que no vuelve a pedir el nombre.
- [x] 5.5 Medir primera respuesta y respuestas posteriores con y sin memoria, registrar tamaño de contexto, mediana y p95 de una muestra suficiente; no declarar una mejora sin datos.
- [x] 5.6 Ejecutar regresiones de login, documentos/RAG, widget externo, métricas, proveedores existentes, lint, tipos y formato.

## 6. Operación y cierre

- [x] 6.1 Actualizar `.env.example`, README y guía de operación con retención, limpieza, límites de contexto, catálogo Vertex y reversión.
- [x] 6.2 Verificar despliegue Docker con variables activadas y desactivadas, sin servicios externos nuevos ni exposición de historial o secretos.
- [ ] 6.3 Preparar evidencia de aceptación, consumo y limitaciones; desplegar únicamente mediante PR aprobado y realizar smoke desde un origen permitido.
- [ ] 6.4 Marcar tareas completas solo tras pruebas verificadas y archivar el cambio cuando la documentación y aceptación estén coherentes.

## 7. Aislamiento de visitantes y operación

- [x] 7.1 Registrar RF-34–RF-36, diseño de identidad firmada y criterios de aceptación.
- [x] 7.2 Implementar reinicio visible y por inactividad en el widget, con protección ante respuestas en curso.
- [x] 7.3 Añadir migración y validación de identidad firmada opcional, con aislamiento por seudónimo, chatbot y origen y fallo cerrado.
- [x] 7.4 Ejecutar periódicamente la limpieza durante la vida del backend y al arrancar; conservar consultas y métricas.
- [x] 7.5 Documentar configuración y ejemplo del servidor anfitrión, gestión de claves, vencimiento y límites.
- [x] 7.6 Probar migraciones, aislamiento, credenciales inválidas, expiración, reinicio, limpieza y regresiones de widget/API.
