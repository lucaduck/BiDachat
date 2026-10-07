# SRS.md — Software Requirements Specification

## BIDACHAT

**Documento:** Especificación de Requisitos de Software  
**Sistema:** BIDACHAT  
**Versión del documento:** 0.2
**Alcance:** Versión completa de la tesis
**Estado:** Aprobado por el usuario para la implementación de la versión completa el 2026-09-30

---

## 1. Propósito

Este documento define los requisitos de software de BIDACHAT de forma clara y verificable.

BIDACHAT es una aplicación web para la gestión y configuración de chatbots orientados a la interpretación de dashboards analíticos del grupo BI-DATA. Los chatbots utilizarán modelos de lenguaje y un mecanismo RAG multimodal para responder consultas en lenguaje natural utilizando información documental y, cuando corresponda, información visual proporcionada por el usuario.

Este SRS será la referencia para:

- desarrollo de la versión completa;
- diseño de casos de uso;
- definición de criterios de aceptación;
- planificación de pruebas;
- trazabilidad entre requisitos e implementación.

Los requisitos adicionales de la versión completa se incorporarán a este documento antes de su implementación para conservar la trazabilidad.

---

## 2. Alcance del sistema

### 2.1 Incluido en la versión completa

BIDACHAT deberá incluir:

- aplicación web de administración;
- autenticación y control de acceso;
- creación, consulta, edición y eliminación de chatbots;
- configuración del modelo de lenguaje de cada chatbot;
- configuración del comportamiento general del chatbot;
- asociación de fuentes de conocimiento;
- carga y procesamiento de documentos;
- generación y almacenamiento de representaciones vectoriales;
- recuperación semántica mediante RAG;
- procesamiento de consultas en lenguaje natural;
- procesamiento de imágenes o capturas proporcionadas por el usuario;
- generación de respuestas mediante el modelo de lenguaje configurado;
- integración del chatbot en dashboards;
- registro de consultas y tiempos de respuesta;
- consulta de métricas básicas.



---

## 3. Usuarios del sistema

### 3.1 Investigador / Administrador

Usuario autorizado del grupo BI-DATA que accede a la aplicación web de administración.

Podrá:

- iniciar y cerrar sesión;
- crear, consultar, editar y eliminar chatbots;
- configurar chatbots;
- asociar fuentes de conocimiento;
- cargar documentos;
- obtener el mecanismo de integración de un chatbot;
- consultar métricas de uso.

### 3.2 Usuario final del chatbot

Persona que utiliza un chatbot integrado en un dashboard.

Podrá:

- realizar preguntas en lenguaje natural;
- proporcionar una imagen o captura de pantalla cuando sea necesario;
- recibir respuestas relacionadas con indicadores, gráficos, tendencias y resultados del dashboard.

El usuario final no tendrá acceso a las funciones administrativas de BIDACHAT.

---

## 4. Convenciones de requisitos

Se utilizarán los siguientes identificadores:

| Prefijo | Significado |
|---|---|
| `RF` | Requisito funcional |
| `RNF` | Requisito no funcional |
| `RS` | Requisito de seguridad |
| `UC` | Caso de uso |
| `CA` | Criterio de aceptación |

### 4.1 Nota de normalización de identificadores

La fuente actual de Notion contiene una duplicación de los identificadores `RF-11` y `RF-12`.

Para evitar ambigüedad dentro de este SRS se adopta una numeración única. No se elimina ni se añade funcionalidad por esta corrección; únicamente se normalizan los identificadores.

La numeración utilizada en este documento es la siguiente:

- `RF-11`: configurar comportamiento, rol, tono y reglas del chatbot;
- `RF-12`: recibir y procesar imágenes o capturas;
- los requisitos documentales continúan desde `RF-13`;
- los requisitos posteriores se desplazan manteniendo su orden;
- las métricas finalizan en `RF-27`.

Esta normalización deberá reflejarse posteriormente en la fuente de Notion si se aprueba este SRS.

---

# 5. Requisitos funcionales

## 5.1 Autenticación y control de acceso

| ID | Requisito |
|---|---|
| **RF-01** | El sistema deberá permitir que un investigador autorizado inicie sesión en la aplicación web. |
| **RF-02** | El sistema deberá restringir las funciones administrativas a usuarios autorizados. |
| **RF-03** | El sistema deberá permitir al usuario autenticado cerrar su sesión. |

