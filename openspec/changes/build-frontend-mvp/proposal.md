## Why

El backend ya proporciona autenticación administrativa, gestión de chatbots, documentos y métricas, pero BIDACHAT no tiene una interfaz operable para investigadores ni un widget que acerque las consultas a los dashboards. El MVP requiere ambas superficies para completar el flujo definido en el SRS.

## What Changes

- Crear la aplicación administrativa en Next.js, TypeScript y Tailwind CSS.
- Incluir inicio/cierre de sesión, resumen operativo, gestión de chatbots, carga/listado de documentos y métricas.
- Crear el widget JavaScript independiente para integrarse en dashboards BI-DATA.
- Aplicar la identidad visual BI-DATA: base oscura, turquesa institucional, Inter, accesibilidad y diseño responsive.
- Centralizar las llamadas HTTP en servicios cliente y no exponer secretos, conexión de datos ni proveedores LLM.

## Capabilities

### New Capabilities

- `admin-frontend`: panel administrativo autenticado para operar chatbots, documentos y métricas del MVP.
- `dashboard-chat-widget`: widget conversacional independiente para dashboards, preparado para el endpoint público de consultas.

### Modified Capabilities

Ninguna: no existen especificaciones consolidadas bajo `openspec/specs/`.

## Impact

Afecta `frontend/` y `widget/`; consume únicamente `/api/v1` mediante HTTPS en despliegue. Depende de los endpoints administrativos existentes y del posterior flujo público de consultas del cambio `add-local-ollama-provider`. No agrega acceso directo a PostgreSQL, pgvector, Gemini, Ollama ni credenciales al cliente.
