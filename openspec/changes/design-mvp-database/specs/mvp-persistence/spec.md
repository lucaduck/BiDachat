## Purpose

Definir el comportamiento persistente mínimo del MVP para conservar configuración, conocimiento aislado y registros de consultas verificables. Implementación derivada del SRS 0.1 aprobado por el usuario el 2026-09-22.

## ADDED Requirements

La selección entre inferencia externa y Ollama local está aprobada para Version 1 y formalizada en el SRS. Este delta conserva únicamente su soporte de persistencia; la ejecución funcional se especifica y planifica en el cambio `add-local-ollama-provider`.

### Requirement: Administrative access can be revoked

El sistema SHALL conservar la información necesaria para autenticar investigadores autorizados y finalizar su acceso al cerrar sesión. Referencias: RF-01–RF-03, RS-01/RS-02, CA-UC01-01 a CA-UC01-04.

#### Scenario: Authorized login

- **WHEN** un investigador activo proporciona credenciales válidas
- **THEN** el sistema permite una sesión administrativa verificable en peticiones posteriores

#### Scenario: Revoked access

- **WHEN** un investigador cierra sesión e intenta reutilizar esa sesión
- **THEN** el sistema deniega las operaciones administrativas

#### Scenario: Invalid or inactive credentials

- **WHEN** las credenciales son inválidas, la sesión expiró o el investigador está inactivo
- **THEN** el sistema deniega el acceso administrativo

### Requirement: Chatbot configuration persists

El sistema SHALL conservar los chatbots y su selección de una combinación admitida de proveedor y modelo, además de instrucciones y fuentes asociadas, permitiendo consultar y editar los datos registrados. Referencias: RF-04–RF-06/RF-08/RF-09/RF-11, CA-UC02-01 a CA-UC02-03, CA-UC03-01 a CA-UC03-04.

#### Scenario: Saved configuration

- **WHEN** un investigador guarda una configuración válida y vuelve a consultarla
- **THEN** obtiene el proveedor, el modelo, las instrucciones y las fuentes guardadas para ese chatbot

#### Scenario: Stable integration

- **WHEN** cambia la combinación de proveedor y modelo generativo de un chatbot existente
- **THEN** la integración del dashboard conserva su identificador y utiliza la nueva configuración sin modificar el snippet

### Requirement: Knowledge retrieval is isolated by chatbot

El sistema SHALL permitir recuperar únicamente conocimiento correctamente procesado y asociado al chatbot consultado. Referencias: RF-13–RF-17, RS-05–RS-07, CA-UC04-01 a CA-UC04-05.

#### Scenario: Ready knowledge

- **WHEN** termina correctamente el procesamiento de un documento admitido
- **THEN** su contenido queda disponible para recuperación semántica del chatbot asociado

#### Scenario: Cross-chatbot access

- **WHEN** se consulta el chatbot A y un documento pertenece exclusivamente al chatbot B
- **THEN** ese documento no forma parte del contexto de A y no puede administrarse mediante las rutas documentales de A

#### Scenario: Interrupted processing

- **WHEN** el procesamiento falla o se interrumpe antes de finalizar
- **THEN** sus resultados parciales no se ofrecen como conocimiento listo y un reintento no duplica los fragmentos disponibles

### Requirement: Query records support attributable metrics

El sistema SHALL registrar cada consulta aceptada, asociarla al chatbot correcto y conservar su duración observada para consulta administrativa. Referencias: RF-24–RF-27, RNF-06/RNF-07, CA-UC06-05, CA-UC07-05, CA-UC08-01 a CA-UC08-04. La definición de duración y tratamiento de interrupciones se propone en el diseño de datos para aprobación.

#### Scenario: Completed query

- **WHEN** termina una consulta textual o con imagen
- **THEN** su registro identifica al chatbot, la combinación de proveedor y modelo usada, el resultado y el tiempo observado desde recepción hasta respuesta lista en backend

#### Scenario: Unobserved completion

- **WHEN** una interrupción del proceso impide observar la finalización de una consulta
- **THEN** el sistema distingue el fallo sin duración medida y no inventa una muestra de latencia

#### Scenario: Empty metrics

- **WHEN** un investigador consulta métricas de un chatbot sin consultas
- **THEN** el conteo es cero y la duración media se indica como no disponible

#### Scenario: Unauthorized metrics access

- **WHEN** un usuario no autorizado solicita métricas administrativas
- **THEN** el sistema deniega su acceso

### Requirement: Deleted chatbots become unavailable

El sistema SHALL retirar un chatbot eliminado de la gestión y de la integración pública y evitar que su conocimiento se reutilice en otro chatbot. Referencias: RF-07, RS-07, CA-UC02-04. La eliminación física de consultas y archivos depende de la política propuesta pendiente de aprobación.

#### Scenario: Delete existing chatbot

- **WHEN** finaliza correctamente la eliminación de un chatbot
- **THEN** deja de estar disponible y nuevas solicitudes a su identificador no generan respuestas ni recuperan su conocimiento

### Requirement: Private infrastructure data stays in the backend

El sistema SHALL mantener credenciales y detalles internos fuera de las respuestas públicas, la configuración del widget y los recursos públicos. Referencias: RS-04/RS-09 y CA-UC05-03.

#### Scenario: Public integration data

- **WHEN** se entrega el mecanismo de integración o un error al cliente
- **THEN** no contiene claves privadas, hashes de autenticación, rutas privadas, cadenas de conexión ni trazas internas
