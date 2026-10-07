# Frontend

El menú lateral incluye **Configuración**, con los modelos registrados, el estado
de las credenciales (sin exponerlas), los ajustes de embeddings y sesión, y el
generador del código del widget. Los ajustes del servidor son de solo consulta;
se modifican mediante la configuración del despliegue.

Interfaz administrativa de BIDACHAT construida con Next.js, TypeScript y Tailwind CSS.

## Desarrollo local

```powershell
cd frontend
npm install
npm run dev
```

La aplicación queda disponible en `http://localhost:3000`. Los servicios cliente vivirán en `services/` y solo consumirán la API FastAPI; nunca deben contener secretos, credenciales ni acceso directo a bases de datos o proveedores LLM.

En Docker, Nginx envía `/api/v1/*` a FastAPI y las demás rutas a Next.js bajo el mismo origen. Al ejecutar Next.js fuera de Compose, su rewrite envía `/api/v1/*` al backend indicado por `BACKEND_API_ORIGIN` (`http://127.0.0.1:8000` por defecto). Esta variable se usa solo en el servidor. La sesión administrativa se conserva en el almacenamiento local del navegador hasta su expiración o cierre de sesión, por lo que una recarga o una vista previa en otra pestaña mantiene el acceso.

Referencia visual vigente: [DESIGN.md](../DESIGN.md).

## Docker y prueba del flujo

Desde la raíz, configura `.env` con `POSTGRES_PASSWORD`, `ADMIN_EMAIL`,
`ADMIN_PASSWORD` y las credenciales del proveedor. Para OpenAI configura
`OPENAI_API_KEY` y `OPENAI_MODEL`; para Gemini, `GEMINI_API_KEY`.
Después ejecuta `docker compose up -d --build`.
Nginx publica el panel en `http://localhost:3000` (o `FRONTEND_PORT`), y la página de
prueba del widget en `/widget-example.html`. Compose arranca PostgreSQL, FastAPI,
Next.js y Nginx; este envía la API directamente a `backend:8000` dentro de la red Docker.
El backend crea el primer administrador y registra los modelos configurados al arrancar.
`OLLAMA_MODEL` registra el modelo descargado en el servicio Docker `ollama`.
Sigue [la guía de Ollama](../docs/local-ollama.md) antes del primer arranque.

Tras iniciar sesión, crea un chatbot, copia el script que aparece en su fila y
pégalo en tu dashboard. El botón **Probar** abre `/preview?chatbot_id=UUID`
con el chatbot seleccionado; `/widget-example.html` conserva el ejemplo local.
El asistente de creación sigue cinco pasos: información general, apariencia,
comportamiento e IA, conocimiento y publicación. Guarda el chatbot y su
personalización al pasar de comportamiento a conocimiento. La vista previa
muestra el color, icono y saludo guardados; el script de publicación conserva
estos ajustes en atributos `data-*` para el widget embebido. Si cambias la
apariencia después de integrar el chatbot, reemplaza el script en cada dashboard
para que el widget muestre la nueva configuración.
En **Apariencia** hay ocho colores sugeridos además del selector personalizado,
y seis iconos: Robot, Conversación, Análisis, Conocimiento, Asistente IA y Soporte.
La selección actualiza la vista visual y se conserva al guardar el chatbot (RF-28).
La carga de documentos genera
embeddings del proveedor configurado durante la petición; el estado `Listo` confirma que se
pueden recuperar como contexto. Una consulta sin documentos también responde.
Para embeddings locales usa `EMBEDDING_PROVIDER=ollama` con `embeddinggemma:300m`.
Si un documento quedó en `Error de procesamiento` antes de configurar el proveedor,
reinicia el backend y usa **Reintentar procesamiento** en la lista de documentos;
el archivo fallido no participa en RAG hasta quedar `Listo`.

Para un dashboard en otro origen, añade su origen exacto a
`WIDGET_ALLOWED_ORIGINS` (separado por comas) y reconstruye el backend. En
despliegue público sirve frontend, script y API mediante HTTPS.

## Referencia de Stitch

Las referencias pertenecen al proyecto **BiDaChat Design System**,
`projects/14860221730757100744`. Se cotejaron los originales de
«Documentos & RAG (Modo Claro)» y «Widget Conversacional Modo Claro»:
Inter, superficies claras, navegación lateral y acciones turquesa. La aplicación
adapta esa dirección a sus funciones y estados reales; no incorpora datos,
planes comerciales ni botones ficticios de las maquetas. Los valores y reglas
actuales de los dos temas están en [DESIGN.md](../DESIGN.md); el archivo
`desing.md` conserva un enlace al historial. Inter se sirve desde `public/fonts/`
con su licencia; los iconos SVG no necesitan servicios externos.

La barra lateral permanece visible al desplazarse y puede contraerse a iconos
en escritorio; el botón conserva la preferencia en el navegador. En móvil se
abre como un panel lateral. En el paso Conocimiento, **Seleccionar archivo**
muestra el nombre de la fuente elegida antes de cargarla.
Las tarjetas y formularios se apilan en pantallas pequeñas.
Las cifras provienen de la API: consultas, documentos y tiempos medidos.
Los controles corresponden a autenticación (RF-01–03), gestión y configuración
(RF-04–11), documentos (RF-13–17) y métricas (RF-24–27).

## Interfaz y aceptación

La dirección visual vigente se documenta en `../DESIGN.md`. Los estilos globales
contienen los tokens compartidos; shell, acceso, administración, editor y prueba
tienen sus propias hojas. `lib/navigation.ts` valida y construye rutas compatibles
con los enlaces existentes; el estado de URL identifica sección, chatbot, paso y filtros.

Pruebas de navegador (con frontend compilado y activo; utilizan respuestas API
sintéticas y no modifican la base de datos):

```bash
npm ci
npx playwright install chromium
QA_BASE_URL=http://127.0.0.1:3000 npm run test:e2e
```

El informe, capturas y resultados se guardan en `../docs/qa/frontend/`. No ejecutar
dos suites simultáneamente sobre el mismo directorio de resultados. En WSL, usar
una carpeta Linux para el ejecutor si la unidad Windows produce errores de directorio;
las mismas pruebas también funcionan con la compilación de Docker.

La prueba `e2e/live-acceptance.mjs` requiere credenciales **de un usuario de prueba**
en un archivo temporal indicado por `BIDACHAT_QA_CREDENTIALS`, modelos locales
activos y los puertos 4173 (permitido) y 4174 (denegado) disponibles. Crea fuentes y
consultas de prueba; las credenciales nunca deben guardarse en el repositorio.
El procedimiento y límites se registran en `../docs/qa/frontend/acceptance.md`.

### Gráficos del módulo Métricas

La sección muestra consultas por periodo, tiempo medio de respuesta y distribución
de estados usando la API autenticada. Los filtros incluyen chatbot, historial o
7/30/90 días, fechas personalizadas, estado y agrupación diaria/semanal/mensual.
Las fechas son UTC y el rango personalizado incluye el día inicial y el final.
Los filtros aplicados se conservan en la URL y al refrescar; las fechas personalizadas
se confirman con «Aplicar filtros». «Actualizar» consulta los datos nuevamente.
La tabla desplegable ofrece los valores de los gráficos y puede desplazarse en móvil.
No se presentan tiempos de respuesta inventados en periodos sin medición.

La marca del panel cambia con el tema usando las dos imágenes BC de `docs/brand`.
El lema «Datos que conversan» usa Caveat alojada en la aplicación; su licencia OFL
se incluye junto al archivo de fuente. Inter permanece en el resto de la interfaz.
