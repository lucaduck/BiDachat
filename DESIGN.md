---
name: BIDACHAT
description: "Sistema visual implementado para la aplicación web de BI-DATA."
colors:
  canvas: "#f5f8fb"
  surface: "#ffffff"
  surface-muted: "#edf3f7"
  sidebar: "#ffffff"
  subtle: "#e7f6fa"
  border: "#d5e2eb"
  text: "#163247"
  muted: "#526a7e"
  primary: "#0aa8c6"
  on-primary: "#062a36"
  link: "#086e89"
  focus: "#087a99"
  success: "#087356"
  success-bg: "#e9f7f1"
  warning: "#865414"
  warning-bg: "#fff6e5"
  danger: "#b02c38"
  danger-bg: "#fff0f1"
  dark-canvas: "#091521"
  dark-surface: "#102332"
  dark-surface-muted: "#172e40"
  dark-sidebar: "#0d1e2c"
  dark-subtle: "#153a48"
  dark-border: "#2b465a"
  dark-text: "#eef5fb"
  dark-muted: "#a6bdce"
  dark-primary: "#35c5df"
  dark-link: "#76d8ea"
  dark-focus: "#6ed9eb"
  dark-success: "#7ce3bd"
  dark-success-bg: "#163a32"
  dark-warning: "#f4cb7b"
  dark-warning-bg: "#3d301e"
  dark-danger: "#ffadb6"
  dark-danger-bg: "#422832"
  code-panel: "#0e2333"
  code-text: "#dfeef7"
  widget-accent: "#14a8ce"
  widget-on-accent-dark: "#08111f"
typography:
  headline:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: "clamp(26px, 2.5vw, 34px)"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "-0.025em"
  title:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: "20px"
    fontWeight: 650
    lineHeight: 1.35
  title-small:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: "17px"
    fontWeight: 650
  body:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.6
  label:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: "13px"
    fontWeight: 600
  button:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: "13px"
    fontWeight: 650
    lineHeight: 1.35
  caption:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: "12px"
    fontWeight: 400
    lineHeight: 1.5
  step-label:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: "12px"
    fontWeight: 650
    letterSpacing: "0.025em"
  metric:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: "30px"
    fontWeight: 650
    lineHeight: 1.25
    letterSpacing: "-0.025em"
  workspace-signature:
    fontFamily: "Caveat, cursive"
    fontSize: "34px"
    fontWeight: 400
    lineHeight: 0.8
  workspace-signature-mobile:
    fontFamily: "Caveat, cursive"
    fontSize: "30px"
    fontWeight: 400
    lineHeight: 0.8
  chatbot-activity-value:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: "28px"
    fontWeight: 700
    letterSpacing: "-0.025em"
  code:
    fontFamily: "ui-monospace, SFMono-Regular, Consolas, monospace"
    fontSize: "12px"
    lineHeight: 1.6
rounded:
  badge: "6px"
  compact: "7px"
  control: "8px"
  button: "9px"
  tile: "10px"
  panel: "12px"
  workspace-brand: "14px"
  dialog: "16px"
  circle: "50%"
