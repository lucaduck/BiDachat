# BIDACHAT

BIDACHAT permite a investigadores de BI-DATA crear, configurar e integrar asistentes conversacionales en dashboards. El panel administra chatbots, fuentes de conocimiento y métricas. Un widget JavaScript envía preguntas y capturas a una API REST; el backend recupera contexto y consulta el modelo configurado.

La aplicación usa Next.js, FastAPI, PostgreSQL con pgvector y Ollama en Docker. Puede utilizar API externas de IA configuradas; backend, base de datos y archivos documentales permanecen en infraestructura controlada. La [arquitectura](docs/architecture.md) explica los límites entre componentes.

## Arranque local

Se necesitan Docker Engine con Compose y capacidad para ejecutar los modelos configurados. Desde la raíz del repositorio:

```bash
cp .env.example .env
```

Edita `.env`: establece `POSTGRES_PASSWORD`, `ADMIN_EMAIL` y `ADMIN_PASSWORD`; revisa los límites de CPU y memoria para tu equipo y los modelos de Ollama. Los valores iniciales del ejemplo corresponden al entorno de desarrollo de referencia, donde Docker ve 7,7 GiB de RAM. `.env` contiene secretos y está excluido de Git.

```bash
docker compose config --quiet
docker compose up -d database ollama
docker compose exec ollama ollama pull embeddinggemma:300m
docker compose exec ollama ollama pull qwen3:1.7b
docker compose up -d --build
docker compose ps
```

Abre `http://127.0.0.1:3000` y entra con el administrador configurado. Si cambias `FRONTEND_PORT`, usa ese puerto. Comprueba la API en `http://127.0.0.1:3000/api/v1/health` y, en desarrollo, su documentación en `/api/v1/docs`. Los puertos locales de diagnóstico de FastAPI y PostgreSQL se configuran con `BACKEND_PORT` y `POSTGRES_PORT`; en producción solo Nginx publica un puerto ligado a `127.0.0.1`.

El modelo inicial `qwen3:1.7b` responde consultas de texto. Las **imágenes como fuentes de conocimiento** requieren configurar `VISION_PROVIDER` y un modelo visual compatible en `VISION_MODEL` (Ollama, Gemini, OpenAI, OpenRouter o Vertex); la imagen adjunta en una conversación también requiere que el modelo de respuesta seleccionado admita visión. Consulta [Ollama local](docs/local-ollama.md) antes de probar esos casos.

El widget conserva memoria textual anónima por chatbot y origen durante la sesión del navegador. El backend limita la ventana mediante `CONVERSATION_TTL_HOURS`, `CONVERSATION_MAX_TURNS` y `CONVERSATION_MAX_CHARS`; no guarda las imágenes como memoria. La limpieza de conversaciones vencidas se ejecuta al iniciar el backend y cada `CONVERSATION_CLEANUP_INTERVAL_MINUTES` (60 minutos por defecto). Conserva las consultas y métricas. También puede ejecutarse manualmente:

```bash
docker compose exec -T backend python -m app.cleanup_conversations
```

La [guía de memoria conversacional](docs/conversation-memory.md) explica los límites, el reinicio de conversación y la identidad firmada opcional. Una sesión anónima identifica una conversación del navegador; no acredita la identidad de una persona.

Vertex admite un catálogo explícito mediante `VERTEX_MODELS` y usa `VERTEX_MODEL` como selección predeterminada. Cada modelo debe comprobarse en el proyecto de Google antes de exponerlo en el editor; consulta la [guía de Vertex AI](docs/vertex-ai.md).

Para comprobar el widget en la instalación local, crea un chatbot y abre `/widget-example.html?chatbot_id=UUID`. Para probarlo en otro sitio, sigue la [guía del widget](widget/README.md) y configura `WIDGET_ALLOWED_ORIGINS` con los orígenes exactos autorizados, incluido el panel para la vista previa (esquema, dominio y puerto). La API rechaza consultas sin `Origin`, con un origen no autorizado o con la lista vacía. Esta comprobación no sustituye la autenticación. `widget/example/` contiene la página de prueba; el build copia una versión a `frontend/public/` para la integración local.

## Mapa del repositorio

| Ruta                                         | Responsabilidad                                                |
| -------------------------------------------- | -------------------------------------------------------------- |
| [`frontend/`](frontend/)                     | Panel Next.js, componentes, cliente API y pruebas de interfaz. |
| [`backend/`](backend/)                       | FastAPI, lógica, RAG, proveedores y pruebas.                   |
| [`widget/`](widget/)                         | Script embebible y página de ejemplo.                          |
| [`database/`](database/)                     | Migraciones SQL y comprobaciones de esquema.                   |
| [`docker/`](docker/) y `docker-compose*.yml` | Imágenes, Nginx y despliegue.                                  |
| [`docs/`](docs/README.md)                    | Guías, referencias, arquitectura y evidencia de pruebas.       |
| [`openspec/`](openspec/)                     | Propuestas y tareas de cambios.                                |

El [mapa detallado](docs/project-structure.md) distingue código fuente, documentos de decisión, datos privados y artefactos generados.

## Documentación y colaboración

- [Índice de documentación](docs/README.md): guías por tarea, referencias, explicaciones y evidencia.
- [SRS](SRS.md): requisitos y criterios de aceptación.
- [Reglas de implementación](AGENTS.md) y [guía de contribución](CONTRIBUTING.md).
- [Rutas de la API](docs/api-routes.md) y [diseño de datos](docs/database-design.md).
- [Despliegue con GitHub Actions](docs/deployment/github-actions.md) y [proxy inverso](docs/deployment/reverse-proxy.md).
- [Matriz de decisión documental](docs/documentation-decision.md): criterios de organización aplicados aquí.

El código y las migraciones muestran la implementación; `SRS.md` mantiene los requisitos. Las [evidencias de prueba](docs/qa/README.md) registran resultados de versiones y entornos concretos. No se presentan como garantía de un despliegue posterior.
