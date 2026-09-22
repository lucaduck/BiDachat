# Glosario y notas de aprendizaje — BIDACHAT

Este documento reúne conceptos, herramientas y aprendizajes que surjan durante el desarrollo de la tesis. Su propósito es explicar con palabras sencillas qué significa cada término, para qué sirve y cómo se relaciona con BIDACHAT.

Es un documento vivo: iremos agregando entradas, ejemplos y dudas conforme avance el proyecto. Las notas no sustituyen los requisitos de [SRS.md](SRS.md) ni las decisiones del [diseño de base de datos](docs/database-design.md).

## Cómo usar este glosario

- Buscar si el concepto ya existe antes de agregarlo.
- Explicarlo con nuestras propias palabras y un ejemplo del proyecto.
- Distinguir lo aprendido de las decisiones propuestas o pendientes de aprobación.
- Anotar las dudas para investigarlas después.
- Añadir la fuente consultada cuando corresponda. Para utilizar una definición en la tesis, verificar y citar una fuente académica o técnica adecuada.

## 1. Herramientas y archivos del proyecto

### OpenSpec

**Qué es:** una herramienta para organizar propuestas de cambio mediante especificaciones, diseño y tareas.

**En BIDACHAT:** permite documentar qué se propone implementar, cómo se plantea hacerlo y qué tareas faltan. Sus archivos están en `openspec/`.

**Aprendizaje:** que una propuesta pase la validación de OpenSpec significa que cumple sus comprobaciones documentales; no significa que esté aprobada o implementada.

### Node.js

**Qué es:** un entorno que permite ejecutar JavaScript fuera del navegador.

**En BIDACHAT:** se utiliza para ejecutar herramientas como OpenSpec y Prettier. También forma parte del entorno previsto para Next.js.

**Aprendizaje:** usar Node.js para herramientas del proyecto no cambia la elección del backend, que sigue siendo FastAPI con Python.

### npm

**Qué es:** un gestor de paquetes del ecosistema de Node.js. Permite instalar dependencias y ejecutar comandos definidos por el proyecto.

**Ejemplo:** `npm run spec:validate` ejecuta el comando de validación declarado en `package.json`. En PowerShell también podemos escribir `npm.cmd`.

### Dependencia

**Qué es:** un paquete de software que un proyecto utiliza para realizar una tarea sin tener que implementarla desde cero.

**En BIDACHAT:** OpenSpec y Prettier son dependencias de desarrollo: ayudan a trabajar en el repositorio.

**Aprendizaje:** una dependencia puede necesitar otros paquetes. Por eso una instalación puede descargar más paquetes que los declarados directamente.

### `package.json`

**Qué es:** el manifiesto de un proyecto que utiliza herramientas del ecosistema Node.js. Declara información del proyecto, dependencias y comandos, llamados scripts.

**En BIDACHAT:** el archivo de la raíz declara OpenSpec, Prettier y los comandos para validar especificaciones y formato.

**Aprendizaje:** se guarda en Git. Actualmente administra herramientas del repositorio; no significa que la aplicación web ya esté implementada.

### `package-lock.json`

**Qué es:** un archivo generado por npm que registra las versiones resueltas de los paquetes y sus dependencias.

**Para qué sirve:** ayuda a reproducir la misma instalación en otros equipos.

**Aprendizaje:** se guarda en Git. El comando `npm ci` instala las dependencias siguiendo este archivo y exige que sea consistente con `package.json`.

### `node_modules/`

**Qué es:** la carpeta donde npm instala los paquetes descargados para el proyecto.

**En BIDACHAT:** contiene OpenSpec, Prettier y los paquetes que necesitan para funcionar.

**Aprendizaje:** no se sube a Git. Se puede regenerar mediante la instalación de dependencias; no debemos editar manualmente su contenido como si fuera código propio.

### Prettier y `.prettierrc.json`