spacing:
  space-4: "4px"
  space-6: "6px"
  space-8: "8px"
  space-10: "10px"
  space-12: "12px"
  space-14: "14px"
  space-16: "16px"
  space-18: "18px"
  space-20: "20px"
  space-24: "24px"
  space-28: "28px"
  space-32: "32px"
  space-36: "36px"
  space-40: "40px"
  space-48: "48px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.button}"
    rounded: "{rounded.button}"
    padding: "10px 16px"
  button-primary-hover:
    backgroundColor: "color-mix(in srgb, var(--primary) 88%, var(--text))"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    typography: "{typography.button}"
    rounded: "{rounded.button}"
    padding: "10px 16px"
  button-secondary-hover:
    backgroundColor: "{colors.surface-muted}"
  button-quiet:
    backgroundColor: "transparent"
    textColor: "{colors.link}"
    typography: "{typography.button}"
    rounded: "{rounded.button}"
    padding: "10px 8px"
  button-danger:
    backgroundColor: "{colors.danger}"
    textColor: "{colors.surface}"
    typography: "{typography.button}"
    rounded: "{rounded.button}"
    padding: "10px 16px"
  button-disabled:
    backgroundColor: "{colors.surface-muted}"
    textColor: "{colors.muted}"
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    rounded: "{rounded.control}"
    padding: "11px 12px"
  navigation:
    backgroundColor: "transparent"
    textColor: "{colors.muted}"
    rounded: "{rounded.control}"
    padding: "11px 12px"
  navigation-current:
    backgroundColor: "{colors.subtle}"
    textColor: "{colors.link}"
  badge:
    backgroundColor: "{colors.subtle}"
    textColor: "{colors.link}"
    rounded: "{rounded.badge}"
    padding: "4px 8px"
  content-panel:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    rounded: "{rounded.panel}"
    padding: "24px"
  alert-info:
    backgroundColor: "{colors.subtle}"
    textColor: "{colors.text}"
    rounded: "{rounded.button}"
    padding: "14px 16px"
  alert-error:
    backgroundColor: "{colors.danger-bg}"
    textColor: "{colors.danger}"
    rounded: "{rounded.button}"
    padding: "14px 16px"
  workspace-signature:
    textColor: "{colors.muted}"
    typography: "{typography.workspace-signature}"
  workspace-signature-mobile:
    typography: "{typography.workspace-signature-mobile}"
  workspace-brand-banner:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    rounded: "{rounded.workspace-brand}"
    padding: "20px 24px"
  workspace-brand-banner-dark:
    backgroundColor: "#0e253e"
    textColor: "#eef6ff"
  chatbot-activity-card:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.workspace-brand}"
    padding: "18px 20px"
  login-card:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.dialog}"
    padding: "24px"
    width: "min(100%, 1100px)"
  login-identity:
    backgroundColor: "#071221"
    rounded: "8px 160px 8px 8px"
  login-input:
    backgroundColor: "{colors.surface-muted}"
    textColor: "{colors.text}"
    rounded: "24px"
    padding: "11px 48px 11px 18px"
  login-submit:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    rounded: "24px"
    padding: "10px 16px"
  widget-message-assistant:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    rounded: "13px 13px 13px 3px"
    padding: "10px 12px"
  widget-message-user:
    backgroundColor: "{colors.widget-accent}"
    textColor: "{colors.widget-on-accent-dark}"
    rounded: "13px 13px 3px 13px"
    padding: "10px 12px"
---

# Design System: BIDACHAT

## Overview

**Creative North Star: "BI-DATA"**

BIDACHAT conserva la identidad BI-DATA con Inter alojada en la aplicación, acciones turquesa y superficies legibles en temas claro y oscuro. La firma del panel «Datos que conversan» añade Caveat manuscrita y las marcas de circuitos suministradas por el usuario. La tipografía, los bordes discretos y el espacio entre controles facilitan el trabajo de investigación.

Este documento registra el sistema implementado y es la autoridad visual actual. Los tokens del frontmatter describen valores reales del código; el prefijo `dark-` identifica su variante oscura, mientras el código conserva los mismos nombres de variables dentro de `data-theme="dark"`. Los valores de componentes sin prefijo expresan el tema claro y cambian mediante las variables semánticas. La estrategia de cada superficie vive en [.impeccable/surfaces/admin-workspace.md](.impeccable/surfaces/admin-workspace.md) y el acceso en [.impeccable/surfaces/login-screen.md](.impeccable/surfaces/login-screen.md). El archivo histórico `desing.md` no gobierna la interfaz actual.

**Key Characteristics:**

- Identidad BI-DATA, Inter y turquesa conservados; Caveat identifica la firma manuscrita del panel.
- Temas claro y oscuro con las mismas funciones.
- Superficies administrativas delimitadas por bordes y capas tonales.
- Estados visibles con texto, foco de teclado y recuperación comprensible.

**The Source Authority Rule.** Documenta valores implementados y preserva la identidad acordada; la copia histórica no sustituye esta autoridad visual.

## Colors

Turquesa funcional sobre neutros azulados: tonos claros para el tema claro y azul marino para el tema oscuro. Los valores normativos están en el frontmatter; no hay un segundo acento global.

### Primary

