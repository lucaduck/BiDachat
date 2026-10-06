Ejecución autorizada por el usuario y verificada en `docs/qa/frontend/acceptance.md`. Las casillas marcadas representan trabajo implementado con evidencia. Se conserva BI-DATA conforme a la dirección autorizada. Las comprobaciones manuales pendientes se mantienen abiertas; no se declara aceptación completa por aprobar pruebas automáticas.

## 1. Base verificable y trazabilidad

- [x] 1.1 Conciliar los criterios propuestos con SRS 0.2 y los deltas pendientes de `build-frontend-mvp`; registrar los criterios adicionales autorizados sin modificar requisitos ajenos.
- [x] 1.2 Actualizar el contexto obsoleto de OpenSpec y documentar una única autoridad visual, conservando el historial de `desing.md` y las referencias aprobadas.
- [x] 1.3 Capturar acceso, cinco secciones, editor y vista previa en claro/oscuro con una versión identificable; separar capturas actuales de referencias antiguas.
- [x] 1.4 Crear datos de prueba aislados para cero/múltiples chatbots, fuente compartida, errores, nombres largos y métricas vacías; usar PostgreSQL + pgvector para integración.
- [x] 1.5 Registrar destinos y acciones L01–L18 con precondiciones y resultados esperados; comprobar qué cubre ya `widget/scripts/visual-check.mjs`.
- [x] 1.6 Medir la línea base de carga, solicitudes y recursos con datos reproducibles; documentar presupuestos de rendimiento propuestos antes de exigirlos.

## 2. Navegación y continuidad — prioridad P0

- [x] 2.1 Implementar parser y constructor de URL en `frontend/lib/navigation.ts`, preservando parámetros existentes y validando vista, modo, UUID y paso.
- [x] 2.2 Añadir pruebas unitarias de enlaces profundos, valores inválidos, compatibilidad y destinos de retorno internos permitidos.
- [x] 2.3 Integrar el estado de ruta en `AdminWorkspace` y `ChatbotManagement`; eliminar copias obsoletas del identificador del editor y verificar historial entre dos chatbots.
- [x] 2.4 Corregir cerrar editor para volver al listado con URL coherente; probar recarga y nueva pestaña.
- [x] 2.5 Distinguir creación explícita, chatbot eliminado y ruta desconocida, mostrando recuperaciones válidas sin abrir un formulario de creación accidental.
- [x] 2.6 Extender breadcrumb a chatbot y paso; mantener sidebar/título coherentes y gestionar foco en transiciones.
- [x] 2.7 Implementar aviso de borrador pendiente y cancelación de salida; comprobar navegación interna, historial y recarga según las capacidades del navegador.
- [x] 2.8 Verificar restauración de sesión y regreso desde `/preview`; conservar destino interno validado durante reautenticación legítima.
- [x] 2.9 Ejecutar casos L01–L11, L16 y L17 con pruebas de navegador y registrar evidencia; corregir antes de pasar al acabado visual.

## 3. Sistema visual compartido — prioridad P1

- [x] 3.1 Preparar composiciones de Resumen, editor y widget en los dos temas siguiendo la identidad actual; fijar la dirección visual con la revisión del usuario.
- [x] 3.2 Definir tokens semánticos para superficie, texto, acción, foco y estados con pares de contraste comprobados.
- [x] 3.3 Unificar Inter, escala tipográfica, espaciados, radios y densidad entre ambos temas; conservar la preferencia al recargar.
- [x] 3.4 Ajustar Button, campos, alertas, estados y etiquetas existentes; incluir carga, vacío, error, deshabilitado, foco y `aria-describedby` donde corresponda.
- [x] 3.5 Extraer estilos de shell y componentes a unidades con responsabilidad clara; retirar reglas duplicadas de `globals.css` durante cada migración.
- [x] 3.6 Separar shell, sidebar y breadcrumb de la carga de datos; verificar sidebar contraído, expandido y menú móvil con foco y Escape.
- [x] 3.7 Documentar los componentes y tokens realmente adoptados, resolviendo la autoridad entre documentos visuales en lugar de dejar reglas contradictorias.

## 4. Pantallas administrativas — prioridad P1

- [x] 4.1 Pulir acceso y restauración de sesión con validación, estado de envío, fallo y visibilidad de contraseña; probar teclado y móvil.
- [x] 4.2 Actualizar Resumen con barras por chatbot y resultados usando agregados reales, periodo consistente y estados sin datos; verificar sumas contra API.
- [x] 4.3 Ajustar listado de chatbots, acciones editar/probar/integrar y eliminación con confirmación; comprobar nombres largos y lista vacía.
- [x] 4.4 Mejorar Documentos con selector, carga visible, estados de procesamiento y recuperación, evitando mostrar datos anteriores al cambiar de chatbot.
- [x] 4.5 Ajustar Métricas con filtros, unidades y ausencia de muestras; verificar que no se fabrican series diarias ni promedios sin ponderar muestras.
- [x] 4.6 Completar Configuración con jerarquía clara, script copiable y estados de credenciales/orígenes de solo lectura; probar portapapeles denegado.
- [x] 4.7 Verificar estados de error y recuperación de cada pantalla con API no disponible, sesión vencida y datos vacíos; conservar entradas cuando corresponda.

