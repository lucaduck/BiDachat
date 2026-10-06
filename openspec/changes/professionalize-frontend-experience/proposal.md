## Why

BIDACHAT necesita una experiencia visual y funcional coherente en la versión completa: el usuario solicita calidad profesional, orientación constante y ausencia de enlaces rotos. La lectura del código confirma navegación repartida entre URL y estado local, estilos superpuestos y una vista previa de apariencia distinta del widget real, lo que dificulta mantener esa coherencia.

Fecha de planificación: 2026-10-05, America/Guayaquil. Alcance de esta entrega: planificación; no implementación ni certificación de la interfaz actual.

## What Changes

- Establecer una navegación verificable entre acceso, resumen, chatbots, editor, documentos, métricas, configuración y vista previa, conservando los enlaces existentes.
- Unificar tokens, componentes, jerarquía, estados y comportamientos para modo claro, oscuro, escritorio y móvil; elevar la identidad BI-DATA existente como dirección provisional.
- Mejorar los flujos de creación, personalización, fuentes de conocimiento, integración y conversación con imágenes que ya define el SRS.
- Hacer explícitas las diferencias entre una vista previa visual, una conversación real y una configuración de servidor de solo lectura.
- Definir pruebas de recorridos, historial, sesión, recursos y widget en un sitio externo independiente; un HTTP 200 por sí solo no acredita que un enlace funcione.
- Priorizar los gráficos de consultas por chatbot y resultados, basados en métricas existentes. Las series diarias requieren otro alcance de API y quedan como evolución propuesta.
- Reorganizar el frontend gradualmente por responsabilidades, conservando Next.js, TypeScript, Tailwind, el cliente API y el widget JavaScript independiente.

## Capabilities

### New Capabilities

- `frontend-experience-quality`: contrato verificable de navegación, diseño accesible, estados, continuidad del editor, fidelidad del widget y pruebas de enlaces. Se formaliza como capacidad nueva de OpenSpec porque `openspec/specs/` no contiene una especificación consolidada; no implica crear otro producto.

### Modified Capabilities

Ninguna especificación consolidada. Antes de aplicar, conciliar esta propuesta con los deltas pendientes de `build-frontend-mvp`, sin duplicar ni archivar trabajo por suposición.

## Impact

- Frontend: `app/page.tsx`, `app/preview/page.tsx`, `app/not-found.tsx`, `app/globals.css`, componentes administrativos, autenticación y componentes UI; servicios de sesión, navegación e integración y sus pruebas.
- Widget: coherencia visual, accesibilidad e interacción de `widget/src/bidachat-widget.js`; conservar su independencia del dashboard anfitrión.
- Documentación: al implementar, alinear `desing.md`, el contexto obsoleto de `openspec/config.yaml` y la lista de revisión web con el SRS vigente. El SRS 0.2 y las instrucciones actuales del usuario prevalecen sobre referencias antiguas al MVP.
- Trazabilidad: RF-01 a RF-14, RF-18 a RF-29; RNF-01, RNF-02, RNF-04, RNF-08, RNF-09, RNF-12 y RNF-13; RS-01 a RS-07 según el flujo. Especialmente CA-UC03-06, CA-UC05-01/03 y CA-UC07-06.
- Dependencias: proponer Playwright y comprobación de accesibilidad únicamente como herramientas de desarrollo para cubrir recorridos reales; comprobar disponibilidad antes de añadirlas. No se proponen cambios de infraestructura, base de datos ni arquitectura SOA.
- La gestión editable de orígenes, credenciales, MFA y recuperación de contraseña requiere trazabilidad y contratos propios antes de incorporarse. No simularla mediante botones sin operación real.
- Referencias de diseño: [UI UX Pro Max](https://uupm.cc/), los diseños de Stitch indicados por el usuario y `impeccable`. La referencia externa orienta decisiones; no constituye una certificación ni una valoración económica del producto.
