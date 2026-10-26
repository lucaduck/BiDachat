## Purpose

Permitir que BIDACHAT consuma modelos Vertex AI mediante un gateway en infraestructura propia, conservando aislamiento, trazabilidad y contratos públicos existentes.

## ADDED Requirements

### Requirement: Explicit model selection

El sistema SHALL permitir seleccionar Vertex y un modelo configurado disponible, conservando la identidad de modelos usados en consultas anteriores. Trazabilidad: RF-08, CA-UC03-01.

#### Scenario: Change provider

- **WHEN** un administrador cambia un chatbot de otro proveedor a un modelo Vertex habilitado
- **THEN** la siguiente consulta usa ese modelo y las consultas anteriores conservan su modelo registrado.

#### Scenario: Removed model

- **WHEN** un modelo Vertex deja de estar habilitado
- **THEN** no puede seleccionarse para nuevas configuraciones, sus referencias históricas permanecen y un chatbot aún asociado recibe indisponibilidad explícita sin sustitución silenciosa.

### Requirement: Multimodal responses through the backend

El sistema SHALL procesar texto e imágenes admitidas mediante el modelo Vertex seleccionado, utilizando la API existente y el contexto autorizado del chatbot. Trazabilidad: RF-12, RF-18 a RF-23, RNF-01, RS-07.

#### Scenario: Text and image query

- **WHEN** una consulta válida contiene texto y una imagen compatible con el modelo configurado
- **THEN** el usuario recibe una respuesta o un error explícito y el cliente no accede directamente al gateway ni a Google.

#### Scenario: Isolated retrieval

- **WHEN** dos chatbots tienen fuentes distintas y uno consulta un dato conocido
- **THEN** solo se recuperan fuentes asociadas al chatbot consultado.

### Requirement: Explicit document vision profile

El sistema SHALL permitir configurar Vertex para describir fuentes visuales antes de generar embeddings, sin modificar automáticamente el perfil visual vigente. Trazabilidad: RF-13.

#### Scenario: Image source processing

- **WHEN** el perfil visual se configura explícitamente con un modelo Vertex multimodal y se carga una imagen válida
- **THEN** se genera su descripción antes de los embeddings y un fallo de inferencia deja un estado de fallo honesto sin publicar chunks incompletos.

### Requirement: Private optional operation

El gateway SHALL ejecutarse en infraestructura propia, con autenticación interna y sin exposición pública ni secretos en clientes. Su desactivación SHALL conservar los proveedores actuales. Trazabilidad: RNF-03, RNF-15, RS-04, RS-09.

#### Scenario: Disabled integration

- **WHEN** Vertex está deshabilitado y no existen credenciales Google
- **THEN** la aplicación arranca y utiliza los proveedores existentes sin requerir el gateway.

#### Scenario: Invalid credentials

- **WHEN** las credenciales del gateway o Google son inválidas
- **THEN** se rechaza la operación con un error seguro y no se exponen secretos en respuesta ni logs.

### Requirement: Honest result and execution history

El sistema SHALL registrar el resultado y tiempo de cada consulta con su modelo ejecutado, sin registrar como éxito respuestas vacías, bloqueadas o fallidas. Trazabilidad: RF-24 a RF-27, RS-09.

#### Scenario: Provider failure

- **WHEN** Vertex excede cuota, bloquea contenido, no responde dentro del plazo o devuelve una respuesta inválida
- **THEN** se registra la consulta fallida, se informa al usuario y no se ejecuta otro modelo silenciosamente.

#### Scenario: Successful query

- **WHEN** Vertex devuelve una respuesta válida para el modelo solicitado
- **THEN** se conserva el modelo identificado y se contabiliza la consulta y su duración en las métricas del chatbot.
