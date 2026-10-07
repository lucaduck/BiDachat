## Context

La motivación y el alcance están en [proposal.md](proposal.md). Este documento describe el trabajo propuesto, no afirma que los defectos ya estén corregidos. Se revisaron el SRS 0.2, el código, `desing.md` y las referencias visuales del usuario. La dirección provisional conserva BI-DATA, Inter, turquesa y los dos temas; no se ha seleccionado un logo nuevo entre las propuestas anteriores.

### Diagnóstico comprobado

| Hallazgo                                                                        | Evidencia                                                                                               | Consecuencia y prioridad                                                                                  |
| ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| URL y editor pueden discrepar                                                   | `chatbot-management.tsx` cierra el editor mediante `replaceState(..., "/")`, manteniendo la vista local | P0: refrescar puede abrir Resumen en lugar de Chatbots                                                    |
| El historial actualiza solo parte del estado                                    | `admin-workspace.tsx` escucha `popstate`; `chatbot-management.tsx` copia `initialEditId` al montar      | P0: verificar y corregir cambios de editor dentro de la misma vista                                       |
| La validación del identificador no acredita existencia                          | La vista previa valida formato UUID; gestión busca el chatbot y puede entregar `undefined` al wizard    | P0: un chatbot eliminado debe mostrar recurso no disponible, nunca convertirse implícitamente en creación |
| Vista visual y widget real tienen implementaciones diferentes                   | `WidgetPreview` en `chatbot-wizard.tsx` frente a `widget/src/bidachat-widget.js`                        | P1: riesgo de diferencias de apariencia; el rótulo «En línea» de la maqueta no mide disponibilidad        |
| Estilos acumulados                                                              | `globals.css`: 2.671 líneas al revisar, con reglas base y sobrescrituras por tema                       | P1: reducir especificidad y mantener una definición por variante                                          |
| Editor concentra responsabilidades                                              | `chatbot-wizard.tsx`: 703 líneas; formulario, persistencia, documentos y vista previa                   | P1: separar por responsabilidades verificables                                                            |
| Resumen consulta cada chatbot                                                   | `dashboard-summary.tsx` carga documentos y métricas por chatbot                                         | P2: medir solicitudes y tiempos con conjuntos de prueba antes de proponer otro endpoint                   |
| Documentación divergente                                                        | `openspec/config.yaml` conserva MVP/SRS borrador; SRS y AGENTS actuales establecen versión completa     | P0 documental: alinear al iniciar implementación                                                          |
| Pruebas de servicios presentes, recorridos completos no localizados en frontend | Vitest y pruebas en `frontend/services`; widget tiene `visual:check`                                    | P1: cubrir navegación y acciones reales reutilizando lo disponible                                        |

Comprobación HTTP del entorno local: `/` y `/bidachat-widget.js` respondieron 200; el script se sirvió como JavaScript. Esto prueba disponibilidad de esos dos recursos únicamente. No se ejecutaron recorridos autenticados ni una auditoría visual nueva en esta planificación. Las capturas anteriores son referencias, no evidencia de aceptación de la versión actual.

## Goals / Non-Goals

**Goals:** una persona debe reconocer dónde está, qué puede hacer y qué ocurrió; conservar contexto al navegar; completar crear → configurar → asociar fuentes → probar → integrar; usar ambas apariencias con teclado y móvil; mantener un frontend que permita cambios locales sin efectos visuales imprevistos.

**Non-Goals:** no se estima un precio de mercado a partir de «100.000 dólares». No se incorporan microservicios, un nuevo framework visual, páginas comerciales, métricas inventadas ni controles ficticios. Nuevas funciones de credenciales, orígenes editables, MFA o recuperación requieren especificación propia. Este cambio no modifica entidades, cardinalidades, migraciones, transacciones ni reglas de eliminación de la base de datos; se conserva la relación chatbot–fuentes descrita en [database-design.md](../../../docs/database-design.md).

## Decisions

### 1. Reglas de calidad aplicadas a BIDACHAT