## 5.2 Gestión y configuración de chatbots

| ID | Requisito |
|---|---|
| **RF-04** | El sistema deberá permitir al investigador crear un chatbot. |
| **RF-05** | El sistema deberá permitir consultar los chatbots registrados. |
| **RF-06** | El sistema deberá permitir editar la configuración de un chatbot. |
| **RF-07** | El sistema deberá permitir eliminar un chatbot. |
| **RF-08** | El sistema deberá permitir seleccionar, para cada chatbot, el proveedor y modelo de lenguaje que utilizará, incluyendo proveedor externo u Ollama local entre las combinaciones admitidas. |
| **RF-09** | El sistema deberá permitir asociar y quitar fuentes de conocimiento de cada chatbot sin eliminar los archivos compartidos. Una fuente quitada dejará de recuperarse en las consultas de ese chatbot. |
| **RF-10** | El sistema deberá generar el mecanismo de integración necesario para incorporar un chatbot en un dashboard. |
| **RF-11** | El sistema deberá permitir definir instrucciones de comportamiento, rol, tono y reglas de respuesta del chatbot. |
| **RF-12** | El chatbot deberá poder recibir y procesar imágenes o capturas de pantalla proporcionadas por el usuario final, incluida una imagen pegada en el campo de pregunta desde el portapapeles, para responder consultas relacionadas con lo que observa en pantalla. |

## 5.3 Procesamiento documental y RAG

| ID | Requisito |
|---|---|
| **RF-13** | El sistema deberá permitir cargar documentos e imágenes PNG, JPEG o WebP como fuentes de conocimiento asociadas a un chatbot. El contenido visual se describirá antes de generar representaciones semánticas. |
| **RF-14** | El sistema deberá procesar los documentos cargados para generar las representaciones necesarias para su recuperación semántica. |
| **RF-15** | El sistema deberá almacenar las representaciones vectoriales generadas a partir de los documentos. |
| **RF-16** | El sistema deberá recuperar información relevante de las fuentes de conocimiento asociadas al chatbot a partir de la consulta del usuario. |
| **RF-17** | El sistema deberá mantener separadas las fuentes de conocimiento correspondientes a cada chatbot durante la recuperación de información. |

## 5.4 Consulta conversacional y procesamiento multimodal

| ID | Requisito |
|---|---|
| **RF-18** | El chatbot deberá permitir al usuario realizar consultas en lenguaje natural. |
| **RF-19** | El sistema deberá permitir incorporar información visual relacionada con el dashboard cuando la consulta lo requiera. |
| **RF-20** | El sistema deberá combinar la consulta del usuario, el contexto documental recuperado y la información visual disponible antes de generar la respuesta. |
| **RF-21** | El sistema deberá enviar el contexto obtenido al modelo de lenguaje configurado para el chatbot. |
| **RF-22** | El sistema deberá devolver al usuario la respuesta generada mediante la interfaz conversacional. |
| **RF-23** | El chatbot deberá poder ser utilizado desde el mecanismo de integración definido para el dashboard correspondiente. |

## 5.5 Métricas de uso

| ID | Requisito |
|---|---|
| **RF-24** | El sistema deberá registrar las consultas realizadas a cada chatbot. |
| **RF-25** | El sistema deberá registrar el tiempo de respuesta de las consultas. |
| **RF-26** | El sistema deberá asociar las métricas registradas con el chatbot correspondiente. |
| **RF-27** | El investigador deberá poder consultar las métricas de uso desde la aplicación web mediante gráficos de consultas, tiempos de respuesta y estados, filtrando por chatbot, periodo o fechas personalizadas y estado, con agrupación diaria, semanal o mensual. |

## 5.6 Personalización y vista previa del widget

| ID | Requisito |
|---|---|
| **RF-28** | El investigador deberá poder configurar y conservar el color principal, el icono y el mensaje de bienvenida del widget de cada chatbot. |
| **RF-29** | El investigador deberá poder revisar una vista previa del widget antes de copiar el mecanismo de integración. |
| **RF-30** | El widget deberá presentar las respuestas del asistente con párrafos, listas y énfasis legibles, sin mostrar los marcadores de formato como texto literal ni ejecutar contenido HTML recibido del modelo. |
| **RF-31** | El widget integrado podrá enviar con cada consulta el texto visible de una región de la página anfitriona indicada en el código de integración, para que el chatbot responda con el contexto actual del dashboard sin rastrear otras páginas. |

