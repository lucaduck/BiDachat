# Comprobación real de fuentes, RAG y proveedores

Fecha: 6 de octubre de 2026. Alcance: tareas 3.1–3.7 del cambio `stabilize-complete-application`. Se usaron usuarios, bots y archivos sintéticos aislados; el ejecutor elimina sus recursos incluso si falla. Ningún resultado simulado se considera aceptación de un proveedor.

| Tarea | Resultado comprobado | Evidencia |
|---|---|---|
| 3.1 | Fixtures independientes y limpieza final tras un fallo de aserción. También se eliminó una limpieza global previa de pruebas que podía borrar usuarios ajenos. | [Ejecución de fuentes](local-acceptance.json), [ejecución de métricas](metrics-acceptance.json) |
| 3.2 | PDF con texto, DOCX, TXT y CSV llegaron a `ready`; cada uno produjo chunks con vector de 768 dimensiones y recuperó el dato sintético. | [Ejecución de fuentes](local-acceptance.json) |
| 3.3 | PNG, JPEG y WebP generaron descripción visual previa al embedding, chunks de 768 dimensiones y recuperación del marcador visible. | [Ejecución de fuentes](local-acceptance.json) |
| 3.4 | PDF corrupto, tipo declarado engañoso, archivo excesivo, firma PNG inválida y PDF sin texto se rechazaron o fallaron sin chunks; no se atribuye OCR al sistema. | [Ejecución de fuentes](local-acceptance.json) |
| 3.5 | Se compartió una fuente textual y una visual entre dos bots; retirarlas de uno eliminó su recuperación allí y mantuvo la fuente y el acceso del otro. | [Ejecución de fuentes](local-acceptance.json) |
| 3.6 | OpenAI (`gpt-5.6-luna`) respondió texto e imagen. OpenRouter (`openrouter/free`) respondió texto e imagen sin costo declarado por la API. La configuración anterior `nvidia/nemotron-3-embed-1b:free` falló como chat por ser un modelo de embeddings y se cambió la configuración local a `openrouter/free`. Gemini queda pendiente: no hay credencial disponible. | [Proveedores](provider-acceptance.json) |
| 3.7 | Una consulta completada y una fallida se reflejan como 2 totales, 1 completada y 1 fallida. Los tiempos persistidos fueron 47 465 ms y 12 051 ms. El modelo ejecutado quedó en cada consulta pese al cambio posterior de configuración. | [Métricas](metrics-acceptance.json) |

La primera ejecución completa falló al comprobar 3.7 porque no se guardaba el instante final de la consulta fallida. Se corrigió el servicio, se añadió una regresión y se repitió 3.7 con éxito. La evidencia de 3.2–3.5 procede de aquella primera ejecución y conserva explícitamente el fallo global; las filas individuales y la limpieza sí pasaron.

El usuario autorizó hasta USD 1 para API externas. Las dos llamadas directas a OpenAI registraron un costo estimado de USD 0,0001868 según los tokens de la respuesta y la tarifa consultada. Una llamada adicional para métricas usó OpenAI, por lo que esa cifra **no** representa el gasto total exacto; el consumo observado permanece muy por debajo del límite autorizado. No se guardaron claves, preguntas ni respuestas privadas en la evidencia.

La inferencia local con `qwen3-vl:2b-instruct` mostró una respuesta 503 intermitente en una ejecución de métricas. Sigue pendiente la estabilización específica del bloque 2. Gemini sigue sin aceptación real hasta disponer de su credencial. Los resultados son de los contenedores locales, no una aceptación del futuro despliegue de producción.

El registro local conserva el modelo antiguo de OpenRouter porque puede estar asociado a bots existentes. No se cambiaron silenciosamente esas asociaciones. Para usar el proveedor comprobado, cada bot afectado debe seleccionar `openrouter/free` en el editor.
