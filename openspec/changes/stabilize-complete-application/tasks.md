Plan preparado el 6 de octubre de 2026. Documentación de planificación completada;
implementación no iniciada. Casillas abiertas representan trabajo futuro, no deuda ya
resuelta. El alcance se explica en [proposal.md](proposal.md), el método en
[design.md](design.md) y la aceptación en [spec.md](specs/complete-application-stability/spec.md).

## 1. Dependencias y base reproducible — prioridad alta

Dependencia: comienzo de ejecución autorizado. Salida: actualización compatible y
evidencia de avisos cerrados o tratados, sin pérdida de los recorridos principales.

- [ ] 1.1 Registrar versiones, lockfiles, imágenes, modelo/configuración no secreta y cambios preexistentes; conservar una referencia de reversión reproducible.
- [ ] 1.2 Reconsultar avisos y compatibilidad oficiales de Next/React y dependencias transitivas; clasificar los cuatro paquetes señalados en producción según archivos incluidos y uso efectivo del proxy.
- [ ] 1.3 Actualizar el lote de producción y lockfile sin actualización forzada indiscriminada; reconstruir Docker standalone y verificar login, editor, retorno de preview y snippet.
- [ ] 1.4 Actualizar herramientas de desarrollo afectadas en un segundo lote y revisar dependencias Python con la herramienta disponible; registrar decisiones y avisos pendientes sin asumir equivalencia entre vulnerabilidad del paquete y explotación real.
- [ ] 1.5 Ejecutar lint, tipos, formato, pruebas afectadas, build y auditorías repetidas; impedir cierre de publicación con avisos críticos/altos aplicables sin tratamiento.

## 2. Inferencia local y errores — prioridad alta

Dependencia: base del bloque 1 estable. Salida: texto e imagen reproducibles con
modelos admitidos; fallos seguros con métricas correctas (RF-08/12/18–26, RS-09).

- [ ] 2.1 Reproducir la respuesta visual vacía con qwen3-vl:2b y comparar con qwen3-vl:2b-instruct; registrar metadatos de finalización y tokens sin guardar entradas privadas.
- [ ] 2.2 Medir GPU, VRAM/RAM y tiempos de carga en Docker durante alternancia de embeddings, texto e imagen; conservar valores actuales como referencia.
- [ ] 2.3 Corregir límites/modo de generación para las combinaciones admitidas dentro del proveedor backend; añadir regresión de respuesta final vacía y salida truncada.
- [ ] 2.4 Validar el modelo configurado para imágenes como fuentes y documentar configuración compatible; no sustituir silenciosamente modelos de bots existentes ni cambiar embeddings/dimensión.
- [ ] 2.5 Probar indisponibilidad, timeout y respuesta inválida: error sin secretos, pregunta/adjunto recuperables y una consulta fallida con modelo/tiempo correctos; sin reintentos ocultos.
- [ ] 2.6 Ejecutar casos reales de texto, imagen y descripción de imagen como fuente; actualizar guía de Ollama con memoria medida, modelos comprobados y límites conocidos.

## 3. Fuentes, RAG y proveedores — prioridad alta

Dependencia: bloque 2 para pruebas visuales. Las filas con proveedor externo
requieren credenciales y presupuesto permitido. Salida: matriz por formato/proveedor
con evidencia real o pendiente explícito (CA-UC04, CA-UC06 y CA-UC07).

- [ ] 3.1 Extender fixtures aislados y ejecutor real: terminar pronto ante error visible y garantizar limpieza aun si falla una prueba; mantener intactos los recursos del usuario.
- [ ] 3.2 Procesar PDF con texto, DOCX, TXT y CSV con un dato conocido por caso; verificar estado disponible, chunks, vectores de 768 y recuperación del dato.
- [ ] 3.3 Procesar PNG, JPEG y WebP como fuentes con el modelo general; verificar descripción previa a embeddings y recuperación del contenido visual.
- [ ] 3.4 Probar archivo corrupto, tipo engañoso, tamaño fuera del límite y PDF sin texto legible; verificar rechazo/fallo honesto sin inventar soporte OCR.
- [ ] 3.5 Probar asociación compartida y retiro entre dos bots con fuentes textuales y visuales; verificar aislamiento en recuperación y ausencia de borrado del archivo compartido.
- [ ] 3.6 Ejecutar texto e imagen en cada proveedor externo habilitado según sus capacidades; registrar modelo, resultado, límites de consumo y filas bloqueadas por credenciales sin marcar mocks como aceptación real.
- [ ] 3.7 Contrastar métricas del periodo contra consultas reales completadas/fallidas y tiempos almacenados; conservar modelo ejecutado al cambiar la configuración de un bot.

