# TruchaSmart

**Sistema Inteligente para Optimización de Producción Piscícola de Trucha** — proyecto del curso
*Procesos de Software* (9.º ciclo).

En las piscigranjas de trucha arcoíris el operario mide temperatura y oxígeno una o dos veces al
día, anota en un cuaderno, avisa verbalmente, alimenta por experiencia y arma reportes en Excel a
fin de mes. TruchaSmart **automatiza la detección, el registro y el cálculo**; las decisiones
siguen siendo humanas.

| Incremento | Historias | Brechas que cierra | Tag |
|---|---|---|---|
| 1 (PMV) | HU-01 autenticación y roles · HU-02 estanques y lotes · HU-03 lecturas · HU-04 alertas | B-01 a B-06 | `v1.0-PMV` |
| 2 | HU-05 historial y riesgo · HU-06 alimentación, mortalidad y FCR · HU-07 ración · HU-08 reportes | B-07 a B-09 | `v2.0-Inc2` |
| 3 (futuro) | Predicción con IA, MQTT, sensores reales | B-10 | — |

> ⚠️ **Los umbrales (`config/umbrales.yaml`) y la tabla de alimentación (`config/alimentacion.yaml`)
> son valores de referencia parametrizables: validar con el técnico de la piscigranja** antes de
> usarlos para decidir sobre peces reales.

## Arquitectura

Arquitectura **hexagonal** (ADR-001) con regla de dependencia `adapters -> ports -> domain`:

```
src/
  domain/    model/ (entidades)  service/ (reglas + casos de uso)   ← solo biblioteca estándar
  ports/     inbound/ (casos de uso)  outbound/ (repositorios, notificador, reportes, hash, reloj)
  adapters/  inbound/ rest · web · simulator     outbound/ persistence · notification · reports · security
  main.py    raíz de composición (FastAPI)
```

La pureza se verifica en CI con `tools/check_domain_purity.py` (AST, métrica M1.1) y con los
contratos de **import-linter** definidos en `pyproject.toml`.

- Decisiones: [`docs/adr/`](docs/adr) (ADR-001 a ADR-005).
- Diagramas C4 (Mermaid): [`docs/c4/`](docs/c4).
- Backlog y Definition of Done: [`docs/backlog.md`](docs/backlog.md).
- Contrato de la API: [`docs/openapi.json`](docs/openapi.json) (verificado en CI).
- Plan GQM y reportes: [`docs/gqm/`](docs/gqm).

**Stack:** Python 3.12+ · FastAPI · SQLAlchemy 2 · PostgreSQL (docker-compose) / SQLite (pruebas) ·
Jinja2 + Chart.js · JWT (cookie HttpOnly y Bearer) · bcrypt · reportlab · pytest + pytest-cov ·
ruff · import-linter · Playwright · GitHub Actions.

## Requisitos

- Python 3.12 o superior (probado con 3.13).
- Git. GitHub CLI (`gh`) opcional para crear Issues y para la métrica M2.2.
- Docker **opcional** (solo para el entorno con PostgreSQL).

## Instalación (Windows)

Git Bash:

```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -e ".[dev]"
python -m playwright install chromium
cp .env.example .env
```

PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
python -m playwright install chromium
Copy-Item .env.example .env
```

### Variables de entorno (`.env.example`)

| Variable | Descripción | Valor por defecto |
|---|---|---|
| `DATABASE_URL` | Cadena SQLAlchemy | `sqlite:///./truchasmart.db` |
| `JWT_SECRET` | Clave para firmar JWT | *(cambiar)* |
| `JWT_EXPIRA_MINUTOS` | Duración de la sesión | `480` |
| `UMBRALES_PATH` | Umbrales de calidad de agua | `config/umbrales.yaml` |
| `ALIMENTACION_PATH` | Tabla de alimentación | `config/alimentacion.yaml` |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | Credenciales de docker-compose | `trucha` / `trucha` / `truchasmart` |

## Ejecutar

### Local con SQLite

```bash
python tools/init_db.py --recrear
uvicorn src.main:app --reload
```

Abrir <http://localhost:8000> (interfaz web) o <http://localhost:8000/docs> (Swagger).

### Con docker-compose (PostgreSQL)

