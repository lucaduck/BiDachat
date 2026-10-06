## Purpose

Permitir que los chatbots del MVP ejecuten inferencia con modelos Ollama locales sin exponer su conexión a clientes públicos.

## ADDED Requirements

### Requirement: A chatbot can use an admitted local Ollama model

El sistema SHALL permitir que un investigador configure un chatbot con una combinación admitida de proveedor `ollama` y modelo local, además de las combinaciones de proveedor externo admitidas. Referencias: RF-08, RNF-05 y RNF-10.

#### Scenario: Saved local model selection

- **WHEN** un investigador guarda un chatbot con un modelo Ollama admitido
- **THEN** el chatbot conserva esa combinación y su identificador de integración no cambia

### Requirement: Queries are executed through the configured provider

El sistema SHALL enviar cada consulta aceptada al proveedor y modelo capturados al inicio de la consulta, usando Ollama cuando la combinación ejecutada tenga proveedor `ollama`. Referencias: RF-18, RF-20–RF-22, RF-24–RF-26 y CA-UC06-04/CA-UC06-05.

#### Scenario: Local inference succeeds

- **WHEN** una consulta textual se ejecuta con un modelo Ollama disponible
- **THEN** el sistema devuelve su respuesta y conserva el modelo ejecutado, estado y duración de la consulta

#### Scenario: Provider selection remains stable during a query

- **WHEN** se cambia la configuración actual del chatbot mientras una consulta ya fue aceptada
- **THEN** esa consulta usa la combinación capturada al aceptarla y la siguiente usa la nueva configuración

### Requirement: Local provider failures are safe and measurable

El sistema MUST manejar la indisponibilidad, respuesta inválida o modelo local no disponible sin revelar direcciones internas, credenciales ni trazas al cliente. Referencias: RS-04, RS-09, RNF-06 y RNF-07.

#### Scenario: Ollama is unavailable

- **WHEN** el proveedor local no responde o el modelo solicitado no está disponible
- **THEN** el sistema registra el fallo de la consulta conforme a su estado observado y devuelve un error público seguro

### Requirement: Ollama remains a backend-only dependency

El frontend y el widget MUST comunicarse exclusivamente con la API de BIDACHAT y nunca con el servicio Ollama. Referencias: RNF-01 y CA-UC05-03.

#### Scenario: Public integration

- **WHEN** se entrega el mecanismo de integración de un chatbot configurado con Ollama
- **THEN** no contiene la dirección del servicio local ni credenciales del proveedor

### Requirement: Local document embeddings

El sistema SHALL generar embeddings de documentos y consultas mediante Ollama cuando EMBEDDING_PROVIDER sea ollama, sin requerir credenciales Gemini. Referencias RF-14–RF-17.

#### Scenario: Local retrieval

- **WHEN** un documento se procesa con EmbeddingGemma y el usuario consulta su chatbot
- **THEN** se generan vectores de 768 dimensiones localmente y solo se recuperan fragmentos del mismo chatbot y perfil
