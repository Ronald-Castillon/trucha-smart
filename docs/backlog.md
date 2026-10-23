# Product Backlog — TruchaSmart

Descomposición **Épica → Historia de usuario → Tareas**. Cada HU tiene su Issue en GitHub
(fuente: `docs/issues/HU-0X.md`, creados con `tools/crear_issues.sh`), su rama
`feature/hu0X-*` y un PR hacia `main`.

## Definition of Done (por historia)
1. Código compilable y la app arranca (`uvicorn src.main:app`).
2. `ruff check .` y `ruff format --check .` sin errores.
3. Pruebas unitarias e integración en verde; E2E de la HU en verde.
4. Cobertura de `src/domain` >= 80 %.
5. Pureza del dominio: `tools/check_domain_purity.py` (M1.1 = 0 %) y `lint-imports` en verde.
6. Capturas de evidencia `evidencias/incX/RF0X_paso1_entrada.png` y `RF0X_paso2_resultado.png`.
7. Documentación y `docs/openapi.json` actualizados.
8. PR revisado con checklist y CI en verde antes del merge.

## Estado del backlog

| HU | Issue | PR | Estado | Defectos (Issue `bug`) |
|---|---|---|---|---|
| HU-01 | #1 | #9 | ✅ Terminada (Inc. 1) | — |
| HU-02 | #2 | #10 | ✅ Terminada (Inc. 1) | — |
| HU-03 | #3 | #12 | ✅ Terminada (Inc. 1) | — |
| HU-04 | #4 | #13 | ✅ Terminada (Inc. 1) | #11 (formato de mensajes del seed) |
| HU-05 | #5 | — | Pendiente (Inc. 2) | — |
| HU-06 | #6 | — | Pendiente (Inc. 2) | — |
| HU-07 | #7 | — | Pendiente (Inc. 2) | — |
| HU-08 | #8 | — | Pendiente (Inc. 2) | — |

## Épicas

| Épica | Objetivo | Brechas | Historias |
|---|---|---|---|
| E1 Acceso y trazabilidad | Saber quién registra y atiende | B-04, B-06 | HU-01 |
| E2 Registro digital de producción | Sustituir el cuaderno | B-01 | HU-02 |
| E3 Monitoreo y alertas de calidad de agua | Medir con frecuencia y detectar condiciones críticas | B-02, B-03, B-05, B-06 | HU-03, HU-04 |
| E4 Análisis histórico | Ver tendencias y riesgo | B-07 | HU-05 |
| E5 Alimentación eficiente | Controlar FCR y ración | B-08 | HU-06, HU-07 |
| E6 Reportería | Reportes inmediatos | B-09 | HU-08 |
| E7 Predicción con IA (*fuera de alcance*) | Anticipar eventos | B-10 | Incremento 3 |

## Incremento 1 (PMV) — milestone "Incremento 1 (PMV)" — tag `v1.0-PMV`

### HU-01 · Registro y autenticación con roles (RF-01, B-04) — `feature/hu01-autenticacion`
- T1.1 Entidad `Usuario`, enum `Rol` y política de permisos (domain/model).
- T1.2 Casos de uso `registrar_usuario` y `autenticar` (ports/inbound + domain/service).
- T1.3 Puertos `RepositorioUsuario`, `HasherPassword`.
- T1.4 Adaptadores bcrypt, JWT (cookie HttpOnly + Bearer), repositorio SQLAlchemy.
- T1.5 Routers `/api/auth/login`, `/api/usuarios`; vista de login web.
- T1.6 Pruebas CP-RF01-01/02 (unit, integración, E2E + capturas).

### HU-02 · Estanques/jaulas y lotes (RF-02, B-01) — `feature/hu02-estanques`
- T2.1 Entidades `Estanque`, `Lote` con invariantes (peces > 0, peso > 0, un lote activo).
- T2.2 Caso de uso `gestionar_estanque`; puertos de repositorio de estanque y lote.
- T2.3 Repositorios SQLAlchemy; routers CRUD; vistas web.
- T2.4 Pruebas CP-RF02-01/02.

### HU-03 · Lecturas de calidad de agua (RF-03, B-02) — `feature/hu03-lecturas`
- T3.1 Entidad `LecturaAgua` con validación física (pH 0–14, OD >= 0, T 0–40 °C).
- T3.2 Caso de uso `registrar_lectura`; puertos `RepositorioLectura`, `Reloj`.
- T3.3 `POST/GET /api/lecturas`; formulario web; simulador CLI (ADR-004).
- T3.4 Pruebas CP-RF03-01/02 (incluye tiempo de respuesta < 2 s).

### HU-04 · Alertas por umbrales (RF-04, B-03, B-05, B-06) — `feature/hu04-alertas`
- T4.1 `Umbral`, `Alerta`, `EvaluadorCalidadAgua` (valores límite).
- T4.2 Carga de `config/umbrales.yaml` en el adaptador; deduplicación de alertas abiertas.
- T4.3 Caso de uso `atender_alerta` (usuario + fecha/hora); puerto `Notificador`.
- T4.4 `/api/alertas`; panel con refresco periódico.
- T4.5 Pruebas CP-RF04-01/02.

**Cierre Inc. 1:** pruebas completas, capturas, `tools/gqm_metrics.py --incremento 1`, tag `v1.0-PMV`.

## Incremento 2 — milestone "Incremento 2" — tag `v2.0-Inc2`

### HU-05 · Historial, tendencia e índice de riesgo (RF-05, B-07) — `feature/hu05-historial`
- T5.1 Servicio `indice_riesgo` con semáforo.
- T5.2 Caso de uso `consultar_historial` con filtro de fechas.
- T5.3 Endpoints de historial/riesgo; vista con tabla y Chart.js.
- T5.4 Pruebas CP-RF05-01/02.

### HU-06 · Alimentación, mortalidad, biomasa y FCR (RF-06, B-08) — `feature/hu06-alimentacion`
- T6.1 Entidades `RegistroAlimentacion`, `RegistroMortalidad`; `calculadora_fcr`.
- T6.2 Caso de uso `registrar_alimentacion` (incluye mortalidad); repositorios.
- T6.3 Endpoints y vistas; FCR "no calculable" si la ganancia es 0.
- T6.4 Pruebas CP-RF06-01/02.

### HU-07 · Recomendación de ración (RF-07, B-08) — `feature/hu07-racion`
- T7.1 `recomendador_racion` con tabla y factores de `config/alimentacion.yaml`.
- T7.2 Caso de uso `recomendar_racion` con la regla aplicada en texto.
- T7.3 Endpoint y vista; pruebas CP-RF07-01/02.

### HU-08 · Reportes PDF y CSV (RF-08, B-09) — `feature/hu08-reportes`
- T8.1 Caso de uso `exportar_reporte`; puerto `GeneradorReportes`.
- T8.2 Adaptadores reportlab (PDF) y csv; endpoints de descarga; vista.
- T8.3 Pruebas CP-RF08-01/02 (tiempo < 5 s).

**Cierre Inc. 2:** mejora continua según el reporte GQM del Inc. 1, `tools/gqm_metrics.py --incremento 2`, tag `v2.0-Inc2`.