## 5. Editor y experiencia conversacional — prioridad P1

- [x] 5.1 Separar pasos, fuentes y vista visual del wizard conservando validaciones y servicios; verificar estado antes/después de la extracción.
- [x] 5.2 Aplicar diseño y validación coherentes a General, Apariencia y Comportamiento; probar guardar, error y reapertura con valores persistidos.
- [x] 5.3 Aplicar diseño al paso Conocimiento: cargar documento/imagen, seleccionar fuentes existentes, asociar y quitar del contexto con estados reales.
- [x] 5.4 Probar una fuente compartida entre dos chatbots; quitarla de uno conserva el archivo y la asociación del otro (RF-09, RF-17, CA-UC03-07).
- [x] 5.5 Ajustar Publicación con resumen, copia y prueba; verificar coincidencia entre apariencia guardada, snippet y widget real (RF-10, RF-28, RF-29).
- [x] 5.6 Corregir diferencias entre vista visual y widget; retirar indicadores ficticios de conectividad y verificar las mismas configuraciones en ambos.
- [x] 5.7 Verificar envío de texto e imagen, pegar, quitar, captura cancelada/no soportada y error de consulta sin pérdida innecesaria de entradas.
- [x] 5.8 Comprobar conversación larga, scroll, foco, apertura/cierre y controles del widget en pantalla pequeña y con teclado.

## 6. Integración independiente y recursos — prioridad P1

- [x] 6.1 Construir widget con sus scripts existentes y comprobar que la copia pública coincide con el artefacto construido; verificar recurso y tipo MIME.
- [x] 6.2 Levantar un sitio estático de QA en otro origen, sin imports ni dependencias internas; insertar únicamente el script generado y probar el chatbot seleccionado.
- [x] 6.3 Probar origen autorizado y denegado con configuración de test, comprobando errores visibles y ausencia de acceso directo a datos o proveedores.
- [x] 6.4 Comprobar L12–L15 y L18: JS/CSS/fuentes/favicon/imágenes, snippet, enlaces externos y alternativas por permisos del navegador.
- [ ] 6.5 Registrar la verificación manual del selector nativo de captura, su cancelación y el resultado real de la consulta multimodal de prueba.

## 7. Aceptación y entrega

- [x] 7.1 Incorporar Playwright o reutilizar la herramienta disponible para los recorridos obligatorios; añadir comprobación automática de accesibilidad como dependencia de desarrollo solo si falta.
- [ ] 7.2 Ejecutar la matriz de estados y tamaños 1440/1089/768/390/320, claro/oscuro y zoom 200 %; revisar capturas en conjunto y corregir los defectos concretos encontrados.
- [ ] 7.3 Comprobar manualmente teclado, foco, lector de pantalla en flujos principales, contraste y movimiento reducido; registrar resultados y limitaciones.
- [x] 7.4 Ejecutar pruebas unitarias/integradas afectadas, lint, formato, tipos y compilación de producción; resolver fallos del alcance.
- [x] 7.5 Ejecutar el recorrido completo con backend de test: acceso → crear → personalizar → asociar → probar → integrar externamente → consulta → métricas.
- [x] 7.6 Comparar rendimiento con la línea base, investigar regresiones concretas y comprobar que refactorizar no añadió solicitudes innecesarias.
- [ ] 7.7 Revisar L01–L18 y los escenarios de la especificación; exigir resultado aprobado o resolver el bloqueo antes de considerar terminada la entrega.
- [x] 7.8 Actualizar documentación técnica y generar informe con versión, capturas, trazas, resultados y limitaciones; verificar también los enlaces de la documentación nueva.

## Pendientes manuales delimitados

- 6.5: selector nativo y adjunto confirmados por el usuario; cancelación probada con
  NotAllowedError simulado. Cancelación real en el diálogo nativo no registrada. La
  consulta multimodal real con imagen del dashboard de QA pasó con la variante instructiva.
- 7.2: matriz80 y ambas apariencias aprobadas; reflujo equivalente a200% aprobado.
  Falta zoom nativo200% registrado.
- 7.3: teclado, foco, contraste automatizado y movimiento reducido comprobados.
  Falta escucha real de un lector de pantalla.
- 7.7: L01–L18 aprobados dentro del alcance documentado; la aceptación manual completa
  permanece abierta por los puntos anteriores. Implementación entregada en el entorno local.
