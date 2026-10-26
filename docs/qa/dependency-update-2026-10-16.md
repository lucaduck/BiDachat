# Actualización controlada de dependencias

Fechas: 16 y 17 de octubre de 2026. Cambio OpenSpec:
`stabilize-complete-application`, tareas 1.1–1.5.

## Inventario y reversión

| Elemento                      | Referencia                                                                |
| ----------------------------- | ------------------------------------------------------------------------- |
| Rama                          | `feature/recommendations-verification`                                    |
| Commit base conservado        | `cc4b5711f4792e568889739807537d8c8285103e`                                |
| Base de `develop`             | `10a01bf43d607c7ea13c2a70144072d97df59207`                                |
| Lockfile frontend anterior    | `4b3d3b277b96e5157fa46d13ff09f068b78cd6573578c82b70a9fc2db3f697a5`        |
| Lockfile frontend actualizado | `4db1d094880771c9b861e813e8b9605f219b081e36c5c9acd2111af99dc2ad09`        |
| Lockfile Python actualizado   | `3fc41377004cac0e99e7e16788933c02bc0cfd309cad86cb7a17931e956c0639`        |
| Imagen frontend anterior      | `sha256:90f7726e80e51f5edfab3f659c0f508cd39b6afd9bed7d1486324a54020c6e95` |
| Imagen de verificación        | `sha256:46a7e50af073d6c8336f32c856cbc2449930f60587e9532593ba7eceec6ea1d4` |

El checkout ya contenía trabajo no confirmado de memoria conversacional, Vertex,
migraciones, documentación y despliegue. Se preservó sin restablecer archivos. La
reversión de este lote consiste en recuperar `frontend/package.json` y
`frontend/package-lock.json` desde el commit base y volver a etiquetar la imagen
anterior. No se modificó esquema, datos, modelos configurados ni `.env` privado.

Configuración no secreta registrada: PostgreSQL/pgvector con embeddings de 768
dimensiones; Ollama y LiteLLM/Vertex como perfiles; límites de recursos requeridos
por ambos Compose. Los hashes actuales de `.env.example`, Compose de desarrollo y
Compose de producción son, respectivamente, `60146c31…`, `21459436…` y
`4a0a1959…`.

Herramientas observadas: Node 24.17.0, npm 11.13.0, Python 3.14.6, Docker 29.6.0,
Docker Compose 5.3.1 y OpenSpec 1.7.0. El proyecto sigue declarando Python 3.12 o
superior y el CI utiliza Python 3.12; la versión local no cambia ese contrato.

## Clasificación de los cuatro paquetes de producción

La línea base del 6 de octubre registró cuatro paquetes. Se volvió a consultar el
registro npm y los avisos GHSA antes de actualizar.

| Paquete         | Clasificación                                                                                                                                                           | Tratamiento                                                                                                  |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| `next` 16.1.4   | Dependencia directa y aplicable al servidor standalone. Los avisos incluían fallos de disponibilidad y fronteras del App Router; no era aceptable publicar esa versión. | Actualizado a 16.4.2. React 19.2.3 se conservó porque satisface los rangos oficiales de React 18 y React 19. |
| `postcss`       | Transitivo de Next y Tailwind. Se usa al construir CSS; no se demostró que procese CSS suministrado por usuarios en ejecución. La versión anidada de Next era 8.4.31.   | Next 16.4.2 incorpora 8.5.23; el árbol también contiene 8.5.28. El aviso desapareció.                        |
| `sharp`         | Transitivo de Next y potencialmente ejecutable por el optimizador de imágenes del servidor. La versión anterior era 0.34.5.                                             | Next 16.4.2 resolvió 0.35.5. El aviso desapareció.                                                           |
| `source-map-js` | Transitivo de PostCSS. El riesgo requiere mapas de fuente manipulados; no existe esa entrada de usuario en BIDACHAT, pero había una corrección compatible.              | Lockfile actualizado de 1.2.1 a 1.2.2 sin override ni actualización forzada.                                 |

La evidencia exacta posterior está en
[`dependency-audit-production-2026-10-17.json`](dependency-audit-production-2026-10-17.json):
cero avisos de producción.

## Segundo lote: herramientas de desarrollo y Python

Se actualizaron ESLint a 9.39.5, Vitest a 5.0.5, Playwright a 1.64.1,
`@axe-core/playwright` a 4.14.0, los tipos de Node a 24.19.2 y Ruff a 0.17.1. La
configuración de Vitest pasó de `.ts` a `.mts` para que Vite 8 la cargue como ESM
sin advertencias. No se agregaron frameworks ni servicios.

La auditoría completa conserva cinco avisos altos, todos dentro de la cadena de
lint de `eslint-config-next` (`@next/eslint-plugin-next`, `fast-glob`, `micromatch`
y `braces`). Son herramientas de desarrollo, no se copian a la imagen standalone
ni aparecen en `npm audit --omit=dev`. La solución automática propone degradar
`eslint-config-next` de 16.4.2 a 14.2.35, incompatible con la versión de Next y con
la regla de mantener ambas versiones alineadas. No se aplicó `--force`; el aviso
queda registrado en
[`dependency-audit-development-2026-10-17.json`](dependency-audit-development-2026-10-17.json)
para volver a evaluarlo cuando exista una corrección compatible.

`uv tree --outdated` confirmó actualizaciones disponibles de FastAPI, pgvector,
Pydantic Settings, PyPDF, SQLAlchemy y Uvicorn. Esa herramienta informa frescura,
no vulnerabilidades. Se actualizó Ruff, que es la herramienta de desarrollo
afectada por este lote; las bibliotecas de ejecución se conservaron porque no había
un aviso aplicable ni un requisito que justificara ampliar el cambio después de
haber pasado la regresión completa.

## Verificación del lote

- Prettier, ESLint y 30 pruebas Vitest: aprobados.
- TypeScript y build optimizado de Next 16.4.2: aprobados.
- Dockerfile frontend: lint, unitarias, build standalone y usuario `node`:
  aprobados.
- Smoke de `/` y `/preview` desde la imagen standalone: aprobado. La primera
  conexión durante el arranque se reinició; el ciclo de espera confirmó el estado
  `Ready` y las peticiones posteriores respondieron correctamente.
- Login claro/oscuro, persistencia de tema, credenciales inválidas y retorno:
  3/3 aprobados.
- Vista previa con contexto y memoria, navegación/retorno al editor, creación y
  personalización, y copia manual del snippet: 4/4 aprobados.
- `npm audit --omit=dev`: cero vulnerabilidades registradas.
- Ruff 0.17.1: lint y formato de 78 archivos aprobados.
- Pytest determinista: 111 pruebas aprobadas y 4 externas excluidas de forma
  explícita. Las externas requieren credenciales y presupuesto habilitado.
- La regresión completa de Playwright se repitió con Chromium y Playwright 1.64.1:
  38/38 casos aprobados en 7,3 minutos.

Este lote de dependencias queda validado, pero no se declara la aplicación lista
para publicación: todavía faltan las tareas abiertas de inferencia local,
rendimiento, aceptación humana, TLS del VPS y cierre integral del cambio.
