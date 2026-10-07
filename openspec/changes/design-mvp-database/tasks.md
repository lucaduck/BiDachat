## 1. Preparación documental

- [x] 1.1 Inicializar OpenSpec para Codex y crear carpetas del MVP; verificar configuración, habilidades y estructura documentada en README.md.
- [x] 1.2 Redactar diseño de datos con siete tablas, incluido `llm_models`, relaciones y trazabilidad; verificar presencia del diagrama, diccionario y decisiones en docs/database-design.md.
- [x] 1.3 Preparar propuesta, especificación y diseño del cambio; verificar correspondencia de la capacidad mvp-persistence con proposal.md.

## 2. Aprobación previa a implementación

- [x] 2.1 Registrar aprobación o correcciones del SRS y de las decisiones de la sección 11 de docs/database-design.md; verificar constancia explícita del usuario y actualizar propuesta/specs si cambia su alcance. El usuario aprobó el SRS 0.1 y las decisiones el 2026-09-22.
- [x] 2.2 Seleccionar el modelo de embeddings y comprobar compatibilidad con la dimensión local 768 o migrarla; verificar igualdad de perfil entre vectores documentales y de consulta antes de procesar conocimiento. Se seleccionó `gemini-embedding-2`/768 y el servicio rechaza perfiles documentales o de consulta incompatibles. PostgreSQL 16.15 y pgvector 0.8.6 ya fueron verificados.
- [x] 2.3 Registrar en qué versión se incorporará la inferencia seleccionable entre proveedor externo y Ollama local; verificar la decisión del usuario y formalizar requisito, escenarios y tareas en el cambio correspondiente antes de implementar esa ampliación. El usuario aprobó Ollama local en Version 1 y se creó `add-local-ollama-provider`.

## 3. Esquema local y persistencia de aplicación

- [x] 3.1 Configurar migración inicial SQL con creación/reversión mediante psql y Docker Compose; verificar creación, reversión sobre la BD local vacía, reaplicación y documentar comandos en database/README.md.
- [x] 3.2 Crear las siete tablas, restricciones e índices autorizados; probar FK, unicidad de (`provider`, `model`), referencias al catálogo, historial inmutable, estados, duración no negativa, cascadas y dimensión vectorial contra PostgreSQL/pgvector.
- [x] 3.3 Implementar conexión y modelos de backend sin credenciales versionadas; verificar persistencia y rollback transaccional con pruebas de integración.
- [x] 3.3.1 Crear aplicación FastAPI y configuración por entorno; verificar salud HTTP, errores públicos seguros, pruebas, Ruff y ejecución Docker conforme a RNF-01/RNF-03/RNF-04 y RS-04/RS-09. No completa la conexión ni los modelos de 3.3.
- [x] 3.4 Implementar persistencia y validación de sesiones revocables; probar cierre de sesión, expiración y desactivación conforme a CA-UC01-01 a CA-UC01-04.
- [x] 3.5 Implementar persistencia de chatbots y configuración; verificar CRUD y estabilidad del identificador conforme a CA-UC02-01 a CA-UC02-04 y CA-UC03-01 a CA-UC03-04. La asociación de fuentes se realiza mediante carga/listado administrativo de documentos aislados por chatbot.
- [x] 3.6 Implementar publicación atómica y recuperación de fragmentos por chatbot; probar fallo parcial, reintento, perfil incompatible y aislamiento A/B conforme a CA-UC04-03 a CA-UC04-05.
- [x] 3.7 Implementar registros de consultas y agregación de métricas; probar éxito, fallo, interrupción sin duración, periodo vacío y asociación correcta conforme a CA-UC06-05, CA-UC07-05 y CA-UC08-01 a CA-UC08-04.
- [x] 3.8 Implementar el borrado aprobado y la limpieza del volumen; verificar cascadas, rollback y concurrencia con cargas/consultas, sin archivos públicos ni datos huérfanos recuperables.

## 4. Verificación y cierre de implementación

- [x] 4.1 Ejecutar pruebas de integración de persistencia con PostgreSQL/pgvector y Ruff sobre el código creado; registrar resultados reales y pendientes de los módulos consumidores.
- [x] 4.2 Documentar instalación, respaldo/restauración y migraciones; verificar comandos en entorno local y validar OpenSpec antes de sincronizar o archivar el cambio implementado.
