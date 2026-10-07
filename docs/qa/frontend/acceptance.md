# BIDACHAT — ejecución y aceptación de la interfaz

Fecha local: 5 de octubre de 2026; evidencias técnicas en UTC del 6 de octubre.
Cambio: `professionalize-frontend-experience`, autorizado mediante «ejecutalo».

## Resultado y alcance

Implementación desplegada en el frontend Docker local, con navegación, editor,
temas y widget actualizados. La revisión final registra comprobaciones ejecutadas;
la aceptación manual completa permanece pendiente del lector de pantalla, del
zoom real del navegador y de la cancelación del selector nativo de captura. No se declara certificación WCAG ni preparación integral
para producción pública a partir de esta revisión de interfaz.

- URL, menú, breadcrumb, chatbot, paso y filtros se mantienen coherentes.
- Sesión vigente al recargar; reautenticación conserva el destino interno.
- Salir de un borrador requiere confirmación; errores conservan los campos.
- Editor separado en campos, fuentes, acciones y vista visual del widget real.
- Temas semánticos claro/oscuro, navegación fija/contraíble y menú móvil con foco.
- Resumen con consultas por chatbot y resultados del mismo periodo; sin cifras
  inventadas, tendencias inexistentes ni estados de conectividad supuestos.
- Fuentes visibles, selección existente, asociación y retirada del contexto.
- Integración con selección reconocible, copia alternativa y orígenes consultables.
- Widget con texto, imagen, pegado, retirada, captura y recuperación de errores.

## Evidencia y versión

La identificación reproducible de la compilación y huellas está en
[release-manifest.json](release-manifest.json). La línea base conservó capturas
del frontend Docker anterior; no se dispone de una revisión exacta de su fuente.
No se presenta esa línea base como una versión Git identificada.

| Comprobación | Resultado | Evidencia |
|---|---|---|
| Navegador | 19 pruebas aprobadas, última ejecución completa | [Reporte Playwright](playwright-report/index.html) |
| Responsive | 80 capturas, 8 superficies × 5 anchos × 2 temas, sin desbordamiento de página | [Galería](index.html), [manifest](capture-manifest.json) |
| Accesibilidad automática | 33 auditorías Axe sin infracciones en etiquetas WCAG 2 A/AA y 2.1 AA seleccionadas | Pruebas de matriz y acceso en Playwright |
| Unidades frontend | 23 aprobadas | [Verificaciones](verification-results.json) |
| Integración backend afectada | 15 aprobadas con PostgreSQL/pgvector; proveedor simulado en pruebas de lógica | [Verificaciones](verification-results.json) |
| Calidad del código | Lint, tipos, formato y compilación de producción aprobados; Ruff del auxiliar de QA aprobado | [Verificaciones](verification-results.json) |
| Flujo real | Crear, personalizar, procesar TXT, RAG, regreso al editor, integración externa e imagen | [Resultados reales](live-results.json) |
| Fuente compartida real | Quitar de A conserva archivo y asociación de B; disponible y reasociable a A | `live-shared-source` en resultados reales |
| Recursos | JS, fuente e icono con MIME correcto; widget construido, público y servido coinciden | [Recursos](resource-results.json) |
| Captura nativa | El usuario confirmó que la captura aparece como adjunto | [Comprobaciones manuales](manual-results.json) |
| Revisión visual independiente | Hallazgos y resolución de tres ajustes móviles | [Revisión](finish-review.md) |

Las capturas usan datos sintéticos identificables. Las pruebas API reales crearon
un usuario, dos chatbots, una fuente y consultas propios; se limpiaron exclusivamente
esos datos y archivos, sin modificar chatbots del usuario. [Limpieza](fixture-cleanup.json).

## Destinos y acciones L01–L18

Precondiciones: sesión de prueba vigente salvo casos de acceso, UUID del recurso
seleccionado y frontend compilado. Respuestas API sintéticas para navegación/estados;
backend y Ollama reales para la integración externa y procesamiento.

| Caso | Resultado y evidencia |
|---|---|
| L01 Secciones | Aprobado: las cinco secciones, selección y títulos en matriz; errores y recuperación en cada sección. |
| L02 Enlace profundo | Aprobado: editor/paso de URL, recarga y filtros restaurados. |
| L03 Historial | Aprobado: atrás/adelante entre pasos y selección explícita de dos chatbots; borrador preservado en el mismo editor. |
| L04 Cierre | Aprobado: cancelar/finalizar vuelve a `view=Chatbots`; la URL describe el listado. |
| L05 Vista previa | Aprobado: enlace generado y retorno al chatbot/paso 5; verificado también con sesión real. |
| L06 Sesión vigente | Aprobado: recarga y nueva pestaña con sesión vigente; regreso real no abre login. |
| L07 Sesión vencida | Aprobado: fecha vencida muestra aviso; login recupera chatbot y paso. Retornos externos rechazados en prueba unitaria. |
| L08 Recurso eliminado | Aprobado: UUID inexistente informa ausencia y ofrece listado; no abre creación. |
| L09 Parámetros inválidos | Aprobado: parser unitario, rutas inválidas en navegador y validación de vista previa. |
| L10 Nueva pestaña | Aprobado: enlace de otro chatbot abre su nombre y paso; sesión disponible. |
| L11 Fragmento | Aprobado: Tab/Enter en «Ir al contenido» mueve foco al área principal. |
| L12 Recursos | Aprobado en recursos usados por recorridos: sin solicitudes fallidas en muestra final; MIME y huellas comprobados. |
| L13 Script | Aprobado: snippet generado con apariencia guardada; inserción en sitio HTTP independiente, sin imports del proyecto. |
| L14 Orígenes | Aprobado: respuesta desde 4173; 4174 produce error visible y conserva pregunta. CORS no se presenta como sustituto de autenticación. |
| L15 Permisos | Aprobado en alcance ejecutado: copia denegada ofrece alternativa, captura cancelada simulada conserva entrada, captura nativa confirmada por usuario. |
| L16 404 | Aprobado: ruta inexistente ofrece regreso al panel. |
| L17 Borrador | Aprobado: cancelar salida conserva campos; confirmarla navega; fallo al guardar conserva valores. El diálogo nativo de recarga conserva el borrador al cancelar: [evidencia](beforeunload-results.json). |
| L18 Referencias | Aprobado al consultar: UI UX Pro Max y WCAG accesibles; dos originales de Stitch recuperados mediante MCP. Enlaces locales nuevos comprobados. |