```bash
docker compose up --build
```

`db/schema.sql` y `db/seed.sql` se cargan automáticamente al crear el volumen. Para recargar
desde cero: `docker compose down -v` y volver a levantar.

### Datos de demostración (`db/seed.sql`)

Se regeneran con `python tools/generar_seed.py`: 3 usuarios, 3 estanques/jaulas con lote activo,
lecturas cada 3 h del 16 al 22 de octubre de 2026, 2 alertas de oxígeno en la Jaula J1,
alimentación diaria y mortalidad.

| Usuario | Contraseña | Rol |
|---|---|---|
| `admin` | `Admin123!` | Administrador |
| `piscicultor` | `Pisci123!` | Piscicultor |
| `operario` | `Oper123!` | Operario |

> Credenciales solo de demostración. Cambiarlas en cualquier entorno compartido.

### Interfaz en vivo

- **Panel:** se actualiza cada segundo, con un mini gráfico de tendencia por estanque y un destello en los valores que cambian.
- **Avisos:** en cualquier página aparece un aviso emergente (y un pitido corto) cuando se crea una alerta nueva.
- **Alertas e historial:** se actualizan solos; el historial solo lo hace si el rango incluye el día de hoy.
- **Simulador desde la web:** el Piscicultor o el Administrador pueden iniciar y detener el sensor simulado de cada estanque desde su tarjeta del panel. Escenarios: normal, oxígeno cayendo y temperatura subiendo; envía una lectura cada 2 s.

### Simulador de sensores por línea de comandos (ADR-004)

Con la app en marcha:

```bash
python -m src.adapters.inbound.simulator --estanque 1 --escenario normal --intervalo 5
```

Escenarios: `normal`, `critico_oxigeno` (el OD cae 0.4 mg/L por lectura hasta 3.5) y
`critico_temperatura` (la temperatura sube 0.5 °C por lectura hasta 20). Opciones:
`--cantidad N` (0 = sin fin), `--url`, `--usuario`/`--password` (o `SIM_URL`, `SIM_USUARIO`,
`SIM_PASSWORD`) y `--semilla`. Cada lectura se evalúa contra los umbrales y el simulador
muestra las alertas generadas; el panel web se refresca cada 2 s.

## API REST (resumen)

Contrato completo: [`docs/openapi.json`](docs/openapi.json) o <http://localhost:8000/docs>.
Autenticación con `POST /api/auth/login` → `Authorization: Bearer <token>` (la web usa cookie
HttpOnly). Todos los errores JSON devuelven `{"error", "detalle", "campo"}` con 401, 403, 404, 409 o 422.

| RF | Método y ruta | Rol mínimo |
|---|---|---|
| RF-01 | `POST /api/auth/login`, `GET /api/auth/yo`, `POST /api/auth/logout` | — |
| RF-01 | `GET/POST /api/usuarios` | Administrador |
| RF-02 | `GET /api/estanques`, `GET /api/estanques/{id}`, `GET /api/estanques/{id}/lotes`, `GET /api/lotes/{id}` | Operario |
| RF-02 | `POST /api/estanques`, `PUT/DELETE /api/estanques/{id}`, `POST /api/estanques/{id}/lotes`, `PUT /api/lotes/{id}/peso`, `POST /api/lotes/{id}/cerrar` | Piscicultor |
| RF-03 | `POST /api/lecturas`, `GET /api/lecturas?estanque_id=`, `GET /api/estanques/{id}/ultima-lectura`, `GET /api/panel` | Operario |
| RF-04 | `GET /api/alertas?estado=&estanque_id=`, `POST /api/alertas/{id}/atender` | Operario |
| RF-05 | `GET /api/estanques/{id}/historial?desde=&hasta=`, `GET /api/estanques/{id}/riesgo` | Operario |
| RF-06 | `POST/GET /api/lotes/{id}/alimentacion`, `POST/GET /api/lotes/{id}/mortalidad`, `GET /api/lotes/{id}/produccion` | Operario |
| RF-07 | `GET /api/lotes/{id}/racion` | Operario |
| RF-08 | `GET /api/reportes/{calidad-agua
| Demo | `GET/POST /api/simulador`, `DELETE /api/simulador/{estanque_id}` (sensor simulado desde la web) | Piscicultor |\|produccion}.{csv\|pdf}?desde=&hasta=` | Piscicultor |