- **Turquesa BI-DATA:** `primary` y `dark-primary`, para acciones y progreso actual. El texto de estas acciones usa `on-primary` en ambos temas.
- **Turquesa de lectura y foco:** `link` y `focus`, con sus variantes oscuras, separan enlaces y señal de teclado de la superficie de acción.
- **Turquesa suave de selección:** `subtle` y `dark-subtle` sostienen navegación activa, iconos y selección de opciones.
- **Acento del widget:** `widget-accent` es el valor predeterminado del widget independiente, configurable por chatbot. Su texto se decide según la luminancia entre `widget-on-accent-dark` y `surface`; no se fuerza el acento administrativo sobre una configuración guardada.

### Neutral

- **Lienzo azul pálido / azul marino:** `canvas` y `dark-canvas`, fondo general.
- **Superficie blanca / marino elevado:** `surface` y `dark-surface`, campos y paneles; `sidebar` y `dark-sidebar`, navegación.
- **Superficie secundaria:** `surface-muted` y `dark-surface-muted`, agrupación tenue y controles deshabilitados.
- **Borde azul gris:** `border` y `dark-border`, contención y separación.
- **Texto principal y secundario:** `text` y `muted`, con sus variantes oscuras, sostienen jerarquía sin usar negro puro.
- **Código de integración:** `code-panel` y `code-text` forman el bloque oscuro de fragmentos en ambos temas. Es una pareja implementada en publicación y ajustes, no un tema adicional.

### Semantic states

Éxito usa `success` sobre `success-bg`; advertencia usa `warning` sobre `warning-bg`; error usa `danger` sobre `danger-bg`. Cada pareja tiene variante oscura. Los avisos coloreados mezclan el color semántico al 30 % con `border` para delimitar el mensaje. El estado listo, fallido o en proceso incluye texto además de la marca de color.

**The Semantic Theme Rule.** Usa las variables semánticas del tema activo para texto, superficies, acciones y estados; conserva la misma función en ambos temas.

## Typography

**Body and heading font:** Inter variable, alojada en `/fonts/inter-variable.woff2`, con `ui-sans-serif`, `system-ui` y `sans-serif` como alternativas. La fuente declara pesos de 100 a 900 y carga con `font-display: swap`. El widget carga el mismo archivo bajo el nombre local `BIDACHAT Inter` para aislarse de la página anfitriona.

**Panel signature font:** Caveat variable, alojada en `/fonts/caveat-variable.ttf`, con `cursive` como alternativa, pesos declarados de 400 a 700 y `font-display: swap`. Su licencia se conserva en `frontend/public/fonts/caveat-license.txt`. Se reserva para la firma obligatoria del panel.

**Code font:** pila de monoespaciadas del token `code`; los fragmentos de publicación y orígenes usan también `ui-monospace, monospace`.

### Hierarchy

- **Headline:** encabezado principal adaptable del token `headline`; títulos equilibrados, con ajuste de palabras largas.
- **Title / title-small:** secciones y subsecciones, según los tokens homónimos. Las variantes observadas incluyen título del editor de 22 px y título de paso de 20 px.
- **Body:** contenido administrativo de 14 px. Los párrafos usan interlineado 1.6 y ancho máximo de 75 caracteres. Descripciones de panel y editor usan 13 px.
- **Label / button:** etiquetas de campos y acciones, según sus tokens. La navegación usa 13 px, peso 550 en reposo y 650 cuando está seleccionada.
- **Caption:** ayudas de campo de 12 px con interlineado 1.5. Hay metadatos de 11 px y marcas compactas de 10 px en contextos secundarios específicos; no son la escala del texto principal.
- **Step label:** 12 px, mayúsculas y espaciado de letras del token `step-label`, incluso en el recorrido móvil.
- **Metric:** números tabulares del token `metric`, reducidos a 26 px y luego 24 px según el espacio de la superficie.

Inter gobierna los controles, títulos y lectura; Caveat identifica únicamente la firma manuscrita «Datos que conversan» del panel. La monoespaciada identifica material técnico copiable. Los tokens `workspace-signature` y `workspace-signature-mobile` registran sus tamaños; la segunda variante se aplica a 768 px. El valor de actividad del listado usa `chatbot-activity-value`.

## Layout

