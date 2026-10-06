# Rutas de la API

La API de BIDACHAT usa el prefijo `/api/v1`. FastAPI genera la pantalla
interactiva `/api/v1/docs` a partir de los decoradores de cada ruta, los grupos
(`tags`) y los esquemas Pydantic. Por ese motivo aparecen descripciones de
campos, límites de tamaño, rutas y respuestas: son parte del contrato técnico
que consumen el panel administrativo y el widget.

Las rutas administrativas requieren `Authorization: Bearer <token>`. El token
se obtiene con el inicio de sesión. La única ruta pública es la consulta del
widget; tiene límite de solicitudes por cliente. La documentación interactiva
solo se habilita en desarrollo y pruebas; en producción se desactiva junto con
el documento OpenAPI.

| Método y ruta | Acceso | Uso |
| --- | --- | --- |
| `GET /api/v1/health` | Público | Comprueba que el backend responde. |
| `POST /api/v1/auth/login` | Público | Inicia la sesión administrativa y devuelve un token temporal. |
| `POST /api/v1/auth/logout` | Administrativo | Revoca el token actual. |
| `GET /api/v1/settings` | Administrativo | Consulta proveedores y límites configurados, sin revelar claves. |
| `GET /api/v1/llm-models` | Administrativo | Lista los modelos que pueden asignarse a un chatbot. |
| `GET /api/v1/chatbots` | Administrativo | Lista los chatbots. |
| `POST /api/v1/chatbots` | Administrativo | Crea un chatbot, con instrucciones y apariencia del widget. |
| `GET /api/v1/chatbots/{chatbot_id}` | Administrativo | Obtiene un chatbot. |
| `PUT /api/v1/chatbots/{chatbot_id}` | Administrativo | Actualiza su configuración. |
| `DELETE /api/v1/chatbots/{chatbot_id}` | Administrativo | Elimina el chatbot y sus datos asociados. |
| `GET /api/v1/documents` | Administrativo | Lista fuentes disponibles para volver a asociarlas. |
| `GET /api/v1/chatbots/{chatbot_id}/documents` | Administrativo | Lista las fuentes asociadas al chatbot. |
| `POST /api/v1/chatbots/{chatbot_id}/documents` | Administrativo | Sube y procesa un documento o imagen como conocimiento. |
| `POST /api/v1/chatbots/{chatbot_id}/documents/associations` | Administrativo | Asocia fuentes existentes al chatbot. |
| `DELETE /api/v1/chatbots/{chatbot_id}/documents/{document_id}` | Administrativo | Quita una fuente del contexto del chatbot. |
| `POST /api/v1/chatbots/{chatbot_id}/documents/{document_id}/processing` | Administrativo | Reintenta procesar una fuente fallida o pendiente. |
| `GET /api/v1/chatbots/{chatbot_id}/metrics` | Administrativo | Consulta consultas, tiempos y estados, con filtros y agrupación. |
| `POST /api/v1/chatbots/{chatbot_id}/queries` | Público, con límite | Recibe la pregunta y una imagen opcional del widget; recupera contexto y devuelve la respuesta. |

## De dónde salen las descripciones

Las rutas se registran en [backend/app/api/router.py](../backend/app/api/router.py).
Los grupos visibles en Swagger se declaran en `auth.py`, `chatbots.py`,
`queries.py` y `settings.py`. Las reglas visibles para los datos de entrada,
como tamaños máximos, tipos de imagen y campos obligatorios, provienen de
`backend/app/schemas/`.

La justificación funcional se encuentra en [SRS.md](../SRS.md): autenticación
RF-01 a RF-03; gestión y configuración RF-04 a RF-12; documentos y RAG RF-13
a RF-17; conversación RF-18 a RF-23; métricas RF-24 a RF-27; y personalización
RF-28 a RF-29. El comportamiento técnico y los parámetros de métricas se
explican también en [backend/README.md](../backend/README.md).
