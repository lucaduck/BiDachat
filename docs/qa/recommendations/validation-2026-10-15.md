# Comprobación de recomendaciones — 15 de octubre de 2026

Base local: `develop` sobre `10a01bf`, con cambios aún sin commit. Se utilizaron
datos sintéticos y una base PostgreSQL/pgvector temporal en un contenedor con
almacenamiento efímero. Los volúmenes existentes de BIDACHAT no se modificaron.
La suite backend final registró **83 aprobadas y 2 omitidas** (pruebas optativas
de modelo local real); las 30 pruebas unitarias del frontend pasaron. Ruff,
ESLint y la comprobación TypeScript que excluye el archivo generado y corrupto
de `.next/dev/types/validator.ts` también aprobaron.

| Recorrido                  | Resultado comprobado                                                                                                                                                                                                                                                                                                                                        | Límite de la evidencia                                                                                                           |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| Integraciones existentes   | 10 pruebas con PostgreSQL/pgvector aprobadas; incluyen reintento de documento compartido desde el chatbot asociado.                                                                                                                                                                                                                                         | No es la base del VPS.                                                                                                           |
| Ingestión y recuperación   | DOCX con tabla, CSV con alias MIME y separador `;`, TXT, PDF digital con tabla e imagen PNG llegaron a chunks recuperables; el documento compartido se recuperó solo mientras existió la asociación.                                                                                                                                                        | Las respuestas de embedding y descripción visual de este recorrido fueron simuladas; `wkhtmltopdf` generó el PDF sintético.      |
| Modelo local real          | PNG, JPEG y WebP con “VENTAS 42” se describieron con `qwen3-vl:2b-instruct`; `embeddinggemma:300m` generó vectores de 768 dimensiones; pgvector recuperó los tres. Prueba aprobada en 416,88 s.                                                                                                                                                             | CPU local, una imagen simple por formato; no extrapolar calidad ni latencia al VPS.                                              |
| Duración del modelo visual | El registro de Ollama muestra `/api/chat` de 2 min 21 s, 1 min 59 s y 2 min 1 s; `/api/embed` de aproximadamente 5 s por fuente.                                                                                                                                                                                                                            | Estas cifras corresponden a este equipo y a cargas secuenciales con `keep_alive: 0`. No son tiempos estándar del chatbot.        |
| Respaldo y restauración    | Un Compose temporal sembró un bot y un original; `backup-production.sh` produjo manifiesto y copia coordinada; `verify-production-backup.sh` restauró en un volumen aislado y comprobó tabla y archivo. Prueba aprobada.                                                                                                                                    | Falta ensayo sobre una copia del despliegue real y comprobar login y recuperación después del restore.                           |
| PDF digital                | La extracción con `pypdf` recuperó `PDF_TASA_BI` y `91 por ciento` de una tabla sencilla.                                                                                                                                                                                                                                                                   | El texto salió por celdas; no se demostró preservación de relaciones en tablas complejas. OCR no forma parte de esta aceptación. |
| Compose de producción      | Configuración renderizada con cinco límites de CPU/RAM; solo Nginx publica `127.0.0.1:3000`. `nginx -t` aprobó.                                                                                                                                                                                                                                             | No se ejecutó aún el stack completo detrás de Apache/TLS del VPS.                                                                |
| Guardrail de fuentes       | El backend añade una instrucción de sistema común para tratar documentos, página e imagen como evidencia no confiable; 42 pruebas dirigidas de proveedores/extracción aprobaron. La primera prueba real repitió una orden inyectada aunque dio el dato correcto; tras pedir expresamente que no cite esas órdenes, la misma prueba respondió sin repetirla. | Una prueba adversarial aprobada no garantiza resistencia general; faltan ataques por página, imagen y proveedores externos.      |

