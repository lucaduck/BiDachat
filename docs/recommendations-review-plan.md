# Revisión crítica y plan de comprobación de recomendaciones

Fecha: 12 de octubre de 2026. Base de código revisada: `10a01bf`.

Documento evaluado: `RECOMENDACIONES_TESIS_PATRICIO.md`, proporcionado por el usuario. Este informe establece un plan; no aprueba automáticamente sus recomendaciones ni modifica los requisitos del sistema.

## 1. Dictamen y límites de la revisión

El documento identifica oportunidades reales en extracción documental, configuración de visión y evaluación experimental. Sin embargo, mezcla defectos, hipótesis de rendimiento, funcionalidades nuevas y configuraciones de un servidor que todavía deben verificarse. No conviene ejecutar sus ejemplos directamente.

La evaluación inicial fue estática: código, SRS, configuración de despliegue y evidencia de pruebas existente. Las comprobaciones posteriores, sus cambios y sus límites se registran al final y en [la evidencia del 15 de octubre](qa/recommendations/validation-2026-10-15.md). Un hallazgo en el código no equivale a una prueba de aceptación en producción.

La aplicación completa es el objetivo vigente. Debe corregirse la caracterización del proyecto como MVP. La calidad de la tesis debe sustentarse en trazabilidad, decisiones justificadas y resultados reproducibles; los calificativos sobre excelencia no constituyen evidencia.

Referencias internas principales:

- [SRS](../SRS.md): requisitos y criterios de aceptación.
- [Procesamiento documental](../backend/app/services/document_processing_service.py): extracción, descripción visual y fragmentación.
- [Conocimiento y recuperación](../backend/app/services/rag_knowledge_service.py): asociaciones, bloqueo y búsqueda.
- [API de chatbots y documentos](../backend/app/api/chatbots.py): carga y reintento.
- [Servicio conversacional](../backend/app/services/conversation_service.py): contexto y elección de proveedor.
- [Configuración de Next.js](../frontend/next.config.ts): cabeceras de fuentes.
- [Compose de producción](../docker-compose.production.yml), [inicialización SQL](../docker/postgres/init-database.sh) y [despliegue](../docker/deploy-production.sh).
- [Aceptación RAG del 6 de octubre](qa/rag/acceptance.md): pruebas locales históricas, con limitaciones expresas. No sustituyen la aceptación del VPS ni cubren todas las tablas y casos complejos.

## 2. Evaluación de cada recomendación

Prioridades propuestas: **P0**, condición para un despliegue verificable; **P1**, corrección funcional o protección del flujo aprobado; **P2**, optimización sujeta a mediciones; **P3**, ampliación opcional. La evaluación académica empieza desde la línea base, aunque sus resultados finales lleguen después.