El sistema usa contenedores fluidos, columnas con `minmax(0, 1fr)`, separación explícita y contenido largo que puede envolver. La escala del frontmatter recoge medidas realmente reutilizadas; el espacio de 8 px está declarado como base, sin imponer que todos los intervalos sean múltiplos de ocho. Los componentes conservan su densidad propia.

### Implemented surfaces — surface strategy

Las siguientes composiciones describen las superficies existentes. Su propósito, orden de contenido y modo Operate pertenecen al brief del workspace, no a una regla universal para nuevas superficies.

- **Workspace:** sidebar de 248 px, o 80 px contraída, y columna flexible. La sidebar es sticky y ocupa `100dvh`; la barra superior tiene altura mínima de 72 px. El contenido tiene máximo de 1520 px y relleno de 28 px 36 px 48 px. A 1100 px la sidebar se reduce a 224 px y el relleno horizontal a 24 px. A 768 px la navegación pasa a cabecera móvil con menú y fondo de bloqueo; contenido a 24 px 20 px 40 px. A 360 px el relleno horizontal baja a 14 px.
- **Resumen:** cuatro métricas contiguas dentro de un único grupo; gráficos en columnas de proporción 1.35 a 1 con separación de 24 px. A 1100 px los gráficos pasan a una columna; a 600 px las métricas pasan a dos columnas. Los paneles tienen 24 px de relleno, los ajustes y el editor 28 px; a 600 px bajan a 20 px.
- **Listado de chatbots:** cuatro contadores de actividad en tarjetas separadas, con separación de 18 px; a 768 px pasan a dos columnas, separación de 12 px y relleno de 16 px. Debajo, las tarjetas de chatbot y la tarjeta accionable de creación forman tres columnas con separación de 20 px; a 1100 px pasan a dos y a 768 px a una. Las cifras proceden de consultas registradas y chatbots configurados; no se incorporan cuentas, planes, satisfacción ni tendencias ficticias de la referencia.
- **Firma y banner del panel:** firma de dos líneas junto al encabezado y banner BI-DATA al final del listado. El banner tiene altura mínima de 104 px y separación interna de 28 px; a 1100 px la separación baja a 20 px y se oculta el bloque secundario de valores. A 768 px se apila, usa separación de 18 px y relleno de 20 px; conserva la marca y el mensaje.
- **Métricas:** filtros en cuatro columnas con separación de 18 px, dos a 1100 px y una a 600 px con separación de 16 px. Los gráficos de volumen y latencia usan dos columnas con separación de 20 px, una a 1100 px; a 600 px cada gráfico usa relleno de 20 px 12 px. El SVG adapta el ancho del lienzo al contenedor y conserva un viewBox de 215 unidades de altura y texto de ejes de 12 px; las fechas se centran sobre su posición para mantenerlas separadas en pantallas estrechas. La tabla de valores desplaza su interior sin ensanchar la página.
- **Editor:** progreso de cinco columnas; a 1200 px número y etiqueta se apilan. Campos y apariencia se distribuyen en dos columnas iguales con separación de 28 px; a 1000 px pasan a una y la apariencia conserva máximo de 420 px. A 600 px el progreso es una tira horizontal con separación de 18 px: el paso actual se centra ajustando únicamente el desplazamiento horizontal de la tira, sin mover la página.
- **Ajustes de integración:** selector y enlace de vista previa se apilan a 600 px. Una confirmación textual debajo conserva el nombre completo del chatbot seleccionado y permite envolverlo.
- **Acceso:** tarjeta `login-card` con dos columnas iguales de identidad y formulario. El lienzo usa 28 px 40 px y el formulario 56 px 44 px; a 1000 px bajan a 24 px y 40 px 28 px, respectivamente. A 760 px la tarjeta apila identidad y formulario, tiene máximo de 480 px y relleno de 16 px; el lienzo usa 20 px 16 px y el formulario 30 px 12 px 20 px. A 360 px el relleno horizontal del formulario baja a 4 px. La composición aprobada y su verificación se registran en el contrato de acceso.
- **Widget:** panel de ancho `min(420px, calc(100vw - 32px))` y altura `min(640px, calc(100dvh - 48px))`, anclado a 24 px del borde inferior y derecho. A 480 px los márgenes son de 12 px y el panel se ajusta al viewport con 24 px de reserva. A 350 px se oculta solo el texto visual de Enviar y permanece su etiqueta accesible. La vista de apariencia ocupa un iframe de 400 px de altura.

