## Purpose

Mantener una conversación coherente en el widget sin convertir datos anónimos
de visitantes en cuentas administrativas ni exponer su historial públicamente.

## ADDED Requirements

### Requirement: Scoped anonymous conversation

El sistema SHALL aceptar un identificador de conversación opaco en una consulta
pública y asociarlo únicamente con el chatbot y origen autorizados que lo
emitieron. Un identificador desconocido, vencido o perteneciente a otro chatbot
u origen SHALL iniciar una conversación nueva sin revelar ni reutilizar turnos
ajenos.

#### Scenario: Consecutive visitor messages

- **WHEN** el widget envía dos consultas válidas con el mismo identificador de conversación activo
- **THEN** la segunda respuesta recibe los turnos recientes de esa misma conversación como contexto

#### Scenario: Cross-chatbot identifier

- **WHEN** un cliente usa un identificador emitido para un chatbot al consultar otro chatbot
- **THEN** el sistema no incorpora el historial anterior y responde sin exponer información de la otra conversación

### Requirement: Bounded retained conversation context

El sistema SHALL conservar únicamente turnos textuales recientes, hasta el
límite configurado de turnos, caracteres y vigencia. Las imágenes adjuntas,
datos de autenticación y secretos SHALL NOT persistirse como memoria
conversacional. La consulta actual seguirá pudiendo procesar su imagen según el
contrato multimodal existente.

#### Scenario: Context exceeds configured limit

- **WHEN** una conversación supera el límite de contexto retenible
- **THEN** el sistema conserva los turnos más recientes dentro del límite y descarta los más antiguos de la memoria enviada al modelo

#### Scenario: Expired conversation

- **WHEN** llega una consulta con una conversación cuya vigencia ya venció
- **THEN** el sistema no incluye sus turnos anteriores y registra una nueva conversación activa

### Requirement: Controlled lifecycle and observability

El sistema SHALL almacenar el estado necesario para recuperar memoria sin
alterar los registros de métricas de `queries`. El sistema SHALL permitir
expirar y depurar conversaciones vencidas mediante una operación controlada.
El historial no SHALL exponerse mediante un endpoint público de lectura.

#### Scenario: Conversation cleanup

- **WHEN** se ejecuta la limpieza de conversaciones vencidas
- **THEN** se eliminan o anonimizan los turnos retenidos conforme a la política configurada sin eliminar métricas históricas de consultas

#### Scenario: Failed generation

- **WHEN** el proveedor falla al responder una consulta con memoria
- **THEN** la consulta conserva su estado fallido y no se añade una respuesta inexistente al historial conversacional

### Requirement: Visitor initiated and idle reset

El widget SHALL permitir iniciar una conversación nueva y SHALL reiniciar la
memoria tras un periodo configurable de inactividad. El siguiente mensaje no
SHALL recuperar turnos de la conversación anterior. Referencias: RF-34 y
CA-UC06-11.

#### Scenario: Visitor starts a new conversation

- **WHEN** el visitante selecciona Nueva conversación
- **THEN** el widget limpia los mensajes visibles y utiliza un identificador nuevo

#### Scenario: Widget inactivity

- **WHEN** se supera el plazo de inactividad configurado
- **THEN** el siguiente mensaje utiliza una conversación nueva

### Requirement: Optional signed visitor identity

Cuando el sitio anfitrión configure identidad firmada, el sistema SHALL validar
una credencial breve emitida por su servidor y aislar la memoria por seudónimo,
chatbot y origen. Una credencial ausente, vencida o inválida SHALL rechazarse
sin utilizar memoria anónima. Referencias: RF-35 y CA-UC06-12.

#### Scenario: Authenticated host changes visitor

- **WHEN** otra identidad firmada presenta un identificador de conversación anterior
- **THEN** el backend crea otra conversación sin recuperar sus mensajes

#### Scenario: Signature or expiry is invalid

- **WHEN** una credencial se modifica o vence
- **THEN** la consulta se rechaza sin generar respuesta ni recuperar memoria

### Requirement: Scheduled expiration cleanup

El backend SHALL ejecutar periódicamente la limpieza de conversaciones vencidas
y conservar consultas y métricas. Referencias: RF-36 y CA-UC06-13.

#### Scenario: Periodic cleanup runs

- **WHEN** el proceso de limpieza encuentra conversaciones vencidas
- **THEN** elimina sus mensajes y preserva los registros históricos de consultas
