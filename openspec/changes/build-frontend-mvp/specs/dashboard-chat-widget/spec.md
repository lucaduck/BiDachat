## Purpose

Permitir insertar una interfaz conversacional BIDACHAT independiente del framework del dashboard y conectada solo con la API pública.

## ADDED Requirements

### Requirement: Widget integration is framework independent

El widget SHALL poder inicializarse con el identificador estable de un chatbot dentro de un dashboard sin depender del framework anfitrión. Referencias: RF-10, RF-23, RNF-01, RNF-02 y CA-UC05-01 a CA-UC05-04.

#### Scenario: Embedded dashboard

- **WHEN** un dashboard carga el widget con un chatbot válido
- **THEN** el usuario puede abrir la interfaz conversacional sin que el dashboard deba conocer la configuración interna del chatbot

### Requirement: Widget conversations use only the public API

El widget MUST enviar preguntas y entradas visuales admitidas únicamente a los endpoints públicos de BIDACHAT; no puede incluir secretos ni acceder a PostgreSQL, RAG, Gemini u Ollama. Referencias: RNF-01, RS-04 y CA-UC05-03.

#### Scenario: Public request

- **WHEN** un usuario envía una consulta desde el widget
- **THEN** el widget muestra el estado de procesamiento y utiliza la respuesta pública de la API sin revelar datos internos

### Requirement: Widget handles conversational states

El widget SHALL presentar conversación vacía, mensajes de usuario y asistente, procesamiento y errores seguros, adaptándose al espacio disponible. Referencias: RF-18–RF-22, RNF-08 y RNF-09.

#### Scenario: Query failure

- **WHEN** la API no puede completar una consulta
- **THEN** el widget conserva la pregunta del usuario y muestra una explicación segura con una opción para reintentar