## Elevation & Depth

La administración utiliza bordes y contraste tonal; los paneles, tarjetas de chatbot, editor y campos no tienen sombras. La tarjeta de acceso incorpora la sombra ambiental de su referencia aprobada como excepción local. La profundidad flotante corresponde al widget sobre el dashboard y al fondo del menú móvil.

### Shadow Vocabulary

- **Login card:** `0 20px 60px rgb(6 24 38 / 12%)`, exclusivamente en la tarjeta de acceso.
- **Widget launcher:** `0 10px 28px rgb(16 51 70 / .2)`.
- **Widget panel:** `0 20px 45px rgb(20 62 83 / .18), 0 3px 10px rgb(18 52 72 / .06)`.
- **Widget assistant message:** `0 2px 6px rgb(22 52 71 / .035)`.

El fondo móvil es `rgb(4 16 26 / 0.4)`. En la vista de apariencia, el widget se integra sin sombra ni borde propio del panel flotante.

## Shapes

Las formas redondeadas distinguen contención y control: campos y navegación usan `control`, botones y avisos `button`, paneles `panel`, marcas e iconos contenidos `tile`. Insignias y pequeños controles usan `badge` o `compact`. El acceso y el panel flotante usan `dialog`. Los números de paso y las señales puntuales usan `circle`.

El acceso conserva variantes locales: `login-identity` reduce su esquina superior derecha a 110 px a 1000 px y a 80 px a 760 px; `login-input` y `login-submit` tienen radio de 24 px. Los acentos turquesa de las esquinas pertenecen a esta composición aprobada.

Bordes de 1 px delimitan superficies; los espacios de carga vacíos usan borde discontinuo. Los mensajes del widget conservan radios asimétricos para distinguir usuario y asistente. El contorno de foco se añade por fuera del control; no cambia su geometría.

## Components

### Buttons

Acciones legibles y contenidas. Hay cuatro variantes implementadas: primaria, secundaria, discreta y destructiva. Forma, relleno y colores figuran en el frontmatter; la altura mínima general es 42 px. Las acciones compactas de filas usan mínimo de 38 px, relleno de 8 px 12 px y texto de 12 px.

El hover primario mezcla `primary` al 88 % con `text`; la secundaria pasa a `surface-muted`. La regla compartida de hover también se aplica actualmente a las variantes discreta y destructiva. No hay tratamiento visual separado para `:active`. Deshabilitado usa superficie secundaria, texto tenue y borde; carga muestra spinner, `aria-busy` y deshabilita la acción. La transición de fondo dura 0.15 s.

### Inputs / Fields

Campos de altura mínima de 44 px, con etiqueta visible, contenedor de 8 px de separación, borde de 1 px y los tokens de `input`. El hover cambia el borde a `muted`; error cambia el borde y mensaje a `danger`, y comunica `aria-invalid` y `aria-describedby`. El placeholder usa `muted` sin reducir opacidad. Las áreas de texto tienen mínimo de 104 px y permiten cambiar altura. Los controles nativos deshabilitados conservan el comportamiento del navegador; no existe una paleta de campo deshabilitado adicional.

### Navigation

Enlace de mínimo 44 px, icono de contorno y texto. Reposo usa `muted`, hover usa `surface-muted` y `text`, y la página actual usa `subtle`, `link` y peso 650 con `aria-current="page"`. La contraída mantiene iconos y nombres accesibles. El menú móvil enfoca su primer enlace, contiene la navegación con Tab y cierra con Escape devolviendo el foco al control de apertura. Tema y contracción persisten; la ruta y breadcrumb identifican la tarea activa.

### Chips / status labels

Insignias compactas `badge` para configuración y recuentos, con texto de 11 px y peso 550. Estados de documentos usan fondo tenue en reposo, pareja de éxito para listo y pareja de error para fallido. No son controles interactivos ni filtros. Las opciones de icono y fuentes sí son controles reales: borde y texto `link`, fondo `subtle` al seleccionar y entrada nativa asociada.

