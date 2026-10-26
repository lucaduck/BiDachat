## Purpose

Permitir al investigador administrar y publicar un cuestionario global con preguntas personalizadas, manteniendo comparable el CSAT y relacionando cada respuesta con la versión que vio el visitante.

## ADDED Requirements

### Requirement: Administración global y activación
El sistema SHALL permitir a un investigador autenticado activar o desactivar un cuestionario que se aplica a todos los chatbots. La puntuación general de satisfacción de 1 a 5 SHALL permanecer obligatoria en cada respuesta enviada y no podrá eliminarse ni cambiar de escala.

#### Scenario: Desactivación global
- **WHEN** el investigador desactiva el cuestionario en Configuración general
- **THEN** ningún chatbot registra nuevas ofertas, mientras las conversaciones y las evaluaciones anteriores siguen disponibles

#### Scenario: Acceso no autorizado
- **WHEN** un visitante intenta editar o publicar el cuestionario sin sesión administrativa
- **THEN** el sistema rechaza la operación sin modificar la versión activa

### Requirement: Preguntas y opciones personalizadas
El sistema SHALL permitir editar título, introducción y agradecimiento, mostrar u ocultar los campos opcionales actuales y agregar preguntas adicionales de opción única o texto libre, marcadas como obligatorias u opcionales. Cada pregunta de opción única SHALL tener opciones con texto y orden propios. El editor SHALL permitir reordenar, editar y quitar preguntas antes de publicar.

#### Scenario: Pregunta de opción única válida
- **WHEN** el investigador crea una pregunta de opción única con al menos dos opciones distintas y guarda el formulario
- **THEN** la vista previa presenta las opciones en el orden definido

#### Scenario: Pregunta abierta válida
- **WHEN** el investigador agrega una pregunta de texto libre
- **THEN** la vista previa muestra un campo de texto con el límite permitido y su estado obligatorio u opcional

#### Scenario: Formulario inválido
- **WHEN** hay preguntas sin texto, opciones vacías o duplicadas, límites excedidos o posiciones inconsistentes
- **THEN** la publicación se rechaza y el formulario activo anterior permanece intacto

### Requirement: Publicación versionada
Cada publicación con cambios de contenido SHALL crear una versión nueva e inmutable del formulario y activarla de manera atómica. La configuración y las respuestas de versiones anteriores SHALL conservarse. Cambiar solo el estado global de activación SHALL mantener la versión activa.

#### Scenario: Publicar edición
- **WHEN** el investigador publica cambios en preguntas, opciones o textos
- **THEN** los nuevos visitantes reciben la nueva versión y las ofertas ya registradas conservan la versión anterior

#### Scenario: Error durante publicación
- **WHEN** falla cualquier paso de validación o persistencia de una nueva versión
- **THEN** no aparece una versión parcial ni cambia la versión activa

### Requirement: Compatibilidad de evaluaciones existentes
La migración SHALL crear una versión inicial equivalente al formulario actual y relacionar con ella las ofertas y respuestas ya almacenadas, sin cambiar sus puntuaciones, chatbot ni fechas.

#### Scenario: Actualización de instalación existente
- **WHEN** la migración encuentra evaluaciones previas
- **THEN** todas quedan asociadas a la versión inicial y las métricas CSAT continúan iguales

### Requirement: Oferta y respuesta contra la versión presentada
El widget SHALL recibir solo la versión publicada y los datos de presentación necesarios desde un origen autorizado. Al ofrecer el cuestionario, el sistema SHALL fijar su versión a la conversación. Al enviar, SHALL validar una respuesta a cada pregunta obligatoria y que cada opción pertenezca a la pregunta de esa versión; SHALL conservar la regla de una única respuesta por conversación.

#### Scenario: Cambio de versión con formulario abierto
- **WHEN** se publica otra versión después de ofrecer un formulario al visitante
- **THEN** ese visitante puede enviar respuestas válidas para la versión que recibió, mientras su conversación siga vigente

#### Scenario: Respuesta incompatible
- **WHEN** el cliente envía una opción de otra pregunta o versión, omite una pregunta obligatoria o duplica una respuesta
- **THEN** el sistema rechaza la solicitud completa sin registrar una respuesta parcial

#### Scenario: Origen o configuración indisponible
- **WHEN** el widget no puede obtener la versión publicada desde un origen autorizado
- **THEN** sigue permitiendo conversar y no muestra una encuesta cuya configuración desconoce

### Requirement: Resultados comparables y privacidad
Métricas SHALL seguir calculando CSAT con la puntuación obligatoria y filtrando por chatbot y periodo. Los resultados de preguntas personalizadas SHALL mostrarse por versión y pregunta, sin mezclar IDs distintos aunque coincida el texto; los textos libres SHALL estar disponibles solo para investigadores autenticados, paginados y sujetos a la retención vigente de 90 días.

#### Scenario: Cambio de opciones
- **WHEN** se consulta una pregunta de opción única después de publicar una versión con opciones diferentes
- **THEN** cada versión conserva sus opciones y conteos propios, mientras CSAT se puede comparar entre versiones

#### Scenario: Vencimiento de texto libre
- **WHEN** una respuesta de texto libre supera 90 días desde su envío
- **THEN** se elimina su contenido y se conserva la indicación de que existió una respuesta para el conteo histórico

### Requirement: Vista previa y publicación comprensibles
Configuración general SHALL presentar una vista previa no interactiva del borrador, el número de versión activa, el alcance global y una acción explícita de publicación que no envíe ofertas ni respuestas reales.

#### Scenario: Revisar borrador
- **WHEN** el investigador modifica el orden o las opciones de una pregunta sin publicar
- **THEN** la vista previa cambia y el widget externo continúa usando la versión publicada
