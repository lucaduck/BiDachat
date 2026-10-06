# Widget

Cliente JavaScript embebible e independiente del framework del dashboard. Compílalo con `npm run build` dentro de `widget/`; el archivo resultante queda en `dist/bidachat-widget.js`.

```html
<script src="https://TU-DOMINIO/bidachat-widget.js" data-chatbot-id="UUID-DEL-CHATBOT"></script>
```

El identificador es público y no es una credencial. El widget usa Shadow DOM
para aislar sus estilos, admite preguntas y una captura opcional PNG/JPEG/WebP
de hasta 4 MiB y consulta `/api/v1/chatbots/{chatbot_id}/queries`. El botón
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

La apariencia usa `data-primary-color` (color hexadecimal) y `data-icon`.
Los iconos admitidos son `bot`, `chat`, `chart`, `book`, `sparkles` y `headset`.
El editor genera estos atributos a partir de la selección guardada.