**Qué es:** Prettier es una herramienta que da formato consistente a archivos compatibles. `.prettierrc.json` contiene sus opciones de configuración.

**En BIDACHAT:** se usa para revisar el formato de los documentos Markdown y archivos JSON y YAML incluidos en el comando de revisión.

**Aprendizaje:** revisar formato no comprueba que los requisitos o el diseño sean correctos. El archivo de configuración sí se guarda en Git.

### Git y `.gitignore`

**Qué es:** Git registra versiones de los archivos del proyecto. `.gitignore` indica qué archivos sin seguimiento deben quedar fuera de ese registro.

**En BIDACHAT:** se excluyen dependencias descargadas, archivos privados, secretos locales y resultados generados.

**Aprendizaje:** agregar un archivo a `.gitignore` no elimina versiones que ya estuvieran registradas en Git.

### Markdown (`.md`)

**Qué es:** un formato de texto que utiliza marcas sencillas para escribir títulos, listas, enlaces y otros elementos.

**Ejemplo:** `# Título` crea un encabezado y `**texto**` indica negrita.

**En BIDACHAT:** este glosario, el SRS y la propuesta de base de datos están escritos en Markdown.

## 2. Requisitos y organización del desarrollo

### SRS — Especificación de Requisitos de Software

**Qué es:** un documento que describe qué debe hacer el sistema y qué condiciones debe cumplir.

**En BIDACHAT:** `SRS.md` contiene requisitos funcionales (RF), no funcionales (RNF), de seguridad (RS), casos de uso (UC) y criterios de aceptación (CA).

**Aprendizaje:** el documento actual figura como borrador. Una propuesta técnica no puede darse por aprobada solo porque está escrita.

### MVP — Producto Mínimo Viable

**Qué es:** una primera versión con las funciones necesarias para cumplir y comprobar el propósito principal del producto.

**En BIDACHAT:** debe permitir completar el flujo desde iniciar sesión y configurar un chatbot hasta consultar desde el widget y registrar métricas.

**Aprendizaje:** mínimo no significa incompleto respecto de los requisitos aprobados de esa versión.

### Criterio de aceptación

**Qué es:** una condición observable que permite comprobar si una función cumple lo esperado.

**Ejemplo:** después de cerrar sesión, el investigador ya no puede acceder a operaciones administrativas protegidas.

### Migración de base de datos

**Qué es:** un cambio versionado de la estructura de la base de datos, como crear una tabla o agregar una columna.

**En BIDACHAT:** las migraciones se ubican en `database/migrations/`. El esquema inicial ya se aplicó en un contenedor Docker local; los siguientes cambios deberán agregarse como migraciones nuevas.

**Aprendizaje:** documentar una tabla no la crea en PostgreSQL. Una migración aplicada sí modifica el esquema real.

## 3. Base de datos y relaciones

### Tabla, fila y columna

**Qué son:** una tabla organiza registros; cada fila representa un registro y cada columna describe uno de sus atributos.

**Ejemplo:** en la tabla propuesta `chatbots`, una fila representa un chatbot y la columna `name` contiene su nombre.

### Clave primaria (PK)

**Qué es:** el campo o conjunto de campos que identifica de forma única cada fila de una tabla. No admite valores nulos.

**En BIDACHAT:** se propone usar `id` como clave primaria de cada tabla.

### Clave foránea (FK)

**Qué es:** un campo o conjunto de campos que referencia una clave válida de otra tabla, o de la misma tabla, para mantener integridad entre registros.

**Ejemplo:** `documents.chatbot_id` referencia `chatbots.id` e indica a qué chatbot pertenece el documento.

**Aprendizaje:** la FK comprueba la relación entre datos; no determina si una persona tiene permiso para consultarlos.

### Cardinalidad y relación uno a muchos (1:N)

**Qué es:** la cardinalidad indica cuántos registros pueden relacionarse. En una relación 1:N, un registro puede vincularse con varios registros de otra tabla.

