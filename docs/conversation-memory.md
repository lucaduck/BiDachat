# Memoria conversacional y contexto de página

El widget mantiene continuidad textual durante una sesión anónima. Genera un UUID opaco por combinación de origen y chatbot, lo guarda en `sessionStorage` y lo envía en `conversation_id` con cada `POST /api/v1/chatbots/{chatbot_id}/queries`.

El backend valida el UUID contra el chatbot, el origen normalizado y el vencimiento. Si no corresponde, crea una conversación nueva y devuelve su identificador sin revelar el motivo interno ni recuperar mensajes ajenos. La API continúa aceptando clientes que no envían `conversation_id`.

## Límites y privacidad

| Variable                 | Valor inicial | Función                                               |
| ------------------------ | ------------: | ----------------------------------------------------- |
| `CONVERSATION_TTL_HOURS` |            24 | Vigencia deslizante de la conversación.               |
| `CONVERSATION_MAX_TURNS` |            12 | Máximo de pares usuario/asistente enviados al modelo. |
| `CONVERSATION_MAX_CHARS` |         12000 | Máximo total de caracteres del historial enviado.     |
| `CONVERSATION_CLEANUP_INTERVAL_MINUTES` | 60 | Intervalo entre limpiezas automáticas en el backend. |

Solo se guardan la pregunta y la respuesta de consultas completadas. Las imágenes y capturas se procesan en la consulta actual y no se copian a `conversation_messages`. El historial se presenta al proveedor como datos no confiables, separado de instrucciones, RAG, contexto de página e imagen.

El widget reinicia la conversación tras 30 minutos de inactividad, o al pulsar **Nueva conversación**. El integrador puede cambiar ese plazo con `data-idle-minutes="60"` (entre 1 y 1440 minutos). El límite de 24 horas del servidor y el de inactividad del navegador son independientes. Reiniciar crea otra conversación; no elimina inmediatamente la anterior.

El backend limpia las conversaciones vencidas al arrancar y después en el intervalo configurado. Si está detenido, la limpieza se reanuda al arrancar. Para ejecutarla manualmente:

```bash
docker compose exec -T backend python -m app.cleanup_conversations
```

El borrado de una conversación elimina sus mensajes y establece `queries.conversation_id` en `NULL`. Conserva la consulta, métricas, modelo ejecutado, fuentes y chatbot. Los registros de `queries` pueden seguir conteniendo preguntas y respuestas: la limpieza de memoria no es una política de borrado de consultas ni elimina las copias de seguridad. La política institucional de retención continúa pendiente.

## Identidad opcional del sitio anfitrión

Por defecto, la identidad es anónima y el UUID se guarda en la sesión de la pestaña, por chatbot y origen. Una pestaña duplicada o abierta desde otra puede heredar una copia de `sessionStorage`; compartir un UUID también puede permitir reutilizar esa conversación anónima. Para un sitio que ya autentica usuarios, el servidor del sitio puede emitir una identidad seudónima firmada. La conversación sigue dependiendo del UUID de esa pestaña: la identidad no recupera automáticamente conversaciones en otro navegador o dispositivo.

1. Configure una clave aleatoria `WIDGET_IDENTITY_MASTER_KEY` en el `.env` del backend y reinicie el contenedor. Genérela, por ejemplo, ejecutando `python -c "import secrets; print(secrets.token_urlsafe(48))"` en un terminal privado. No envíe su valor por chat ni la suba al repositorio.
2. Autorice el origen exacto del sitio mediante `WIDGET_ALLOWED_ORIGINS`. Genere una clave específica para un chatbot y origen, y guárdela con permisos restrictivos en el servidor del sitio. El comando imprime una credencial: redirija su salida a un archivo protegido y transfiera el archivo por un canal seguro. Sustituya el UUID y el origen por los reales.

   ```bash
   umask 077
   docker compose exec -T backend python -m app.widget_identity_key \
     00000000-0000-4000-8000-000000000000 https://dashboard.example.com \
     > /ruta/privada/bidachat-widget-signing-key
   ```

   Use el archivo Compose correspondiente al entorno si no usa el Compose de desarrollo. El servidor anfitrión recibe únicamente esta clave derivada, no la clave maestra de BIDACHAT.