El proveedor que describe fuentes visuales puede configurarse por separado
con `VISION_PROVIDER` y `VISION_MODEL`. Las pruebas de contrato cubren los tres
proveedores externos sin generar consumo; la prueba de tres formatos usó Ollama.
En la repetición de una imagen con límite de 3 GiB, el contenedor llegó a
2,88 GiB durante la inferencia y terminó en 142,49 s. Esta observación no garantiza que 3 GiB basten
para otras imágenes o concurrencia.

## Inventario del VPS y preparación de permisos

Servidor `srvldk.lucaduck.com`, vinculado al dominio del proyecto: 4 CPU AMD
EPYC virtuales, 7,8 GiB RAM, sin swap, 132 GiB libres en `/`; no se observaron
dispositivos `/dev/nvidia*` ni `/dev/dri/*`. No hay contenedores BIDACHAT en
ejecución. La ruta acordada existe y contiene `.env`; no necesita un checkout
Git porque el workflow transfiere los archivos del commit aprobado por SSH.
Inicialmente el directorio y `.env` pertenecían a `root:root`.
Se transfirió la propiedad de **esos dos elementos** a `despliegue:despliegue`,
se dejó el directorio en modo `750` y el archivo en `600`, y se comprobó como
`despliegue` que puede leer `.env` y escribir en la ruta. El usuario pertenece
al grupo Docker, pero su acceso SSH con la clave local probada fue rechazado.
El Apache del dominio aún sirve `public_html` y no tiene `ProxyPass` hacia
BIDACHAT. Tiene activos los módulos
Apache `proxy`, `proxy_http`, `headers`, `rewrite` y `ssl`, pero no `remoteip`.
El DNS público responde con direcciones de Cloudflare. En el `.env` existen
`FRONTEND_PORT=3000`, `EMBEDDING_PROVIDER=ollama`,
`EMBEDDING_MODEL=embeddinggemma:300m` y `OLLAMA_MODEL=qwen3-vl:2b-instruct`; no
se encontraron las diez variables obligatorias de límites de CPU/RAM. No se
leyeron ni imprimieron valores de credenciales.

Estas condiciones impiden validar la aplicación en ese VPS. La siguiente
liberación debe verificar el acceso SSH de GitHub Actions para `despliegue`, completar los límites
según la memoria compartida con otros servicios, instalar el proxy Apache y
publicar las imágenes GHCR de un commit aprobado. Solo entonces corresponde
probar TLS, orígenes permitidos, identidad real del cliente, tiempos, respaldo
y restauración sobre una copia de datos del entorno.

## Comandos de pruebas locales

```bash
DATABASE_URL=postgresql+psycopg://bidachat_test:local_test_only@127.0.0.1:49831/bidachat_test \
  APP_ENV=test GEMINI_API_KEY= OPENAI_API_KEY= OPENROUTER_API_KEY= \
  backend/.venv/bin/python -m pytest -q -p no:cacheprovider -m integration backend/tests

DATABASE_URL=postgresql+psycopg://bidachat_test:local_test_only@127.0.0.1:49831/bidachat_test \
  APP_ENV=test GEMINI_API_KEY= OPENAI_API_KEY= OPENROUTER_API_KEY= \
  backend/.venv/bin/python -m pytest -q -p no:cacheprovider \
  backend/tests/test_ingestion_pipeline.py backend/tests/test_ingestion_regression.py

DATABASE_URL=postgresql+psycopg://bidachat_test:local_test_only@127.0.0.1:49831/bidachat_test \
  APP_ENV=test GEMINI_API_KEY= OPENAI_API_KEY= OPENROUTER_API_KEY= \
  BIDACHAT_TEST_OLLAMA_BASE_URL=http://127.0.0.1:51337 \
  backend/.venv/bin/python -m pytest -q -p no:cacheprovider \
  backend/tests/test_local_provider_acceptance.py -k three_image_formats
```

Los puertos anteriores fueron asignados temporalmente por Docker; cada nueva
ejecución debe obtener sus propios puertos. Los contenedores de prueba se
detienen al cerrar la comprobación.