| Sección                        | Evaluación crítica                                                                                                                                                                                              | Decisión propuesta                                                                                                                                                                                                                              |
| ------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2.1 Puertos                    | Producción ya publica únicamente Nginx en `127.0.0.1:${FRONTEND_PORT}:80`. Backend y PostgreSQL no necesitan puertos del host. Cambiar puertos no demuestra aislamiento.                                        | Implementado: mantener internos DB, backend y Ollama; seleccionar `FRONTEND_PORT` según un puerto libre del VPS y apuntar allí el proxy público. Verificar en el host.                                                                          |
| 2.1 Recursos                   | Los límites de CPU/RAM propuestos carecen de medición. Además, omiten a Ollama, identificado como riesgo principal. La ausencia de `nvidia-smi` por sí sola no prueba la ausencia de hardware acelerador.       | Implementado: límites obligatorios en ambos Compose para los cinco servicios. P0 pendiente: medir carga y memoria del VPS, definir sus diez valores y verificar límites efectivos en Docker.                                                    |
| 2.2 Proxy/TLS                  | El patrón proxy del host → Nginx contenedor encaja con el proyecto. El dominio, rutas y proxy del documento no están confirmados. Los 600 segundos propuestos no constituyen un presupuesto de tiempo validado. | P0: adaptar el proxy existente, verificar TLS, cabeceras, cookies, tamaños y tiempos entre todos los saltos.                                                                                                                                    |
| 2.3 Fuentes/CORS               | Next.js ya configura `Access-Control-Allow-Origin: *` para `/fonts/:path*`. No está demostrado el supuesto defecto crítico.                                                                                     | Verificar desde otro origen a través del proxy real. Modificar solo si falla; evitar cabeceras duplicadas. Cachear un año con `immutable` exige versionar la URL del recurso.                                                                   |
| 2.4 Respaldos                  | Necesarios, pero el ejemplo usa Compose de desarrollo, credenciales/rutas fijas y nombre de volumen supuesto. Dos archivos generados no demuestran una restauración consistente.                                | P0: preparar respaldo coordinado, validación, restauración aislada y retención limitada a conjuntos completos. No usar el script literalmente.                                                                                                  |
| 3.1 DOCX                       | Confirmado: el extractor solo recorre párrafos. El ejemplo agrega todas las tablas al final, perdiendo su posición en el documento.                                                                             | P1: conservar el orden de párrafos y tablas, encabezados y relación entre celdas. Probar documentos con datos presentes únicamente en tablas.                                                                                                   |
| 3.1 PDF                        | Se usa extracción de texto; la conservación de relaciones tabulares no está garantizada. No puede afirmarse que todo PDF pierda todas sus tablas.                                                               | P1: construir casos representativos y medir fallos. Evaluar otra biblioteca únicamente si los casos justifican la dependencia. Separar PDF digital y PDF escaneado.                                                                             |
| 3.2 Visión                     | Confirmado: las imágenes como fuentes se describían con `provider="ollama"` y `OLLAMA_MODEL`, independientemente del modelo conversacional.                                                                     | Implementado: `VISION_PROVIDER` y `VISION_MODEL` separan la descripción de fuentes visuales. El valor por defecto conserva Ollama; una API externa se selecciona explícitamente y requiere su clave. Mantener separado el perfil de embeddings. |
| 3.3 CSV                        | Confirmado: se interpreta como texto y se aplica fragmentación genérica. Puede separar filas y encabezados. La mejora “drástica” es una hipótesis.                                                              | P1: procesar filas con contexto de columnas; probar comillas, delimitadores, saltos de línea, valores vacíos y filas grandes. Comparar recuperación antes/después.                                                                              |
| 3.4 Búsqueda híbrida           | Es razonable para códigos exactos, pero FTS de PostgreSQL no equivale automáticamente a BM25. Sumar puntuaciones sin calibrarlas introduce otra fuente de error.                                                | P2: demostrar primero fallos de recuperación; comparar búsqueda vectorial, lexical e híbrida. Evaluar fusión por rangos o normalización justificada y revisar tokenización de códigos.                                                          |
| 4.1 HNSW                       | No se observa índice vectorial en las migraciones revisadas. Esto no demuestra que cada consulta recorra toda la tabla ni que la búsqueda sea el cuello de botella.                                             | P2: usar `EXPLAIN (ANALYZE, BUFFERS)` en un entorno de prueba y medir latencia, memoria y calidad de recuperación antes de decidir.                                                                                                             |
| 4.2 Documentos compartidos     | La recuperación ya consulta `chatbot_documents`; el diagnóstico general del documento es demasiado amplio. Existe una inconsistencia concreta en el reintento desde un bot asociado.                            | P1: reproducir y corregir ese recorrido, preservando aislamiento y bloqueo. No sustituir filtros indiscriminadamente.                                                                                                                           |
| 5.1 Inyección de instrucciones | Quitar etiquetas HTML y añadir XML no garantiza protección frente a instrucciones maliciosas en texto o imágenes.                                                                                               | P1: minimizar contexto, tratarlo como datos no confiables y probar ataques indirectos, aislamiento y presentación segura de respuestas. Registrar límites de la defensa.                                                                        |
| 5.2 Errores normalizados       | RFC 7807 fue sustituido por RFC 9457. Adoptar Problem Details es una decisión de contrato; no es requisito universal para que una API sea REST.                                                                 | P3: inventariar errores y consumidores. Priorizar coherencia y ausencia de datos sensibles; migrar el formato solo si hay una necesidad aprobada.                                                                                               |
| 6.1 Espera y reintento         | El widget ya muestra “Procesando consulta…” y recupera el formulario ante errores. No se observa `AbortController` en ese archivo. Un corte fijo a 60 s puede romper consultas locales válidas.                 | P1: definir presupuesto total y estados de fallo; distinguir cancelación del navegador de cancelación de inferencia y evitar duplicados por reintentos.                                                                                         |
| 6.2 Valoraciones               | Es una funcionalidad nueva. La satisfacción voluntaria no demuestra exactitud factual y tiene sesgo de participación.                                                                                           | P3: aprobar alcance/SRS antes de añadir tabla o endpoint. Definir quién vota, duplicados, abuso y denominador de la métrica.                                                                                                                    |
| 7.1 Evaluación RAG             | Es pertinente; 30 preguntas y umbrales 0,85/0,80/0,75 no quedan justificados en el documento. RAGAS no sustituye referencias correctas ni revisión humana.                                                      | Iniciar en fase 0: diseñar conjunto y rúbrica; justificar muestra y umbrales antes de medir resultados finales.                                                                                                                                 |
| 7.2 Comparación de modelos     | La tabla de segundos y porcentajes no incluye mediciones verificables. La conclusión favorece APIs antes de ejecutar el experimento. El procesamiento propio sigue usando CPU aun con inferencia externa.       | Retirar esas cifras del diagnóstico. Medir modelos concretos, calidad, latencia, costo y recursos con condiciones controladas.                                                                                                                  |
| 7.3 SUS                        | SUS aporta una medida de usabilidad percibida. Superar 68 no constituye una certificación científica ni un porcentaje de éxito.                                                                                 | Diseñar tareas reales, muestra y tratamiento de incertidumbre. Complementar con finalización de tareas, errores y observaciones.                                                                                                                |
| 8 Priorización                 | Incluye como obligatorios arreglos no demostrados y propone compilar en el VPS pese al despliegue previsto con GHCR.                                                                                            | Sustituir por las fases de este plan. Mantener imágenes identificadas por commit, PR aprobado y procedimiento de reversión.                                                                                                                     |

