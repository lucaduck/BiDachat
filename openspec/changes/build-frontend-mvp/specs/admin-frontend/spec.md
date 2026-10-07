## Purpose

Proporcionar a investigadores autorizados una interfaz administrativa clara para operar los chatbots de BIDACHAT desde la API existente.

## ADDED Requirements

### Requirement: Administrative access is session protected

El panel administrativo SHALL solicitar inicio de sesión antes de mostrar operaciones de chatbots, documentos o métricas. El cliente MUST descartar el token de sesión al cerrar sesión o recibir una respuesta no autorizada. Referencias: RF-01–RF-03, RS-01 y RS-02.

#### Scenario: Unauthenticated visitor

- **WHEN** una persona abre una ruta administrativa sin sesión válida
- **THEN** ve la pantalla de inicio de sesión y no se muestran datos administrativos

#### Scenario: Session expires

- **WHEN** la API responde que la sesión dejó de ser válida
- **THEN** el cliente elimina el estado autenticado y dirige al inicio de sesión sin mostrar detalles internos

### Requirement: Researchers can manage chatbot configuration

El panel SHALL permitir listar, crear, consultar, editar y eliminar chatbots, incluido el modelo admitido y las instrucciones de comportamiento. Referencias: RF-04–RF-11 y CA-UC02-01 a CA-UC03-04.

#### Scenario: Create chatbot

- **WHEN** un investigador completa datos válidos y guarda un chatbot
- **THEN** la interfaz confirma la operación y muestra el chatbot en la lista

#### Scenario: Invalid configuration

- **WHEN** la API rechaza la configuración
- **THEN** la interfaz muestra un mensaje en español sin exponer información de infraestructura

### Requirement: Researchers can manage private knowledge sources

El panel SHALL permitir cargar y listar documentos exclusivamente dentro del chatbot seleccionado, mostrando su estado de procesamiento. Referencias: RF-09, RF-13–RF-17, RS-05–RS-07 y CA-UC04-01 a CA-UC04-05.

#### Scenario: Document upload feedback

- **WHEN** un investigador carga un documento admitido
- **THEN** la interfaz muestra progreso, resultado y el documento únicamente en el chatbot al que fue asociado

### Requirement: Researchers can inspect chatbot metrics

El panel SHALL mostrar por chatbot las consultas, estados y tiempos de respuesta disponibles, incluyendo un estado explícito cuando no existan datos. Referencias: RF-24–RF-27 y CA-UC08-01 a CA-UC08-04.

#### Scenario: Empty metrics

- **WHEN** un chatbot no tiene consultas en el periodo seleccionado
- **THEN** la interfaz muestra conteo cero y tiempo medio no disponible

### Requirement: The administration interface is accessible and responsive

El panel MUST mantener navegación, acciones y estados comprensibles en escritorio, tableta y móvil; los estados no pueden depender solo del color. Referencias: RNF-08, RNF-09 y RS-09.

#### Scenario: Processing state

- **WHEN** una operación administrativa está en curso
- **THEN** el control involucrado comunica visualmente que está procesando y evita acciones duplicadas
