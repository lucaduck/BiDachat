# Estructura del proyecto y justificación

## Criterio general

Un repositorio y un backend FastAPI con servicios lógicos, conforme a AGENTS.md y RNF-04. Frontend y widget acceden exclusivamente a REST `/api/v1` (RNF-01). Las carpetas preparan el MVP; su existencia no implica que los módulos estén implementados.

| Carpeta                | Responsabilidad                                           | Justificación                                                 |
| ---------------------- | --------------------------------------------------------- | ------------------------------------------------------------- |
| `frontend/app`         | Rutas y páginas Next.js                                   | Interfaz administrativa                                       |
| `frontend/components`  | Componentes reutilizables                                 | Consistencia de la guía visual                                |
| `frontend/services`    | Cliente de la API                                         | Evita acceso directo a BD o Gemini                            |
| `frontend/types`       | Tipos y contratos TypeScript                              | Representar entradas/salidas de API                           |
| `frontend/lib`         | Utilidades compartidas                                    | Reutilización cuando exista necesidad                         |
| `frontend/public`      | Recursos públicos                                         | Imágenes y recursos de interfaz, nunca documentos privados    |
| `backend/app/api`      | Endpoints REST delgados                                   | Validar y delegar operaciones                                 |
| `backend/app/services` | Autenticación, chatbots, documentos, consultas y métricas | Lógica de aplicación y límites transaccionales                |
| `backend/app/models`   | Modelos de persistencia                                   | Representar el esquema aprobado                               |
| `backend/app/schemas`  | Validación y serialización API                            | RS-05, contratos separados de persistencia                    |
| `backend/app/rag`      | Extracción, división, embeddings y recuperación           | RF-14–RF-17; filtro obligatorio por chatbot                   |
| `backend/app/llm`      | Integración Gemini                                        | RF-21; proveedor separado de lógica general                   |
| `backend/app/database` | Conexiones y sesiones PostgreSQL                          | Acceso a persistencia desde backend                           |
| `backend/app/core`     | Configuración e infraestructura compartida                | Secretos, parámetros y utilidades necesarias                  |
| `backend/tests`        | Pruebas de criterios de aceptación                        | Integración real con PostgreSQL/pgvector cuando se implemente |
| `widget/src`           | Cliente JavaScript embebible                              | RF-10/RF-23, independiente del dashboard                      |
| `widget/dist`          | Resultado futuro de compilación                           | Se ignoran generados excepto `.gitkeep`                       |
| `database/migrations`  | Historial versionado del esquema                          | Cambios reproducibles tras aprobación                         |
| `database/seeds`       | Inicialización controlada                                 | Sin credenciales reales ni usuarios públicos de prueba        |
| `docs`                 | Diseño, decisiones y guías                                | Revisión técnica y trazabilidad                               |
| `docker`               | Inicialización PostgreSQL y futuros Dockerfiles           | RNF-03; Compose en raíz ejecuta actualmente la base           |
| `openspec/changes`     | Propuestas activas                                        | Separar diseño pendiente de especificaciones consolidadas     |
| `openspec/specs`       | Especificaciones consolidadas                             | Inicialmente vacío; no fingir aprobación                      |
| `.agents/skills`       | Flujos OpenSpec generados para Codex                      | Asistencia al ciclo propuesta, implementación y archivo       |

`database/` conserva migraciones; `backend/app/database/` contiene el código de conexión. `backend/app/models/` representa tablas; `backend/app/schemas/` define contratos HTTP. Estas separaciones previenen mezclar responsabilidades sin introducir servicios desplegables adicionales.
