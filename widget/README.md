# Widget

Cliente JavaScript embebible e independiente del framework del dashboard. Compílalo con `npm run build` dentro de `widget/`; el archivo resultante queda en `dist/bidachat-widget.js`.

```html
<script src="https://TU-DOMINIO/bidachat-widget.js" data-chatbot-id="UUID-DEL-CHATBOT"></script>
```

El identificador es público y no es una credencial. El widget usa Shadow DOM
para aislar sus estilos, admite preguntas y una captura opcional PNG/JPEG/WebP
de hasta 4 MiB y consulta por HTTP `POST`
`/api/v1/chatbots/{chatbot_id}/queries`. El botón
**Adjuntar** selecciona una imagen local; **Capturar** solicita permiso del
navegador para capturar una pestaña, ventana o pantalla y prepara un fotograma
JPEG. El usuario puede revisar o quitar la imagen antes de enviarla. Una imagen
también puede pegarse en el campo de pregunta con `Ctrl+V`; se aplican las mismas
validaciones de formato y 4 MiB que al seleccionar un archivo. El pegado de texto
sin imagen conserva el comportamiento normal del campo. La captura requiere
un contexto seguro (HTTPS o localhost) y soporte de `getDisplayMedia`.
El frontend
Docker publica el script en `/bidachat-widget.js` y una prueba en
`/widget-example.html`. En una página externa, agrega su origen a
`WIDGET_ALLOWED_ORIGINS` y usa la URL pública HTTPS del frontend en `src`.
El script no contiene claves ni accede a la base de datos o al proveedor LLM.

La lista debe incluir también el origen del panel para usar la vista previa.
Una lista vacía bloquea todas las consultas públicas. El backend exige un único
encabezado `Origin` con coincidencia exacta; rechaza su ausencia, `null`, rutas,
subdominios no registrados y valores múltiples antes de consultar datos o IA.
Las entradas de configuración se normalizan (dominio, puerto predeterminado y
barra final), pero no se admiten comodines. En producción use los orígenes HTTPS
reales; no copie los valores localhost del ejemplo de desarrollo.

Después de cambiar el `.env`, recree el backend con
`docker compose up -d --force-recreate --no-deps backend` (o el Compose de producción).
CORS y la validación usan la misma configuración. Los clientes de API fuera del
navegador también deben enviar un origen permitido, pero pueden falsificarlo:
esta lista no reemplaza autenticación, identidad firmada ni límites de consumo.

El código generado incluye `data-context-selector="main"`. Al enviar cada
pregunta, el widget extrae hasta 6000 caracteres de texto visible del primer
elemento que coincida con ese selector y los envía como `page_context` a la
API REST. Para otra estructura, cambia el selector por ejemplo a
`data-context-selector="#dashboard"`; para desactivar el envío, elimina el
atributo. No rastrea URLs ni lee HTML, campos de formulario, contenido editable,
botones, elementos ocultos o subárboles con `data-bidachat-ignore`. Es contexto
de la consulta actual, independiente de las fuentes RAG almacenadas. El sitio
anfitrión debe mantener fuera de esa región cualquier dato que no deba enviarse
al chatbot o al proveedor de IA configurado.

Las respuestas del asistente se presentan con párrafos, listas, énfasis y bloques
de código cuando el modelo los devuelve. El widget construye estos elementos
como nodos de texto seguros; no interpreta HTML recibido del modelo. La API no
envía referencias documentales en la respuesta actual, por lo que el widget no
presenta una atribución de fuente sin datos verificables.

La apariencia usa `data-primary-color` (color hexadecimal) y `data-icon`.
Los iconos admitidos son `bot`, `chat`, `chart`, `book`, `sparkles` y `headset`.
El editor genera estos atributos a partir de la selección guardada.

## Memoria e identidad del sitio

El widget ofrece **Nueva conversación** y reinicia por inactividad; el valor inicial es 30 minutos y se ajusta con `data-idle-minutes` (1–1440). La integración opcional con sitios que autentican visitantes se configura con `data-identity-endpoint`. Consulte la [guía de memoria e identidad](../docs/conversation-memory.md) antes de activar esta opción.
