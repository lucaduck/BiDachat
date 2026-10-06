## 1. Configuración y contrato de proveedores

- [x] 1.1 Añadir validación de `OLLAMA_BASE_URL` como configuración privada del backend; verificar que no aparezca en respuestas API, respuestas públicas ni widget.
- [x] 1.2 Definir el contrato interno de inferencia y la selección por `executed_llm_model_id`; verificar con pruebas unitarias que una consulta no relee la configuración actual del chatbot.

## 2. Inferencia local y conversación

- [x] 2.1 Implementar el adaptador Ollama que comprueba disponibilidad del modelo y ejecuta consultas textuales; verificar respuesta correcta y errores seguros con un servidor de prueba.
- [x] 2.2 Integrar el adaptador en el flujo conversacional de FastAPI, RAG, registro de consulta y métricas; verificar que una consulta configurada con Ollama queda asociada al modelo ejecutado y no accede a documentos de otro chatbot.
- [x] 2.3 Validar capacidades de modelo antes de aceptar imagen o texto y rechazar combinaciones incompatibles; verificar los casos de error sin ejecutar inferencia.

## 3. Verificación y operación local

- [x] 3.1 Ejecutar pruebas de integración contra PostgreSQL/pgvector y pruebas del adaptador; verificar éxito, modelo no disponible, indisponibilidad de Ollama, trazabilidad y aislamiento.
- [x] 3.2 Documentar Ollama dockerizado con GPU, descarga de modelos y conexión interna desde el backend; verificar los comandos sin versionar modelos ni secretos.

## 4. Embeddings locales y puesta en marcha aprobados

- [x] 4.1 Instalar Ollama y descargar Qwen3-VL 2B y EmbeddingGemma 300M.
- [x] 4.2 Integrar embeddings locales y reflejar el proveedor en Configuración; probar validación de vectores y ausencia de dependencia Gemini.
- [x] 4.3 Configurar el entorno, reprocesar documentos y verificar RAG, imagen y uso GPU reales.