---

# 6. Requisitos no funcionales

| ID | Categoría | Requisito |
|---|---|---|
| **RNF-01** | Interoperabilidad | La comunicación del frontend y de los clientes externos con el backend deberá realizarse mediante la API REST sobre HTTP, sin WebSocket ni acceso directo a la base de datos, al motor RAG o al proveedor del LLM. |
| **RNF-02** | Interoperabilidad | El mecanismo de integración del chatbot deberá ser independiente de la tecnología utilizada por la aplicación web que contiene el dashboard. |
| **RNF-03** | Portabilidad | Los componentes necesarios para ejecutar la aplicación deberán poder desplegarse de forma reproducible mediante contenedores Docker. |
| **RNF-04** | Mantenibilidad | Los componentes principales deberán mantenerse desacoplados de acuerdo con la arquitectura SOA, evitando dependencias innecesarias entre frontend, backend, RAG, almacenamiento y LLM. |
| **RNF-05** | Mantenibilidad | La modificación del modelo de lenguaje configurado para un chatbot no deberá requerir cambios en el código del dashboard donde se encuentre integrado. |
| **RNF-06** | Rendimiento | El sistema deberá permitir medir el tiempo transcurrido desde la recepción de una consulta hasta la entrega de la respuesta. |
| **RNF-07** | Rendimiento | Los tiempos de respuesta deberán registrarse para permitir su posterior análisis durante las pruebas y evaluación del sistema. |
| **RNF-08** | Usabilidad | La interfaz conversacional deberá permitir que el usuario formule consultas en lenguaje natural sin requerir conocimientos de programación. |
| **RNF-09** | Usabilidad | La interfaz deberá proporcionar retroalimentación visual mientras una consulta se encuentre en procesamiento. |
| **RNF-10** | Adaptabilidad | La aplicación deberá permitir cambiar la configuración del modelo de lenguaje utilizado por un chatbot sin modificar el dashboard donde se encuentra integrado. |
| **RNF-11** | Adaptabilidad | El componente de inteligencia artificial deberá permitir ser evaluado mediante los criterios de adaptabilidad establecidos para el trabajo de titulación. |
| **RNF-12** | Usabilidad | El panel y el flujo de configuración deberán adaptarse a escritorio y móvil, mantener contraste legible y permitir navegación por teclado. |
| **RNF-13** | Usabilidad | Las rutas no encontradas deberán ofrecer una salida clara hacia el panel. |
| **RNF-14** | Despliegue | La aplicación contenedorizada deberá publicar panel, widget y API bajo un único origen mediante Nginx como proxy inverso; frontend y backend permanecerán en la red interna en producción. |
| **RNF-15** | Despliegue | El backend, PostgreSQL/pgvector, el almacenamiento documental y los servicios locales de RAG e inferencia deberán ejecutarse en infraestructura controlada por BI-DATA; no se utilizarán servicios externos de base de datos ni de backend. Las únicas integraciones externas de ejecución permitidas serán las API de proveedores de IA configurados. |

> **Nota:** `RNF-05` y `RNF-10` expresan condiciones muy similares desde categorías distintas. Se mantienen porque así constan actualmente en la fuente de requisitos. Su posible consolidación deberá aprobarse antes de eliminar cualquiera de los dos.

---

# 7. Requisitos de seguridad

| ID | Requisito |
|---|---|
| **RS-01** | La aplicación deberá requerir autenticación para acceder a las funciones del panel administrativo. |
| **RS-02** | La API deberá verificar la autorización del usuario antes de permitir operaciones administrativas sobre chatbots, documentos, configuraciones y métricas. |
| **RS-03** | Toda comunicación entre clientes, widget y backend deberá realizarse mediante HTTPS/TLS en los entornos de despliegue. |
| **RS-04** | Las credenciales privadas, claves de API, secretos de autenticación y datos de conexión deberán permanecer en el backend mediante variables de entorno o mecanismos equivalentes y no deberán incluirse en código fuente, repositorio, frontend ni widget público. |
| **RS-05** | La API deberá validar los datos recibidos antes de procesarlos o almacenarlos y rechazar entradas que no cumplan el formato esperado. |
| **RS-06** | La carga de documentos deberá validar los tipos de archivo y límites permitidos antes de incorporarlos al procesamiento RAG. |
| **RS-07** | El sistema deberá mantener aislamiento entre chatbots, de modo que una consulta solo pueda recuperar documentos, configuraciones y contexto asociados al chatbot correspondiente. |
| **RS-08** | Los endpoints públicos utilizados por los chatbots deberán incorporar mecanismos para limitar el uso abusivo o excesivo de solicitudes. |
| **RS-09** | Los errores enviados al cliente no deberán revelar claves, credenciales, cadenas de conexión, trazas internas ni información sensible de la infraestructura. |

