# BIDACHAT

Aplicación web para gestionar chatbots que ayudan a interpretar dashboards de BI-DATA.

## Estado actual

El repositorio contiene frontend Next.js, backend FastAPI y PostgreSQL + pgvector
en Docker Compose. El panel administra chatbots y documentos; el widget público
envía consultas de texto o captura, recupera contexto por chatbot y responde
mediante Gemini, Ollama, OpenAI u OpenRouter configurado. Los documentos se procesan al cargarlos.
Para usarlo hay que configurar credenciales de administrador y al menos un
proveedor en `.env`. La integración Docker completa requiere Docker Desktop
activo para verificarse en este equipo.

El documento principal para revisar es [Diseño de base de datos](docs/database-design.md): contiene siete tablas, diagrama de relaciones, diccionario de datos, justificaciones, aislamiento, borrado, métricas y decisiones pendientes.

## Estructura

```text
BIDACHAT/
├── frontend/
│   ├── app/
│   ├── components/
│   ├── services/
│   ├── types/
│   ├── lib/
│   └── public/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── services/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── rag/
│   │   ├── llm/
│   │   ├── database/
│   │   └── core/
│   └── tests/
├── widget/
│   ├── src/
│   └── dist/
├── database/
│   ├── migrations/
│   └── seeds/
├── docs/
├── docker/
├── openspec/
│   ├── config.yaml
│   ├── specs/
│   └── changes/
└── .agents/skills/openspec-*/
```

Consulta [la responsabilidad de cada carpeta](docs/project-structure.md). `docker-compose.yml` levanta la base de datos, el backend FastAPI, el frontend y Ollama con GPU.

## API local

Para probar el sistema completo, copia `.env.example` a `.env`, configura
`POSTGRES_PASSWORD`, `ADMIN_EMAIL` y `ADMIN_PASSWORD`. Para el perfil local,
descarga primero los modelos de Ollama y arranca:

```powershell
docker compose up -d ollama
docker compose exec ollama ollama pull embeddinggemma:300m
docker compose exec ollama ollama pull qwen3-vl:2b
docker compose up -d --build
```

Abre `http://localhost:3000`, inicia sesión, crea un chatbot y copia su script
de integración. Prueba visualmente el widget en
`http://localhost:3000/widget-example.html?chatbot_id=UUID` con el UUID creado.
Si cambias `FRONTEND_PORT`, usa ese puerto. El perfil `EMBEDDING_PROVIDER=ollama` permite documentos y búsqueda semántica
sin clave Gemini. Consulta [la guía del frontend](frontend/README.md).

Para usar un modelo de consumo mediante OpenRouter, añadir en `.env`:

```text
OPENROUTER_API_KEY=clave_privada
OPENROUTER_MODEL=proveedor/modelo
OPENROUTER_SITE_URL=http://localhost:3000
```

Después ejecutar `docker compose up -d --build backend`, abrir **Configuración**
y seleccionar el modelo `openrouter` al crear o editar el chatbot. La clave se
queda dentro del backend.

```powershell
docker compose up -d --build backend
```

API: <http://localhost:8000/api/v1/health>. Documentación: <http://localhost:8000/api/v1/docs>. Consulta [configuración, desarrollo y pruebas del backend](backend/README.md).
El catálogo de rutas está en [docs/api-routes.md](docs/api-routes.md).

En el equipo actual, el `.env` selecciona el puerto **8001** porque 8000 está ocupado: [salud](http://localhost:8001/api/v1/health) y [documentación](http://localhost:8001/api/v1/docs).

## Base de datos local

```powershell
docker compose up -d database
docker compose ps
```

La base se encuentra en `localhost:5433` y conserva sus datos en un volumen Docker. Requiere las variables del `.env` local. Consulta [la guía de ejecución y pruebas](database/README.md) antes de inicializar otro equipo.

## Herramientas de especificación

OpenSpec 1.13.0 y Prettier están fijados como dependencias de desarrollo en el manifiesto raíz. Este manifiesto administra documentación, no sustituye los futuros manifiestos del frontend y backend. Se verificó con Node.js 24.18.0 y npm 11.16.0.

```powershell
npm.cmd ci
npm.cmd run spec:list
npm.cmd run spec:validate
npm.cmd run format:check
```

En shells que no sean PowerShell puede utilizarse `npm` en lugar de `npm.cmd`.

OpenSpec se inicializó mediante su CLI oficial con `init --tools codex`; las habilidades generadas están en `.agents/skills/`. [Documentación oficial de OpenSpec](https://github.com/Fission-AI/OpenSpec/blob/main/docs/cli.md).

## Flujo de trabajo

1. Leer [SRS.md](SRS.md) y [AGENTS.md](AGENTS.md).
2. Revisar [la propuesta de datos](docs/database-design.md) y sus decisiones de aprobación.
3. Consultar el cambio `design-mvp-database` en `openspec/changes/`.
4. Registrar las decisiones pendientes y ajustar los documentos antes de implementar servicios o nuevas migraciones.
5. Implementar tareas aprobadas, comprobar criterios de aceptación y ejecutar pruebas reales.
6. Sincronizar y archivar el cambio solo cuando se haya completado; `openspec/specs/` se reserva para especificaciones consolidadas.

La existencia de artefactos o una validación exitosa de OpenSpec verifica estructura documental, no aprobación del diseño ni funcionamiento del MVP.

## Configuración

[.env.example](.env.example) enumera variables previstas con secretos vacíos. Al implementar los servicios, copiarlo a `.env` y completar valores locales. `.env`, archivos privados y salidas de compilación se excluyen del repositorio. La única variable `NEXT_PUBLIC_*` propuesta es la URL pública de la API.

## Fuentes del proyecto

- [SRS.md](SRS.md): requisitos y criterios de aceptación, borrador 0.1.
- [AGENTS.md](AGENTS.md): reglas de implementación.
- [desing.md](desing.md): guía visual existente; se conserva su nombre original.
- [Diseño de base de datos](docs/database-design.md): propuesta técnica pendiente de aprobación.
- [Revisión de inicialización](docs/initialization-review.md): comprobaciones y límites de esta entrega.

### IA local

Configuración y operación: [Ollama local](docs/local-ollama.md).

### Integración y despliegue

El flujo de GitHub usa `develop` para integración y `production` para publicar
las imágenes y desplegar una versión aprobada. La configuración del servidor,
las ramas y los secretos necesarios está en [la guía de GitHub Actions](docs/deployment/github-actions.md).
