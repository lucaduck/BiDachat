# Revisión de inicialización

**Fecha:** 2026-09-15. **Alcance:** estructura, herramientas de especificación y diseño documental de base de datos.

## Ciclos de revisión

1. **Requisitos y alcance:** lectura de SRS.md, AGENTS.md y desing.md. El repositorio no tenía código. Se conservó el estado de borrador del SRS y no se interpretaron métricas ilustrativas de la guía visual como requisitos nuevos.
2. **Modelo y relaciones:** revisión inicial de seis entidades y actualización a siete tras aprobar el catálogo `llm_models`, además de FK, cardinalidades y ausencia de entidades innecesarias. Se dejó explícito que autoría no equivale a permiso exclusivo y que documentos compartidos necesitan otra decisión.
3. **Integridad y operación:** revisión de publicación atómica de fragmentos, filtros por chatbot, fallos sin duración observada, perfil vectorial fijo y separación entre borrado SQL y limpieza de archivos.
4. **Verificación documental:** validación estricta de OpenSpec, formato de documentos nuevos, enlaces locales, referencias CA/RF/RNF/RS y carpetas esperadas.

## Resultados ejecutados

| Comprobación                            | Resultado                                                                |
| --------------------------------------- | ------------------------------------------------------------------------ |
| `npm.cmd run spec:validate`             | 1 cambio válido, 0 fallos, modo estricto                                 |
| Estado de `design-mvp-database`         | 4/4 artefactos de planificación completos                                |
| `npm.cmd run format:check`              | Formato correcto en todos los archivos incluidos                         |
| Revisión de Markdown                    | 13 documentos nuevos revisados; 20 enlaces a archivos locales existentes |
| Identificadores explícitos RF/RNF/RS/CA | Todos encontrados en SRS.md                                              |
| Estructura                              | 21 carpetas esperadas con `.gitkeep`                                     |
| Exclusiones Git                         | `.env`, almacenamiento privado y `node_modules` ignorados correctamente  |

La verificación de enlaces comprueba archivos de destino; no renderiza el diagrama ni valida enlaces web o anclas. Git mostró una advertencia al intentar leer la configuración global de exclusiones fuera del entorno permitido; las exclusiones locales anteriores sí se comprobaron. Los archivos iniciales SRS.md, AGENTS.md y desing.md se conservaron sin edición.

## Herramientas

- OpenSpec 1.13.0, inicializado mediante CLI oficial para Codex; seis habilidades generadas en `.agents/skills/`.
- Dependencias de desarrollo fijadas en package.json y package-lock.json.
- Prettier para Markdown, JSON y YAML nuevos.
- Node.js 24.18.0 y npm 11.16.0 durante la inicialización.

## Límites de la entrega

En la entrega de inicialización del 2026-09-15 no se crearon migraciones, tablas reales, endpoints, interfaz ni bundle de widget. No se ejecutaron entonces pruebas funcionales del MVP o SQL de los ejemplos. La actualización del 2026-09-16 aplicó el esquema local y ejecutó las comprobaciones SQL descritas abajo; las pruebas de concurrencia, autorización y aislamiento de servicios siguen pendientes.

El cambio `design-mvp-database` conserva tareas de aprobación e implementación sin completar. OpenSpec puede indicar que los cuatro artefactos de planificación existen; eso no significa que el diseño esté aprobado o implementado.

## Aprobación solicitada

La [sección 11 del diseño de datos](database-design.md#11-aprobación-y-siguiente-paso) reúne las decisiones que el usuario pidió revisar antes de implementar la base. La estructura del proyecto y la inicialización de herramientas ya están realizadas.

## Actualización de base local — 2026-09-16

Por petición del usuario se levantó `database` en Docker Compose con PostgreSQL 16.15 y pgvector 0.8.6. La imagen quedó fijada por digest, con volumen persistente y puerto publicado solo en `127.0.0.1:5433`.

Se comprobaron creación, reversión sobre esquema sin filas, reaplicación y persistencia de tablas tras recrear el contenedor. `database/tests/verify_initial_schema.sql` pasó las pruebas de relaciones, historial LLM, unicidad, FK, estados, duración, dimensión/norma vectorial y cascadas. La transacción de prueba se revirtió y la base quedó sin registros.

No se configuró todavía un modelo de embeddings. La dimensión local inicial es 768 y debe validarse contra el modelo elegido antes de cargar conocimiento. Las políticas del SRS pendientes no se consideran aprobadas por levantar este entorno local.

## Actualización de persistencia backend — 2026-09-21

Se implementó la conexión asíncrona FastAPI–PostgreSQL mediante SQLAlchemy y psycopg, con configuración privada por `DATABASE_URL`. Los modelos representan las siete tablas existentes y conservan las migraciones SQL como fuente del esquema. El backend en Compose espera la salud de PostgreSQL antes de iniciar.

La prueba de integración confirmó escritura, lectura, rollback ante una excepción y limpieza del registro temporal contra PostgreSQL local. Las nueve pruebas del backend pasaron; Ruff no reportó errores ni diferencias de formato. Esta entrega completa la infraestructura de persistencia de la tarea 3.3, pero no implementa todavía autenticación, CRUD, RAG, consultas o métricas.

## Actualización de sesiones administrativas — 2026-09-21

Se implementaron persistencia, validación y revocación de sesiones administrativas para UC-01. Las contraseñas usan scrypt con sal aleatoria y PostgreSQL conserva solo el digest SHA-256 de cada token aleatorio. La validación rechaza sesiones inexistentes, vencidas o revocadas y usuarios desactivados. La API incorpora `/api/v1/auth/login` y `/api/v1/auth/logout`; no incorpora registro público ni roles adicionales.

Las catorce pruebas del backend pasaron, incluidas las pruebas API y de servicio contra PostgreSQL. Estas comprobaciones cubren CA-UC01-01 a CA-UC01-04 dentro del alcance backend. El SRS permanece como borrador y esta implementación no aprueba las demás políticas pendientes.

## Actualización de gestión de chatbots — 2026-09-21

Se implementaron rutas administrativas protegidas para listar el catálogo `llm_models` y crear, listar, consultar, actualizar y eliminar chatbots. La actualización conserva el UUID estable y permite modificar la selección del modelo y las instrucciones sin alterar el mecanismo futuro de integración. `created_by` se conserva como trazabilidad y no se usa como filtro exclusivo en esta implementación mínima.

Las quince pruebas del backend pasaron, incluida la integración CRUD contra PostgreSQL, el rechazo de modelos no registrados y la protección de las rutas sin sesión. La tarea 3.5 permanece abierta porque CA-UC03-02 requiere completar la asociación operativa de fuentes mediante el módulo documental/RAG; no se declara satisfecha solo por la FK existente.
