## Purpose

Definir una experiencia de BIDACHAT coherente, accesible y verificable, en la que navegación, estado visual y acciones correspondan a funciones reales de la aplicación completa. Esta propuesta detalla criterios de los requisitos existentes; debe conciliarse con el SRS antes de implementar.

## ADDED Requirements

### Requirement: Navigation reflects the current task

El sistema SHALL mantener concordancia entre URL, sección activa, título y ruta de navegación, incluyendo el chatbot y paso cuando se está editando. Los enlaces ya compartidos SHALL seguir abriendo su destino o una recuperación explícita. Trazabilidad: RF-05, RF-06, RNF-12; petición del usuario de orientación y enlaces funcionales.

#### Scenario: Navigate between administrative sections

- **WHEN** el investigador navega desde Chatbots hacia Configuración
- **THEN** la URL, el menú y el breadcrumb identifican Configuración y refrescar mantiene esa sección

#### Scenario: Restore history within the editor

- **WHEN** se usa atrás o adelante entre dos chatbots o pasos de edición guardados en el historial
- **THEN** el formulario muestra el chatbot y paso del destino, sin conservar datos de otro editor

#### Scenario: Close the editor

- **WHEN** el investigador cierra el editor
- **THEN** vuelve al listado de Chatbots y refrescar mantiene el listado

### Requirement: Missing resources have an explicit recovery

El sistema SHALL distinguir una ruta desconocida, parámetros inválidos y un chatbot inexistente, ofreciendo una salida válida en cada caso. Un identificador ausente en los datos SHALL NOT interpretarse como autorización implícita para crear un chatbot. Trazabilidad: RF-04, RF-05, RNF-13.

#### Scenario: Deleted chatbot link

- **WHEN** se abre un enlace de edición de un chatbot eliminado
- **THEN** se informa que no está disponible y se ofrece volver al listado sin abrir el formulario de creación

#### Scenario: Invalid destination

- **WHEN** una URL contiene un paso no admitido o una ruta inexistente
- **THEN** el sistema recupera un destino válido explicado o muestra la página de no encontrado con salida al panel

### Requirement: Session and preview preserve the intended destination

El sistema SHALL restaurar una sesión todavía válida antes de decidir mostrar el acceso y SHALL conservar un destino interno validado cuando sea necesaria reautenticación. La vista previa SHALL permitir volver al mismo chatbot y al paso de origen cuando esté especificado. Trazabilidad: RF-01, RF-02, RF-29, CA-UC03-06.

#### Scenario: Return with valid session

- **WHEN** el investigador abre una prueba desde el editor y vuelve con una sesión vigente
- **THEN** ve ese chatbot y su paso de origen sin ser enviado innecesariamente al login

#### Scenario: Expired session

- **WHEN** la sesión ha vencido al intentar acceder a un editor
- **THEN** se solicita autenticación y, tras autenticar, se recupera el destino interno si el recurso sigue disponible

### Requirement: Unsaved edits are not silently discarded

El sistema SHALL avisar antes de abandonar un editor con cambios sin guardar y SHALL conservar los campos ante fallos de validación o guardado. Trazabilidad: RF-06, RF-11, RF-28 y RNF-12, como criterio de calidad propuesto.

#### Scenario: Cancel navigation away from a draft

- **WHEN** se cancela la salida del editor tras el aviso de cambios pendientes
- **THEN** se conserva el borrador y el usuario continúa en la misma tarea

#### Scenario: Save fails

- **WHEN** falla el guardado de configuración
- **THEN** se informa el fallo, no se muestra confirmación de éxito y se conserva lo introducido para corregir o reintentar

### Requirement: Themes preserve readability and behavior

El sistema SHALL ofrecer modo claro y oscuro con iguales funciones y jerarquía, preferencia conservada y estados legibles. El color SHALL acompañarse de texto o significado accesible para errores y estados. Trazabilidad: RNF-12 y solicitudes del usuario sobre modo claro y oscuro.

#### Scenario: Change and restore theme

- **WHEN** se cambia el tema y se recarga la aplicación
- **THEN** se mantiene la preferencia y todos los controles siguen identificables y operables

#### Scenario: Failure state in both themes

- **WHEN** se muestra un error de procesamiento en cualquiera de los temas
- **THEN** su texto, foco y acción de recuperación son legibles y el estado no depende únicamente de su color

### Requirement: Keyboard and small-screen operation remain complete

El sistema SHALL permitir los recorridos principales mediante teclado, mostrar foco visible, asociar etiquetas/errores a campos y adaptar contenido a móvil sin ocultar acciones esenciales. Trazabilidad: RNF-12. Los contrastes y objetivos de interacción se evaluarán conforme a los criterios WCAG 2.2 adoptados en el plan, sin declarar conformidad antes de auditar.