---

# 8. Casos de uso y criterios de aceptación

Los siguientes casos de uso agrupan los requisitos funcionales en flujos comprensibles. No se crea un caso de uso por cada requisito para evitar fragmentar innecesariamente el comportamiento del sistema.

## UC-01 — Autenticar investigador

**Actor principal:** Investigador / Administrador

**Objetivo:** Permitir el acceso seguro al panel administrativo y el cierre de sesión.

**Precondiciones:**

- el investigador debe estar autorizado para utilizar BIDACHAT.

**Flujo principal:**

1. El investigador abre la pantalla de inicio de sesión.
2. Ingresa sus credenciales.
3. El sistema valida la información.
4. El sistema permite el acceso al panel administrativo.
5. El investigador puede cerrar sesión cuando lo requiera.
6. Al cerrar sesión, el sistema finaliza el acceso autenticado.

**Flujos alternativos:**

- Si las credenciales no son válidas, el sistema rechaza el acceso.
- Si un usuario no autenticado intenta acceder a una función administrativa, el sistema deniega el acceso.

**Requisitos relacionados:** `RF-01`, `RF-02`, `RF-03`, `RS-01`, `RS-02`.

### Criterios de aceptación

- **CA-UC01-01:** Dadas credenciales válidas de un investigador autorizado, cuando inicia sesión, entonces el sistema permite acceder al panel administrativo.
- **CA-UC01-02:** Dadas credenciales inválidas, cuando se intenta iniciar sesión, entonces el sistema deniega el acceso.
- **CA-UC01-03:** Dado un usuario no autenticado, cuando intenta acceder a una función administrativa, entonces el sistema deniega la operación.
- **CA-UC01-04:** Dado un investigador autenticado, cuando cierra sesión, entonces deja de tener acceso a las funciones administrativas protegidas.

## UC-02 — Gestionar chatbots

**Actor principal:** Investigador / Administrador

**Objetivo:** Crear, consultar, editar y eliminar chatbots.

**Precondiciones:**

- el investigador debe estar autenticado.

**Flujo principal:**

1. El investigador abre la sección de chatbots.
2. El sistema muestra los chatbots registrados.
3. El investigador puede crear un nuevo chatbot.
4. El investigador puede consultar su información.
5. El investigador puede modificar su configuración.
6. El investigador puede eliminarlo cuando sea necesario.

**Requisitos relacionados:** `RF-04`, `RF-05`, `RF-06`, `RF-07`.

### Criterios de aceptación

- **CA-UC02-01:** Cuando el investigador registra un chatbot con los datos requeridos, entonces el sistema lo almacena y lo muestra en la lista.
- **CA-UC02-02:** Cuando el investigador consulta la lista de chatbots, entonces el sistema muestra los chatbots registrados.
- **CA-UC02-03:** Cuando el investigador modifica un chatbot con datos válidos, entonces los cambios quedan almacenados.
- **CA-UC02-04:** Cuando el investigador elimina un chatbot y la operación finaliza correctamente, entonces este deja de aparecer como disponible en la gestión administrativa.

## UC-03 — Configurar chatbot

**Actor principal:** Investigador / Administrador

**Objetivo:** Definir la configuración necesaria para el comportamiento de un chatbot.

**Precondiciones:**

- el investigador debe estar autenticado;
- el chatbot debe existir.

**Flujo principal:**

1. El investigador selecciona un chatbot.
2. Selecciona primero el proveedor de IA y después uno de los modelos disponibles para ese proveedor.
3. Asocia las fuentes de conocimiento correspondientes.
4. Define las instrucciones de comportamiento, rol, tono y reglas de respuesta.
5. Guarda la configuración.
6. El sistema utiliza posteriormente dicha configuración al atender consultas.

