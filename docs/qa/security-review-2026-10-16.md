# Revisión de sesión, autorización, límites y errores

Fecha: 16 de octubre de 2026. Alcance: RS-01–RS-04, RS-08–RS-09 y
`stabilize-complete-application` 6.1. Esta revisión describe controles observados
en el código y pruebas locales; no equivale a una auditoría de penetración ni a
aceptación del VPS.

## Resultado

| Frontera            | Evidencia comprobada                                                                                                                                                                                        | Resultado y límite                                                                                                                                                                                                    |
| ------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Credenciales        | Contraseñas con `scrypt`, sal aleatoria y comparación constante. Usuario inexistente consume una derivación para reducir diferencias temporales.                                                            | Aprobado en pruebas de servicio. La política institucional de contraseñas depende del responsable del despliegue.                                                                                                     |
| Sesión              | Token opaco aleatorio de 32 bytes; en PostgreSQL solo se almacena SHA-256. La API valida usuario activo, vencimiento y revocación. Logout revoca el token.                                                  | Aprobado. El navegador conserva el token en `localStorage`; un XSS podría leerlo. Migrar a cookie exige una decisión separada sobre CSRF, proxy y compatibilidad.                                                     |
| Tiempo de sesión    | `SESSION_TTL_MINUTES` fija el vencimiento emitido por el backend y el frontend lo comprueba antes de reutilizar la sesión.                                                                                  | Aprobado localmente. No existe renovación silenciosa ni rotación automática.                                                                                                                                          |
| Administración      | Todos los endpoints de chatbots, documentos, modelos, métricas y configuración dependen de `get_current_session`. Salud, login y consultas del widget son públicos por diseño.                              | Aprobado por inspección y pruebas 401. No existen roles adicionales porque el SRS solo requiere investigador autorizado.                                                                                              |
| Intentos de login   | Contadores persistentes y bloqueados en PostgreSQL: cinco fallos por cuenta en 15 minutos y 60 globales por minuto. Las cuentas se identifican mediante hash del correo normalizado.                        | Aprobado con concurrencia y expiración. La respuesta 429 incluye `Retry-After`.                                                                                                                                       |
| Consultas públicas  | Límite de diez solicitudes por minuto y cliente en el único proceso backend previsto. La respuesta 429 ahora incluye `Retry-After: 60`.                                                                     | Control activo, con límite conocido: es memoria de proceso, se reinicia al recrear el backend y no coordina réplicas. Cambiar a un límite persistente requiere diseño de identidad y capacidad antes de otra réplica. |
| Orígenes del widget | CORS admite únicamente `WIDGET_ALLOWED_ORIGINS` y solo `POST`/`OPTIONS` con `Content-Type`.                                                                                                                 | Reduce uso desde navegadores no autorizados. CORS no autentica clientes HTTP ni sustituye el límite de abuso. Su aceptación real depende del proxy y dominio de producción.                                           |
| Errores             | Fallos del proveedor se traducen a 503 genérico; errores inesperados se registran en servidor y devuelven un mensaje 500 sin excepción, clave ni respuesta del proveedor. Los 401 usan un mensaje uniforme. | Aprobado en pruebas de contrato. Los logs del VPS todavía deben revisarse durante la aceptación para confirmar permisos y retención.                                                                                  |

## Comprobaciones ejecutadas

- Login correcto, credenciales inválidas, logout y rechazo del token revocado.
- Vencimiento y revocación de sesiones en el servicio de autenticación.
- Límite de login persistente, atómico, normalizado y con ventanas expirables.
- Rechazo 401 de operaciones administrativas sin bearer válido.
- Límite del endpoint conversacional y cabecera `Retry-After`.
- Conversión de errores de proveedor y errores inesperados a mensajes seguros.

## Condiciones que siguen abiertas para publicación

1. Verificar HTTPS, cabeceras reenviadas e identidad efectiva del cliente detrás
   de Cloudflare, Apache y Nginx.
2. Confirmar que archivos de log, `.env`, respaldos y credenciales tienen permisos
   y retención adecuados en el VPS.
3. Medir el límite conversacional bajo carga real. Si se agregan réplicas del
   backend, reemplazar el contador de proceso por un mecanismo coordinado aprobado.
4. Mantener pruebas XSS y CSP dentro de la revisión de la interfaz; el riesgo de
   `localStorage` depende directamente de impedir ejecución de script no confiable.

No se propone JWT como corrección automática: el token opaco actual permite
revocación inmediata y evita incluir datos de usuario en el cliente. Tampoco se
añade Redis ni otro componente para un despliegue de una sola réplica.
