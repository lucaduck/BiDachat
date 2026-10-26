## Purpose

Definir el contrato de centralización de generación externa para conservar la selección de modelos, el contexto y la privacidad de BIDACHAT durante la migración a un gateway privado.

## ADDED Requirements

### Requirement: Explicit external routing
El sistema SHALL enviar toda generación externa de los proveedores migrados por el gateway privado, incluyendo chat y descripción visual, sin sustituir proveedor ni modelo silenciosamente.

#### Scenario: External chat and source description
- **WHEN** un chatbot o el perfil visual usa un proveedor migrado
- **THEN** la solicitud pasa por el gateway con el modelo configurado y sin llamada directa alternativa desde el backend.

#### Scenario: Gateway failure
- **WHEN** el gateway no está disponible
- **THEN** se devuelve un error seguro y se registra el fallo sin reintentos ni fallback automático a otro destino.

### Requirement: Compatible model selection and responses
El sistema SHALL conservar IDs de modelos, configuración de chatbots, instrucciones, memoria, contexto RAG y tratamiento de imágenes; SHALL mantener las opciones de privacidad y la identificación verificable del proveedor/modelo ejecutado.

#### Scenario: Same model name across providers
- **WHEN** Gemini y Vertex ofrecen el mismo identificador de modelo
- **THEN** cada selección resuelve exclusivamente al proveedor elegido y conserva su asociación histórica en métricas.

#### Scenario: OpenAI response compatibility
- **WHEN** se migra un modelo OpenAI
- **THEN** se verifica soporte equivalente de Responses, `store:false`, instrucciones e imágenes antes de habilitar la ruta nueva.

#### Scenario: Incomplete response
- **WHEN** el proveedor devuelve respuesta vacía, bloqueada, incompleta o con identidad inesperada
- **THEN** no se presenta como respuesta completada y no se filtra el cuerpo interno del error.

### Requirement: Local inference and embedding independence
El sistema SHALL conservar rutas directas de Ollama y embeddings, sin cambiar modelo, dimensiones ni representaciones almacenadas.

#### Scenario: Local only installation
- **WHEN** solo se configuran modelos locales y no se levanta el gateway
- **THEN** la aplicación procesa consultas locales sin credenciales externas ni archivo Google.

#### Scenario: Gateway offline with existing documents
- **WHEN** el gateway se detiene y un chatbot usa Ollama
- **THEN** el chatbot recupera sus fuentes y responde por la ruta local, conservando los vectores existentes.

### Requirement: Private credentials and truthful configuration
El sistema SHALL mantener secretos fuera del cliente y los registros, permitir proveedores externos independientes de Vertex y distinguir configuración de conectividad verificada.

#### Scenario: OpenAI without Vertex
- **WHEN** solo OpenAI está habilitado como proveedor externo
- **THEN** el gateway arranca sin proyecto, región ni JSON Google y el panel ofrece sus modelos configurados sin exponer claves.

#### Scenario: Logs and endpoint exposure
- **WHEN** ocurre una petición exitosa o fallida
- **THEN** no se registran credenciales ni contenido conversacional; el puerto del gateway no es público y solo se aceptan solicitudes autenticadas del backend.

### Requirement: Evidence and reversible transition
La aceptación SHALL distinguir pruebas simuladas y reales por proveedor/capacidad y mantener un procedimiento de reversión que preserve datos.

#### Scenario: Missing provider credentials
- **WHEN** faltan credenciales o presupuesto para validar un proveedor
- **THEN** su aceptación real queda pendiente explícita, sin declararlo verificado por mocks.

#### Scenario: Rollback
- **WHEN** se revierte una migración fallida mediante configuración o versión anterior
- **THEN** los chatbots, conversaciones, métricas y embeddings existentes permanecen disponibles sin regeneración ni borrado.
