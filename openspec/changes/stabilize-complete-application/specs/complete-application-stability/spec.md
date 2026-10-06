## Purpose

Establecer la aceptación observable de los flujos existentes de BIDACHAT al cerrar deuda técnica, manteniendo la trazabilidad al SRS y diferenciando resultados reales de simulaciones y verificaciones pendientes.

Este delta representa requisitos ya aprobados; no incorpora nuevas funciones al SRS.

## ADDED Requirements

### Requirement: Preserve authenticated administration and integration

El sistema SHALL conservar autenticación, autorización administrativa, navegación, configuración persistente e integración del widget después de actualizar dependencias (RF-01–03, RF-04–11, RF-23, RF-28–29, RS-01–04, UI-01–07).

#### Scenario: Existing chatbot after update
- **WHEN** un usuario autorizado abre un chatbot existente tras desplegar la actualización
- **THEN** sus valores guardados, fuentes, vista previa y mecanismo de integración permanecen utilizables y el retorno conserva el editor seleccionado

#### Scenario: Unauthorized administrative request
- **WHEN** un cliente sin sesión válida solicita datos o modifica recursos administrativos
- **THEN** la API rechaza la operación sin revelar información privada

### Requirement: Deliver valid conversational output or a safe failure

El sistema SHALL mostrar contenido final utilizable de los modelos admitidos o un error recuperable sin exponer secretos, registrar el resultado en el chatbot correspondiente y preservar la entrada al fallar (RF-08, RF-12, RF-18–26, RNF-06–09, RS-09; CA-UC06-02/04/05, CA-UC07-04/05).

#### Scenario: Supported visual model
- **WHEN** se envía una imagen con valores legibles y una pregunta al modelo visual admitido
- **THEN** el widget muestra una respuesta relacionada con esos valores y la consulta registra su modelo ejecutado, resultado y tiempo

#### Scenario: Empty final response or provider unavailable
- **WHEN** el proveedor devuelve contenido final vacío, un tiempo de espera agotado o un error
- **THEN** el sistema informa el fallo de forma segura, mantiene la pregunta y adjunto recuperables y registra la consulta como fallida sin duplicarla mediante reintentos ocultos

### Requirement: Recover allowed knowledge sources with chatbot isolation

El sistema SHALL procesar fuentes admitidas, describir imágenes antes de sus representaciones semánticas, recuperar únicamente fuentes asociadas y conservar las fuentes compartidas al quitar una asociación (RF-09, RF-13–17; RS-05–07; CA-UC04-01–06).

#### Scenario: Real document or image source
- **WHEN** se carga una fuente permitida con contenido conocido y termina su procesamiento
- **THEN** una consulta al chatbot asociado puede recuperar contenido de esa fuente; una imagen se describe antes de generar sus representaciones

#### Scenario: Remove one shared association
- **WHEN** una fuente compartida se quita del contexto de un chatbot A y sigue asociada a B
- **THEN** A deja de recuperar esa fuente y B conserva su acceso sin eliminación del archivo compartido

#### Scenario: Invalid source or interrupted processing
- **WHEN** la fuente no cumple los límites o falla su procesamiento
- **THEN** se informa rechazo o fallo sin publicar representaciones incompletas como disponibles para recuperación

### Requirement: Keep metrics accurate through reliability changes

El sistema SHALL conservar conteos y tiempos asociados al chatbot y al periodo consultado sin fabricar series ni promedios sin muestras (RF-24–27; RNF-06–07; UI-05).

#### Scenario: Mixed query outcomes
- **WHEN** el periodo contiene consultas completadas y fallidas de varios chatbots
- **THEN** Resumen y Métricas muestran los agregados correspondientes sin mezclar periodos ni datos ajenos

### Requirement: Preserve usable navigation and visual input controls

El sistema SHALL conservar navegación por teclado, reflujo, estados legibles en ambos temas y control humano sobre los adjuntos y la captura (RF-12, RF-28–29; RNF-12–13; UI-01–07).

#### Scenario: Manual accessibility acceptance
- **WHEN** una persona recorre acceso, editor, publicación y widget con lector de pantalla y zoom nativo 200 %
- **THEN** puede identificar controles, ubicación y errores, completar las acciones y alcanzar el contenido sin que controles esenciales se superpongan u oculten

#### Scenario: Native capture cancellation
- **WHEN** la persona cancela el selector nativo de captura
- **THEN** no se añade un adjunto nuevo, se conserva la entrada previa y el usuario puede continuar la conversación

### Requirement: Maintain secure reproducible deployment

El sistema SHALL ejecutarse mediante contenedores reproducibles, mantener credenciales en el backend y usar HTTPS/TLS en despliegue publicado (RNF-01–04; RS-03–04, RS-08–09).

#### Scenario: Published deployment
- **WHEN** se verifica el panel, la API y el widget en el destino de publicación definido
- **THEN** utilizan HTTPS/TLS sin contenido activo mixto, respetan los orígenes configurados y no incluyen claves privadas en recursos públicos

#### Scenario: Rebuilt local environment
- **WHEN** se reconstruyen los contenedores con las versiones documentadas y datos de prueba aislados
- **THEN** puede completarse acceso, creación, carga, recuperación, conversación externa y consulta de métricas sin acceso directo del cliente a datos o proveedores
