# Comprobación de recomendaciones — 15 de octubre de 2026

Base local: rama `feature/recommendations-verification` derivada de `develop`
en `10a01bf`. Se utilizaron
datos sintéticos y una base PostgreSQL/pgvector temporal en un contenedor con
almacenamiento efímero. Los volúmenes existentes de BIDACHAT no se modificaron.
La suite backend final registró **84 aprobadas y 4 omitidas** (pruebas optativas
de modelo local real); las 30 pruebas unitarias del frontend pasaron. Ruff,
ESLint y la comprobación TypeScript que excluye el archivo generado y corrupto
de `.next/dev/types/validator.ts` también aprobaron.

| Recorrido                  | Resultado comprobado                                                                                                                                                                                                                                                                                                                                                                                                                                            | Límite de la evidencia                                                                                                                                 |
| -------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Integraciones existentes   | 10 pruebas con PostgreSQL/pgvector aprobadas; incluyen reintento de documento compartido desde el chatbot asociado.                                                                                                                                                                                                                                                                                                                                             | No es la base del VPS.                                                                                                                                 |
| Ingestión y recuperación   | DOCX con tabla, CSV con alias MIME y separador `;`, TXT, PDF digital con tabla e imagen PNG llegaron a chunks recuperables; el documento compartido se recuperó solo mientras existió la asociación.                                                                                                                                                                                                                                                            | Las respuestas de embedding y descripción visual de este recorrido fueron simuladas; `wkhtmltopdf` generó el PDF sintético.                            |
| Modelo local real          | PNG, JPEG y WebP con “VENTAS 42” se describieron con `qwen3-vl:2b-instruct`; `embeddinggemma:300m` generó vectores de 768 dimensiones; pgvector recuperó los tres. Prueba aprobada en 416,88 s.                                                                                                                                                                                                                                                                 | CPU local, una imagen simple por formato; no extrapolar calidad ni latencia al VPS.                                                                    |
| Duración del modelo visual | El registro de Ollama muestra `/api/chat` de 2 min 21 s, 1 min 59 s y 2 min 1 s; `/api/embed` de aproximadamente 5 s por fuente.                                                                                                                                                                                                                                                                                                                                | Estas cifras corresponden a este equipo y a cargas secuenciales con `keep_alive: 0`. No son tiempos estándar del chatbot.                              |
| Respaldo y restauración    | Un Compose temporal sembró un bot y un original; `backup-production.sh` produjo manifiesto y copia coordinada; `verify-production-backup.sh` restauró en un volumen aislado y comprobó tabla y archivo. Prueba aprobada.                                                                                                                                                                                                                                        | Falta ensayo sobre una copia del despliegue real y comprobar login y recuperación después del restore.                                                 |
| PDF digital                | La extracción con `pypdf` recuperó `PDF_TASA_BI` y `91 por ciento` de una tabla sencilla.                                                                                                                                                                                                                                                                                                                                                                       | El texto salió por celdas; no se demostró preservación de relaciones en tablas complejas. OCR no forma parte de esta aceptación.                       |
| Compose de producción      | Configuración renderizada con cinco límites de CPU/RAM; solo Nginx publica `127.0.0.1:3000`. `nginx -t` aprobó.                                                                                                                                                                                                                                                                                                                                                 | No se ejecutó aún el stack completo detrás de Apache/TLS del VPS.                                                                                      |
| Guardrail de fuentes       | El backend añade una instrucción de sistema común para tratar documentos, página e imagen como evidencia no confiable. La primera prueba real repitió una orden documental aunque dio el dato correcto; tras pedir que no la cite, ese caso pasó. Una orden en el contexto de página desvió la respuesta; tras omitir líneas evidentemente imperativas, la repetición pasó. Una imagen con un dato y una orden visible produjo el dato correcto sin obedecerla. | El filtro puede descartar texto legítimo y no detecta todas las órdenes. Una imagen y un modelo local no cubren otros ataques ni proveedores externos. |

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
al grupo Docker. La clave SSH que existía en el equipo fue rechazada, por lo
que se creó una clave dedicada fuera del repositorio y se añadió su parte
pública a `authorized_keys` sin retirar las entradas previas. Con verificación
estricta de la clave del host, la conexión como `despliegue` pasó y confirmó
lectura del `.env`, escritura en la ruta de despliegue y acceso a Docker. La
clave pública obtenida por `ssh-keyscan` coincidió con la clave del host
consultada mediante la sesión administrativa existente; el archivo
`known_hosts` se guardó fuera del repositorio.
El Apache del dominio aún sirve `public_html` y no tiene `ProxyPass` hacia
BIDACHAT. Tiene activos los módulos
Apache `proxy`, `proxy_http`, `headers`, `rewrite` y `ssl`, pero no `remoteip`.
El DNS público responde con direcciones de Cloudflare. En el `.env` existen
`FRONTEND_PORT=3000`, `EMBEDDING_PROVIDER=ollama`,
`EMBEDDING_MODEL=embeddinggemma:300m` y `OLLAMA_MODEL=qwen3-vl:2b-instruct`.
Tras elegir OpenAI para las imágenes, se fijaron `VISION_PROVIDER=openai` y
`VISION_MODEL=gpt-5.6-luna`. Este modelo admite entrada de imágenes mediante
Responses API según la [ficha oficial](https://developers.openai.com/api/docs/models/gpt-5.6-luna).
Se agregaron los diez límites de CPU/RAM requeridos por Compose: Ollama 2 CPU / 3 GiB,
backend 1 CPU / 768 MiB, frontend 1 CPU / 512 MiB, Nginx 0,25 CPU / 128 MiB y
PostgreSQL 1 CPU / 768 MiB. Son valores iniciales para un VPS compartido; su suma
máxima de memoria se acerca a la RAM libre observada y aún requiere medición bajo
carga y ajuste. Se verificó propietario `despliegue:despliegue`, modo `600` y
lectura por el usuario de despliegue. No se imprimieron valores de credenciales.
La petición real de una imagen sintética a `gpt-5.6-luna` fue rechazada con
HTTP `401`, código `invalid_api_key`; una lectura de `/v1/models` con la clave
del VPS y otra con la clave local dieron el mismo resultado. No hubo respuesta
visual externa válida ni se registraron tokens de respuesta. Se necesita actualizar la credencial
de OpenAI en el `.env` privado del VPS y repetir una prueba acotada antes de
aceptar ese recorrido.

El proveedor visual anterior describe **fuentes de conocimiento subidas**.
Una imagen o captura enviada en una conversación sigue el proveedor y modelo
elegidos para ese chatbot; seleccionar OpenAI en el perfil visual global no
cambia automáticamente los chatbots que usen Ollama. Los embeddings continúan
con `embeddinggemma:300m` en Ollama local.

Estas condiciones impiden validar la aplicación completa en ese VPS. La siguiente
liberación debe cargar y verificar la clave privada y `known_hosts` en los
secretos de GitHub Actions,
corregir la credencial de OpenAI, medir los límites efectivos bajo carga,
instalar el proxy Apache y publicar las
imágenes GHCR de un commit aprobado. Desde el equipo del usuario aún no hay
acceso SSH para `despliegue` antes de esta comprobación; ahora funciona desde
este entorno, pero aún no se ha ensayado desde GitHub Actions. Solo entonces corresponde
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
