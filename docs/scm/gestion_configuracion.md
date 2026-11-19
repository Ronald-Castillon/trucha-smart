# Plan de gestión de configuración de software (SCM)

Unidad IV · TruchaSmart. Herramienta: suite gratuita de GitHub (repositorio, Issues, Pull
Requests, protección de ramas, Actions y Releases).

## 1. Elementos de configuración y líneas base

| Elemento de configuración | Ubicación |
|---|---|
| Código fuente (arquitectura hexagonal) | `src/domain`, `src/ports`, `src/adapters` |
| Pruebas | `tests/unit`, `tests/integration`, `tests/e2e`, `tests/carga` |
| Base de datos | `db/schema.sql`, `db/seed.sql` |
| Configuración del dominio | `config/umbrales.yaml`, `config/alimentacion.yaml` |
| Modelo de IA | `models/riesgo/` |
| Contrato de la API | `docs/openapi.json` |
| Construcción y despliegue | `Dockerfile`, `docker-compose.yml`, `render.yaml`, `.github/workflows/` |
| Documentación | `docs/` (ADR, C4, GQM, calidad, releases, SCM) |

| Línea base | Rama o tag | Qué contiene |
|---|---|---|
| Producción | `main` | Solo versiones liberadas (`release/*`, `hotfix/*`) |
| Integración | `develop` | Trabajo terminado y revisado del equipo |
| Versiones liberadas | tags `v1.0-PMV`, `v2.0-Inc2`, `v3.0-Inc3`, `v4.0-Inc4`, `vX.Y.Z` | Instantánea inmutable publicada en GitHub Releases |

## 2. Administración del cambio

1. **Registro.** Todo cambio se registra como Issue: las historias con la etiqueta `hu` y las
   solicitudes de cambio con la plantilla [Solicitud de Cambio (RFC)](../../.github/ISSUE_TEMPLATE/change_request.md),
   que aplica las etiquetas `change-request` y `pendiente-evaluacion`.
2. **Evaluación.** El solicitante completa el análisis de impacto (esfuerzo, riesgo, elementos de
   configuración afectados y versión de destino).
3. **Aprobación (CCB).** El Tech Lead revisa la RFC y cambia `pendiente-evaluacion` por `aprobado`,
   o la cierra como rechazada con su motivo.
4. **Implementación.** Se crea una rama `feature/<id>-<nombre>` desde `develop` (o `hotfix/*` desde
   `main` si es urgente) con commits convencionales.
5. **Revisión.** El Pull Request usa la [plantilla de PR](../../.github/PULL_REQUEST_TEMPLATE.md), se
   enlaza al Issue y necesita **1 aprobación de un par distinto del autor** y los checks de CI.
6. **Cierre.** El Issue se cierra cuando el cambio llega a `main` en una versión liberada.

## 3. Estrategia de ramificación (GitFlow)

| Rama | Se crea desde | Se integra en | Uso |
|---|---|---|---|
| `main` | — | — | Línea base de producción |
| `develop` | `main` | — | Línea base de integración |
| `feature/*` | `develop` | `develop` (PR) | Una historia de usuario o solicitud de cambio |
| `release/vX.Y.Z` | `develop` | `main` (PR) y de vuelta a `develop` | Estabilizar: versión, notas de entrega |
| `hotfix/*` | `main` | `main` (PR) y de vuelta a `develop` | Parche urgente de producción |

Historia: los incrementos 1 a 4 se desarrollaron con ramas `feature/huXX-*` integradas por PR en
`main` (desarrollo basado en tronco). Desde la Unidad IV se agrega `develop` y se aplica GitFlow
completo.

### Protección de ramas (Settings → Branches)

| Regla | `main` | `develop` |
|---|---|---|
| Require a pull request before merging | ✓ | ✓ |
| Require approvals (1) y descartar aprobaciones al cambiar el código | ✓ | ✓ |
| Require status checks to pass: Calidad, Seguridad, Imagen Docker, PostgreSQL, E2E | ✓ | ✓ |
| Require conversation resolution | ✓ | ✓ |
| Bloquear force push y borrado | ✓ | ✓ |

## 4. Construcción del sistema (integración continua)

`.github/workflows/ci.yml` se ejecuta en cada Pull Request hacia `develop` o `main` y en cada push:
lint (ruff), pureza del dominio e import-linter, pruebas con cobertura ≥ 80 %, OpenAPI, SAST
(Bandit) y dependencias (pip-audit), construcción de la imagen Docker, integración con
PostgreSQL 16, E2E con Playwright, y confiabilidad y rendimiento. La protección de ramas bloquea la
fusión si algún check obligatorio falla.

## 5. Versiones y entregas

- **Versionamiento semántico:** `vMAJOR.MINOR.PATCH`. Los incrementos del curso conservan sus
  tags (`v1.0-PMV` … `v4.0-Inc4`, equivalentes a 1.0.0 … 4.0.0); los cambios posteriores usan
  SemVer estricto (`v4.1.0` para una mejora compatible, `v4.1.1` para un parche).
- **Publicación:** `.github/workflows/release.yml` construye desde el tag el paquete Python, la
  imagen Docker y el contrato OpenAPI, y publica el GitHub Release con las notas de
  `docs/releases/<tag>.md`.

## 6. Trazabilidad

La matriz unificada Cambio → Issue → Rama → PR → Tag → Release está en
[matriz_trazabilidad.md](matriz_trazabilidad.md).
