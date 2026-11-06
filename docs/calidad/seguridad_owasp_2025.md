# Seguridad (FURPS+ "+"): OWASP Top 10 2025, SAST y restricciones

Issue #32 (RNF-+) · Incremento 3

## 1. Análisis estático y de dependencias (medido)

| Herramienta | Alcance | Resultado | Meta | Evidencia |
|---|---|---|---|---|
| Bandit 1.9.4 (SAST) | `src/` (5 679 líneas) | 0 altos, 0 medios, 2 bajos | 0 altos / medios | `evidencias/inc3/seguridad/bandit.json`, job `seguridad` en CI |
| pip-audit 2.10.1 | dependencias instaladas | 0 vulnerabilidades en 99 paquetes | 0 vulnerabilidades conocidas | `evidencias/inc3/seguridad/pip-audit.json`, job `seguridad` en CI |

Los 2 hallazgos bajos de Bandit se revisaron y se aceptan:

- **B311** (`random` en `src/adapters/inbound/simulator/escenarios.py`): genera lecturas simuladas
  reproducibles, no secretos. Los secretos usan `secrets` (claves de integración) y bcrypt.
- **B105** (cadena tipo contraseña en `src/adapters/config.py`): es la clave JWT *de ejemplo*; con
  `APP_ENV=produccion` la aplicación se niega a arrancar si se usa (prueba
  `test_produccion_rechaza_la_clave_jwt_de_ejemplo_o_corta` y job `docker` de CI).

Fecha de la medición local: 2026-10-30. CI repite ambos análisis en cada push (job `seguridad`) y
falla con hallazgos de severidad media/alta o con vulnerabilidades conocidas.

## 2. Matriz OWASP Top 10 2025

| # | Categoría | Riesgo en TruchaSmart | Mitigación implementada | Evidencia (archivo / prueba) |
|---|---|---|---|---|
| A01 | Broken Access Control | Un operario modifica estanques o gestiona usuarios; acceso sin sesión | Permisos por rol en el dominio (`Usuario.exigir`), verificados en cada caso de uso; 401 sin token, 403 sin permiso; cookie `SameSite=Lax` frente a CSRF | `src/domain/model/usuario.py`, `tests/unit/test_usuarios.py`, `tests/integration/test_api_*.py` (403) |
| A02 | Security Misconfiguration | Clave JWT por defecto en producción; cabeceras ausentes; clickjacking; contenedor como root | La app no arranca con `APP_ENV=produccion` y la clave por defecto o < 32 caracteres; cookie `Secure` en producción; CSP, `X-Frame-Options: DENY`, `nosniff`, `Referrer-Policy`, `Permissions-Policy`; la imagen Docker corre con usuario sin privilegios | `src/adapters/config.py`, `src/adapters/inbound/rest/seguridad_http.py`, `tests/integration/test_seguridad_http.py` |
| A03 | Software Supply Chain Failures | Dependencia con vulnerabilidad conocida; acciones de CI desactualizadas | pip-audit en CI; Dependabot semanal (pip, GitHub Actions, Docker); versiones mínimas fijadas en `pyproject.toml` | `.github/dependabot.yml`, `.github/workflows/ci.yml` (job `seguridad`) |
| A04 | Cryptographic Failures | Contraseñas o claves de integración legibles en la BD | bcrypt con sal para contraseñas; SHA-256 de las claves de integración (solo se muestra una vez); JWT HS256 con expiración | `src/adapters/outbound/security/`, `src/domain/model/clave_integracion.py`, `tests/unit/test_integraciones.py` |
| A05 | Injection | Inyección SQL en filtros de historial o reportes; XSS en nombres de estanque | SQLAlchemy con parámetros enlazados (sin SQL concatenado con datos del usuario); Jinja2 con autoescape; validación de tipos con Pydantic | `src/adapters/outbound/persistence/`, `src/adapters/inbound/rest/esquemas.py` |
| A06 | Insecure Design | Decisiones automáticas peligrosas (suspender alimentación sin humano) | Arquitectura hexagonal con reglas en el dominio; recomendaciones explicables, la decisión es humana (ADR-005, ADR-006); umbrales configurables | `docs/adr/`, `config/umbrales.yaml` |
| A07 | Authentication Failures | Fuerza bruta sobre el login | Bloqueo de 5 min tras 3 intentos fallidos (423); mensajes genéricos; contraseñas de 8+ caracteres | HU-11, `tests/unit/test_seguridad.py`, `tests/integration/test_api_auditoria.py`, `evidencias/inc3/RF11_*` |
| A08 | Software or Data Integrity Failures | Imagen de despliegue alterada; datos de sensores falsos | La imagen Docker se construye en CI desde el repositorio; la API externa es de solo lectura con clave revocable; lecturas validadas por rango | `Dockerfile`, job `docker` en CI, HU-09 |
| A09 | Security Logging and Alerting Failures | No saber quién accedió o intentó acceder | Bitácora de seguridad (logins, bloqueos, claves creadas/revocadas/rechazadas) con usuario, IP y hora, sin secretos | HU-11, `/auditoria`, `GET /api/auditoria`, `evidencias/inc3/RF11_paso2_resultado.png` |
| A10 | Mishandling of Exceptional Conditions | Errores que exponen trazas o dejan el sistema caído | Manejador global con formato `{"error","detalle","campo"}` sin trazas; `/api/salud` responde 503 si la BD cae y la app se recupera sola | `src/adapters/inbound/rest/errores.py`, `tests/integration/test_salud.py`, `docs/calidad/confiabilidad.md` |

## 3. Restricciones técnicas (FURPS+ "+")

| Restricción | Cumplimiento | Evidencia |
|---|---|---|
| Contrato de API documentado | OpenAPI 3 exportado y verificado en CI (`export_openapi.py --check`) | `docs/openapi.json` |
| Despliegue en contenedor | `Dockerfile` + `docker-compose.yml`; CI construye la imagen | job `docker` en CI |
| Base de datos PostgreSQL 16 (SQLite en desarrollo) | Pruebas de integración y de confiabilidad/carga contra PostgreSQL en CI | jobs `postgres`, `confiabilidad-rendimiento` |
| Arquitectura hexagonal | Dominio y puertos solo con biblioteca estándar; 3 contratos import-linter | `tools/check_domain_purity.py`, `pyproject.toml` |

## 4. Deuda conocida (no oculta)

- La CSP permite `'unsafe-inline'` para scripts porque varias plantillas usan `<script>` en línea;
  moverlos a archivos estáticos permitiría quitarla.
- No hay HTTPS en la aplicación: se espera un proxy inverso con TLS en el despliegue (la cookie
  `Secure` se activa con `APP_ENV=produccion`).
- No hay limitación de tasa global por IP; el bloqueo por cuenta de HU-11 cubre la fuerza bruta
  sobre un usuario, no el *password spraying* sobre muchos usuarios.
