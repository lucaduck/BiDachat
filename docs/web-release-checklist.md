# Revisión web para BIDACHAT

Esta tabla adapta la lista de la captura compartida al panel administrativo, el widget embebible y la página de prueba. El panel requiere autenticación y no está pensado para posicionamiento en buscadores.

| Elemento | Decisión para BIDACHAT |
|---|---|
| Aviso legal | Preparar con los datos oficiales de la entidad responsable antes de publicar. |
| Política de privacidad | Necesaria por el tratamiento de cuentas, consultas, capturas y documentos. El texto final requiere responsable, contacto, finalidades, conservación y destinatarios verificados. |
| Aviso de cookies | Añadir solo si se incorporan cookies que lo requieran. La sesión actual conserva el token en memoria y localStorage y el frontend no instala cookies de analítica o publicidad. |
| HTTPS | Obligatorio en despliegue para el panel, API y widget (`RS-03`). Configurar TLS en el proxy o plataforma de alojamiento; el HTTP local es solo para desarrollo. |
| Meta títulos y descripciones | Incluir título y descripción legibles. El panel tiene `noindex` por estar protegido. |
| Datos estructurados | No se necesitan en el panel privado. Reevaluar si se crea una web pública del proyecto. |
| Sitemap y robots.txt | No se necesita sitemap del panel privado. `robots.txt` no protege información; la autenticación y `noindex` cumplen funciones distintas. |
| Ficha de Google | No corresponde a esta aplicación administrativa. |
| Favicon | Incluido como icono SVG de BIDACHAT. |
| Texto alternativo | Requerido para imágenes informativas; los iconos decorativos actuales se ocultan a lectores de pantalla. |
| Imágenes comprimidas | No hay fotografías de producto en el panel actual. Optimizar cualquier imagen que se agregue más adelante. |
| Velocidad de carga | Verificar compilación de producción y evitar recursos externos innecesarios. |
| Contraste de colores | Verificar en desktop y móvil en los temas claro y oscuro del proyecto. |
| Vista móvil | El panel y el asistente de creación se adaptan a pantallas pequeñas. |
| Página 404 | Incluida con enlace de retorno al panel. |
| Enlaces rotos | Revisar al publicar las rutas internas y el enlace de integración del widget. |
| Formularios contra spam | Login con límite de intentos; consultas públicas con límite de solicitudes. Mantener validación del lado de la API. |

Los textos jurídicos deben validarse con la entidad responsable antes de su publicación. No se deben mostrar datos institucionales supuestos como si fueran oficiales.

Referencias: [Ley Orgánica de Protección de Datos Personales de Ecuador](https://spdp.gob.ec/wp-content/uploads/2024/12/03.pdf.pdf) y [guía de indexación de Google](https://developers.google.com/search/docs/fundamentals/get-started-developers).