**Requisitos relacionados:** `RF-08`, `RF-09`, `RF-11`, `RF-28`, `RF-29`, `RNF-05`, `RNF-10`, `RNF-12`.

### Criterios de aceptación

- **CA-UC03-01:** Cuando el investigador selecciona un proveedor de IA, el formulario muestra solo sus modelos; al elegir un modelo válido y guardar, el chatbot queda asociado a ese modelo. Al cambiar de proveedor, debe elegir un nuevo modelo antes de guardar.
- **CA-UC03-02:** Cuando el investigador asocia fuentes de conocimiento y guarda los cambios, entonces estas quedan vinculadas al chatbot correspondiente.
- **CA-UC03-07:** Cuando el investigador quita una fuente del chatbot, esta deja de formar parte de su recuperación RAG y permanece disponible para volver a asociarla.
- **CA-UC03-03:** Cuando el investigador define instrucciones de comportamiento y guarda la configuración, entonces estas quedan disponibles para el procesamiento de las consultas.
- **CA-UC03-04:** Cuando se modifica la configuración del modelo de lenguaje del chatbot, entonces no es necesario modificar el código del dashboard donde está integrado.
- **CA-UC03-05:** Cuando el investigador guarda la apariencia y el saludo, entonces se conservan con el chatbot y se muestran al volver a editarlo.
- **CA-UC03-06:** Cuando el investigador abre la vista previa, entonces ve el color, icono y saludo configurados antes de publicar el widget.
- **CA-UC03-08:** El investigador puede seleccionar propuestas de colores e iconos o usar un color personalizado; la selección se refleja en la vista previa y se conserva al guardar (RF-28).

## UC-04 — Gestionar documentos y conocimiento RAG

**Actor principal:** Investigador / Administrador

**Objetivo:** Incorporar documentos a la base de conocimiento de un chatbot y permitir su recuperación semántica.

**Precondiciones:**

- el investigador debe estar autenticado;
- el chatbot debe existir.

**Flujo principal:**

1. El investigador selecciona un chatbot.
2. Carga un documento permitido.
3. El sistema valida el archivo.
4. El sistema procesa el documento.
5. El sistema genera las representaciones necesarias para búsqueda semántica.
6. El sistema almacena las representaciones vectoriales.
7. Ante una consulta, el sistema recupera información relacionada únicamente con el chatbot correspondiente.

**Flujos alternativos:**

- Si el archivo no cumple las restricciones establecidas, el sistema rechaza la carga.
- Si la consulta pertenece a otro chatbot, el sistema no debe recuperar información de una base de conocimiento ajena.

**Requisitos relacionados:** `RF-13`, `RF-14`, `RF-15`, `RF-16`, `RF-17`, `RS-05`, `RS-06`, `RS-07`.

### Criterios de aceptación

- **CA-UC04-01:** Cuando el investigador carga un documento permitido, entonces el sistema lo acepta para procesamiento.
- **CA-UC04-06:** Cuando el investigador carga una imagen PNG, JPEG o WebP permitida, el sistema genera una descripción textual con el modelo visual local antes de crear sus embeddings.
- **CA-UC04-02:** Cuando un archivo no cumple el tipo o límites permitidos, entonces el sistema rechaza su incorporación al RAG.
- **CA-UC04-03:** Después de procesar correctamente un documento, entonces sus representaciones quedan disponibles para recuperación semántica.
- **CA-UC04-04:** Dado contenido conocido dentro de una fuente asociada, cuando se realiza una consulta relacionada, entonces el sistema puede recuperar contexto procedente de esa fuente.
- **CA-UC04-05:** Cuando se realiza una consulta a un chatbot, entonces la recuperación no utiliza documentos asociados exclusivamente a otro chatbot.

## UC-05 — Integrar chatbot en un dashboard

**Actor principal:** Investigador / Administrador

**Objetivo:** Obtener el mecanismo necesario para utilizar un chatbot desde un dashboard.

**Precondiciones:**

- el investigador debe estar autenticado;
- el chatbot debe existir y tener una configuración válida.

**Flujo principal:**

