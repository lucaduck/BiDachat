# BIDACHAT

Aplicación web para gestionar chatbots que ayudan a interpretar dashboards de BI-DATA.

## Estado actual

Repositorio inicializado con OpenSpec, estructura del MVP, base PostgreSQL + pgvector y aplicación FastAPI ejecutables en Docker. El esquema inicial de siete tablas está aplicado en el contenedor local. El backend ofrece salud HTTP, documentación API, conexión asíncrona, modelos de persistencia, sesiones administrativas revocables, CRUD/configuración básica de chatbots, carga documental privada, publicación/recuperación RAG aislada por chatbot y métricas administrativas agregadas. Quedan pendientes el flujo conversacional con LLM, el widget, la interfaz web y el borrado coordinado con el volumen. El SRS fue aprobado por el usuario como referencia de implementación del MVP el 2026-09-22.

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

Los archivos `.gitkeep` conservan en Git las carpetas vacías. Consulta [la responsabilidad de cada carpeta](docs/project-structure.md). `docker-compose.yml` levanta la base de datos y el backend FastAPI.

## API local

```powershell
docker compose up -d --build backend
```

API: <http://localhost:8000/api/v1/health>. Documentación: <http://localhost:8000/api/v1/docs>. Consulta [configuración, desarrollo y pruebas del backend](backend/README.md).

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
