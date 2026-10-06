## Context

Ver [proposal.md](proposal.md) para motivación y alcance. Base del 6 de octubre: 19 pruebas de navegador, 23 unitarias frontend y 15 backend afectadas; RAG TXT y widget externo reales aprobados. La inferencia visual con `qwen3-vl:2b` falló; la variante instructiva respondió. No se ha ejecutado aquí una auditoría exhaustiva de seguridad ni una prueba de producción pública.

Hallazgos específicos del código:

- `frontend/package.json`: Next.js 16.1.4; dependencias fijadas y lockfile. El árbol de producción tiene cuatro paquetes con avisos; el conteo no demuestra exposición de cada ruta.
- `frontend/next.config.ts`: proxy de `/api/v1` hacia FastAPI y timeout de 900 s. Construcción standalone y usuario no privilegiado en Docker.
- `backend/app/llm/provider.py`: límites Ollama `num_predict=512`, `think=false`, `keep_alive=0`; `Settings` permite contexto y timeout configurables. Pruebas del proveedor usan transportes simulados.
- `DocumentProcessingService`: describe imágenes mediante `settings.ollama_model`, distinto del modelo seleccionado para la conversación; después divide y genera embeddings. Usar instruct solo en un chatbot no corrige automáticamente las imágenes como conocimiento.
- Carga documental: acepta y confirma el archivo, confirma estado de procesamiento y espera al proveedor dentro de la petición. Publicación de chunks y fallo se gestionan en servicios existentes.
- `DashboardSummary`: documentos y métricas por chatbot, patrón de listado inicial más 2N solicitudes.
- Sesión: token en memoria y localStorage. Respaldos/restauración documentados; `.github/workflows/` no existe en este checkout.

## Goals / Non-Goals

**Goals:**

- Cerrar defectos reproducibles mediante cambios pequeños, evidencia por criterio y reversión identificable.
- Mantener clientes → API → servicios → PostgreSQL/pgvector y proveedores en backend.
- Separar comprobaciones automáticas, llamadas reales, trabajo humano y condiciones de publicación.

**Non-Goals:**

- Introducir una segunda base de datos, cola, caché o servicio independiente.
- Migrar todos los tokens a cookies, cambiar contratos o modificar modelos existentes sin una necesidad y propuesta concretas derivadas de la revisión.
- Añadir funciones o una nueva dirección visual.

## Decisions

### 1. Actualización por lotes con base reproducible

Actualizar primero dependencias de producción afectadas y sus versiones compatibles, después herramientas de desarrollo. Revisar avisos oficiales vigentes al ejecutar, distinguir dependencia declarada de archivos incluidos en standalone y conservar lockfile, imagen anterior y pruebas de humo. Evitar actualizaciones forzadas indiscriminadas: pueden degradar versiones o introducir una ruptura ajena al requisito.

Cierre de cada lote: lint, tipos, formato, pruebas afectadas, build y auditoría repetida. Un aviso pendiente debe tener aplicabilidad y tratamiento documentados; un aviso crítico/alto aplicable sin mitigación impide declarar publicación lista. Revisar también dependencias Python con la herramienta disponible, sin instalar infraestructura adicional.

### 2. Política de inferencia acotada al proveedor

Reproducir texto/imagen con los dos modelos instalados y capturar metadatos de finalización, conteo de tokens, latencia y memoria sin guardar entradas privadas. Mantener configuración y validación en backend. Si 512 tokens o el modo de razonamiento causan truncamiento, ajustar límites de generación con validación y pruebas del caso; evitar simplemente multiplicar límites para todos los modelos.

Conservar `keep_alive=0` como base hasta medir VRAM/RAM y alternancia embeddings/inferencia: cambiarlo puede reducir cargas, pero también agotar memoria. Validar disponibilidad real de GPU y memoria en Docker. Recomendación instruct documentada; cambios al modelo de fuentes o bots existentes deben ser explícitos y compatibles con su configuración.

Una respuesta vacía seguirá siendo fallo seguro. No agregar fallback automático hacia otro proveedor/modelo ni reintentos ocultos que dupliquen consumo o métricas. El usuario podrá reintentar desde el flujo existente.

### 3. Matriz real con datos aislados

Reutilizar auxiliar `backend/scripts/ui_acceptance_fixtures.py`, pruebas y ejecutor real existentes. Fuentes con un dato identificable por caso, PDF con texto, DOCX, CSV, TXT y PNG/JPEG/WebP. PDF escaneado y cifrado son casos de rechazo/limitación: no introducir OCR sin requisito.

Verificar por fuente estado, contenido/chunks, dimensión 768, recuperación y aislamiento. La imagen de conocimiento requiere probar el modelo de `OLLAMA_MODEL`; la imagen conversacional requiere probar el modelo del chatbot. Para proveedores externos, ejecutar únicamente con credenciales habilitadas y límite de gasto permitido; ausencias de credenciales se registran como pendiente, nunca como aprobado por mocks.