## 4. Rendimiento y recuperación — prioridad media

Dependencia: fixtures del bloque 3 y corrección del proveedor. Salida: mediciones
comparables y resolución de fallos concretos; sin umbrales arbitrarios de rendimiento.

- [ ] 4.1 Medir solicitudes, bytes y tiempos del Resumen con cero, dos y un conjunto mayor de bots aislados, mismo periodo y carga local registrada; documentar el crecimiento 1 + 2N.
- [ ] 4.2 Reducir solicitudes redundantes demostradas; si se requiere agregado API, fijar contrato/periodo/autorización y mantener endpoints thin con lógica en servicios existentes.
- [ ] 4.3 Verificar equivalencia de conteos, fuentes compartidas y promedios respecto a la API original; conservar separación entre cero y ausencia de muestras.
- [ ] 4.4 Probar desconexión, timeout de proveedor, repetición de carga y reinicio durante procesamiento; registrar estados persistidos y publicación parcial si existe.
- [ ] 4.5 Corregir únicamente los fallos de recuperación o bloqueo demostrados en los servicios y transacciones existentes; probar que no quedan fuentes incompletas disponibles ni se eliminan datos ajenos.

## 5. Automatización y aceptación de interfaz — prioridad media

Dependencia: cada bloque corregido aporta regresiones; cierre con versión integrada.
Salida: puertas de calidad reproducibles y comprobaciones humanas registradas.

- [ ] 5.1 Integrar lint, formato, tipos, unidades, backend crítico y build en CI del repositorio; usar PostgreSQL/pgvector aislado y un job de navegador con respuestas controladas.
- [ ] 5.2 Separar llamadas externas/LLM reales de las verificaciones de cada PR; proteger secretos y artefactos, fijar precondiciones y limpieza del recorrido real.
- [ ] 5.3 Ejecutar regresión integrada de navegación/sesión, editor, asociación de fuentes, widget externo y métricas; revisar capturas de los tamaños/temas afectados por las actualizaciones.
- [ ] 5.4 Registrar escucha con lector de pantalla y zoom nativo 200 % en acceso, editor, publicación y widget; corregir hallazgos comprobados y repetir solo recorridos afectados.
- [ ] 5.5 Registrar cancelación humana del selector nativo de captura y conservación de pregunta/adjunto previo; mantener la confirmación anterior de captura adjunta como evidencia válida.
- [ ] 5.6 Actualizar tareas 6.5, 7.2, 7.3 y 7.7 de professionalize-frontend-experience solo cuando la evidencia correspondiente exista; generar matriz RF/RNF/RS/CA con resultados y límites actuales.

## 6. Condiciones de publicación y entrega

Dependencia: bloques locales cerrados. El destino TLS requiere dominio/plataforma
y acceso autorizados; estos pendientes no impiden entregar los bloques locales.

- [ ] 6.1 Revisar persistencia/revocación de sesión, acceso administrativo, límites de consultas y errores seguros; documentar hallazgos concretos y tratar defectos demostrados sin decidir una migración de autenticación por defecto.
- [ ] 6.2 Crear respaldo de base y documentos de QA y restaurar en volúmenes temporales aislados; verificar fuentes, asociaciones, recuperación y limpieza sin operar sobre datos del usuario.
- [ ] 6.3 Documentar destino de publicación y configurar/verificar HTTPS/TLS en el mecanismo autorizado; comprobar panel, API y widget externo sin contenido activo mixto y con orígenes correctos.
- [ ] 6.4 Reconstruir la versión final reproducible y ejecutar acceso → crear/configurar → cargar/procesar → recuperar → conversar con imagen → integrar externamente → consultar métricas; probar reversión de imagen/configuración en el entorno aislado.
- [ ] 6.5 Publicar informe de cierre con versiones, avisos tratados, pruebas, mediciones y pendientes; distinguir «verificado localmente» de «aceptado para publicación» y no declarar 100 % sin criterio/evidencia.

## Regla de trabajo y cierre

Cada tarea sigue: reproducir → corregir → verificar → guardar evidencia → marcar.
Un fallo reproducible se corrige antes de cerrar su bloque. Si faltan credenciales,
interacción humana o destino, registrar el pendiente específico y continuar con las
tareas independientes; el paso del tiempo no cuenta como aprobación.

No hay estimación de días ni promesa de latencia: dependen de acceso al entorno,
proveedores y comprobaciones humanas. Un bloque cierra por evidencia, no por tiempo.