En Apariencia, las propuestas de colores e iconos usan grupos de radio con nombre visible y dos columnas; a 360 px pasan a una columna. Las muestras de color acompañan al nombre y al estado del control, sin depender solo del color. El selector personalizado conserva el hexadecimal actual. Los ocho colores sugeridos pertenecen a la personalización del widget; no sustituyen la paleta administrativa.

### Cards / Containers

Panel `content-panel` como agrupación general, con borde y sin sombra. Tarjetas de chatbot apilan identidad, texto y acciones; los nombres permiten envolver. El grupo de métricas del resumen conserva separadores internos y números tabulares. Los contadores de actividad del listado son cuatro tarjetas independientes con el radio `workspace-brand`; sus cifras también son tabulares. La tarjeta de creación usa borde discontinuo `link`, altura mínima de 300 px y un botón que abre la creación; su hover usa `subtle`. El área vacía ofrece título, explicación y acción disponible, con relleno de 48 px 24 px y borde discontinuo.

La tarjeta de acceso usa `login-card` y la sombra local registrada en Elevation & Depth. Su panel `login-identity` conserva el logo suministrado `docs/brand/Logo BIDACHAT DARK.png` en ambos temas mediante `/brand/logo-bidachat-dark.png`, con máximo de 480 px y ancho de 200 px a 760 px. El título usa `clamp(28px, 2.5vw, 36px)` e interlineado 1.2; campos y envío tienen altura mínima de 48 px con sus variantes locales del frontmatter. Conservan etiquetas, foco, error y carga compartidos; el control de tema está disponible antes de autenticarse y la contraseña puede mostrarse u ocultarse.

### Panel signature and circuit branding

«Datos que conversan» se presenta en dos líneas: «Datos que» y «conversan». Usa Caveat, color `muted`, interlineado del token de firma y rotación de −9 grados. La segunda línea se desplaza 32 px, tiene relleno inferior de 6 px y subrayado mediante borde de 2 px en `primary`. La firma permanece visible en ambos temas y en móvil.

La marca de circuitos conserva los PNG originales: `docs/brand/Logotipo BC de Circuitos Tecnológicos.png` en claro, servido como `/brand/logo-bc-circuit-light.png`, y `docs/brand/Logotipo BC de Circuito Futurista.png` en oscuro, servido como `/brand/logo-bc-circuit.png`. El mismo componente selecciona la imagen por tema y se reutiliza a 46 px en la sidebar y 56 px en el banner. Las imágenes decorativas llevan alternativa vacía; el nombre de marca queda en texto. La marca de acceso conserva su propio recurso.

La sidebar y el banner reutilizan esos originales como máscaras CSS de luminancia, con opacidad de 0.12 y 0.1, respectivamente. En claro la máscara combina una capa blanca y el original claro mediante exclusión para conservar los circuitos sin su fondo. La máscara de la sidebar se oculta cuando está contraída y a 768 px; la del banner permanece decorativa detrás del contenido.

El banner claro usa `surface`, `text`, `border` y `muted`. El oscuro usa la variante local `workspace-brand-banner-dark`, borde `#234864`, divisor `#326282` y texto secundario `#b8d3e8`; su máscara usa `dark-primary`. Estos valores pertenecen a la marca del panel y no reemplazan los tokens globales del tema.

### Query-backed metrics

Volumen por periodo, tiempo medio de respuesta en milisegundos y distribución de estados representan registros reales de consultas del chatbot seleccionado. Los filtros ofrecen historial completo, últimos 7/30/90 días o fechas personalizadas UTC que incluyen el día final, estado y agrupación por día, semana o mes. Los filtros aplicados persisten en la URL. No disponible, vacío, carga y error con reintento tienen texto explícito; un tiempo ausente no se transforma en una medición de cero.

Barras, línea y puntos usan `link`; los ejes usan `muted` y la cuadrícula `border`. Los SVG tienen nombre accesible y remiten a una tabla desplegable con caption, encabezados y valores tabulares, alojada en un contenedor con desplazamiento interior. La distribución de resultados combina color semántico, nombre de estado y cantidad.

### Alerts / loading

