# Reporte GQM — Incremento 1

Generado por `tools/gqm_metrics.py --incremento 1` el 2026-10-23 01:41.
Los valores se calculan a partir de artefactos reales del repositorio (código, coverage.xml, evidencias/, Issues/defectos.csv, docs/gqm/*.yaml).

| Métrica | Nombre | Valor | Meta | Estado |
|---|---|---|---|---|
| M1.1 | Pureza del dominio | 0.0 % | <= 0.0 % | ✅ cumple |
| M1.2 | Componentes hexagonales conformes | 100 % | >= 100 % | ✅ cumple |
| M2.1 | Evidencias de aceptación | 100 % | >= 100 % | ✅ cumple |
| M2.2 | Densidad de defectos | 0.25 Def/RF | <= 1.00 Def/RF | ✅ cumple |
| M2.3 | Cobertura de src/domain (líneas) | 100.0 % | >= 80.0 % | ✅ cumple |
| M3.1 | Brechas AS-IS resueltas | 60 % | >= 60 % | ✅ cumple |
| M3.2 | Mejora de indicadores de valor | pendiente | >= 50.0 % | ⏳ pendiente |

## Detalle

- **M1.1** — 0 de 15 módulos de src/domain importan fuera de stdlib
- **M1.2** — domain/model: OK; domain/service: OK; ports/inbound: OK; ports/outbound: OK; adapters (inbound + outbound): OK; import-linter: OK
- **M2.1** — 8 de 8 capturas en evidencias/inc1/
- **M2.2** — 1 defectos / 4 RF · fuente: GitHub Issues (label bug + inc1) · #11 Bug: las alertas de db/seed.sql usan un formato de mensaje distinto al del evaluador
- **M2.3** — 504 de 504 líneas ejecutables cubiertas
- **M3.1** — 6 de 10 resueltas y verificadas: B-01, B-02, B-03, B-04, B-05, B-06
- **M3.2** — IV-1: pendiente (falta AS-IS o TO-BE); IV-2: pendiente (falta AS-IS o TO-BE); IV-3: pendiente (falta AS-IS o TO-BE)
