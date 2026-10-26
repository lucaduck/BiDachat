# Evidencia de aceptación: memoria, Preview y catálogo Vertex

Fecha de ejecución local: **16 de octubre de 2026**.

## Alcance comprobado

- Memoria textual anónima con UUID, aislamiento por chatbot y origen, expiración y límites.
- Contexto visible actual de `#preview-dashboard` en cada turno.
- Catálogo explícito de Vertex con `gemini-3.1-flash-lite` y `gemini-3.5-flash`.
- Conservación del modelo ejecutado en consultas históricas.
- Migración de una base existente y creación completa de una base vacía.

## Resultados

| Comprobación                               | Resultado                                                                          |
| ------------------------------------------ | ---------------------------------------------------------------------------------- |
| Backend completo                           | 111 pruebas aprobadas, 4 omitidas por condiciones documentadas.                    |
| Frontend unitario                          | 30 pruebas aprobadas durante la imagen de producción.                              |
| Playwright completo                        | 23 pruebas aprobadas.                                                              |
| Playwright tras el ajuste final del widget | 2 pruebas focalizadas aprobadas: host externo y Preview.                           |
| Ruff                                       | 78 archivos válidos y formateados.                                                 |
| Next.js                                    | lint, TypeScript y compilación de producción aprobados.                            |
| Compose                                    | perfiles CPU, GPU y Vertex válidos.                                                |
| OpenSpec                                   | validación estricta aprobada.                                                      |
| Salud local                                | Nginx devolvió `{"status":"ok"}` y todos los servicios requeridos estaban activos. |

La aceptación real de tres turnos con `gemini-3.1-flash-lite` recordó el nombre **Patricio**, evitó volver a pedirlo y respondió **89,4 %** con el contexto de Preview. Los tiempos integrales almacenados fueron 36636 ms, 6377 ms y 4579 ms. El chatbot temporal se eliminó al terminar.

La medición comparativa posterior ejecutó 30 pares alternados, sin fallos. Los datos completos están en [conversation-memory-latency-2026-10-16.json](conversation-memory-latency-2026-10-16.json). El tramo FastAPI–LiteLLM–Vertex obtuvo:

| Condición   |        Contexto |   Mediana |        p95 |
| ----------- | --------------: | --------: | ---------: |
| Sin memoria | 1291 caracteres | 830,66 ms | 1375,24 ms |
| Con memoria | 1377 caracteres | 781,75 ms | 1291,95 ms |

La muestra describe este entorno local. No demuestra que la memoria reduzca la latencia y no define un SLA de producción.

## Consumo observable

- `gemini-3.5-flash`, texto: 5 tokens de entrada y 97 de salida, incluidos 95 de razonamiento.
- Imagen roja con `gemini-3.5-flash`: 1099 tokens de entrada y 121 de salida, incluidos 119 de razonamiento.
- Imagen roja con `gemini-3.1-flash-lite`: 1099 tokens de entrada y 2 de salida.
- Medición de memoria: un calentamiento excluido y 60 generaciones cortas. El gateway usado por la aplicación no devuelve el uso a esta capa, por lo que el costo y los tokens exactos deben contrastarse en Facturación de Google Cloud. No se afirma un valor monetario sin ese registro.

Las ejecuciones se acotaron a las llamadas anteriores para respetar el límite de **USD 1** autorizado. El cliente no informa el costo monetario consolidado, por lo que el cumplimiento definitivo del límite debe contrastarse con el registro de Facturación de Google Cloud.

## Migración y reversión

`docker/postgres/migrate-database.sh`:

1. reconoció y registró las cinco migraciones de la base local existente;
2. fue idempotente al ejecutarse nuevamente;
3. creó las cinco migraciones sobre una base temporal vacía;
4. verificó cinco registros y doce tablas, incluidas once de dominio y una de control;
5. eliminó la base temporal al finalizar.

El corredor detiene el despliegue ante una migración parcialmente aplicada. La reversión de `005` fue probada previamente en una base aislada; en producción requiere respaldo y autorización porque elimina la memoria retenida.

## Limitaciones y acciones externas

- La política institucional debe confirmar o reducir los valores provisionales de 24 horas, 12 turnos y 12000 caracteres.
- La medición excluye transporte del navegador, PostgreSQL, embeddings y recuperación RAG.
- No se ha realizado despliegue desde un PR aprobado ni smoke contra el VPS porque este equipo todavía no tiene acceso SSH.
- La facturación de Google Cloud puede aparecer con retraso; debe revisarse antes de ampliar pruebas o tráfico.

## Smoke requerido después del PR aprobado

1. Confirmar contenedores sanos y `GET /api/v1/health` por HTTPS.
2. Iniciar sesión y comprobar el catálogo Vertex por proveedor y modelo.
3. Abrir Preview, indicar un nombre y verificar que el siguiente turno lo recuerde.
4. Cambiar un KPI visible y confirmar que la consulta posterior recibe el nuevo valor.
5. Cargar el widget desde un origen incluido en `WIDGET_ALLOWED_ORIGINS` y repetir dos turnos.
6. Verificar en métricas el estado, modelo ejecutado y tiempo de las consultas.
7. Ejecutar la limpieza controlada y confirmar que las consultas históricas permanecen.

Solo después de este smoke y de aprobar la retención se puede cerrar y archivar el cambio OpenSpec.

## Aislamiento y limpieza: comprobación local del 18 de octubre de 2026

- La migración `006` se aplicó, revirtió y volvió a aplicar en PostgreSQL temporal; el corredor de migraciones también se ejecutó dos veces. Después se aplicó a la base de desarrollo tras generar y comprobar un respaldo.
- Las pruebas de backend comprobaron firmas por chatbot y origen, caducidad, manipulación, aislamiento de identidades, conservación de consultas y reintento de la limpieza. La generación del token del sitio se verificó con el ejemplo documentado. No se consultó a ningún proveedor de IA en estas pruebas.
- Playwright verificó reinicio manual, reinicio por inactividad, rechazo al no poder verificar identidad y supresión de una respuesta en curso al cambiar la sesión del sitio. El servidor anfitrión y las respuestas de API se simularon en el navegador; queda pendiente una aceptación con un sitio autenticado real y su propia implementación del endpoint de identidad.
- La política institucional de retención y la aceptación en producción continúan pendientes. Las consultas conservadas en `queries` requieren una política de retención separada.
