## Purpose

Recoger la satisfacción voluntaria de visitantes al terminar una conversación y ofrecer resultados agregados verificables a los investigadores sin exponer conversaciones ajenas.

## ADDED Requirements

### Requirement: Optional survey at explicit conversation finish

El widget SHALL ofrecer el cuestionario únicamente cuando el visitante elija finalizar una conversación que tenga al menos una respuesta completada. SHALL permitir omitirlo, cerrarlo y seguir usando el asistente sin exigir datos personales. Cerrar el panel o iniciar una conversación nueva no SHALL enviar una evaluación automáticamente.

#### Scenario: Visitor finishes an answered conversation
- **WHEN** el visitante selecciona «Finalizar conversación» después de una respuesta completada
- **THEN** el widget muestra una encuesta opcional y accesible sin interrumpir la consulta anterior

#### Scenario: Visitor omits the survey
- **WHEN** el visitante elige «Omitir»
- **THEN** el widget inicia una conversación nueva sin registrar una valoración

#### Scenario: Conversation has no completed answer
- **WHEN** el visitante intenta finalizar una conversación sin respuestas completadas
- **THEN** el widget la reinicia sin ofrecer ni enviar una encuesta

### Requirement: Brief structured satisfaction response

La encuesta SHALL admitir una puntuación general entera de 1 a 5, resolución percibida (sí, parcialmente o no), claridad entera de 1 a 5 y comentario opcional limitado. Solo la puntuación general SHALL ser obligatoria para enviar; los campos omitidos SHALL permanecer ausentes de sus propios agregados. El usuario SHALL poder revisar y corregir la selección antes del envío.

#### Scenario: Valid minimal response
- **WHEN** el visitante selecciona satisfacción 4 y envía sin completar los otros campos
- **THEN** el sistema registra satisfacción 4 y no imputa resolución ni claridad

#### Scenario: Invalid response
- **WHEN** el cliente envía una puntuación fuera de 1 a 5, una opción desconocida o un comentario demasiado largo
- **THEN** la API rechaza la solicitud sin guardar una evaluación parcial

### Requirement: Scoped and single submission

La API SHALL aceptar una oferta y una evaluación como máximo por conversación vigente que tenga una respuesta completada y coincida con chatbot, origen autorizado e identidad firmada cuando esté configurada. SHALL limitar el abuso, no revelar si una conversación ajena existe y no proporcionar lectura pública de evaluaciones o comentarios. Tras un envío correcto SHALL rechazar cambios posteriores; una repetición idéntica no SHALL crear otra evaluación.

#### Scenario: Wrong chatbot, origin or identity
- **WHEN** se usa el identificador de una conversación desde otro chatbot, origen o identidad firmada
- **THEN** la API rechaza la operación sin confirmar la existencia de esa conversación

#### Scenario: Duplicate response
- **WHEN** se repite el envío para la misma conversación
- **THEN** existe una sola evaluación contabilizable y la respuesta guardada no cambia

#### Scenario: Expired conversation
- **WHEN** se intenta responder después de que la conversación haya vencido
- **THEN** la API rechaza el envío y el widget permite continuar con una conversación nueva

### Requirement: Privacy and lifecycle of feedback

El sistema SHALL conservar la evaluación cuantitativa y el momento de oferta independientemente de la eliminación de memoria vencida. SHALL almacenar el comentario únicamente durante el plazo aprobado en SRS y eliminarlo después; SHALL NOT copiar a la evaluación preguntas, respuestas, imágenes, nombre, correo, credenciales, origen o identidad del visitante. Al eliminar un chatbot SHALL eliminar sus evaluaciones. Los comentarios se mostrarán solo a investigadores autenticados y como texto no ejecutable.

#### Scenario: Memory expires
- **WHEN** la limpieza elimina una conversación vencida y sus turnos
- **THEN** sus puntuaciones y oferta permanecen para agregados, y la API pública no permite agregar otra respuesta a esa conversación

#### Scenario: Comment retention ends
- **WHEN** vence el plazo aprobado de conservación del comentario
- **THEN** el texto se elimina sin borrar las puntuaciones ni alterar los agregados

### Requirement: Filtered and interpretable satisfaction metrics

El panel administrativo SHALL mostrar, por chatbot y periodo, número de ofertas y respuestas, participación (respuestas/ofertas), CSAT (puntuaciones 4 o 5 / puntuaciones válidas), distribución de 1 a 5, resolución percibida, promedio de claridad y evolución temporal con tamaños de muestra. SHALL identificar los valores sin muestra como no disponibles y SHALL aplicar el mismo periodo y zona horaria UTC a tarjetas, gráficos y tabla accesible. No SHALL presentar estas valoraciones como prueba de exactitud de la IA.

#### Scenario: Mixed and omitted optional answers
- **WHEN** un periodo contiene respuestas completas y otras sin resolución o claridad
- **THEN** cada gráfico usa solo su denominador válido y muestra el número de respuestas utilizado

#### Scenario: No offers in period
- **WHEN** el filtro no incluye ofertas
- **THEN** el panel muestra cero ofertas y participación/CSAT como no disponibles, sin dividir por cero

#### Scenario: Unauthorized metrics access
- **WHEN** un visitante sin sesión administrativa solicita resultados o comentarios
- **THEN** la API deniega el acceso
