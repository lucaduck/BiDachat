## 1. Planificación y requisitos de entrada

- [x] 1.1 Documentar propuesta, diseño y escenarios; evidencia: archivos de este cambio basados en inspección del backend, catálogo y despliegue.
- [ ] 1.2 Incorporar al SRS el alcance aprobado de Vertex mediante gateway; verificar correspondencia con RF-08, RF-12/13, RF-18 a RF-27, RNF-15 y escenarios de la especificación.
- [ ] 1.3 Registrar proyecto Google, ubicación, modelo multimodal accesible y presupuesto de pruebas; verificar facturación, API habilitada y permisos sin registrar secretos.
- [ ] 1.4 Preparar identidad de desarrollo/VPS según diseño; verificar acceso al archivo solo por el servicio autorizado y ausencia en Git/imágenes.

## 2. Gateway privado y recursos

- [ ] 2.1 Seleccionar versión/digest oficial de LiteLLM y crear configuración estática para un modelo explícito; verificar arranque sin base adicional, fallback, reintentos automáticos ni callbacks externos.
- [ ] 2.2 Añadir servicio opcional a Compose de desarrollo y producción con autenticación, montajes de lectura y límites obligatorios al habilitarlo; verificar configuraciones apagada y encendida, y ausencia de puerto publicado.
- [ ] 2.3 Implementar comprobación de salud no facturable; verificar arranque, reinicio y rechazo de llamadas sin clave interna.
- [ ] 2.4 Medir memoria/CPU del gateway y presupuestar recursos compartidos del VPS; entregar tabla de límites y margen observado antes de habilitar producción.

## 3. Integración del backend

- [ ] 3.1 Añadir configuración validada y estado sanitizado; verificar que Vertex apagado no requiere credenciales y que Vertex habilitado con datos incompletos falla claramente.
- [ ] 3.2 Implementar adaptador `vertex_gateway.py` con HTTPX y delegación pequeña en `provider.py`; verificar texto, imagen, modelo, autenticación y timeout mediante pruebas de contrato.
- [ ] 3.3 Manejar 401/403/429/503, timeout, modelo inesperado, respuesta vacía y bloqueo; verificar error seguro, sin éxito falso ni llamada a un modelo alternativo.
- [ ] 3.4 Integrar catálogo explícito y validación de disponibilidad; verificar alta idempotente, selección válida, retiro de modelo sin borrar historial y rechazo de selección deshabilitada.
- [ ] 3.5 Admitir Vertex en el perfil visual documental conservando el valor actual; verificar descripción antes de embeddings y fallo sin publicar chunks incompletos.
- [ ] 3.6 Verificar conversación y métricas con PostgreSQL/pgvector: consulta exitosa/fallida, cambio de modelo, aislamiento entre dos bots y conservación del modelo histórico.

## 4. Interfaz y contrato público

- [ ] 4.1 Añadir etiquetas/tipos de Vertex en los selectores existentes; verificar carga del modelo guardado, filtrado por proveedor y guardado de selección válida.
- [ ] 4.2 Mostrar configuración/disponibilidad sin exponer credenciales ni afirmar conectividad no probada; verificar estados habilitado, deshabilitado y modelo retirado en claro/oscuro.
- [ ] 4.3 Probar widget desde una página de otro origen autorizado; verificar texto, adjunto y contexto web con el contrato REST vigente y rechazo del origen no autorizado.

## 5. Aceptación real y calidad

- [x] 5.1 Ejecutar una llamada real mínima autorizada y confirmar identidad del modelo; evidencia local en `docs/vertex-ai.md`, sección «Verificación local de credencial».
- [ ] 5.2 Ejecutar corpus con texto, PNG, JPEG y WebP de contenido conocido; registrar esperado/obtenido, modelo, tiempo, consumo y limitaciones sin usar mocks como aceptación real.
- [ ] 5.3 Probar recuperación textual/visual, contexto web y aislamiento entre chatbots; verificar respuestas sustentadas, retiro de fuentes y escenarios adversariales de contexto, registrando fallos honestamente.
- [ ] 5.4 Comparar tiempos con preguntas/contextos equivalentes, informando muestras y primera ejecución separada; entregar mediciones sin afirmar una mejora no demostrada.
- [ ] 5.5 Ejecutar regresiones afectadas de proveedores existentes, frontend, lint, tipos y formato; verificar que no se modifican contratos ni perfiles activos por defecto.
- [ ] 5.6 Revisar legibilidad: adaptador con responsabilidad única, rutas delgadas, nombres claros y reutilización justificada; resolver duplicación y abstracciones innecesarias antes de cerrar.

## 6. Documentación y despliegue

- [ ] 6.1 Actualizar ejemplos de entorno y guías de instalación/operación con credenciales, recursos, cuotas, errores y rollback; verificar comandos y enlaces sin secretos reales.
- [ ] 6.2 Actualizar preflight y empaquetado del despliegue para incluir configuración del gateway; verificar paquete completo, perfil coherente y exclusión de credenciales en Actions.
- [ ] 6.3 Desplegar mediante PR aprobado e integrado, activar un chatbot de prueba y ejecutar smoke desde página externa; verificar acceso, respuesta, métricas y consumo de recursos del VPS.
- [ ] 6.4 Ensayar reversión conservando historial y fuentes; verificar funcionamiento con proveedor anterior y gateway deshabilitado.
- [ ] 6.5 Consolidar evidencia por escenario y pendientes explícitos; cerrar solo con aceptación real satisfecha, pruebas afectadas aprobadas y documentación coherente.
