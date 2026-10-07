# Política de seguridad

## Alcance

BIDACHAT protege el panel administrativo, la API, PostgreSQL con pgvector, los documentos privados, el RAG y la integración con proveedores de IA.

## Reglas fundamentales

- Las funciones administrativas requieren una sesión válida.
- Los secretos, contraseñas y cadenas de conexión solo se almacenan en variables de entorno.
- El frontend y el widget solo se comunican con la API; no acceden directamente a la base de datos, RAG o proveedor de IA.
- Cada chatbot solo puede acceder a sus propios documentos, fragmentos y métricas.
- Los documentos se validan antes de almacenarse y permanecen en almacenamiento privado.
- Los errores públicos no deben revelar credenciales, rutas internas ni trazas técnicas.
- En despliegue, la comunicación debe usar HTTPS.

## Reportar una vulnerabilidad

No publiques vulnerabilidades ni secretos en issues públicos. Reporta el problema de forma privada al responsable del proyecto, incluyendo una descripción breve, pasos para reproducirlo y su posible impacto.

## Corrección

Toda vulnerabilidad confirmada debe analizarse, corregirse, probarse y documentarse sin exponer detalles sensibles.