| Regla                  | Aplicación concreta                                                              | Evidencia exigida                                       |
| ---------------------- | -------------------------------------------------------------------------------- | ------------------------------------------------------- |
| Visibilidad del estado | Ubicación, chatbot, paso, guardado y procesamiento visibles                      | Capturas y recorridos en éxito, espera y fallo          |
| Consistencia           | Mismos verbos, controles y estados en editor, documentos y configuración         | Catálogo de componentes y comparación entre pantallas   |
| Jerarquía              | Una acción principal por tarea, títulos claros, detalles secundarios separados   | La tarea principal se identifica en la primera pantalla |
| Control y recuperación | Volver, cancelar, quitar adjunto y reintentar conservan el contexto válido       | Pruebas de cancelación, error y regreso                 |
| Prevención de errores  | Validación previa de archivos y confirmación de acciones destructivas            | Archivo inválido y eliminación cancelada                |
| Reconocimiento         | Fuente seleccionada, modelo actual y estado visibles sin memorizar otra pantalla | Editor y biblioteca con datos reales                    |
| Veracidad              | Sin actividad inventada, «En línea» supuesto ni guardados falsos                 | API y rótulos coinciden                                 |
| Accesibilidad          | Teclado, foco, contraste, reflujo y errores asociados a campos                   | Pruebas automáticas y revisión manual                   |
| Continuidad            | URL, pantalla, sesión e historial describen la misma tarea                       | Abrir enlace, refrescar, atrás y adelante               |

