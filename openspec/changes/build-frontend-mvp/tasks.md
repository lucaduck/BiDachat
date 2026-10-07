## 1. Base del frontend y sistema visual

- [x] 1.1 Inicializar la aplicación Next.js con TypeScript, Tailwind CSS, ESLint y Prettier en `frontend/`; verificar compilación y lint sin errores.
- [ ] 1.2 Traducir los tokens de `desing.md` a Tailwind y crear componentes reutilizables de botón, campo, selector, alerta, estado vacío y carga; verificar contraste, foco visible y estados no dependientes solo del color.
- [ ] 1.3 Implementar el shell administrativo responsive con navegación lateral, cabecera y menú móvil; verificar capturas en escritorio 1440 px y móvil 390 px.

## 2. Sesión y servicios API

- [x] 2.1 Crear tipos y servicios HTTP para `/api/v1`, con token Bearer mantenido solo en memoria, errores seguros y descarte de sesión ante 401; verificar pruebas unitarias de encabezados, logout y expiración.
- [x] 2.2 Implementar login, logout y protección de rutas administrativas; verificar que un visitante no autenticado no recibe ni visualiza datos administrativos.

## 3. Operación administrativa

- [ ] 3.1 Crear el resumen inicial con chatbots, documentos y métricas disponibles, además de estados vacíos y enlaces a acciones; verificar navegación y datos sintéticos etiquetados en pruebas visuales.
- [ ] 3.2 Implementar listado, creación, edición y eliminación de chatbots con modelos admitidos e instrucciones; verificar los flujos contra la API y mensajes seguros de validación.
- [ ] 3.3 Implementar carga y listado de documentos aislados por chatbot, con validación visible, progreso y estados de procesamiento; verificar PDF, DOCX, TXT, CSV, error y tamaño máximo.
- [ ] 3.4 Implementar métricas por chatbot con selector de periodo, estados de carga/error y período vacío; verificar conteos, media no disponible y acceso protegido.

## 4. Widget embebible

- [ ] 4.1 Configurar el bundle JavaScript del widget con Shadow DOM, inicialización por `chatbot_id` y disparador accesible; verificar que su estilo no cambia el dashboard anfitrión.
- [ ] 4.2 Implementar las vistas de conversación vacía, mensajes, procesamiento, error y reintento; conectar solicitudes reales cuando el endpoint público del cambio `add-local-ollama-provider` esté disponible.
- [ ] 4.3 Documentar el snippet de integración sin secretos y probarlo dentro de una página de dashboard de ejemplo; verificar que el widget no accede directamente a base de datos ni proveedores LLM.

## 5. Verificación y entrega

- [ ] 5.1 Ejecutar pruebas de componentes, flujos autenticados y accesibilidad de teclado; verificar lint, formato y pruebas afectadas.
- [ ] 5.2 Ejecutar una revisión Impeccable de las superficies administrativas y del widget, corrigiendo hallazgos mecánicos; verificar escritorio, móvil y estados asíncronos en capturas.
- [ ] 5.3 Actualizar README de frontend/widget y la guía de ejecución Docker; verificar que no se versionen tokens, secretos ni URL privada de Ollama.
