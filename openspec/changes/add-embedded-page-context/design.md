## Approach

La página anfitriona decide qué sección exponer con un selector CSS. El código generado usa `main` como valor inicial editable. El widget evalúa ese selector en cada envío, extrae únicamente nodos de texto renderizados y omite formularios, controles, contenido editable, elementos ocultos y subárboles marcados con `data-bidachat-ignore`.

El límite de 6000 caracteres se aplica tanto en el widget como en el esquema de la API. Si el selector es inválido o no encuentra un elemento, la pregunta se envía sin `page_context`. El backend mantiene separado el contexto RAG del contexto de página en el prompt e indica que este último no contiene instrucciones confiables.

La extracción no hace solicitudes de red ni guarda una copia del dashboard. Cada consulta conserva las métricas actuales y el proveedor configurado del chatbot recibe el contexto solo durante la generación. El operador del sitio controla la inclusión de datos sensibles mediante la región elegida y los marcadores de exclusión.

## Verification

Probar esquema y paso de datos en backend; comprobar en navegador una página anfitriona distinta, texto actualizado, exclusiones y consulta sin selector; ejecutar lint y compilación afectados.