Usar [UI UX Pro Max](https://uupm.cc/) para contrastar decisiones de estilo, color, tipografía, gráficos y estados. Usar [WCAG 2.2](https://www.w3.org/TR/WCAG22/) como referencia propuesta de accesibilidad: contraste 4,5:1 para texto normal y 3:1 para texto grande; foco visible y sin ocultación; tamaño de objetivo conforme a 2.5.8 y sus excepciones. El proyecto puede adoptar 44 px como objetivo cómodo para acciones táctiles, sin presentarlo como mínimo AA universal. La auditoría automática sola no acredita conformidad.

### 2. Dirección visual y sistema de diseño

La propuesta es una interfaz administrativa sobria, con superficies diferenciadas, tipografía legible y acento turquesa reservado para acción, selección y marca. Conservar las referencias de Stitch «Documentos & RAG (Modo Claro)» y «Widget Conversacional Modo Claro» como evidencia visual pendiente de cotejar con sus originales en implementación.

- Tokens semánticos para lienzo, superficie, texto principal/secundario, borde, acción, texto sobre acción, foco, éxito, advertencia y error. Ambos temas comparten estructura y densidad.
- Tipografía Inter ya alojada en el proyecto. Escala propuesta: cuerpo 14–16 px, auxiliares 12–13 px, títulos de sección 18–22 px y título de página 28–32 px. Evitar texto de 9–11 px para información necesaria.
- Espaciado de 4, 8, 12, 16, 24 y 32 px. Bordes y radios coherentes; elevación moderada solamente donde comunica superposición.
- Contraste calculado para turquesa/texto y cada estado. No conservar blanco sobre turquesa si no alcanza el contraste requerido.
- Iconos existentes, mismo trazo; texto junto a acciones esenciales y nombre accesible en botones solo con icono.
- Mismos tamaños de controles en claro y oscuro. Corregir sobrescrituras que cambian simultáneamente color, tamaño y espaciado por tema.
- Movimiento breve para apertura, cierre y confirmación, respetando `prefers-reduced-motion`. Ninguna animación retrasa una acción.

Antes de migrar todas las pantallas, presentar una composición representativa de Resumen, editor y widget en claro y oscuro. Esa revisión fija la composición visual; la funcionalidad y los criterios de navegación ya quedan definidos en esta propuesta. Registrar después las decisiones reales, evitando mantener `desing.md` y otro documento de diseño como autoridades contradictorias.

### 3. Estructura del frontend

Mantener la estructura autorizada. Extraer componentes cuando tengan una responsabilidad o repetición concreta, no por un límite arbitrario de líneas.

```text
frontend/
  app/                       Entradas existentes: /, /preview, not-found
    globals.css              Tokens y estilos verdaderamente globales
  components/
    ui/                      Button, Field, Alert, estados, iconos
    layout/                  Admin shell, sidebar, breadcrumbs
    admin/
      chatbot-wizard/        Pasos, navegación, fuentes, vista visual
      ...                    Resumen, chatbots, documentos, métricas, ajustes
    auth/                    Sesión y acceso
  lib/
    navigation.ts            Interpretación y generación de URL tipadas
  services/                  API, validación e integración existentes
  types/                     Contratos de API y estado compartido necesario
  tests/e2e/                 Recorridos y evidencia de aceptación
widget/
  src/                       Cliente independiente; modularizar si se justifica
  scripts/                   Construcción y verificación existentes
```

Separar primero estilos por componente o módulo CSS usando soporte ya incluido en Next.js; conservar Tailwind para utilidades y tokens según las convenciones existentes. Migrar una pantalla por vez y retirar su regla antigua al mismo tiempo. No crear un segundo sistema de estilos completo.

Alternativas consideradas: reescribir toda la aplicación de una vez aumentaría el riesgo de perder flujos funcionales; instalar un kit UI completo duplicaría componentes existentes. La propuesta favorece migración gradual con pruebas.

### 4. Navegación como contrato único

Conservar inicialmente las URL actuales para no romper marcadores ni código compartido. Un único parser/constructor convierte los parámetros existentes a un estado tipado; el router y los componentes consumen ese estado. Las acciones de navegación usan enlaces reales cuando corresponde; los botones ejecutan acciones.

| Destino        | URL compatible                            | Contexto que debe conservar                                                            |
| -------------- | ----------------------------------------- | -------------------------------------------------------------------------------------- |
| Acceso/Resumen | `/`                                       | La sesión determina la pantalla; no mostrar datos administrativos antes de restaurarla |
| Chatbots       | `/?view=Chatbots`                         | Listado y retorno después de cerrar editor                                             |
| Edición        | `/?view=Chatbots&edit=<uuid>&step=<0..4>` | Identificador válido y existente; paso permitido                                       |
| Creación       | `/?view=Chatbots&mode=create` propuesto   | Modo explícito; nunca inferido de un chatbot inexistente                               |
| Documentos     | `/?view=Documentos`                       | Selección del chatbot según contrato de filtros                                        |
| Métricas       | `/?view=Métricas`                         | Chatbot y periodo aplicados                                                            |
| Configuración  | `/?view=Configuración`                    | Selección de integración                                                               |
| Prueba         | `/preview?chatbot_id=<uuid>&...`          | Apariencia y retorno al editor del chatbot seleccionado                                |
| No encontrado  | Ruta inexistente                          | Explicación y enlace de salida útil                                                    |

`mode=create` es una propuesta de navegación a registrar antes de implementar. Los parámetros de chatbot/periodo de Documentos y Métricas se formalizarán en la misma tabla de rutas, preservando los enlaces sin filtros. Admitir de forma segura los parámetros visuales actuales y `editor_step`; rechazar valores desconocidos sin renderizar estados imposibles.

Resolver edición y creación desde URL, eliminar copias de estado que quedan obsoletas al cambiar historial. No reiniciar un borrador válido por una recarga de datos. Mostrar aviso de cambios sin guardar antes de abandonar una edición sucia; cancelarlo mantiene el borrador. No persistir secretos o adjuntos en URL. El cierre correcto vuelve a `view=Chatbots`, no a `/`.

Breadcrumb propuesto: `Panel operativo › Chatbots › <nombre> › Conocimiento`. Sidebar, título, breadcrumb y URL deben coincidir. En móvil, adaptar la ruta sin cortar el nombre de la tarea; los ancestros siguen disponibles. Gestionar foco al navegar y devolverlo al activador al cerrar menú/modal.

### 5. Plan por pantalla

| Pantalla              | Cambio previsto                                                                              | Criterio visible de finalización                                                    |
| --------------------- | -------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| Acceso                | Campos legibles, mostrar contraseña, errores diferenciados y restauración de sesión          | Un enlace protegido se abre después de autenticar sin perder su destino             |
| Resumen               | Cifras actuales, barras por chatbot, resultado de consultas y fuentes que requieren atención | Todo dato tiene periodo/estado; gráfico vacío no se representa como actividad       |
| Chatbots              | Nombre, descripción, modelo y acciones jerarquizadas; editar/probar/integrar consistentes    | Cualquier acción abre el chatbot elegido; sin controles superpuestos                |
| Editor General        | Nombre, descripción y validación junto al campo                                              | No avanzar con datos obligatorios inválidos                                         |
| Editor Apariencia     | Color, icono y saludo con vista visual fiel                                                  | Lo guardado coincide con la prueba interactiva                                      |
| Editor Comportamiento | Proveedor/modelo e instrucciones con ayuda contextual breve                                  | Valor actual claro; fallo al guardar conserva lo introducido                        |
| Editor Conocimiento   | Cargar, asociar existentes y quitar del contexto; estados de procesamiento                   | Quitar asociación conserva el archivo compartido; texto e imagen distinguidos       |
| Editor Publicación    | Resumen guardado, prueba real y script correcto                                              | Copiar confirma; error de portapapeles ofrece copia manual                          |
| Documentos            | Selección de chatbot, carga visible, lista legible y recuperación de fallos                  | Procesamiento fallido no se presenta como listo; no mostrar fuentes de otro chatbot |
| Métricas              | Filtros claros, unidad de respuesta y muestras válidas                                       | Ausencia de muestras se muestra «Sin datos», no 0 ms                                |
| Configuración         | Agrupar proveedores, widget y conocimiento; estados informativos veraces                     | No presentar orígenes ni claves como editables sin una operación implementada       |
| Vista previa          | Contexto de prueba explícito, widget real y retorno correcto                                 | Regresar conserva chatbot y paso; una sesión válida no vuelve a login               |
| Widget externo        | Conversación legible, adjuntar/pegar/capturar/quitar y respuesta de errores                  | Probado desde otro origen HTTP(S), sin depender del frontend anfitrión              |
| No encontrado         | Explicación breve y salida coherente                                                         | Ruta desconocida y chatbot ausente tienen recuperaciones distintas                  |

No añadir tendencias temporales con la API actual: hoy entrega agregados por chatbot/periodo. Una gráfica diaria necesita agrupación temporal real. Conservar diferencia entre solicitudes completadas, fallidas y en proceso; no calcular satisfacción a partir de éxito técnico.

### 6. Estados y accesibilidad

Cada flujo debe especificar: inicial, carga, vacío, datos, envío, éxito, validación, fallo recuperable, sesión expirada y recurso no disponible cuando corresponda. Estados especiales: cero modelos, archivo excedido o no admitido, procesamiento fallido, captura cancelada/no soportada, portapapeles denegado, backend caído, consulta limitada y chatbot eliminado.

Reutilizar componentes UI. Asociar errores con `aria-describedby`, anunciar resultados sin mover el foco innecesariamente, evitar doble envío, mantener texto y adjunto tras un fallo cuando sea seguro reintentar. No usar solo color para estados. Tablas, nombres de archivo largos, código y mensajes extensos deben tener política de reflujo o desplazamiento local.

Verificar escritorio a 1440 y 1089 px, tableta a 768 px, móvil a 390 px y reflujo a 320 px; ambos temas y zoom de 200 %. Son dimensiones de prueba propuestas, no umbrales de rendimiento. El menú móvil debe manejar apertura, Escape, foco y fondo inactivo.

### 7. Plan de enlaces y acciones sin fallos

Crear un registro de destinos con origen, acción, destino esperado, precondición de sesión/recurso, resultado y evidencia. Cubrir enlaces, botones de navegación, fragmentos, recursos, scripts generados y llamadas API. No convertir errores de API en supuestos enlaces rotos ni aceptar una página de login como destino correcto para una sesión vigente.

| Caso                            | Comprobación                                                                  |
| ------------------------------- | ----------------------------------------------------------------------------- |
| L01 Navegación principal        | Las cinco secciones abren contenido, URL y breadcrumb coherentes              |
| L02 Enlace profundo             | Abrir editor guardado directamente y refrescar mantiene chatbot y paso        |
| L03 Historial                   | Atrás/adelante entre secciones, dos chatbots y pasos restaura el destino      |
| L04 Cierre                      | Cerrar editor vuelve a Chatbots; refrescar sigue en Chatbots                  |
| L05 Vista previa                | Abrir desde listado/editor/ajustes y volver al chatbot correcto               |
| L06 Sesión vigente              | Refrescar y volver desde vista previa conserva acceso                         |
| L07 Sesión vencida              | Informa reautenticación; tras login recupera solo un destino interno validado |
| L08 Recurso eliminado           | UUID válido inexistente muestra salida; nunca abre creación por accidente     |
| L09 Parámetros inválidos        | UUID, paso, vista y color malformados producen recuperación definida          |
| L10 Navegación nueva pestaña    | Enlaces internos relevantes funcionan al abrir en otra pestaña                |
| L11 Fragmento                   | «Ir al contenido» mueve el foco al área principal                             |
| L12 Recursos                    | JS, CSS, fuente, favicon e imágenes sin fallos inesperados ni MIME incorrecto |
| L13 Script generado             | Copiar e insertar carga el chatbot esperado desde un sitio independiente      |
| L14 Origen autorizado           | Consulta válida llega a la API; origen denegado muestra error comprensible    |
| L15 Capacidades del navegador   | Portapapeles/captura denegados o no soportados tienen alternativa             |
| L16 404                         | Ruta desconocida responde con recuperación y retorno al panel                 |
| L17 Borrador                    | Cancelar abandono conserva campos; confirmar sigue el destino elegido         |
| L18 Rutas externas documentadas | Comprobar enlaces reales; registrar bloqueos externos separadamente           |

Pruebas unitarias para parser/constructor de URL y validación de retornos; pruebas de navegador para flujos. Usar fixtures deterministas para visuales/errores y una prueba integrada con backend de test y PostgreSQL para el recorrido principal. Aislar datos de prueba de los chatbots del usuario. En el widget, automatizar pegado/selección donde el navegador permita; comprobar manualmente el selector nativo de captura y su cancelación. Registrar las pruebas manuales pendientes, sin marcarlas aprobadas.

El sitio externo de prueba debe levantarse como sitio estático independiente; solo consume el script público y API. Mantener `example` sin imports, dependencias o acceso a datos internos del proyecto. Un fixture de QA separado puede reproducir esa integración.

### 8. Rendimiento, seguridad y evidencia

Medir navegación, solicitudes repetidas, carga del widget, tamaño de recursos y respuesta percibida antes/después con el mismo conjunto de datos. El SRS no fija presupuestos numéricos de frontend; proponerlos con la línea base, sin inventar una promesa de Lighthouse o tiempo de LLM.

Mantener credenciales en backend, validar destinos de retorno internos y conservar autorización en API. No usar URLs o capturas de prueba para publicar tokens. El aislamiento de fuentes y las reglas de eliminación no cambian por el rediseño. La sesión actual usa almacenamiento local: documentarlo correctamente sin introducir una migración de autenticación implícita en esta propuesta visual.

Entregar un informe de aceptación con versión/commit, entorno, matriz de casos, resultado, captura o traza y riesgos pendientes. La revisión visual se hace en una pasada conjunta de tamaños y temas, una corrección agrupada y una confirmación; repetir después únicamente si aparece un fallo concreto o una nueva modificación.

## Risks / Trade-offs

- [Regresión por retirar CSS global] → Migrar por componente y comparar capturas de ambos temas antes de retirar reglas.
- [Pérdida de borradores al unificar navegación] → Probar historial y cambios sin guardar antes de continuar con el acabado visual.
- [Falsa equivalencia entre maqueta y widget] → Comparar el mismo contenido y configuración; identificar la vista estática como vista visual sin declarar conectividad.
- [Control visible sin backend] → Mantenerlo informativo o registrar una extensión funcional separada.
- [Respuesta variable del LLM] → Separar fixtures deterministas de una prueba integrada; registrar tiempos sin prometer una latencia fija.
- [Enlace externo cambia tras publicar] → Auditoría al liberar; la garantía de cero fallos se limita a la matriz y versión comprobadas.
- [Cambios locales previos extensos] → Inventariar antes de aplicar, preservar trabajo existente y hacer entregas pequeñas reversibles.

## Migration Plan

| Fase                     | Entrega                                                                              | Dependencia y salida                                          |
| ------------------------ | ------------------------------------------------------------------------------------ | ------------------------------------------------------------- |
| 0. Base verificable      | Inventario, matriz de navegación, requisitos conciliados, capturas y datos de prueba | Conflictos documentales identificados y trazabilidad acordada |
| 1. Navegación            | Fuente única de ruta, editor, sesión, historial y recuperación                       | L01–L11 y L16–L17 aprobados                                   |
| 2. Sistema visual        | Tokens, componentes y composición representativa de ambos temas                      | Revisión de referencia y estados de controles aprobada        |
| 3. Shell y pantallas     | Resumen, listado, documentos, métricas y configuración                               | Pantallas sin regresiones de navegación ni estados falsos     |
| 4. Editor y conversación | Cinco pasos, vista fiel, adjuntos y widget                                           | Crear/configurar/probar funciona de extremo a extremo         |
| 5. Integración externa   | Script, origen permitido/denegado, recursos y errores                                | L12–L15 y prueba externa aprobados                            |
| 6. Cierre de calidad     | Accesibilidad, responsividad, pruebas y evidencia de liberación                      | Ningún caso obligatorio fallido o sin revisar                 |

Estimar duración después del inventario y las composiciones, usando complejidad real y evidencia; no fijar una fecha arbitraria en esta propuesta. Mantener cada fase en cambios pequeños. Revertir la fase que falle mediante sus cambios de código conservando compatibilidad de URL y datos; no hay migración de base de datos que revertir. No publicar una fase incompleta que suprima una función existente.

## Open Questions

- Preferencia visual solicitada al usuario: conservar identidad turquesa/Stitch o explorar otra. El plan usa la primera como supuesto provisional; la respuesta ajusta composición y tokens, no elimina las pruebas funcionales.
- Logo final pendiente: conservar la marca actual hasta elegir expresamente una propuesta.
- Dominio definitivo de despliegue: confirmar al verificar el script publicado; usar entornos locales independientes mientras tanto.
