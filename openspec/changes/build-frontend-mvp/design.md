## Context

El backend ya expone autenticación Bearer, CRUD de chatbots, carga documental y métricas bajo `/api/v1`; `frontend/` y `widget/` solo contienen estructura inicial. La dirección visual aprobada en `desing.md` es una interfaz **Operate**: oscura, sobria e institucional, con turquesa BI-DATA, Inter, navegación lateral y componentes reutilizables. Véase `proposal.md` para la motivación.

## Goals / Non-Goals

**Goals:**

- Entregar una experiencia administrativa completa y orientada a tareas para investigadores.
- Mantener un widget compacto, legible y visualmente subordinado al dashboard anfitrión.
- Hacer visibles los estados de carga, vacío, éxito y error en cada operación asíncrona.
- Centralizar la comunicación API y el tratamiento seguro de sesión en el cliente.

**Non-Goals:**

- Crear un panel de BI, una biblioteca documental compartida o un historial multiusuario.
- Guardar tokens, secretos, URLs de Ollama o claves de proveedor en código, almacenamiento persistente del navegador o widget.
- Reemplazar las reglas visuales existentes por una identidad distinta o añadir un framework UI adicional.
- Simular la conversación final antes de que exista el endpoint público de consultas.

## Decisions

- **Arquitectura de superficies:** Next.js administra las rutas de login, resumen, chatbots, documentos y métricas; el widget se compila como JavaScript independiente. Ambas superficies consumen solo API REST. Se descarta el acceso directo a base de datos o LLM por RNF-01 y `SECURITY.md`.
- **Sesión efímera:** el token Bearer se mantiene únicamente en memoria del cliente y se elimina al cerrar sesión o ante 401. Se descarta `localStorage` para reducir persistencia de credenciales; una recarga requiere autenticar de nuevo hasta que el backend ofrezca una cookie HttpOnly aprobada.
- **Servicios y tipos:** `frontend/services/` concentra `fetch`, encabezados Bearer, errores seguros y rutas; `frontend/types/` representa contratos API. Componentes y páginas no construyen URLs ni manejan detalles de red.
- **Sistema visual:** se traducen los tokens de `desing.md` a Tailwind: fondo `#08111F`, superficies `#102033`, turquesa `#14A8CE`, estados semánticos con texto e icono, espaciado de 4/8/12/16/24/32 y una sola tipografía Inter. Se descartan gradientes decorativos, tarjetas anidadas y gráficos sin significado.
- **Topología administrativa:** escritorio usa barra lateral persistente, cabecera de contexto y contenido principal; tableta compacta navegación; móvil usa menú colapsable y una columna. El resumen inicial prioriza chatbots activos, documentos pendientes y métricas recientes, con enlaces a la tarea correspondiente.
- **Widget:** se inicializa con `chatbot_id`, usa Shadow DOM para evitar que el CSS del dashboard afecte su interfaz y conserva un disparador accesible. Mientras el endpoint público no exista, se muestra un estado de integración pendiente en desarrollo, no una llamada ficticia.

## Risks / Trade-offs

- [La sesión se pierde al recargar] → reautenticación explícita y no persistencia insegura del token.
- [La API conversacional aún no existe] → implementar la carcasa del widget y conectar la consulta solo tras el cambio de proveedor/flujo público.
- [El CSS del dashboard interfiere] → Shadow DOM, estilos encapsulados y un tamaño adaptable.
- [Datos vacíos o lentos] → estados diseñados de carga, vacío y error, con acciones de reintento.
- [Pantallas pequeñas] → revisar escritorio y móvil en una pasada conjunta antes de completar cada superficie.

## Migration Plan

1. Inicializar Next.js y Tailwind dentro de `frontend/` sin introducir otro framework visual.
2. Implementar tokens, shell, componentes base y servicios API con pruebas.
3. Construir rutas administrativas por flujo: sesión, resumen, chatbots, documentos y métricas.
4. Construir el bundle del widget y conectarlo al endpoint público cuando el backend esté disponible.
5. Ejecutar pruebas, lint, revisión responsive y detector Impeccable antes de integrar.