#### Scenario: Mobile menu interaction

- **WHEN** se abre el menú móvil, se navega con teclado y se cierra con Escape
- **THEN** el foco es coherente, vuelve al activador y el fondo no recibe interacción mientras el menú actúa como superposición

#### Scenario: Narrow viewport and long content

- **WHEN** se muestra un nombre de archivo largo o un script en una pantalla estrecha
- **THEN** el contenido se ajusta o desplaza dentro de su área y no oculta las acciones ni ensancha toda la página

### Requirement: Source management communicates scope and processing

El sistema SHALL distinguir cargar, asociar y quitar del contexto; mostrar el estado real de cada fuente y ofrecer recuperación de fallos. Quitar una asociación SHALL conservar la fuente compartida. Trazabilidad: RF-09, RF-13, RF-14, RF-17, CA-UC03-07.

#### Scenario: Remove a source from context

- **WHEN** el investigador quita una fuente asociada al chatbot
- **THEN** deja de figurar en su contexto y permanece disponible para asociarse nuevamente

#### Scenario: Invalid or failed upload

- **WHEN** el archivo no se admite o su procesamiento falla
- **THEN** se comunica la causa útil y una acción posible sin presentar la fuente como lista

### Requirement: Widget appearance and real capabilities are distinguishable

El sistema SHALL conservar la apariencia configurada en la vista visual y la conversación real, identificando cualquier simulación. Adjuntar, pegar, capturar y quitar imágenes SHALL producir estados revisables y recuperables. Trazabilidad: RF-12, RF-18, RF-19, RF-28, RF-29, RNF-09, CA-UC07-06.

#### Scenario: Compare configured appearance

- **WHEN** se guarda icono, color y saludo y se abre la prueba
- **THEN** el widget real coincide con lo configurado y no declara disponibilidad del proveedor sin evidencia

#### Scenario: Paste then remove an image

- **WHEN** se pega una imagen admitida en el campo de pregunta y se quita antes de enviar
- **THEN** la imagen se muestra primero como adjunto revisable y no se incluye en la consulta posterior

#### Scenario: Capture unavailable

- **WHEN** el navegador no admite captura o el usuario cancela su permiso
- **THEN** no se envía una imagen accidentalmente y permanece disponible la opción de adjuntar

### Requirement: Integration uses working resources and truthful settings

El sistema SHALL generar un script que cargue el chatbot seleccionado en un sitio externo autorizado y SHALL distinguir información consultable de ajustes editables. Trazabilidad: RF-10, RF-23, RNF-01, RNF-02, CA-UC05-01, CA-UC05-03.

#### Scenario: Independent host integration

- **WHEN** se copia el script y se inserta en otro sitio HTTP(S) autorizado
- **THEN** carga el recurso JavaScript, muestra el chatbot correcto y se comunica con la API sin dependencias del frontend anfitrión

#### Scenario: Clipboard denied or origin rejected

- **WHEN** el navegador impide copiar o el servidor rechaza un origen
- **THEN** se informa el problema con recuperación pertinente y no se comunica éxito falso

#### Scenario: Read-only configuration

- **WHEN** la API solo permite consultar los orígenes configurados
- **THEN** la pantalla los presenta como información y no ofrece controles de agregar o quitar sin una operación real

### Requirement: Metrics describe real measurements

El sistema SHALL mostrar métricas con periodo, unidad y estados correctos. Gráficos SHALL derivarse de mediciones disponibles; ausencia de muestras SHALL distinguirse de valor cero. Trazabilidad: RF-24 a RF-27 y RNF-06/RNF-07.

#### Scenario: No completed measurements

- **WHEN** no hay respuestas completadas con duración medible
- **THEN** el tiempo de respuesta se presenta como sin datos, no como 0 ms

#### Scenario: Aggregate comparison

- **WHEN** se muestran barras por chatbot o resultados de consultas
- **THEN** los valores corresponden al mismo periodo y a los estados devueltos por la API, sin inventar series temporales

### Requirement: Release evidence covers destinations and critical actions

Cada entrega SHALL registrar resultados de los destinos y acciones de su matriz de aceptación. Un HTTP 200 que muestra una pantalla equivocada SHALL contar como fallo funcional. Trazabilidad: RNF-12, RNF-13 y la solicitud de enlaces sin fallos.

#### Scenario: Incorrect page behind a successful response

- **WHEN** un enlace de editor responde 200 pero muestra otro chatbot o un acceso innecesario
- **THEN** la revisión lo marca fallido y bloquea la aceptación de ese recorrido

#### Scenario: Verification is incomplete

- **WHEN** un caso obligatorio no se ha ejecutado o no tiene evidencia
- **THEN** figura como pendiente y la entrega no afirma que todos los enlaces o recorridos están verificados