**En BIDACHAT:** se propone que un chatbot tenga cero o muchos documentos y que cada documento pertenezca exactamente a un chatbot.

**Aprendizaje:** esta relación es una decisión propuesta. Compartir un documento entre varios chatbots requeriría revisar el modelo.

### Transacción

**Qué es:** un conjunto de operaciones de base de datos que se confirma como una unidad o se revierte si no puede completarse.

**Ejemplo:** guardar todos los fragmentos de un documento y marcarlo como listo dentro de una misma transacción.

**Aprendizaje:** una transacción de PostgreSQL no revierte automáticamente acciones externas, como escribir o borrar un archivo del disco.

### Aislamiento entre chatbots

**Qué es:** la regla que impide que una consulta utilice datos o conocimiento que pertenecen exclusivamente a otro chatbot.

**Ejemplo:** el chatbot A solo recupera los documentos asociados a A, aunque existan documentos similares en B.

**Aprendizaje:** requiere filtros correctos en backend y pruebas de acceso cruzado; no basta con tener claves foráneas.

## 4. Inteligencia artificial y comunicación

### Embedding

**Qué es:** una representación de contenido mediante un vector de números, generada por un modelo. Permite comparar similitud según esa representación.

**En BIDACHAT:** los fragmentos documentales tendrán embeddings para buscar contexto relacionado con una pregunta.

**Aprendizaje:** vectores de igual dimensión no son necesariamente compatibles si fueron generados por modelos distintos.

### pgvector

**Qué es:** una extensión de PostgreSQL que permite almacenar vectores y realizar búsquedas por similitud.

**En BIDACHAT:** permite mantener los datos relacionales y los vectores en la misma base de datos.

### RAG — Generación aumentada por recuperación

**Qué es:** un enfoque que recupera información relevante y la incorpora al contexto que recibe un modelo generativo para responder.

**Ejemplo en BIDACHAT:** pregunta → búsqueda en documentos del chatbot → contexto recuperado → modelo de lenguaje → respuesta.

**Aprendizaje:** recuperar documentos no equivale a entrenar un modelo y no garantiza por sí solo que la respuesta sea correcta.

### API

**Qué es:** una interfaz que define cómo un programa puede solicitar operaciones o intercambiar datos con otro.

**En BIDACHAT:** el frontend y el widget se comunican con FastAPI mediante la API. No acceden directamente a PostgreSQL ni a Gemini.

### Widget

**Qué es:** un componente de interfaz que puede incorporarse dentro de otra aplicación o página.

**En BIDACHAT:** será el cliente de chat integrado en los dashboards de BI-DATA.

## 5. Bitácora de aprendizajes

| Fecha      | Concepto o situación                      | Qué aprendimos                                                                                                                    | Duda o siguiente paso                                                                                      |
| ---------- | ----------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| 2026-09-15 | Archivos creados al instalar herramientas | `package.json` declara herramientas, `package-lock.json` fija la instalación y `node_modules/` contiene los paquetes descargados. | Distinguir las herramientas de desarrollo de las dependencias de la aplicación al implementar los módulos. |
| 2026-09-15 | Diseño de la base de datos                | Las relaciones, el aislamiento y las políticas de borrado deben justificarse antes de aplicar el esquema.                         | Revisar las decisiones pendientes en `docs/database-design.md`.                                            |

## 6. Plantilla para nuevos conceptos

Copiar esta plantilla en la sección correspondiente y completar los campos que ayuden a entender el concepto:

```markdown
### Nombre del concepto

**Qué es:** explicación sencilla con nuestras propias palabras.

**Para qué sirve:** problema que ayuda a resolver.

**Ejemplo en BIDACHAT:** caso concreto del proyecto.

**Qué aprendimos:** observación importante o confusión que resolvimos.

**Dudas pendientes:** qué falta verificar, si aplica.

**Fuente consultada:** documento, enlace o referencia, si aplica.

**Fecha de la anotación:** AAAA-MM-DD.
```