1. El investigador selecciona un chatbot.
2. Solicita su mecanismo de integración.
3. El sistema proporciona la información necesaria para incorporarlo en el dashboard.
4. El dashboard carga el chatbot.
5. El chatbot se comunica con BIDACHAT mediante la API.

**Requisitos relacionados:** `RF-10`, `RF-23`, `RNF-01`, `RNF-02`.

### Criterios de aceptación

- **CA-UC05-01:** Cuando el investigador solicita la integración de un chatbot, entonces el sistema proporciona el mecanismo definido para incorporarlo en un dashboard.
- **CA-UC05-02:** Cuando el chatbot está integrado correctamente, entonces el usuario puede abrirlo y realizar consultas desde el dashboard.
- **CA-UC05-03:** El widget o cliente integrado deberá comunicarse con el backend mediante la API y no directamente con la base de datos, el RAG o el proveedor del LLM.
- **CA-UC05-04:** La configuración interna del chatbot podrá cambiar sin requerir modificaciones en el código del dashboard.

## UC-06 — Realizar una consulta conversacional

**Actor principal:** Usuario final del chatbot

**Objetivo:** Obtener una respuesta en lenguaje natural utilizando el contexto del chatbot.

**Precondiciones:**

- el chatbot debe estar disponible;
- el chatbot debe tener una configuración válida.

**Flujo principal:**

1. El usuario abre el chatbot.
2. Escribe una pregunta en lenguaje natural.
3. El sistema identifica el chatbot y su configuración.
4. El sistema recupera contexto de las fuentes de conocimiento correspondientes.
5. Si el sitio anfitrión configuró una región de contexto, el widget añade el texto visible actual de esa región; el sistema lo trata como datos no confiables y construye el contexto para el modelo de lenguaje.
6. El sistema envía la información al modelo configurado.
7. El modelo genera una respuesta.
8. El sistema muestra la respuesta al usuario.
9. El sistema registra la consulta y su tiempo de respuesta.

**Requisitos relacionados:** `RF-16`, `RF-18`, `RF-20`, `RF-21`, `RF-22`, `RF-24`, `RF-25`, `RF-26`, `RF-31`, `RNF-06`, `RNF-07`, `RNF-08`, `RNF-09`.

### Criterios de aceptación

- **CA-UC06-01:** Cuando el usuario envía una pregunta en lenguaje natural, entonces el sistema acepta la consulta sin exigir conocimientos de programación.
- **CA-UC06-02:** Mientras la consulta está siendo procesada, entonces la interfaz muestra retroalimentación visual.
- **CA-UC06-03:** Cuando existe contexto documental relacionado, entonces este se incorpora al contexto utilizado para generar la respuesta.
- **CA-UC06-04:** Cuando el modelo genera una respuesta correctamente, entonces esta se muestra en la interfaz conversacional.
- **CA-UC06-05:** Después de procesar la consulta, entonces el sistema registra la consulta y el tiempo de respuesta asociados al chatbot.
- **CA-UC06-06:** Cuando la respuesta incluye listas o énfasis, el widget los presenta con formato legible en ambos temas; el contenido HTML del modelo se muestra como texto y no se ejecuta.
- **CA-UC06-07:** Cuando el script declara una región de contexto, cada pregunta incluye hasta 6000 caracteres de texto visible actualizado de esa región, sin HTML, formularios ni contenido marcado para excluir; el backend lo distingue del contexto RAG. Si la región no existe o el selector es inválido, la consulta continúa sin contexto de página.

## UC-07 — Realizar una consulta multimodal con imagen

**Actor principal:** Usuario final del chatbot

**Objetivo:** Resolver una consulta utilizando una imagen o captura de pantalla del dashboard junto con el contexto documental disponible.

**Precondiciones:**

- el chatbot debe estar disponible;
- el usuario debe proporcionar una imagen o captura cuando la consulta dependa de información visual.

**Flujo principal:**

1. El usuario abre el chatbot.
2. Proporciona una imagen o captura de pantalla.
3. Formula una pregunta relacionada con la imagen.
4. El sistema procesa la información visual.
5. El sistema recupera contexto documental cuando corresponda.
6. El sistema combina la consulta, la información documental y la información visual disponible.
7. El sistema envía el contexto al modelo configurado.
8. El sistema devuelve la respuesta al usuario.
9. El sistema registra la consulta y el tiempo de respuesta.

