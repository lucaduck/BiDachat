# Auditoría técnica integral de BIDACHAT

Fecha: 18 de octubre de 2026. Rama revisada:
`feature/recommendations-verification`. Revisión base: `cc4b5711f479`.

## Alcance y método

La revisión contrastó requisitos, código, migraciones, contenedores, CI/CD,
seguridad, memoria conversacional, RAG, documentación y pruebas. Se inspeccionó
el árbol de trabajo actual, que contiene cambios locales posteriores a la revisión
base. Por ello, este informe describe el estado local observado y no certifica una
versión publicada.

Se aplicaron cuatro tipos de evidencia:

1. trazabilidad contra `SRS.md` y los cambios OpenSpec;
2. análisis estático de los recorridos críticos y sus fronteras de confianza;
3. ejecución local de pruebas, lint, formato, compilaciones y validaciones de
   configuración;
4. contraste con las actas de aceptación ya conservadas en `docs/qa/`.

No se ejecutó una prueba de penetración ni se inspeccionó el VPS. HTTPS, Apache,
Cloudflare, permisos, respaldos programados y secretos del servidor permanecen
fuera de la evidencia local.

## Dictamen ejecutivo

El sistema tiene una base técnica coherente con el SRS: aplicación web cliente
servidor, API REST, servicios lógicos dentro de FastAPI, PostgreSQL con pgvector,
widget independiente, proveedores de IA aislados y despliegue Docker. Las pruebas
deterministas, compilaciones y configuraciones revisadas pasan.

El estado actual **no debe declararse listo para producción** hasta resolver un
hallazgo alto de integridad de datos y cerrar las condiciones del proxy y del
respaldo previo a migraciones. No se encontraron hallazgos críticos que expongan
credenciales en el repositorio ni dependencias vulnerables en el conjunto de
producción del frontend.

| Prioridad  | Cantidad | Interpretación                                                                   |
| ---------- | -------: | -------------------------------------------------------------------------------- |
| P0 crítica |        0 | No se observó compromiso inmediato o pérdida inevitable en todos los recorridos. |
| P1 alta    |        3 | Deben resolverse o aceptarse formalmente antes del despliegue.                   |
| P2 media   |        3 | Reducen seguridad, privacidad u operabilidad; requieren planificación próxima.   |
| P3 baja    |        2 | Mejoras de reproducibilidad y mantenimiento.                                     |

## Hallazgos

### AUD-01 · Eliminar el chatbot propietario borra una fuente todavía compartida

**Prioridad:** P1 alta · **Área:** integridad de datos · **Requisitos:** RF-09,
RS-07, CA-UC03-07.

`documents.chatbot_id` referencia al chatbot de origen con `ON DELETE CASCADE`.
La relación N:M posterior no cambió esa propiedad: `chatbot_documents` también
elimina sus filas cuando desaparece el documento. Antes de borrar un chatbot,
`ChatbotDeletionService` selecciona todas las fuentes cuyo `chatbot_id` es el bot
eliminado y, después del commit, borra sus archivos.

Como consecuencia, si una fuente creada en A está asociada también a B, eliminar
A elimina el registro, sus chunks, las asociaciones y el archivo aunque B todavía
la utilice. Las pruebas existentes comprueban borrar un bot y quitar asociaciones,
pero no el caso combinado “eliminar propietario con fuente compartida”.

**Cierre requerido:** definir la propiedad del archivo separada de su asociación,
crear una migración segura y una prueba de integración con dos bots. Eliminar A
debe conservar la fuente mientras B siga asociado; el archivo físico solo se
elimina cuando no quedan asociaciones según la política aprobada.

### AUD-02 · La identidad usada por el límite público depende del proxy del VPS

**Prioridad:** P1 alta · **Área:** RS-08 / despliegue.

El endpoint público limita diez consultas por minuto usando
`request.client.host`. Uvicorn acepta encabezados reenviados desde cualquier
dirección con `--forwarded-allow-ips='*'`, mientras Nginx concatena
`X-Forwarded-For` mediante `$proxy_add_x_forwarded_for`. El diseño es seguro solo
si Apache o el terminador TLS reemplaza la cabecera aportada por el cliente, tal
como indica la guía del repositorio. Esa condición no se verificó en el VPS.

