# Registro de mejora continua

Acciones tomadas a partir de la medición GQM y de las retrospectivas de cada incremento.

## Después del Incremento 1 (`v1.0-PMV`) → aplicado al inicio del Incremento 2

| # | Hallazgo (fuente) | Acción | Verificación |
|---|---|---|---|
| MC-01 | RF-03/RF-04: una lectura del **sensor** aparecía en el panel abierto en < 2.5 s, no en < 2 s, porque el panel consultaba cada 2 s (E2E `test_rf03_lecturas`, `test_rf04_alertas`) | Intervalo de refresco del panel: 2 s → **1 s** (`static/panel.js`) | Las E2E exigen ahora **< 2.0 s** desde el `POST /api/lecturas` hasta que el dato o la alerta son visibles |
| MC-02 | ADR-003 (PostgreSQL detrás de un puerto) no estaba verificado: Docker no estaba disponible en el equipo y las pruebas solo usaban SQLite | Nuevo job de CI **"Integración con PostgreSQL 16"**: carga `db/schema.sql` + `db/seed.sql` en PostgreSQL y ejecuta todas las pruebas de integración contra PostgreSQL (`TEST_DATABASE_URL`) | Job `postgres` en `.github/workflows/ci.yml` |
| MC-03 | Defecto #11: los datos demo armaban mensajes a mano y divergían del dominio | `tools/generar_seed.py` usa `Umbral.describir` + prueba de regresión | `test_mensajes_de_alertas_del_seed_siguen_el_formato_del_dominio` |
| MC-04 | La herramienta GQM omitía módulos en la raíz de `src/domain` (M2.3) y `lint-imports` fallaba en consolas Windows | Corregido antes de emitir el reporte del Inc. 1; la herramienta tiene pruebas propias | `tests/unit/test_gqm_metrics.py` |

Métricas sin desviación en el Inc. 1: M1.1 = 0 % (dominio no contaminado), M1.2 = 100 %,
M2.1 = 100 %, M2.3 = 100 %. M3.2 sigue pendiente de las líneas base AS-IS del equipo.

## Durante el Incremento 2 → recomendaciones para el Incremento 3

| # | Hallazgo (fuente) | Acción | Estado |
|---|---|---|---|
| MC-05 | Defecto #19: los datos cargados con `db/seed.sql` en SQLite usaban otro formato de fecha que el ORM y los filtros inclusivos perdían las lecturas de las 00:00 (E2E de RF-08) | `tools/init_db.py` normaliza las marcas de tiempo + prueba de regresión | Corregido en el Inc. 2 |
| MC-06 | M2.2 del Inc. 2 = 0.25 Def/RF (1 defecto / 4 RF) supera la meta de 0.2 | Causa raíz: dos rutas de carga de datos (SQL a mano vs. ORM) para el mismo esquema. Propuesta Inc. 3: generar el seed con los repositorios del ORM (o con Alembic) para que el formato no dependa de una traducción manual de dialecto, y ejecutar las E2E también contra PostgreSQL | Pendiente (Inc. 3) |
| MC-07 | La vista de PDF no se puede capturar en Chromium headless | Se agregó una vista previa HTML del reporte (`/reportes/vista`) con botones de descarga; mejora la usabilidad y deja evidencia verificable | Hecho |
| MC-08 | M3.2 sigue sin línea base AS-IS | El equipo debe medir IV-1..IV-3 en la piscigranja y completar `docs/gqm/valor_indicadores.yaml` | Pendiente (equipo) |
