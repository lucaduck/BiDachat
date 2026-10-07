# Política de comparación del frontend

Fecha: 2026-10-05. Presupuestos propuestos para este cambio, establecidos antes de la comparación final; son criterios internos de regresión y no umbrales nuevos del SRS.

- Resumen: no añadir consultas administrativas para dibujar gráficos; reutilizar el mismo par documentos/métricas por chatbot. Para dos chatbots: cinco solicitudes de datos en el resumen (listado y dos pares).
- Vista visual: cero consultas conversacionales o accesos al LLM. La apariencia se actualiza al pausar la escritura, evitando recargar el widget con cada pulsación.
- Recursos: ningún recurso propio debe fallar o tener MIME inesperado. Una fuente propia se comparte entre temas y widget; un gráfico no necesita otra biblioteca.
- Transferencia: investigar incrementos superiores al 20 % en una navegación comparable de una versión de producción; no comparar compilación de desarrollo con producción.
- Tiempo: guardar duraciones observadas con las mismas respuestas sintéticas. No usar una sola muestra como promesa de rendimiento ni atribuir al frontend la duración de Ollama.

La línea base usa el frontend de Docker que estaba activo antes de los cambios, datos sintéticos de dos chatbots y 1440 px. La versión anterior no tenía un identificador de fuente adjunto a sus capturas; se identifica por fecha, archivos de evidencia y origen de ejecución. Los resultados finales incorporan digest de imagen y huellas del código.