### 4. Rendimiento guiado por resultados

Comparar Resumen con cero, dos y un conjunto mayor de bots de QA, manteniendo mismo periodo y datos. Tamaños de QA no constituyen capacidad prometida. Registrar solicitudes, bytes y tiempos; reducir duplicación mediante los servicios existentes. Si hace falta un agregado API, fijar DTO, periodo y autorización antes de añadir un endpoint; no crear datos diarios inexistentes ni promedios no ponderados.

Probar desconexión de cliente, caída del proveedor, repetición de carga y reinicio durante procesamiento. Corregir estados o transacciones incompletas demostrados. Evaluar extracción fuera del hilo/event loop cuando se mida bloqueo. Un proceso durable, cola o esquema adicional queda fuera de este diseño y requeriría propuesta sustentada por el resultado.

### 5. Persistencia y fronteras transaccionales

Conservar cardinalidades de [database-design.md](../../../docs/database-design.md): chatbot → consultas, documentos ↔ chatbots mediante asociación y documento → chunks. Sin cambios de dimensión ni entidades en esta planificación.

La aceptación del archivo precede al procesamiento; los chunks válidos solo se publican con éxito. Revisar interrupciones entre commits sin tratar una transacción larga con llamadas de red como solución. Quitar asociación no elimina fuentes compartidas; la limpieza del usuario de QA no toca archivos de otros usuarios. Consultas conservan estado, tiempo y modelo ejecutado, incluso si falla el proveedor.

### 6. Verificación continua y cierre manual

Incorporar los comandos existentes a CI con PostgreSQL/pgvector aislado. Llamadas reales y pruebas que consuman credenciales se ejecutan como verificación explícita, separadas de cada PR. No incluir secretos en capturas, artefactos ni logs. Mantener reglas de formato y pruebas significativas; ampliar regresión únicamente por el cambio o un riesgo concreto.

Cerrar zoom, lector de pantalla y cancelación de captura mediante registro humano; reutilizar tareas 6.5, 7.2, 7.3 y 7.7 del cambio visual. La verificación del selector de privacidad requiere interacción humana. Confirmación previa de captura adjunta permanece válida, sin repetirla innecesariamente.

### 7. Preparación para publicación delimitada

Con destino y dominio definidos, validar TLS en la plataforma/proxy elegido y widget en sitio externo HTTPS. Ensayar respaldo y restauración en volúmenes temporales con base y documentos, comprobar asociaciones y recuperación y eliminar únicamente esos volúmenes. Las instrucciones de respaldo ya existen: el pendiente es demostrar restauración.

Revisar persistencia/revocación y exposición del token en un informe acotado. Cambiar a cookies requeriría resolver proxy, CSRF, atributos, orígenes y compatibilidad; no decidir esa migración a partir de un aviso genérico. El destino de publicación y accesos son precondiciones de esta fase, no de los bloques locales.

## Risks / Trade-offs

- Actualización Next/React → consultar compatibilidad y validar en imagen Docker antes de sustituir la anterior.
- Más tokens o modelo residente → medir memoria real y conservar posibilidad de reversión de configuración.
- API externa con coste → ejecutar solo con límite permitido y fixtures mínimos; registrar bloqueo si falta.
- Cambiar embeddings → no cambiar proveedor/dimensión en este plan; exigir reindexación y estrategia propia si se propone después.
- Medición local concurrente → registrar hardware, calentamiento y carga; no imponer un umbral de latencia inexistente en SRS.
- Pruebas humanas o destino no disponibles → mantener tareas pendientes y entregar bloques locales con su evidencia.

## Migration Plan

1. Inventario y huellas actuales; copia verificable del despliegue y datos necesarios, sin imprimir secretos.
2. Lote de dependencias en checkout actual o rama acordada, conservando cambios previos; construir una nueva imagen etiquetada.
3. Validación de inferencia y fuentes en recursos de QA; ninguna sustitución global de modelos.
4. Correcciones de rendimiento/recuperación demostradas y prueba de equivalencia.
5. Automatización y aceptación; reconstrucción limpia y recorrido externo.
6. Publicación solo con destino autorizado y evidencia de TLS/restauración. Revertir a imagen/configuración anterior si la prueba de humo falla; si surgiera migración, exigir antes su plan reversible.

## Open Questions

- Versiones objetivo: escoger al ejecutar según avisos oficiales y compatibilidad, sin fijar en un plan una versión que podría quedar obsoleta.
- Credenciales y presupuesto disponibles para proveedores externos: determinan qué filas reales pueden ejecutarse, no cambian el contrato.
- Dominio/plataforma de publicación y acceso al lector de pantalla: necesarios para las últimas comprobaciones, no para iniciar los lotes locales.
