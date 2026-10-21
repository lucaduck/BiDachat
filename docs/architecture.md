# Arquitectura de BIDACHAT

Esta explicación representa la implementación del repositorio. El [SRS](../SRS.md) define el comportamiento requerido; el [Compose de producción](../docker-compose.production.yml) y las [rutas FastAPI](../backend/app/api/router.py) describen la configuración ejecutable. Conforme a la [decisión documental](documentation-decision.md#convención-para-diagramas), los gráficos usan niveles del [modelo C4](https://c4model.com/) y sintaxis Mermaid. En C4, “contenedor” significa aplicación o almacén en ejecución y no exige un contenedor Docker.

## Contexto del sistema

```mermaid
flowchart LR
    researcher[Investigador autorizado] -->|Administra asistentes| bidachat[BIDACHAT]
    visitor[Visitante del dashboard] -->|Pregunta desde el widget| bidata[Dashboard BI-DATA]
    bidata -->|Integra el widget y consulta la API| bidachat
    bidachat -->|Solo cuando se configura un proveedor externo| ai[API externa de IA]
```

BIDACHAT administra chatbots y fuentes, procesa consultas y registra métricas. El dashboard BI-DATA aloja el widget, pero la base de datos, el backend y los archivos originales permanecen en infraestructura controlada por el proyecto. No hay servicios externos para base de datos o backend; las API de IA configuradas son la integración externa de ejecución permitida por RNF-15.

## Aplicaciones y almacenes en ejecución

```mermaid
flowchart LR
    admin[Panel en navegador] -->|HTTPS| public[Proxy TLS del host]
    dashboard[Dashboard externo con widget JS] -->|HTTPS| public
    public --> nginx[Nginx de BIDACHAT]
    nginx -->|Páginas y script| next[Next.js]
    nginx -->|REST /api/v1| api[FastAPI]
    api --> postgres[(PostgreSQL + pgvector)]
    api --> files[(Volumen documental privado)]
    api --> ollama[Ollama local]
    api -->|Según configuración| direct[Gemini / OpenAI / OpenRouter]
    api -->|Perfil Vertex habilitado| litellm[LiteLLM privado]
    litellm -->|Credencial de servicio| vertex[Vertex AI]
```

El panel y el widget son clientes de la API REST. Nginx ofrece panel, script y API bajo un origen; en producción solo publica un puerto en `127.0.0.1` para el proxy TLS del host. FastAPI concentra autenticación, gestión, procesamiento documental, recuperación, proveedores y métricas. Next.js y el widget no consultan PostgreSQL ni proveedores de IA directamente. LiteLLM solo se inicia con el perfil opcional `vertex`, no publica un puerto al host y es el único proceso que monta la credencial de servicio de Google.

## Componentes lógicos de FastAPI

```mermaid
flowchart LR
    routes[Rutas y esquemas API] --> auth[Autenticación]
    routes --> chatbots[Gestión de chatbots]
    routes --> documents[Documentos]
    routes --> queries[Consultas]
    routes --> metrics[Métricas]

    documents --> rag[Procesamiento y recuperación RAG]
    queries --> memory[Memoria conversacional]
    queries --> rag
    queries --> llm[Adaptadores LLM]

    auth --> persistence[Modelos y sesiones SQLAlchemy]
    chatbots --> persistence
    documents --> persistence
    queries --> persistence
    metrics --> persistence
    memory --> persistence
    rag --> persistence

    llm --> ollama[Ollama]
    llm --> external[Gemini / OpenAI / OpenRouter]
    llm --> gateway[Gateway Vertex]
    gateway --> litellm[LiteLLM]
```

Las rutas permanecen delgadas y delegan reglas a `app/services/`. La recuperación
RAG usa documentos asociados al chatbot; la memoria conserva solamente mensajes
textuales recientes de una conversación válida. Los adaptadores de `app/llm/`
encapsulan cada proveedor y evitan que las credenciales lleguen a los clientes.

La lógica del backend vive en `app/services/`; `app/api/` expone rutas, `app/models/` representa persistencia, `app/schemas/` valida el contrato y `app/llm/` aísla proveedores. Es una arquitectura cliente-servidor con servicios lógicos dentro de un backend FastAPI. El despliegue no separa esos servicios como microservicios.

El widget envía cada consulta mediante HTTP a la API; no existe conexión WebSocket permanente. El backend recupera fragmentos asociados al chatbot, combina la pregunta con el contexto permitido y registra el resultado y el tiempo. Para datos y límites específicos, consultar [diseño de base de datos](database-design.md), [memoria y contexto](conversation-memory.md), [Vertex mediante LiteLLM](vertex-ai.md), [rutas](api-routes.md) y [guía del proxy](deployment/reverse-proxy.md).