La búsqueda aproximada intercambia parte de la recuperación exacta por velocidad; debe evaluarse también con filtros por chatbot. Véase la [documentación de pgvector](https://github.com/pgvector/pgvector#filtering). PostgreSQL describe sus funciones `ts_rank` y `ts_rank_cd` en [su documentación de búsqueda textual](https://www.postgresql.org/docs/current/textsearch-controls.html#TEXTSEARCH-RANKING). La norma actual de errores es [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457.html).

El mapa inicial también menciona OCR, fragmentación semántica, reranking, Prometheus y auditoría de dependencias sin desarrollarlos. OCR requiere alcance explícito; fragmentación y reranking deben demostrar beneficio; primero se aprovecharán métricas y registros existentes antes de añadir infraestructura de observabilidad. La auditoría de dependencias debe actualizar evidencia sobre las versiones realmente desplegadas.

### Corrección aplicada al punto 2.1

La [configuración de producción](../docker-compose.production.yml) deja sin publicación al backend, PostgreSQL, frontend y Ollama. `BACKEND_PORT` y `POSTGRES_PORT` pertenecen al Compose de desarrollo; no deben copiarse como medidas de seguridad al despliegue del VPS. Solo `FRONTEND_PORT` define un puerto del host, ligado a `127.0.0.1`; el proxy HTTPS del host debe usar ese mismo valor. El puerto 3005 del documento original es una posibilidad, no una obligación. Antes de cambiarlo hay que comprobar que está libre y actualizar el proxy externo en la misma operación.

Los límites viven ahora en el [Compose de desarrollo](../docker-compose.yml) y en el [Compose de producción](../docker-compose.production.yml). Ambos requieren CPU y memoria para Ollama, backend, frontend, Nginx y PostgreSQL. El [despliegue](../docker/deploy-production.sh) valida la configuración antes de descargar imágenes o recrear servicios. El `.env.example` ofrece valores iniciales para el entorno de desarrollo, cuyo runtime ve 7,7 GiB de RAM. El VPS tiene 4 CPU virtuales y 7,8 GiB de RAM, compartidos con otros servicios; todavía faltan valores efectivos de los diez límites y una prueba de carga allí. La [guía de despliegue](deployment/github-actions.md#puertos-y-recursos-en-un-vps-compartido) indica cómo elegir y verificar los valores.

## 3. Hallazgos adicionales que condicionan el plan

### 3.1 Reintento de documentos compartidos

Recorrido identificado por lectura del código:

1. La ruta de reintento obtiene el documento mediante su asociación con el chatbot B.
2. Llama al procesador con el identificador de B.
3. `begin_processing()` llama a `_get_locked_document()`.
4. Este último exige `Document.chatbot_id == B`, aunque el propietario original sea A.

La condición permite anticipar un fallo; su respuesta HTTP exacta debe reproducirse. El reindexador por consola utiliza el propietario original, por lo que no corresponde atribuirle automáticamente el mismo problema. Debe definirse y comprobarse el efecto de reprocesar una fuente que comparten varios bots, incluida la concurrencia.

### 3.2 Aplicación de migraciones

El inicializador de PostgreSQL enumera las migraciones 001–004. Se monta como script de inicialización del volumen. Añadir una migración 005 no actualiza por sí solo bases existentes ni la incorpora a esa lista.

Antes de cambios de esquema: definir ejecución versionada, orden, registro de aplicación, manejo de fallo y restauración. Comprobar instalación vacía y actualización de una copia con datos. Evitar resolverlo eliminando volúmenes.

### 3.3 Confusión entre tres modelos

El modelo de conversación, el de descripción visual y el de embeddings tienen funciones distintas. La opción CPU no garantiza que el modelo escogido comprenda imágenes. Tampoco la falta de GPU impide conceptualmente usar un modelo visual: hay que comprobar capacidades y recursos.

Cambiar el modelo conversacional no debe obligar a regenerar todos los embeddings. Cambiar el perfil de embeddings sí exige tratar la compatibilidad y reindexación de las fuentes.

### 3.4 Comparación experimental sesgada por configuración

El servicio conversacional recupera actualmente `top_k=2` para Ollama y `top_k=5` para otros proveedores. Comparar directamente sus respuestas confunde la capacidad del modelo con la cantidad de contexto recibido.

Se requieren dos experimentos distintos: modelos con el mismo contexto para comparar generación; configuraciones completas de la aplicación para comparar utilidad operacional. Ambos deben informar su configuración.

## 4. Plan de trabajo y condiciones de salida

### Fase 0 — Inventario y línea base

**Objetivo:** establecer qué existe, qué falla y cómo se medirá la mejora.

- [ ] Confirmar VPS, dominio, ruta de despliegue, proxy existente, CPU/RAM/disco y GPU disponible. El documento propone `/home/uprocach/TESIS-PATRICIO`; la conversación previa indica `/home/lucaduck/domains/bidachat.lucaduck.com/docker/bidachat`.
- [ ] Identificar imagen/commit realmente desplegado y diferencias con `10a01bf`; registrar configuración sin secretos.
- [ ] Mapear cada hallazgo a requisito, caso de uso y criterio de aceptación. Clasificar cambios nuevos antes de incorporarlos al SRS.
- [ ] Reutilizar fixtures y ejecutores existentes; añadir casos ausentes sin borrar recursos del usuario.
- [ ] Diseñar corpus con tablas DOCX/PDF, CSV, imágenes, códigos exactos, contexto de página, preguntas sin respuesta y fuentes compartidas.
- [ ] Registrar respuesta esperada, evidencia que la sustenta y modalidad de cada caso; separar conjunto de ajuste y evaluación final.
- [ ] Medir línea base por etapa: extracción, embeddings, búsqueda, inferencia y tiempo total percibido por el cliente. Incluir errores y consultas agotadas, no solo éxitos.

**Salida:** inventario verificado, matriz de pruebas y resultados iniciales versionados. Los números del documento original no se incorporan como resultados.

### Fase 1 — Despliegue recuperable y aislamiento

**Dependencia:** inventario de fase 0. **Trazabilidad:** RNF-03, RNF-14, RNF-15, RS-03 y RS-04.

- [ ] Comprobar configuración efectiva de producción, red interna y puertos desde el host y otro equipo.
- [ ] Validar TLS, cabeceras reenviadas y sesión a través del proxy existente y Nginx contenedor.
- [ ] Probar widget y fuentes desde una página de otro origen permitido; comprobar rechazo de origen no permitido sin tratar CORS como autenticación.
- [ ] Establecer presupuesto de recursos considerando al resto de servicios y a Ollama; medir ingestión e inferencia simultáneas.
- [ ] Preparar respaldo de base y archivos con una estrategia explícita de consistencia, permisos restrictivos, manifiesto y verificación de integridad.
- [ ] Restaurar en volúmenes aislados y verificar login, bots, asociaciones, archivos y recuperación. Definir pérdida de datos y tiempo de recuperación tolerables con el responsable.
- [ ] Definir mecanismo mínimo de actualización de esquema y probar una migración en una copia con datos.
- [ ] Verificar pipeline conforme al flujo de PR aprobado, imágenes GHCR por commit y reversión compatible con el esquema. No reconstruir arbitrariamente producción en el VPS.

**Salida:** restauración demostrada, servicios internos no publicados y actualización ensayada sin pérdida de datos. Un healthcheck exitoso no basta.

### Fase 2 — Exactitud de ingestión y fuentes compartidas

**Dependencia:** línea base; respaldo/migraciones si cambia persistencia. **Trazabilidad:** RF-09, RF-13–RF-17, RS-06, RS-07 y CA-UC04.

- [ ] Reproducir reintento desde B sobre documento fallido de A; comprobar rechazo para C sin asociación.
- [ ] Corregir autorización por asociación y mantener exclusión de procesamiento simultáneo. Probar retiro de asociación y preservación de archivos compartidos.
- [ ] Incorporar extracción DOCX en orden documental; conservar relación encabezado/celda y manejar tablas vacías o combinadas según casos soportados.
- [ ] Incorporar CSV estructurado y fragmentación que mantenga contexto de columnas dentro del límite de entrada.
- [ ] Evaluar PDF con tablas mediante fixtures; adoptar extractor adicional solo si resuelve fallos y su costo operativo es aceptable.
- [ ] Establecer configuración explícita de visión y validar combinaciones admitidas; probar PNG, JPEG, WebP, ausencia de proveedor y modelo sin capacidad visual.
- [ ] Reprocesar únicamente los fixtures y las fuentes seleccionadas para migración; registrar versión del tratamiento cuando sea necesaria para reproducibilidad.

**Salida:** datos conocidos recuperables con su significado, fallos honestos para archivos no soportados e independencia entre fuentes de distintos chatbots. No prometer OCR de PDF escaneado por admitir imágenes.

### Fase 3 — Resiliencia y contexto no confiable

**Dependencia:** línea base y presupuesto de tiempos. **Trazabilidad:** RF-22, RF-30, RF-31, RNF-09, RS-05, RS-07–RS-09.

- [ ] Alinear tiempos del proveedor, backend, ambos proxies y cliente usando el recorrido completo, no un valor aislado de 60 segundos.
- [ ] Probar proveedor lento, desconexión, timeout, error de API y reintento; definir tratamiento de consultas cuyo resultado no llegó al navegador.
- [ ] Verificar que el usuario conserva texto/adjunto y que un fallo queda registrado con estado final correcto.
- [ ] Probar instrucciones maliciosas en página, documentos e imágenes, delimitadores manipulados y contenido HTML en respuestas.
- [ ] Verificar selección mínima de contexto, exclusión de formularios/secretos, aislamiento de recuperación y ausencia de ejecución de HTML.
- [ ] Revisar errores y límites de abuso; conservar contratos de consumidores salvo cambio justificado.

**Salida:** pruebas de regresión del flujo conversacional, fallos identificables y límites de protección documentados. El filtrado de etiquetas y la separación estructurada son defensas parciales; [OWASP](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html) describe defensa en profundidad y evaluación de resultados.

### Fase 4 — Optimización con experimentos controlados

**Dependencia:** ingestión correcta y línea base estable. **Trazabilidad:** RF-16, RNF-06, RNF-07 y RNF-11.

- [ ] Identificar la etapa dominante antes de optimizar; separar arranque frío de ejecución con modelo cargado.
- [ ] Evaluar HNSW frente a búsqueda exacta con tamaños y distribución por chatbot representativos; registrar planes SQL, p50/p95, memoria y recuperación de vecinos.
- [ ] Medir relevancia respecto a respuestas de referencia además de coincidencia con vecinos exactos: un vecino exacto no garantiza evidencia útil.
- [ ] Comparar búsqueda vectorial/lexical/híbrida para códigos y lenguaje natural; ajustar solo sobre el conjunto de desarrollo.
- [ ] Evaluar cambios de fragmentación o reranking únicamente si queda un fallo concreto no resuelto.
- [ ] Conservar una alternativa solo si su mejora medida justifica costo, complejidad y posible pérdida de recuperación. Fijar el criterio de decisión antes de la evaluación final.

**Salida:** decisión documentada por experimento, incluso si el resultado es conservar la implementación actual. No existe obligación de añadir HNSW o búsqueda híbrida para demostrar calidad de ingeniería.

### Fase 5 — Evaluación académica final

**Dependencia:** protocolo iniciado en fase 0 y versión congelada tras correcciones. **Trazabilidad:** RNF-06, RNF-07, RNF-11, UC-06–UC-08.

- [ ] Evaluar respuestas con referencias comprobadas y rúbrica humana de exactitud, relevancia, sustento y reconocimiento de falta de información.
- [ ] Distinguir recuperación documental, comprensión de página y comprensión visual; evaluar sustento contra todo el contexto legítimo suministrado.
- [ ] Si se usa RAGAS, fijar versión, métricas, modelo evaluador, entradas y costos; contrastar una muestra con evaluación humana y revisar discrepancias.
- [ ] Justificar tamaño del conjunto y umbrales con objetivos de tesis; 30 preguntas puede ser un piloto, no una garantía de representatividad.
- [ ] Comparar modelos con idéntico contexto y parámetros compatibles, y por separado comparar configuraciones operacionales completas. Registrar identificadores efectivos, tokens, hardware, calentamiento y concurrencia.
- [ ] Publicar número de observaciones, dispersión, errores, costos y limitaciones junto con promedios y percentiles. Un modelo local no tiene tarifa por token de proveedor, pero sí costo de recursos.
- [ ] Realizar tareas de usuario y SUS; informar muestra e incertidumbre. La interpretación de muestras pequeñas exige cuidado, como documenta este [estudio metodológico sobre SUS](https://arxiv.org/abs/2101.00455).

**Salida:** tablas y gráficos derivados de ejecuciones trazables. Las conclusiones se redactan después de los resultados y pueden mostrar que no hubo mejora.

### Fase 6 — Cierre y aceptación

- [ ] Relacionar requisito → caso → prueba → evidencia → cambio/PR.
- [ ] Ejecutar pruebas afectadas, formato y lint; repetir regresiones críticas de login, configuración, asociación, consulta desde otra página y métricas.
- [ ] Actualizar documentación existente de despliegue, límites y resultados; evitar duplicar manuales.
- [ ] Verificar la versión liberada en el entorno destino y dejar pendientes explícitos cuando falte evidencia.

**Salida:** acta de aceptación con alcance real, limitaciones y procedimiento de recuperación.

## 5. Reglas para ejecutar el plan

1. Trabajar por cambio pequeño: reproducir → corregir → probar → comparar → registrar. Volver a corregir si falla un criterio afectado.
2. Mantener REST sobre HTTP, PostgreSQL/pgvector y backend modular. Estas recomendaciones no requieren WebSocket ni microservicios.
3. Mantener backend, base y almacenamiento en infraestructura controlada; solo las API de IA configuradas pueden ser integraciones externas de ejecución.
4. No añadir dependencias, feedback, OCR ni nuevos contratos sin necesidad y alcance aprobados. Una herramienta de evaluación no debe convertirse por defecto en dependencia de producción.
5. Usar datos sintéticos o autorizados, limpieza acotada a fixtures y presupuesto definido antes de experimentos con API externas. No cargar documentos privados a herramientas de evaluación sin autorización.
6. Conservar cada ejecución, incluso fallida, con fecha, commit, configuración, modelo efectivo y resultado. La evidencia histórica no se reemplaza por resultados nuevos.
7. Estimar esfuerzo por bloque después de inventariar corpus y servidor. No prometer una duración ni un umbral de respuesta sin esa base.

## 6. Primera entrega propuesta

Completar el inventario y conjunto de regresión de fase 0. Los primeros casos técnicos serán: reintento de documento compartido, DOCX con tabla, CSV con encabezados separados por fragmentación e imagen como fuente bajo la configuración CPU prevista. En paralelo al inventario, definir restauración y actualización de esquema antes de intervenir el VPS.

**Avance del 13 de octubre de 2026:** [la línea base](qa/recommendations/baseline-2026-10-13.md) reprodujo y corrigió los casos de extracción DOCX y CSV; se añadió una regresión para reintento compartido y scripts para respaldo coordinado y verificación de restauración aislada. [La revisión de guardrails](qa/recommendations/guardrails-review-2026-10-13.md) identifica los controles existentes y sus límites. El motor Docker no respondió en este entorno, por lo que la integración PostgreSQL, la prueba de restauración real, el CORS por proxy y la medición por etapa continúan pendientes. No se modificó el VPS ni el SRS en esta entrega.

**Avance del 15 de octubre de 2026:** [la comprobación local y el inventario del VPS](qa/recommendations/validation-2026-10-15.md) confirman pruebas backend aprobadas, ingestión y recuperación con fixtures sintéticos, visión real con Ollama para PNG/JPEG/WebP, pruebas adversariales de documento, página e imagen con un modelo local y respaldo/restauración aislados. Se configuró por separado el proveedor de descripción de imágenes y se corrigieron los permisos de la ruta y `.env` para `despliegue`. El workflow transfiere el commit aprobado por SSH sin exigir un checkout Git en el VPS. El VPS aún no ejecuta BIDACHAT: faltan acceso SSH de despliegue, límites efectivos de recursos y proxy Apache. Siguen abiertos el ensayo operacional en el VPS, el corpus académico completo, pruebas adversariales más variadas y por proveedor externo, y las decisiones de optimización basadas en mediciones.

**Decisión para el VPS del mismo día:** el usuario eligió OpenAI para describir
fuentes visuales. Se configuró `gpt-5.6-luna` como modelo visual y se agregaron
los diez límites exigidos al `.env` de producción. Su seguridad operativa aún
depende de medir consumo real de memoria y concurrencia. El usuario confirmó
que su equipo todavía no tiene acceso SSH; siguen pendientes la clave de
`despliegue` para GitHub Actions, el PR aprobado, el proxy Apache, el despliegue
y la aceptación extremo a extremo.

La llamada visual real con la clave configurada devolvió `401 invalid_api_key`;
la clave local también fue rechazada. El proveedor visual quedó seleccionado,
pero su aceptación externa está pendiente de una credencial válida y de una
prueba que registre modelo, respuesta y consumo dentro del presupuesto acordado.