El contador vive además en memoria de un proceso: se reinicia al recrear el
backend, no coordina réplicas y conserva una clave por cada identidad observada.
Es compatible con la única réplica actual, pero no constituye un control estable
si la cabecera puede falsificarse.

**Cierre requerido:** probar en el dominio real una solicitud con
`X-Forwarded-For` manipulado, comprobar la IP observada por FastAPI y documentar
el resultado. El proxy público debe reemplazar la cabecera antes de Nginx. Si se
añaden réplicas, se debe rediseñar el límite con un mecanismo compartido aprobado.

### AUD-03 · El despliegue migra la base sin exigir un respaldo reciente

**Prioridad:** P1 alta · **Área:** continuidad operativa.

El repositorio incluye respaldo coordinado, verificación de huellas y restauración
aislada. Sin embargo, `docker/deploy-production.sh` ejecuta las migraciones después
de levantar PostgreSQL sin crear o validar primero un respaldo. El workflow copia
el script de respaldo al VPS, pero tampoco lo invoca.

Una tarea cron diaria reduce exposición, pero no garantiza un punto recuperable
inmediatamente anterior a una migración. Tampoco existe reversión automática si
la aplicación falla después de una migración compatible solo hacia delante.

**Cierre requerido:** acordar RPO/RTO, ejecutar y validar un respaldo previo al
despliegue que aplique migraciones, conservar el SHA de la versión y ensayar la
restauración en una copia del despliegue real. El pipeline debe detenerse si el
respaldo previo falla.

### AUD-04 · Las conversaciones vencidas no tienen limpieza programada

**Prioridad:** P2 media · **Área:** privacidad y operación.

El backend rechaza memoria vencida y crea otra conversación, por lo que el modelo
no reutiliza ese historial. También existe `python -m app.cleanup_conversations`,
que elimina conversaciones vencidas y sus mensajes por cascada. No hay una tarea
en Compose, GitHub Actions ni la documentación de despliegue que programe su
ejecución.

El vencimiento funcional, por tanto, no equivale a eliminación física. Las filas
pueden crecer indefinidamente y conservar preguntas y respuestas más tiempo del
esperado.

**Cierre requerido:** aprobar una política de retención y programar el comando en
el VPS con bloqueo, registro de resultado y alerta de fallo. Añadir una comprobación
que confirme la eliminación sin afectar consultas y métricas históricas.

### AUD-05 · El token administrativo permanece legible para JavaScript

**Prioridad:** P2 media · **Área:** sesión.

El backend usa un token opaco aleatorio, almacena solo su hash, valida vencimiento
y permite revocación inmediata. El frontend guarda el token completo en
`localStorage` para conservar la sesión al recargar. Cualquier XSS ejecutado en el
origen administrativo podría leerlo.

No se observó renderizado directo de respuestas del modelo como HTML ejecutable y
el widget construye contenido dinámico mediante `textContent`, controles que
reducen el riesgo. Aun así, el repositorio no define una Content Security Policy
para el panel y las cabeceras finales del proxy público no fueron comprobadas.

**Cierre requerido:** decidir entre cookie `HttpOnly`, con su protección CSRF, o
mantener el token actual con CSP estricta y pruebas XSS. Verificar las cabeceras
reales del dominio antes de aceptar el riesgo residual.

### AUD-06 · El árbol de desarrollo del frontend conserva cinco avisos altos

**Prioridad:** P2 media · **Área:** cadena de suministro.

`npm audit --omit=dev` reporta cero vulnerabilidades. La auditoría completa reporta
cinco avisos altos en la cadena de herramientas de desarrollo asociada a
`eslint-config-next`, `fast-glob`, `micromatch` y `braces`. El arreglo automático
propuesto degrada paquetes principales a una combinación incompatible, por lo que
no debe aplicarse sin una actualización controlada.

**Cierre requerido:** actualizar Next/ESLint y sus dependencias cuando exista una
ruta compatible, volver a ejecutar lint, pruebas, build y navegador, y conservar
el resultado. El hallazgo no implica una dependencia vulnerable dentro de la
imagen standalone de producción observada.

### AUD-07 · La imagen base del frontend no está fijada por digest

**Prioridad:** P3 baja · **Área:** reproducibilidad.