3. El servidor anfitrión debe autenticar la sesión del visitante y emitir un token breve para **ese usuario** mediante un endpoint de su mismo origen. El ejemplo [sign_widget_identity.py](examples/sign_widget_identity.py) muestra la firma: pase el identificador interno autenticado y una segunda clave aleatoria privada del sitio para generar el seudónimo. No utilice el correo ni acepte una identidad enviada por el navegador como prueba de autenticación. Devuelva `{"token": "..."}` con `Cache-Control: no-store`; si no hay sesión válida, responda 401. Los tokens duran cinco minutos y se obtienen nuevamente al abrir y al enviar.
4. Añada al script del widget `data-identity-endpoint="/api/bidachat-identity"`. El navegador consulta esa ruta en el sitio anfitrión; el widget envía el token a BIDACHAT, que comprueba firma, plazo, origen y chatbot. Si falla, la consulta se rechaza. La identidad anónima ordinaria sigue disponible para integraciones que no configuran este atributo.
5. Cuando el sitio cambie de usuario o cierre sesión sin recargar la página, después de cambiar su estado de autenticación debe ejecutar `window.dispatchEvent(new Event("bidachat:identity-changed"))`. El widget limpia la conversación visible, cierra el panel e invalida la respuesta en curso. Si se cambia la sesión sin notificar, el widget solo detecta la nueva identidad al volver a abrirse o al enviar otra pregunta.

La clave derivada debe mantenerse en el servidor anfitrión. Un token robado puede reproducirse hasta que expire. Cambiar la clave maestra invalida claves derivadas y el acceso a conversaciones firmadas anteriores; estas se eliminan al vencer. El origen permitido por CORS no sustituye a la autenticación del sitio ni a la protección de sus credenciales.

## Contexto de página

El integrador decide qué región visible puede enviar mediante `data-context-selector`. El widget lee nuevamente esa región en cada pregunta, elimina controles y nodos marcados con `data-bidachat-ignore`, normaliza el texto y limita el resultado a 6000 caracteres. No rastrea enlaces ni otras páginas.

La ruta `/preview` usa exclusivamente `#preview-dashboard`. Por ello envía los KPI y el gráfico de demostración, pero excluye encabezado, navegación, introducción y mensajes del chatbot.

## Evidencia local del 16 de octubre de 2026

- Migración `005` aplicada, revertida y reaplicada en una base PostgreSQL temporal con pgvector; la base temporal fue eliminada.
- Pruebas Playwright confirmaron contexto actualizado, persistencia tras recarga y separación entre dos chatbots.
- Una conversación real con Vertex `gemini-3.1-flash-lite` recordó el nombre **Patricio** en el segundo turno y respondió **89,4 %** usando el contexto del tablero en el tercero.
- Los tiempos backend de esa aceptación integral fueron 36636 ms, 6377 ms y 4579 ms. Es una prueba funcional de tres observaciones y no una estimación de rendimiento.
- El chatbot temporal de aceptación fue eliminado al finalizar.

### Medición exploratoria de memoria

Se ejecutaron 30 pares alternados con Vertex `gemini-3.1-flash-lite`, después de un calentamiento excluido. Cada par usó la misma pregunta: una generación sin historial y otra con un turno previo fijo de 42 caracteres. La instrumentación midió el texto exacto enviado por `LlmProvider` a LiteLLM, sin registrar secretos ni respuestas.

| Condición   | Muestras correctas |  Contexto total |   Mediana |        p95 |             Rango |
| ----------- | -----------------: | --------------: | --------: | ---------: | ----------------: |
| Sin memoria |                 30 | 1291 caracteres | 830,66 ms | 1375,24 ms | 664,75–1983,45 ms |
| Con memoria |                 30 | 1377 caracteres | 781,75 ms | 1291,95 ms | 600,59–1613,32 ms |

No hubo fallos. La alternancia reduce el sesgo temporal, pero esta medición abarca solo la generación entre FastAPI, LiteLLM y Vertex en el entorno local; excluye HTTP del widget, base de datos, embeddings y recuperación RAG. La diferencia observada no demuestra que la memoria mejore la velocidad y no constituye un SLA. Las observaciones sanitizadas están en [`docs/qa/conversation-memory-latency-2026-10-16.json`](qa/conversation-memory-latency-2026-10-16.json).

La política institucional de retención sigue pendiente. Los valores actuales son límites técnicos configurables.
