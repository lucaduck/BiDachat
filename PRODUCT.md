# BIDACHAT

## Producto y usuarios

Aplicación web del grupo BI-DATA para que investigadores autorizados creen,
configuren e integren asistentes que interpretan cuadros de mando analíticos.
Los visitantes del dashboard conversan mediante un widget independiente.
El objetivo actual es la versión completa descrita en SRS.md.

## Tareas principales

- Acceder al panel y mantener una sesión vigente al recargar.
- Crear y configurar un chatbot en cinco pasos: General, Apariencia,
  Comportamiento, Conocimiento y Publicación.
- Cargar documentos o imágenes, reutilizar fuentes y quitar asociaciones del contexto.
- Probar el asistente, integrar su script en un sitio externo y consultar métricas reales.
- Enviar preguntas con una imagen adjunta, pegada o capturada por el usuario.

## Restricciones confirmadas

- Español en la interfaz; identificadores técnicos en inglés.
- Conservar identidad BI-DATA: turquesa, Inter y marca BIDACHAT vigente.
- Temas claro y oscuro, navegación visible y contraíble, adaptación a móvil,
  teclado y mensajes comprensibles de estados y errores.
- Backend único con servicios lógicos; clientes acceden a la API, nunca a datos o proveedores directamente.
- Mantener Next.js, TypeScript, Tailwind CSS, FastAPI, PostgreSQL + pgvector,
  widget JavaScript y Docker Compose. Reutilizar servicios existentes.
- `widget/example` es una página independiente para pruebas; no se incorpora al panel administrativo.
- La configuración de orígenes y credenciales solo se consulta mientras no haya una operación de edición aprobada.

## Fuentes de verdad

SRS.md define requisitos; AGENTS.md define implementación; DESIGN.md documenta
el sistema visual realmente adoptado. El cambio autorizado está en
`openspec/changes/professionalize-frontend-experience/`.

## Aceptación

La calidad se demuestra con recorridos de navegador, datos aislados, integración
con PostgreSQL + pgvector y proveedores locales, capturas en ambos temas y
resultados documentados. Las comprobaciones automáticas no sustituyen la escucha
con un lector de pantalla ni la selección manual en el diálogo nativo de captura.

On 2026-10-06 the user required the “Datos que conversan” panel signature to keep the handwritten, tilted, two-line style and turquoise underline from their supplied reference. Inter remains the interface family; the signature uses locally hosted Caveat. The panel reuses the exact circuit marks selected by the user: `docs/brand/Logotipo BC de Circuitos Tecnológicos.png` in light and `docs/brand/Logotipo BC de Circuito Futurista.png` in dark, in the sidebar and BI-DATA banner with the requested faded circuit treatment.
