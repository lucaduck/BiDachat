## ADDED Requirements

### Requirement: Send selected live page text with a widget question

El widget SHALL enviar con cada pregunta hasta 6000 caracteres de texto visible de la región indicada por `data-context-selector`, sin HTML ni valores de formularios (RF-31; CA-UC06-07).

#### Scenario: Dashboard changes after loading
- **WHEN** el contenido visible de la región cambia y el usuario envía otra pregunta
- **THEN** la consulta incluye el texto actualizado, no una copia tomada al cargar el script

#### Scenario: Excluded or missing content
- **WHEN** hay controles, formularios, elementos ocultos o `data-bidachat-ignore`, o el selector no encuentra la región
- **THEN** esos contenidos no se envían y la consulta sigue funcionando

### Requirement: Treat page context as separate untrusted input

La API SHALL aceptar `page_context` opcional, aplicar su límite y enviarlo al modelo separado de las fuentes RAG, sin persistirlo como fuente de conocimiento (RF-31; CA-UC06-07).

#### Scenario: Page text and chatbot documents
- **WHEN** una consulta tiene ambos tipos de contexto
- **THEN** el prompt identifica su origen por separado e indica que el texto de la página no aporta instrucciones confiables