### Reglas de negocio (valores de referencia, `config/*.yaml`)

- **Índice de riesgo (RF-05):** `min(100, 40 × parámetros críticos + 15 × en precaución + 10 × alertas críticas abiertas)`; verde 0–29, amarillo 30–59, rojo ≥ 60.
- **Biomasa y FCR (RF-06):** biomasa = peces vivos × peso medio; FCR = alimento total / ganancia de biomasa ("no calculable" si la ganancia es 0).
- **Ración (RF-07):** biomasa × tasa (% según peso medio: < 10 g 5 %, 10–50 g 3 %, 50–200 g 2 %, ≥ 200 g 1.2 %) × factor de temperatura × factor de oxígeno (normal 1, precaución 0.7/0.5, crítico 0 = suspender).
- **Reportes (RF-08):** vista previa en `/reportes` y descarga en PDF o CSV (UTF-8 con BOM para Excel).

## Pruebas y calidad

```bash
ruff check . && ruff format --check .
python tools/check_domain_purity.py          # M1.1
lint-imports                                 # contratos de arquitectura
pytest -m "not e2e" --cov=src/domain --cov-report=xml --cov-fail-under=80
pytest -m e2e                                # Playwright; guarda capturas en evidencias/
python tools/export_openapi.py --check       # contrato OpenAPI al día
```

Los casos de prueba obligatorios (CP-RF01-01 … CP-RF08-02) se identifican por su ID en el nombre o
docstring de cada prueba.

### Reporte GQM

```bash
python tools/gqm_metrics.py --incremento 1   # escribe docs/gqm/reporte_inc1.md
python tools/gqm_metrics.py --incremento 2   # escribe docs/gqm/reporte_inc2.md
```

Antes de generarlo, ejecutar las pruebas con `--cov-report=xml` y las E2E.

Los indicadores de valor TO-BE (IV-1 a IV-3) se **miden** sobre la app en ejecución con
`python tools/medir_indicadores.py --etiqueta inc2` (muestras crudas en `docs/gqm/mediciones/`).
Las líneas base AS-IS de `docs/gqm/valor_indicadores.yaml` están marcadas como **estimadas**
(derivadas del enunciado) o pendientes: **el equipo debe reemplazarlas por mediciones de campo**
(`as_is_tipo: medido`). Mientras haya un AS-IS estimado o falte alguno, M3.2 se muestra con su
valor pero con el estado "⚠️ no acredita". Los defectos se cuentan desde GitHub Issues (`bug` + `inc1`/`inc2`) o,
si `gh` no está disponible, desde `docs/gqm/defectos.csv`.

## Flujo de trabajo (Scrum + DevOps)

- `main` estable; una rama `feature/hu0X-nombre-corto` por historia; PR hacia `main` con la
  plantilla `.github/pull_request_template.md`; commits convencionales (`feat`, `fix`, `test`,
  `docs`, `chore`, `refactor`).
- Issues por HU con criterios Dado/Cuando/Entonces: `docs/issues/` y `bash tools/crear_issues.sh`.
- Los defectos encontrados en pruebas de aceptación se registran como Issue con `bug` + `incN`.

### Tags de hito

```bash
git tag -a v1.0-PMV -m "Incremento 1 (PMV): HU-01 a HU-04"
git tag -a v2.0-Inc2 -m "Incremento 2: HU-05 a HU-08"
git push origin --tags
```

## Estructura del repositorio

```
.github/            workflows/ci.yml, pull_request_template.md
config/             umbrales.yaml, alimentacion.yaml
db/                 schema.sql (PostgreSQL), seed.sql (demo)
docs/               adr/, c4/, gqm/, issues/, backlog.md, openapi.json
evidencias/         inc1/, inc2/ (capturas generadas por las pruebas E2E)
src/                domain/, ports/, adapters/, main.py
tests/              unit/, integration/, e2e/
tools/              check_domain_purity.py, gqm_metrics.py, crear_issues.sh,
                    export_openapi.py, init_db.py, generar_seed.py
Dockerfile, docker-compose.yml, pyproject.toml, .env.example
```