PostgreSQL, Nginx, Ollama, LiteLLM y la imagen base Python están fijados con SHA-256.
Las dos etapas del Dockerfile frontend usan `node:24-alpine` sin digest. Una
reconstrucción del mismo commit puede recibir una base distinta.

**Cierre requerido:** fijar un digest compatible para ambas etapas y actualizarlo
mediante un cambio de dependencia probado. Las imágenes de aplicación desplegadas
sí usan la etiqueta inmutable del SHA de Git.

### AUD-08 · El estado local no es una unidad de entrega reproducible

**Prioridad:** P3 baja · **Área:** trazabilidad de versión.

La auditoría observó 172 archivos modificados o eliminados y 27 rutas no
rastreadas sobre `cc4b5711f479`. El pipeline de producción solo publica una revisión
fusionada y aprobada, por lo que estos cambios no forman todavía una versión que
otra persona pueda obtener desde GitHub y repetir exactamente.

**Cierre requerido:** separar o revisar los cambios, ejecutar nuevamente los gates,
crear commits convencionales y abrir el PR correspondiente. No se debe desplegar
directamente este árbol local.

## Controles aprobados

| Control           | Evidencia del 18 de octubre                                                                                                   |
| ----------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| Backend           | Ruff check y format aprobados; 111 pruebas deterministas aprobadas, 4 externas excluidas.                                     |
| Frontend          | Prettier, ESLint, 30 pruebas Vitest, TypeScript y build de Next aprobados.                                                    |
| Widget            | Build y `node --check` aprobados.                                                                                             |
| OpenSpec          | 8 cambios validados en modo estricto, 0 fallos.                                                                               |
| Compose           | Desarrollo, producción CPU y superposición GPU válidos. Producción exige límites e `IMAGE_TAG`.                               |
| Secretos          | No se encontraron claves privadas o tokens con los patrones revisados; solo `.env.example` está rastreado.                    |
| Dependencias web  | 0 avisos en producción; 5 altos limitados al árbol de desarrollo.                                                             |
| Red de producción | Solo Nginx publica `127.0.0.1`; frontend, backend, PostgreSQL, Ollama y LiteLLM quedan internos.                              |
| Contenedores      | Backend y frontend se ejecutan como usuarios sin privilegios; imágenes de terceros están fijadas por digest.                  |
| CI/CD             | CI en PR a `develop`/`production`; publicación solo tras PR aprobado de `develop` a `production`, revisión exacta y merge.    |
| API               | Endpoints administrativos requieren sesión; errores de proveedor y fallos internos se traducen a mensajes públicos genéricos. |
| Memoria           | Aislada por chatbot y origen, con TTL, máximos de turnos/caracteres y persistencia solo de turnos completados.                |

## Pruebas externas y validaciones pendientes

Las cuatro pruebas marcadas `external` consultan Ollama real para visión y
guardrails en documentos, página e imagen. Se excluyen del gate determinista y no
se repitieron en esta auditoría. Las actas existentes registran pruebas reales de
Ollama, OpenAI, OpenRouter y Vertex en fechas y entornos concretos; no garantizan
disponibilidad futura ni el comportamiento del VPS.

Antes de aceptar producción faltan, como mínimo:

1. resolver AUD-01 y añadir su regresión;
2. ejecutar respaldo y restauración en una copia del VPS;
3. comprobar TLS, CORS y encabezados reenviados en el dominio real;
4. confirmar permisos y retención de `.env`, credencial Vertex, logs y respaldos;
5. ejecutar una consulta textual, multimodal y RAG por cada proveedor habilitado,
   registrando modelo ejecutado, duración y métrica;
6. verificar la limpieza programada de conversaciones vencidas;
7. repetir CI y aceptación de navegador sobre el commit final.

## Orden recomendado

```text
Integridad de fuentes compartidas
            |
            v
Respaldo previo + restauración aislada
            |
            v
Proxy real, TLS e identidad del cliente
            |
            v
Retención de memoria + cabeceras de sesión
            |
            v
Dependencias y reproducibilidad
            |
            v
PR aprobado y aceptación final en VPS
```

Este orden protege primero los datos, después la capacidad de recuperación y
finalmente la superficie pública. No requiere introducir otra base de datos,
broker, framework o arquitectura de microservicios.
