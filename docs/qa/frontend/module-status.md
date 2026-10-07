# Estado funcional y deuda técnica

Fecha: 6 de octubre de 2026. Estado del código y del despliegue Docker local.

## Criterio de evaluación

«Operativo verificado» significa que los recorridos descritos pasaron las pruebas
registradas. No equivale a cobertura del 100 % del código, certificación de todos
los requisitos ni disponibilidad garantizada en producción. No se asignan porcentajes
sin una matriz completa de requisitos y evidencia por criterio.

## Módulos

| Área | Estado y alcance comprobado |
|---|---|
| Acceso y sesión | Operativo: login real; recarga, nueva pestaña, vencimiento y retorno al destino comprobados en navegador. |
| Gestión de chatbots | Operativo: creación real; listado, edición, guardado, eliminación y sus errores comprobados en pruebas afectadas. |
| Configuración y apariencia | Operativo: cinco pasos, personalización persistente, protección de borrador, vista visual y retorno al editor. El catálogo no demuestra compatibilidad real de todos los modelos. |
| Fuentes compartidas | Operativo: subir, asociar, reutilizar y quitar del contexto. Prueba real confirma que quitar de A conserva archivo y contexto de B. |
| Procesamiento y RAG | Operativo para TXT en el recorrido real: procesamiento, embeddings Ollama, PostgreSQL/pgvector y recuperación. Queda ampliar aceptación real de PDF, DOCX, CSV e imágenes como fuentes. |
| Conversación y widget externo | Operativo: texto e imagen con qwen3-vl:2b-instruct en sitio HTTP independiente; errores y orígenes no autorizados comprobados. Un modelo diferente falló; no se considera todo el módulo LLM cerrado. |
| Métricas y resumen | Operativo: consultas, éxitos/fallos, tiempos y asociación al chatbot; tres completadas y una fallida en la prueba real. Escalabilidad del resumen pendiente. |
| Configuración general | Operativa como consulta: estados de credenciales, modelos, integración y orígenes. No existe edición de secretos ni de orígenes desde este panel. |
| Interfaz y navegación | Operativas en los recorridos y tamaños probados: claro/oscuro, sidebar fijo/contraíble, menú móvil, historial y filtros. Aceptación manual de accesibilidad pendiente. |

## Deuda técnica y validaciones pendientes

| Prioridad | Pendiente | Evidencia y criterio para cerrarlo |
|---|---|---|
| Alta | Dependencias con avisos de seguridad | Audit actual: 14 paquetes en total; cuatro en árbol de producción, uno crítico y tres altos. Actualizar versiones compatibles, repetir auditoría, compilación y pruebas. Los avisos no acreditan explotación de BIDACHAT. |
| Alta | Compatibilidad de inferencia local | qwen3-vl:2b devolvió contenido final vacío y provocó 503; instruct respondió correctamente. Revisar límites por modelo y manejo de respuesta; reproducir consulta visual sin salida vacía. |
| Alta | Cobertura real de proveedores y fuentes | La aceptación registrada usa Ollama y TXT, más una imagen conversacional. Repetir los casos aplicables con PDF/DOCX/CSV, imágenes como conocimiento y los proveedores externos que se habiliten. |
| Media | Solicitudes del resumen crecen por chatbot | dashboard-summary solicita documentos y métricas por cada bot: listado inicial + 2N solicitudes. Consolidar agregados en la API existente si se necesita soportar más chatbots y verificar equivalencia de resultados. |
| Media | Trabajo prolongado dentro de la petición de carga | La API espera procesamiento/embeddings; el proxy admite un tiempo elevado. Verificar recuperación ante interrupciones y concurrencia antes de decidir cambios dentro del stack actual. |
| Media | Cierre manual de accesibilidad y captura | Lector de pantalla, zoom nativo 200 % y cancelación del selector nativo pendientes. La captura como adjunto fue confirmada por el usuario. |
| Media | Automatización de verificaciones | Pruebas y comandos reproducibles existen; no hay .github/workflows en este checkout. Integrar las puertas de calidad en el mecanismo de CI elegido para el repositorio. |
| Antes de publicación | Validación operacional y de sesión | No se acreditó despliegue HTTPS, restauración de respaldo ni carga concurrente en esta revisión. Hay instrucciones de respaldo/restauración. Revisar persistencia del token en localStorage como parte del endurecimiento de sesión. |

La configuración editable sería una ampliación funcional que requiere definir el
alcance. No se registra la ausencia de esa ampliación como fallo del panel de consulta.

## Evidencias

- [Aceptación y límites](acceptance.md): 19 pruebas de navegador, 23 unitarias frontend,
  15 backend afectadas, 80 capturas y 33 auditorías Axe.
- [Flujos reales y fallo conservado](live-results.json).
- [Dependencias](dependency-audit-summary.json).
- [Revisión visual](finish-review.md).
- [Guía de respaldo y restauración](../../../database/README.md).

El frontend usa Next.js 16.1.4 y rewrites hacia FastAPI. Existe un aviso publicado
por el mantenedor para esta combinación de versión y proxy:
[GHSA-ggv3-7p47-pfv8](https://github.com/vercel/next.js/security/advisories/GHSA-ggv3-7p47-pfv8).
La coincidencia amerita priorizar actualización; esta revisión no contiene una
prueba de explotación ni asegura que un solo parche cierre todos los avisos.