Avisos informativos, éxito, advertencia y error usan las parejas semánticas y texto explícito. Error anuncia `role="alert"`; los demás avisos y carga usan `role="status"`. El spinner gira en 0.8 s lineal; `prefers-reduced-motion: reduce` elimina las animaciones, transiciones y desplazamiento suave de la interfaz administrativa.

### Editor progress and widget preview

Cada paso muestra número, etiqueta y estado; el actual usa `aria-current="step"` y la pareja primaria, y los completos muestran una marca con éxito. El progreso es informativo. La apariencia renderiza el widget real en iframe, refleja el tema de la aplicación y actualiza la configuración tras 200 ms; comunica que la conversación se prueba en Publicación. Esa composición pertenece a la superficie del editor.

### Conversational widget

Componente independiente aislado mediante Shadow DOM. La cabecera usa identidad, icono y cierre; el historial desplazable anuncia mensajes mediante `role="log"`; usuario y asistente se diferencian por alineación, color y geometría. El composer ofrece adjuntar, capturar, escribir y enviar con nombres accesibles. La imagen adjunta muestra miniatura, nombre y tamaño, y permite quitarla. Durante una consulta hay texto de procesamiento, `aria-busy` y controles deshabilitados; al fallar se recupera la pregunta y se conserva la imagen para reintento. Abrir enfoca la pregunta; cerrar devuelve el foco al lanzador. Su foco usa contorno de 2 px y separación de 2 px.

**The Visible Focus Rule.** Conserva el foco visible y las etiquetas de los controles. El color de un estado siempre acompaña texto.

El foco administrativo usa contorno de 3 px y separación de 3 px con `focus`. Los iconos administrativos son SVG de contorno, normalmente de 20 px, con trazo de 1.7; botones usan 18 px. El widget usa trazo de 1.8. Los iconos decorativos no sustituyen el nombre del control.

## Do's and Don'ts

### Do:

- **Do** usar las variables semánticas del tema activo y conservar la identidad BI-DATA.
- **Do** reutilizar botones, campos, avisos y navegación existentes con sus estados reales.
- **Do** mantener etiquetas visibles, foco de teclado y texto que explique los estados.
- **Do** permitir nombres largos, fragmentos de integración y documentos sin recortar información necesaria.
- **Do** mantener los cambios de composición específicos en el brief de la superficie.

### Don't:

- **Don't** convertir la paleta histórica en tokens actuales.
- **Don't** añadir familias tipográficas, acentos decorativos o componentes que el sistema implementado no utiliza.
- **Don't** presentar el color como la única señal de éxito, error, selección o progreso.
- **Don't** trasladar las sombras del widget a los paneles administrativos planos.
- **Don't** promover la composición de una pantalla a una prohibición visual global.

### Extraction sources

- `frontend/app/globals.css` — tokens de tema, tipo, controles, avisos, foco y movimiento reducido.
- `frontend/components/layout/admin-shell.css`, `admin-shell.tsx` y `workspace-brand-banner.tsx` — shell, navegación, firma, banner, persistencia y teclado.
- `frontend/components/ui/brand.tsx` y `circuit-logo.tsx` — reutilización de los originales de circuitos por tema.
- `frontend/components/admin/metrics.css`, `metrics-panel.tsx` y `metrics-charts.tsx` — filtros, gráficos adaptables, fechas centradas y tabla accesible.
- `frontend/components/admin/chatbot-activity.tsx` y `chatbot-management.tsx` — contadores reales, listado y creación.
- `frontend/components/admin/admin-panels.css` y `settings-panel.tsx` — paneles, métricas, estados, fragmentos y selección.
- `frontend/components/admin/chatbot-wizard/wizard.css`, `chatbot-wizard.tsx` y `widget-preview.tsx` — editor y apariencia real.
- `frontend/components/ui/button.tsx`, `field.tsx`, `status.tsx` e `icon.tsx` — API y estados de componentes.
- `frontend/components/auth/login.css` y `login-screen.tsx` — superficie de acceso; contrato en `.impeccable/surfaces/login-screen.md`.
- `widget/src/bidachat-widget.js` — cliente flotante, conversación y adaptación.

Extracción del código adoptado; no constituye por sí misma una verificación de navegador, contraste, lector de pantalla ni aceptación funcional. La evidencia de QA vive en `docs/qa/frontend/`.
