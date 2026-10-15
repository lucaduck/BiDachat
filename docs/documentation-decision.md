# Decisión sobre documentación y estructura del repositorio

Fecha: 12 de octubre de 2026. Estado: aplicada a la navegación y a las guías de este repositorio.

## Problema y criterios

BIDACHAT reúne interfaz Next.js, API FastAPI, widget JavaScript, PostgreSQL/pgvector y despliegue Docker. El repositorio ya tiene un [SRS](../SRS.md), reglas para agentes, manuales por componente y evidencias de pruebas. Parte de la documentación conserva lenguaje de la fase MVP y el volumen de evidencias dificulta localizar una guía operativa.

La elección debe permitir encontrar instrucciones, mantener trazabilidad con requisitos, evitar duplicar contratos generados por código y conservar los enlaces existentes. El esfuerzo de mantenimiento importa porque el proyecto tiene un equipo pequeño y una tesis que debe poder verificarse.

**Terminología:** ISO/IEC/IEEE 15289 y 29148 son normas formales. Diátaxis, arc42 y C4 son marcos de documentación o visualización. GitHub publica convenciones para archivos de repositorio. Ninguno impone una estructura universal de carpetas para un monorepositorio como este.

## Matriz de decisión: documentación

| Enfoque                                                            | Lo que resuelve                                                                             | Encaje con BIDACHAT                                                                | Costo o límite                                                                                                       | Decisión                                                                                    |
| ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| [Diátaxis](https://diataxis.fr/)                                   | Separa tutoriales, guías de tareas, referencia y explicación según la necesidad del lector. | Alto: permite clasificar los documentos actuales sin moverlos ni romper enlaces.   | No especifica por sí solo requisitos, arquitectura ni carpetas de código.                                            | **Elegido para navegación y redacción.**                                                    |
| [arc42](https://arc42.org/)                                        | Plantilla completa de documentación de arquitectura.                                        | Medio: útil si la arquitectura crece o debe auditarse con detalle.                 | Adoptar toda la plantilla ahora repetiría SRS, diseño de datos y guías de despliegue.                                | Consultar sus preguntas; no imponer la plantilla completa.                                  |
| [ISO/IEC/IEEE 15289:2019](https://www.iso.org/standard/74909.html) | Define contenido de elementos documentales del ciclo de vida.                               | Medio para una tesis y su trazabilidad.                                            | Aplicación formal requiere seleccionar elementos y comprobar conformidad; no prescribe la navegación de estas guías. | Referencia metodológica; no declarar conformidad.                                           |
| [ISO/IEC/IEEE 29148:2018](https://www.iso.org/standard/72089.html) | Ingeniería y contenido de requisitos.                                                       | Alto para el SRS, bajo para manuales de operación.                                 | No resuelve la estructura del repositorio ni sustituye la comprobación de requisitos existentes.                     | Mantener el SRS como fuente de requisitos; revisar conformidad por separado si se solicita. |
| [C4](https://c4model.com/)                                         | Diagramas de contexto, contenedores y componentes.                                          | Alto para comunicar la relación entre dashboard, widget, API, datos y proveedores. | Es una notación arquitectónica, no un sistema de documentación.                                                      | Usar como complemento en la [explicación de arquitectura](architecture.md).                 |

**Resultado:** Diátaxis ordena la documentación general; el SRS conserva la autoridad sobre requisitos; C4 sirve para explicar la arquitectura. Un documento nuevo debe tener un propósito identificable antes de crearse.

## Matriz de decisión: estructura del repositorio

| Alternativa                                                                                      | Ventaja en este proyecto                                                                                                             | Costo o riesgo                                                                                                                         | Decisión                                                                       |
| ------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| Monorepositorio actual, separado por `frontend/`, `backend/`, `widget/`, `database/` y `docker/` | Conserva en un mismo cambio API, cliente, migraciones, pruebas y despliegue. Los límites ya corresponden a responsabilidades reales. | Necesita un mapa vigente y reglas claras para fuentes, artefactos generados y evidencias.                                              | **Conservar y documentar** en [estructura del proyecto](project-structure.md). |
| Repositorios separados por componente                                                            | Permitiría permisos y publicaciones independientes.                                                                                  | Fragmentaría cambios que atraviesan widget, API y esquema; exigiría sincronizar versiones y PR adicionales sin una necesidad aprobada. | No adoptar.                                                                    |
| Reorganización en `packages/` con Nx/Turborepo u otro orquestador                                | Puede ayudar cuando muchos paquetes comparten compilación y caché.                                                                   | Añadiría dependencia, migración de rutas y otra capa de herramientas para tres clientes y un backend Python.                           | No adoptar sin un cuello de botella medido.                                    |

GitHub recomienda un README que explique propósito y arranque, y permite [enlaces relativos entre archivos](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes). Las [pautas de contribución](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/setting-guidelines-for-repository-contributors) explican el flujo humano; [AGENTS.md](../AGENTS.md) mantiene las reglas para agentes. Se añade un índice en `docs/` y se conserva `docs/qa/` como evidencia, fuera del recorrido de instalación.

## Reglas aplicadas

1. **Fuentes de verdad:** `SRS.md` define requisitos; `AGENTS.md` cómo implementar; código y migraciones muestran la implementación; OpenAPI generado documenta el contrato ejecutable. Los manuales enlazan a estas fuentes y no presentan una propuesta antigua como estado actual.
2. **Entrada corta:** el README raíz presenta producto, estructura, puesta en marcha y destinos. [El índice de documentación](README.md) dirige al lector según su tarea.
3. **Ubicación por responsabilidad:** cada componente conserva código y pruebas cerca de sí. `docs/` contiene manuales, explicación y referencia transversal; `docs/qa/` contiene resultados fechados; `docs/design-history/` y propuestas OpenSpec conservan historia.
4. **Enlaces estables:** usar rutas relativas. Al mover un documento, actualizar referencias en el mismo cambio y comprobarlas. Se mantienen las rutas actuales cuando una reorganización solo aportaría estética.
5. **Estado verificable:** distinguir comportamiento implementado, diseño propuesto y resultados observados. Toda cifra experimental debe indicar versión, fecha, entorno, método y límites.
6. **Cambio conjunto:** una modificación de API, esquema, configuración o despliegue debe revisar el documento que la explica, el requisito afectado y las pruebas pertinentes.
7. **Sin duplicación:** una tabla de rutas manual es orientación; ante discrepancias, contrastar el código y OpenAPI. Un diagrama explica límites; no reemplaza Compose ni migraciones.

## Verificación de la aplicación

- [x] Índice de documentos por necesidad del lector.
- [x] README raíz reducido a entrada y rutas vigentes.
- [x] Mapa de carpetas ajustado al árbol real.
- [x] Explicación de arquitectura con diagramas de contexto y componentes ejecutables.
- [x] Evidencias `docs/qa/` identificadas como resultados históricos.
- [ ] Auditoría formal de conformidad con ISO/IEC/IEEE 15289 o 29148. No se reivindica en esta decisión.