Un estado 200 no se usó como sustituto de verificar pantalla, nombre, paso o contenido.
La lista representa estos destinos y escenarios, no una garantía universal de que
cualquier URL futura o sitio externo permanecerá disponible.

## Prueba real y elección del modelo

Un TXT sintético definió Faro = 137 y meta = 150. Ollama generó embeddings y la
consulta RAG devolvió 137 desde la aplicación y el sitio externo autorizado.
La primera consulta con imagen y `qwen3-vl:2b` terminó con HTTP 503 del backend:
Ollama generó 512 tokens sin contenido final utilizable. La evidencia de ese fallo
se conserva; no se convirtió en una aprobación.

Se repitió exclusivamente con el chatbot aislado usando el modelo ya instalado
`qwen3-vl:2b-instruct`. Respondió: «La imagen muestra una comparación trimestral de
dos valores: A con 40 y B con 80». Las métricas registraron tres consultas
completadas y una fallida. No se cambiaron modelos de chatbots existentes.

## Rendimiento y estructura

La [política](performance-policy.md) define un presupuesto de regresión para este
cambio. [Comparación](performance-results.json): Resumen conserva cinco solicitudes
de datos para dos chatbots; la vista de apariencia no ejecuta consultas al LLM.
Los bytes medidos pertenecen al documento principal, con caché deshabilitada por
el ejecutor de fixtures; no incluyen los recursos internos del iframe. Una muestra
por superficie/tema, con otras cargas locales concurrentes, no acredita un tiempo
garantizado ni mide el coste de inferencia.

No se agregaron frameworks de interfaz, servicios de infraestructura ni biblioteca
de gráficos. Playwright y Axe son dependencias de desarrollo. Se reutilizan API,
servicios, componentes e iconos existentes. [DESIGN.md](../../../DESIGN.md) es la
autoridad visual; el diseño anterior se conserva en su historial.

## Límites y pendientes concretos

1. Escucha real con NVDA/Narrator: no ejecutada. Etiquetas, roles, foco y regiones
   vivas pasaron comprobaciones automáticas; eso no reemplaza escuchar el recorrido.
2. Zoom nativo al 200 %: pendiente. El reflujo equivalente a 720 CSS px se comprobó,
   junto con 320 px; no se etiqueta como prueba manual de zoom.
3. La consulta multimodal real usó una imagen del dashboard sintético; el usuario
   confirmó aparte el adjunto del selector nativo. No se afirma que esa captura
   específica se envió y analizó durante su comprobación.
4. La cancelación del selector nativo de captura requiere comprobación humana;
   se verificó únicamente su equivalente simulado.
5. Esta revisión no es una auditoría de seguridad de producción. La instalación
   informó avisos de vulnerabilidad en dependencias existentes; no se aplicaron
   actualizaciones forzadas que cambien versiones fuera del alcance aprobado.
   La consulta del 6 de octubre registra 14 paquetes con avisos en el árbol completo
   y cuatro en dependencias de producción: [resumen](dependency-audit-summary.json).

Para completar la aceptación manual: recorrer acceso/editor/publicación con un
lector de pantalla y verificar anuncios, foco y recuperación; repetir editor,
Configuración y widget con zoom real 200 %. Registrar dispositivo, navegador y
resultado en `manual-results.json`. La implementación se entrega con estos límites
explícitos; las tareas correspondientes permanecen abiertas.

## Referencias y reproducción

La elección de gráficos, estados y controles se contrastó con
[UI UX Pro Max](https://uupm.cc/). Los objetivos de contraste, foco y reflujo se
apoyan en [WCAG 2.2](https://www.w3.org/TR/WCAG22/), sin declarar conformidad completa.
[Registro de originales Stitch](stitch-references.json) distingue las referencias
históricas de las capturas de esta implementación. Se conservaron Inter, superficies
claras, turquesa y controles conversacionales; los prototipos no se ejecutan como
pantallas de la aplicación ni aportan datos ficticios.

Instrucciones de pruebas de navegador en [frontend/README.md](../../../frontend/README.md).
Para el recorrido real, crear una cuenta aislada mediante
`backend/scripts/ui_acceptance_fixtures.py create` dentro del contenedor backend y
guardar su salida en un archivo temporal privado; usarlo como
`BIDACHAT_QA_CREDENTIALS` al ejecutar `npm run test:live`. Requiere el modelo
`qwen3-vl:2b-instruct` registrado y descargado, embeddings locales y 4173 autorizado.
Al terminar, ejecutar `cleanup --user-id UUID` del mismo auxiliar y retirar el
archivo temporal. Nunca guardar contraseñas en el repositorio ni usar cuentas reales
para este procedimiento.