**Requisitos relacionados:** `RF-12`, `RF-16`, `RF-18`, `RF-19`, `RF-20`, `RF-21`, `RF-22`, `RF-24`, `RF-25`.

### Criterios de aceptación

- **CA-UC07-01:** Cuando el usuario proporciona una imagen admitida junto con una pregunta, entonces el sistema acepta ambos elementos para procesamiento.
- **CA-UC07-06:** Cuando el usuario pega una imagen en el campo de pregunta, el widget la muestra como adjunto revisable y permite quitarla antes de enviar la consulta.
- **CA-UC07-02:** Cuando la consulta depende de información visual, entonces el sistema incorpora esa información al contexto enviado al modelo.
- **CA-UC07-03:** Cuando también existe información documental relacionada, entonces el sistema puede combinar el contexto documental con la información visual disponible.
- **CA-UC07-04:** Cuando el procesamiento finaliza correctamente, entonces la respuesta se muestra en la interfaz conversacional.
- **CA-UC07-05:** El procesamiento de una consulta multimodal deberá registrar su tiempo de respuesta.

## UC-08 — Consultar métricas de uso

**Actor principal:** Investigador / Administrador

**Objetivo:** Consultar las métricas básicas registradas por BIDACHAT.

**Precondiciones:**

- el investigador debe estar autenticado;
- deben existir métricas registradas para mostrarlas.

**Flujo principal:**

1. El investigador abre la sección de métricas.
2. El sistema obtiene las métricas registradas.
3. El sistema las relaciona con el chatbot correspondiente.
4. El sistema muestra al menos la información de uso y tiempos de respuesta disponible.

**Requisitos relacionados:** `RF-24`, `RF-25`, `RF-26`, `RF-27`, `RNF-06`, `RNF-07`.

### Criterios de aceptación

- **CA-UC08-01:** Cuando existen consultas registradas, entonces el investigador puede consultar las métricas desde la aplicación web.
- **CA-UC08-02:** Las métricas mostradas deben estar asociadas al chatbot correspondiente.
- **CA-UC08-03:** El sistema deberá permitir consultar los tiempos de respuesta registrados.
- **CA-UC08-04:** Un usuario no autorizado no deberá acceder a las métricas administrativas.
- **CA-UC08-05:** Los gráficos y totales deben usar los mismos registros y filtros; se pueden consultar periodos de 7, 30 o 90 días, historial completo o fechas personalizadas inclusivas en UTC.
- **CA-UC08-06:** Las agrupaciones diaria, semanal y mensual muestran periodos sin consultas como cero y tiempos sin medición como no disponibles; los filtros se conservan en la URL.
- **CA-UC08-07:** La interfaz permite recuperar fallos de carga, informa rangos inválidos y ofrece una tabla accesible con los valores de los gráficos.

---

# 9. Trazabilidad de casos de uso

| Caso de uso | Requisitos funcionales principales |
|---|---|
| **UC-01** Autenticar investigador | RF-01, RF-02, RF-03 |
| **UC-02** Gestionar chatbots | RF-04, RF-05, RF-06, RF-07 |
| **UC-03** Configurar chatbot | RF-08, RF-09, RF-11 |
| **UC-04** Gestionar documentos y RAG | RF-13, RF-14, RF-15, RF-16, RF-17 |
| **UC-05** Integrar chatbot | RF-10, RF-23 |
| **UC-06** Consulta conversacional | RF-16, RF-18, RF-20, RF-21, RF-22, RF-24, RF-25, RF-26, RF-31 |
| **UC-07** Consulta multimodal | RF-12, RF-16, RF-18, RF-19, RF-20, RF-21, RF-22, RF-24, RF-25 |
| **UC-08** Consultar métricas | RF-24, RF-25, RF-26, RF-27 |

---

# 10. Criterio general de aceptación de la versión completa

La versión completa de BIDACHAT se considerará funcional cuando sea posible completar de extremo a extremo el siguiente flujo:

```text
Investigador inicia sesión
        |
        v
Crea y configura un chatbot
        |
        v
Asocia y carga documentos
        |
        v
El sistema procesa el conocimiento
        |
        v
El chatbot se integra en un dashboard
        |
        v
Usuario realiza una consulta
        |
        +----------------------+
        |                      |
        v                      v
   Consulta textual       Consulta + imagen
        |                      |
        +----------+-----------+
                   |
                   v
            Recuperación RAG
                   |
                   v
           Modelo de lenguaje
                   |
                   v
             Respuesta final
                   |
                   v
          Registro de métricas
```

Además:

- el acceso administrativo debe estar protegido;
- las fuentes de conocimiento de diferentes chatbots deben mantenerse aisladas;
- los secretos deben permanecer en el backend;
- el usuario debe recibir retroalimentación mientras una consulta se procesa;
- los tiempos de respuesta deben quedar registrados;
- la aplicación deberá poder ejecutarse de forma reproducible mediante Docker.

---

# 11. Observaciones pendientes de aprobación

1. **Normalización de RF:** este SRS corrige la duplicación actual de `RF-11` y `RF-12` mediante renumeración única.
2. **RNF-05 y RNF-10:** se mantienen separados aunque actualmente son similares.
3. **Criterios de aceptación:** los criterios `CA-*` fueron derivados de los requisitos existentes para volverlos verificables. La fuente de Notion establece que las historias de usuario deben tener criterios de aceptación, pero no contiene todavía estos criterios detallados.
4. **Umbrales de rendimiento:** no se establece un tiempo máximo de respuesta porque la fuente actual no define un valor cuantitativo aprobado.
5. **Alcance de la versión completa:** las funcionalidades adicionales aprobadas deberán documentarse en una revisión posterior de este SRS.

---

## Estado del documento

Este documento representa la línea base de especificación para la **versión completa** de BIDACHAT. Cada nuevo requisito aprobado deberá añadirse aquí antes de implementarse.


## Criterios de interfaz autorizados — 5 de octubre de 2026

La solicitud «ejecutalo» autoriza el cambio `professionalize-frontend-experience`.
Estos criterios amplían la aceptación de RF-01 a RF-10, RF-24 a RF-29 y RNF de
usabilidad; no añaden otro sistema de analítica ni alteran la arquitectura:

- UI-01: La navegación muestra sección, chatbot y paso actual y admite acceso directo, recarga y historial.
- UI-02: El retorno desde vista previa conserva el editor y la sesión vigente; una reautenticación mantiene un destino interno válido.
- UI-03: Los borradores requieren confirmación antes de descartarse; las rutas inválidas o eliminadas ofrecen una recuperación válida.
- UI-04: Ambos temas comparten componentes, estados legibles, foco visible y preferencia persistente; navegación y formularios se adaptan a móvil.
- UI-05: El resumen compara consultas por chatbot y resultados mediante agregados reales del mismo periodo; no genera series inexistentes.
- UI-06: La vista visual reutiliza el widget real, distingue apariencia de prueba conversacional y conserva fuentes compartidas al quitar una asociación.
- UI-07: Enlaces, recursos y script generado se verifican mediante recorridos de navegador e integración externa independiente, incluyendo errores y permisos denegados.

La especificación detallada, escenarios y matriz L01–L18 se conservan en
`openspec/changes/professionalize-frontend-experience/`.

### Identidad del panel — 6 de octubre de 2026

El usuario aprobó el panel de referencia y el logo
`docs/brand/Logotipo BC de Circuito Futurista.png` para la identidad administrativa.
El panel incorpora la marca desvanecida del lateral, el lema «Datos que conversan»
y el bloque institucional BI-DATA, adaptados a los temas claro y oscuro.
El listado presenta la actividad acumulada mediante métricas existentes y un
acceso funcional para crear chatbots; los valores de la maqueta no son datos del sistema.

**Identidad por tema — 6 de octubre de 2026:** El panel usa «Logotipo BC de Circuitos Tecnológicos.png» en modo claro y «Logotipo BC de Circuito Futurista.png» en modo oscuro, incluidos sus usos en la marca BIDACHAT y el bloque BI-DATA. El lema «Datos que conversan» conserva el estilo manuscrito, inclinado, de dos líneas y con subrayado turquesa de la referencia aportada.

**Identidad del acceso — 7 de octubre de 2026:** La pantalla de inicio de sesión cambia el logo con el tema. En modo oscuro utiliza `docs/brand/logotipo-autenticacion-blanco.png`; en modo claro conserva su variante para fondo claro.
